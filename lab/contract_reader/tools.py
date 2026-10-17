"""The contract reader's tools: names, descriptions, input schemas, and the routes they read.

The descriptions are the lab's, name no trap and are identical for every foundation (guard 4). C2
(graph only) hides `TEXT_TOOLS` with `--disallowedTools`, so the reader never sees them.

Every answer is shaped the same way for every foundation (`shape`): `produced_by` and `raised_by`
are dropped, because they name the tool and model that built the object, and an answer over
`MAX_CHARS` is cut with a note saying so.
"""

from __future__ import annotations

import json
import urllib.parse
from typing import Any

from contract_reader.client import Answer, Contract

MAX_CHARS = 60_000
DROPPED = frozenset({"produced_by", "raised_by"})
TEXT_TOOLS = ("search", "list_documents", "read_passages")

_DATE = {"type": "string", "description": "A date, YYYY-MM-DD."}
_INSTANT = {"type": "string", "description": "A moment, as an ISO 8601 timestamp."}
_CURSOR = {"type": "string", "description": "The next_cursor of a previous result, for more."}
_ID = {"type": "string"}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "find_entities",
        "description": (
            "Find things in the knowledge base by name: people, organizations, places, products,"
            " events, documents and agreements. Returns each match with its id. Give q (all or part"
            " of a name), kind (one of person, organization, place, product, event, document,"
            " agreement), or both."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"q": {"type": "string"}, "kind": {"type": "string"}},
        },
    },
    {
        "name": "get_entity",
        "description": (
            "One entity: its names, its identifiers in other systems, and the facts about it, each"
            " with its evidence. valid_at keeps the facts that hold on that date, as the documents"
            " state it. known_at shows what the knowledge base held at that moment."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"entity_id": _ID, "valid_at": _DATE, "known_at": _INSTANT},
            "required": ["entity_id"],
        },
    },
    {
        "name": "list_facts",
        "description": (
            "The facts whose subject is one entity, optionally only those with one predicate. Each"
            " fact has its object, qualifiers, the dates it holds from and to, its status and its"
            " evidence. valid_at and known_at work as in get_entity."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_id": _ID,
                "predicate": {"type": "string"},
                "valid_at": _DATE,
                "known_at": _INSTANT,
                "cursor": _CURSOR,
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "get_fact",
        "description": (
            "One fact by its id, with its evidence: the quoted words and the document they're in."
            " A fact a rule derived comes with its premises."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"fact_id": _ID},
            "required": ["fact_id"],
        },
    },
    {
        "name": "lookup_identifier",
        "description": (
            "The entity that another system's identifier refers to, such as an account, customer or"
            " registration number. Give the system's name and the identifier. The answer is"
            " not_known when the knowledge base holds no such identifier."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"system": {"type": "string"}, "id": _ID},
            "required": ["system", "id"],
        },
    },
    {
        "name": "neighbourhood",
        "description": (
            "The entities connected to one entity and the facts between them, one or two hops out."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_id": _ID,
                "hops": {"type": "integer", "enum": [1, 2]},
                "valid_at": _DATE,
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "search",
        "description": (
            "Search the documents' text. Returns the closest passages, each with its document and"
            " the words that matched."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "list_documents",
        "description": (
            "The documents in the knowledge base, with their titles, file names and dates. q keeps"
            " the documents whose title or file name contains it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"q": {"type": "string"}, "cursor": _CURSOR},
        },
    },
    {
        "name": "read_passages",
        "description": "One document's text, passage by passage, in order.",
        "inputSchema": {
            "type": "object",
            "properties": {"document_id": _ID, "cursor": _CURSOR},
            "required": ["document_id"],
        },
    },
]

NAMES = frozenset(t["name"] for t in TOOLS)


def _seg(value: object) -> str:
    """One path segment: an id from the reader never adds a segment or a query."""
    return urllib.parse.quote(str(value), safe="")


def _str(args: dict[str, Any], key: str) -> str | None:
    v = args.get(key)
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def shape(obj: Any) -> Any:
    """The same view of every foundation: no producer fields."""
    if isinstance(obj, dict):
        return {k: shape(v) for k, v in obj.items() if k not in DROPPED}
    if isinstance(obj, list):
        return [shape(v) for v in obj]
    return obj


def render(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= MAX_CHARS:
        return text
    return (
        text[:MAX_CHARS]
        + f"\n[cut: this answer is {len(text)} characters and only the first {MAX_CHARS} are shown."
        " Narrow the request, or use a cursor.]"
    )


class BadArgumentsError(ValueError):
    pass


def _route(kb: str, name: str, args: dict[str, Any], c: Contract) -> Answer:
    k = _seg(kb)

    def need(key: str) -> str:
        v = _str(args, key)
        if v is None:
            raise BadArgumentsError(f"{key} is required.")
        return v

    if name == "find_entities":
        q, kind = _str(args, "q"), _str(args, "kind")
        if not q and not kind:
            raise BadArgumentsError("Give q, kind, or both.")
        return c.request("GET", f"/kbs/{k}/entities", {"q": q, "kind": kind, "limit": 20})
    if name == "get_entity":
        return c.request(
            "GET",
            f"/entities/{_seg(need('entity_id'))}",
            {"valid_at": _str(args, "valid_at"), "known_at": _str(args, "known_at")},
        )
    if name == "list_facts":
        return c.request(
            "GET",
            f"/kbs/{k}/facts",
            {
                "subject": need("entity_id"),
                "predicate": _str(args, "predicate"),
                "valid_at": _str(args, "valid_at"),
                "known_at": _str(args, "known_at"),
                "cursor": _str(args, "cursor"),
                "limit": 50,
            },
        )
    if name == "get_fact":
        return c.request("GET", f"/facts/{_seg(need('fact_id'))}", {"expand": "premises"})
    if name == "lookup_identifier":
        return c.request("GET", f"/kbs/{k}/identifiers/{_seg(need('system'))}/{_seg(need('id'))}")
    if name == "neighbourhood":
        hops = args.get("hops", 1)
        if hops not in (1, 2):
            raise BadArgumentsError("hops is 1 or 2.")
        return c.request(
            "GET",
            f"/kbs/{k}/graph/around/{_seg(need('entity_id'))}",
            {"hops": hops, "limit": 100, "valid_at": _str(args, "valid_at")},
        )
    if name == "search":
        limit = args.get("limit", 10)
        if not isinstance(limit, int) or not 1 <= limit <= 20:
            raise BadArgumentsError("limit is a whole number from 1 to 20.")
        return c.request("POST", f"/kbs/{k}/search", body={"q": need("query"), "limit": limit})
    if name == "list_documents":
        return c.request(
            "GET",
            f"/kbs/{k}/documents",
            {"q": _str(args, "q"), "cursor": _str(args, "cursor"), "limit": 100},
        )
    if name == "read_passages":
        doc = _seg(need("document_id"))
        d = c.request("GET", f"/documents/{doc}")
        if d.status != 200 or not isinstance(d.body, dict):
            return d
        version = d.body.get("current_version")
        return c.request(
            "GET",
            f"/documents/{doc}/versions/{_seg(version)}/passages",
            {"cursor": _str(args, "cursor")},
        )
    raise BadArgumentsError(f"No tool is called {name}.")


def call(c: Contract, kb: str, name: str, args: dict[str, Any]) -> tuple[str, bool, int | None]:
    """A tool call: the text the reader sees, whether it's an error, and the HTTP status (None when
    the arguments were refused before any request)."""
    try:
        a = _route(kb, name, args, c)
    except BadArgumentsError as e:
        return render({"error": "bad_request", "detail": str(e)}), True, None
    if 200 <= a.status < 300:
        return render(shape(a.body)), False, a.status
    body = a.body if isinstance(a.body, dict) else {"detail": str(a.body)[:500]}
    return render({"status": a.status, **shape(body)}), True, a.status
