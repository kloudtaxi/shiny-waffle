"""The stdio MCP server, as `claude` runs it: a subprocess speaking JSON-RPC on stdin and stdout."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from tests.contract_reader.conftest import TOKEN, Fake

SERVER = Path(__file__).resolve().parents[2] / "lab" / "contract_reader" / "server.py"


def converse(env: dict[str, str], messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stdin = "".join(json.dumps(m) + "\n" for m in messages)
    out = subprocess.run(
        [sys.executable, "-I", str(SERVER)],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=True,
    )
    return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]


def test_handshake_list_and_call_with_a_log(fake: Fake, tmp_path: Path) -> None:
    token = tmp_path / "t.token"
    token.write_text(TOKEN)
    log = tmp_path / "calls.jsonl"
    env = {
        "CONTRACT_READER_MODE": "bearer",
        "CONTRACT_READER_URL": fake.url,
        "CONTRACT_READER_KB": "kb1",
        "CONTRACT_READER_TOKEN_FILE": str(token),
        "CONTRACT_READER_LOG": str(log),
    }
    replies = converse(
        env,
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "get_fact", "arguments": {"fact_id": "f1"}},
            },
            {"jsonrpc": "2.0", "id": 4, "method": "nope"},
        ],
    )
    assert [r["id"] for r in replies] == [1, 2, 3, 4]
    assert replies[0]["result"]["serverInfo"]["name"] == "foundation"
    assert len(replies[1]["result"]["tools"]) == 9
    call = replies[2]["result"]
    assert call["isError"] is False and json.loads(call["content"][0]["text"])["fact_id"] == "f1"
    assert replies[3]["error"]["code"] == -32601
    (rec,) = [json.loads(line) for line in log.read_text().splitlines()]
    assert rec["tool"] == "get_fact" and rec["status"] == 200 and rec["is_error"] is False
    assert TOKEN not in log.read_text() and "Pelican" not in log.read_text()


def test_tools_list_needs_no_foundation(tmp_path: Path) -> None:
    env = {
        "CONTRACT_READER_MODE": "bearer",
        "CONTRACT_READER_URL": "http://127.0.0.1:9",
        "CONTRACT_READER_KB": "kb1",
        "CONTRACT_READER_TOKEN_FILE": str(tmp_path / "absent"),
    }
    (r,) = converse(env, [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}])
    assert len(r["result"]["tools"]) == 9


def test_an_unreachable_foundation_is_a_tool_error_not_a_crash(tmp_path: Path) -> None:
    token = tmp_path / "t.token"
    token.write_text(TOKEN)
    env = {
        "CONTRACT_READER_MODE": "bearer",
        "CONTRACT_READER_URL": "http://127.0.0.1:9",
        "CONTRACT_READER_KB": "kb1",
        "CONTRACT_READER_TOKEN_FILE": str(token),
    }
    (r,) = converse(
        env,
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_fact", "arguments": {"fact_id": "f1"}},
            }
        ],
    )
    assert r["result"]["isError"] is True
    assert json.loads(r["result"]["content"][0]["text"])["error"] == "unreachable"
