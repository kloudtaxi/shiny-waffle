"""Asking for a decision (B-06 Task 10; spec §6.1-6.3 and §6.8): version 1, decided on the system
of record's figures, with input conflicts, approvals as people, actions, basis and register_used.
Replay only. S22's v1 must equal the contract's example (`contract/s22.example.json`, export `v1`)
on every field the kernel and the service decide; times and ids are illustrative there."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from owm_service import _lab
from owm_service.assemble import findings, flag_about, flags, judgments
from owm_service.conditions import conflict_condition, input_conflicts
from owm_service.config import load_settings
from owm_service.decisions import Decisions
from owm_service.errors import CannotDecide, NotFound, Refused
from owm_service.events import Event, ExecutionRow
from owm_service.models import (
    Actor,
    CreditFindings,
    DecisionRecord,
    DecisionRequest,
    DecisionType,
    DiscountFindings,
    PersonRef,
    SlaFindings,
)
from owm_service.org import Org
from owm_service.people import People
from owm_service.sessions import Sessions
from owm_service.sor import BASIS_FIELDS
from owm_service.state import derive_state, is_live

from . import harness

LAB = Path(__file__).resolve().parents[2]
EXAMPLE: dict[str, Any] = json.loads(
    (LAB / "lab/owm_service/contract/s22.example.json").read_text()
)
SARAH_REF = {"id": "EMP-101", "name": "Sarah Chen", "title": "Enterprise Account Executive",
             "function": "Sales"}  # fmt: skip


# -- fixtures and helpers -----------------------------------------------------------------------
@pytest.fixture
def sarah(org: Org) -> Actor:  # overrides conftest's plain-dict Sarah for this module
    return Sessions(org).open_person("EMP-101")[1]


@pytest.fixture
def dealdesk(org: Org) -> Actor:
    return Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")[1]


@pytest.fixture
def marcus(org: Org) -> Actor:
    return Sessions(org).open_person("EMP-602")[1]


@pytest.fixture
def org_live_off(tmp_path: Path) -> Org:
    return Org(load_settings({"OWM_STATE_DIR": str(tmp_path / "state"), "OWM_JEV": "replay"}))


def example(name: str) -> dict[str, Any]:
    out: dict[str, Any] = EXAMPLE[name]
    return out


def dump(m: BaseModel) -> dict[str, Any]:
    """As the service serves it (ruling R13): absent `?:` fields stay absent."""
    return m.model_dump(mode="json", exclude_unset=True)


def strip_about(j: dict[str, Any]) -> dict[str, Any]:
    """A judgment without `about`, which the example leaves null (§12.4), and with only the chosen
    option's probability: the example writes each distribution as `{choice: p, unclear: 1 - p}`,
    while the kernel reports every option it asked about."""
    out = {k: v for k, v in j.items() if k not in ("about", "probabilities")}
    if j["form"] == "choice":
        out["p_choice"] = j["probabilities"][j["choice"]]
    return out


def body(kind: str, subject: str, submitted: dict[str, Any] | None) -> DecisionRequest:
    key = "ticket" if kind == "sla" else "request_id"
    raw: dict[str, Any] = {"decision_type": kind, "subject": {key: subject}}
    if submitted is not None:
        raw["submitted"] = submitted
    return DecisionRequest.model_validate(raw)


def ask(
    org: Org, actor: Actor, subject: str, submitted: dict[str, Any] | None, kind: str = "discount"
) -> DecisionRecord:
    return Decisions(org).ask(actor, body(kind, subject, submitted))


def decision_events(org: Org) -> list[Event]:
    return [e for e in org.log.read(org.org_id) if e.kind.startswith("decision.")]


def seed(org: Org, rid: str, **fields: str) -> None:
    """A copy of DR-9001 under `rid`, with `fields` changed, inserted through the overlay."""
    row = dict(org.sor.row("discount_requests", "DR-9001") or {})
    with org.log.transaction() as tx:
        org.sor.insert(tx, "discount_requests", {**row, "request_id": rid, **fields},
                       actor={"kind": "person", "id": "EMP-101"}, at=org.clock.now())  # fmt: skip


def s22_kernel(org: Org) -> _lab.KernelResult:
    """The kernel's result on DR-9001 as the CRM holds it, as the service asks for it."""
    row = org.sor.row("discount_requests", "DR-9001")
    assert row is not None
    entries, store = org.procedures()
    as_of = datetime(2026, 9, 23).date()
    return _lab.decide(
        "discount", evidence=org.evidence, inputs={"sid": "pending", "record": row, "as_of": as_of},
        at=as_of, register=org.kernel_register(), entries=entries, store=store, engine=org.engine,
        staff=org.evidence.table("employees"), requested_by=row["requested_by"],
        policy_terms=org.policy_terms, route_mode=False,
    )  # fmt: skip


# -- S22: the contract's example ----------------------------------------------------------------
def test_s22_v1_matches_the_contract_example(org: Org, dealdesk: Actor) -> None:
    v1 = Decisions(org).ask(dealdesk, body("discount", "DR-9001", {"requested_discount": 0.08}))
    ex = example("v1")
    for k in ("decision_type", "subject", "submitted", "requested_by", "as_of", "outcome",
              "gated_outcome", "routed", "findings", "conditions", "approvals", "actions",
              "state"):  # fmt: skip
        assert dump(v1)[k] == ex[k], k
    assert [strip_about(j) for j in dump(v1)["judgments"]] == [
        strip_about(j) for j in ex["judgments"]
    ]
    assert v1.decided_by.procedure.sha256 == ex["decided_by"]["procedure"]["sha256"]
    assert (v1.decided_by.judgments, v1.decided_by.uncertain) == (14, 0)
    assert v1.flags == []
    assert (v1.decision_id, v1.version, v1.previous, v1.executed) == ("DEC-0001", 1, None, [])
    assert v1.actor == dealdesk
    assert v1.floor is None  # Task 11 sets the floor


def test_s22_judgments_say_what_they_are_about(org: Org, dealdesk: Actor) -> None:
    v1 = Decisions(org).ask(dealdesk, body("discount", "DR-9001", {"requested_discount": 0.08}))
    about = [j.about for j in v1.judgments]
    assert about[:4] == ["Enterprise Account Executives", "VP Sales", "DR-9001", "ACME-MFG-2025"]
    assert all(about)
    assert v1.judgments[4].form == "yes_no" and v1.judgments[4].p_yes == 0.98


def test_s22_is_stored_whole_and_read_back(org: Org, dealdesk: Actor) -> None:
    d = Decisions(org)
    v1 = d.ask(dealdesk, body("discount", "DR-9001", {"requested_discount": 0.08}))
    assert d.get(v1.decision_id) == v1 == d.get(v1.decision_id, 1)
    assert Decisions(Org(org.settings)).get(v1.decision_id) == v1  # a restart reads the log
    assert d.list() == [v1] and d.list(decision_type="discount", subject="DR-9001") == [v1]
    assert d.list(state="ready") == [] and d.list(decision_type="sla") == []
    (ev,) = d.events(v1.decision_id)
    assert (ev.kind, ev.stream, ev.actor) == ("decision.versioned", "DR-9001", dump(dealdesk))
    assert set(ev.payload) == {"version", "kernel", "kernel_extra"}
    fixed = ev.payload["version"]
    assert "state" not in fixed and "executed" not in fixed  # derived on read
    assert fixed["floor"] is None and fixed["previous"] is None  # required-nullable: present
    assert "ticket" not in fixed["subject"] and "related" not in str(fixed["flags"])  # R13
    assert set(ev.payload["kernel_extra"]) == {"judgment_about", "flag_items", "approval_roles",
                                               "relied"}  # fmt: skip
    k = d.kernel_record(v1.decision_id, 1)
    assert k == ev.payload["kernel"] and k["authority"]["approver"] == "Michael Torres"
    assert k["judgments"][4]["noul"] == 0.98  # the kernel's own shape, not the contract's
    with pytest.raises(NotFound):
        d.get("DEC-9999")
    with pytest.raises(NotFound):
        d.get(v1.decision_id, 2)
    with pytest.raises(NotFound):
        d.kernel_record(v1.decision_id, 2)
    with pytest.raises(NotFound):
        d.events("DEC-9999")
    with pytest.raises(ValueError, match="colour"):
        d.list(colour="red")


def test_s22_basis_and_register_used(org: Org, dealdesk: Actor) -> None:
    v1 = Decisions(org).ask(dealdesk, body("discount", "DR-9001", {"requested_discount": 0.08}))
    (rec,) = v1.basis.records
    row = org.sor.row("discount_requests", "DR-9001")
    assert row is not None
    assert (rec.system, rec.table, rec.id) == ("crm", "discount_requests", "DR-9001")
    assert rec.fields == {c: row[c] for c in BASIS_FIELDS["discount"]}
    assert rec.fields["requested_discount_pct"] == "15.0"
    assert (rec.read_at, rec.last_changed) == (v1.requested_at, None)
    reg = {e["doc_id"]: e for e in org.register_state().entries}
    docs = [(x.doc_id, x.registered) for x in v1.basis.documents]
    assert docs == [("ACME-MFG-2025", True), ("EXC-ACME-NS500-15", True),
                    ("PRICING-POLICY-2026", True)]  # deduplicated, the kernel's order  # fmt: skip
    assert all(x.sha256 == reg[x.doc_id]["sha256"] for x in v1.basis.documents)
    assert [(u.doc_id, u.status, u.file_matches) for u in v1.register_used] == [
        (doc, "in_force", True) for doc, _ in docs]  # fmt: skip
    assert v1.requested_at <= v1.decided_at


def test_basis_last_changed_names_the_editor(org: Org, sarah: Actor, dealdesk: Actor) -> None:
    def edit(fields: dict[str, str], actor: Actor) -> datetime:
        at = org.clock.now()
        with org.log.transaction() as tx:
            org.sor.edit(tx, "discount_requests", "DR-9001", fields, actor=dump(actor), at=at)
        return at

    edit({"list_value_usd": "250000"}, sarah)  # not a basis field
    first = Decisions(org).ask(sarah, body("discount", "DR-9001", None))
    assert first.basis.records[0].last_changed is None
    # a basis field, rewritten as it was, so the kernel's inputs (and the replay) don't move
    at = edit({"request_date": "2026-09-23"}, dealdesk)
    with org.log.transaction() as tx:  # free the subject for a second decision
        org.log.append(tx, at=org.clock.now(), org=org.org_id, stream="DR-9001",
                       kind="decision.withdrawn", actor=None,
                       payload={"decision_id": first.decision_id, "version": 1})  # fmt: skip
    changed = ask(org, sarah, "DR-9001", None).basis.records[0].last_changed
    assert changed is not None and changed.at == at.isoformat()
    assert changed.by is not None and changed.by.id == "EMP-101"  # the agent's principal


# -- the record wins over the submission -------------------------------------------------------
def test_s25_has_no_condition(org: Org, sarah: Actor) -> None:
    v1 = ask(org, sarah, "DR-9001", {})
    assert v1.conditions == [] and v1.submitted is not None and dump(v1)["submitted"] == {}
    assert v1.state == "awaiting_approval"


def test_nothing_submitted_is_null(org: Org, sarah: Actor) -> None:
    v = ask(org, sarah, "CR-9201", None, "credit")
    assert v.submitted is None and dump(v)["submitted"] is None and v.conditions == []
    assert v.state == "awaiting_approval"


def test_s23_decides_on_the_crm_date(org: Org, sarah: Actor) -> None:
    v1 = ask(org, sarah, "DR-9001", {"request_date": "2025-09-23"})
    assert isinstance(v1.findings, DiscountFindings) and v1.findings.authority is not None
    assert v1.as_of == "2026-09-23" and v1.findings.authority.policy == "PRICING-POLICY-2026"
    assert [c.field for c in v1.conditions] == ["request_date"]
    assert v1.conditions[0].what == (
        "Confirm the request date on DR-9001: submitted 2025-09-23, the CRM says 2026-09-23. "
        "The decision is on the CRM's 2026-09-23.")  # fmt: skip
    assert v1.outcome == "APPROVE_WITH_AUTHORIZATION"


def test_s24_status_conflict(org: Org, sarah: Actor) -> None:
    v1 = ask(org, sarah, "DR-9001", {"status": "Approved"})
    (c,) = v1.conditions
    assert (c.id, c.field, c.submitted, c.on_record) == ("c1", "status", "Approved",
                                                         "Pending Approval")  # fmt: skip
    assert [p.id for p in c.who] == ["EMP-101"] and c.blocking and c.opened_in_version == 1


def test_s35_credit_conflict(org: Org, sarah: Actor) -> None:
    v1 = ask(org, sarah, "CR-9201", {"requested_limit_usd": 300000}, "credit")
    (c,) = v1.conditions
    assert (c.field, c.submitted, c.on_record) == ("requested_limit_usd", 300000, 400000.0)
    assert [p.id for p in c.who] == ["EMP-101"]
    assert c.what == ("Confirm the requested limit on CR-9201: submitted $300,000, the ERP says "
                      "$400,000. The decision is on the ERP's $400,000.")  # fmt: skip
    assert dump(v1)["subject"] == {"request_id": "CR-9201", "customer_id": "C-1001"}
    assert isinstance(v1.findings, CreditFindings)
    assert v1.findings.eligibility.model_dump() == {
        "status": "eligible", "maximum_limit_usd": 750000.0, "basis": "cap:Strategic"}  # fmt: skip
    assert v1.findings.registered == ["CREDIT-POLICY-2026 v1"]
    assert [(a.kind, a.role, a.person and a.person.id) for a in v1.approvals] == [
        ("approval", "Finance Manager", "EMP-401")]  # fmt: skip
    assert [dump(a) for a in v1.actions] == [
        {
            "action": "set_credit_limit",
            "expected_actor": None,
            "params": {"request_id": "CR-9201", "customer_id": "C-1001", "limit_usd": 400000.0},
        }
    ]
    assert v1.basis.records[0].system == "erp" and v1.state == "not_ready"


def test_s36_sla_has_claim_decision_and_no_conditions(org: Org, marcus: Actor) -> None:
    v1 = ask(org, marcus, "SR-39385", None, "sla")
    assert v1.outcome == v1.gated_outcome == "BREACH_CREDIT_OWED" and v1.conditions == []
    assert v1.requested_by is None and v1.floor is None
    assert v1.as_of == org.clock.today().isoformat()  # the service clock (contract §5.2)
    assert dump(v1)["subject"] == {"ticket": "SR-39385", "account_id": "CRM-2048",
                                   "product": "NS-500"}  # fmt: skip
    assert [(a.kind, a.role, a.person and a.person.id) for a in v1.approvals] == [
        ("claim_decision", "Director of Customer Support", "EMP-602")]  # fmt: skip
    (act,) = v1.actions
    assert (act.action, act.params) == ("issue_service_credit", {
        "ticket": "SR-39385", "account_id": "CRM-2048", "amount_usd": 4200.0})  # fmt: skip
    assert act.expected_actor is not None and act.expected_actor.id == "EMP-604"
    f = v1.findings
    assert isinstance(f, SlaFindings) and f.account_owner is not None
    assert (f.scope, f.severity, f.credit_usd, f.account_owner.id) == ("in", 1, 4200.0, "EMP-101")
    assert f.breach is not None and f.breach.restoration == "missed_band2"
    owner = next(o for o in f.obligations if o.role == "ACCOUNT_OWNER")
    assert (owner.holder, owner.holder_ref) == (None, "owner:CRM-2048")
    engage = f.obligations[0]
    assert engage.holder is not None and (engage.holder.id, engage.holder_ref) == ("EMP-601", None)
    claim = next(o for o in f.obligations if o.duty == "claim")
    assert (claim.party, claim.status, claim.holder, claim.due) == ("counterparty", "met", None,
                                                                    None)  # fmt: skip
    (rec,) = v1.basis.records
    events = [r for r in org.sor.table("ticket_events") if r["ticket_id"] == "SR-39385"]
    digest = hashlib.sha256(json.dumps(events, sort_keys=True).encode()).hexdigest()
    assert (rec.system, rec.table, rec.fields["events"]) == ("service", "service_tickets", digest)
    assert rec.fields["opened_at"] == "2026-06-16T02:14:00-05:00"
    assert v1.state == "awaiting_approval"


# -- refusals and failures ----------------------------------------------------------------------
def test_body_as_of_is_refused() -> None:
    with pytest.raises(ValidationError, match="as_of"):
        DecisionRequest.model_validate({"decision_type": "discount", "as_of": "2025-09-23",
                                        "subject": {"request_id": "DR-9001"}})  # fmt: skip


def test_dc6_second_decision(org: Org, sarah: Actor) -> None:
    first = ask(org, sarah, "DR-9001", None)
    with pytest.raises(Refused) as e:
        ask(org, sarah, "DR-9001", None)
    assert e.value.status == 409 and e.value.refusals[0].rule == "DC-6"
    assert e.value.refusals[0].existing == first.decision_id
    assert e.value.refusals[0].detail == example("secondDecision")["refusals"][0]["detail"]
    assert len(decision_events(org)) == 1
    assert ask(org, sarah, "CR-9201", None, "credit").decision_id == "DEC-0002"  # other subject


def test_unknown_subject_without_figures_is_404(org: Org, sarah: Actor) -> None:
    for subject, submitted, kind in [
        ("DR-0000", None, "discount"),
        ("DR-0000", {"requested_discount": 0.08}, "discount"),  # no customer or product
        ("DR-0000", {"customer": "CRM-2048", "requested_discount": 0.08}, "discount"),
        ("CR-0000", {"customer": "C-1001"}, "credit"),  # no requested limit
        ("SR-00000", None, "sla"),
    ]:
        with pytest.raises(NotFound) as e:
            ask(org, sarah, subject, submitted, kind)
        assert subject in e.value.what
    assert decision_events(org) == []


def test_missing_record_decides_on_the_submitted_figures(
    org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review Focus 1's other branch. The replay index has no answers for a record nobody holds,
    so the kernel is handed DR-9001's row; what the service passed it is checked separately."""
    kr = s22_kernel(org)
    seen: list[dict[str, Any]] = []

    def fake(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        seen.append(kw)
        return kr

    monkeypatch.setattr(_lab, "decide", fake)
    submitted = {"customer": "CRM-2048", "product": "NS-500", "requested_discount": 0.15}
    v1 = ask(org, sarah, "DR-0001", submitted)
    (kw,) = seen
    record = kw["inputs"]["record"]
    assert (record["request_id"], record["account_id"], record["product_sku"]) == (
        "DR-0001", "CRM-2048", "NS-500")  # fmt: skip
    assert record["requested_discount_pct"] == "15"
    assert record["requested_by"] == "sarah.chen@northstar.example"
    today = org.clock.today()
    assert record["request_date"] == today.isoformat() and kw["at"] == today
    assert v1.as_of == today.isoformat() and v1.basis.records == []
    (c,) = v1.conditions
    assert (c.id, c.source, c.field, c.on_record, c.blocking) == (
        "c1", "missing_record", None, None, True)  # fmt: skip
    assert c.submitted == submitted and [p.id for p in c.who] == ["EMP-101"]
    assert "DR-0001" in c.what and "the CRM" in c.what
    assert dump(v1)["subject"] == {"request_id": "DR-0001", "account_id": "CRM-2048",
                                   "product": "NS-500"}  # fmt: skip
    assert v1.actions[0].params["discount"] == 0.15 and v1.state == "not_ready"
    assert v1.requested_by is not None and v1.requested_by.id == "EMP-101"


@pytest.mark.parametrize(
    ("kind", "subject"),
    [("sla", {"request_id": "DR-9001"}), ("discount", {"request_id": "CR-9201"}),
     ("credit", {"request_id": "DR-9001"}), ("discount", {"ticket": "SR-39385"}),
     ("sla", {"ticket": ""})],
)  # fmt: skip
def test_subject_type_mismatch_is_422(
    org: Org, sarah: Actor, kind: str, subject: dict[str, str]
) -> None:
    req = DecisionRequest.model_validate({"decision_type": kind, "subject": subject})
    with pytest.raises(Refused) as e:
        Decisions(org).ask(sarah, req)
    assert e.value.status == 422 and e.value.refusals[0].rule == "DC-2"
    assert e.value.refusals[0].detail.startswith("subject")
    assert decision_events(org) == []


@pytest.mark.parametrize(
    "fields",
    [{"requested_by": "nobody@northstar.example"}, {"requested_discount_pct": ""},
     {"request_date": ""}, {"requested_by": ""}],
)  # fmt: skip
def test_kernel_failure_is_503_and_nothing_versioned(
    org: Org, sarah: Actor, fields: dict[str, str]
) -> None:
    """Review Focus 3 and ruling R19: a row the service can't put to the kernel, or the kernel
    can't decide, is a 503 with a `decision.failed` event, never a 500 and never a version."""
    seed(org, "DR-9199", **fields)
    with pytest.raises(CannotDecide) as e:
        ask(org, sarah, "DR-9199", None)
    assert e.value.status == 503
    (failed,) = decision_events(org)
    assert (failed.kind, failed.stream) == ("decision.failed", "DR-9199")
    assert failed.payload["reason"] == e.value.detail and failed.actor == dump(sarah)
    assert Decisions(org).list() == []


def test_jev_miss_is_503(org_live_off: Org) -> None:
    org = org_live_off
    sarah = Sessions(org).open_person("EMP-101")[1]
    seed(org, "DR-9198", justification="A justification the replay index never saw")
    with pytest.raises(CannotDecide) as e:
        ask(org, sarah, "DR-9198", None)
    assert "Jev" in e.value.detail and "not recorded" in e.value.detail
    assert [ev.kind for ev in decision_events(org)] == ["decision.failed"]
    assert not org.engine.calls.exists()  # replay only: nothing went out


def test_a_kernel_error_is_503(org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        raise CannotDecide("no discount procedure is in force")

    monkeypatch.setattr(_lab, "decide", broken)
    with pytest.raises(CannotDecide, match="no discount procedure"):
        ask(org, sarah, "DR-9001", None)
    assert [ev.kind for ev in decision_events(org)] == ["decision.failed"]


def test_a_write_that_moved_is_409(org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch) -> None:
    """The kernel runs outside the write lock; the write re-checks DC-6 and the subject's last
    event, so a decision made meanwhile wins and this one is refused (spec §5)."""
    real = _lab.decide
    nested: list[str] = []

    def racing(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        if not nested:
            nested.append("")
            nested[0] = ask(org, sarah, "DR-9001", None).decision_id
        return real(kind, **kw)

    monkeypatch.setattr(_lab, "decide", racing)
    with pytest.raises(Refused) as e:
        ask(org, sarah, "DR-9001", None)
    assert e.value.status == 409 and e.value.refusals[0].existing == nested[0] == "DEC-0001"
    assert [ev.kind for ev in decision_events(org)] == ["decision.versioned"]

    def appending(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        with org.log.transaction() as tx:
            org.log.append(tx, at=org.clock.now(), org=org.org_id, stream="CR-9201",
                           kind="decision.failed", actor=None, payload={"reason": "x"})  # fmt: skip
        return real(kind, **kw)

    monkeypatch.setattr(_lab, "decide", appending)
    with pytest.raises(Refused) as e:
        ask(org, sarah, "CR-9201", None, "credit")
    assert e.value.status == 409 and e.value.refusals[0].existing is None
    assert "CR-9201" in e.value.refusals[0].detail


# -- the mapping: every kernel record the lab makes fits the contract ---------------------------
PEOPLE = People(_lab.staff(_lab.corpus_root("base")))
ROUTED = [("S22", "F1"), ("S35", "F4"), ("S36", "F7")]  # set F attacks that withhold findings
KIND: dict[str, DecisionType] = {"discount": "discount", "credit": "credit", "sla": "sla"}


@pytest.mark.parametrize("sid", [s for sids in harness.DECISIONS.values() for s in sids])
def test_kernel_records_fit_the_contract(sid: str) -> None:
    kind = KIND[harness.KIND_OF[sid]]
    record, about = harness.decide_with_capture(sid)
    assert findings(kind, record, PEOPLE).type == kind
    assert len(judgments(record, about)) == len(record["judgments"])
    items = harness.lab("additions").flag_items(record["flags"], route_mode=False, routed=False)
    assert [f.text for f in flags(items, {harness.subject_of(sid)})] == record["flags"]


@pytest.mark.parametrize(("sid", "attack"), ROUTED)
def test_withheld_records_fit_the_contract(sid: str, attack: str) -> None:
    kind = KIND[harness.KIND_OF[sid]]
    record = harness.decide(sid, attack=attack, route=True)
    assert record["outcome"] is None and record["gated_outcome"] == harness.ROUTE_TO[kind]
    f = findings(kind, record, PEOPLE)
    if isinstance(f, DiscountFindings):
        assert f.commercial_eligibility.status == "unknown" and f.authority is None
    elif isinstance(f, CreditFindings):
        assert f.eligibility.status == "unknown" and f.authority is None and f.registered == []
    else:
        assert (f.breach, f.scope, f.obligations, f.account_owner) == (None, None, [], None)
    known = harness.doc_ids(harness.corpus(sid)) | {harness.subject_of(sid)}
    items = harness.lab("additions").flag_items(record["flags"], route_mode=True, routed=True)
    out = flags(items, known)
    assert any(f.code == "withheld" and f.routes and f.about for f in out)


def test_flag_about_names_whole_ids() -> None:
    known = {"GRT-ACME-2026", "GRT-ACME-2026-ALT", "SLA-SCHEDULE-2.0", "DR-9001", "ACME-MFG-2025"}
    assert flag_about("GRT-ACME-2026-ALT: not registered; set aside until it is", known) == [
        "GRT-ACME-2026-ALT"]  # fmt: skip
    assert flag_about("incident for Legal: acme_master_supply_agreement.md differs from approved "
                      "ACME-MFG-2025 v1; decided on DR-9001.", known) == [
        "ACME-MFG-2025", "DR-9001"]  # fmt: skip
    assert flag_about("routed: SLA-SCHEDULE-2.0 set aside", known) == ["SLA-SCHEDULE-2.0"]
    assert flag_about("cannot decide restoration: missing the root-cause finding", known) == []


# -- conditions ---------------------------------------------------------------------------------
def test_input_conflicts_compare_by_contract_names() -> None:
    rec = {"requested_discount": 0.15, "request_date": "2026-09-23", "status": "Pending Approval",
           "customer": "CRM-2048", "product": "NS-500", "requestor": "EMP-101"}  # fmt: skip
    assert input_conflicts("discount", None, rec) == []
    assert input_conflicts("discount", {"requested_discount": 0.15 + 1e-12}, rec) == []
    assert input_conflicts("discount", {"requested_discount": "0.15"}, rec) == []
    assert input_conflicts("discount", {"requested_discount": None, "customer": "CRM-2048"},
                           rec) == []  # fmt: skip
    assert input_conflicts("discount", {"product": "NS-400", "requested_discount": 0.08}, rec) == [
        ("requested_discount", 0.08, 0.15),
        ("product", "NS-400", "NS-500"),
    ]  # §3.5 order
    assert input_conflicts("discount", {"requested_limit_usd": 1}, rec) == []  # not on record
    assert input_conflicts("sla", {"status": "Open"}, {"status": "Restored"}) == []


def test_conflict_condition_s22_wording() -> None:
    sarah = PersonRef.model_validate(SARAH_REF)
    c = conflict_condition("c1", "discount", "DR-9001", "requested_discount", 0.08, 0.15, sarah, 1)
    assert dump(c) == example("v1")["conditions"][0]


# -- state ----------------------------------------------------------------------------------------
def _ev(seq: int, kind: str, payload: dict[str, Any]) -> Event:
    at = datetime(2026, 9, 23, tzinfo=UTC)
    return Event(seq, at, at, "northstar", "DR-1", kind, None, payload)


def test_state_is_derived_first_match_wins() -> None:
    v: dict[str, Any] = {
        "decision_id": "DEC-0001", "version": 1, "subject": {"request_id": "DR-1"},
        "actions": [{"action": "apply_discount", "params": {}, "expected_actor": None}],
        "conditions": [{"id": "c1", "blocking": True, "resolved": None}],
        "approvals": [{"kind": "approval", "given": None, "declined": None}],
    }  # fmt: skip
    resolved = _ev(2, "condition.resolved", {"decision_id": "DEC-0001", "condition_id": "c1",
                                             "resolved": {"rerun_version": 2}})  # fmt: skip
    approved = _ev(3, "decision.approved", {"decision_id": "DEC-0001", "version": 1, "index": 0,
                                            "given": {}})  # fmt: skip
    declined = _ev(3, "decision.declined", {"decision_id": "DEC-0001", "version": 1, "index": 0,
                                            "declined": {}})  # fmt: skip
    other = _ev(3, "decision.approved", {"decision_id": "DEC-0002", "version": 1, "index": 0,
                                         "given": {}})  # fmt: skip
    withdrawn = _ev(4, "decision.withdrawn", {"decision_id": "DEC-0001", "version": 1})
    spent = [ExecutionRow("northstar", "DR-1", "apply_discount", "DEC-0001", 1, "CLR-00001", "t")]
    elsewhere = [ExecutionRow("northstar", "DR-2", "apply_discount", "DEC-0009", 1, "C", "t")]
    assert derive_state(v, [], []) == "not_ready"
    assert derive_state(v, [resolved], elsewhere) == "awaiting_approval"
    assert derive_state(v, [resolved, other], []) == "awaiting_approval"
    assert derive_state(v, [resolved, approved], []) == "ready"
    assert derive_state(v, [resolved, declined], []) == "declined"
    assert derive_state(v, [resolved, approved], spent) == "spent"
    assert derive_state(v, [withdrawn], spent) == "withdrawn"
    assert derive_state({**v, "actions": []}, [], []) == "no_action"
    assert derive_state({**v, "version": 2}, [resolved, approved], []) == "awaiting_approval"
    assert [is_live(s) for s in ("no_action", "not_ready", "awaiting_approval", "ready")] == [
        True] * 4  # fmt: skip
    assert [is_live(s) for s in ("withdrawn", "declined", "spent")] == [False] * 3
