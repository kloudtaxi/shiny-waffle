"""Kernel additions for the OWM service (B-06 Task 1): what each judgment is about, the decision's
trace, and flags as `{code, text, routes}`. All of it is additive: no record changes."""

from __future__ import annotations

from typing import Any

import pytest

from . import harness

CHOICE_KEYS = ["q", "choice", "probabilities", "confidence", "uncertain"]
NOUL_KEYS = ["q", "noul", "yes", "uncertain"]
Q_CHOICE = {"type": "choice", "instructions": "Which?", "criteria": {"a": "A", "b": "B"}}
Q_NOUL = {"type": "noul", "instructions": "Is it?"}


class StubEngine:
    """Answers every question the same way, and keeps what it was asked."""

    def __init__(self) -> None:
        self.calls: list[tuple[Any, Any]] = []

    def ask(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((state, questions))
        answers = {name: {"noul": 0.9} if q["type"] == "noul" else
                   {"choice": "a", "probabilities": {"a": 0.8, "b": 0.2}, "confidence": 0.8}
                   for name, q in questions.items()}  # fmt: skip
        return {"answers": answers}


def _judge_both(kernel: Any, eng: StubEngine) -> list[dict[str, Any]]:
    return [kernel.judge(eng, {"document": "text"}, "pick", Q_CHOICE),
            kernel.judge(eng, {"role": "VP Sales"}, "is_it", Q_NOUL)]  # fmt: skip


def test_judge_records_nothing_without_capture() -> None:
    kernel = harness.lab("kernel")
    eng = StubEngine()
    choice, noul = _judge_both(kernel, eng)
    assert kernel.JUDGED.get() is None
    assert list(choice) == CHOICE_KEYS
    assert list(noul) == NOUL_KEYS


def test_capture_changes_neither_what_jev_is_asked_nor_the_result() -> None:
    kernel, additions = harness.lab("kernel"), harness.lab("additions")
    plain_eng, captured_eng = StubEngine(), StubEngine()
    plain = _judge_both(kernel, plain_eng)
    with additions.capture(subject="DR-9001") as cap:
        captured = _judge_both(kernel, captured_eng)
        assert kernel.SUBJECT.get() == "DR-9001"
    assert captured_eng.calls == plain_eng.calls
    assert captured == plain
    # no spec reader ran, so the document judgment is about the subject; the role one, its role
    assert [cap.about[id(j)] for j in captured] == ["DR-9001", "VP Sales"]
    assert kernel.JUDGED.get() is None and kernel.SUBJECT.get() is None


def test_s01_judgment_about_names_documents_and_roles() -> None:
    rec, about = harness.decide_with_capture("S01")
    assert len(about) == len(rec["judgments"]) == 14 and all(about)
    docs = harness.doc_ids("base")
    for j, a in zip(rec["judgments"], about, strict=True):
        if j["q"] in ("party", "covers_product"):
            assert a in docs
        if j["q"] == "basis":
            assert a == "DR-9001"
        if j["q"] == "role":
            assert a not in docs and a != "DR-9001"


def test_flag_items_keep_text_and_order() -> None:
    additions = harness.lab("additions")
    flags = ["routed: X set aside (on_mismatch: route)",
             "EXC-1: not registered; set aside until it is"]  # fmt: skip
    assert additions.flag_items(flags, route_mode=True, routed=True) == [
        {"code": "routed", "text": flags[0], "routes": True},
        {"code": "set_aside", "text": flags[1], "routes": False},
    ]


# one example per row of the contract's §5.5 table: (flag, code, when it routes)
FLAG_ROWS = [
    ("routed: EXC-ACME-NS500-15 set aside (on_mismatch: route)", "routed", "always"),
    ("withheld: commercial_eligibility, authority (computed without EXC-ACME-NS500-15)",
     "withheld", "routed"),
    ("incident for Deal Desk: EXC-1.md differs from approved EXC-1 v1; decided on the approved "
     "version", "incident", "never"),
    ("incident: the procedure file credit_v3.yaml differs from PROC-CREDIT v1; the approved "
     "version was used (raised to Elena Novak)", "incident", "never"),
    ("conflict: policies PRICING-POLICY-2025, PRICING-POLICY-2026", "conflict", "never"),
    ("conflict: registered PRICING-POLICY-2025, PRICING-POLICY-2026", "conflict", "never"),
    ("conflict: exceptions EXC-A-1, EXC-A-2", "conflict", "never"),
    ("conflict: guarantee GUAR-1, GUAR-2", "conflict", "always"),
    ("conflict: registered guarantee GUAR-1, GUAR-2", "conflict", "always"),
    ("MSA-ACME-2025: amended by AMD-ACME-1; terms not confirmed", "conflict", "always"),
    ("tamper signs in EXC-ACME-NS500-15", "tamper", "always"),
    ("EXC-1: document on file is mismatch against registered version 1", "mismatch",
     "route_mode"),
    ("EXC-1: document on file is missing against registered version 2", "mismatch",
     "route_mode"),
    ("EXC-1: differs from its registered version 1; set aside", "set_aside", "never"),
    ("EXC-9: not registered; set aside until it is", "set_aside", "never"),
    ("AMD-1: amends MSA-X-2025, not on file", "not_on_file", "routed"),
    ("AMD-2: depends on AMD-1, which is not on file", "not_on_file", "routed"),
    ("cannot decide: missing open time", "cannot_decide", "routed"),
    ("out of scope: no support terms cover this customer and product", "out_of_scope", "routed"),
    ("no claim yet: 1200.00 would be owed if claimed by 2026-07-24", "note", "routed"),
    ("claim received after the window closed on 2026-07-24", "note", "never"),
    ("EXC-2: issued by Sales, which doesn't own exceptions", "note", "never"),
]  # fmt: skip


ROW_IDS = [f"{i:02d}-{code}" for i, (_, code, _) in enumerate(FLAG_ROWS)]


@pytest.mark.parametrize(("flag", "code", "rule"), FLAG_ROWS, ids=ROW_IDS)
@pytest.mark.parametrize("route_mode", [False, True])
@pytest.mark.parametrize("routed", [False, True])
def test_flag_code_table(flag: str, code: str, rule: str, route_mode: bool, routed: bool) -> None:
    additions = harness.lab("additions")
    routes = {"always": True, "never": False, "routed": routed, "route_mode": route_mode}[rule]
    assert additions.flag_items([flag], route_mode=route_mode, routed=routed) == [
        {"code": code, "text": flag, "routes": routes}
    ]


@pytest.mark.parametrize("sid", list(harness.KIND_OF))
def test_every_routed_decision_has_a_routing_flag_item(sid: str) -> None:
    rec = harness.decide(sid)
    route_to = harness.ROUTE_TO[harness.KIND_OF[sid]]
    routed = rec["gated_outcome"] == route_to and rec["gated_outcome"] != rec["outcome"]
    items = harness.lab("additions").flag_items(
        rec["flags"], route_mode=harness.route_mode(sid), routed=routed
    )
    assert [i["text"] for i in items] == rec["flags"]
    if routed and not rec["uncertain"]:
        assert any(i["routes"] for i in items), rec["flags"]
    if not routed:
        assert not any(i["routes"] for i in items), rec["flags"]


def test_governed_trace_is_optional() -> None:
    trace: dict[str, Any] = {}
    with_trace = harness.decide("S01", trace=trace)
    without = harness.decide("S01")
    assert with_trace == without
    relied = trace["relied"]
    assert relied and all(isinstance(f, str) and isinstance(d, str) for f, d in relied)
    assert {d for _, d in relied} <= harness.doc_ids("base")
