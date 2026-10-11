"""Resolving, re-running, approving, declining and withdrawing (B-06 Task 12; spec §6.3-6.4,
contract §5.6-5.8 and §6.1). Replay only.

Every step checks DC-1 to DC-5 first. A resolution or a `/rerun` re-runs the kernel on the row as it
is now, keeping `as_of`, and writes version n+1; that re-run is where the ratchet holds a requester
who edited the CRM down into their own band (S22's ratchet branch). S22's version 2 on each branch
must equal the contract's example (`v2AfterApproval`, `v2Ratchet`) on every field the kernel and
the service decide; times and ids are illustrative there."""

from __future__ import annotations

import dataclasses
import json
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from owm_service import _lab
from owm_service.clock import DEMO_TZ
from owm_service.config import load_settings
from owm_service.decisions import Decisions
from owm_service.errors import CannotDecide, NotFound, Refused
from owm_service.models import (
    Actor,
    DecisionRecord,
    DecisionRequest,
    RerunRequest,
    ResolveRequest,
    StepRequest,
)
from owm_service.org import Org
from owm_service.ratchet import floor_of
from owm_service.sessions import Sessions

LAB = Path(__file__).resolve().parents[2]
EXAMPLE: dict[str, Any] = json.loads(
    (LAB / "lab/owm_service/contract/s22.example.json").read_text()
)
MICHAEL = {"id": "EMP-200", "name": "Michael Torres", "title": "VP Sales", "function": "Sales"}


# -- fixtures and helpers -----------------------------------------------------------------------
def _person(org: Org, emp: str) -> Actor:
    return Sessions(org).open_person(emp)[1]


@pytest.fixture
def sarah(org: Org) -> Actor:  # overrides conftest's plain-dict Sarah for this module
    return _person(org, "EMP-101")


@pytest.fixture
def michael(org: Org) -> Actor:
    return _person(org, "EMP-200")


@pytest.fixture
def david(org: Org) -> Actor:
    return _person(org, "EMP-300")


@pytest.fixture
def elena(org: Org) -> Actor:
    return _person(org, "EMP-402")


@pytest.fixture
def kelly(org: Org) -> Actor:
    return _person(org, "EMP-500")


@pytest.fixture
def marcus(org: Org) -> Actor:
    return _person(org, "EMP-602")


@pytest.fixture
def dealdesk(org: Org) -> Actor:
    return Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")[1]


def dump(m: BaseModel) -> dict[str, Any]:
    """As the service serves it (ruling R13): absent `?:` fields stay absent."""
    return m.model_dump(mode="json", exclude_unset=True)


def ask(
    org: Org, actor: Actor, subject: str, submitted: dict[str, Any] | None = None,
    kind: str = "discount",
) -> DecisionRecord:  # fmt: skip
    key = "ticket" if kind == "sla" else "request_id"
    raw: dict[str, Any] = {"decision_type": kind, "subject": {key: subject}}
    if submitted is not None:
        raw["submitted"] = submitted
    return Decisions(org).ask(actor, DecisionRequest.model_validate(raw))


def ask_s22(org: Org, dealdesk: Actor) -> DecisionRecord:
    return ask(org, dealdesk, "DR-9001", {"requested_discount": 0.08})


def edit(org: Org, actor: Actor, key: str, fields: dict[str, str],
         table: str = "discount_requests") -> datetime:  # fmt: skip
    at = org.clock.now()
    with org.log.transaction() as tx:
        org.sor.edit(tx, table, key, fields, actor=dump(actor), at=at)
    return at


def resolve(org: Org, actor: Actor, did: str, cid: str, version: int,
            resolution: str, note: str | None = None) -> DecisionRecord:  # fmt: skip
    body = ResolveRequest.model_validate(
        {"decision_version": version, "resolution": resolution}
        | ({} if note is None else {"note": note}))  # fmt: skip
    return Decisions(org).resolve(actor, did, cid, body)


def step(version: int, note: str | None = None) -> StepRequest:
    return StepRequest.model_validate(
        {"decision_version": version} | ({} if note is None else {"note": note}))  # fmt: skip


def refused(fn: Callable[[], object]) -> Refused:
    with pytest.raises(Refused) as e:
        fn()
    return e.value


def rules(e: Refused) -> list[str]:
    return [r.rule for r in e.refusals]


def without(d: dict[str, Any], *paths: str) -> dict[str, Any]:
    """`d` without the dotted `paths` (a `*` segment means every list item)."""
    out: dict[str, Any] = json.loads(json.dumps(d))

    def drop(node: Any, parts: list[str]) -> None:
        if node is None:
            return
        head, rest = parts[0], parts[1:]
        if head == "*":
            for item in node:
                drop(item, rest)
        elif not rest:
            node.pop(head, None)
        else:
            drop(node.get(head), rest)

    for p in paths:
        drop(out, p.split("."))
    return out


def hhmm(at: datetime) -> str:
    return at.astimezone(DEMO_TZ).strftime("%H:%M")


def s22_v2_main(org: Org, dealdesk: Actor, sarah: Actor) -> DecisionRecord:
    v1 = ask_s22(org, dealdesk)
    return resolve(org, sarah, v1.decision_id, "c1", 1, "confirmed_record")


# -- S22, both branches (spec §6.9) --------------------------------------------------------------
def test_s22_main_branch(org: Org, dealdesk: Actor, sarah: Actor, michael: Actor) -> None:
    d = Decisions(org)
    v1 = ask_s22(org, dealdesk)
    e = refused(lambda: d.approve(michael, v1.decision_id, step(1)))
    assert (e.status, rules(e)) == (422, ["DC-4"])
    v2 = resolve(org, sarah, v1.decision_id, "c1", 1, "confirmed_record")
    c1 = v2.conditions[0]
    assert c1.resolved is not None
    assert (v2.version, v2.state, c1.resolved.rerun_version) == (2, "awaiting_approval", 2)
    # v1 is kept; a condition id is unique across versions, so its resolution shows there too
    old = d.get(v1.decision_id, 1)
    assert old.version == 1 and old.conditions[0].resolved == c1.resolved
    v2 = d.approve(michael, v1.decision_id, step(2))
    assert v2.state == "ready"
    ex = EXAMPLE["v2AfterApproval"]
    got = dump(v2)
    for k in ("decision_type", "subject", "submitted", "requested_by", "as_of", "outcome",
              "gated_outcome", "routed", "findings", "flags", "actions", "state",
              "previous"):  # fmt: skip
        assert got[k] == ex[k], k
    assert [without(c, "resolved.at") for c in got["conditions"]] == [
        without(c, "resolved.at") for c in ex["conditions"]]  # fmt: skip
    assert [without(a, "given.at") for a in got["approvals"]] == [
        without(a, "given.at") for a in ex["approvals"]]  # fmt: skip
    assert without(got["floor"], "set_by.decision_id") == without(ex["floor"], "set_by.decision_id")
    assert got["floor"]["set_by"]["decision_id"] == v1.decision_id
    # fixed at version 1: who asked, when, and the date the policy is read for
    assert (got["actor"], got["requested_at"], got["as_of"]) == (
        dump(v1)["actor"],
        v1.requested_at,
        v1.as_of,
    )
    assert v2.decided_at >= v1.decided_at


def test_s22_ratchet_branch(org: Org, dealdesk: Actor, sarah: Actor, michael: Actor) -> None:
    v1 = ask_s22(org, dealdesk)
    at = edit(org, sarah, "DR-9001", {"requested_discount_pct": "8.0"})
    v2 = resolve(org, sarah, v1.decision_id, "c1", 1, "corrected_record")
    assert v2.outcome == "APPROVE" and v2.state == "not_ready"
    assert {f.code for f in v2.flags} >= {"ratchet", "self_sourced_basis"}
    c2 = next(c for c in v2.conditions if c.source == "ratchet")
    assert [p.id for p in c2.who] == ["EMP-200"]
    e = refused(lambda: resolve(org, sarah, v1.decision_id, c2.id, 2, "confirmed_lower_level"))
    assert e.status == 422 and rules(e)[0] in {"DC-2", "DC-3"} and "DC-3" in rules(e)
    ex = EXAMPLE["v2Ratchet"]
    got = dump(v2)
    for k in ("decision_type", "subject", "submitted", "requested_by", "as_of", "outcome",
              "gated_outcome", "routed", "approvals", "actions", "state",
              "previous"):  # fmt: skip
        assert got[k] == ex[k], k
    # The example nulls an authorized requester's required_role and approver; the kernel (and the
    # truth, e.g. S14: ENTERPRISE_AE, EMP-101) name the requester's own role and the requester.
    authority = {**ex["findings"]["authority"], "required_role": "Enterprise Account Executive",
                 "approver": got["requested_by"]}  # fmt: skip
    assert got["findings"] == {**ex["findings"], "authority": authority}
    assert [without(c, "resolved.at") for c in got["conditions"]] == [
        without(c, "resolved.at") for c in ex["conditions"]]  # fmt: skip
    want_flags = json.loads(json.dumps(ex["flags"]).replace("10:21", hhmm(at)))
    assert got["flags"] == want_flags
    assert without(got["floor"], "set_by.decision_id") == without(ex["floor"], "set_by.decision_id")
    # the row as it is now is what the decision rests on
    assert got["basis"]["records"][0]["fields"]["requested_discount_pct"] == "8.0"
    v3 = resolve(org, michael, v1.decision_id, c2.id, 2, "confirmed_lower_level")
    assert v3.state == "ready" and v3.floor is not None and v3.floor.confirmed_by is not None
    assert v3.floor.confirmed_by.id == "EMP-200"
    assert (v3.floor.level, v3.floor.set_by.version) == (0, 2)
    assert not [c for c in v3.conditions if c.resolved is None]
    assert [(c.id, c.resolved and c.resolved.rerun_version) for c in v3.conditions] == [
        ("c1", 2), ("c2", 3)]  # fmt: skip
    assert "ratchet" not in {f.code for f in v3.flags}
    assert v3.previous is not None and v3.previous.what_changed == (
        "Michael Torres confirmed the lower approval level; no conditions remain.")  # fmt: skip
    floor = floor_of(org, "DR-9001")
    assert floor is not None and floor.level.band == 0  # the log agrees with the version


def test_a_rerun_after_an_edit_is_held_by_the_ratchet(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor
) -> None:
    """Ready, then the requester edits the CRM down into her own band and asks for a re-run: the
    outcome stands, but the version is below DR-9001's floor (spec §6.3, ready → not_ready)."""
    d = Decisions(org)
    v2 = s22_v2_main(org, dealdesk, sarah)
    assert d.approve(michael, v2.decision_id, step(2)).state == "ready"
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "8.0"})
    v3 = d.rerun(sarah, v2.decision_id, RerunRequest(decision_version=2))
    assert (v3.version, v3.outcome, v3.state, v3.approvals) == (3, "APPROVE", "not_ready", [])
    ratchet = [c for c in v3.conditions if c.source == "ratchet"]
    assert [(c.id, [p.id for p in c.who], c.opened_in_version) for c in ratchet] == [
        ("c2", ["EMP-200"], 3)]  # fmt: skip
    assert ratchet[0].what == ("Confirm the lower approval level: version 1 needed the VP Sales; "
                               "version 3 is within Sarah Chen's own authority.")  # fmt: skip
    # c1 was confirmed on 15%; the CRM now holds the submitted 8%, so nothing conflicts
    assert [c.id for c in v3.conditions if c.source == "input_conflict"] == ["c1"]
    assert v3.previous is not None and v3.previous.what_changed == (
        "Sarah Chen asked for a re-run; the level fell below the floor.")  # fmt: skip


# -- the rules (DC-1 to DC-5) -------------------------------------------------------------------
def test_agent_cannot_resolve(org: Org, dealdesk: Actor) -> None:
    """DC-1, on every command: agents never take a people step."""
    d = Decisions(org)
    v1 = ask_s22(org, dealdesk)
    did = v1.decision_id
    for fn in (lambda: resolve(org, dealdesk, did, "c1", 1, "confirmed_record"),
               lambda: d.rerun(dealdesk, did, RerunRequest(decision_version=1)),
               lambda: d.approve(dealdesk, did, step(1)),
               lambda: d.decline(dealdesk, did, step(1, "no")),
               lambda: d.withdraw(dealdesk, did, step(1))):  # fmt: skip
        e = refused(fn)
        assert (e.status, rules(e)) == (422, ["DC-1"])
    assert Decisions(org).get(did).version == 1


def test_stale_version_is_409(org: Org, dealdesk: Actor, sarah: Actor, michael: Actor) -> None:
    """DC-5: the version a step names must be the current one."""
    d = Decisions(org)
    v2 = s22_v2_main(org, dealdesk, sarah)
    did = v2.decision_id
    for fn in (lambda: d.approve(michael, did, step(1)),
               lambda: d.approve(michael, did, step(3)),
               lambda: d.decline(michael, did, step(1, "too deep")),
               lambda: d.rerun(sarah, did, RerunRequest(decision_version=1)),
               lambda: d.withdraw(sarah, did, step(1)),
               lambda: resolve(org, sarah, did, "c1", 1, "confirmed_record")):  # fmt: skip
        e = refused(fn)
        assert (e.status, rules(e)) == (409, ["DC-5"])
    assert d.get(did).version == 2 and d.get(did).state == "awaiting_approval"


def test_resolve_needs_a_person_the_condition_names(
    org: Org, dealdesk: Actor, michael: Actor, kelly: Actor
) -> None:
    v1 = ask_s22(org, dealdesk)
    for who in (michael, kelly):
        e = refused(partial(resolve, org, who, v1.decision_id, "c1", 1, "confirmed_record"))
        assert (e.status, rules(e)) == (422, ["DC-2"])
        assert "c1" in e.refusals[0].detail and "Sarah Chen" in e.refusals[0].detail


def test_resolution_must_fit_the_source(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor
) -> None:
    """R28: input_conflict takes confirmed_record or corrected_record, missing_record takes
    corrected_record, ratchet takes confirmed_lower_level; anything else is DC-2, naming both."""
    v1 = ask_s22(org, dealdesk)
    did = v1.decision_id
    e = refused(lambda: resolve(org, sarah, did, "c1", 1, "confirmed_lower_level"))
    assert (e.status, rules(e)) == (422, ["DC-2"])
    assert "input_conflict" in e.refusals[0].detail
    assert "confirmed_lower_level" in e.refusals[0].detail
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "8.0"})
    v2 = resolve(org, sarah, did, "c1", 1, "corrected_record")
    for wrong in ("confirmed_record", "corrected_record"):
        e = refused(partial(resolve, org, michael, did, "c2", 2, wrong))
        assert (e.status, rules(e)) == (422, ["DC-2"])
        assert "ratchet" in e.refusals[0].detail and wrong in e.refusals[0].detail
    assert v2.version == Decisions(org).get(did).version == 2


def test_a_resolved_condition_is_not_resolved_again(
    org: Org, dealdesk: Actor, sarah: Actor
) -> None:
    v2 = s22_v2_main(org, dealdesk, sarah)
    e = refused(lambda: resolve(org, sarah, v2.decision_id, "c1", 2, "confirmed_record"))
    assert (e.status, rules(e)) == (422, ["DC-2"]) and "already resolved" in e.refusals[0].detail


def test_an_unknown_condition_is_404(org: Org, dealdesk: Actor, sarah: Actor) -> None:
    v1 = ask_s22(org, dealdesk)
    with pytest.raises(NotFound):
        resolve(org, sarah, v1.decision_id, "c9", 1, "confirmed_record")
    with pytest.raises(NotFound):
        Decisions(org).approve(sarah, "DEC-0999", step(1))


def test_approve_needs_the_person_the_approval_names(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, david: Actor
) -> None:
    """DC-2 for anyone else; DC-3 for the requester; a given approval isn't given twice."""
    d = Decisions(org)
    v2 = s22_v2_main(org, dealdesk, sarah)
    did = v2.decision_id
    e = refused(lambda: d.approve(david, did, step(2)))
    assert (e.status, rules(e)) == (422, ["DC-2"])
    e = refused(lambda: d.approve(sarah, did, step(2)))
    assert e.status == 422 and "DC-3" in rules(e)
    approved = d.approve(michael, did, step(2, "within the exception"))
    assert approved.approvals[0].given is not None
    assert approved.approvals[0].given.note == "within the exception"
    assert approved.approvals[0].given.by.model_dump() == MICHAEL
    e = refused(lambda: d.approve(michael, did, step(2)))
    assert (e.status, rules(e)) == (422, ["DC-2"]) and "already" in e.refusals[0].detail


def test_s34_concurrence_passed_from(org: Org, michael: Actor, elena: Actor, david: Actor) -> None:
    """Michael Torres asks for $650,000 for Acme: the Director of Finance approves, and the VP
    Sales concurrence passes from Michael, the requester, to David Morgan (separation of duties).
    Michael can take neither step."""
    row = org.sor.row("credit_requests", "CR-9201")
    assert row is not None
    with org.log.transaction() as tx:
        org.sor.insert(tx, "credit_requests", {**row, "request_id": "CR-9208",
                       "requested_limit_usd": "650000",
                       "requested_by": "michael.torres@northstar.example"},
                       actor=dump(michael), at=org.clock.now())  # fmt: skip
    d = Decisions(org)
    v1 = ask(org, michael, "CR-9208", None, "credit")
    assert v1.outcome == "APPROVE_WITH_AUTHORIZATION" and v1.state == "awaiting_approval"
    a = v1.approvals
    assert [(x.kind, x.person and x.person.id) for x in a] == [
        ("approval", "EMP-402"),
        ("concurrence", "EMP-300"),
    ]
    assert a[1].passed_from is not None and a[1].passed_from.person.id == "EMP-200"
    e = refused(lambda: d.approve(michael, v1.decision_id, step(1)))
    assert e.status == 422 and "DC-3" in rules(e)
    after_elena = d.approve(elena, v1.decision_id, step(1))
    assert after_elena.state == "awaiting_approval" and after_elena.approvals[0].given is not None
    assert after_elena.approvals[1].given is None
    done = d.approve(david, v1.decision_id, step(1, "concur"))
    assert done.state == "ready" and done.approvals[1].given is not None
    assert done.approvals[1].given.by.id == "EMP-300"


def test_one_person_never_gives_two_approvals(
    org: Org, sarah: Actor, elena: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DC-3: the approver and a concurrer are never the same person. The kernel prep already makes
    sure of it, so the kernel's roles are made to name Elena Novak twice."""
    real = _lab.decide

    def twice(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        kr = real(kind, **kw)
        roles = [{"kind": "approval", "role": "Director of Finance", "person_id": "EMP-402",
                  "passed_from": None},
                 {"kind": "concurrence", "role": "VP Sales", "person_id": "EMP-402",
                  "passed_from": None}]  # fmt: skip
        return dataclasses.replace(kr, approval_roles=roles)

    monkeypatch.setattr(_lab, "decide", twice)
    d = Decisions(org)
    v1 = ask(org, sarah, "DR-9001")
    assert [a.person and a.person.id for a in v1.approvals] == ["EMP-402", "EMP-402"]
    d.approve(elena, v1.decision_id, step(1))
    e = refused(lambda: d.approve(elena, v1.decision_id, step(1)))
    assert (e.status, rules(e)) == (422, ["DC-3"])
    assert d.get(v1.decision_id).state == "awaiting_approval"


# -- decline, withdraw --------------------------------------------------------------------------
def test_decline_keeps_the_floor(org: Org, dealdesk: Actor, sarah: Actor, michael: Actor) -> None:
    """A decline needs a note. The decision is then closed, so a new ask on DR-9001 is allowed,
    and it inherits DR-9001's floor (VP Sales, set by the declined decision's version 1)."""
    d = Decisions(org)
    v2 = s22_v2_main(org, dealdesk, sarah)
    did = v2.decision_id
    for note in (None, "  "):
        e = refused(partial(d.decline, michael, did, step(2, note)))
        assert (e.status, rules(e)) == (422, ["DC-2"]) and "note" in e.refusals[0].detail
    out = d.decline(michael, did, step(2, "not without the CFO's view"))
    assert out.state == "declined" and out.approvals[0].declined is not None
    assert out.approvals[0].declined.note == "not without the CFO's view"
    for fn in (lambda: d.approve(michael, did, step(2)),
               lambda: d.rerun(sarah, did, RerunRequest(decision_version=2)),
               lambda: d.withdraw(sarah, did, step(2))):  # fmt: skip
        e = refused(fn)
        assert (e.status, rules(e)) == (422, ["DC-2"]) and "declined" in e.refusals[0].detail
    again = ask(org, sarah, "DR-9001")
    assert again.decision_id != did and again.floor is not None
    assert (again.floor.level, again.floor.set_by.decision_id, again.floor.set_by.version) == (
        1, did, 1)  # fmt: skip


def test_decline_is_held_while_a_blocking_condition_is_open(
    org: Org, dealdesk: Actor, michael: Actor
) -> None:
    v1 = ask_s22(org, dealdesk)
    e = refused(lambda: Decisions(org).decline(michael, v1.decision_id, step(1, "no")))
    assert (e.status, rules(e)) == (422, ["DC-4"]) and "c1" in e.refusals[0].detail


def test_withdraw_only_by_requester(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor
) -> None:
    d = Decisions(org)
    v1 = ask_s22(org, dealdesk)
    did = v1.decision_id
    e = refused(lambda: d.withdraw(michael, did, step(1)))
    assert (e.status, rules(e)) == (422, ["DC-2"])
    out = d.withdraw(sarah, did, step(1))
    assert (out.state, out.version) == ("withdrawn", 1)
    e = refused(lambda: d.withdraw(sarah, did, step(1)))
    assert (e.status, rules(e)) == (422, ["DC-2"]) and "withdrawn" in e.refusals[0].detail
    e = refused(lambda: resolve(org, sarah, did, "c1", 1, "confirmed_record"))
    assert (e.status, rules(e)) == (422, ["DC-2"])
    assert ask(org, sarah, "DR-9001").decision_id != did  # the subject is free again


# -- re-running ---------------------------------------------------------------------------------
def test_rerun_is_open_to_the_requester_or_an_approver(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, kelly: Actor
) -> None:
    """Approvals bind to a version: a re-run's version starts with nothing given."""
    d = Decisions(org)
    v2 = s22_v2_main(org, dealdesk, sarah)
    did = v2.decision_id
    e = refused(lambda: d.rerun(kelly, did, RerunRequest(decision_version=2)))
    assert (e.status, rules(e)) == (422, ["DC-2"])
    assert d.approve(michael, did, step(2)).state == "ready"
    v3 = d.rerun(michael, did, RerunRequest(decision_version=2))
    assert (v3.version, v3.state) == (3, "awaiting_approval")
    assert v3.approvals[0].given is None and d.get(did, 2).approvals[0].given is not None
    assert v3.previous is not None and v3.previous.version == 2
    assert v3.previous.what_changed == "Michael Torres asked for a re-run; no conditions remain."
    v4 = d.rerun(sarah, did, RerunRequest(decision_version=3))
    assert v4.version == 4 and v4.as_of == v2.as_of == "2026-09-23"


def test_an_open_condition_carries_with_its_id(org: Org, dealdesk: Actor, sarah: Actor) -> None:
    d = Decisions(org)
    v1 = ask_s22(org, dealdesk)
    v2 = d.rerun(sarah, v1.decision_id, RerunRequest(decision_version=1))
    assert [dump(c) for c in v2.conditions] == [dump(c) for c in v1.conditions]
    assert v2.state == "not_ready" and v2.conditions[0].opened_in_version == 1
    assert v2.previous is not None
    assert v2.previous.what_changed == "Sarah Chen asked for a re-run; c1 is open."


def test_a_confirmed_figure_holds_while_the_row_still_holds_it(
    org: Org, dealdesk: Actor, sarah: Actor
) -> None:
    """A resolved input conflict stays resolved while the row holds the figure that was confirmed.
    When the row changes, a new condition opens with the next id; when it changes back, the
    confirmation covers it again and the newer, unresolved condition goes."""
    d = Decisions(org)
    v2 = s22_v2_main(org, dealdesk, sarah)
    did = v2.decision_id
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "12.0"})
    v3 = d.rerun(sarah, did, RerunRequest(decision_version=2))
    assert [
        (c.id, c.on_record, c.resolved is not None, c.opened_in_version) for c in v3.conditions
    ] == [("c1", 0.15, True, 1), ("c2", 0.12, False, 3)]
    assert v3.state == "not_ready"
    assert v3.conditions[1].what == ("Confirm the discount on DR-9001: submitted 8%, the CRM says "
                                     "12%. The decision is on the CRM's 12%.")  # fmt: skip
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "15.0"})
    v4 = d.rerun(sarah, did, RerunRequest(decision_version=3))
    assert [(c.id, c.resolved is not None) for c in v4.conditions] == [("c1", True)]
    assert v4.state == "awaiting_approval"


def test_a_correction_that_still_differs_opens_a_new_condition(
    org: Org, dealdesk: Actor, sarah: Actor
) -> None:
    v1 = ask_s22(org, dealdesk)
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "12.0"})
    v2 = resolve(org, sarah, v1.decision_id, "c1", 1, "corrected_record", "fixed the CRM")
    c1, c2 = v2.conditions
    assert c1.resolved is not None
    assert (c1.id, c1.resolved.resolution, c1.resolved.note, c1.resolved.rerun_version) == (
        "c1", "corrected_record", "fixed the CRM", 2)  # fmt: skip
    assert (c2.id, c2.source, c2.submitted, c2.on_record, c2.resolved) == (
        "c2", "input_conflict", 0.08, 0.12, None)  # fmt: skip
    assert v2.state == "not_ready"
    assert v2.previous is not None and v2.previous.what_changed == (
        "The CRM now says 12%, changed by the requester; c2 is open.")  # fmt: skip


def test_a_correction_covers_nothing_later(org: Org, dealdesk: Actor, sarah: Actor) -> None:
    """Only a confirmed figure holds. Sarah corrects the CRM to her 8%; when it says 15% again, the
    old correction (on_record 15%) doesn't cover it: a new condition opens."""
    d = Decisions(org)
    v1 = ask_s22(org, dealdesk)
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "8.0"})
    v2 = resolve(org, sarah, v1.decision_id, "c1", 1, "corrected_record")
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "15.0"})
    v3 = d.rerun(sarah, v1.decision_id, RerunRequest(decision_version=2))
    assert [(c.id, c.source, c.resolved is not None) for c in v2.conditions] == [
        ("c1", "input_conflict", True), ("c2", "ratchet", False)]  # fmt: skip
    # back in the VP Sales band, so not below the floor: the open ratchet goes
    assert [(c.id, c.source, c.on_record, c.resolved is not None) for c in v3.conditions] == [
        ("c1", "input_conflict", 0.15, True), ("c3", "input_conflict", 0.15, False)]  # fmt: skip
    assert v3.state == "not_ready" and v3.previous is not None
    assert v3.previous.what_changed == "Sarah Chen asked for a re-run; c3 is open."


def test_an_open_ratchet_carries_and_its_confirmation_holds(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor
) -> None:
    """Still below the floor at the same level: the ratchet keeps its id and the version that
    opened it. Confirming it on a later version lowers the floor to that version's level."""
    d = Decisions(org)
    v1 = ask_s22(org, dealdesk)
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "8.0"})
    v2 = resolve(org, sarah, v1.decision_id, "c1", 1, "corrected_record")
    v3 = d.rerun(sarah, v1.decision_id, RerunRequest(decision_version=2))
    assert [dump(c) for c in v3.conditions] == [dump(c) for c in v2.conditions]
    assert v3.state == "not_ready" and v3.previous is not None
    assert (
        v3.previous.what_changed
        == "Sarah Chen asked for a re-run; the level is still below the floor."
    )
    v4 = resolve(org, michael, v1.decision_id, "c2", 3, "confirmed_lower_level")
    assert v4.state == "ready" and v4.floor is not None and v4.floor.confirmed_by is not None
    assert (v4.floor.level, v4.floor.set_by.version, v4.floor.confirmed_by.id) == (0, 2, "EMP-200")


def test_missing_record_corrected(org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch) -> None:
    """The requester adds the record and resolves the missing_record condition: the re-run reads
    the row. With no row yet, a new missing_record condition opens. The replay has no answers for
    a record nobody holds, so the kernel is handed DR-9001's result."""
    row = org.sor.row("discount_requests", "DR-9001")
    assert row is not None
    real = _lab.decide
    kr = real("discount", evidence=org.evidence,
              inputs={"sid": "pending", "record": row, "as_of": datetime(2026, 9, 23).date()},
              at=datetime(2026, 9, 23).date(), register=org.kernel_register(),
              entries=org.procedures()[0], store=org.procedures()[1], engine=org.engine,
              staff=org.evidence.table("employees"), requested_by=row["requested_by"],
              policy_terms=org.policy_terms, route_mode=False)  # fmt: skip
    seen: list[dict[str, Any]] = []

    def fake(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        seen.append(kw["inputs"])
        return kr

    monkeypatch.setattr(_lab, "decide", fake)
    submitted = {"customer": "CRM-2048", "product": "NS-500", "requested_discount": 0.15}
    v1 = ask(org, sarah, "DR-0001", submitted)
    assert [(c.id, c.source) for c in v1.conditions] == [("c1", "missing_record")]
    v2 = resolve(org, sarah, v1.decision_id, "c1", 1, "corrected_record")
    assert [(c.id, c.source, c.resolved is not None) for c in v2.conditions] == [
        ("c1", "missing_record", True), ("c2", "missing_record", False)]  # fmt: skip
    with org.log.transaction() as tx:
        org.sor.insert(tx, "discount_requests", {**row, "request_id": "DR-0001"},
                       actor=dump(sarah), at=org.clock.now())  # fmt: skip
    v3 = resolve(org, sarah, v1.decision_id, "c2", 2, "corrected_record")
    assert [(c.id, c.resolved is not None) for c in v3.conditions] == [("c1", True), ("c2", True)]
    assert v3.state == "awaiting_approval" and v3.basis.records[0].id == "DR-0001"
    assert seen[-1]["sid"] == v1.decision_id and seen[-1]["as_of"].isoformat() == v1.as_of
    assert v3.previous is not None
    assert v3.previous.what_changed == "The CRM now holds DR-0001; no conditions remain."


def test_a_rerun_keeps_as_of_and_the_requester(
    org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`as_of` is fixed at version 1 (S23's trap): a re-run after the request date was edited
    still reads the policy for the first date. The kernel gets the decision's id as its sid."""
    d = Decisions(org)
    v1 = ask(org, sarah, "DR-9001")
    real = _lab.decide
    seen: list[dict[str, Any]] = []

    def spy(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        seen.append({"inputs": kw["inputs"], "at": kw["at"]})
        return real(kind, **kw)

    monkeypatch.setattr(_lab, "decide", spy)
    edit(org, sarah, "DR-9001", {"request_date": "2026-09-30"})
    v2 = d.rerun(sarah, v1.decision_id, RerunRequest(decision_version=1))
    assert v2.as_of == v1.as_of == "2026-09-23"
    assert seen[0]["at"].isoformat() == "2026-09-23" and seen[0]["inputs"]["sid"] == "DEC-0001"
    assert v2.requested_by == v1.requested_by and v2.requested_at == v1.requested_at


def test_a_rerun_refuses_a_changed_requester(org: Org, sarah: Actor, michael: Actor) -> None:
    """The decision is its requester's: a re-run on a row that now names someone else fails closed
    (503), so an edit can't hand the request to another person mid-decision."""
    d = Decisions(org)
    v1 = ask(org, sarah, "DR-9001")
    edit(org, michael, "DR-9001", {"requested_by": "kelly.floyd@northstar.example"})
    with pytest.raises(CannotDecide, match="requester"):
        d.rerun(sarah, v1.decision_id, RerunRequest(decision_version=1))
    assert d.get(v1.decision_id).version == 1


def test_a_rerun_the_kernel_cannot_make_writes_nothing(
    org: Org, dealdesk: Actor, sarah: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = Decisions(org)
    v1 = ask_s22(org, dealdesk)

    def broken(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        raise CannotDecide("boom")

    monkeypatch.setattr(_lab, "decide", broken)
    with pytest.raises(CannotDecide):
        resolve(org, sarah, v1.decision_id, "c1", 1, "confirmed_record")
    kinds = [e.kind for e in d.events(v1.decision_id)]
    assert kinds == ["decision.versioned", "decision.failed"]
    now = d.get(v1.decision_id)
    assert now.version == 1 and now.conditions[0].resolved is None


def test_sla_rerun_by_the_claim_decider(org: Org, marcus: Actor, sarah: Actor) -> None:
    """SLA has no requester (`requested_by` is null): the claim decision's holder re-runs it, and
    makes the claim decision on the new version."""
    d = Decisions(org)
    v1 = ask(org, marcus, "SR-39385", None, "sla")
    e = refused(lambda: d.rerun(sarah, v1.decision_id, RerunRequest(decision_version=1)))
    assert (e.status, rules(e)) == (422, ["DC-2"])
    v2 = d.rerun(marcus, v1.decision_id, RerunRequest(decision_version=1))
    assert (v2.version, v2.as_of, v2.outcome, v2.conditions, v2.floor) == (
        2, v1.as_of, "BREACH_CREDIT_OWED", [], None)  # fmt: skip
    assert v2.decided_at > v1.decided_at
    assert d.approve(marcus, v1.decision_id, step(2)).state == "ready"


# -- concurrency (spec §5: the kernel outside the lock, each write re-checks) --------------------
def _in_thread(fn: Callable[[], DecisionRecord], name: str) -> tuple[threading.Thread, list[Any]]:
    out: list[Any] = []

    def run() -> None:
        try:
            out.append(fn())
        except Exception as e:  # noqa: BLE001 - the test inspects it
            out.append(e)

    t = threading.Thread(target=run, name=name)
    t.start()
    return t, out


def test_concurrent_approve_and_rerun_one_wins(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The re-run's kernel is held until the approval lands: the approval wins, and the re-run's
    write finds the subject moved and is refused with 409."""
    v2 = s22_v2_main(org, dealdesk, sarah)
    did = v2.decision_id
    real = _lab.decide
    entered, approved = threading.Event(), threading.Event()

    def held(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        entered.set()
        assert approved.wait(10)
        return real(kind, **kw)

    monkeypatch.setattr(_lab, "decide", held)
    t, rerun_out = _in_thread(
        lambda: Decisions(org).rerun(sarah, did, RerunRequest(decision_version=2)), "rerun"
    )
    assert entered.wait(10)
    approve_out = Decisions(org).approve(michael, did, step(2))
    approved.set()
    t.join(10)
    outcomes = [approve_out, *rerun_out]
    assert sum(isinstance(x, DecisionRecord) for x in outcomes) == 1
    loser = rerun_out[0]
    assert isinstance(loser, Refused) and (loser.status, rules(loser)) == (409, ["DC-5"])
    now = Decisions(org).get(did)
    assert (now.version, now.state) == (2, "ready")


def test_a_held_approve_loses_to_a_rerun(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The approval passes its checks on version 2, then waits at its write while a re-run writes
    version 3: the approval's write re-checks DC-5 and is refused with 409."""
    v2 = s22_v2_main(org, dealdesk, sarah)
    did = v2.decision_id
    real_tx = org.log.transaction
    at_write, rerun_done = threading.Event(), threading.Event()

    @contextmanager
    def held_tx() -> Iterator[Any]:
        if threading.current_thread().name == "approve":
            at_write.set()
            assert rerun_done.wait(10)
        with real_tx() as tx:
            yield tx

    monkeypatch.setattr(org.log, "transaction", held_tx)
    t, approve_out = _in_thread(lambda: Decisions(org).approve(michael, did, step(2)), "approve")
    assert at_write.wait(10)
    v3 = Decisions(org).rerun(sarah, did, RerunRequest(decision_version=2))
    rerun_done.set()
    t.join(10)
    (loser,) = approve_out
    assert v3.version == 3
    assert isinstance(loser, Refused) and (loser.status, rules(loser)) == (409, ["DC-5"])
    now = Decisions(org).get(did)
    assert (now.version, now.state, now.approvals[0].given) == (3, "awaiting_approval", None)


# -- the log is the record ----------------------------------------------------------------------
def test_state_rebuilt_from_the_log_equals_the_live_state(
    org: Org, tmp_path: Path, dealdesk: Actor, sarah: Actor, michael: Actor
) -> None:
    """Both S22 branches, then a fresh Org on the same log: every version reads back the same, and
    the step events carry the payloads `state.py` reads."""
    d = Decisions(org)
    v1 = ask_s22(org, dealdesk)
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "8.0"})
    resolve(org, sarah, v1.decision_id, "c1", 1, "corrected_record")
    resolve(org, michael, v1.decision_id, "c2", 2, "confirmed_lower_level")
    d.withdraw(sarah, v1.decision_id, step(3))
    edit(org, sarah, "DR-9001", {"requested_discount_pct": "15.0"})
    second = ask(org, sarah, "DR-9001", {"requested_discount": 0.15})
    d.approve(michael, second.decision_id, step(1))
    live = {(r.decision_id, n): dump(d.get(r.decision_id, n))
            for r in d.list() for n in range(1, r.version + 1)}  # fmt: skip
    again = Decisions(Org(load_settings({"OWM_STATE_DIR": str(tmp_path / "state")})))
    assert {k: dump(again.get(*k)) for k in live} == live
    kinds = [e.kind for e in d.events(v1.decision_id)]
    assert kinds == [
        "decision.versioned",
        "condition.resolved",
        "decision.versioned",
        "condition.resolved",
        "decision.versioned",
        "decision.withdrawn",
    ]
    resolved = [e.payload for e in d.events(v1.decision_id) if e.kind == "condition.resolved"]
    assert [(p["condition_id"], p["resolved"]["rerun_version"]) for p in resolved] == [
        ("c1", 2), ("c2", 3)]  # fmt: skip
    approved = next(e for e in d.events(second.decision_id) if e.kind == "decision.approved")
    assert (approved.payload["version"], approved.payload["index"]) == (1, 0)
    assert approved.payload["given"]["by"] == MICHAEL
    # the second decision's 15% is back in the VP Sales band: the floor rises again
    assert second.floor is not None and second.floor.level == 1
