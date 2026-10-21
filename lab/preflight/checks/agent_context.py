"""The agent-context check: the probe shows the agent's runtime injects nothing it shouldn't."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from preflight.markers import Markers, found_kinds
from preflight.observe.probe import ProbeObservation, stream_events
from preflight.record import CheckResult, Value

PASS_SUMMARY = "cwd outside repo · tools as expected · MCP connected · no operator named"


def _init(obs: ProbeObservation) -> dict[str, Any] | None:
    for ev in stream_events(obs.raw_stream):
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            return ev
    return None


def _answer(obs: ProbeObservation) -> str:
    for ev in reversed(stream_events(obs.raw_stream)):
        if ev.get("type") == "result":
            return str(ev.get("result") or "")
    return ""


def _auto_memory_has_content(init: dict[str, Any]) -> bool:
    paths = init.get("memory_paths")
    auto = paths.get("auto") if isinstance(paths, dict) else None
    if not isinstance(auto, str) or not auto:
        return False
    folder = Path(auto)
    return folder.is_dir() and any(folder.iterdir())


def _problems(obs: ProbeObservation, repo: Path, markers: Markers) -> list[str]:
    if obs.error:
        return [obs.error]
    init = _init(obs)
    if init is None:
        return ["probe stream has no init event"]
    out: list[str] = []
    cwd = str(init.get("cwd") or "")
    if cwd and Path(cwd).resolve().is_relative_to(repo.resolve()):
        out.append("cwd is inside the repo")
    if repo.name.lower() in cwd.lower():
        out.append("cwd names the repo")
    expected = obs.meta.get("expected_tools")
    if expected is not None and sorted(init.get("tools") or []) != sorted(expected):
        out.append("tools in context differ from the runner's expected tools")
    servers = {s.get("name"): s.get("status") for s in init.get("mcp_servers") or []}
    for name in obs.meta.get("expected_servers") or []:
        if servers.get(name) != "connected":
            out.append(f"MCP server {name} not connected")
    if _auto_memory_has_content(init):
        out.append("auto memory directory exists and isn't empty")
    if any(e.get("subtype") == "permission_denied" for e in stream_events(obs.raw_stream)):
        out.append("a permission was denied")
    out.extend(f"runner: {p}" for p in obs.meta.get("problems") or [])
    kinds = found_kinds(_answer(obs), markers)
    out.extend(
        f"the probe's answer names the {k}" for k in ("operator", "home", "repo") if k in kinds
    )
    return out


def check_agent_context(obs: ProbeObservation, repo: Path, markers: Markers) -> CheckResult:
    """Fail on any context the agent should not have; the record holds kinds only."""
    problems = _problems(obs, repo, markers)
    if problems:
        return CheckResult(
            name="agent_context",
            status="fail",
            summary=problems[0],
            problems=problems,
        )
    return CheckResult(name="agent_context", status="pass", summary=PASS_SUMMARY)


def _names(items: object) -> list[str]:
    names: list[str] = []
    for item in items if isinstance(items, list) else []:
        names.append(str(item.get("name", "")) if isinstance(item, dict) else str(item))
    return sorted(names)


def _digest(items: object) -> str:
    names = _names(items)
    return f"{len(names)} · {hashlib.sha256(chr(10).join(names).encode()).hexdigest()[:12]}"


def reader_values(obs: ProbeObservation, cli_version: str, markers: Markers) -> list[Value]:
    """What the reader's setup was, for the fingerprint. Names are hashed, never paths."""
    init = _init(obs) or {}
    meta = obs.meta
    known = "date" in found_kinds(_answer(obs), markers)

    def v(field: str, label: str, value: Any) -> Value:
        return Value(
            field=f"reader.{field}",
            label=label,
            group="reader",
            value=value,
            source="the probe",
            state="read",
            compare="equal",
        )

    return [
        v("runner", "Runner", meta.get("runner")),
        v("model", "Model", meta.get("model")),
        v("flags", "Flags", meta.get("flags")),
        v("expected_tools", "Expected tools", meta.get("expected_tools")),
        v("system_prompt_sha256", "System prompt hash", meta.get("system_prompt_sha256")),
        v("tools", "Tools in context", sorted(init.get("tools") or [])),
        v("claude_code_version", "Claude Code version", init.get("claude_code_version")),
        v("claude_cli_version", "claude --version", cli_version),
        v("api_key_source", "API key source", init.get("apiKeySource")),
        v("skills", "Skills", _digest(init.get("skills"))),
        v("plugins", "Plugins", _digest(init.get("plugins"))),
        v("agents", "Agents", _digest(init.get("agents"))),
        v("slash_commands", "Slash commands", _digest(init.get("slash_commands"))),
        v("knows_real_date", "Knows the real date", known),
    ]
