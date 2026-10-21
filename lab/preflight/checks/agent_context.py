"""The agent-context check: the probe shows the agent's runtime injects nothing it shouldn't."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from preflight.markers import Markers, found_kinds, redact
from preflight.observe.probe import ProbeObservation, stream_events
from preflight.record import CheckResult, State, Value

PASS_SUMMARY = "cwd outside repo · tools as expected · MCP connected · no operator named"


def _init(obs: ProbeObservation) -> dict[str, Any] | None:
    for ev in stream_events(obs.raw_stream):
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            return ev
    return None


def _result(obs: ProbeObservation) -> dict[str, Any] | None:
    for ev in reversed(stream_events(obs.raw_stream)):
        if ev.get("type") == "result":
            return ev
    return None


def _answer(obs: ProbeObservation) -> str:
    res = _result(obs)
    return str(res.get("result") or "") if res else ""


def _auto_memory_has_content(init: dict[str, Any]) -> bool | None:
    paths = init.get("memory_paths")
    auto = paths.get("auto") if isinstance(paths, dict) else None
    if not isinstance(auto, str) or not auto:
        return False
    folder = Path(auto)
    if not folder.is_dir():
        return False
    try:
        return any(folder.iterdir())
    except PermissionError:
        return None


def _problems(obs: ProbeObservation, repo: Path, markers: Markers) -> list[str]:
    if obs.error:
        return [obs.error]
    init = _init(obs)
    if init is None:
        return ["probe stream has no init event"]
    out: list[str] = []
    cwd = str(init.get("cwd") or "")
    if not cwd:
        out.append("probe init event has no cwd")
    if cwd and Path(cwd).resolve().is_relative_to(repo.resolve()):
        out.append("cwd is inside the repo")
    if repo.name.lower() in cwd.lower():
        out.append("cwd names the repo")
    expected = obs.meta.get("expected_tools")
    if expected is not None and sorted(init.get("tools") or []) != sorted(expected):
        out.append("tools in context differ from the runner's expected tools")
    servers = {
        s.get("name"): s.get("status") for s in init.get("mcp_servers") or [] if isinstance(s, dict)
    }
    for name in obs.meta.get("expected_servers") or []:
        if servers.get(name) != "connected":
            out.append(f"MCP server {name} not connected")
    memory = _auto_memory_has_content(init)
    if memory is None:
        out.append("auto memory directory can't be read")
    elif memory:
        out.append("auto memory directory exists and isn't empty")
    result = _result(obs)
    denied = any(e.get("subtype") == "permission_denied" for e in stream_events(obs.raw_stream))
    if denied or (result is not None and result.get("permission_denials")):
        out.append("a permission was denied")
    if result is None:
        out.append("probe stream has no result event")
    elif result.get("is_error") is True:
        out.append("the probe ended on an error")
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


def reader_values(obs: ProbeObservation, cli_version: str | None, markers: Markers) -> list[Value]:
    """What the reader's setup was, for the fingerprint. Names are hashed, never paths.

    A probe that failed (`obs.error`) read nothing: every probe-derived value is unread.
    """
    init = _init(obs) or {}
    meta = obs.meta
    known = "date" in found_kinds(_answer(obs), markers)

    def clean(x: Any) -> Any:
        if isinstance(x, str):
            return redact(x, markers)
        if isinstance(x, list):
            return [clean(i) for i in x]
        return x

    def v(field: str, label: str, value: Any, state: State = "read") -> Value:
        return Value(
            field=f"reader.{field}",
            label=label,
            group="reader",
            value=value,
            source="the probe",
            state=state,
            compare="equal",
        )

    out = [
        v("runner", "Runner", clean(meta.get("runner"))),
        v("model", "Model", clean(meta.get("model"))),
        v("flags", "Flags", clean(meta.get("flags"))),
        v("expected_tools", "Expected tools", clean(meta.get("expected_tools"))),
        v("system_prompt_sha256", "System prompt hash", clean(meta.get("system_prompt_sha256"))),
        v("tools", "Tools in context", sorted(init.get("tools") or [])),
        v("claude_code_version", "Claude Code version", init.get("claude_code_version")),
        v(
            "claude_cli_version",
            "claude --version",
            cli_version,
            "read" if cli_version is not None else "unread",
        ),
        v("api_key_source", "API key source", init.get("apiKeySource")),
        v("skills", "Skills", _digest(init.get("skills"))),
        v("plugins", "Plugins", _digest(init.get("plugins"))),
        v("agents", "Agents", _digest(init.get("agents"))),
        v("slash_commands", "Slash commands", _digest(init.get("slash_commands"))),
        v("knows_real_date", "Knows the real date", known),
    ]
    if obs.error:
        cli_field = "reader.claude_cli_version"
        out = [
            x if x.field == cli_field else x.model_copy(update={"value": None, "state": "unread"})
            for x in out
        ]
    return out
