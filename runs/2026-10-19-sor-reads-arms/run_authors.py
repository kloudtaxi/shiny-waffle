"""Run a blind author with the blind reader's own isolation (notes.md, amendment 4).

    uv run python runs/2026-10-19-sor-reads-arms/run_authors.py probe
    uv run python runs/2026-10-19-sor-reads-arms/run_authors.py a|b

Each author works in a fresh temp directory outside the repository that holds only:
- its brief (`brief.md`);
- copies of its allowed inputs (`inputs/`);
- an empty `out/`.

It runs as `claude -p` with `--setting-sources project` and `--no-session-persistence`. There is no
CLAUDE.md anywhere up its tree and no memory for that directory, so no instruction file, memory or
project context loads; the probe checks this first. Built-in tools are limited to reading and
writing files (plus WebFetch for Author A's Toolbox docs). There are no MCP servers.

Outputs:
- Author A's `out/` goes to `author-a/`;
- Author B's goes to the sealed folder in the scratchpad, read-only;
- each stream log goes to the scratchpad, outside this run folder, so it never counts toward the
  reader's $200 stop.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
DOCS = LAB / "dataset/evidence/documents"
SCRATCH = Path("/private/tmp/claude-501/-Users-mehulmehta-DEV-Sovera-2026-dev-owm-ve-shiny-waffle/"
               "bc40f257-9055-4a15-92b1-eb0b410661e9/scratchpad")  # fmt: skip
A_DOCS = ["sla_schedule_v1.md", "sla_schedule_v2.md", "acme_support_schedule_c.md",
          "blueriver_support_terms.md", "cedar_support_terms.md", "support_severity_guide.md",
          "support_escalation_procedure.md", "support_org_chart.md", "holiday_calendar.md"]  # fmt: skip
PROBE = ("Before doing anything else: (1) list every instruction file, CLAUDE.md, memory, or project "
         "context you were given besides this message and your system prompt, quoting the first "
         "line of each, or say 'none'; (2) list the tools available to you; (3) list the files "
         "in the current directory. Nothing else.")  # fmt: skip
TASK = "Read brief.md in the current directory and follow it exactly."


def workspace(author: str) -> Path:
    ws = Path(tempfile.mkdtemp(prefix=f"northstar-author-{author}-"))
    if ws.resolve().is_relative_to(LAB):
        raise RuntimeError(f"{ws} is inside the repo")
    (ws / "inputs/documents").mkdir(parents=True)
    (ws / "out").mkdir()
    if author == "a":
        shutil.copy(HERE / "author-a/brief-blind.md", ws / "brief.md")
        shutil.copy(HERE / "author-a/schema.md", ws / "inputs/schema.md")
        for f in A_DOCS:
            shutil.copy(DOCS / f, ws / "inputs/documents" / f)
    elif author == "b":
        shutil.copy(HERE / "brief-author-b-blind.md", ws / "brief.md")
        for p in sorted(DOCS.glob("*.md")):
            shutil.copy(p, ws / "inputs/documents" / p.name)
    return ws


def claude(ws: Path, prompt: str, model: str, web: bool) -> str:
    tools = "Read,Write,Edit,Glob,Grep" + (",WebFetch" if web else "")
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "stream-json",
           "--verbose", "--setting-sources", "project", "--no-session-persistence",
           "--strict-mcp-config", "--tools", tools, "--allowedTools", tools,
           "--max-turns", "80"]  # fmt: skip
    proc = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=3600)
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(proc.stderr[-2000:])
    return proc.stdout


def result(stream: str) -> dict:  # type: ignore[type-arg]
    for ln in reversed(stream.splitlines()):
        if ln.startswith("{"):
            ev = json.loads(ln)
            if ev.get("type") == "result":
                return ev  # type: ignore[no-any-return]
    return {}


def main() -> None:
    which = sys.argv[1]
    logs = SCRATCH / "author-logs"
    logs.mkdir(exist_ok=True)
    if which == "probe":
        ws = workspace("probe")
        out = claude(ws, PROBE, "sonnet", web=True)
        (logs / "probe.jsonl").write_text(out)
        r = result(out)
        print(json.dumps({"cost_usd": r.get("total_cost_usd"), "answer": r.get("result")}, indent=1))
        shutil.rmtree(ws, ignore_errors=True)
        return
    model = {"a": "opus", "b": "sonnet"}[which]
    ws = workspace(which)
    out = claude(ws, TASK, model, web=(which == "a"))
    (logs / f"author-{which}.jsonl").write_text(out)
    r = result(out)
    dest = HERE / "author-a" if which == "a" else SCRATCH / "sor-attack-sealed"
    dest.mkdir(parents=True, exist_ok=True)
    produced = sorted(p.name for p in (ws / "out").iterdir())
    for p in (ws / "out").iterdir():
        shutil.copy(p, dest / p.name)
        if which == "b":
            (dest / p.name).chmod(0o444)
    shutil.rmtree(ws, ignore_errors=True)
    print(json.dumps({"author": which, "model": model, "produced": produced,
                      "cost_usd": r.get("total_cost_usd"), "turns": r.get("num_turns"),
                      "stop": r.get("subtype")}, indent=1))  # fmt: skip


if __name__ == "__main__":
    main()
