"""§12.2 item 3 (spec §10): the must-fixes from the contract reviews and G-46. Replay only, $0.

- (a) An `as_of` in the body is refused with 422, at the HTTP level and at the model level, and
  S23 decides on the CRM's date, not the submitted 2025-09-23 (PRICING-POLICY-2026, Michael).
- (b) A second decision on DR-9001 while the first is live gets 409 DC-6 naming it as `existing`.
- (c) DR-9102 (S10) at 25% needs the CRO. Sarah edits the CRM to 8% and re-runs: the outcome stands
  at APPROVE, but the version is below DR-9102's floor, so a ratchet condition waits on David
  Morgan (EMP-300) and clearance is refused `condition_open`.
- (d) The same on DR-9001 (S22's branch, spec §6.9): the ratchet condition names Michael Torres
  (EMP-200).
Both 8% re-runs replay recorded Jev answers: the discount judgments ask about the justification,
the customer, the product and the documents, never the figure (spec §10, checked 2026-10-11)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from owm_service.clearance import Clearances
from owm_service.decisions import Decisions
from owm_service.errors import Refused
from owm_service.models import (
    Actor,
    ClearanceRequest,
    DecisionRecord,
    DecisionRequest,
    DiscountFindings,
    NotCleared,
    RerunRequest,
    ResolveRequest,
)
from owm_service.org import Org
from owm_service.sessions import Sessions

from .. import harness

S23_BODY: dict[str, Any] = {"decision_type": "discount", "subject": {"request_id": "DR-9001"},
                            "submitted": {"request_date": "2025-09-23"}}  # fmt: skip


def person(org: Org, emp: str) -> Actor:
    return Sessions(org).open_person(emp)[1]


def edit(org: Org, actor: Actor, key: str, fields: dict[str, str]) -> None:
    """A systems-of-record edit, as `PATCH /lab/sor/discount_requests/{key}` makes it."""
    at = org.clock.now()  # before the write: never first read inside one
    with org.log.transaction() as tx:
        org.sor.edit(tx, "discount_requests", key, fields, actor=actor.model_dump(mode="json"),
                     at=at)  # fmt: skip


def clear(org: Org, actor: Actor, rec: DecisionRecord) -> NotCleared:
    """Ask to clear the version's decided action, with exactly its decided params."""
    (act,) = rec.actions
    req = ClearanceRequest(decision_id=rec.decision_id, decision_version=rec.version,
                           action=act.action, params=act.params)  # fmt: skip
    out = Clearances(org, Decisions(org)).ask(actor, rec.decision_id, req)
    assert isinstance(out, NotCleared), out
    return out


def authority(rec: DecisionRecord) -> tuple[str | None, str | None]:
    assert isinstance(rec.findings, DiscountFindings) and rec.findings.authority is not None
    a = rec.findings.authority
    return a.policy, a.approver.id if a.approver else None


# -- (a) as_of ------------------------------------------------------------------------------------
def test_body_as_of_is_refused_by_the_model() -> None:
    with pytest.raises(ValidationError, match="as_of"):
        DecisionRequest.model_validate({**S23_BODY, "as_of": "2025-09-23"})


def test_body_as_of_refused_over_http_and_s23_decides_on_the_crm_date(tmp_path: Path) -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from owm_service.app import create_app

    app = create_app(harness.scenario_settings("S23", tmp_path))
    client = TestClient(app)
    r = client.post("/lab/sessions", json={"person_id": "EMP-101"})
    assert r.status_code == 201, r.text
    sarah = {"Authorization": f"Bearer {r.json()['token']}"}
    r = client.post("/api/v1/decisions", json={**S23_BODY, "as_of": "2025-09-23"}, headers=sarah)
    assert r.status_code == 422
    (err,) = r.json()["detail"]
    assert (err["type"], err["loc"]) == ("extra_forbidden", ["body", "as_of"])
    assert client.get("/api/v1/decisions", headers=sarah).json() == []  # nothing was decided
    r = client.post("/api/v1/decisions", json=S23_BODY, headers=sarah)
    assert r.status_code == 201, r.text
    v1 = DecisionRecord.model_validate(r.json())
    assert v1.as_of == "2026-09-23"  # the CRM's request date, not the submitted 2025-09-23
    assert authority(v1) == ("PRICING-POLICY-2026", "EMP-200")
    assert v1.gated_outcome == harness.expected("S23")["outcome"] == "APPROVE_WITH_AUTHORIZATION"
    assert [(a.kind, a.person and a.person.id) for a in v1.approvals] == [("approval", "EMP-200")]
    (c,) = v1.conditions
    assert (c.source, c.field) == ("input_conflict", "request_date")
    assert (c.submitted, c.on_record) == ("2025-09-23", "2026-09-23")
    org: Org = app.state.owm.org
    assert harness.kernel_part(org, v1)["authority"]["policy"] == "PRICING-POLICY-2026"
    # (b) over HTTP too: the first decision is live, so a second is 409 DC-6 naming it
    r = client.post("/api/v1/decisions", json=S23_BODY, headers=sarah)
    assert r.status_code == 409
    (refusal,) = r.json()["refusals"]
    assert (refusal["rule"], refusal["existing"]) == ("DC-6", v1.decision_id)


# -- (b) DC-6 -------------------------------------------------------------------------------------
def test_second_decision_on_dr9001_is_409_dc6(tmp_path: Path) -> None:
    org = harness.scenario_org("S22", tmp_path)
    first = harness.ask(org, "S22")
    with pytest.raises(Refused) as e:
        harness.ask(org, "S25")  # the same request, asked again with nothing submitted
    assert e.value.status == 409
    (refusal,) = e.value.refusals
    assert (refusal.rule, refusal.existing) == ("DC-6", first.decision_id)
    assert [d.decision_id for d in Decisions(org).list()] == [first.decision_id]


# -- (c) and (d): the ratchet (G-46) ---------------------------------------------------------------
def test_dr9102_25_to_8_is_ratcheted_to_the_cro(tmp_path: Path) -> None:
    org = harness.scenario_org("S10", tmp_path)  # DR-9102 at 25%, seeded through the overlay
    d = Decisions(org)
    sarah = person(org, "EMP-101")
    v1 = harness.ask(org, "S10")
    assert (v1.gated_outcome, v1.state) == ("APPROVE_WITH_AUTHORIZATION", "awaiting_approval")
    assert [(a.kind, a.person and a.person.id) for a in v1.approvals] == [("approval", "EMP-300")]
    assert v1.floor is not None and (v1.floor.level, v1.floor.subject) == (2, "DR-9102")
    edit(org, sarah, "DR-9102", {"requested_discount_pct": "8.0"})
    v2 = d.rerun(sarah, v1.decision_id, RerunRequest(decision_version=1))
    assert (v2.version, v2.outcome, v2.gated_outcome) == (2, "APPROVE", "APPROVE")
    assert authority(v2)[1] == "EMP-101"  # left alone, 8% is within Sarah's own authority
    (ratchet,) = [c for c in v2.conditions if c.source == "ratchet"]
    assert [p.id for p in ratchet.who] == ["EMP-300"] and ratchet.blocking
    assert {"ratchet", "self_sourced_basis"} <= {f.code for f in v2.flags}
    assert (v2.state, v2.approvals) == ("not_ready", [])
    assert v2.floor is not None and v2.floor.level == 2
    refused = clear(org, sarah, v2)
    assert [(r.code, r.condition_id) for r in refused.reasons] == [("condition_open", ratchet.id)]
    assert not org.engine.calls.exists()  # the 8% re-run replayed: $0


def test_dr9001_crm_8_is_ratcheted_to_michael(tmp_path: Path) -> None:
    """S22's branch (spec §6.9): the agent asks on 8%, the CRM says 15%; Sarah edits the CRM to 8%
    and resolves her condition as corrected."""
    org = harness.scenario_org("S22", tmp_path)
    sarah = person(org, "EMP-101")
    agent = Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")[1]
    v1 = Decisions(org).ask(agent, harness.request_for("S22"))
    assert v1.gated_outcome == "APPROVE_WITH_AUTHORIZATION" and authority(v1)[1] == "EMP-200"
    assert v1.floor is not None and v1.floor.level == 1
    (c1,) = v1.conditions
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "8.0"})
    v2 = Decisions(org).resolve(sarah, v1.decision_id, c1.id, ResolveRequest(
        decision_version=1, resolution="corrected_record"))  # fmt: skip
    assert (v2.version, v2.outcome, v2.gated_outcome) == (2, "APPROVE", "APPROVE")
    (ratchet,) = [c for c in v2.conditions if c.source == "ratchet"]
    assert [p.id for p in ratchet.who] == ["EMP-200"] and ratchet.blocking
    assert {"ratchet", "self_sourced_basis"} <= {f.code for f in v2.flags}
    assert v2.state == "not_ready"
    refused = clear(org, agent, v2)
    assert [(r.code, r.condition_id) for r in refused.reasons] == [("condition_open", ratchet.id)]
    (reason,) = refused.reasons
    assert reason.waiting_on is not None and [p.id for p in reason.waiting_on] == ["EMP-200"]
    assert not org.engine.calls.exists()  # the 8% re-run replayed: $0
