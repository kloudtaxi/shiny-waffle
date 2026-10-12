"""Procedures (B-06 Task 18; spec §7.3; contract §4.5 at 30977cd): a new procedure version is a
register change of kind `procedure` through the same two steps, with the people rules (the owner
comes from the decision type) and ADM (`build_procedures.register`: an admitted report for this
exact text). Approved versions go to the org's procedure store, and decisions run the version in
force on their date. A procedure approval never moves the document register (ruling R50).

Admission reports are read from `runs/2026-10-06-procedures-governed/admission/` here, by the
tests only; the service gets each one as JSON inside the change. Jev is replay only."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from owm_service import _lab
from owm_service.changes import ChangeBody
from owm_service.config import load_settings
from owm_service.decisions import Decisions
from owm_service.errors import CannotDecide, NotFound, Refused
from owm_service.models import Actor, DecisionRecord, DecisionRequest
from owm_service.org import Org
from owm_service.procedures import get_procedure, list_procedures
from owm_service.register_queue import RegisterQueue
from owm_service.register_view import view
from owm_service.sessions import Sessions

from ._registrar import CHECK

LAB = Path(__file__).resolve().parents[2]
SPECS = LAB / "lab/owm_kernel/specs"
ADMISSION = LAB / "runs/2026-10-06-procedures-governed/admission"
SLA_V2_SHA = "71ff8a9ddb26a14183bc5b9c3215bfd46152749b93c33b63ef7f15715482ff96"
TICKET = "SR-39385"  # S36's ticket: P3 recorded its SLA v2 calls at 2026-10-07
LATER = "2026-10-07T09:00:00-05:00"


def no_sla_v2(e: dict[str, Any]) -> bool:
    """The brief's filter: the procedure bootstrap without PROC-SLA v2."""
    return not (e["proc_id"] == "PROC-SLA" and e["version"] == 2)


# -- fixtures and builders ----------------------------------------------------------------------
OrgAt = Callable[..., Org]


@pytest.fixture
def org_at(tmp_path: Path) -> OrgAt:
    """A fresh org at `clock`, in its own state dir, with an optional bootstrap filter."""
    made = 0

    def make(clock: str = "2026-09-23T09:00:00-05:00", **kw: Any) -> Org:
        nonlocal made
        made += 1
        env = {"OWM_STATE_DIR": str(tmp_path / f"org{made}"), "OWM_CLOCK": clock}
        return Org(load_settings(env), **kw)

    return make


@pytest.fixture
def filtered(org_at: OrgAt) -> Org:
    return org_at(procedure_filter=no_sla_v2)


def person(org: Org, emp: str) -> Actor:
    return Sessions(org).open_person(emp)[1]


def agent(org: Org) -> Actor:
    return Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")[1]


def spec(name: str) -> str:
    return (SPECS / name).read_text()


def report(name: str) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads((ADMISSION / name).read_text())
    return loaded


def procedure(
    proc_id: str = "PROC-SLA", decision_type: str = "sla", version: int = 2, *,
    text: str = "sla_agent.yaml", admission: str = "sla_agent.json",
    effective_from: str = "2026-10-06", submit: bool = True, **over: Any,
) -> ChangeBody:  # fmt: skip
    """A procedure version as a register change (contract §4.5): `text` and `admission` name a
    spec under `lab/owm_kernel/specs/` and its report."""
    raw = {"action": "register", "kind": "procedure", "base_version": 17, "submit": submit,
           "proc_id": proc_id, "decision_type": decision_type, "version": version,
           "effective_from": effective_from, "effective_to": None, "text": spec(text),
           "report": report(admission)}  # fmt: skip
    return ChangeBody.model_validate(raw | over)


def refused(fn: Callable[[], Any]) -> Refused:
    with pytest.raises(Refused) as e:
        fn()
    return e.value


def ask_sla(org: Org, ticket: str = TICKET) -> DecisionRecord:
    req = DecisionRequest.model_validate({"decision_type": "sla", "subject": {"ticket": ticket}})
    return Decisions(org).ask(person(org, "EMP-602"), req)


def kernel(org: Org, rec: DecisionRecord) -> dict[str, Any]:
    return Decisions(org).kernel_record(rec.decision_id, 1)


def later(org: Org) -> None:
    org.clock.set(datetime.fromisoformat(LATER), None)


def register_sla_v2(org: Org) -> str:
    """Hannah (Customer Support) submits sla_agent.yaml as PROC-SLA v2 from 2026-10-06 with its
    admission report; Marcus approves. The change id."""
    q = RegisterQueue(org)
    pending = q.submit_new(person(org, "EMP-601"), procedure())
    q.approve(person(org, "EMP-602"), pending.change_id)
    return pending.change_id


# -- the bootstrap ------------------------------------------------------------------------------
def test_bootstrap_procedures(org: Org) -> None:
    assert {p["id"] for p in list_procedures(org)} == {"PROC-DISCOUNT", "PROC-CREDIT", "PROC-SLA"}


def test_sla_version_by_date(org_at: OrgAt) -> None:
    """The bootstrap's P3 case: SLA v1 until 2026-10-05, v2 (sla_agent.yaml) from 2026-10-06."""
    early, late = org_at(), org_at(LATER)
    assert ask_sla(early).decided_by.procedure.version == 1
    v2 = ask_sla(late)
    assert (v2.decided_by.procedure.version, v2.decided_by.procedure.sha256) == (2, SLA_V2_SHA)
    assert get_procedure(early, "PROC-SLA")["in_force"] == 1
    assert get_procedure(late, "PROC-SLA")["in_force"] == 2
    for org in (early, late):  # replay only: nothing went to Jev
        assert not org.engine.calls.exists()


def test_procedure_reads_have_v11s_version_fields(org: Org) -> None:
    sla = get_procedure(org, "PROC-SLA")
    assert (sla["proc_id"], sla["decision_type"], sla["owning_function"]) == (
        "PROC-SLA", "sla", "Customer Support")  # fmt: skip
    v1, v2 = sla["versions"]
    assert (v1["version"], v1["status"], v2["version"], v2["status"]) == (
        1, "in_force", 2, "scheduled")  # fmt: skip
    assert v2["sha256"] == SLA_V2_SHA
    assert v2["author"] == {"kind": "agent", "name": (
        "proposed by an agent (the SLA author subagent); revision 1 after the admission gate's "
        "report (runs/2026-10-06-spec-admission/)")}  # fmt: skip
    assert v2["registered_by"] == {"id": "EMP-601", "name": "Hannah Lindqvist",
                                   "title": "Support Escalation Manager",
                                   "on": "2026-10-06"}  # fmt: skip
    assert v2["approved_by"] == {"id": "EMP-602", "name": "Marcus Adeyemi",
                                 "title": "Director of Customer Support",
                                 "on": "2026-10-06"}  # fmt: skip
    assert v2["admission"]["verdict"] == "admitted"
    assert set(v2["admission"]["gates"]) == {"A", "B", "C"}
    assert all(g["passed"] for g in v2["admission"]["gates"].values())
    assert v2["change"] is None
    assert get_procedure(org, "PROC-DISCOUNT")["versions"][0]["author"]["kind"] == "person"
    with pytest.raises(NotFound):
        get_procedure(org, "PROC-NOPE")


# -- the refusals (run_governed.py P1) ----------------------------------------------------------
def test_not_admitted_is_adm(org: Org) -> None:
    """credit_agent.yaml failed gate C (P1): ADM, at submit and in a draft's checks."""
    q = RegisterQueue(org)
    body = procedure("PROC-CREDIT", "credit", text="credit_agent.yaml",
                     admission="credit_agent.json", effective_from="2026-10-10")  # fmt: skip
    r = refused(lambda: q.submit_new(person(org, "EMP-401"), body))
    assert (r.status, r.refusals[0].rule) == (422, "ADM")
    assert r.refusals[0].detail == "PROC-CREDIT-v2.yaml: not admitted (failed gate C)"
    draft = q.draft(agent(org), body.model_copy(update={"submit": False}))
    assert draft.state == "draft"
    assert [(c.rule, c.detail) for c in draft.checks or []] == [
        ("ADM", "PROC-CREDIT-v2.yaml: not admitted (failed gate C)")]  # fmt: skip


def test_a_report_for_another_text_is_adm(filtered: Org) -> None:
    q = RegisterQueue(filtered)
    body = procedure(admission="sla.json")  # sla.yaml's report, with sla_agent.yaml's text
    r = refused(lambda: q.submit_new(person(filtered, "EMP-601"), body))
    assert (r.refusals[0].rule, r.refusals[0].detail) == (
        "ADM", "PROC-SLA-v2.yaml: the admission report is not for this exact text")  # fmt: skip


def test_a_text_without_registered_kinds_is_adm(org: Org) -> None:
    """sla.yaml was admitted with the gate's standard mapping applied (the lab registers it with
    that mapping as its deployment). A change can't carry a deployment, so the service refuses
    a text that doesn't declare its own registered kinds rather than run it unlike admitted."""
    q = RegisterQueue(org)
    body = procedure(version=3, text="sla.yaml", admission="sla.json",
                     effective_from="2026-11-01")  # fmt: skip
    r = refused(lambda: q.submit_new(person(org, "EMP-601"), body))
    assert r.refusals[0].rule == "ADM"
    assert "declares no registered_kinds" in r.refusals[0].detail


def test_approver_is_registrar_is_rr4(filtered: Org) -> None:
    q = RegisterQueue(filtered)
    hannah = person(filtered, "EMP-601")
    pending = q.submit_new(hannah, procedure())
    assert [p.id for p in pending.approvers] == ["EMP-602", "EMP-300"]
    r = refused(lambda: q.approve(hannah, pending.change_id))
    assert (r.status, r.refusals[0].rule) == (422, "RR-4")
    assert "the approver is the submitter" in r.refusals[0].detail
    assert q.get(pending.change_id).state == "pending"


def test_agent_cannot_approve(filtered: Org) -> None:
    q = RegisterQueue(filtered)
    pending = q.submit_new(person(filtered, "EMP-601"), procedure())
    r = refused(lambda: q.approve(agent(filtered), pending.change_id))
    assert (r.status, r.refusals[0].rule) == (422, "RR-2")
    r = refused(lambda: q.submit_new(agent(filtered), procedure()))
    assert r.refusals[0].rule == "RR-2"


def test_the_owner_comes_from_the_decision_type(filtered: Org) -> None:
    """RR-3 for a submitter outside the decision type's owner; RR-4 for an approver who isn't its
    head or an Executive."""
    q = RegisterQueue(filtered)
    r = refused(lambda: q.submit_new(person(filtered, "EMP-101"), procedure()))  # Sarah, Sales
    assert r.refusals[0].rule == "RR-3"
    assert "Customer Support, which owns sla_schedule" in r.refusals[0].detail
    pending = q.submit_new(person(filtered, "EMP-601"), procedure())
    r = refused(lambda: q.approve(person(filtered, "EMP-200"), pending.change_id))  # Michael
    assert r.refusals[0].rule == "RR-4"


def test_versions_are_numbered_in_order(org: Org) -> None:
    """RR-5, as the registrar orders it (an unknown kind before the people rules, the rest
    after): an unknown decision type, a version already registered, a gap, or a procedure that
    belongs to another decision type."""
    q = RegisterQueue(org)
    cases = [
        ("EMP-601", procedure(decision_type="refund"), "no decision type 'refund'"),
        ("EMP-601", procedure(), "PROC-SLA v2 is registered already; the next version is 3"),
        ("EMP-601", procedure(version=4), "PROC-SLA's next version is 3, not 4"),
        ("EMP-401", procedure(decision_type="credit"), "PROC-SLA is a sla procedure, not credit"),
    ]
    for emp, body, detail in cases:
        r = refused(lambda emp=emp, body=body: q.submit_new(person(org, emp), body))  # type: ignore[misc]
        assert r.refusals[0].rule == "RR-5", detail
        assert detail in r.refusals[0].detail


def test_a_procedure_body_takes_its_own_fields() -> None:
    with pytest.raises(ValueError, match="needs proc_id"):
        ChangeBody.model_validate({"action": "register", "kind": "procedure", "base_version": 17,
                                   "submit": True, "text": "x", "effective_from": "2026-10-06",
                                   "decision_type": "sla", "version": 2, "report": {}})  # fmt: skip
    with pytest.raises(ValueError, match="takes no doc_id"):
        procedure(doc_id="PROC-SLA")
    with pytest.raises(ValueError, match="takes no proc_id"):
        ChangeBody.model_validate({"action": "register", "kind": "credit_policy",
                                   "base_version": 17, "submit": True, "doc_id": "X",
                                   "effective_from": "2027-01-01",
                                   "proc_id": "PROC-X"})  # fmt: skip


# -- the happy path -----------------------------------------------------------------------------
def test_registering_an_admitted_version(filtered: Org, org_at: OrgAt) -> None:
    """Hannah submits sla_agent.yaml as PROC-SLA v2 from 2026-10-06 with its admitted report;
    Marcus approves. An SLA ask at 2026-10-07 is stamped v2 and replays at $0: the kernel's record
    equals the one the bootstrap's own v2 gives (P3's case)."""
    gap = org_at(LATER, procedure_filter=no_sla_v2)
    with pytest.raises(CannotDecide, match="no sla procedure is in force on 2026-10-07"):
        ask_sla(gap)  # without v2, nothing governs an SLA decision from 2026-10-06
    change = register_sla_v2(filtered)
    assert RegisterQueue(filtered).get(change).state == "approved"
    later(filtered)
    rec = ask_sla(filtered)
    assert (rec.decided_by.procedure.id, rec.decided_by.procedure.version,
            rec.decided_by.procedure.sha256) == ("PROC-SLA", 2, SLA_V2_SHA)  # fmt: skip
    mine = kernel(filtered, rec)
    assert not [f for f in mine.get("flags", []) if str(f).startswith("incident:")]
    assert not filtered.engine.calls.exists()  # replay only: $0
    reference = org_at(LATER)  # the bootstrap's PROC-SLA v2
    assert mine == kernel(reference, ask_sla(reference))
    v2 = get_procedure(filtered, "PROC-SLA")["versions"][1]
    assert (v2["status"], v2["change"], v2["sha256"]) == ("in_force", change, SLA_V2_SHA)
    assert v2["registered_by"]["id"] == "EMP-601" and v2["approved_by"]["id"] == "EMP-602"
    assert v2["registered_by"]["on"] == v2["approved_by"]["on"] == "2026-09-23"
    assert v2["author"] == {"kind": "person", "name": "Hannah Lindqvist"}
    assert v2["admission"]["report"] == change and v2["admission"]["verdict"] == "admitted"
    assert v2["admission"]["gates"]["A"] == {"passed": True, "detail": "10 of 10 held"}


def test_the_approved_text_runs_from_the_orgs_store(filtered: Org) -> None:
    """The store holds the approved text by its fingerprint, and the specs directory the kernel
    checks holds it under the version's file name; without that directory the kernel would flag
    every decision (`incident: the procedure file … differs`)."""
    register_sla_v2(filtered)
    entries, store = filtered.procedures()
    v2 = next(e for e in entries if (e["proc_id"], e["version"]) == ("PROC-SLA", 2))
    assert store == filtered.dir / "procedure-store"
    assert (store / f"{SLA_V2_SHA}.yaml").read_text() == spec("sla_agent.yaml")
    assert v2["file"] == "PROC-SLA-v2.yaml"
    assert (filtered.procedure_specs / v2["file"]).read_text() == spec("sla_agent.yaml")
    later(filtered)
    prep = _prepared(filtered)
    without = _lab.decide(
        "sla", evidence=filtered.evidence, inputs=prep.inputs, at=prep.at,
        register=filtered.kernel_register(), entries=entries, store=store,
        engine=filtered.engine, staff=filtered.evidence.table("employees"), requested_by=None,
        policy_terms=filtered.policy_terms, route_mode=False,
    )  # fmt: skip
    assert any(str(f).startswith("incident: the procedure file PROC-SLA-v2.yaml differs")
               for f in without.record["flags"])  # fmt: skip


def test_an_agents_draft_keeps_its_author(filtered: Org) -> None:
    q = RegisterQueue(filtered)
    draft = q.draft(agent(filtered), procedure(submit=False))
    assert (draft.state, draft.checks) == ("draft", [])
    assert {p.id for p in q.waiting_on(draft.change_id)} == _support(filtered)
    q.submit(person(filtered, "EMP-601"), draft.change_id, 17)
    q.approve(person(filtered, "EMP-300"), draft.change_id)  # David, the Executive
    v2 = get_procedure(filtered, "PROC-SLA")["versions"][1]
    assert v2["author"] == {"kind": "agent", "name": "Deal Desk Agent"}
    assert v2["approved_by"]["id"] == "EMP-300"


def test_the_change_reads_as_a_register_change(filtered: Org) -> None:
    """In the contract's `RegisterChange`: kind `procedure`, the version as its doc_id, the
    procedure's fields as terms, and the diff against the version it supersedes."""
    q = RegisterQueue(filtered)
    c = q.submit_new(person(filtered, "EMP-601"), procedure())
    assert (c.kind, c.doc_id, c.sha256, c.effective_from, c.effective_to) == (
        "procedure", "PROC-SLA v2", SLA_V2_SHA, "2026-10-06", None)  # fmt: skip
    assert c.terms == {"proc_id": "PROC-SLA", "decision_type": "sla", "version": 2}
    assert [r.model_dump() for r in c.relations or []] == [
        {"type": "supersedes", "target": "PROC-SLA v1"}]  # fmt: skip
    assert {d.key: (d.was, d.now) for d in c.diff} == {
        "effective_from": ("2025-01-01", "2026-10-06"),
        "effective_to": ("2026-10-05", None),
        "sha256": ("5e45743925ab1291a7be299229a9c1aa5d0facbf8f8888e29ee3def28b895b2b",
                   SLA_V2_SHA),
    }  # fmt: skip


def test_approved_versions_survive_a_restart(filtered: Org) -> None:
    register_sla_v2(filtered)
    again = Org(filtered.settings, procedure_filter=no_sla_v2)
    assert [v["version"] for v in get_procedure(again, "PROC-SLA")["versions"]] == [1, 2]
    later(again)
    assert ask_sla(again).decided_by.procedure.version == 2


# -- the document register is untouched (ruling R50) --------------------------------------------
def test_a_procedure_approval_leaves_the_document_register_alone(filtered: Org) -> None:
    q = RegisterQueue(filtered)
    before = filtered.register_state()
    version, entries = before.version, [dict(e) for e in before.entries]
    credit = q.submit_new(person(filtered, "EMP-401"), _credit_2027())  # pending throughout
    register_sla_v2(filtered)
    after = filtered.register_state()
    assert (after.version, after.entries) == (version, entries)
    assert view(filtered, None).version == version
    approved = q.approve(person(filtered, "EMP-402"), credit.change_id)  # no RR-13
    assert approved.state == "approved"
    assert filtered.register_state().version == version + 1


def test_coverage_names_the_version_decisions_run(org_at: OrgAt) -> None:
    """Two versions open at once (v1 has no end): decisions run the higher one
    (`governed.in_force`), and the register's coverage and the procedure read say so."""
    org = org_at()
    q = RegisterQueue(org)
    pending = q.submit_new(person(org, "EMP-401"), procedure(
        "PROC-CREDIT", "credit", text="credit_v3.yaml", admission="credit_v3.json",
        effective_from="2026-10-01"))  # fmt: skip
    q.approve(person(org, "EMP-402"), pending.change_id)
    org.clock.set(datetime.fromisoformat("2026-10-02T09:00:00-05:00"), None)
    credit = next(c for c in view(org, None).coverage if c.decision_type == "credit")
    assert credit.procedure is not None and credit.procedure.version == 2
    read = get_procedure(org, "PROC-CREDIT")
    assert read["in_force"] == 2
    assert [v["status"] for v in read["versions"]] == ["superseded", "in_force"]


# -- helpers that need the module under test ----------------------------------------------------
def _prepared(org: Org) -> Any:
    from owm_service.prepare import prepare

    row = org.sor.row("service_tickets", TICKET)
    return prepare(org, "sla", TICKET, row, {}, None, org.clock.now())


def _support(org: Org) -> set[str]:
    return {e for e, r in RegisterQueue(org).staff.rows.items()
            if r["department"] == "Customer Support"}  # fmt: skip


def _credit_2027() -> ChangeBody:
    fields = {k: v for k, v in CHECK.credit_2027().items()
              if k not in {"submit_by", "approve_by", "file"}}  # fmt: skip
    return ChangeBody.model_validate(fields | {"text": CHECK.text_2027_credit(), "submit": True})
