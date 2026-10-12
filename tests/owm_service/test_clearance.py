"""Clearance, redemption and reporting (B-06 Task 13; spec §6.7, contract §5.9 and §7). Replay only.

An agent or a person asks for a clearance on a decided action. The OWM refuses it with every failing
check, in the contract's order, or issues a single-use, five-minute clearance bound to the version,
the params and the session's actor. Redeeming it spends the action for its subject, whichever
decision asks; a report closes the loop, and a failed one opens an incident and stays spent."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from owm_service import _lab
from owm_service.clearance import Clearances
from owm_service.clock import DEMO_TZ
from owm_service.config import load_settings
from owm_service.decisions import Decisions
from owm_service.errors import NotFound, Refused
from owm_service.models import (
    Actor,
    ClearanceRequest,
    Cleared,
    DecisionRecord,
    DecisionRequest,
    Executor,
    NotCleared,
    NotRedeemed,
    Redeemed,
    RedeemRequest,
    ReportRequest,
    RerunRequest,
    ResolveRequest,
    StepRequest,
)
from owm_service.org import Org
from owm_service.sessions import Mandates, MandateTerms, Sessions

LAB = Path(__file__).resolve().parents[2]
EXAMPLE: dict[str, Any] = json.loads(
    (LAB / "lab/owm_service/contract/s22.example.json").read_text()
)
P15: dict[str, Any] = {"request_id": "DR-9001", "account_id": "CRM-2048", "product": "NS-500",
                       "discount": 0.15}  # fmt: skip
P8 = {**P15, "discount": 0.08}
EXEC = Executor(system="crm", adapter="lab-adapter")
CONFIRM = ResolveRequest(decision_version=1, resolution="confirmed_record")  # S22's c1, Sarah


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
def marcus(org: Org) -> Actor:
    return _person(org, "EMP-602")


@pytest.fixture
def paul(org: Org) -> Actor:
    return _person(org, "EMP-604")


@pytest.fixture
def dealdesk(org: Org) -> Actor:
    return Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")[1]


@pytest.fixture
def c(org: Org) -> Clearances:
    return Clearances(org, Decisions(org))


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


def step(version: int, note: str | None = None) -> StepRequest:
    return StepRequest.model_validate(
        {"decision_version": version} | ({} if note is None else {"note": note}))  # fmt: skip


def ready_s22(org: Org, dealdesk: Actor, sarah: Actor, michael: Actor) -> DecisionRecord:
    """S22's main branch to version 2, ready: Sarah confirms the CRM's 15%, Michael approves."""
    d = Decisions(org)
    v1 = ask_s22(org, dealdesk)
    d.resolve(sarah, v1.decision_id, "c1", CONFIRM)
    v2 = d.approve(michael, v1.decision_id, step(2))
    assert (v2.version, v2.state) == (2, "ready")
    return v2


def creq(
    rec: DecisionRecord, params: dict[str, Any], *, version: int | None = None,
    action: str | None = None, **extra: Any,
) -> ClearanceRequest:  # fmt: skip
    if action is None:
        action = rec.actions[0].action
    return ClearanceRequest.model_validate({
        "decision_id": rec.decision_id,
        "decision_version": rec.version if version is None else version,
        "action": action, "params": params, **extra,
    })  # fmt: skip


def cleared(r: Cleared | NotCleared) -> Cleared:
    assert isinstance(r, Cleared), dump(r)
    return r


def refused_with(r: Cleared | NotCleared) -> NotCleared:
    assert isinstance(r, NotCleared), dump(r)
    return r


def codes(r: Cleared | NotCleared | Redeemed | NotRedeemed) -> list[str]:
    assert isinstance(r, NotCleared | NotRedeemed), dump(r)
    return [x.code for x in r.reasons]


def clear15(c: Clearances, actor: Actor, rec: DecisionRecord) -> Cleared:
    return cleared(c.ask(actor, rec.decision_id, creq(rec, P15)))


def redeem(c: Clearances, ok: Cleared, params: dict[str, Any] | None = None
           ) -> Redeemed | NotRedeemed:  # fmt: skip
    body = RedeemRequest(params=ok.bound.params if params is None else params, executor=EXEC)
    return c.redeem(ok.clearance_id, body)


def report(c: Clearances, cid: str, status: str) -> str | None:
    body = ReportRequest.model_validate({"status": status, "external_ref": "X-1", "detail": None})
    return c.report(cid, body).incident_id


def hhmm(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(DEMO_TZ).strftime("%H:%M")


def refused(fn: Callable[[], object]) -> Refused:
    with pytest.raises(Refused) as e:
        fn()
    return e.value


def kinds_on(org: Org, stream: str) -> list[str]:
    return [e.kind for e in org.log.read(org.org_id, stream=stream)]


class OneMandate:
    """A mandate book holding one agent's terms (Clearances takes any `for_agent` lookup)."""

    def __init__(self, terms: MandateTerms) -> None:
        self.terms = terms

    def for_agent(self, agent_id: str) -> MandateTerms | None:
        return self.terms if agent_id == self.terms.agent.id else None


def dealdesk_terms(org: Org, **may_do: Any) -> OneMandate:
    """The Deal Desk mandate with its one `may_do` entry changed."""
    terms = Mandates(org).for_agent("AGT-DEALDESK")
    assert terms is not None
    entry = terms.may_do[0].model_copy(update=may_do)
    return OneMandate(terms.model_copy(update={"may_do": [entry]}))


# -- the contract's S22 clearances (§10) ----------------------------------------------------------
def test_refused8_matches_the_contract(org: Org, dealdesk: Actor, c: Clearances) -> None:
    v1 = ask_s22(org, dealdesk)
    r = refused_with(c.ask(dealdesk, v1.decision_id, creq(v1, P8)))
    assert codes(r) == ["differs", "condition_open", "awaiting_approval"]
    ex = EXAMPLE["refused8"]["reasons"]
    got = [dump(x) for x in r.reasons]
    assert got[0] == ex[0]  # "15% was decided; 8% was asked for."
    assert got[2] == ex[2]  # "The VP Sales approves.", waiting on Michael
    assert {k: got[1][k] for k in ("code", "waiting_on", "condition_id")} == {
        k: ex[1][k] for k in ("code", "waiting_on", "condition_id")}  # fmt: skip
    assert got[1]["detail"] == v1.conditions[0].what  # the condition, as the decision words it
    assert org.log.clearances() == []


def test_cleared_then_used_then_spent(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    before = org.clock.now()
    ok = clear15(c, dealdesk, v2)
    after = org.clock.now()
    ex = EXAMPLE["cleared15"]
    got = dump(ok)
    assert (got["cleared"], got["single_use"]) == (True, True)
    assert got["clearance_id"] == "CLR-00001"
    assert got["bound"] == {**ex["bound"], "decision_id": v2.decision_id, "actor": dump(dealdesk)}
    expires = datetime.fromisoformat(ok.expires_at)
    assert before + timedelta(seconds=300) <= expires <= after + timedelta(seconds=300)
    done = redeem(c, ok)
    assert isinstance(done, Redeemed) and done.redeemed
    again = redeem(c, ok)
    assert codes(again) == ["used"]
    assert isinstance(again, NotRedeemed)
    assert again.reasons[0].detail == f"{ok.clearance_id} was redeemed at {hhmm(done.at)}."
    r = refused_with(c.ask(dealdesk, v2.decision_id, creq(v2, P15)))
    assert [dump(x) for x in r.reasons] == [{
        "code": "spent",
        "detail": f"apply_discount on DR-9001 was executed by {v2.decision_id} under "
                  f"{ok.clearance_id} at {hhmm(done.at)}.",
    }]  # fmt: skip
    rec = Decisions(org).get(v2.decision_id)
    assert rec.state == "spent"
    assert [dump(x) for x in rec.executed] == [{
        "action": "apply_discount", "decision_id": v2.decision_id, "version": 2,
        "clearance_id": ok.clearance_id, "redeemed_at": done.at, "report": None,
        "incident_id": None,
    }]  # fmt: skip
    (row,) = org.log.executions()
    assert (row.subject, row.action, row.clearance_id, row.redeemed_at) == (
        "DR-9001", "apply_discount", ok.clearance_id, done.at)  # fmt: skip
    used = org.log.get_clearance(ok.clearance_id)
    assert used is not None and used.used_at == done.at


def test_a_later_decision_is_spent_from_version_one(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances
) -> None:
    """The contract's `laterDecision`: DEC-0001 is no longer live, so a new decision on DR-9001 can
    be made, but apply_discount is spent for the subject, so it's spent from version 1."""
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    done = redeem(c, ok)
    assert isinstance(done, Redeemed)
    assert report(c, ok.clearance_id, "applied") is None
    later = ask(org, sarah, "DR-9001")
    assert (later.decision_id, later.version, later.state, later.conditions) == (
        "DEC-0002", 1, "spent", [])  # fmt: skip
    ex = dict(EXAMPLE["laterDecision"]["executed"][0], decision_id=v2.decision_id,
              clearance_id=ok.clearance_id, redeemed_at=done.at)  # fmt: skip
    assert [dump(x) for x in later.executed] == [ex]
    r = refused_with(c.ask(dealdesk, later.decision_id, creq(later, P15)))
    assert codes(r) == ["spent"]  # nothing waits on anyone once it is spent
    assert r.reasons[0].detail == (f"apply_discount on DR-9001 was executed by {v2.decision_id} "
                                   f"under {ok.clearance_id} at {hhmm(done.at)}.")  # fmt: skip
    assert Decisions(org).get(v2.decision_id).executed == later.executed


# -- redemption ---------------------------------------------------------------------------------
def test_expired(org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    org.clock.set(datetime.fromisoformat(ok.expires_at) + timedelta(seconds=1), None)
    r = redeem(c, ok)
    assert codes(r) == ["expired"]
    assert isinstance(r, NotRedeemed)
    assert r.reasons[0].detail == f"{ok.clearance_id} expired at {hhmm(ok.expires_at)}."
    row = org.log.get_clearance(ok.clearance_id)
    assert row is not None and row.used_at is None  # a refusal rolls back
    assert org.log.executions() == []
    assert Decisions(org).get(v2.decision_id).state == "ready"
    refusals = org.log.read(org.org_id, kinds=("redeem.refused",))
    assert [e.payload["reasons"][0]["code"] for e in refusals] == ["expired"]
    # attempts and refused redemptions decide nothing: on the decision's stream, not the subject's
    assert kinds_on(org, v2.decision_id) == ["clearance.attempted", "redeem.refused"]
    assert not {"clearance.attempted", "redeem.refused"} & set(kinds_on(org, "DR-9001"))


def test_mismatch_on_other_params(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    for params in ({**P15, "account_id": "CRM-9999"}, P8, {**P15, "extra": 1},
                   {k: v for k, v in P15.items() if k != "product"}):  # fmt: skip
        assert codes(redeem(c, ok, params)) == ["mismatch"], params
    row = org.log.get_clearance(ok.clearance_id)
    assert row is not None and row.used_at is None
    assert isinstance(redeem(c, ok), Redeemed)  # still unused, so the bound params redeem it


def test_race_second_redemption_is_spent(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    a, b = clear15(c, dealdesk, v2), clear15(c, dealdesk, v2)
    results = run_in_threads(lambda x: redeem(c, x), [a, b])
    assert sorted(isinstance(r, Redeemed) for r in results) == [False, True]
    loser = next(r for r in results if isinstance(r, NotRedeemed))
    assert codes(loser) == ["spent"]
    assert len(org.log.executions()) == 1
    assert len(org.log.read(org.org_id, kinds=("clearance.redeemed",))) == 1


def test_the_unique_key_is_the_last_guard(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # fmt: skip
    """Step 5: even if the re-checks read a decision from before the first redemption, the second
    insert hits UNIQUE (org, subject, action) and is refused `spent`; nothing of it is kept."""
    v2 = ready_s22(org, dealdesk, sarah, michael)
    a, b = clear15(c, dealdesk, v2), clear15(c, dealdesk, v2)
    assert isinstance(redeem(c, a), Redeemed)
    stale_view = v2  # the decision as read before the first redemption: ready
    monkeypatch.setattr(c.decisions, "get", lambda *_a, **_k: stale_view)
    monkeypatch.setattr(Clearances, "_spent", lambda *_a, **_k: [])
    r = redeem(c, b)
    assert codes(r) == ["spent"]
    assert isinstance(r, NotRedeemed) and a.clearance_id in r.reasons[0].detail
    row = org.log.get_clearance(b.clearance_id)
    assert row is not None and row.used_at is None
    assert [x.clearance_id for x in org.log.executions()] == [a.clearance_id]


def run_in_threads(fn: Callable[[Cleared], Any], items: Sequence[Cleared]) -> list[Any]:
    barrier = threading.Barrier(len(items))
    out: list[Any] = [None] * len(items)

    def run(i: int, x: Cleared) -> None:
        barrier.wait(10)
        try:
            out[i] = fn(x)
        except Exception as e:  # noqa: BLE001 - the test inspects it
            out[i] = e

    threads = [threading.Thread(target=run, args=(i, x)) for i, x in enumerate(items)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    return out


def test_redeem_rechecks_a_withdrawn_decision(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances
) -> None:
    """A clearance issued on a ready version can't be redeemed once the requester withdraws it."""
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    Decisions(org).withdraw(sarah, v2.decision_id, step(2))
    assert codes(redeem(c, ok)) == ["stale"]
    assert codes(c.ask(dealdesk, v2.decision_id, creq(v2, P15))) == ["stale"]
    assert org.log.executions() == []


def test_a_rerun_racing_a_redemption_is_409(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # fmt: skip
    """R33: the redemption goes on the subject's stream, so a re-run whose kernel ran while the
    action was spent finds the subject moved at its write and is refused with 409."""
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    real = _lab.decide
    entered, redeemed = threading.Event(), threading.Event()

    def held(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        entered.set()
        assert redeemed.wait(10)
        return real(kind, **kw)

    monkeypatch.setattr(_lab, "decide", held)
    out: list[Any] = []

    def rerun() -> None:
        body = RerunRequest(decision_version=2)
        try:
            out.append(Decisions(org).rerun(sarah, v2.decision_id, body))
        except Exception as e:  # noqa: BLE001 - the test inspects it
            out.append(e)

    t = threading.Thread(target=rerun)
    t.start()
    assert entered.wait(10)
    assert isinstance(redeem(c, ok), Redeemed)
    redeemed.set()
    t.join(10)
    (loser,) = out
    assert isinstance(loser, Refused) and (loser.status, loser.refusals[0].rule) == (409, "DC-5")
    now = Decisions(org).get(v2.decision_id)
    assert (now.version, now.state) == (2, "spent")
    assert kinds_on(org, "DR-9001")[-1] == "clearance.redeemed"


# -- reports and incidents ----------------------------------------------------------------------
def test_failed_report_stays_spent_and_opens_incident(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    e = refused(lambda: report(c, ok.clearance_id, "applied"))
    assert e.status == 422 and "redeemed" in e.refusals[0].detail  # nothing to report yet
    assert isinstance(redeem(c, ok), Redeemed)
    assert report(c, ok.clearance_id, "failed") == "INC-0001"
    rec = Decisions(org).get(v2.decision_id)
    assert rec.state == "spent"
    assert [(x.report, x.incident_id) for x in rec.executed] == [("failed", "INC-0001")]
    (inc,) = org.log.read(org.org_id, kinds=("incident.opened",))
    assert (inc.stream, inc.payload["incident_id"], inc.payload["function"]) == (
        "DR-9001", "INC-0001", "Sales")  # fmt: skip
    assert inc.payload["clearance_id"] == ok.clearance_id
    again = refused(lambda: report(c, ok.clearance_id, "applied"))
    assert again.status == 422 and "already" in again.refusals[0].detail
    assert codes(c.ask(dealdesk, v2.decision_id, creq(v2, P15))) == ["spent"]
    with pytest.raises(NotFound):
        report(c, "CLR-99999", "applied")
    assert kinds_on(org, "DR-9001")[-3:] == [
        "clearance.redeemed", "execution.reported", "incident.opened"]  # fmt: skip


def test_redeem_and_report_record_who_called(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances
) -> None:
    """Ruling R35: the session behind a redemption or a report is recorded as `by` beside the
    executor, on every event it writes, refused redemptions included. Without one, nothing is."""
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    body = RedeemRequest(params=ok.bound.params, executor=EXEC)
    who = sarah.model_dump(mode="json")
    assert isinstance(c.redeem(ok.clearance_id, body, by=sarah), Redeemed)
    assert isinstance(c.redeem(ok.clearance_id, body, by=sarah), NotRedeemed)
    failed = ReportRequest(status="failed", external_ref=None, detail="CRM timeout")
    assert c.report(ok.clearance_id, failed, by=sarah).incident_id == "INC-0001"
    kinds = ("clearance.redeemed", "redeem.refused", "execution.reported", "incident.opened")
    evs = org.log.read(org.org_id, kinds=kinds)
    assert sorted(e.kind for e in evs) == sorted(kinds)
    assert all(e.payload["by"] == who for e in evs)
    assert all(e.actor == {"kind": "system", **EXEC.model_dump()} for e in evs)


def test_redeem_without_a_caller_records_no_by(
    org: Org, dealdesk: Actor, sarah: Actor, michael: Actor, c: Clearances
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    assert isinstance(redeem(c, ok), Redeemed)
    (e,) = org.log.read(org.org_id, kinds=("clearance.redeemed",))
    assert "by" not in e.payload


def test_s36_failed_credit_goes_to_customer_support(
    org: Org, marcus: Actor, paul: Actor, c: Clearances
) -> None:
    """S36's $4,200 credit is issued once: Paul clears and the adapter redeems it; a failed report
    raises an incident for Customer Support, and a second clearance is refused `spent`."""
    d = Decisions(org)
    v1 = ask(org, marcus, "SR-39385", None, "sla")
    ready = d.approve(marcus, v1.decision_id, step(1))
    assert ready.state == "ready"
    params = ready.actions[0].params
    assert params == {"ticket": "SR-39385", "account_id": "CRM-2048", "amount_usd": 4200.0}
    ok = cleared(c.ask(paul, v1.decision_id, creq(ready, params)))
    assert isinstance(redeem(c, ok), Redeemed)
    assert report(c, ok.clearance_id, "failed") == "INC-0001"
    (inc,) = org.log.read(org.org_id, kinds=("incident.opened",))
    assert inc.payload["function"] == "Customer Support"
    assert codes(c.ask(paul, v1.decision_id, creq(ready, params))) == ["spent"]
    later = ask(org, marcus, "SR-39385", None, "sla")
    assert later.state == "spent" and later.executed[0].incident_id == "INC-0001"


def test_failed_credit_limit_goes_to_finance(org: Org, michael: Actor, c: Clearances) -> None:
    sessions = Sessions(org)
    elena, david = sessions.open_person("EMP-402")[1], sessions.open_person("EMP-300")[1]
    row = org.sor.row("credit_requests", "CR-9201")
    assert row is not None
    with org.log.transaction() as tx:
        org.sor.insert(tx, "credit_requests", {**row, "request_id": "CR-9208",
                       "requested_limit_usd": "650000",
                       "requested_by": "michael.torres@northstar.example"},
                       actor=dump(michael), at=org.clock.now())  # fmt: skip
    d = Decisions(org)
    v1 = ask(org, michael, "CR-9208", None, "credit")
    d.approve(elena, v1.decision_id, step(1))
    done = d.approve(david, v1.decision_id, step(1, "concur"))
    assert done.state == "ready"
    ok = cleared(c.ask(elena, v1.decision_id, creq(done, done.actions[0].params)))
    assert isinstance(redeem(c, ok), Redeemed)
    assert report(c, ok.clearance_id, "failed") == "INC-0001"
    (inc,) = org.log.read(org.org_id, kinds=("incident.opened",))
    assert inc.payload["function"] == "Finance"


# -- mandates (agents only; may_ask is never checked) ---------------------------------------------
def test_outside_mandate_for_external_agent(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor, c: Clearances
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    external = Sessions(org).open_agent("AGT-EXTERNAL", "EMP-101")[1]
    r = refused_with(c.ask(external, v2.decision_id, creq(v2, P15)))
    assert codes(r) == ["outside_mandate"]
    assert "AGT-EXTERNAL" in r.reasons[0].detail and "no mandate" in r.reasons[0].detail
    # a person isn't mandate-checked
    assert cleared(c.ask(sarah, v2.decision_id, creq(v2, P15))).bound.actor == sarah


def test_may_ask_unenforced(org: Org, sarah: Actor, dealdesk: Actor) -> None:
    """Asking grants nothing, so a mandate-less agent may ask, and the Deal Desk Agent may ask for
    a decision its mandate's `may_ask` doesn't list: version 1 is written either way."""
    external = Sessions(org).open_agent("AGT-EXTERNAL", "EMP-101")[1]
    v1 = ask_s22(org, external)
    assert (v1.version, v1.actor) == (1, external)
    credit = ask(org, dealdesk, "CR-9201", None, "credit")
    assert credit.version == 1 and credit.actor == dealdesk


def test_mandate_terms(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor, marcus: Actor
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    d = Decisions(org)
    rogue = Sessions(org).open_agent("AGT-DEALDESK", "EMP-101", version="sha256:rogue")[1]
    r = refused_with(Clearances(org, d).ask(rogue, v2.decision_id, creq(v2, P15)))
    assert codes(r) == ["outside_mandate"] and "sha256:rogue" in r.reasons[0].detail
    only_credit = Clearances(org, d, dealdesk_terms(org, decision_types=["credit"]))
    r = refused_with(only_credit.ask(dealdesk, v2.decision_id, creq(v2, P15)))
    assert codes(r) == ["outside_mandate"] and "discount" in r.reasons[0].detail
    unknown_limit = Clearances(org, d, dealdesk_terms(org, limits={"per_week": 5}))
    r = refused_with(unknown_limit.ask(dealdesk, v2.decision_id, creq(v2, P15)))
    assert codes(r) == ["outside_mandate"] and "per_week" in r.reasons[0].detail
    # an action its mandate doesn't list: S36's service credit
    sla = ask(org, dealdesk, "SR-39385", None, "sla")
    ready = d.approve(marcus, sla.decision_id, step(1))
    r = refused_with(Clearances(org, d).ask(dealdesk, sla.decision_id,
                                            creq(ready, ready.actions[0].params)))  # fmt: skip
    assert codes(r) == ["outside_mandate"] and "issue_service_credit" in r.reasons[0].detail


def test_at_most_binds_the_lower_value(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    c = Clearances(org, Decisions(org), dealdesk_terms(org, match={"discount": "at_most"}))
    for bad in (0.16, -0.01, "0.12", None):
        assert codes(c.ask(dealdesk, v2.decision_id, creq(v2, {**P15, "discount": bad}))) == [
            "differs"], bad  # fmt: skip
    assert codes(c.ask(dealdesk, v2.decision_id, creq(v2, {**P15, "account_id": "X"}))) == [
        "differs"]  # fmt: skip
    # people aren't mandate-checked, so the mandate's at_most isn't theirs: exact
    assert codes(c.ask(sarah, v2.decision_id, creq(v2, {**P15, "discount": 0.12}))) == ["differs"]
    ok = cleared(c.ask(dealdesk, v2.decision_id, creq(v2, {**P15, "discount": 0.12})))
    assert ok.bound.params == {**P15, "discount": 0.12}
    assert codes(redeem(c, ok, P15)) == ["mismatch"]  # the bound value, not the decided one
    assert isinstance(redeem(c, ok), Redeemed)


def test_per_day_limit(org: Org, sarah: Actor, michael: Actor, dealdesk: Actor,
                       c: Clearances) -> None:  # fmt: skip
    """The mandate allows 200 clearances a day: the 201st is outside it. Dry runs and other
    actors' clearances don't count; the next day starts afresh."""
    v2 = ready_s22(org, dealdesk, sarah, michael)
    cleared(c.ask(sarah, v2.decision_id, creq(v2, P15)))
    refused_with(c.ask(dealdesk, v2.decision_id, creq(v2, P15, dry_run=True)))
    for _ in range(200):
        cleared(c.ask(dealdesk, v2.decision_id, creq(v2, P15)))
    r = refused_with(c.ask(dealdesk, v2.decision_id, creq(v2, P15)))
    assert codes(r) == ["outside_mandate"]
    assert "per_day" in r.reasons[0].detail and "200" in r.reasons[0].detail
    tomorrow = org.clock.now().replace(hour=9, minute=0) + timedelta(days=1)
    org.clock.set(tomorrow, None)
    cleared(c.ask(dealdesk, v2.decision_id, creq(v2, P15)))


# -- the other checks ---------------------------------------------------------------------------
def test_dry_run_issues_nothing_and_is_logged(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor, c: Clearances
) -> None:
    v1 = ask_s22(org, dealdesk)
    assert codes(c.ask(dealdesk, v1.decision_id, creq(v1, P8, dry_run=True))) == [
        "differs", "condition_open", "awaiting_approval"]  # fmt: skip
    v2 = ready_s22_from(org, v1, sarah, michael)
    r = refused_with(c.ask(dealdesk, v2.decision_id, creq(v2, P15, dry_run=True)))
    assert r.reasons == []  # nothing stops it, and nothing was issued
    assert org.log.clearances() == []
    ok = clear15(c, dealdesk, v2)
    attempts = c.attempts(v2.decision_id)
    assert [(a.request.dry_run, a.response.root.cleared) for a in attempts] == [
        (True, False), (True, False), (None, True)]  # fmt: skip
    assert all(a.actor == dealdesk for a in attempts)
    assert dump(attempts[-1].response) == dump(ok)
    assert attempts[0].request == creq(v1, P8, dry_run=True)
    with pytest.raises(NotFound):
        c.attempts("DEC-9999")


def ready_s22_from(org: Org, v1: DecisionRecord, sarah: Actor, michael: Actor) -> DecisionRecord:
    d = Decisions(org)
    d.resolve(sarah, v1.decision_id, "c1", CONFIRM)
    return d.approve(michael, v1.decision_id, step(2))


def test_stale_after_basis_edit(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor, c: Clearances
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    with org.log.transaction() as tx:
        org.sor.edit(tx, "discount_requests", "DR-9001", {"request_date": "2026-09-24"},
                     actor=dump(sarah), at=org.clock.now())  # fmt: skip
    r = refused_with(c.ask(dealdesk, v2.decision_id, creq(v2, P15)))
    assert codes(r) == ["stale"] and "request_date" in r.reasons[0].detail
    assert codes(redeem(c, ok)) == ["stale"]
    row = org.log.get_clearance(ok.clearance_id)
    assert row is not None and row.used_at is None


def test_stale_when_the_version_moved(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor, c: Clearances
) -> None:
    v1 = ask_s22(org, dealdesk)
    v2 = ready_s22_from(org, v1, sarah, michael)
    r = refused_with(c.ask(dealdesk, v1.decision_id, creq(v2, P15, version=1)))
    assert codes(r) == ["stale"] and "version 2" in r.reasons[0].detail
    ok = clear15(c, dealdesk, v2)
    Decisions(org).rerun(sarah, v2.decision_id, RerunRequest(decision_version=2))
    assert "stale" in codes(redeem(c, ok))


def test_stale_when_a_register_document_is_revoked(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor, c: Clearances,
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # fmt: skip
    """A document in `register_used` revoked on or before the action date (the C01x probe) makes
    the decision stale; a revocation that takes effect later doesn't, until that day."""
    v2 = ready_s22(org, dealdesk, sarah, michael)
    assert "EXC-ACME-NS500-15" in {u.doc_id for u in v2.register_used}
    state = org.register_state()

    class Revoked:
        version = state.version
        entries = [dict(e, revoked_on="2026-09-30") if e["doc_id"] == "EXC-ACME-NS500-15" else e
                   for e in state.entries]  # fmt: skip

    monkeypatch.setattr(org, "register_state", lambda: Revoked)
    ok = clear15(c, dealdesk, v2)  # revoked from the 30th: not yet
    org.clock.set(datetime(2026, 9, 30, 9, 0, tzinfo=DEMO_TZ), None)
    r = refused_with(c.ask(dealdesk, v2.decision_id, creq(v2, P15)))
    assert codes(r) == ["stale"] and "EXC-ACME-NS500-15" in r.reasons[0].detail
    assert codes(redeem(c, ok)) == ["expired", "stale"]  # from expired to the re-checks, together


def test_stale_when_a_ticket_event_is_added(
    org: Org, marcus: Actor, paul: Actor, c: Clearances
) -> None:
    """For SLA the basis `events` field is a digest of the ticket's events (ruling R17)."""
    d = Decisions(org)
    v1 = ask(org, marcus, "SR-39385", None, "sla")
    ready = d.approve(marcus, v1.decision_id, step(1))
    ok = cleared(c.ask(paul, v1.decision_id, creq(ready, ready.actions[0].params)))
    with org.log.transaction() as tx:
        org.sor.insert(tx, "ticket_events", {"ticket_id": "SR-39385",
                       "at": org.clock.now().isoformat(), "event": "customer_reply"},
                       actor=dump(paul), at=org.clock.now())  # fmt: skip
    assert codes(redeem(c, ok)) == ["stale"]


def test_suspended(org: Org, tmp_path: Path, sarah: Actor, michael: Actor,
                   dealdesk: Actor, c: Clearances) -> None:  # fmt: skip
    v2 = ready_s22(org, dealdesk, sarah, michael)
    ok = clear15(c, dealdesk, v2)
    env = {"OWM_STATE_DIR": str(tmp_path / "state"),
           "OWM_SUSPENDED": "AGT-DEALDESK@sha256:demo-dealdesk-v1"}  # fmt: skip
    held = Org(load_settings(env))
    c2 = Clearances(held, Decisions(held))
    r = refused_with(c2.ask(dealdesk, v2.decision_id, creq(v2, P15)))
    assert codes(r) == ["suspended"]
    assert codes(c2.redeem(ok.clearance_id, RedeemRequest(params=P15, executor=EXEC))) == [
        "suspended"]  # fmt: skip
    assert cleared(c2.ask(sarah, v2.decision_id, creq(v2, P15)))  # people are never suspended


def test_declined_closes_the_gate(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor, c: Clearances
) -> None:
    v1 = ask_s22(org, dealdesk)
    d = Decisions(org)
    d.resolve(sarah, v1.decision_id, "c1", CONFIRM)
    gone = d.decline(michael, v1.decision_id, step(2, "Not this quarter."))
    r = refused_with(c.ask(dealdesk, gone.decision_id, creq(gone, P15)))
    assert [dump(x) for x in r.reasons] == [
        {"code": "declined", "detail": "Michael Torres declined version 2: Not this quarter."}
    ]


def test_an_action_the_decision_did_not_decide(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor, c: Clearances
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    body = creq(v2, {"request_id": "DR-9001", "customer_id": "C-1001", "limit_usd": 1.0},
                action="set_credit_limit")  # fmt: skip
    r = refused_with(c.ask(sarah, v2.decision_id, body))
    assert codes(r) == ["differs"] and "apply_discount" in r.reasons[0].detail


def test_request_checks(org: Org, dealdesk: Actor, sarah: Actor, c: Clearances) -> None:
    v1 = ask_s22(org, dealdesk)
    e = refused(lambda: c.ask(dealdesk, "DEC-0002", creq(v1, P8)))
    assert (e.status, e.refusals[0].rule) == (422, "DC-2")
    e = refused(lambda: c.ask(dealdesk, v1.decision_id, creq(v1, P8, actor=dump(sarah))))
    assert (e.status, e.refusals[0].rule) == (403, "RR-1")
    same = c.ask(dealdesk, v1.decision_id, creq(v1, P8, actor=dump(dealdesk)))
    assert codes(same)[0] == "differs"
    with pytest.raises(NotFound):
        c.ask(dealdesk, "DEC-9999", creq(v1, P8).model_copy(update={"decision_id": "DEC-9999"}))
    with pytest.raises(NotFound):
        c.redeem("CLR-99999", RedeemRequest(params=P15, executor=EXEC))
    assert [a.response.root.cleared for a in c.attempts(v1.decision_id)] == [False]


# -- the log is the record ----------------------------------------------------------------------
def test_rebuilt_projections_equal_the_live_state(
    org: Org, tmp_path: Path, sarah: Actor, michael: Actor, dealdesk: Actor, c: Clearances
) -> None:
    v2 = ready_s22(org, dealdesk, sarah, michael)
    refused_with(c.ask(dealdesk, v2.decision_id, creq(v2, P8)))
    ok, spare = clear15(c, dealdesk, v2), clear15(c, dealdesk, v2)
    assert isinstance(redeem(c, ok), Redeemed)
    assert codes(redeem(c, spare)) == ["spent"]
    report(c, ok.clearance_id, "failed")
    later = ask(org, sarah, "DR-9001")
    d = Decisions(org)
    live = ([dump(r) for r in d.list()], org.log.clearances(), org.log.executions())
    again = Org(load_settings({"OWM_STATE_DIR": str(tmp_path / "state")}))
    again.log.rebuild_projections()
    rebuilt = ([dump(r) for r in Decisions(again).list()], again.log.clearances(),
               again.log.executions())  # fmt: skip
    assert rebuilt == live
    assert Decisions(again).get(later.decision_id).executed[0].incident_id == "INC-0001"
    redeemed = again.log.read(again.org_id, kinds=("clearance.redeemed",))
    assert redeemed[0].payload["executor"] == dump(EXEC)
