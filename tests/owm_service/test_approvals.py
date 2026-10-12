"""The approvals view (B-06 Task 14; contract §8, spec §4): what waits on the viewer, what waits on
someone else that the viewer follows, and what the viewer has done. Replay only.

`decision_approval` items are a version's outstanding approvals, held by any open blocking
condition (DC-4); `condition` items are open conditions, ratchet confirmations included. Register
items arrive in Task 19."""

from __future__ import annotations

from typing import Any

import pytest

from owm_service import approvals
from owm_service.decisions import Decisions
from owm_service.errors import Refused
from owm_service.models import (
    Actor,
    ApprovalsView,
    DecisionRecord,
    DecisionRequest,
    ResolveRequest,
    StepRequest,
)
from owm_service.org import Org
from owm_service.register_queue import RegisterQueue
from owm_service.sessions import Sessions

CONFIRM = ResolveRequest(decision_version=1, resolution="confirmed_record")


def person(org: Org, emp: str) -> Actor:
    return Sessions(org).open_person(emp)[1]


def ask(org: Org, actor: Actor, subject: str, submitted: dict[str, Any] | None = None,
        kind: str = "discount") -> DecisionRecord:  # fmt: skip
    key = "ticket" if kind == "sla" else "request_id"
    raw: dict[str, Any] = {"decision_type": kind, "subject": {key: subject}}
    if submitted is not None:
        raw["submitted"] = submitted
    return Decisions(org).ask(actor, DecisionRequest.model_validate(raw))


def step(version: int, note: str | None = None) -> StepRequest:
    return StepRequest.model_validate(
        {"decision_version": version} | ({} if note is None else {"note": note}))  # fmt: skip


def s22(org: Org) -> tuple[DecisionRecord, Actor, Actor, Actor]:
    """S22's version 1, asked by the Deal Desk Agent for Sarah: c1 open, Michael's approval held."""
    agent = Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")[1]
    v1 = ask(org, agent, "DR-9001", {"requested_discount": 0.08})
    return v1, agent, person(org, "EMP-101"), person(org, "EMP-200")


def kinds(items: list[Any]) -> list[tuple[str, str]]:
    return [(i.kind, i.id) for i in items]


def waiting(v: ApprovalsView) -> list[str]:
    return [p.id for i in v.waiting_on_you for p in i.waiting_on]


def test_s22_v1_michaels_approval_is_held_by_c1(org: Org) -> None:
    v1, _, _, michael = s22(org)
    did = v1.decision_id
    view = approvals.view(org, michael)
    (item,) = view.waiting_on_you
    assert (item.kind, item.id) == ("decision_approval", f"{did}:v1:approvals[0]")
    assert [p.id for p in item.waiting_on] == ["EMP-200"]
    assert [(h.condition_id, [p.id for p in h.who]) for h in item.held_by] == [("c1", ["EMP-101"])]
    assert item.raised_by == v1.actor and item.raised_at == v1.decided_at
    assert item.href == f"/api/v1/decisions/{did}"
    assert "VP Sales" in item.detail and "c1" in item.detail
    assert view.waiting_on_others == [] and view.done == []


def test_s22_v1_sarah_has_c1_and_follows_michaels_approval(org: Org) -> None:
    v1, _, sarah, _ = s22(org)
    did = v1.decision_id
    view = approvals.view(org, sarah)
    assert kinds(view.waiting_on_you) == [("condition", f"{did}:c1")]
    (c1,) = view.waiting_on_you
    assert c1.held_by == [] and c1.detail == v1.conditions[0].what
    assert [p.id for p in c1.waiting_on] == ["EMP-101"]
    assert kinds(view.waiting_on_others) == [("decision_approval", f"{did}:v1:approvals[0]")]


def test_an_agent_has_nothing_waiting_on_it(org: Org) -> None:
    """DC-1: agents take no people step, so nothing waits on one. It follows its principal's work,
    which waits on people."""
    v1, agent, _, _ = s22(org)
    view = approvals.view(org, agent)
    assert view.waiting_on_you == [] and view.done == []
    assert {i.kind for i in view.waiting_on_others} == {"condition", "decision_approval"}


def test_someone_uninvolved_sees_nothing(org: Org) -> None:
    s22(org)
    view = approvals.view(org, person(org, "EMP-604"))
    assert view == ApprovalsView(waiting_on_you=[], waiting_on_others=[], done=[])


def test_done_lists_what_the_viewer_resolved_and_approved(org: Org) -> None:
    v1, _, sarah, michael = s22(org)
    d, did = Decisions(org), v1.decision_id
    d.resolve(sarah, did, "c1", CONFIRM)
    v2 = d.approve(michael, did, step(2, "ok"))
    assert v2.state == "ready"
    mine = approvals.view(org, michael)
    assert mine.waiting_on_you == [] and mine.waiting_on_others == []
    (done,) = mine.done
    assert (done.kind, done.id, done.result) == ("decision_approval", f"{did}:v2:approvals[0]",
                                                 "approved")  # fmt: skip
    given = v2.approvals[0].given
    assert given is not None and done.at == given.at
    hers = approvals.view(org, sarah)
    assert hers.waiting_on_you == [] and hers.waiting_on_others == []
    (resolved,) = hers.done
    assert (resolved.kind, resolved.id, resolved.result) == ("condition", f"{did}:c1",
                                                             "confirmed_record")  # fmt: skip


def test_a_ratchet_confirmation_is_a_condition_item(org: Org) -> None:
    """S22's G-46 branch: Sarah edits the CRM to 8% and re-runs; the ratchet's c2 waits on
    Michael, and nothing else does (APPROVE stands, so no approval is outstanding)."""
    v1, _, sarah, michael = s22(org)
    did = v1.decision_id
    with org.log.transaction() as tx:
        org.sor.edit(tx, "discount_requests", "DR-9001", {"requested_discount_pct": "8.0"},
                     actor=sarah.model_dump(mode="json"), at=org.clock.now())  # fmt: skip
    v2 = Decisions(org).resolve(sarah, did, "c1", ResolveRequest(
        decision_version=1, resolution="corrected_record"))  # fmt: skip
    assert v2.state == "not_ready" and v2.approvals == []
    view = approvals.view(org, michael)
    (c2,) = view.waiting_on_you
    assert (c2.kind, c2.id) == ("condition", f"{did}:c2")
    assert "lower approval level" in c2.title and c2.detail == v2.conditions[-1].what
    assert kinds(approvals.view(org, sarah).waiting_on_others) == [("condition", f"{did}:c2")]


def test_a_credit_approval_and_concurrence_wait_on_two_people(org: Org) -> None:
    michael = person(org, "EMP-200")
    row = org.sor.row("credit_requests", "CR-9201")
    assert row is not None
    with org.log.transaction() as tx:
        org.sor.insert(tx, "credit_requests", {**row, "request_id": "CR-9208",
                       "requested_limit_usd": "650000",
                       "requested_by": "michael.torres@northstar.example"},
                       actor=michael.model_dump(mode="json"), at=org.clock.now())  # fmt: skip
    v1 = ask(org, michael, "CR-9208", None, "credit")
    elena, david = person(org, "EMP-402"), person(org, "EMP-300")
    assert waiting(approvals.view(org, elena)) == ["EMP-402"]
    assert waiting(approvals.view(org, david)) == ["EMP-300"]
    (concur,) = approvals.view(org, david).waiting_on_you
    assert concur.title.startswith("Concur") and concur.held_by == []
    assert len(approvals.view(org, michael).waiting_on_others) == 2
    Decisions(org).approve(elena, v1.decision_id, step(1))
    assert approvals.view(org, elena).waiting_on_you == []
    assert len(approvals.view(org, michael).waiting_on_others) == 1


def test_a_closed_decision_waits_on_nobody(org: Org) -> None:
    v1, _, sarah, michael = s22(org)
    Decisions(org).decline(michael, v1.decision_id, step(1, "Not this quarter."))
    assert approvals.view(org, sarah).waiting_on_you == []
    assert approvals.view(org, sarah).waiting_on_others == []
    (done,) = approvals.view(org, michael).done
    assert (done.kind, done.result) == ("decision_approval", "declined")


def test_a_change_refused_at_approval_is_done_for_that_approver(org: Org) -> None:
    from .test_register_queue import credit

    priya, elena = person(org, "EMP-401"), person(org, "EMP-402")
    q = RegisterQueue(org)
    first = q.submit_new(priya, credit())
    second = q.submit_new(priya, credit(text=(credit().text or "") + "\nReviewed annually.\n"))
    q.approve(elena, first.change_id)
    with pytest.raises(Refused):
        q.approve(elena, second.change_id)  # RR-13: the register moved since it was submitted
    view = approvals.view(org, elena)
    assert second.change_id not in [i.id for i in view.waiting_on_you]
    results = {i.id: i.result for i in view.done if i.kind == "register_change"}
    assert results == {first.change_id: "approved", second.change_id: "refused"}
    assert approvals.view(org, priya).done == []  # the submitter did nothing
