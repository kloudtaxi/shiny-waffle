"""The `sor` stdio MCP server for G-51's generated-SQL arms (`runs/2026-10-19-sor-reads-arms/`).

    python lab/sor_reads/gate_server.py        # needs sqlglot (uv run --with sqlglot==30.23.0)

Two tools:
- `read_conventions`: the conventions page (schema notes, conventions, example queries), plus, in
  the sync variant only, the "synced business documentation" files appended after it;
- `run_sql`: one SQL statement through the gate, then MCP Toolbox's `execute_sql` on the read-only
  SQLite file.

**The gate** fails closed:
- the SQL must parse in SQLite's dialect, as exactly one statement;
- the statement must be a SELECT (or a UNION, INTERSECT or EXCEPT of them, CTEs allowed);
- no node anywhere may be a command, DML or DDL, or a file or extension function;
- every table must be one of the database's tables, or a CTE defined in the statement;
- a `LIMIT 200` is imposed (a smaller limit is kept).

The database file is read-only too, so a write that slipped past the gate still fails there.

Configured by env:
- `SOR_TOOLBOX`: the Toolbox binary;
- `SOR_EXEC_CONFIG`: its config holding `execute_sql`;
- `SOR_DB`: the SQLite file;
- `SOR_CONVENTIONS`: the conventions page;
- `SOR_SYNC_DOCS` (optional): paths to synced documents, separated by the OS path separator;
- `SOR_LOG` (optional): a JSONL call log.

Standard library besides sqlglot; newline-delimited JSON-RPC 2.0 over stdio, the loop shape of
`lab/contract_reader/server.py`.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, ParseError

SERVER_INFO = {"name": "sor", "version": "0.1.0-lab"}
ROW_LIMIT = 200
SET_OPS = (exp.Union, exp.Intersect, exp.Except)
_FORBIDDEN_NAMES = ("Command", "Insert", "Update", "Delete", "Drop", "Create", "Alter", "Merge",
                    "TruncateTable", "Pragma", "Transaction", "Commit", "Rollback", "Set", "Use",
                    "Attach", "Detach", "Copy", "LoadData")  # fmt: skip
FORBIDDEN = tuple(c for n in _FORBIDDEN_NAMES if isinstance(c := getattr(exp, n, None), type))
# SQLite functions that reach the file system or load code (some builds ship them)
DENY_FUNCS = {"load_extension", "readfile", "writefile", "edit", "fts3_tokenizer", "zipfile",
              "sqlar_compress", "sqlar_uncompress", "lsdir", "fsdir"}  # fmt: skip

TOOLS = [
    {
        "name": "read_conventions",
        "description": "Returns the data team's documentation for the systems-of-record database: "
        "what each table and column means, how tables relate, conventions, and example queries. "
        "Read it before writing SQL.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "run_sql",
        "description": "Runs one read-only SQL query (SQLite dialect) against Northstar's systems "
        "of record (CRM, ERP, HR, service desk) and returns the rows as JSON. Exactly one SELECT "
        f"statement; at most {ROW_LIMIT} rows come back. Call read_conventions first.",
        "inputSchema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "One SELECT statement."}},
            "required": ["sql"],
            "additionalProperties": False,
        },
    },
]


def db_tables(db: Path) -> set[str]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    finally:
        con.close()


def gate(sql: str, tables: set[str]) -> tuple[str | None, str | None]:
    """(the SQL to run, None) or (None, why it was refused)."""
    try:
        parsed = [s for s in sqlglot.parse(sql, read="sqlite", error_level=ErrorLevel.RAISE) if s]
        # a comment after the last semicolon parses as a comment-only Semicolon: not a statement
        parsed = [s for s in parsed if not isinstance(s, exp.Semicolon)]
    except (ParseError, sqlglot.errors.TokenError) as e:
        return None, f"refused: the SQL could not be parsed ({str(e).splitlines()[0]})"
    if len(parsed) != 1:
        return None, f"refused: exactly one statement is allowed, got {len(parsed)}"
    stmt = parsed[0]
    if not isinstance(stmt, (exp.Select, *SET_OPS)):
        return None, f"refused: only SELECT queries are allowed, got {type(stmt).__name__}"
    bad = next((n for n in stmt.walk() if isinstance(n, FORBIDDEN)), None)
    if bad is not None:
        return None, f"refused: {type(bad).__name__} isn't allowed"
    fn = next((f for f in stmt.find_all(exp.Func) if f.name.lower() in DENY_FUNCS), None)
    if fn is not None:
        return None, f"refused: the function {fn.name.lower()}() isn't allowed"
    ctes = {c.alias_or_name for c in stmt.find_all(exp.CTE)}
    for t in stmt.find_all(exp.Table):
        if t.name and t.name not in tables and t.name not in ctes:
            return None, f"refused: unknown table {t.name!r}"
    if isinstance(stmt, exp.Select):
        lim = stmt.args.get("limit")
        expr = lim.expression if isinstance(lim, exp.Limit) else None
        keep = isinstance(expr, exp.Literal) and expr.is_int and int(expr.name) <= ROW_LIMIT
        out = stmt if keep else stmt.limit(ROW_LIMIT)
        return out.sql(dialect="sqlite"), None
    return f"SELECT * FROM ({stmt.sql(dialect='sqlite')}) LIMIT {ROW_LIMIT}", None


class Session:
    def __init__(self, env: dict[str, str]) -> None:
        self.toolbox, self.config = env["SOR_TOOLBOX"], env["SOR_EXEC_CONFIG"]
        self.db = Path(env["SOR_DB"])
        self.tables = db_tables(self.db)
        page = Path(env["SOR_CONVENTIONS"]).read_text()
        synced = [Path(p) for p in env.get("SOR_SYNC_DOCS", "").split(os.pathsep) if p]
        if synced:
            page += "\n\n---\n\n# Synced business documentation\n\n" + "\n\n---\n\n".join(
                p.read_text() for p in synced
            )
        self.conventions = page
        log = env.get("SOR_LOG")
        self.log = Path(log) if log else None

    def tool(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        started = time.monotonic()
        rec: dict[str, Any] = {"tool": name}
        if name == "read_conventions":
            text, is_error = self.conventions, False
        elif name == "run_sql":
            sql = str(args.get("sql", ""))
            gated, refusal = gate(sql, self.tables)
            rec.update({"sql": sql, "gated_sql": gated, "refused": refusal})
            if refusal:
                text, is_error = refusal, True
            else:
                text, is_error = self.execute(str(gated))
        else:
            text, is_error = f"unknown tool {name!r}", True
        rec.update({"is_error": is_error, "chars": len(text),
                    "ms": round((time.monotonic() - started) * 1000)})  # fmt: skip
        self._log(rec)
        return text, is_error

    def execute(self, sql: str) -> tuple[str, bool]:
        proc = subprocess.run(
            [self.toolbox, "invoke", "execute_sql", json.dumps({"sql": sql}), "--config",
             self.config, "--disable-version-check", "--log-level", "ERROR"],
            capture_output=True, text=True, timeout=60, env={**os.environ, "SOR_DB": str(self.db)},
        )  # fmt: skip
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout).strip().splitlines()
            return f"error: {err[-1] if err else 'the query failed'}", True
        return proc.stdout.strip(), False

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
        return None
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
