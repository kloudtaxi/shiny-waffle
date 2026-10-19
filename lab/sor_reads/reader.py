"""G-51's three-arm reader: `lab/exam/reader.py`'s controls, unchanged, plus one extra MCP server.

    uv run --with sqlglot==30.23.0 python lab/sor_reads/reader.py --tools-arm GD \
        run --run runs/2026-10-19-sor-reads-arms --arm b20 --variant C2 --rep 1 \
        --out clean-GD --cap-usd 200
    (probe works the same way: --tools-arm GS probe --run … --arm b20 --variant C2)

`--tools-arm` picks what sits beside the graph (`runs/2026-10-19-sor-reads-arms/plan.md`):
- `G`: nothing (the exam's C2);
- `GD`: MCP Toolbox over stdio with Author A's declared tools (`author-a/tools.yaml`);
- `GS`: `lab/sor_reads/gate_server.py`, with `read_conventions` and gated `run_sql`;
- `GS-sync`: the same, with the synced documents appended to the conventions page.

**Only three of the exam reader's functions are replaced, and only to add the server:**
- `mcp_config` adds a server named `sor`;
- `ask` allows it with `mcp__sor`, the server-wide permission;
- `check_probe` expects its tools too.

Everything else is the exam's own code: the model, the system prompt with the procedure, the
hidden text tools, the turn limit, the blind temp directory, infra errors and the spend guard. The
spend guard sums every answer under the run folder, across all arms.

Env, read once: `SOR_TOOLBOX` (the binary), `SOR_DB` (the SQLite file), and for `GS-sync`,
`SOR_SYNC_DOCS` (paths, separated by the OS path separator).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[2]
RUN = LAB / "runs/2026-10-19-sor-reads-arms"
ARMS = ("G", "GD", "GS", "GS-sync")

_spec = importlib.util.spec_from_file_location("exam_reader", LAB / "lab/exam/reader.py")
assert _spec and _spec.loader
exam = importlib.util.module_from_spec(_spec)
sys.modules["exam_reader"] = exam
_spec.loader.exec_module(exam)

STATE: dict[str, Any] = {"arm": "G"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sor_server(log: str) -> dict[str, Any] | None:
    arm = STATE["arm"]
    toolbox, db = os.environ["SOR_TOOLBOX"], os.environ["SOR_DB"]
    if arm == "G":
        return None
    if arm == "GD":
        return {"type": "stdio", "command": toolbox,
                "args": ["--stdio", "--config", str(RUN / "author-a/tools.yaml"),
                         "--disable-version-check", "--log-level", "ERROR"],
                "env": {"SOR_DB": db}}  # fmt: skip
    env = {"SOR_TOOLBOX": toolbox, "SOR_DB": db, "SOR_EXEC_CONFIG": str(RUN / "exec.yaml"),
           "SOR_CONVENTIONS": str(RUN / "author-a/conventions.md"),
           "SOR_LOG": log.replace(".calls.jsonl", ".sor.calls.jsonl")}  # fmt: skip
    if arm == "GS-sync":
        env["SOR_SYNC_DOCS"] = os.environ["SOR_SYNC_DOCS"]
    return {"type": "stdio", "command": sys.executable,
            "args": ["-I", str(LAB / "lab/sor_reads/gate_server.py")], "env": env}  # fmt: skip


def mcp_config(env: dict[str, str]) -> str:
    base = json.loads(exam.mcp_config_original(env))
    extra = sor_server(env.get("CONTRACT_READER_LOG", ""))
    if extra is not None:
        base["mcpServers"]["sor"] = extra
    return json.dumps(base)


def ask(prompt: str, sysprompt: str, env: dict[str, str], variant: str, model: str) -> str:
    """`exam.ask`, line for line, with `mcp__sor` added to the allowed tools."""
    blind = Path(tempfile.mkdtemp(prefix="northstar-sor-blind-"))
    if blind.resolve().is_relative_to(LAB):
        raise RuntimeError(f"blind directory {blind} is inside the repo")
    hidden = exam.HIDDEN[variant]
    allowed = [t for t in exam.ALL_TOOLS if t not in hidden]
    allow = exam.names(allowed) + (",mcp__sor" if STATE["arm"] != "G" else "")
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "stream-json",
           "--verbose", "--system-prompt", sysprompt, "--strict-mcp-config", "--mcp-config",
           mcp_config(env), "--tools", "", "--allowedTools", allow, "--setting-sources",
           "project", "--no-session-persistence", "--max-turns", str(exam.MAX_TURNS)]  # fmt: skip
    if hidden:
        cmd.append(f"--disallowedTools={exam.names(hidden)}")
    try:
        proc = subprocess.run(
            cmd, cwd=blind, env=dict(os.environ), capture_output=True, text=True, timeout=1800
        )
    finally:
        shutil.rmtree(blind, ignore_errors=True)
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(proc.stderr[-2000:])
    return proc.stdout


def check_probe(stream: str, variant: str) -> list[str]:
    """The exam's checks, with the `sor` server's tools expected too (and connected)."""
    evs = exam.events(stream)
    init = next((e for e in evs if e.get("type") == "system" and e.get("subtype") == "init"), {})
    tools = sorted(init.get("tools") or [])
    graph = sorted(f"mcp__{exam.SERVER_NAME}__{t}" for t in exam.ALL_TOOLS
                   if t not in exam.HIDDEN[variant])  # fmt: skip
    sor = sorted(t for t in tools if t.startswith("mcp__sor__"))
    problems = []
    if sorted(set(tools) - set(sor)) != graph:
        problems.append(f"graph tools in context {sorted(set(tools) - set(sor))} != {graph}")
    if STATE["arm"] == "G" and sor:
        problems.append(f"arm G has sor tools: {sor}")
    if STATE["arm"] != "G" and not sor:
        problems.append("no sor tools in context")
    if STATE["arm"] in ("GS", "GS-sync") and sor != ["mcp__sor__read_conventions",
                                                     "mcp__sor__run_sql"]:  # fmt: skip
        problems.append(f"GS tools {sor}")
    servers = {s.get("name"): s.get("status") for s in init.get("mcp_servers") or []}
    for name in [exam.SERVER_NAME] + ([] if STATE["arm"] == "G" else ["sor"]):
        if servers.get(name) != "connected":
            problems.append(f"MCP server {name} not connected: {servers}")
    if any(e.get("subtype") == "permission_denied" for e in evs):
        problems.append("a permission was denied")
    return problems


def fingerprint() -> dict[str, Any]:
    arm = STATE["arm"]
    out: dict[str, Any] = {"tools_arm": arm}
    toolbox = Path(os.environ["SOR_TOOLBOX"])
    out["toolbox_sha256"] = sha(toolbox)
    out["toolbox_version"] = subprocess.run([str(toolbox), "--version"], capture_output=True,
                                            text=True).stdout.strip()  # fmt: skip
    sys.path.insert(0, str(LAB / "lab/sor_reads"))
    from load_sqlite import canonical_sha

    out["sor_db_canonical_sha256"] = canonical_sha(Path(os.environ["SOR_DB"]))
    files = {"GD": ["author-a/tools.yaml"],
             "GS": ["author-a/conventions.md", "exec.yaml"],
             "GS-sync": ["author-a/conventions.md", "exec.yaml"]}.get(arm, [])  # fmt: skip
    out["files"] = {f: sha(RUN / f) for f in files}
    if arm in ("GS", "GS-sync"):
        import sqlglot

        out["sqlglot"] = sqlglot.__version__
        out["gate_sha256"] = sha(LAB / "lab/sor_reads/gate_server.py")
    if arm == "GS-sync":
        out["sync_docs_sha256"] = [sha(Path(p)) for p in os.environ["SOR_SYNC_DOCS"].split(
            os.pathsep) if p]  # fmt: skip
    return out


def main() -> None:
    argv = sys.argv[1:]
    if len(argv) < 2 or argv[0] != "--tools-arm" or argv[1] not in ARMS:
        raise SystemExit(f"usage: reader.py --tools-arm {{{','.join(ARMS)}}} probe|run …")
    STATE["arm"] = argv[1]
    exam.mcp_config_original = exam.mcp_config
    exam.mcp_config, exam.ask, exam.check_probe = mcp_config, ask, check_probe
    fp = fingerprint()
    rest = argv[2:]
    if rest and rest[0] == "run":
        out = rest[rest.index("--out") + 1] if "--out" in rest else "part2"
        arm = rest[rest.index("--arm") + 1]
        variant = rest[rest.index("--variant") + 1]
        rep = rest[rest.index("--rep") + 1]
        folder = RUN / out / arm / variant / f"r{rep}"
        folder.mkdir(parents=True, exist_ok=True)
        name = "sor-setup.json"
        if (folder / name).exists():
            name = f"sor-setup-resume-{len(list(folder.glob('sor-setup-resume-*.json'))) + 1}.json"
        (folder / name).write_text(json.dumps(fp, indent=1) + "\n")
    else:
        print(json.dumps(fp, indent=1))
    sys.argv = [sys.argv[0], *rest]
    exam.main()


if __name__ == "__main__":
    main()
