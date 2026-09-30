"""A stdio MCP server standing in for part of the OWM contract (PRD-3 §11), for lab readers.

    python3 lab/owm_standin/server.py \
        --procedure discount_approval=owm/procedures/discount-approval.md \
        [--decisions decisions.json] [--log calls.jsonl]

It serves **governed content the agent calls for**, instead of content pasted into its prompt: the
agents-first form (agents call; they do not receive assemblies).

- `list_procedures`, `get_procedure`: the organization's decision procedures, served verbatim with a
  content hash so a run records exactly which version the reader read.
- `find_decisions`, `get_decision` (only with `--decisions`): recorded decisions, i.e. decision
  memory, as typed records.

This is lab scaffolding, not an OWM implementation: read-only, no authorization, no persistence
beyond the files it is given. Standard library only; newline-delimited JSON-RPC 2.0 over stdio.
Every call is appended to `--log` (if given) so the run keeps an audit trail of what was served.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

SERVER_INFO = {"name": "owm", "version": "0.1.0-lab"}


def load_procedures(specs: list[str]) -> dict[str, dict[str, str]]:
    out = {}
    for spec in specs:
        kind, path = spec.split("=", 1)
        text = Path(path).read_text()
        heading = re.search(r"^#\s+(.+)$", text, re.M)
        digest = hashlib.sha256(text.encode()).hexdigest()
        out[kind] = {
            "decision_kind": kind,
            "title": heading.group(1).strip() if heading else kind,
            "version": digest[:12],
            "sha256": digest,
            "text": text,
        }
    return out


def tool_list(
    procedures: dict[str, Any], decisions: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    tools = [
        {
            "name": "list_procedures",
            "description": "List the organization's governed decision procedures: how the "
            "organization decides each kind of request.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "get_procedure",
            "description": "Get one governed decision procedure by its decision kind (see "
            "list_procedures): its steps, principles, outcome definitions and the decision "
            "record format.",
            "inputSchema": {
                "type": "object",
                "properties": {"decision_kind": {"type": "string"}},
                "required": ["decision_kind"],
            },
        },
    ]
    if decisions is not None:
        tools += [
            {
                "name": "find_decisions",
                "description": "Search the organization's recorded decisions (decision memory) "
                "by request id, customer, or free text. Returns summaries.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "request_id": {"type": "string"},
                        "customer": {"type": "string"},
                        "text": {"type": "string"},
                    },
                },
            },
            {
                "name": "get_decision",
                "description": "Get one recorded decision in full: the request, outcome, "
                "authority, policy, evidence, approval and timestamps.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"decision_id": {"type": "string"}},
                    "required": ["decision_id"],
                },
            },
        ]
    return tools


def call(
    name: str,
    args: dict[str, Any],
    procedures: dict[str, Any],
    decisions: list[dict[str, Any]] | None,
) -> tuple[Any, bool]:
    if name == "list_procedures":
        return {"procedures": [{k: p[k] for k in ("decision_kind", "title", "version")}
                               for p in procedures.values()]}, False  # fmt: skip
    if name == "get_procedure":
        p = procedures.get(str(args.get("decision_kind", "")))
        if p is None:
            return {"error": "unknown decision_kind", "available": sorted(procedures)}, True
        return p, False
    if decisions is not None and name == "find_decisions":
        rid = str(args.get("request_id") or "").lower()
        cust = str(args.get("customer") or "").lower()
        text = str(args.get("text") or "").lower()
        hits = []
        for d in decisions:
            blob = json.dumps(d).lower()
            if rid and rid != str(d.get("request", {}).get("id", "")).lower():
                continue
            if cust and cust not in str(d.get("request", {}).get("customer", "")).lower():
                continue
            if text and not all(w in blob for w in text.split()):
                continue
            hits.append({k: d.get(k) for k in ("decision_id", "decided_at", "outcome", "status")}
                        | {"request_id": d.get("request", {}).get("id"),
                           "customer": d.get("request", {}).get("customer")})  # fmt: skip
        return {"decisions": hits}, False
    if decisions is not None and name == "get_decision":
        did = str(args.get("decision_id", ""))
        found = next((d for d in decisions if d.get("decision_id") == did), None)
        if found is None:
            return {"error": "unknown decision_id"}, True
        return found, False
    return {"error": f"unknown tool {name}"}, True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--procedure", action="append", default=[], help="KIND=PATH")
    ap.add_argument("--decisions", type=Path, default=None)
    ap.add_argument("--log", type=Path, default=None)
    a = ap.parse_args()
    procedures = load_procedures(a.procedure)
    decisions = json.loads(a.decisions.read_text()) if a.decisions else None
    tools = tool_list(procedures, decisions)

    def log(rec: dict[str, Any]) -> None:
        if a.log:
            with a.log.open("a") as fh:
                fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **rec}) + "\n")

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
            payload, is_error = call(name, args, procedures, decisions)
            log({"tool": name, "arguments": args, "is_error": is_error})
            result = {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "isError": is_error,
            }
        elif method == "ping":
            result = {}
        elif mid is None:
            continue  # a notification (e.g. notifications/initialized): no reply
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
