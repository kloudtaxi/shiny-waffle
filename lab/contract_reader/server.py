"""The `foundation` stdio MCP server: the contract reader's tools, over one knowledge base.

    python lab/contract_reader/server.py

Configured by env, so a `claude --mcp-config` file carries no secret:
- `CONTRACT_READER_MODE`: `bearer` (B-20) or `adapter` (web-next's adapter over today's foundation);
- `CONTRACT_READER_URL`: the foundation's root (bearer) or web-next's (adapter), without
  `/api/knowledge/v1`;
- `CONTRACT_READER_KB`: the knowledge base every tool reads;
- `CONTRACT_READER_TOKEN_FILE` (bearer): a file holding the token, read once and kept in memory;
- `CONTRACT_READER_PERSON` (adapter): the BlueLeaf person web-next signs in;
- `CONTRACT_READER_LOG` (optional): a JSONL call log, one record per `tools/call`:
  `{"at", "tool", "arguments", "status", "is_error", "chars", "ms"}`. Neither the answer nor any
  credential goes into it.

The server signs in lazily, on the first tool call, so `tools/list` (the reader's probe) works
without the foundation. Standard library only; newline-delimited JSON-RPC 2.0 over stdio, the loop
shape of `lab/rounds/tools_server.py`.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contract_reader.client import Contract, UnreachableError, adapter, bearer  # noqa: E402
from contract_reader.tools import TOOLS, call, render  # noqa: E402

SERVER_INFO = {"name": "foundation", "version": "0.1.0-lab"}


class Session:
    def __init__(self, env: dict[str, str]) -> None:
        self.mode = env.get("CONTRACT_READER_MODE", "")
        self.url = env.get("CONTRACT_READER_URL", "")
        self.kb = env.get("CONTRACT_READER_KB", "")
        self.token_file = env.get("CONTRACT_READER_TOKEN_FILE", "")
        self.person = env.get("CONTRACT_READER_PERSON", "")
        log = env.get("CONTRACT_READER_LOG")
        self.log = Path(log) if log else None
        self._contract: Contract | None = None
        if self.mode not in ("bearer", "adapter") or not self.url or not self.kb:
            raise SystemExit("contract_reader: set CONTRACT_READER_MODE, _URL and _KB")

    def contract(self) -> Contract:
        if self._contract is None:
            if self.mode == "bearer":
                self._contract = bearer(self.url, Path(self.token_file))
            else:
                self._contract = adapter(self.url, self.person)
        return self._contract

    def tool(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        started = time.monotonic()
        status: int | None = None
        try:
            text, is_error, status = call(self.contract(), self.kb, name, args)
        except (UnreachableError, PermissionError, OSError, ValueError) as e:
            text, is_error = render({"error": "unreachable", "detail": str(e)}), True
        self._log(
            {
                "tool": name,
                "arguments": args,
                "status": status,
                "is_error": is_error,
                "chars": len(text),
                "ms": round((time.monotonic() - started) * 1000),
            }
        )
        return text, is_error

    def _log(self, rec: dict[str, Any]) -> None:
        if self.log is None:
            return
        line = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **rec}
        try:
            with self.log.open("a") as fh:
                fh.write(json.dumps(line, ensure_ascii=False) + "\n")
        except OSError:
            pass


def handle(session: Session, msg: dict[str, Any]) -> dict[str, Any] | None:
    mid, method = msg.get("id"), msg.get("method")
    params = msg.get("params")
    if not isinstance(params, dict):
        params = {}
    result: Any = None
    error: dict[str, Any] | None = None
    if method == "initialize":
        result = {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        args = params.get("arguments")
        text, is_error = session.tool(
            str(params.get("name", "")), args if isinstance(args, dict) else {}
        )
        result = {"content": [{"type": "text", "text": text}], "isError": is_error}
    elif method == "ping":
        result = {}
    elif mid is None:
        return None  # a notification: no reply
    else:
        error = {"code": -32601, "message": f"method not found: {method}"}
    if mid is None:
        return None
    reply: dict[str, Any] = {"jsonrpc": "2.0", "id": mid}
    reply.update({"error": error} if error else {"result": result})
    return reply


def main() -> None:
    session = Session(dict(os.environ))
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        reply = handle(session, msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
