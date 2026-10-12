"""The register queue (B-06 Task 16; spec §7.1, §7.4, §7.5; contract §4.2-4.4 at 30977cd): the
contract's two steps over the lab's one-shot registrar, with stored drafts (B-11).

A draft is a dry `apply` with stand-ins (the owning function's head submits, an Executive
approves) whose first refusal becomes `checks`. A submit is a dry `apply` with the real submitter
and a stand-in approver against the `base_version` the submitter sends. An approval runs scoped
RR-13 first, then the real `apply` against the register as it is now. Approved results are stored
and replayed on rebuild; no rule runs again. Every `apply` reads the service clock (RR-9)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import BaseModel

from owm_service import _lab
from owm_service.config import load_settings
from owm_service.errors import NotFound, Refused
from owm_service.models import Actor, RefusalFix, RegisterChange, SupersedesRelation
from owm_service.org import Org
from owm_service.register_queue import ChangeBody, RegisterQueue
from owm_service.sessions import Sessions

from ._registrar import CHECK

LAB = Path(__file__).resolve().parents[2]
CASES = LAB / "runs/2026-10-08-register-attacks/sealed/cases"
DROP = frozenset({"submit_by", "approve_by", "file", "proposed_by", "text"})


# -- fixtures and builders ----------------------------------------------------------------------
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
def priya(org: Org) -> Actor:
    return _person(org, "EMP-401")


@pytest.fixture
def elena(org: Org) -> Actor:
    return _person(org, "EMP-402")


@pytest.fixture
def hannah(org: Org) -> Actor:
    return _person(org, "EMP-601")


@pytest.fixture
def marcus(org: Org) -> Actor:
    return _person(org, "EMP-602")


@pytest.fixture
def dealdesk(org: Org) -> Actor:
    return Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")[1]


def dump(m: BaseModel) -> dict[str, Any]:
    """As the service serves it (ruling R13): absent `?:` fields stay absent."""
    return m.model_dump(mode="json", exclude_unset=True)


def body(change: dict[str, Any], text: str | None, *, submit: bool, **over: Any) -> ChangeBody:
    """A registrar-format change (check_registrar, the attack cases) as the queue's input."""
    fields = {k: v for k, v in change.items() if k not in DROP}
    return ChangeBody.model_validate(fields | {"text": text, "submit": submit} | over)


def credit(*, submit: bool = True, text: str | None = None, **over: Any) -> ChangeBody:
    """Finance's 2027 credit policy, superseding 2026 (check_registrar L1)."""
    return body(CHECK.credit_2027(), text or CHECK.text_2027_credit(), submit=submit, **over)


def edge(on: str = "2026-10-01", *, submit: bool = False, **over: Any) -> ChangeBody:
    """Sales's second Acme exception (check_registrar L2), effective `on`."""
    change, text = CHECK.exception_edge()
    return body(change | {"effective_from": on}, text.replace("2026-09-10", on), submit=submit,
                **over)  # fmt: skip


def revoke_brl(on: str = "2026-10-01", **over: Any) -> ChangeBody:
    """Customer Support revokes BlueRiver's support terms from `on` (check_registrar L3)."""
    raw = {"action": "revoke", "base_version": 17, "target": "SUP-BRL-2025", "revoked_on": on,
           "submit": True}  # fmt: skip
    return ChangeBody.model_validate(raw | over)


def case(name: str, *, submit: bool = True, **over: Any) -> ChangeBody:
    """An attack case's first change, as written."""
    change = yaml.safe_load((CASES / f"{name}.yaml").read_text())["changes"][0]
    return body(change, (CASES / change["text"]).read_text(), submit=submit, **over)


def mandate(*, submit: bool) -> ChangeBody:
    text = "---\ndoc_id: MANDATE-X-2027\ntitle: X mandate\n---\nThe X agent may ask.\n"
    return ChangeBody(
        action="register", base_version=17, doc_id="MANDATE-X-2027", kind="agent_mandate",
        title="X mandate", text=text, effective_from="2027-01-01", effective_to=None, terms={},
        relations=[], submit=submit,
    )  # fmt: skip


def refused(e: pytest.ExceptionInfo[Refused]) -> tuple[int, list[str]]:
    return e.value.status, [r.rule for r in e.value.refusals]


def entry(org: Org, doc_id: str) -> dict[str, Any]:
    found: dict[str, Any] = next(e for e in org.register_state().entries if e["doc_id"] == doc_id)
    return found


def ids(changes: list[Any]) -> list[str]:
    return [c.change_id for c in changes]


# -- drafts -------------------------------------------------------------------------------------
def test_agent_draft_is_stored_with_checks(org: Org, dealdesk: Actor) -> None:
    q = RegisterQueue(org)
    ok = q.draft(dealdesk, edge())
    assert (ok.change_id, ok.state, ok.base_version) == ("CHG-0001", "draft", 17)
    assert ok.proposed_by == dealdesk and ok.proposed_at is not None
    assert datetime.fromisoformat(ok.proposed_at).date() == org.clock.today()
    assert ok.checks == [] and "checks" in dump(ok)
    assert (ok.submitted_by, ok.submitted_at, ok.approvers) == (None, None, [])
    assert ok.doc_id == "EXC-ACME-EDGE-12" and ok.kind == "exception" and ok.sha256
    assert q.get(ok.change_id) == ok
    bad = q.draft(dealdesk, edge(on="2026-09-10"))
    assert [c.rule for c in bad.checks or []] == ["RR-9"]
    # the stand-in runs were thrown away: the register didn't move
    assert org.register_state().version == 17 and len(org.register_state().entries) == 17


def test_draft_without_a_head_uses_an_executive_and_reports_rr3(org: Org, sarah: Actor) -> None:
    q = RegisterQueue(org)
    rows = {e: dict(r) for e, r in q.staff.rows.items()}
    rows["EMP-101"]["manager_id"] = "EMP-300"  # two Sales members now report outside Sales
    q.staff = _lab.Staff(rows)
    assert q.staff.head("Sales") is None
    d = q.draft(sarah, edge())
    assert [c.rule for c in d.checks or []] == ["RR-3"]


def test_draft_submitted_by_a_person_with_their_base_version(
    org: Org, dealdesk: Actor, michael: Actor, priya: Actor, elena: Actor, david: Actor
) -> None:
    q = RegisterQueue(org)
    d = q.draft(dealdesk, edge())  # at version 17
    q.approve(elena, q.submit_new(priya, credit()).change_id)  # an unrelated change: 18
    assert org.register_state().version == 18
    with pytest.raises(Refused) as stale:
        q.submit(michael, d.change_id, 17)  # the drafter's base is stale now
    assert refused(stale) == (409, ["RR-13"])
    assert q.get(d.change_id).state == "draft"
    p = q.submit(michael, d.change_id, 18)  # the base Michael reviewed it against
    assert (p.state, p.base_version) == ("pending", 18)
    assert p.submitted_by == org.people.ref("EMP-200") and p.submitted_at is not None
    assert p.proposed_by == dealdesk and p.proposed_at == d.proposed_at
    assert [a.id for a in p.approvers] == ["EMP-300"]  # the head submitted: the Executive approves
    assert p.checks is None and "checks" not in dump(p)
    done = q.approve(david, p.change_id)
    assert done.state == "approved" and org.register_state().version == 19
    e = entry(org, "EXC-ACME-EDGE-12")
    assert e["proposed_by"] == dealdesk.model_dump(mode="json")
    assert e["registered_by"] == "Michael Torres (EMP-200, VP Sales)"
    assert e["approved_by"] == "David Morgan (EMP-300, Chief Revenue Officer)"
    assert e["registered_on"] == e["approved_on"] == "2026-09-23"  # the service clock's date


def test_submit_with_stale_base_is_409(org: Org, priya: Actor) -> None:
    q = RegisterQueue(org)
    with pytest.raises(Refused) as e:
        q.submit_new(priya, credit(base_version=16))
    assert refused(e) == (409, ["RR-13"])
    assert q.list() == []  # nothing queued


def test_dismiss_draft_rules(org: Org, dealdesk: Actor, sarah: Actor, priya: Actor) -> None:
    q = RegisterQueue(org)
    d = q.draft(dealdesk, edge())
    with pytest.raises(Refused) as e:
        q.withdraw(priya, d.change_id)  # Finance doesn't own an exception
    assert refused(e) == (422, ["RR-3"])
    assert q.get(d.change_id).state == "draft"
    assert q.withdraw(sarah, d.change_id).state == "withdrawn"
    with pytest.raises(Refused) as closed:
        q.withdraw(sarah, d.change_id)
    assert refused(closed) == (422, ["DC-2"])


def test_a_pending_change_is_withdrawn_by_its_submitter_only(
    org: Org, priya: Actor, elena: Actor
) -> None:
    q = RegisterQueue(org)
    p = q.submit_new(priya, credit())
    with pytest.raises(Refused) as e:
        q.withdraw(elena, p.change_id)
    assert refused(e) == (422, ["RR-3"])
    assert q.withdraw(priya, p.change_id).state == "withdrawn"
    with pytest.raises(Refused) as closed:
        q.approve(elena, p.change_id)
    assert refused(closed) == (422, ["DC-2"])


# -- approval -----------------------------------------------------------------------------------
def test_approve_happy_path_bumps_version(org: Org, sarah: Actor, michael: Actor) -> None:
    q = RegisterQueue(org)
    p = q.submit_new(sarah, case("C09"))
    assert p.state == "pending" and [a.id for a in p.approvers] == ["EMP-200", "EMP-300"]
    assert (p.proposed_by, p.proposed_at) == (None, None)  # submitted directly
    assert {d.key for d in p.diff} >= {"effective_from", "effective_to"}  # against 2027
    a = q.approve(michael, p.change_id)
    assert a.state == "approved" and a.approved_by == org.people.ref("EMP-200")
    assert a.approved_at is not None and a.refused is None
    state = org.register_state()
    assert state.version == 18
    e = entry(org, "PRICING-POLICY-2028")
    assert e["proposed_by"] is None and e["sha256"] == p.sha256
    text = (CASES / "C09/c09.md").read_text()
    assert state.store[e["sha256"]] == text
    assert (org.dir / "register-store" / f"{e['sha256']}.md").read_text() == text


def test_kernel_register_cache_moves_with_the_version(
    org: Org, sarah: Actor, michael: Actor
) -> None:
    q = RegisterQueue(org)
    before = org.kernel_register()
    assert org.kernel_register() is before and "PRICING-POLICY-2028" not in before.by_id()
    q.approve(michael, q.submit_new(sarah, case("C09")).change_id)
    after = org.kernel_register()
    assert after is not before and "PRICING-POLICY-2028" in after.by_id()
    assert org.kernel_register() is after


def test_rr13_at_approval_leaves_refused(org: Org, priya: Actor, elena: Actor) -> None:
    q = RegisterQueue(org)
    first = q.submit_new(priya, credit())
    second = q.submit_new(priya, credit(text=CHECK.text_2027_credit() + "\nReviewed annually.\n"))
    assert second.state == "pending"  # each passed its own dry run at 17
    q.approve(elena, first.change_id)
    with pytest.raises(Refused) as e:
        q.approve(elena, second.change_id)  # credit_policy for the company moved since submit
    assert refused(e) == (409, ["RR-13"])
    got = q.get(second.change_id)
    assert got.state == "refused" and [r.rule for r in got.refused or []] == ["RR-13"]
    assert got.approved_by is None and org.register_state().version == 18
    with pytest.raises(Refused) as closed:
        q.approve(elena, second.change_id)
    assert refused(closed) == (422, ["DC-2"])


def test_a_change_elsewhere_does_not_hold_approval(
    org: Org, priya: Actor, elena: Actor, hannah: Actor, marcus: Actor
) -> None:
    q = RegisterQueue(org)
    c = q.submit_new(priya, credit())
    r = q.submit_new(hannah, revoke_brl())
    q.approve(elena, c.change_id)
    done = q.approve(marcus, r.change_id)  # submitted at 17; applied at 18, the register now
    assert done.state == "approved" and org.register_state().version == 19


def test_a_rule_failing_at_approval_leaves_refused(org: Org, hannah: Actor, marcus: Actor) -> None:
    q = RegisterQueue(org)
    p = q.submit_new(hannah, revoke_brl("2026-10-01"))
    org.clock.set(datetime.fromisoformat("2026-10-05T09:00:00-05:00"), None)
    with pytest.raises(Refused) as e:
        q.approve(marcus, p.change_id)  # the revocation is now backdated (RR-9)
    assert refused(e) == (422, ["RR-9"])
    got = q.get(p.change_id)
    assert got.state == "refused" and [r.rule for r in got.refused or []] == ["RR-9"]
    assert org.register_state().version == 17


def test_submitter_cannot_approve(org: Org, priya: Actor, michael: Actor) -> None:
    q = RegisterQueue(org)
    p = q.submit_new(priya, credit())
    assert [a.id for a in p.approvers] == ["EMP-402", "EMP-300"]
    for who in (priya, michael):  # the submitter; a head of another function
        with pytest.raises(Refused) as e:
            q.approve(who, p.change_id)
        assert refused(e) == (422, ["RR-4"])
    assert q.get(p.change_id).state == "pending"


def test_decline_needs_an_approver_and_a_note(org: Org, priya: Actor, elena: Actor) -> None:
    q = RegisterQueue(org)
    p = q.submit_new(priya, credit())
    with pytest.raises(Refused) as e:
        q.decline(priya, p.change_id, "no")
    assert refused(e) == (422, ["RR-4"])
    with pytest.raises(Refused) as blank:
        q.decline(elena, p.change_id, "  ")
    assert refused(blank) == (422, ["DC-2"])
    d = q.decline(elena, p.change_id, "Keep 2026's caps for now.")
    assert d.state == "declined" and d.refused is None
    assert d.declined is not None and d.declined.by == org.people.ref("EMP-402")
    assert d.declined.note == "Keep 2026's caps for now."


# -- refusals -----------------------------------------------------------------------------------
def test_c08_refusal_carries_unmatched(org: Org, sarah: Actor) -> None:
    q = RegisterQueue(org)
    with pytest.raises(Refused) as e:
        q.submit_new(sarah, case("C08"))
    assert refused(e) == (422, ["RR-6"])
    r = e.value.refusals[0]
    assert r.unmatched == "does not grant approval authority"
    assert set(dump(r)) == {"rule", "detail", "unmatched"}  # absent fields omitted (R13)
    assert not r.detail.startswith("RR-6")
    d = q.draft(sarah, case("C08", submit=False))
    assert [dump(c) for c in d.checks or []] == [dump(r)]


def test_rr10_refusal_offers_fix(org: Org, hannah: Actor) -> None:
    q = RegisterQueue(org)
    with pytest.raises(Refused) as e:
        q.submit_new(hannah, case("C04"))
    assert refused(e) == (422, ["RR-10"])
    r = e.value.refusals[0]
    target = SupersedesRelation(type="supersedes", target="HR-HOLIDAYS-2025-26")
    assert r.fix == RefusalFix(relations=[target])
    assert set(dump(r)) == {"rule", "detail", "fix"}


def test_people_refusals_omit_absent_fields(org: Org, sarah: Actor) -> None:
    with pytest.raises(Refused) as e:
        RegisterQueue(org).submit_new(sarah, credit())  # Sales submits a credit policy
    assert refused(e) == (422, ["RR-3"])
    assert set(dump(e.value.refusals[0])) == {"rule", "detail"}


def test_revoke_flow(org: Org, hannah: Actor, marcus: Actor) -> None:
    q = RegisterQueue(org)
    p = q.submit_new(hannah, revoke_brl())
    assert (p.action, p.target, p.revoked_on) == ("revoke", "SUP-BRL-2025", "2026-10-01")
    assert not {"doc_id", "kind", "terms", "effective_to", "sha256"} & set(dump(p))
    assert [a.id for a in p.approvers] == ["EMP-602", "EMP-300"]
    assert q.approve(marcus, p.change_id).state == "approved"
    e = entry(org, "SUP-BRL-2025")
    assert e["revoked_on"] == "2026-10-01"
    assert e["revoked_by"] == "Hannah Lindqvist (EMP-601, Support Escalation Manager)"
    assert e["revocation_approved_by"] == "Marcus Adeyemi (EMP-602, Director of Customer Support)"
    assert org.register_state().version == 18


def test_agent_mandate_kind_is_rr5(org: Org, michael: Actor) -> None:
    q = RegisterQueue(org)
    with pytest.raises(Refused) as e:
        q.submit_new(michael, mandate(submit=True))  # the registrar doesn't know the kind
    assert refused(e) == (422, ["RR-5"])
    assert "agent_mandate" in e.value.refusals[0].detail
    assert [c.rule for c in q.draft(michael, mandate(submit=False)).checks or []] == ["RR-5"]


def test_no_backdating_against_the_clock(org: Org, michael: Actor) -> None:
    # effective 2026-09-10: after the registrar's own clock (2026-09-01), which admits it (L2),
    # but before the service clock's date, 2026-09-23
    with pytest.raises(Refused) as e:
        RegisterQueue(org).submit_new(michael, edge(on="2026-09-10", submit=True))
    assert refused(e) == (422, ["RR-9"])
    assert "2026-09-23" in e.value.refusals[0].detail


def test_a_change_the_registrar_cant_read_is_rr5_not_a_crash(org: Org, priya: Actor) -> None:
    q = RegisterQueue(org)
    terms = dict(CHECK.credit_2027()["terms"], bands="every band")  # a string, not a list
    with pytest.raises(Refused) as e:
        q.submit_new(priya, credit(terms=terms))
    assert refused(e) == (422, ["RR-5"])
    assert [c.rule for c in q.draft(priya, credit(submit=False, terms=terms)).checks or []] == [
        "RR-5"
    ]


@pytest.mark.parametrize(
    "raw",
    [
        {"action": "revoke", "target": "SUP-BRL-2025", "doc_id": "X"},  # a document on a revoke
        {"action": "revoke", "target": "SUP-BRL-2025", "text": "---\n---\n"},
        {"action": "revoke"},  # no target
        {"action": "register", "doc_id": "X", "effective_from": "2027-01-01"},  # no kind
        {"action": "register", "doc_id": "X", "kind": "exception", "effective_from": "2027-13-01"},
        {
            "action": "register",
            "doc_id": "X",
            "kind": "exception",
            "effective_from": "2027-01-01",
            "target": "Y",
        },  # a target on a register
        {"action": "revoke", "target": "SUP-BRL-2025", "as_of": "2026-09-23"},  # an extra field
    ],
)
def test_a_body_that_doesnt_fit_its_action_is_invalid(raw: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        ChangeBody.model_validate(raw | {"base_version": 17, "submit": False})


# -- who may act --------------------------------------------------------------------------------
def test_agents_draft_but_never_take_a_people_step(org: Org, dealdesk: Actor, priya: Actor) -> None:
    q = RegisterQueue(org)
    d = q.draft(dealdesk, edge())
    p = q.submit_new(priya, credit())
    steps: list[Callable[[], RegisterChange]] = [
        lambda: q.submit_new(dealdesk, edge(submit=True)),
        lambda: q.submit(dealdesk, d.change_id, 17),
        lambda: q.approve(dealdesk, p.change_id),
        lambda: q.decline(dealdesk, p.change_id, "no"),
        lambda: q.withdraw(dealdesk, d.change_id),
        lambda: q.remind(dealdesk, p.change_id),
    ]
    for step in steps:
        with pytest.raises(Refused) as e:
            step()
        assert refused(e) == (422, ["RR-2"])
    assert (q.get(d.change_id).state, q.get(p.change_id).state) == ("draft", "pending")


def test_a_body_principal_that_differs_is_rr1(
    org: Org, michael: Actor, dealdesk: Actor, sarah: Actor
) -> None:
    q = RegisterQueue(org)
    for actor, b in [
        (michael, edge(submit=True, submitted_by="EMP-101")),
        (michael, edge(submitted_by="EMP-101")),
        (michael, edge(proposed_by=dealdesk.model_dump(mode="json"))),
        (dealdesk, edge(submitted_by="EMP-101")),
        (dealdesk, edge(proposed_by=sarah.model_dump(mode="json"))),
    ]:
        with pytest.raises(Refused) as e:
            (q.submit_new if b.submit else q.draft)(actor, b)
        assert refused(e) == (403, ["RR-1"])
    assert q.list() == []
    ok = q.submit_new(michael, edge(submit=True, submitted_by="EMP-200",
                                   proposed_by=michael.model_dump(mode="json")))  # fmt: skip
    assert ok.state == "pending" and ok.submitted_by == org.people.ref("EMP-200")


def test_remind_is_the_submitters_once_a_day(org: Org, priya: Actor, elena: Actor) -> None:
    q = RegisterQueue(org)
    p = q.submit_new(priya, credit())
    assert q.remind(priya, p.change_id) == q.get(p.change_id)
    with pytest.raises(Refused) as again:
        q.remind(priya, p.change_id)
    assert refused(again) == (422, ["DC-2"])
    with pytest.raises(Refused) as other:
        q.remind(elena, p.change_id)
    assert refused(other) == (422, ["RR-3"])
    org.clock.set(datetime.fromisoformat("2026-09-24T09:00:00-05:00"), None)
    q.remind(priya, p.change_id)
    reminded = [e for e in org.log.read(org.org_id, stream=f"change:{p.change_id}")
                if e.kind == "change.reminded"]  # fmt: skip
    assert [e.payload["on"] for e in reminded] == ["2026-09-23", "2026-09-24"]


# -- reads --------------------------------------------------------------------------------------
def test_get_includes_drafts_and_unknown_is_404(org: Org, sarah: Actor) -> None:
    q = RegisterQueue(org)
    d = q.draft(sarah, edge())
    assert q.get(d.change_id).state == "draft"
    with pytest.raises(NotFound):
        q.get("CHG-9999")


def test_list_by_state_and_waiting_on(
    org: Org, dealdesk: Actor, priya: Actor, hannah: Actor
) -> None:
    q = RegisterQueue(org)
    a = q.draft(dealdesk, edge())  # an agent's draft: work for all of Sales
    b = q.draft(priya, credit(submit=False))  # a person's own draft stays with them
    c = q.submit_new(hannah, revoke_brl())  # pending: Customer Support's head, the Executive
    assert ids(q.list()) == ["CHG-0001", "CHG-0002", "CHG-0003"]
    assert ids(q.list(state="draft")) == [a.change_id, b.change_id]
    assert ids(q.list(state="pending")) == [c.change_id]
    assert ids(q.list(waiting_on="EMP-101")) == [a.change_id]
    assert ids(q.list(waiting_on="EMP-401")) == [b.change_id]
    assert ids(q.list(waiting_on="EMP-300")) == [c.change_id]
    assert ids(q.list(state="pending", waiting_on="EMP-101")) == []
    sales = {
        r["employee_id"] for r in org.evidence.table("employees") if r["department"] == "Sales"
    }
    assert {p.id for p in q.waiting_on(a.change_id)} == sales
    assert [p.id for p in q.waiting_on(b.change_id)] == ["EMP-401"]
    assert [p.id for p in q.waiting_on(c.change_id)] == ["EMP-602", "EMP-300"]


# -- rebuild ------------------------------------------------------------------------------------
def test_rebuild_does_not_rerun_rules(
    org: Org, tmp_path: Path, sarah: Actor, michael: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    q = RegisterQueue(org)
    p = q.submit_new(sarah, case("C09"))
    q.approve(michael, p.change_id)
    live = org.register_state()

    def tightened(*args: Any, **kwargs: Any) -> Any:
        raise _lab.RefusedError("RR-6", "a rule that tightened after the approval")

    monkeypatch.setattr(_lab._registrar, "apply", tightened)
    again = Org(load_settings({"OWM_STATE_DIR": str(tmp_path / "state")}))
    state = again.register_state()
    assert state.version == 18 and state.entries == live.entries and state.store == live.store
    assert RegisterQueue(again).get(p.change_id) == q.get(p.change_id)
    assert RegisterQueue(again).get(p.change_id).state == "approved"
