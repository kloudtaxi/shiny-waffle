"""The contract reader's tools: the routes they read, and one view of every foundation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from contract_reader.client import UnreachableError, adapter, bearer
from contract_reader.tools import MAX_CHARS, NAMES, TEXT_TOOLS, TOOLS, call
from tests.contract_reader.conftest import PERSON, PREFIX, TOKEN, Fake


@pytest.fixture
def token_file(tmp_path: Path) -> Path:
    p = tmp_path / "t.token"
    p.write_text(TOKEN + "\n")
    return p


def run(
    fake: Fake, token_file: Path, name: str, args: dict[str, Any]
) -> tuple[Any, bool, int | None]:
    text, is_error, status = call(bearer(fake.url, token_file), "kb1", name, args)
    return json.loads(text), is_error, status


def test_the_tool_set_and_its_text_tools() -> None:
    assert NAMES == {
        "find_entities",
        "get_entity",
        "list_facts",
        "get_fact",
        "lookup_identifier",
        "neighbourhood",
        "search",
        "list_documents",
        "read_passages",
    }
    assert set(TEXT_TOOLS) <= NAMES
    for t in TOOLS:
        assert t["description"] and t["inputSchema"]["type"] == "object"


def test_descriptions_name_no_lab_or_trap_word() -> None:
    words = json.dumps(TOOLS).casefold()
    for w in ("acme", "northstar", "crm-2048", "duns", "discount", "exception", "utopia", "b-20"):
        assert w not in words


def test_bearer_sends_the_token_and_reads_the_right_routes(fake: Fake, token_file: Path) -> None:
    out, err, status = run(fake, token_file, "find_entities", {"q": "Pelican"})
    assert (err, status) == (False, 200) and out["items"][0]["entity_id"] == "e1"
    s = fake.last()
    assert s.path == f"{PREFIX}/kbs/kb1/entities" and s.query == {"q": ["Pelican"], "limit": ["20"]}
    assert s.headers["Authorization"] == f"Bearer {TOKEN}"

    run(
        fake,
        token_file,
        "list_facts",
        {"entity_id": "e1", "valid_at": "2026-09-23", "predicate": ""},
    )
    s = fake.last()
    assert s.path == f"{PREFIX}/kbs/kb1/facts"
    assert s.query == {"subject": ["e1"], "valid_at": ["2026-09-23"], "limit": ["50"]}

    run(fake, token_file, "get_fact", {"fact_id": "f1"})
    assert fake.last().query == {"expand": ["premises"]}

    run(fake, token_file, "neighbourhood", {"entity_id": "e1", "hops": 2})
    s = fake.last()
    assert s.path == f"{PREFIX}/kbs/kb1/graph/around/e1" and s.query["hops"] == ["2"]


def test_producer_fields_are_dropped_everywhere(fake: Fake, token_file: Path) -> None:
    for name, args in (("get_entity", {"entity_id": "e1"}), ("get_fact", {"fact_id": "f1"})):
        text, _, _ = call(bearer(fake.url, token_file), "kb1", name, args)
        assert "produced_by" not in text and "some-foundation" not in text


def test_a_foundation_problem_reaches_the_reader_as_an_error(fake: Fake, token_file: Path) -> None:
    out, err, status = run(fake, token_file, "lookup_identifier", {"system": "CRM", "id": "X-1"})
    assert err and status == 404 and out["error"] == "not_known" and out["status"] == 404
    out, err, status = run(fake, token_file, "search", {"query": "depot"})
    assert err and status == 501 and out["error"] == "not_served"
    assert fake.last().body == {"q": "depot", "limit": 10}


def test_ids_from_the_reader_never_add_a_path_segment(fake: Fake, token_file: Path) -> None:
    run(fake, token_file, "get_entity", {"entity_id": "../kbs/other"})
    assert fake.last().path == f"{PREFIX}/entities/..%2Fkbs%2Fother"
    run(fake, token_file, "lookup_identifier", {"system": "C R M", "id": "a/b?c"})
    assert fake.last().path == f"{PREFIX}/kbs/kb1/identifiers/C%20R%20M/a%2Fb%3Fc"


def test_bad_arguments_are_refused_before_any_request(fake: Fake, token_file: Path) -> None:
    for name, args in (
        ("find_entities", {}),
        ("get_entity", {}),
        ("neighbourhood", {"entity_id": "e1", "hops": 3}),
        ("search", {"query": "x", "limit": 50}),
        ("no_such_tool", {}),
    ):
        before = len(fake.seen)
        _, err, status = run(fake, token_file, name, args)
        assert err and status is None and len(fake.seen) == before


def test_read_passages_reads_the_current_version(fake: Fake, token_file: Path) -> None:
    out, err, _ = run(fake, token_file, "read_passages", {"document_id": "d1"})
    assert not err and out["items"][0] == {"seq": 0, "text": "Pelican runs it."}
    assert [s.path for s in fake.seen[-2:]] == [
        f"{PREFIX}/documents/d1",
        f"{PREFIX}/documents/d1/versions/3/passages",
    ]


def test_a_long_answer_is_cut_and_says_so(fake: Fake, token_file: Path) -> None:
    fake.big = True
    text, err, _ = call(bearer(fake.url, token_file), "kb1", "list_facts", {"entity_id": "e1"})
    assert not err and len(text) < MAX_CHARS + 300
    assert text.endswith("Narrow the request, or use a cursor.]")


def test_the_adapter_signs_in_and_sends_the_cookie(fake: Fake) -> None:
    c = adapter(fake.url, PERSON)
    text, err, status = call(c, "kb1", "get_fact", {"fact_id": "f1"})
    assert not err and status == 200
    login = fake.seen[0]
    assert login.path == "/api/v1/auth/login" and login.body == {"email": PERSON}
    s = fake.last()
    assert "Authorization" not in s.headers and "sid=ok" in s.headers["Cookie"]


def test_a_refused_sign_in_and_an_unreachable_foundation(fake: Fake, token_file: Path) -> None:
    with pytest.raises(PermissionError):
        adapter(fake.url, "someone@else.example")
    with pytest.raises(UnreachableError) as e:
        call(bearer("http://127.0.0.1:9", token_file), "kb1", "get_fact", {"fact_id": "f1"})
    assert TOKEN not in str(e.value) and "127.0.0.1" not in str(e.value)


def test_answers_are_slimmed_the_same_way_for_every_foundation() -> None:
    from contract_reader.tools import shape

    fact = {
        "fact_id": "f1",
        "kb_id": "kb1",
        "predicate": {"key": "operates", "label": "operates", "typed": False},
        "qualifiers": [],
        "valid": {
            "from": {"value": None, "precision": "unknown"},
            "to": {"value": "2025", "precision": "year"},
        },
        "retracted_at": None,
        "recorded_at": "2026-10-17T00:00:00Z",
        "evidence": [
            {
                "doc_id": "d1",
                "version": 1,
                "text_sha256": "abc",
                "passage_id": "p1",
                "span": {"start": 0, "end": 4},
                "quote": "runs",
                "alignment": "exact",
                "origin": "stated",
                "anchors": [],
                "stale": False,
                "document_deleted": False,
            }
        ],
    }
    assert shape(fact) == {
        "fact_id": "f1",
        "predicate": {"key": "operates", "label": "operates", "typed": False},
        "valid": {"from": {"precision": "unknown"}, "to": {"value": "2025", "precision": "year"}},
        "recorded_at": "2026-10-17T00:00:00Z",
        "evidence": [{"doc_id": "d1", "quote": "runs", "alignment": "exact"}],
    }
    hit = {"passage": {"passage_id": "p", "doc_id": "d1", "seq": 2, "text": "t", "headings": []},
           "doc": {"doc_id": "d1", "version": 1, "title": "T", "filename": "t.md"},
           "score": 0.5, "highlights": [{"start": 0, "end": 1}]}  # fmt: skip
    assert shape(hit) == {
        "passage": {"doc_id": "d1", "seq": 2, "text": "t"},
        "doc": {"doc_id": "d1", "title": "T", "filename": "t.md"},
    }
    assert shape({"stale": True, "origin": "ocr"}) == {"stale": True, "origin": "ocr"}
