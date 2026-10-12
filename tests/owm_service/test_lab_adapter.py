"""The demo adapter (B-06 Task 14; spec §8.3) and the decision history (contract `DecisionEvent`).
Replay only.

The adapter closes the loop a real executor would: it redeems a clearance with the params it is
bound to, writes the effect into the systems-of-record overlay as `{system: adapter}`, and reports
`applied`, or `failed` when told to fail. A refused redemption writes nothing."""

from __future__ import annotations

from typing import Any

import pytest

from owm_service import history, lab_adapter
from owm_service.clearance import Clearances
from owm_service.decisions import Decisions
from owm_service.errors import NotFound
from owm_service.events import Event
from owm_service.models import (
    Actor,
    ClearanceRequest,
    Cleared,
    DecisionRecord,
    DecisionRequest,
    ResolveRequest,
    StepRequest,
)
from owm_service.org import Org
from owm_service.sessions import Sessions

ADAPTER = {"kind": "system", "id": "adapter"}
P15: dict[str, Any] = {"request_id": "DR-9001", "account_id": "CRM-2048", "product": "NS-500",
                       "discount": 0.15}  # fmt: skip


def person(org: Org, emp: str) -> Actor:
    return Sessions(org).open_person(emp)[1]


def ask(org: Org, actor: Actor, subject: str, submitted: dict[str, Any] | None = None,
        kind: str = "discount") -> DecisionRecord:  # fmt: skip
    key = "ticket" if kind == "sla" else "request_id"
    raw: dict[str, Any] = {"decision_type": kind, "subject": {key: subject}}
    if submitted is not None:
        raw["submitted"] = submitted
    return Decisions(org).ask(actor, DecisionRequest.model_validate(raw))


def step(version: int) -> StepRequest:
    return StepRequest(decision_version=version)


def clear(org: Org, actor: Actor, rec: DecisionRecord, params: dict[str, Any]) -> Cleared:
    req = ClearanceRequest.model_validate({
        "decision_id": rec.decision_id, "decision_version": rec.version,
        "action": rec.actions[0].action, "params": params})  # fmt: skip
    r = Clearances(org, Decisions(org)).ask(actor, rec.decision_id, req)
    assert isinstance(r, Cleared), r
    return r


def s22_cleared(org: Org) -> tuple[DecisionRecord, Cleared, Actor]:
    """S22's main branch: Sarah confirms the CRM's 15%, Michael approves, the agent clears 15%."""
    agent = Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")[1]
    d = Decisions(org)
    v1 = ask(org, agent, "DR-9001", {"requested_discount": 0.08})
    d.resolve(person(org, "EMP-101"), v1.decision_id, "c1",
              ResolveRequest(decision_version=1, resolution="confirmed_record"))  # fmt: skip
    v2 = d.approve(person(org, "EMP-200"), v1.decision_id, step(2))
    return v2, clear(org, agent, v2, P15), agent


def run(org: Org, cid: str, *, fail: bool = False, by: Actor | None = None) -> dict[str, Any]:
    return lab_adapter.execute(org, Clearances(org, Decisions(org)), cid, fail=fail, by=by)


def edits(org: Org, table: str) -> list[Event]:
    return [e for e in org.log.read(org.org_id, stream="sor")
            if e.payload["table"] == table and e.actor == ADAPTER]  # fmt: skip


def test_s22_applies_the_discount_in_the_crm(org: Org) -> None:
    v2, ok, agent = s22_cleared(org)
    cid = ok.clearance_id
    before = org.sor.row("discount_requests", "DR-9001")
    assert before is not None
    out = run(org, cid, by=agent)
    assert out["redeemed"] is True and out["report"] == "applied" and out["incident_id"] is None
    row = org.sor.row("discount_requests", "DR-9001")
    assert row is not None
    assert (row["status"], row["approved_by"], row["approved_on"]) == (
        "Approved",
        "michael.torres@northstar.example",
        org.clock.today().isoformat(),
    )
    assert row["justification"] == f"{before['justification']} [{cid}]"
    assert {e.payload["field"] for e in edits(org, "discount_requests")} == {
        "status", "approved_by", "approved_on", "justification"}  # fmt: skip
    assert out["effect"]["table"] == "discount_requests" and out["effect"]["id"] == "DR-9001"
    rec = Decisions(org).get(v2.decision_id)
    assert rec.state == "spent" and [x.report for x in rec.executed] == ["applied"]
    # R35: the session that drove the adapter is recorded on the redemption and the report
    for kind in ("clearance.redeemed", "execution.reported"):
        (e,) = org.log.read(org.org_id, kinds=(kind,))
        assert e.payload["by"] == agent.model_dump(mode="json"), kind


def test_a_refused_redemption_writes_nothing(org: Org) -> None:
    _, ok, _ = s22_cleared(org)
    run(org, ok.clearance_id)
    n = len(org.log.read(org.org_id, stream="sor"))
    again = run(org, ok.clearance_id)
    assert again["redeemed"] is False and [r["code"] for r in again["reasons"]] == ["used"]
    assert len(org.log.read(org.org_id, stream="sor")) == n
    assert len(org.log.read(org.org_id, kinds=("execution.reported",))) == 1


def test_fail_reports_failed_writes_no_effect_and_opens_an_incident(org: Org) -> None:
    v2, ok, _ = s22_cleared(org)
    out = run(org, ok.clearance_id, fail=True)
    assert out["redeemed"] is True and out["report"] == "failed"
    assert out["incident_id"] == "INC-0001" and out["effect"] is None
    assert edits(org, "discount_requests") == []
    rec = Decisions(org).get(v2.decision_id)
    assert rec.state == "spent" and rec.executed[0].incident_id == "INC-0001"


def test_an_effect_the_system_refuses_is_reported_failed(
    org: Org, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Redeemed is spent: if the overlay then refuses the write, the adapter reports `failed` and
    the incident says why, rather than leaving a spent action with no report."""
    _, ok, _ = s22_cleared(org)

    def refuse(*a: Any, **kw: Any) -> None:
        raise NotFound("discount_requests DR-9001")

    monkeypatch.setattr(org.sor, "edit", refuse)
    out = run(org, ok.clearance_id)
    assert out["report"] == "failed" and out["incident_id"] == "INC-0001" and out["effect"] is None
    (rep,) = org.log.read(org.org_id, kinds=("execution.reported",))
    assert "DR-9001" in str(rep.payload["detail"])


def test_unknown_clearance_is_404(org: Org) -> None:
    with pytest.raises(NotFound):
        run(org, "CLR-99999")


def test_credit_limit_is_approved_in_the_erp(org: Org) -> None:
    michael = person(org, "EMP-200")
    row = org.sor.row("credit_requests", "CR-9201")
    assert row is not None
    with org.log.transaction() as tx:
        org.sor.insert(tx, "credit_requests", {**row, "request_id": "CR-9208",
                       "requested_limit_usd": "650000",
                       "requested_by": "michael.torres@northstar.example"},
                       actor=michael.model_dump(mode="json"), at=org.clock.now())  # fmt: skip
    d = Decisions(org)
    elena = person(org, "EMP-402")
    v1 = ask(org, michael, "CR-9208", None, "credit")
    d.approve(elena, v1.decision_id, step(1))
    done = d.approve(person(org, "EMP-300"), v1.decision_id, step(1))
    ok = clear(org, elena, done, done.actions[0].params)
    assert run(org, ok.clearance_id)["report"] == "applied"
    after = org.sor.row("credit_requests", "CR-9208")
    assert after is not None
    assert (after["status"], after["approved_by"], after["approved_on"]) == (
        "Approved",
        "elena.novak@northstar.example",
        org.clock.today().isoformat(),
    )
    assert after["requested_limit_usd"] == "650000"


def test_s36_inserts_the_service_credit(org: Org) -> None:
    marcus, paul = person(org, "EMP-602"), person(org, "EMP-604")
    v1 = ask(org, marcus, "SR-39385", None, "sla")
    ready = Decisions(org).approve(marcus, v1.decision_id, step(1))
    ok = clear(org, paul, ready, ready.actions[0].params)
    out = run(org, ok.clearance_id)
    assert out["report"] == "applied"
    (credit,) = [r for r in org.sor.table("service_credits") if r["credit_id"] == ok.clearance_id]
    assert credit == {"credit_id": ok.clearance_id, "ticket_id": "SR-39385",
                      "account_id": "CRM-2048", "ticket_opened": "2026-06-16",
                      "amount_usd": "4200.00",
                      "approved_on": org.clock.today().isoformat()}  # fmt: skip
    (ins,) = [e for e in org.log.read(org.org_id, stream="sor") if e.kind == "sor.inserted"]
    assert ins.actor == ADAPTER


# -- the decision history (contract DecisionEvent) ------------------------------------------------
def test_s22_history_in_time_order(org: Org) -> None:
    v2, ok, agent = s22_cleared(org)
    did = v2.decision_id
    refused = ClearanceRequest.model_validate({
        "decision_id": did, "decision_version": 2, "action": "apply_discount",
        "params": {**P15, "discount": 0.08}, "dry_run": True})  # fmt: skip
    Clearances(org, Decisions(org)).ask(agent, did, refused)
    run(org, ok.clearance_id, by=agent)
    run(org, ok.clearance_id)  # refused: used (on the decision's own stream)
    evs = history.events(org, Decisions(org), did)
    assert [e.kind for e in evs] == [
        "requested",
        "decided",
        "condition_resolved",
        "decided",
        "approved",
        "clearance_cleared",
        "clearance_refused",
        "clearance_redeemed",
        "execution_reported",
        "clearance_refused",
    ]
    assert [e.version for e in evs] == [1, 1, 1, 2, 2, 2, 2, 2, 2, 2]
    assert evs[0].actor == agent and evs[2].actor.kind == "person"
    assert evs[7].actor == agent  # `by`, the session that drove the adapter
    assert evs[9].actor == agent  # no `by`: the actor the clearance was issued to
    assert "dry run" in evs[6].detail and "used" in evs[9].detail
    assert evs[3].detail.startswith("Version 2: APPROVE_WITH_AUTHORIZATION")
    assert [e.at for e in evs] == sorted(e.at for e in evs)


def test_history_of_an_unknown_decision_is_404(org: Org) -> None:
    with pytest.raises(NotFound):
        history.events(org, Decisions(org), "DEC-9999")
