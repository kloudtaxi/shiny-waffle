"""§12.2 item 2 (spec §10): what the service adds to the kernel's record, against the truth.
Replay only, $0.

- **Input conflicts** equal the oracle's on the 14 scenarios whose `expected:` lists them (S22
  `requested_discount`, S23 `request_date`, S24 `status`, S35 `requested_limit_usd`, and ten with
  none). `northstar build` refuses to write unless the oracle's result equals each scenario's
  `expected:` (`oracle.check`), so comparing with `expected:` is comparing with the oracle.
- **Approvals** by person id (and kind, for credit), compared where version 1's gated outcome is
  the expected outcome: the discount approver; the credit approvers as `[(id, kind)]`; for an SLA
  credit owed, the claim decision by the `decide_claim` holder and the credit's expected actor the
  `issue_memo` holder (S36: Marcus Adeyemi, EMP-602, and Paul Brennan, EMP-604).
- **Actions** are decided exactly when the outcome clears: APPROVE or APPROVE_WITH_AUTHORIZATION
  (discount, credit), BREACH_CREDIT_OWED (SLA).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from owm_service.models import CreditFindings, DecisionRecord, DiscountFindings

from .. import harness

CLEARS = {
    "discount": {"APPROVE", "APPROVE_WITH_AUTHORIZATION"},
    "credit": {"APPROVE", "APPROVE_WITH_AUTHORIZATION"},
    "sla": {"BREACH_CREDIT_OWED"},
}
WITH_CONFLICTS = [s for s in harness.ALL if s in ("S22", "S23", "S24", "S25") or s in
                  harness.CREDIT]  # fmt: skip


def v1_of(sid: str, tmp: Path) -> DecisionRecord:
    return harness.ask(harness.scenario_org(sid, tmp), sid)


def holder(sid: str, duty: str) -> str:
    """Who the truth says holds an SLA duty on the scenario's ticket."""
    (who,) = [row[2] for row in harness.expected(sid)["northstar"] if row[0] == duty]
    return str(who)


def test_fourteen_scenarios_list_input_conflicts() -> None:
    listed = [s for s in harness.ALL if "input_conflicts" in harness.expected(s)]
    assert listed == WITH_CONFLICTS and len(listed) == 14
    named = {s: harness.expected(s)["input_conflicts"] for s in listed if
             harness.expected(s)["input_conflicts"]}  # fmt: skip
    assert named == {"S22": ["requested_discount"], "S23": ["request_date"], "S24": ["status"],
                     "S35": ["requested_limit_usd"]}  # fmt: skip


@pytest.mark.parametrize("sid", WITH_CONFLICTS)
def test_input_conflicts_match_the_oracle(sid: str, tmp_path: Path) -> None:
    org = harness.scenario_org(sid, tmp_path)
    v1 = harness.ask(org, sid)
    conflicts = [c for c in v1.conditions if c.source == "input_conflict"]
    assert {c.field for c in conflicts} == set(harness.expected(sid)["input_conflicts"])
    assert len(conflicts) == len(harness.expected(sid)["input_conflicts"])
    requester = org.people.by_email(harness.record_of(sid)["requested_by"])
    assert requester is not None and v1.requested_by == requester
    for c in conflicts:  # the requester confirms or corrects her own figure; until then it blocks
        assert c.blocking and c.opened_in_version == 1 and c.resolved is None
        assert c.who == [requester]
    assert [c for c in v1.conditions if c.source != "input_conflict"] == []


@pytest.mark.parametrize("sid", harness.ALL)
def test_approvals_and_actions_match_truth(sid: str, tmp_path: Path) -> None:
    kind, exp = harness.KIND_OF[sid], harness.expected(sid)
    v1 = v1_of(sid, tmp_path)
    clears = v1.gated_outcome in CLEARS[kind]
    assert bool(v1.actions) == clears, (v1.gated_outcome, v1.actions)
    if v1.gated_outcome != exp["outcome"]:
        # approvals are compared only where the outcome is the truth's; item 1 holds the outcome
        # to the committed record. (On 2026-10-11 all 42 version 1 outcomes were the truth's.)
        return
    given = [(a.kind, a.person.id if a.person else None) for a in v1.approvals]
    if kind == "discount":
        assert isinstance(v1.findings, DiscountFindings) and v1.findings.authority is not None
        approver = v1.findings.authority.approver
        assert approver is not None and approver.id == exp["approver"]
        want = [("approval", exp["approver"])] if v1.gated_outcome == "APPROVE_WITH_AUTHORIZATION" \
            else []  # fmt: skip
        assert given == want
    elif kind == "credit":
        assert isinstance(v1.findings, CreditFindings)
        assert [(who, k) for k, who in given] == [tuple(a) for a in exp["approvers"]]
    elif v1.gated_outcome == "BREACH_CREDIT_OWED":
        assert given == [("claim_decision", holder(sid, "decide_claim"))]
        (act,) = v1.actions
        assert act.action == "issue_service_credit"
        assert act.expected_actor is not None and act.expected_actor.id == holder(sid, "issue_memo")
        assert act.params == {"ticket": harness.subject_of(sid),
                              "account_id": v1.subject.account_id,
                              "amount_usd": exp["credit_usd"]}  # fmt: skip
    else:
        assert given == []
    if clears and kind != "sla":
        (act,) = v1.actions
        row = harness.record_of(sid)
        if kind == "discount":
            assert (act.action, act.params) == ("apply_discount", {
                "request_id": row["request_id"], "account_id": row["account_id"],
                "product": row["product_sku"],
                "discount": float(row["requested_discount_pct"]) / 100})  # fmt: skip
        else:
            assert (act.action, act.params) == ("set_credit_limit", {
                "request_id": row["request_id"], "customer_id": row["erp_customer_id"],
                "limit_usd": float(row["requested_limit_usd"])})  # fmt: skip
        assert act.expected_actor is None
