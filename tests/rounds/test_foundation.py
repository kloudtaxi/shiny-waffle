"""The foundation helpers against recorded API shapes; `utopia` and `blind_reader` are patched."""

from __future__ import annotations

import urllib.error
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from rounds import foundation

KB = "0b9a3f4e-5d1c-4c2a-9f7e-3a1b2c3d4e5f"


def _doc(n: int, created: str, updated: str) -> dict[str, Any]:
    """One `Document` as `GET /kbs/{id}/documents` serialises it (utopia-core models.rs)."""
    return {
        "id": f"7c1e2d3f-0000-4000-8000-00000000000{n}", "kb_id": KB, "source_id": None,
        "filename": f"doc-{n}.md", "mime": "text/markdown", "size_bytes": 2048,
        "sha256": "ab" * 32, "status": "ready", "error": None, "doc_time": None,
        "doc_time_source": "none", "time_context": None, "time_context_at": None,
        "graph_status": "done", "graph_error": None, "text_len": 1800, "chunk_count": 3,
        "tags": [], "external_key": None, "missing_since": None, "deleted_at": None,
        "purged_at": None, "reader_needed": None, "created_at": created, "updated_at": updated,
    }  # fmt: skip


# A `DocumentPage` of three live documents, newest `created_at` first (the route's order). The
# newest `updated_at` belongs to the oldest document, so only paging to the end finds it, and it
# sorts below the others as a string ("00.5Z" < "00Z").
DOCS = [
    _doc(3, "2026-10-04T10:00:00Z", "2026-10-04T10:00:00Z"),
    _doc(2, "2026-10-03T10:00:00.123456Z", "2026-10-05T08:00:00Z"),
    _doc(1, "2026-10-02T10:00:00Z", "2026-10-05T08:00:00.5Z"),
]
STATS = {"total": 3, "ready": 3, "done": 2, "extracting": 1, "failed": 0, "deleted": 1}


def _serve(monkeypatch: pytest.MonkeyPatch, page: dict[str, Any] | None = None) -> list[str]:
    paths: list[str] = []

    def jcall(method: str, path: str, data: object = None) -> Any:
        assert method == "GET" and data is None
        paths.append(path)
        if page is not None:
            return page
        q = parse_qs(urlsplit(path).query)
        limit, offset = int(q["limit"][0]), int(q["offset"][0])
        return {"docs": DOCS[offset : offset + limit], **STATS}

    monkeypatch.setattr("rounds.foundation.utopia.jcall", jcall)
    return paths


def test_import_is_offline_and_mcp_url_shape() -> None:
    assert foundation.mcp_url("x").endswith("/kbs/x/mcp")


def test_fingerprint_reads_the_document_page_and_pages_to_the_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(foundation, "PAGE", 2)
    paths = _serve(monkeypatch)
    assert foundation.fingerprint(KB) == {
        "documents": 3, "deleted": 1, "ready": 3, "done": 2, "latest": "2026-10-05T08:00:00.5Z",
    }  # fmt: skip
    assert paths == [
        f"/kbs/{KB}/documents?limit=2&offset=0",
        f"/kbs/{KB}/documents?limit=2&offset=2",
    ]


def test_fingerprint_asks_for_the_routes_largest_page(monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _serve(monkeypatch)
    assert foundation.fingerprint(KB)["documents"] == 3
    assert paths == [f"/kbs/{KB}/documents?limit=200&offset=0"]  # the route clamps to 1..200


def test_fingerprint_of_an_empty_base(monkeypatch: pytest.MonkeyPatch) -> None:
    empty = {"docs": [], **STATS, "total": 0, "ready": 0, "done": 0, "deleted": 0}
    _serve(monkeypatch, empty)
    assert foundation.fingerprint(KB) == {
        "documents": 0, "deleted": 0, "ready": 0, "done": 0, "latest": None,
    }  # fmt: skip


@pytest.mark.parametrize("missing", ["total", "docs"])
def test_fingerprint_without_total_or_docs_is_a_foundation_error(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    page = {"docs": DOCS, **STATS}
    del page[missing]
    _serve(monkeypatch, page)
    with pytest.raises(RuntimeError) as exc:
        foundation.fingerprint(KB)
    assert str(exc.value) == "foundation error"


def _exits(*_a: Any, **_k: Any) -> Any:
    raise SystemExit("GET /kbs/x -> 500 secret detail")


def _http_error(*_a: Any, **_k: Any) -> Any:
    raise urllib.error.HTTPError("http://x", 502, "secret detail", {}, None)  # type: ignore[arg-type]


@pytest.mark.parametrize("fail", [_exits, _http_error], ids=["system-exit", "http-error"])
def test_every_call_fails_as_a_plain_foundation_error(
    monkeypatch: pytest.MonkeyPatch, fail: Any
) -> None:
    for target in [
        "utopia.jcall",
        "blind_reader.mint_token",
        "blind_reader.revoke",
        "blind_reader.mcp_tools",
    ]:
        monkeypatch.setattr(f"rounds.foundation.{target}", fail)
    calls: list[Callable[[], object]] = [
        lambda: foundation.fingerprint(KB),
        lambda: foundation.mint(KB),
        lambda: foundation.revoke("tok-1"),
        lambda: foundation.kb_tools("t", KB),
    ]
    for call in calls:
        with pytest.raises(RuntimeError) as exc:
            call()
        assert str(exc.value) == "foundation error"
        assert exc.value.__cause__ is None and exc.value.__suppress_context__
