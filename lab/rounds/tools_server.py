"""The `deal_desk` stdio MCP server: the action tools a proof-round agent calls.

    python lab/rounds/tools_server.py

Configured by env: DEAL_DESK_URL (the service), DEAL_DESK_TOKEN (the agent's session bearer),
DEAL_DESK_WRITE_PATH (`direct` or `blueleaf`), DEAL_DESK_SCENARIO (`S22`), DEAL_DESK_LOG (the
call-log path). The arm decides what `apply_discount` does: `direct` writes the CRM, the way a
credential on the real system would; `blueleaf` goes decide, clearance, adapter, and writes only
if the service clears it. Every `tools/call` appends one record to the log:
`{"at", "tool", "arguments", "result", "is_error"}`. The token never reaches the log.

Standard library only; newline-delimited JSON-RPC 2.0 over stdio (the loop shape of
`lab/owm_standin/server.py`, copied rather than imported).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rounds.scenarios import (  # noqa: E402
    APPLY_DISCOUNT_DESCRIPTION,
    DECIDE_DESCRIPTION,
    GET_REQUEST_DESCRIPTION,
    SCENARIOS,
    Scenario,
)

SERVER_INFO = {"name": "deal_desk", "version": "0.1.0-lab"}
API = "/api/v1"
TABLE = "discount_requests"

_REQUEST_ID = {"type": "string", "description": "For example DR-9001."}


def tool_list(write_path: str) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = [
        {
            "name": "get_request",
            "description": GET_REQUEST_DESCRIPTION,
            "inputSchema": {
                "type": "object",
                "properties": {"request_id": _REQUEST_ID},
                "required": ["request_id"],
            },
        },
        {
            "name": "apply_discount",
            "description": APPLY_DISCOUNT_DESCRIPTION,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "request_id": _REQUEST_ID,
                    "discount_pct": {"type": "number", "description": "For example 12.5."},
                },
                "required": ["request_id", "discount_pct"],
            },
        },
    ]
    if write_path == "blueleaf":
        tools.append(
            {
                "name": "decide",
                "description": DECIDE_DESCRIPTION,
                "inputSchema": {
                    "type": "object",
                    "properties": {"request_id": _REQUEST_ID},
                    "required": ["request_id"],
                },
            }
        )
    return tools


@dataclass
class Ctx:
    url: str
    token: str
    scenario: Scenario
    write_path: str
    decision_id: str | None = None


class _HttpError(Exception):
    def __init__(self, message: str, status: int = 0, body: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


def _http(ctx: Ctx, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {ctx.token}"}
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(ctx.url.rstrip("/") + path, data=data, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        raise _HttpError(f"{e.code} {_short_detail(e, raw)}", e.code, _loads(raw)) from None
    except (urllib.error.URLError, OSError) as e:
        raise _HttpError(f"unreachable {type(e).__name__}") from None


def _loads(raw: bytes) -> Any:
    try:
        return json.loads(raw)
    except ValueError:
        return None


def _short_detail(e: urllib.error.HTTPError, raw_bytes: bytes) -> str:
    raw = _loads(raw_bytes)
    if raw is None:
        return str(e.reason)
    detail = raw.get("detail", raw) if isinstance(raw, dict) else raw
    text = detail if isinstance(detail, str) else json.dumps(detail)
    return text[:200]


def _find_row(ctx: Ctx, request_id: str) -> dict[str, Any] | None:
    rows = _http(ctx, "GET", f"/lab/sor/{TABLE}")["rows"]
    return next((r for r in rows if r.get("request_id") == request_id), None)


def _pct(args: dict[str, Any]) -> float | None:
    raw = args.get("discount_pct")
    if isinstance(raw, bool) or raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value == value and abs(value) != float("inf") else None


def _decide(ctx: Ctx) -> dict[str, Any]:
    try:
        rec: dict[str, Any] = _http(ctx, "POST", f"{API}/decisions", ctx.scenario.decide_body)
    except _HttpError as e:
        # The service allows one live decision per request (DC-6) and names it: adopt it.
        existing = _existing_decision(e)
        if existing is None:
            raise
        rec = _http(ctx, "GET", f"{API}/decisions/{existing}")
    ctx.decision_id = str(rec["decision_id"])
    return rec


def _existing_decision(e: _HttpError) -> str | None:
    if e.status != 409 or not isinstance(e.body, dict):
        return None
    for ref in e.body.get("refusals", []):
        if isinstance(ref, dict) and ref.get("existing"):
            return str(ref["existing"])
    return None


def _apply_direct(ctx: Ctx, request_id: str, pct: float) -> dict[str, Any]:
    today = _http(ctx, "GET", "/lab/clock")["date"]
    patch = {
        "requested_discount_pct": f"{pct:.1f}",
        "status": "Approved",
        "approved_by": ctx.scenario.requester_email,
        "approved_on": str(today),
    }
    out: dict[str, Any] = _http(ctx, "PATCH", f"/lab/sor/{TABLE}/{request_id}", patch)
    return out


def _apply_blueleaf(ctx: Ctx, pct: float) -> dict[str, Any]:
    if ctx.decision_id is None:
        _decide(ctx)
    rec = _http(ctx, "GET", f"{API}/decisions/{ctx.decision_id}")
    action = next((a for a in rec.get("actions", []) if a.get("action") == "apply_discount"), None)
    if action is None:
        return {
            "cleared": False,
            "refused": [{"code": "no_action", "detail": "the decision allows no apply_discount"}],
        }
    params = {**action["params"], "discount": round(pct / 100, 4)}
    cl = _http(
        ctx,
        "POST",
        f"{API}/decisions/{rec['decision_id']}/clearance",
        {
            "decision_id": rec["decision_id"],
            "decision_version": rec["version"],
            "action": "apply_discount",
            "params": params,
        },
    )
    if not cl.get("cleared"):
        refused = [
            {"code": r.get("code"), "detail": r.get("detail")} for r in cl.get("reasons", [])
        ]
        return {"cleared": False, "refused": refused}
    adapter = _http(ctx, "POST", "/lab/adapter/execute", {"clearance_id": cl["clearance_id"]})
    return {"cleared": True, "bound": cl.get("bound"), "adapter": adapter}


def call(name: str, args: dict[str, Any], ctx: Ctx) -> tuple[dict[str, Any], bool]:
    try:
        return _dispatch(name, args, ctx)
    except _HttpError as e:
        return {"error": str(e)}, True


def _dispatch(name: str, args: dict[str, Any], ctx: Ctx) -> tuple[dict[str, Any], bool]:
    request_id = str(args.get("request_id", ""))
    if name == "get_request":
        row = _find_row(ctx, request_id)
        return (row, False) if row is not None else ({"error": "not found"}, True)
    if name == "decide" and ctx.write_path == "blueleaf":
        if request_id != ctx.scenario.request_id:
            return {"error": "unknown request"}, True
        return _decide(ctx), False
    if name == "apply_discount":
        pct = _pct(args)
        if pct is None:
            return {"error": "discount_pct must be a number"}, True
        if ctx.write_path == "direct":
            return _apply_direct(ctx, request_id, pct), False
        if request_id != ctx.scenario.request_id:
            return {"error": "unknown request"}, True
        return _apply_blueleaf(ctx, pct), False
    return {"error": f"unknown tool {name}"}, True


def _log(path: Path | None, rec: dict[str, Any]) -> None:
    if path is None:
        return
    line = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **rec}
    with path.open("a") as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + "\n")


def main() -> None:
    log_env = os.environ.get("DEAL_DESK_LOG")
    log_path = Path(log_env) if log_env else None
    ctx = Ctx(
        url=os.environ["DEAL_DESK_URL"],
        token=os.environ["DEAL_DESK_TOKEN"],
        scenario=SCENARIOS[os.environ.get("DEAL_DESK_SCENARIO", "S22")],
        write_path=os.environ.get("DEAL_DESK_WRITE_PATH", "direct"),
    )
    tools = tool_list(ctx.write_path)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        mid, method = msg.get("id"), msg.get("method")
        params = msg.get("params") or {}
        result: Any = None
        error: dict[str, Any] | None = None
        if method == "initialize":
            result = {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            }
        elif method == "tools/list":
            result = {"tools": tools}
        elif method == "tools/call":
            name = params.get("name", "")
            args = params.get("arguments") or {}
            payload, is_error = call(name, args, ctx)
            _log(
                log_path,
                {"tool": name, "arguments": args, "result": payload, "is_error": is_error},
            )
            result = {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "isError": is_error,
            }
        elif method == "ping":
            result = {}
        elif mid is None:
            continue  # a notification: no reply
        else:
            error = {"code": -32601, "message": f"method not found: {method}"}
        if mid is None:
            continue
        reply: dict[str, Any] = {"jsonrpc": "2.0", "id": mid}
        reply.update({"error": error} if error else {"result": result})
        sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
