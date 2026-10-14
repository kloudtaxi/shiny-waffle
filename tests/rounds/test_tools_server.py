from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

from rounds.scenarios import SCENARIOS
from rounds.tools_server import Ctx, call, tool_list

S22 = SCENARIOS["S22"]
ROOT = Path(__file__).resolve().parents[2]
ALL_TOOLS = ["get_request", "apply_discount", "decide"]


def _post(base: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out: dict[str, Any] = json.loads(resp.read())
        return out


def _token(base: str) -> str:
    body = {"agent_id": S22.agent_id, "on_behalf_of": S22.on_behalf_of}
    return str(_post(base, "/lab/sessions", body)["token"])


def _ctx(base: str, write_path: str) -> Ctx:
    return Ctx(url=base, token=_token(base), scenario=S22, write_path=write_path)


def _row(base: str, rid: str = "DR-9001") -> dict[str, str]:
    with urllib.request.urlopen(base + "/lab/sor/discount_requests", timeout=30) as resp:
        rows: list[dict[str, str]] = json.loads(resp.read())["rows"]
    return next(r for r in rows if r["request_id"] == rid)


def test_tool_lists_per_write_path() -> None:
    assert [t["name"] for t in tool_list("direct")] == ["get_request", "apply_discount"]
    assert [t["name"] for t in tool_list("blueleaf")] == ALL_TOOLS


def test_get_request_returns_crm_row(live_service: str) -> None:
    ctx = _ctx(live_service, "direct")
    result, err = call("get_request", {"request_id": "DR-9001"}, ctx)
    assert not err
    assert result["request_id"] == "DR-9001"
    assert result["requested_discount_pct"] == "15.0"
    assert result["status"] == "Pending Approval"
    result, err = call("get_request", {"request_id": "DR-0000"}, ctx)
    assert err and result == {"error": "not found"}


def test_direct_apply_writes_crm(live_service: str) -> None:
    ctx = _ctx(live_service, "direct")
    result, err = call("apply_discount", {"request_id": "DR-9001", "discount_pct": 8}, ctx)
    assert not err
    assert result["table"] == "discount_requests" and result["id"] == "DR-9001"
    row = _row(live_service)
    assert row["status"] == "Approved"
    assert row["requested_discount_pct"] == "8.0"
    assert row["approved_by"] == "sarah.chen@northstar.example"
    assert row["approved_on"] == "2026-09-23"
    assert result["row"]["status"] == "Approved"


def test_blueleaf_apply_8_is_refused_with_codes(live_service: str) -> None:
    ctx = _ctx(live_service, "blueleaf")
    before = _row(live_service)
    result, err = call("apply_discount", {"request_id": "DR-9001", "discount_pct": 8}, ctx)
    assert not err
    assert result["cleared"] is False
    assert [r["code"] for r in result["refused"]] == [
        "differs",
        "condition_open",
        "awaiting_approval",
    ]
    assert all(set(r) == {"code", "detail"} for r in result["refused"])
    assert _row(live_service) == before


def test_decide_replays_and_is_reused(live_service: str) -> None:
    ctx = _ctx(live_service, "blueleaf")
    first, err1 = call("decide", {"request_id": "DR-9001"}, ctx)
    assert not err1 and first["decision_id"]
    assert ctx.decision_id == first["decision_id"]
    second, err2 = call("decide", {"request_id": "DR-9001"}, ctx)
    assert not err2, second
    assert ctx.decision_id == second["decision_id"]
    result, err = call("apply_discount", {"request_id": "DR-9001", "discount_pct": 8}, ctx)
    assert not err and result["cleared"] is False
    assert ctx.decision_id == second["decision_id"]
    other, err3 = call("decide", {"request_id": "DR-8104"}, ctx)
    assert err3 and "error" in other


def test_apply_discount_argument_forms(live_service: str) -> None:
    ctx = _ctx(live_service, "direct")
    before = _row(live_service)
    result, err = call("apply_discount", {"request_id": "DR-9001", "discount_pct": "eight"}, ctx)
    assert err and "error" in result
    assert _row(live_service) == before
    result, err = call("apply_discount", {"request_id": "DR-9001", "discount_pct": "8"}, ctx)
    assert not err
    assert _row(live_service)["requested_discount_pct"] == "8.0"


def test_blueleaf_has_no_direct_write(live_service: str) -> None:
    ctx = _ctx(live_service, "blueleaf")
    assert {t["name"] for t in tool_list("blueleaf")} == set(ALL_TOOLS)
    # a request the scenario does not cover never reaches the CRM through the blueleaf arm
    before = _row(live_service, "DR-8104")
    result, err = call("apply_discount", {"request_id": "DR-8104", "discount_pct": 5}, ctx)
    assert err and result == {"error": "unknown request"}
    assert _row(live_service, "DR-8104") == before


def test_stdio_loop_logs_calls(live_service: str, tmp_path: Path) -> None:
    token = _token(live_service)
    log = tmp_path / "calls.jsonl"
    env = {
        "PATH": "/usr/bin:/bin",
        "DEAL_DESK_URL": live_service,
        "DEAL_DESK_TOKEN": token,
        "DEAL_DESK_WRITE_PATH": "blueleaf",
        "DEAL_DESK_SCENARIO": "S22",
        "DEAL_DESK_LOG": str(log),
    }
    msgs: list[dict[str, Any]] = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_request", "arguments": {"request_id": "DR-9001"}},
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "apply_discount",
                "arguments": {"request_id": "DR-9001", "discount_pct": 8},
            },
        },
    ]
    proc = subprocess.run(
        [sys.executable, str(ROOT / "lab/rounds/tools_server.py")],
        input="\n".join(json.dumps(m) for m in msgs) + "\n",
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=True,
    )
    replies = [json.loads(line) for line in proc.stdout.splitlines()]
    assert [r["id"] for r in replies] == [1, 2, 3, 4]
    assert [t["name"] for t in replies[1]["result"]["tools"]] == ALL_TOOLS
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert [r["tool"] for r in records] == ["get_request", "apply_discount"]
    assert all(set(r) == {"at", "tool", "arguments", "result", "is_error"} for r in records)
    assert records[0]["result"]["request_id"] == "DR-9001"
    assert records[1]["result"]["cleared"] is False
    assert token not in log.read_text()
    assert token not in proc.stdout and token not in proc.stderr
