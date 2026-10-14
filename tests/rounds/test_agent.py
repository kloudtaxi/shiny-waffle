from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from rounds import agent
from rounds.agent import (
    AgentCall,
    allowed_tools,
    claude_agent,
    claude_argv,
    mcp_config,
    parse_servers,
    parse_stream,
)
from rounds.scenarios import PROMPTS, SCENARIOS
from rounds.scripted_agent import scripted

S22 = SCENARIOS["S22"]
FAKE_KB_TOKEN = "kb-token-value-123"
FAKE_BEARER = "bearer-value-456"
FAKE_CLAUDE_TOKEN = "claude-token-value-789"


def _call(base: str, write_path: str, log: Path, arm: str, kb_url: str | None = None) -> AgentCall:
    body = json.dumps({"agent_id": S22.agent_id, "on_behalf_of": S22.on_behalf_of}).encode()
    req = urllib.request.Request(
        base + "/lab/sessions", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        token = str(json.loads(resp.read())["token"])
    env = {
        "ROUNDS_ARM": arm,
        "DEAL_DESK_URL": base,
        "DEAL_DESK_TOKEN": token,
        "DEAL_DESK_WRITE_PATH": write_path,
        "DEAL_DESK_SCENARIO": "S22",
        "DEAL_DESK_LOG": str(log),
    }
    return AgentCall(
        system_prompt=PROMPTS["realistic"],
        ask=S22.ask,
        mcp_config=mcp_config(kb_url, write_path),
        allowed_tools=allowed_tools(write_path, []),
        env=env,
    )


def _row(base: str) -> dict[str, str]:
    with urllib.request.urlopen(base + "/lab/sor/discount_requests", timeout=30) as resp:
        rows: list[dict[str, str]] = json.loads(resp.read())["rows"]
    return next(r for r in rows if r["request_id"] == "DR-9001")


def test_mcp_config_names_and_no_secrets() -> None:
    config = mcp_config("http://kb.example/mcp", "blueleaf")
    servers = config["mcpServers"]
    assert set(servers) == {"kb", "deal_desk"}
    assert servers["kb"]["headers"]["Authorization"] == "Bearer ${KB_MCP_TOKEN}"
    env = servers["deal_desk"]["env"]
    assert set(env) == {
        "DEAL_DESK_URL",
        "DEAL_DESK_TOKEN",
        "DEAL_DESK_WRITE_PATH",
        "DEAL_DESK_SCENARIO",
        "DEAL_DESK_LOG",
    }
    assert all(v == "${" + k + "}" for k, v in env.items())
    dumped = json.dumps(config)
    assert FAKE_KB_TOKEN not in dumped and FAKE_BEARER not in dumped


def test_mcp_config_without_kb() -> None:
    servers = mcp_config(None, "direct")["mcpServers"]
    assert set(servers) == {"deal_desk"}


def test_allowed_tools_per_arm() -> None:
    assert allowed_tools("direct", []) == [
        "mcp__deal_desk__get_request",
        "mcp__deal_desk__apply_discount",
    ]
    tools = allowed_tools("blueleaf", ["search_chunks"])
    assert "mcp__deal_desk__decide" in tools and tools[-1] == "mcp__kb__search_chunks"


def test_claude_argv_controls() -> None:
    call = AgentCall(
        system_prompt="sys",
        ask="do it",
        mcp_config=mcp_config(None, "direct"),
        allowed_tools=allowed_tools("direct", []),
        env={"DEAL_DESK_TOKEN": FAKE_BEARER, "KB_MCP_TOKEN": FAKE_KB_TOKEN},
    )
    argv = claude_argv(call)
    assert "--strict-mcp-config" in argv
    assert argv[argv.index("--tools") + 1] == ""
    assert "--no-session-persistence" in argv
    assert argv[argv.index("--setting-sources") + 1] == "project"
    assert argv[argv.index("--max-turns") + 1] == "40"
    assert argv[argv.index("--model") + 1] == "claude-opus-5-5"
    assert argv[argv.index("--system-prompt") + 1] == "sys"
    assert "--disallowedTools" not in argv
    assert not any(a.startswith("--disallowedTools") for a in argv)
    joined = " ".join(argv)
    assert FAKE_KB_TOKEN not in joined and FAKE_BEARER not in joined


def test_parse_stream_reads_result_event() -> None:
    stream = "\n".join(
        [
            '{"type":"system","subtype":"init"}',
            "not json {",
            '{"type":"result","subtype":"error_max_turns","result":"early","num_turns":2,'
            '"total_cost_usd":0.1}',
            '{"type":"result","subtype":"success","result":"done","num_turns":5,'
            '"total_cost_usd":0.25}',
        ]
    )
    assert parse_stream(stream) == ("done", 0.25, 5, "success")
    assert parse_stream('{"type":"system"}\ngarbage') == (None, 0.0, 0, "no result")


INIT = (
    '{"type":"system","subtype":"init","tools":["mcp__kb__search"],"mcp_servers":['
    '{"name":"kb","status":"connected","source":"dynamic"},'
    '{"name":"deal_desk","status":"failed","source":"dynamic"}]}'
)


def test_parse_servers_reads_the_init_event() -> None:
    later = '{"type":"system","subtype":"init","mcp_servers":[]}'
    stream = "\n".join(["not json {", INIT, '{"type":"assistant"}', later])
    assert parse_servers(stream) == {"kb": "connected", "deal_desk": "failed"}
    assert parse_servers('{"type":"system","subtype":"init"}') == {}
    assert parse_servers('{"type":"result","subtype":"success"}\ngarbage') == {}


def test_claude_agent_outcomes(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def run_timeout(*a: Any, **k: Any) -> Any:
        seen["cwd"] = Path(k["cwd"])
        seen["env"] = k["env"]
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    call = AgentCall("s", "a", mcp_config(None, "direct"), [], {"KB_MCP_TOKEN": FAKE_KB_TOKEN})
    monkeypatch.setattr(subprocess, "run", run_timeout)
    res = claude_agent(call, token=FAKE_CLAUDE_TOKEN)
    assert (res.error, res.stop) == ("timeout", "timeout")
    assert not seen["cwd"].exists()
    assert not seen["cwd"].resolve().is_relative_to(agent.REPO)
    assert seen["env"]["KB_MCP_TOKEN"] == FAKE_KB_TOKEN

    def run_fail(*a: Any, **k: Any) -> Any:
        return subprocess.CompletedProcess(a, 1, stdout="", stderr="secret detail")

    monkeypatch.setattr(subprocess, "run", run_fail)
    res = claude_agent(call, token=FAKE_CLAUDE_TOKEN)
    assert res.error == "agent error"
    assert "secret detail" not in (res.error or "")

    def run_ok(*a: Any, **k: Any) -> Any:
        out = '{"type":"result","subtype":"success","result":"ok","num_turns":3,"total_cost_usd":1}'
        return subprocess.CompletedProcess(a, 0, stdout=INIT + "\n" + out, stderr="")

    monkeypatch.setattr(subprocess, "run", run_ok)
    res = claude_agent(call, token=FAKE_CLAUDE_TOKEN)
    assert (res.reply, res.cost_usd, res.turns, res.stop, res.error) == (
        "ok",
        1.0,
        3,
        "success",
        None,
    )
    assert res.servers == {"kb": "connected", "deal_desk": "failed"}

    def run_timeout_after_init(*a: Any, **k: Any) -> Any:
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1, output=INIT.encode())

    monkeypatch.setattr(subprocess, "run", run_timeout_after_init)
    res = claude_agent(call, token=FAKE_CLAUDE_TOKEN)
    assert (res.error, res.servers) == ("timeout", {"kb": "connected", "deal_desk": "failed"})


def test_scripted_agent_drives_tools(live_service: str, tmp_path: Path) -> None:
    direct = _call(live_service, "direct", tmp_path / "d.jsonl", "alone_realistic")
    fn = scripted(
        {
            "alone_realistic": [
                ("get_request", {"request_id": "DR-9001"}),
                ("apply_discount", {"request_id": "DR-9001", "discount_pct": 8}),
            ]
        },
        live_service,
        cost_usd=0.5,
    )
    res = fn(direct)
    assert res.error is None and res.stop == "success" and res.turns == 2 and res.cost_usd == 0.5
    row = _row(live_service)
    assert row["status"] == "Approved" and row["requested_discount_pct"] == "8.0"
    events = [json.loads(ln) for ln in res.transcript.splitlines()]
    uses = [
        b["name"]
        for e in events
        if e["type"] == "assistant"
        for b in e["message"]["content"]
        if b["type"] == "tool_use"
    ]
    assert uses == ["mcp__deal_desk__get_request", "mcp__deal_desk__apply_discount"]
    assert events[-1]["type"] == "result" and events[-1]["total_cost_usd"] == 0.5
    assert (events[0]["type"], events[0]["subtype"]) == ("system", "init")
    assert res.servers == parse_servers(res.transcript) == {"deal_desk": "connected"}
    assert len((tmp_path / "d.jsonl").read_text().splitlines()) == 2


def test_scripted_blueleaf_decide_then_apply8_does_not_write(
    live_service: str, tmp_path: Path
) -> None:
    before = _row(live_service)
    blue = _call(live_service, "blueleaf", tmp_path / "b.jsonl", "with_blueleaf")
    fn = scripted(
        {
            "with_blueleaf": [
                ("decide", {"request_id": "DR-9001"}),
                ("apply_discount", {"request_id": "DR-9001", "discount_pct": 8}),
            ]
        },
        live_service,
    )
    res = fn(blue)
    assert res.error is None
    assert _row(live_service) == before
    replies = [
        json.loads(e["message"]["content"][0]["content"])
        for e in map(json.loads, res.transcript.splitlines())
        if e["type"] == "user"
    ]
    assert replies[-1]["cleared"] is False


def test_scripted_human_step_then_apply15_applies(live_service: str, tmp_path: Path) -> None:
    blue = _call(live_service, "blueleaf", tmp_path / "h.jsonl", "with_blueleaf")
    fn = scripted(
        {
            "with_blueleaf": [
                ("decide", {"request_id": "DR-9001"}),
                ("human", {}),
                ("apply_discount", {"request_id": "DR-9001", "discount_pct": 15}),
            ]
        },
        live_service,
    )
    res = fn(blue)
    assert res.error is None and res.turns == 2
    results = [
        json.loads(json.loads(ln)["message"]["content"][0]["content"])
        for ln in res.transcript.splitlines()
        if json.loads(ln)["type"] == "user"
    ]
    assert results[-1]["cleared"] is True and results[-1]["adapter"]["redeemed"] is True
    row = _row(live_service)
    assert row["status"] == "Approved"
    assert row["approved_by"] == "michael.torres@northstar.example"


def test_scripted_reports_kb_when_configured_and_a_chosen_status(
    live_service: str, tmp_path: Path
) -> None:
    call = _call(live_service, "direct", tmp_path / "k.jsonl", "alone_realistic", "http://kb/mcp")
    both = {"kb": "connected", "deal_desk": "connected"}
    res = scripted({"alone_realistic": []}, live_service)(call)
    assert res.servers == parse_servers(res.transcript) == both
    down = scripted({"alone_realistic": []}, live_service, servers={"deal_desk": "failed"})(call)
    assert down.servers == {"kb": "connected", "deal_desk": "failed"}


def test_scripted_crash(live_service: str, tmp_path: Path) -> None:
    blue = _call(live_service, "blueleaf", tmp_path / "c.jsonl", "with_blueleaf")
    fn = scripted(
        {"with_blueleaf": [("decide", {"request_id": "DR-9001"}), ("crash", {})]}, live_service
    )
    res = fn(blue)
    assert (res.error, res.stop) == ("crashed", "crashed")
    assert '"type": "result"' not in res.transcript


def test_claude_agent_signs_in_fresh_with_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Signed in as the operator, Claude Code tells the agent the account's email (the 2026-10-14
    probe). A fresh config dir holds no account, and the long-lived token signs it in."""
    seen: dict[str, Any] = {}

    def run(*a: Any, **k: Any) -> Any:
        cfg = Path(k["env"]["CLAUDE_CONFIG_DIR"])
        seen.update(env=k["env"], cfg=cfg, empty=cfg.is_dir() and not any(cfg.iterdir()))
        return subprocess.CompletedProcess(a, 2, stdout="", stderr=f"bad {FAKE_CLAUDE_TOKEN}")

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))
    monkeypatch.setattr(subprocess, "run", run)
    call = AgentCall("s", "a", mcp_config(None, "direct"), [], {})
    res = claude_agent(call, token=FAKE_CLAUDE_TOKEN)
    assert seen["env"]["CLAUDE_CODE_OAUTH_TOKEN"] == FAKE_CLAUDE_TOKEN
    assert seen["empty"] and not seen["cfg"].resolve().is_relative_to(agent.REPO)
    assert seen["cfg"] != Path.home() / ".claude" and not seen["cfg"].exists()
    assert FAKE_CLAUDE_TOKEN not in res.transcript and "[redacted]" in res.transcript
    assert FAKE_CLAUDE_TOKEN not in claude_argv(call)


def test_claude_agent_error_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "tok-abcdefgh-123456"
    call = AgentCall("s", "a", mcp_config(None, "direct"), [], {"X": token, "S": "S22"})
    ok = '{"type":"result","subtype":"success","result":"r","num_turns":1,"total_cost_usd":0}'

    def run(stdout: str, stderr: str, code: int) -> Any:
        return lambda *a, **k: subprocess.CompletedProcess(a, code, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(subprocess, "run", run(ok, "", 1))
    assert claude_agent(call, token=FAKE_CLAUDE_TOKEN).error == "agent error"
    maxed = (
        '{"type":"result","subtype":"error_max_turns","is_error":true,"num_turns":40,'
        '"total_cost_usd":2}'
    )
    monkeypatch.setattr(subprocess, "run", run(maxed, "", 0))
    res = claude_agent(call, token=FAKE_CLAUDE_TOKEN)
    assert (res.error, res.stop) == ("agent error", "error_max_turns")
    monkeypatch.setattr(subprocess, "run", run("", f"boom {token} S22", 2))
    res = claude_agent(call, token=FAKE_CLAUDE_TOKEN)
    assert res.error == "agent error"
    assert token not in res.transcript and "[redacted]" in res.transcript
    assert "S22" in res.transcript


def test_scripted_missing_env_raises_before_child(
    live_service: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    call = _call(live_service, "direct", tmp_path / "m.jsonl", "alone_realistic")
    del call.env["DEAL_DESK_TOKEN"]
    started: list[int] = []
    real = subprocess.Popen

    def spy(*a: Any, **k: Any) -> Any:
        started.append(1)
        return real(*a, **k)

    monkeypatch.setattr(subprocess, "Popen", spy)
    with pytest.raises(RuntimeError, match="missing env: DEAL_DESK_TOKEN"):
        scripted({"alone_realistic": []}, live_service)(call)
    assert started == []


def test_scripted_handshake_failure_reaps_child(
    live_service: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    call = _call(live_service, "direct", tmp_path / "e.jsonl", "alone_realistic")
    call.mcp_config["mcpServers"]["deal_desk"]["args"] = ["-c", "pass"]
    procs: list[Any] = []
    real = subprocess.Popen

    def spy(*a: Any, **k: Any) -> Any:
        p = real(*a, **k)
        procs.append(p)
        return p

    monkeypatch.setattr(subprocess, "Popen", spy)
    with pytest.raises(Exception):  # noqa: B017 - the handshake error surfaces as is
        scripted({"alone_realistic": []}, live_service)(call)
    assert len(procs) == 1 and procs[0].poll() is not None
