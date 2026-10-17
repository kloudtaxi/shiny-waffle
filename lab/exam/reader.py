"""Part 2's reader: the blind reader's controls, with the contract reader as its only tools.

    uv run python lab/exam/reader.py probe --run runs/<exam> --arm <arm> --variant C1
    uv run python lab/exam/reader.py run --run runs/<exam> --arm <arm> --variant C2 --rep 1 \
        [--only S21,S26] [--workers 4] [--cap-usd 180]

`runs/<exam>/arms.json` names each arm's foundation: `mode` (`bearer` or `adapter`), `url`,
`token_file` (bearer) or `person` (adapter), and `kbs`, one knowledge base per corpus. Nothing
secret is in it: a bearer token stays in its file, which only the MCP server reads.

**The controls are `lab/utopia/blind_reader.py`'s** (its README lists them), unchanged:
- the same model and the fixed system prompt, imported from it, with the scenario's procedure
  appended (pre-registration §4);
- a fresh, empty temp directory outside the repo, `--tools ""`, `--strict-mcp-config`,
  `--setting-sources project`, `--no-session-persistence` and `--max-turns 40`;
- C2's text tools are hidden with `--disallowedTools`, never only left off the allowlist;
- a question whose `.jsonl` exists is never asked again.

**The spend guard:** every answer's `total_cost_usd` is summed across the whole exam folder (the
pilot, probes aside, included), finished answers too. No new question starts once the sum
reaches `--cap-usd`.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(LAB / "lab"), str(LAB / "lab" / "utopia")]

from blind_reader import DEFAULT_MODEL, SYSTEM_PROMPT  # noqa: E402

from contract_reader.tools import TEXT_TOOLS, TOOLS  # noqa: E402

SERVER_NAME = "foundation"
SERVER = LAB / "lab" / "contract_reader" / "server.py"
PROCEDURES = {
    "discount": LAB / "owm/procedures/discount-approval.md",
    "credit": LAB / "owm/procedures/credit-limit.md",
    "sla": LAB / "owm/procedures/sla-response.md",
}
HIDDEN = {"C1": [], "C2": list(TEXT_TOOLS)}
ALL_TOOLS = [t["name"] for t in TOOLS]
MAX_TURNS = 40
PROBE_PROMPT = (
    "Before using any tool: (1) list the names of every tool available to you; "
    "(2) say whether you were given any instruction files, memory, or project "
    "context besides this message and your system prompt, and if so quote their "
    "first lines. Then call find_entities once with q 'Northstar' and report "
    "how many entities came back. Nothing else."
)


def questions(run: Path) -> list[dict[str, str]]:
    lines = (run / "questions.tsv").read_text().splitlines()
    head = lines[0].split("\t")
    assert head == ["id", "corpus", "process", "question"], head
    return [dict(zip(head, ln.split("\t", 3), strict=True)) for ln in lines[1:] if ln.strip()]


def arm_config(run: Path, arm: str) -> dict[str, Any]:
    arms = json.loads((run / "arms.json").read_text())["arms"]
    cfg: dict[str, Any] = arms[arm]
    if cfg["mode"] not in ("bearer", "adapter"):
        raise SystemExit(f"arm {arm}: mode is bearer or adapter")
    return cfg


def server_env(cfg: dict[str, Any], kb: str, log: Path) -> dict[str, str]:
    env = {
        "CONTRACT_READER_MODE": cfg["mode"],
        "CONTRACT_READER_URL": cfg["url"],
        "CONTRACT_READER_KB": kb,
        "CONTRACT_READER_LOG": str(log),
    }
    if cfg["mode"] == "bearer":
        env["CONTRACT_READER_TOKEN_FILE"] = str((LAB / cfg["token_file"]).resolve())
    else:
        env["CONTRACT_READER_PERSON"] = cfg["person"]
    return env


def mcp_config(env: dict[str, str]) -> str:
    server = {"type": "stdio", "command": sys.executable, "args": ["-I", str(SERVER)], "env": env}
    return json.dumps({"mcpServers": {SERVER_NAME: server}})


def names(tools: list[str]) -> str:
    return ",".join(f"mcp__{SERVER_NAME}__{t}" for t in tools)


def system_prompt(proc: str) -> tuple[str, dict[str, str]]:
    text = PROCEDURES[proc].read_text()
    record = {
        "path": str(PROCEDURES[proc].relative_to(LAB)),
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    return f"{SYSTEM_PROMPT}\n\n{text}", record


def ask(prompt: str, sysprompt: str, env: dict[str, str], variant: str, model: str) -> str:
    blind = Path(tempfile.mkdtemp(prefix="northstar-exam-blind-"))
    if blind.resolve().is_relative_to(LAB):
        raise RuntimeError(f"blind directory {blind} is inside the repo")
    hidden = HIDDEN[variant]
    allowed = [t for t in ALL_TOOLS if t not in hidden]
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
        sysprompt,
        "--strict-mcp-config",
        "--mcp-config",
        mcp_config(env),
        "--tools",
        "",
        "--allowedTools",
        names(allowed),
        "--setting-sources",
        "project",
        "--no-session-persistence",
        "--max-turns",
        str(MAX_TURNS),
    ]
    if hidden:
        cmd.append(f"--disallowedTools={names(hidden)}")
    try:
        proc = subprocess.run(
            cmd, cwd=blind, env=dict(os.environ), capture_output=True, text=True, timeout=1800
        )
    finally:
        shutil.rmtree(blind, ignore_errors=True)
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(proc.stderr[-2000:])
    return proc.stdout


def events(stream: str) -> list[dict[str, Any]]:
    out = []
    for ln in stream.splitlines():
        if ln.strip().startswith("{"):
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return out


def result_of(stream: str) -> dict[str, Any]:
    return next((e for e in events(stream) if e.get("type") == "result"), {})


def cost_so_far(run: Path) -> float:
    total = 0.0
    for p in run.rglob("*.jsonl"):
        if p.name.endswith(".calls.jsonl"):
            continue
        total += float(result_of(p.read_text()).get("total_cost_usd") or 0)
    return total


def summarize(q: dict[str, str], arm: str, variant: str, kb: str, stream: str) -> str:
    evs = events(stream)
    init = next((e for e in evs if e.get("type") == "system" and e.get("subtype") == "init"), {})
    result = next((e for e in evs if e.get("type") == "result"), {})
    denied = [e for e in evs if e.get("subtype") == "permission_denied"]
    calls: list[dict[str, Any]] = []
    for e in evs:
        msg = e.get("message")
        if isinstance(msg, dict):
            calls += [
                b
                for b in msg.get("content") or []
                if isinstance(b, dict) and b.get("type") == "tool_use"
            ]
    used = [c["name"].split("__")[-1] for c in calls]
    counts = ", ".join(f"{t}×{used.count(t)}" for t in dict.fromkeys(used))
    return "\n".join(
        [
            f"# {arm} · {variant} · {q['id']}",
            "",
            f"- Corpus: {q['corpus']} (`{kb}`) · process: {q['process']}",
            f"- Model: `{init.get('model')}`",
            f"- Turns: {result.get('num_turns')} · duration: {result.get('duration_ms')} ms · "
            f"cost: {result.get('total_cost_usd')} · stop: {result.get('subtype')}",
            f"- Tool calls: {len(calls)} ({counts})",
            f"- Text tools used: {sorted(set(used) & set(TEXT_TOOLS)) or 'none'}",
            f"- Tools in reader context: {len(init.get('tools') or [])} · "
            f"permission denials: {len(denied)}",
            "",
            "## Question (verbatim)",
            "",
            f"> {q['question']}",
            "",
            "## Answer",
            "",
            (result.get("result") or "_(no result)_").strip(),
            "",
        ]
    )


def check_probe(stream: str, variant: str) -> list[str]:
    """What's wrong with a probe, if anything: the pre-registered checks."""
    evs = events(stream)
    init = next((e for e in evs if e.get("type") == "system" and e.get("subtype") == "init"), {})
    tools = sorted(init.get("tools") or [])
    want = sorted(f"mcp__{SERVER_NAME}__{t}" for t in ALL_TOOLS if t not in HIDDEN[variant])
    problems = []
    if tools != want:
        problems.append(f"tools in context {tools} != {want}")
    servers = init.get("mcp_servers") or []
    if not any(s.get("name") == SERVER_NAME and s.get("status") == "connected" for s in servers):
        problems.append(f"MCP server not connected: {servers}")
    if any(e.get("subtype") == "permission_denied" for e in evs):
        problems.append("a permission was denied")
    return problems


def git_head() -> str:
    out = subprocess.run(
        ["git", "-C", str(LAB), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return out.stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser(prog="exam-reader")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("probe", "run"):
        p = sub.add_parser(name)
        p.add_argument("--run", type=Path, required=True)
        p.add_argument("--arm", required=True)
        p.add_argument("--variant", choices=sorted(HIDDEN), required=True)
        p.add_argument("--model", default=DEFAULT_MODEL)
    rp = sub.choices["run"]
    rp.add_argument("--rep", type=int, required=True)
    rp.add_argument("--only", default="", help="comma-separated question ids")
    rp.add_argument("--workers", type=int, default=4)
    rp.add_argument("--cap-usd", type=float, required=True)
    rp.add_argument("--out", default="part2", help="folder under the run, e.g. pilot")
    a = ap.parse_args()

    run = a.run.resolve()
    cfg = arm_config(run, a.arm)
    qs = questions(run)

    if a.cmd == "probe":
        kb = cfg["kbs"]["base"]
        log = Path(tempfile.mkdtemp(prefix="exam-probe-")) / "calls.jsonl"
        sysprompt, _ = system_prompt("discount")
        stream = ask(PROBE_PROMPT, sysprompt, server_env(cfg, kb, log), a.variant, a.model)
        problems = check_probe(stream, a.variant)
        res = result_of(stream)
        print(json.dumps({"arm": a.arm, "variant": a.variant, "problems": problems,
                          "cost_usd": res.get("total_cost_usd"),
                          "answer": (res.get("result") or "")[:600]}, indent=1))  # fmt: skip
        raise SystemExit(1 if problems else 0)

    only = {s for s in a.only.split(",") if s}
    todo = [q for q in qs if not only or q["id"] in only]
    out = run / a.out / a.arm / a.variant / f"r{a.rep}"
    out.mkdir(parents=True, exist_ok=True)
    setup = {
        "arm": a.arm,
        "foundation": cfg,
        "variant": a.variant,
        "hidden_via_disallowedTools": HIDDEN[a.variant],
        "tools": TOOLS,
        "model": a.model,
        "system_prompt": SYSTEM_PROMPT,
        "procedures": {k: system_prompt(k)[1] for k in PROCEDURES},
        "questions_sha256": hashlib.sha256((run / "questions.tsv").read_bytes()).hexdigest(),
        "lab_commit": git_head(),
        "flags": "--tools '' --strict-mcp-config --setting-sources project "
        f"--no-session-persistence --max-turns {MAX_TURNS}; cwd = fresh temp dir outside the repo",
        "cap_usd": a.cap_usd,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (out / "setup.json").write_text(json.dumps(setup, indent=1, ensure_ascii=False) + "\n")

    lock = threading.Lock()
    spent = [cost_so_far(run)]

    def one(q: dict[str, str]) -> None:
        path = out / f"{q['id']}.jsonl"
        if path.exists():
            return
        with lock:
            if spent[0] >= a.cap_usd:
                print(f"{q['id']} skipped: the spend guard is at ${spent[0]:.2f}", flush=True)
                return
        kb = cfg["kbs"][q["corpus"]]
        sysprompt, _ = system_prompt(q["process"])
        log = out / f"{q['id']}.calls.jsonl"
        t0 = time.time()
        try:
            stream = ask(q["question"], sysprompt, server_env(cfg, kb, log), a.variant, a.model)
        except Exception as exc:  # recorded; the run goes on
            (out / f"{q['id']}.error.txt").write_text(str(exc)[:4000])
            print(f"{q['id']} FAILED: {str(exc)[:200]}", flush=True)
            return
        path.write_text(stream)
        (out / f"{q['id']}.md").write_text(summarize(q, a.arm, a.variant, kb, stream))
        c = float(result_of(stream).get("total_cost_usd") or 0)
        with lock:
            spent[0] += c
        print(
            f"{q['id']} done in {time.time() - t0:.0f}s, ${c:.3f} (total ${spent[0]:.2f})",
            flush=True,
        )

    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        list(pool.map(one, todo))
    print(f"spent so far across the exam: ${spent[0]:.2f} (cap ${a.cap_usd:.0f})")


if __name__ == "__main__":
    main()
