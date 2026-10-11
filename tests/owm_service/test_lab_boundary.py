"""The lab boundary (B-06 Task 7): `_lab.decide` makes exactly the record `governed.decide` makes,
the kernel reads its tables through the overlay, and the Jev engine is replay only unless a live
run is switched on, and then only up to its cap. Replay only: no test constructs a live engine."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from owm_service import _lab
from owm_service.errors import CannotDecide

from . import harness

Overlay = Callable[[str, list[dict[str, str]]], list[dict[str, str]]]
KINDS: dict[str, _lab.DecisionType] = {"discount": "discount", "credit": "credit", "sla": "sla"}


def strip(record: dict[str, Any]) -> dict[str, Any]:
    """The record without `scenario`, the one key that carries the caller's id."""
    return {k: v for k, v in record.items() if k != "scenario"}


def same(name: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return rows


@pytest.fixture(scope="module")
def engine(tmp_path_factory: pytest.TempPathFactory) -> _lab.ReplayEngine:
    calls = tmp_path_factory.mktemp("jev") / "calls.jsonl"
    return _lab.ReplayEngine(_lab.replay_files(_lab.LAB_ROOT), calls, live=False, cap=0)


def run(
    sid: str, engine: _lab.ReplayEngine, tmp: Path, *, overlay: Overlay = same,
    root: Path | None = None, route_mode: bool = False, sid_as: str | None = None,
    staff: list[dict[str, str]] | None = None, entries: list[dict[str, Any]] | None = None,
) -> _lab.KernelResult:  # fmt: skip
    """`_lab.decide` on the scenario's inputs, as the service calls it: the corpus's bootstrap
    register, the bootstrap procedures and the corpus's staff list."""
    kind, corpus = KINDS[harness.KIND_OF[sid]], harness.corpus(sid)
    state = _lab.register_bootstrap(corpus)
    register = _lab.kernel_register(state, tmp / "register")
    terms = {e["doc_id"]: e.get("terms") for e in state.entries}
    boot, store = _lab.procedures_bootstrap()
    root = root or _lab.corpus_root(corpus)
    inputs = harness.inputs(sid) | ({"sid": sid_as} if sid_as else {})
    return _lab.decide(
        kind, evidence=_lab.make_evidence(root, overlay), inputs=inputs, at=harness.at_of(sid),
        register=register, entries=boot if entries is None else entries, store=store,
        engine=engine, staff=_lab.staff(root) if staff is None else staff,
        requested_by=None if kind == "sla" else str(inputs["record"]["requested_by"]),
        policy_terms=terms.get, route_mode=route_mode,
    )  # fmt: skip


# -- decide -------------------------------------------------------------------------------------
def test_decide_s01_equals_direct_governed(engine: _lab.ReplayEngine, tmp_path: Path) -> None:
    trace: dict[str, Any] = {}
    reference = harness.reference("S01", trace)
    r = run("S01", engine, tmp_path, sid_as="DEC-0001")
    assert r.record["scenario"] == "DEC-0001"
    assert strip(r.record) == strip(reference)
    assert len(r.judgment_about) == 14 and all(r.judgment_about)
    assert r.approval_roles[0]["person_id"] == "EMP-200"
    assert r.relied == [tuple(x) for x in trace["relied"]] and r.relied
    assert all(isinstance(x, tuple) and len(x) == 2 for x in r.relied)
    assert [i["text"] for i in r.flag_items] == r.record.get("flags", [])
    assert not engine.calls.exists()  # replayed: zero live calls


def test_decide_s36_sla_equals_direct_governed(engine: _lab.ReplayEngine, tmp_path: Path) -> None:
    r = run("S36", engine, tmp_path)
    assert strip(r.record) == strip(harness.reference("S36"))
    assert {(x["kind"], x["person_id"]) for x in r.approval_roles} == {
        ("claim_decision", "EMP-602"), ("expected_actor", "EMP-604")}  # fmt: skip
    assert all(r.judgment_about)


def test_overlay_is_what_the_kernel_reads(engine: _lab.ReplayEngine, tmp_path: Path) -> None:
    seen: list[str] = []

    def drop_events(name: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        seen.append(name)
        if name != "ticket_events":
            return rows
        return [r for r in rows if r["ticket_id"] != "SR-39385"]

    reference = strip(harness.reference("S36"))
    dropped = run("S36", engine, tmp_path, overlay=drop_events)
    assert "ticket_events" in seen
    assert strip(dropped.record) != reference


def test_overlay_leaves_documents_alone() -> None:
    root = _lab.corpus_root("base")
    plain = harness.lab("kernel").Evidence(root)
    ev = _lab.make_evidence(root, lambda name, rows: [])
    assert isinstance(ev, harness.lab("kernel").Evidence)
    assert [d.raw for d in ev.docs()] == [d.raw for d in plain.docs()]
    assert ev.table("employees") == [] and plain.table("employees")


def test_route_mode_deploys_on_mismatch_route(engine: _lab.ReplayEngine, tmp_path: Path) -> None:
    """F1 on S21 (Task 1's route-mode case): a registered document on file differs from its
    registered version. Route mode sends the decision to route_to; the entries are not mutated."""
    root = harness.attacked_roots("F1")[harness.corpus("S21")]
    entries, _ = _lab.procedures_bootstrap()
    before = copy.deepcopy(entries)
    routed = run("S21", engine, tmp_path / "r", root=root, route_mode=True, entries=entries)
    assert entries == before
    assert strip(routed.record) == strip(harness.decide("S21", attack="F1", route=True))
    assert routed.record["gated_outcome"] == _lab.ROUTE_TO["discount"]
    assert "routed" in [i["code"] for i in routed.flag_items if i["routes"]]
    plain = run("S21", engine, tmp_path / "p", root=root)
    assert strip(plain.record) == strip(harness.decide("S21", attack="F1"))
    assert plain.record["gated_outcome"] != _lab.ROUTE_TO["discount"]


# -- errors -------------------------------------------------------------------------------------
def test_jev_unavailable_propagates(tmp_path: Path) -> None:
    empty = _lab.ReplayEngine([], tmp_path / "calls.jsonl", live=False, cap=0)
    with pytest.raises(_lab.JevUnavailable, match="not recorded"):
        run("S01", empty, tmp_path)


def test_no_procedure_is_cannot_decide(engine: _lab.ReplayEngine, tmp_path: Path) -> None:
    with pytest.raises(CannotDecide, match="no discount procedure is in force") as e:
        run("S01", engine, tmp_path, entries=[])
    assert type(e.value.__cause__).__name__ == "NoProcedureError"


def test_approval_conflict_is_cannot_decide(engine: _lab.ReplayEngine, tmp_path: Path) -> None:
    staff = [e for e in _lab.staff(_lab.corpus_root("base")) if e["employee_id"] != "EMP-101"]
    assert len(staff) < len(_lab.staff(_lab.corpus_root("base")))  # Sarah Chen is EMP-101
    with pytest.raises(CannotDecide, match="no staff member requested this") as e:
        run("S01", engine, tmp_path, staff=staff)
    assert type(e.value.__cause__).__name__ == "ApprovalConflict"


# -- the replay engine --------------------------------------------------------------------------
def _recorded(path: Path, state: Any, questions: dict[str, Any], response: Any) -> None:
    h = harness.lab("engine").request_hash("jev-1.13.0", state, questions)
    with path.open("a") as f:
        f.write(json.dumps({"hash": h, "response": response}) + "\n")


def test_replay_miss_raises_jev_unavailable(tmp_path: Path) -> None:
    eng = _lab.ReplayEngine([], tmp_path / "calls.jsonl", live=False, cap=0)
    assert eng.model == "jev-1.13.0"
    with pytest.raises(_lab.JevUnavailable, match=r"^not recorded: [0-9a-f]{12}$"):
        eng.ask({"x": 1}, {"q": {}})


def test_replay_hits_recordings_and_the_calls_file(tmp_path: Path) -> None:
    runs, calls = tmp_path / "runs-engine-calls.jsonl", tmp_path / "calls.jsonl"
    _recorded(runs, {"x": 1}, {"q": {}}, {"answers": {"q": "from runs"}})
    _recorded(calls, {"x": 2}, {"q": {}}, {"answers": {"q": "from calls"}})
    eng = _lab.ReplayEngine([runs], calls, live=False, cap=0)
    assert eng.ask({"x": 1}, {"q": {}}) == {"answers": {"q": "from runs"}}
    assert eng.ask({"x": 2}, {"q": {}}) == {"answers": {"q": "from calls"}}


def test_an_answer_is_a_copy(tmp_path: Path) -> None:
    """The kernel puts parts of an answer (`probabilities`) into the record, and one engine serves
    every decision: changing a record must not change the next answer."""
    runs = tmp_path / "engine-calls.jsonl"
    _recorded(runs, {"x": 1}, {"q": {}}, {"answers": {"q": {"probabilities": {"a": 0.9}}}})
    eng = _lab.ReplayEngine([runs], tmp_path / "calls.jsonl", live=False, cap=0)
    eng.ask({"x": 1}, {"q": {}})["answers"]["q"]["probabilities"]["a"] = 0.1
    assert eng.ask({"x": 1}, {"q": {}}) == {"answers": {"q": {"probabilities": {"a": 0.9}}}}


def test_replay_files_are_the_recordings_under_runs() -> None:
    files = _lab.replay_files(_lab.LAB_ROOT)
    assert files == sorted(files) and files
    assert all(f.is_relative_to(_lab.LAB_ROOT / "runs") for f in files)
    assert all("engine-calls" in f.name or "jev-calls" in f.name for f in files)


def _no_typesafe(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError("TypeSafe was constructed")


def test_live_at_cap_never_calls_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_lab._engine, "TypeSafe", _no_typesafe)
    eng = _lab.ReplayEngine([], tmp_path / "calls.jsonl", live=True, cap=0)
    with pytest.raises(_lab.JevUnavailable, match=r"live Jev cap reached \(0\)"):
        eng.ask({"x": 1}, {"q": {}})
    calls = tmp_path / "full.jsonl"  # the cap counts the calls already in the file
    _recorded(calls, {"x": 2}, {"q": {}}, {})
    _recorded(calls, {"x": 3}, {"q": {}}, {})
    eng = _lab.ReplayEngine([], calls, live=True, cap=2)
    with pytest.raises(_lab.JevUnavailable, match=r"live Jev cap reached \(2\)"):
        eng.ask({"x": 1}, {"q": {}})


class FakeJev:
    """Stands in for TypeSafe's engine: answers locally, and counts what it was asked."""

    model = "jev-1.13.0"

    def __init__(self) -> None:
        self.asked = 0

    def ask(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        self.asked += 1
        return {"answers": {"q": state}}


def test_live_under_cap_records_through_recorder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeJev()
    built: list[str] = []

    def typesafe(model: str) -> FakeJev:
        built.append(model)
        return fake

    monkeypatch.setattr(_lab._engine, "TypeSafe", typesafe)
    calls = tmp_path / "calls.jsonl"
    eng = _lab.ReplayEngine([], calls, live=True, cap=1)
    assert built == []  # lazily, on the first live call
    assert eng.ask({"x": 1}, {"q": {}}) == {"answers": {"q": {"x": 1}}}
    assert built == ["jev-1.13.0"] and fake.asked == 1
    assert len(calls.read_text().splitlines()) == 1
    assert eng.ask({"x": 1}, {"q": {}}) == {"answers": {"q": {"x": 1}}}  # now recorded
    with pytest.raises(_lab.JevUnavailable, match=r"live Jev cap reached \(1\)"):
        eng.ask({"x": 2}, {"q": {}})
    assert fake.asked == 1


# -- the small helpers --------------------------------------------------------------------------
def test_corpus_root() -> None:
    assert _lab.corpus_root("base") == _lab.LAB_ROOT / "dataset/evidence"
    assert _lab.corpus_root("missing-contract-evidence") == (
        _lab.LAB_ROOT / "dataset/evidence-variants/missing-contract-evidence")  # fmt: skip


def test_staff_and_pass_up() -> None:
    staff = _lab.staff(_lab.corpus_root("base"))
    assert {"EMP-200", "EMP-300"} <= {e["employee_id"] for e in staff}
    up = _lab.pass_up(staff, "EMP-200", "VP Sales")
    assert up is not None and up["employee_id"] == "EMP-300"


def test_credit_tier() -> None:
    ev = _lab.make_evidence(_lab.corpus_root("base"), same)
    assert _lab.credit_tier(ev, {"erp_customer_id": "C-1001"}) == "Strategic"
    assert _lab.credit_tier(ev, {"erp_customer_id": "C-0000"}) is None


def test_procedures_bootstrap() -> None:
    entries, store = _lab.procedures_bootstrap()
    assert {e["proc_id"] for e in entries} == {"PROC-DISCOUNT", "PROC-CREDIT", "PROC-SLA"}
    assert all((store / f"{e['sha256']}.yaml").exists() for e in entries)


def test_register_bootstrap_and_kernel_register(tmp_path: Path) -> None:
    state = _lab.register_bootstrap("base")
    register = _lab.kernel_register(state, tmp_path)
    assert len(register.entries) == 17 == state.version
    assert all((tmp_path / "store" / f"{e['sha256']}.md").exists() for e in register.entries)


def test_register_rules_are_the_kernels() -> None:
    """`entry_in_force` and `revoked_on_or_before` call the kernel's own rules (window, RR-12
    revocation, supersedes), so the service's choice can't drift from the kernel's."""
    kernel = harness.lab("kernel")
    entries = _lab.register_bootstrap("base").entries
    for kind in ("pricing_policy", "credit_policy"):
        mine = [e for e in entries if e["kind"] == kind]
        for on in (date(2025, 9, 23), date(2026, 9, 23), date(2027, 2, 1)):
            assert _lab.entry_in_force(mine, on) is kernel.entry_in_force(mine, on, [])
    revoked = {"doc_id": "X", "effective_from": "2026-01-01", "effective_to": None,
               "revoked_on": "2026-09-01"}  # fmt: skip
    days = (date(2026, 8, 31), date(2026, 9, 1), date(2026, 9, 2))
    assert [_lab.revoked_on_or_before(revoked, d) for d in days] == [False, True, True]
    assert [_lab.revoked_on_or_before(revoked, d) for d in days] == [
        not kernel.in_window(revoked, d) for d in days]  # fmt: skip
    assert not _lab.revoked_on_or_before({"doc_id": "Y", "revoked_on": None}, days[1])


def test_route_to() -> None:
    assert _lab.ROUTE_TO == {"discount": "REQUEST_EVIDENCE", "credit": "REQUEST_EVIDENCE",
                             "sla": "CANNOT_DECIDE"}  # fmt: skip
