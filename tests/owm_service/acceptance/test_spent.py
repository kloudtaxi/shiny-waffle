"""§12.2 item 4 (spec §10, contract §5.9 and §7.2): an action is spent for its subject, whichever
decision asks. Replay only, $0.

- (a) S36 end to end: Marcus Adeyemi asks about SR-39385 (BREACH_CREDIT_OWED, $4,200) and gives
  the claim decision; Paul Brennan, the credit's expected actor, asks for clearance with the
  decided params (people aren't mandate-checked); the lab adapter redeems it and issues the
  credit, and the decision is spent. A new decision on SR-39385 may be asked, and it is `spent` at
  version 1, its `executed` naming the first decision and the clearance; its own clearance (for
  the $2,100 the kernel now finds under the cap) is refused `spent`.
- (b) Two clearances on one decision, redeemed at once in two threads: exactly one is redeemed,
  the other refused `spent`.
- (c) A `failed` report leaves the decision spent and opens an incident for Customer Support, and
  a new clearance is refused `spent`.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from owm_service import lab_adapter
from owm_service.clearance import Clearances
from owm_service.decisions import Decisions
from owm_service.models import (
    Actor,
    ClearanceRequest,
    Cleared,
    DecisionRecord,
    DryRun,
    Executor,
    NotCleared,
    NotRedeemed,
    Redeemed,
    RedeemRequest,
    StepRequest,
)
from owm_service.org import Org
from owm_service.sessions import Sessions

from .. import harness

CREDIT = {"ticket": "SR-39385", "account_id": "CRM-2048", "amount_usd": 4200.0}
EXECUTOR = Executor(system="service", adapter="lab-adapter")


def person(org: Org, emp: str) -> Actor:
    return Sessions(org).open_person(emp)[1]


def clear(org: Org, actor: Actor, rec: DecisionRecord) -> Cleared | NotCleared:
    """Ask to clear the version's decided credit, with exactly its decided params."""
    (act,) = rec.actions
    req = ClearanceRequest(decision_id=rec.decision_id, decision_version=rec.version,
                           action=act.action, params=act.params)  # fmt: skip
    out = Clearances(org, Decisions(org)).ask(actor, rec.decision_id, req)
    assert not isinstance(out, DryRun), out  # a real attempt
    return out


def cleared(r: Cleared | NotCleared) -> Cleared:
    assert isinstance(r, Cleared), r
    return r


def codes(r: Cleared | NotCleared | Redeemed | NotRedeemed) -> list[str]:
    assert isinstance(r, NotCleared | NotRedeemed), r
    return [x.code for x in r.reasons]


def s36_ready(tmp: Path) -> tuple[Org, DecisionRecord, Actor]:
    """S36 asked by Marcus and its claim decided by him: ready. The org, the version, Paul."""
    org = harness.scenario_org("S36", tmp)
    marcus, paul = person(org, "EMP-602"), person(org, "EMP-604")
    v1 = harness.ask(org, "S36")
    assert (v1.gated_outcome, v1.state) == ("BREACH_CREDIT_OWED", "awaiting_approval")
    assert [(a.kind, a.person and a.person.id) for a in v1.approvals] == [
        ("claim_decision", "EMP-602")]  # fmt: skip
    (act,) = v1.actions
    assert (act.action, act.params) == ("issue_service_credit", CREDIT)
    assert act.expected_actor is not None and act.expected_actor.id == "EMP-604"
    ready = Decisions(org).approve(marcus, v1.decision_id, StepRequest(decision_version=1))
    assert ready.state == "ready"
    return org, ready, paul


def test_s36_spent_across_decisions(tmp_path: Path) -> None:
    org, ready, paul = s36_ready(tmp_path)
    d, c = Decisions(org), Clearances(org, Decisions(org))
    ok = cleared(clear(org, paul, ready))
    assert ok.bound.params == CREDIT and ok.bound.actor == paul
    out = lab_adapter.execute(org, c, ok.clearance_id, fail=False)
    assert (out["redeemed"], out["report"], out["incident_id"]) == (True, "applied", None)
    (credit,) = [r for r in org.sor.table("service_credits") if r["credit_id"] == ok.clearance_id]
    assert (credit["ticket_id"], credit["amount_usd"]) == ("SR-39385", "4200.00")
    first = d.get(ready.decision_id)
    assert first.state == "spent"
    later = harness.ask(org, "S36")  # allowed: the first decision is no longer live
    assert later.decision_id != first.decision_id
    assert (later.version, later.state) == (1, "spent")
    # The kernel counts the $4,200 already issued against the account's cap for June (`sla.yaml`
    # `cap_used`) and finds $2,100 of room left, without seeing that it was this ticket's own
    # credit: only `spent` stops a second payment on SR-39385 (Task 15 report)
    assert later.gated_outcome == "BREACH_CREDIT_OWED"
    assert [a.params["amount_usd"] for a in later.actions] == [2100.0]
    assert [(x.action, x.decision_id, x.version, x.clearance_id, x.report)
            for x in later.executed] == [("issue_service_credit", first.decision_id, 1,
                                          ok.clearance_id, "applied")]  # fmt: skip
    assert codes(clear(org, paul, later)) == ["spent"]
    assert codes(clear(org, paul, first)) == ["spent"]
    assert not org.engine.calls.exists()


def test_two_clearances_race_and_one_is_spent(tmp_path: Path) -> None:
    org, ready, paul = s36_ready(tmp_path)
    c = Clearances(org, Decisions(org))
    one, two = cleared(clear(org, paul, ready)), cleared(clear(org, paul, ready))
    start = threading.Barrier(2)
    results: dict[str, Any] = {}

    def redeem(cid: str) -> None:
        start.wait()
        try:
            results[cid] = c.redeem(cid, RedeemRequest(params=CREDIT, executor=EXECUTOR))
        except BaseException as e:  # noqa: BLE001 - surfaced by the assertions below
            results[cid] = e

    threads = [threading.Thread(target=redeem, args=(x.clearance_id,)) for x in (one, two)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert not any(t.is_alive() for t in threads)
    got = [results[one.clearance_id], results[two.clearance_id]]
    won = [r for r in got if isinstance(r, Redeemed)]
    lost = [r for r in got if isinstance(r, NotRedeemed)]
    assert (len(won), len(lost)) == (1, 1), got
    assert codes(lost[0]) == ["spent"]
    (row,) = org.log.executions()
    assert (row.subject, row.action, row.decision_id) == ("SR-39385", "issue_service_credit",
                                                          ready.decision_id)  # fmt: skip
    assert Decisions(org).get(ready.decision_id).state == "spent"


def test_failed_report_stays_spent_and_opens_an_incident(tmp_path: Path) -> None:
    org, ready, paul = s36_ready(tmp_path)
    c = Clearances(org, Decisions(org))
    ok = cleared(clear(org, paul, ready))
    out = lab_adapter.execute(org, c, ok.clearance_id, fail=True)
    assert (out["redeemed"], out["report"], out["incident_id"]) == (True, "failed", "INC-0001")
    assert [r for r in org.sor.table("service_credits") if r["credit_id"] == ok.clearance_id] == []
    (incident,) = org.log.read(org.org_id, kinds=("incident.opened",))
    assert incident.payload["function"] == "Customer Support"
    now = Decisions(org).get(ready.decision_id)
    assert now.state == "spent"
    assert [(x.clearance_id, x.report, x.incident_id) for x in now.executed] == [
        (ok.clearance_id, "failed", "INC-0001")]  # fmt: skip
    assert codes(clear(org, paul, now)) == ["spent"]
