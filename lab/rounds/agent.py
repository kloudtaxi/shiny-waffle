"""The agent call of a proof round: headless `claude -p` with the arm's MCP tools.

The shape mirrors the blind reader (`lab/utopia/blind_reader.py`): a fresh empty directory outside
the repo, no built-in tools, `--strict-mcp-config`, `--setting-sources project`. Tokens are never
in argv or in the MCP config: the config holds `${VAR}` references that Claude Code expands from the
process env, and the real values travel only in `AgentCall.env`.

A failed run reports one of a fixed vocabulary in `AgentResult.error` ("timeout", "crashed",
"agent error"); the transcript keeps the detail. `AgentResult.servers` is each MCP server's status
from the stream's `init` event, since Claude Code carries on without a server that failed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rounds.tools_server import tool_list

TOOLS_SERVER = Path(__file__).resolve().parent / "tools_server.py"
REPO = Path(__file__).resolve().parents[2]
DEAL_DESK_VARS = (
    "DEAL_DESK_URL",
    "DEAL_DESK_TOKEN",
    "DEAL_DESK_WRITE_PATH",
    "DEAL_DESK_SCENARIO",
    "DEAL_DESK_LOG",
)


@dataclass
class AgentCall:
    system_prompt: str
    ask: str
    mcp_config: dict[str, Any]
    allowed_tools: list[str]
    env: dict[str, str]
    model: str = "claude-opus-5-5"
    max_turns: int = 40
    timeout_s: int = 600


@dataclass
class AgentResult:
    transcript: str
    reply: str | None
    cost_usd: float
    turns: int
    stop: str
    error: str | None
    servers: dict[str, str] = field(default_factory=dict)  # MCP server -> status, from `init`


AgentFn = Callable[[AgentCall], AgentResult]


def mcp_config(kb_mcp_url: str | None, write_path: str) -> dict[str, Any]:
    """The `--mcp-config` document: `kb` (when there is a URL) and `deal_desk`, secrets by `${VAR}`.

    `write_path` reaches the server through DEAL_DESK_WRITE_PATH in the env, not through the file.
    """
    servers: dict[str, Any] = {}
    if kb_mcp_url is not None:
        servers["kb"] = {
            "type": "http",
            "url": kb_mcp_url,
            "headers": {"Authorization": "Bearer ${KB_MCP_TOKEN}"},
        }
    servers["deal_desk"] = {
        "type": "stdio",
        "command": sys.executable,
        "args": [str(TOOLS_SERVER)],
        "env": {name: "${" + name + "}" for name in DEAL_DESK_VARS},
    }
    return {"mcpServers": servers}


def allowed_tools(write_path: str, kb_tools: list[str]) -> list[str]:
    """Every `deal_desk` tool the arm has, plus every `kb` read tool, by full name."""
    deal_desk = [f"mcp__deal_desk__{t['name']}" for t in tool_list(write_path)]
    return deal_desk + [f"mcp__kb__{t}" for t in kb_tools]


def claude_argv(call: AgentCall) -> list[str]:
    return [
        "claude",
        "-p",
        call.ask,
        "--model",
        call.model,
        "--output-format",
        "stream-json",
        "--verbose",
        "--system-prompt",
        call.system_prompt,
        "--strict-mcp-config",
        "--mcp-config",
        json.dumps(call.mcp_config),
        "--tools",
        "",
        "--allowedTools",
        ",".join(call.allowed_tools),
        "--setting-sources",
        "project",
        "--no-session-persistence",
        "--max-turns",
        str(call.max_turns),
    ]


def _events(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip().startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            out.append(event)
    return out


def parse_servers(text: str) -> dict[str, str]:
    """`{name: status}` from the first `system`/`init` event's `mcp_servers`; `{}` without one.

    Claude Code carries on when an MCP server fails to connect, so the runner checks this."""
    for event in _events(text):
        if event.get("type") == "system" and event.get("subtype") == "init":
            servers = event.get("mcp_servers")
            if not isinstance(servers, list):
                return {}
            return {str(s["name"]): str(s.get("status")) for s in servers
                    if isinstance(s, dict) and s.get("name")}  # fmt: skip
    return {}


def parse_stream(text: str) -> tuple[str | None, float, int, str]:
    """`(reply, cost_usd, turns, stop)` from the last `result` event of a stream-json transcript."""
    last: dict[str, Any] | None = None
    for event in _events(text):
        if event.get("type") == "result":
            last = event
    if last is None:
        return None, 0.0, 0, "no result"
    reply = last.get("result")
    return (
        reply if isinstance(reply, str) else None,
        float(last.get("total_cost_usd") or 0.0),
        int(last.get("num_turns") or 0),
        str(last.get("subtype") or "no result"),
    )


def claude_agent(call: AgentCall) -> AgentResult:
    blind = Path(tempfile.mkdtemp(prefix="northstar-rounds-"))
    try:
        if blind.resolve().is_relative_to(REPO):
            raise RuntimeError(f"blind directory {blind} is inside the repo")
        env = {**os.environ, **call.env}
        try:
            proc = subprocess.run(
                claude_argv(call),
                cwd=blind,
                env=env,
                capture_output=True,
                text=True,
                timeout=call.timeout_s,
            )
        except subprocess.TimeoutExpired as e:
            partial = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else e.stdout
            partial = partial or ""
            return AgentResult(partial, None, 0.0, 0, "timeout", "timeout", parse_servers(partial))
    finally:
        shutil.rmtree(blind, ignore_errors=True)
    if proc.returncode != 0 and not proc.stdout:
        tail = _redact(proc.stderr[-2000:], call.env)
        return AgentResult(tail, None, 0.0, 0, "agent error", "agent error")
    reply, cost, turns, stop = parse_stream(proc.stdout)
    failed = proc.returncode != 0 or _result_is_error(proc.stdout)
    return AgentResult(proc.stdout, reply, cost, turns, stop, "agent error" if failed else None,
                       parse_servers(proc.stdout))  # fmt: skip


def _redact(text: str, env: dict[str, str]) -> str:
    for value in env.values():
        if len(value) >= 8:
            text = text.replace(value, "[redacted]")
    return text


def _result_is_error(text: str) -> bool:
    last = next((e for e in reversed(_events(text)) if e.get("type") == "result"), None)
    return bool(last and last.get("is_error"))
