"""Arm B: a blind reader (headless `claude -p`) that answers the scenarios over Utopia's MCP.

    python3 lab/utopia/blind_reader.py probe --run runs/<run> [--variant B2]
    python3 lab/utopia/blind_reader.py run --run runs/<run> --out runs/<run>/arm-b B1 B2

Variants: B1 sees all of Utopia's MCP tools. B2 is graph only: `search_chunks` and
`get_document` are removed from the reader's context entirely (`--disallowedTools`). Tools that
are merely left off the allowlist stay visible and are refused at call time, which tells the
reader documents exist; the first B2 attempt was discarded for exactly that.

Blindness: every reader call runs in a fresh, empty temporary directory **outside the repo**,
with no built-in tools, `--strict-mcp-config` and `--setting-sources project`. The reader must
never see `truth/`, the answer key, or this repo's CLAUDE.md. Its only inputs are the question,
the fixed system prompt below and the MCP tools.

Token: each invocation mints a personal token (read scope, only the KBs named in the run's
`questions.tsv`, 2-day expiry), passes it to `claude` through UTOPIA_MCP_TOKEN (the MCP
config expands it), never writes it to disk, and revokes it when the invocation ends.

A finished question (its .jsonl exists) is never asked again, so a crashed run can resume.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

import utopia

DEFAULT_MODEL = "claude-opus-5-5"
SERVER = "utopia"
TEXT_TOOLS = {"search_chunks", "get_document"}
HIDDEN = {"B1": [], "B2": sorted(TEXT_TOOLS)}
# Verbatim since 2026-09-28. Changing it changes the experiment.
SYSTEM_PROMPT = (
    "You answer questions about an organization. Your only source of information is the "
    "organization's knowledge base, which you can reach through the tools provided. "
    "Answer the question you are asked."
)
PROBE_PROMPT = (
    "Before using any tool: (1) list the names of every tool available to you; "
    "(2) say whether you were given any instruction files, memory, or project "
    "context besides this message and your system prompt, and if so quote their "
    "first lines. Then call find_entities once with name 'Northstar' and report "
    "how many entities came back. Nothing else."
)


def questions(run: Path) -> list[tuple[str, str, str]]:
    rows = (run / "questions.tsv").read_text().splitlines()[1:]
    return [(r.split("\t")[0], r.split("\t")[1], r.split("\t")[2]) for r in rows if r.strip()]


def mint_token(name: str, kbs: list[str]) -> tuple[str, str]:
    body = {"name": name, "scope": "read", "kb_ids": kbs, "expires_in_days": 2}
    resp = utopia.jcall("POST", "/me/tokens", body)
    return resp["token"], resp["info"]["id"]


def revoke(token_id: str) -> None:
    utopia.call("DELETE", f"/me/tokens/{token_id}")
    print("revoked token", token_id)


def mcp_tools(token: str, kb: str) -> list[dict[str, Any]]:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode()
    req = urllib.request.Request(
        f"{utopia.API}/kbs/{kb}/mcp",
        body,
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    tools: list[dict[str, Any]] = json.load(urllib.request.urlopen(req))["result"]["tools"]
    return tools


def mcp_names(tools: list[str]) -> str:
    return ",".join(f"mcp__{SERVER}__{t}" for t in tools)


def mcp_config(kb: str) -> str:
    server = {
        "type": "http",
        "url": f"{utopia.API}/kbs/{kb}/mcp",
        "headers": {"Authorization": "Bearer ${UTOPIA_MCP_TOKEN}"},
    }
    return json.dumps({"mcpServers": {SERVER: server}})


def reader(
    token: str,
    kb: str,
    prompt: str,
    allowed: list[str],
    hidden: list[str],
    model: str,
    max_turns: int = 40,
) -> str:
    blind = Path(tempfile.mkdtemp(prefix="northstar-blind-"))
    if blind.resolve().is_relative_to(utopia.LAB):
        raise RuntimeError(f"blind directory {blind} is inside the repo")
    cmd = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "stream-json",
        "--verbose",
        "--system-prompt",
        SYSTEM_PROMPT,
        "--strict-mcp-config",
        "--mcp-config",
        mcp_config(kb),
        "--tools",
        "",
        "--allowedTools",
        mcp_names(allowed),
        "--setting-sources",
        "project",
        "--no-session-persistence",
        "--max-turns",
        str(max_turns),
    ]
    if hidden:
        cmd.append(f"--disallowedTools={mcp_names(hidden)}")
    env = {**os.environ, "UTOPIA_MCP_TOKEN": token}
    try:
        proc = subprocess.run(cmd, cwd=blind, env=env, capture_output=True, text=True, timeout=1200)
    finally:
        shutil.rmtree(blind, ignore_errors=True)
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(proc.stderr[-2000:])
    return proc.stdout


def _tool_result_text(block: dict[str, Any]) -> str:
    content = block.get("content")
    if isinstance(content, list):
        return "".join(c.get("text", "") for c in content if isinstance(c, dict))
    return str(content)


def summarize(
    sid: str, variant: str, kb: str, question: str, stream: str, allowed: list[str]
) -> str:
    events = [json.loads(ln) for ln in stream.splitlines() if ln.strip().startswith("{")]
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    result = next((e for e in events if e.get("type") == "result"), {})
    denied = [e for e in events if e.get("subtype") == "permission_denied"]
    calls: list[dict[str, Any]] = []
    results: dict[str, tuple[str, bool]] = {}
    for e in events:
        msg = e.get("message")
        if not isinstance(msg, dict):  # system events carry a plain-string message
            continue
        for block in msg.get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                calls.append(block)
            elif block.get("type") == "tool_result":
                results[block.get("tool_use_id", "")] = (
                    _tool_result_text(block),
                    bool(block.get("is_error", False)),
                )
    used = [c["name"].split("__")[-1] for c in calls]
    counts = ", ".join(f"{t}×{used.count(t)}" for t in dict.fromkeys(used))
    md = [
        f"# {variant} · {sid}",
        "",
        f"- KB: `{kb}` · model: `{init.get('model')}` · variant tools: {', '.join(allowed)}",
        f"- MCP servers: `{json.dumps(init.get('mcp_servers'))}`",
        f"- Turns: {result.get('num_turns')} · duration: {result.get('duration_ms')} ms · "
        f"cost: {result.get('total_cost_usd')} · stop: {result.get('subtype')}",
        f"- Tool calls: {len(calls)} ({counts})",
        f"- Text tools used: {sorted(set(used) & TEXT_TOOLS) or 'none'}",
        f"- Tools in reader context: {len(init.get('tools') or [])} · "
        f"permission denials: {len(denied)}",
        "",
        "## Question (verbatim)",
        "",
        f"> {question}",
        "",
        "## Answer",
        "",
        (result.get("result") or "_(no result)_").strip(),
        "",
        "## Tool calls",
        "",
    ]
    for i, c in enumerate(calls, 1):
        text, err = results.get(c.get("id", ""), ("", False))
        args = json.dumps(c.get("input"), ensure_ascii=False)
        tool = c["name"].split("__")[-1]
        md.append(f"{i}. `{tool}` `{args}` → {'ERROR ' if err else ''}{len(text)} chars")
    return "\n".join(md) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(prog="blind_reader", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("probe", "run"):
        p = sub.add_parser(name)
        p.add_argument("--run", type=Path, required=True, help="run folder with questions.tsv")
        p.add_argument("--model", default=DEFAULT_MODEL)
        p.add_argument("--token-name", default=None)
    sub.choices["probe"].add_argument("--variant", choices=sorted(HIDDEN), default="B1")
    run_p = sub.choices["run"]
    run_p.add_argument("--out", type=Path, required=True, help="e.g. runs/<run>/arm-b")
    run_p.add_argument("variants", nargs="*", choices=sorted(HIDDEN), default=["B1", "B2"])
    a = parser.parse_args()

    run = a.run.resolve()
    qs = questions(run)
    kbs = sorted({kb for _, kb, _ in qs})
    token_name = a.token_name or f"northstar-{a.cmd}-{time.strftime('%Y%m%d-%H%M')}"
    token, token_id = mint_token(token_name, kbs)
    try:
        tools = [t["name"] for t in mcp_tools(token, kbs[0])]
        allowed = {v: [t for t in tools if t not in HIDDEN[v]] for v in HIDDEN}
        if a.cmd == "probe":
            out = reader(
                token, kbs[0], PROBE_PROMPT, allowed[a.variant], HIDDEN[a.variant], a.model, 5
            )
            print(summarize("probe", a.variant, kbs[0], "(probe)", out, allowed[a.variant]))
            return

        a.out.mkdir(parents=True, exist_ok=True)
        setup = {
            "model": a.model,
            "system_prompt": SYSTEM_PROMPT,
            "server": SERVER,
            "variants": {v: allowed[v] for v in a.variants},
            "hidden_via_disallowedTools": {v: HIDDEN[v] for v in a.variants},
            "tools_list": mcp_tools(token, kbs[0]),
            "flags": "--tools '' --strict-mcp-config --setting-sources project "
            "--no-session-persistence --max-turns 40; cwd = fresh temp dir outside the repo",
            "token": f"{token_name}: read scope, kb_ids = {kbs}, 2-day expiry, revoked after run",
            "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        setup_file = a.out / f"setup-{'-'.join(a.variants)}.json"
        setup_file.write_text(json.dumps(setup, indent=2) + "\n")

        def one_variant(variant: str) -> None:
            vdir = a.out / variant
            vdir.mkdir(parents=True, exist_ok=True)
            for sid, kb, question in qs:
                if (vdir / f"{sid}.jsonl").exists():
                    continue  # already run; never re-ask a finished question
                t0 = time.time()
                try:
                    stream = reader(token, kb, question, allowed[variant], HIDDEN[variant], a.model)
                except Exception as exc:  # keep going; record the failure
                    (vdir / f"{sid}.error.txt").write_text(str(exc))
                    print(f"{variant} {sid} FAILED: {str(exc)[:200]}", flush=True)
                    continue
                (vdir / f"{sid}.jsonl").write_text(stream)
                summary = summarize(sid, variant, kb, question, stream, allowed[variant])
                (vdir / f"{sid}.md").write_text(summary)
                print(f"{variant} {sid} done in {time.time() - t0:.0f}s", flush=True)

        with cf.ThreadPoolExecutor(max_workers=len(a.variants)) as pool:
            list(pool.map(one_variant, a.variants))
    finally:
        revoke(token_id)


if __name__ == "__main__":
    main()
