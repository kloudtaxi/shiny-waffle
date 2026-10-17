"""A fake foundation that serves a few contract routes, and records every request it gets.

It answers as B-20 does (a bearer token) and as web-next's adapter does (a sign-in, then a cookie),
so one fixture tests both ways in.
"""

from __future__ import annotations

import json
import threading
import urllib.parse
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

TOKEN = "fake-token-not-a-secret"
PERSON = "reader@blueleaf.example"
PREFIX = "/api/knowledge/v1"

FACT = {
    "fact_id": "f1",
    "kb_id": "kb1",
    "subject": {"entity_id": "e1", "name": "Pelican Haulage Ltd", "kind": None},
    "predicate": {"key": "operates", "label": "operates", "typed": False},
    "object": {"kind": "value", "value": "Rotterdam depot", "unit": None, "datatype": "string"},
    "evidence": [{"doc_id": "d1", "quote": "runs the Rotterdam depot", "alignment": "exact"}],
    "produced_by": {"run_id": "r", "stage": "extract", "tool": "some-foundation", "model": "m"},
}


@dataclass
class Seen:
    method: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    body: Any


@dataclass
class Fake:
    url: str
    seen: list[Seen] = field(default_factory=list)
    big: bool = False

    def last(self) -> Seen:
        return self.seen[-1]


def _routes(fake: Fake, method: str, path: str) -> tuple[int, Any]:
    p = path[len(PREFIX) :]
    if method == "GET" and p == "/kbs/kb1/entities":
        return 200, {
            "items": [{"entity_id": "e1", "name": "Pelican Haulage Ltd"}],
            "next_cursor": None,
        }
    if method == "GET" and p == "/entities/e1":
        return 200, {"entity_id": "e1", "facts": [FACT], "produced_by": FACT["produced_by"]}
    if method == "GET" and p == "/kbs/kb1/facts":
        items = [FACT] * (2000 if fake.big else 1)
        return 200, {"items": items, "next_cursor": None}
    if method == "GET" and p == "/facts/f1":
        return 200, FACT
    if method == "GET" and p.startswith("/kbs/kb1/identifiers/"):
        return 404, {"error": "not_known", "detail": "No such identifier.", "coverage": {"read": 2}}
    if method == "GET" and p == "/kbs/kb1/graph/around/e1":
        return 200, {"nodes": [], "edges": [], "focus": "e1"}
    if method == "POST" and p == "/kbs/kb1/search":
        return 501, {"error": "not_served", "detail": "K10 isn't served."}
    if method == "GET" and p == "/kbs/kb1/documents":
        return 200, {"items": [{"doc_id": "d1", "title": "Depots"}], "next_cursor": None}
    if method == "GET" and p == "/documents/d1":
        return 200, {"doc_id": "d1", "current_version": 3}
    if method == "GET" and p == "/documents/d1/versions/3/passages":
        return 200, {
            "items": [{"passage_id": "p1", "seq": 0, "text": "Pelican runs it."}],
            "next_cursor": None,
        }
    return 404, {"error": "not_found", "detail": "No such thing."}


@pytest.fixture
def fake() -> Iterator[Fake]:
    state: dict[str, Fake] = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a: Any) -> None:
            pass

        def _do(self, method: str) -> None:
            f = state["fake"]
            parsed = urllib.parse.urlsplit(self.path)
            n = int(self.headers.get("content-length") or 0)
            raw = self.rfile.read(n) if n else b""
            body = json.loads(raw) if raw else None
            f.seen.append(
                Seen(
                    method,
                    parsed.path,
                    urllib.parse.parse_qs(parsed.query),
                    dict(self.headers),
                    body,
                )
            )
            if parsed.path == "/api/v1/auth/login":
                if body == {"email": PERSON}:
                    self.send_response(200)
                    self.send_header("Set-Cookie", "sid=ok; Path=/")
                    self.end_headers()
                    self.wfile.write(b"{}")
                else:
                    self.send_response(401)
                    self.end_headers()
                return
            authed = self.headers.get("Authorization") == f"Bearer {TOKEN}" or "sid=ok" in (
                self.headers.get("Cookie") or ""
            )
            status, out = (
                _routes(f, method, parsed.path) if authed else (401, {"error": "forbidden"})
            )
            data = json.dumps(out).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            self._do("GET")

        def do_POST(self) -> None:
            self._do("POST")

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state["fake"] = Fake(f"http://127.0.0.1:{server.server_address[1]}")
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        yield state["fake"]
    finally:
        server.shutdown()
        server.server_close()
