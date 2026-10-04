"""Reference decision procedure — the canonical sales discount process (doc 03 §11).

This is the *laboratory's* oracle, not the OWM. It exists to prove the dataset is
coherent: each scenario's hand-authored expectation must follow from (a) the truth
and (b) only the evidence keys the generated corpus authoritatively supports. If
the two disagree, the build refuses to write the dataset.

Its output is a candidate answer key; it is not evidence that any OWM behaves so.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any

from northstar.artifacts import Artifact
from northstar.model import (
    CreditPolicy,
    CreditRequest,
    DiscountRequest,
    Employee,
    PricingException,
    Scenario,
    Truth,
)


def available_keys(artifacts: Iterable[Artifact]) -> frozenset[str]:
    return frozenset(k for a in artifacts for k in a.supports)


def resolve_request(truth: Truth, scenario: Scenario) -> DiscountRequest:
    spec = dict(scenario.request or {})
    base = truth.discount_request(spec.pop("base"))
    return base.model_copy(update=spec)


def applicable_exception(
    truth: Truth, customer: str, product: str, as_of: date, available: frozenset[str]
) -> PricingException | None:
    """The exception in force on ``as_of``. Superseded facts are kept, never overwritten —
    selection is by validity, and supersession only breaks ties between overlapping facts."""
    live = [
        x
        for x in truth.exceptions
        if x.customer == customer
        and x.product == product
        and x.active_on(as_of)
        and x.id in available
    ]
    superseded = {x.supersedes for x in live}
    current = [x for x in live if x.id not in superseded]
    return max(current, key=lambda x: x.valid_from) if current else None


def _approver(truth: Truth, requestor: Employee, role: str) -> Employee:
    if requestor.role == role:
        return requestor
    node: Employee | None = requestor
    while node is not None and node.manager is not None:
        node = truth.employee(node.manager)
        if node.role == role:
            return node
    return truth.holders_of(role)[0]


def decide(truth: Truth, scenario: Scenario, available: frozenset[str]) -> dict[str, Any]:
    assert scenario.as_of is not None
    as_of = scenario.as_of
    req = resolve_request(truth, scenario)
    cust = truth.customer(req.customer)
    requestor = truth.employee(req.requestor)
    reasons: list[str] = []
    evidence: list[str] = []

    # -- the submitted record against the system of record ------------------------
    submitted = dict(scenario.submitted or {})
    unknown = set(submitted) - set(type(req).model_fields)
    if unknown:
        raise ValueError(f"{scenario.id}: submitted fields not on a request: {sorted(unknown)}")
    conflicts = sorted(k for k, v in submitted.items() if getattr(req, k) != v)
    if conflicts:
        reasons.append(
            "the submitted record conflicts with the system of record on " + ", ".join(conflicts)
        )

    account = truth.account_for(cust.id)
    if account and account.id in available:
        evidence.append(account.id)
    if cust.source_ids["erp"] in available:
        evidence.append(cust.source_ids["erp"])

    # -- commercial eligibility -------------------------------------------------
    eligibility: dict[str, Any] = {"status": "standard", "maximum_discount": None, "basis": None}
    if req.basis == "contract_exception":
        contract = next(
            (
                c
                for c in truth.contracts
                if c.customer == cust.id and c.active_on(as_of) and c.id in available
            ),
            None,
        )
        exc = applicable_exception(truth, cust.id, req.product, as_of, available)
        if contract is None:
            eligibility = {
                "status": "unknown",
                "maximum_discount": None,
                "basis": None,
                "missing_evidence": ["active customer contract", "pricing exception"],
            }
            reasons.append(
                "request relies on a contract term that no available evidence establishes"
            )
        else:
            evidence.append(contract.id)
            if exc is None or req.product not in contract.covers:
                eligibility = {"status": "not_covered", "maximum_discount": None, "basis": None}
                reasons.append("no pricing exception covers this product on this date")
            else:
                evidence.append(exc.id)
                status = (
                    "eligible" if req.requested_discount <= exc.maximum_discount else "exceeded"
                )
                eligibility = {
                    "status": status,
                    "maximum_discount": exc.maximum_discount,
                    "basis": exc.id,
                }
                reasons.append(
                    "customer exception permits requested discount"
                    if status == "eligible"
                    else "requested discount exceeds the customer's contractual exception"
                )

    # -- authority --------------------------------------------------------------
    policy = truth.policy_on(as_of)
    if policy is None or policy.id not in available:
        raise ValueError(f"{scenario.id}: no pricing policy evidenced on {as_of}")
    evidence.append(policy.id)
    if policy.authority_matrix_document and policy.authority_matrix_document in available:
        evidence.append(policy.authority_matrix_document)
    if "organization_chart" in available:
        evidence.append("organization_chart")
    evidence.append(req.id)

    limit = policy.limit_for(requestor.role) or 0.0
    authorized = req.requested_discount <= limit
    band = policy.band_for(req.requested_discount)
    approver = _approver(truth, requestor, band.role)
    reasons.append("requestor holds authority" if authorized else "requestor lacks authority")
    if not authorized:
        reasons.append(f"{truth.role_title(band.role)} approval is required")
        reasons.append(f"{approver.name} holds {truth.role_title(band.role)} authority")

    # -- outcome ----------------------------------------------------------------
    outcome = {
        "unknown": "REQUEST_EVIDENCE",
        "not_covered": "REVIEW_REQUIRED",
        "exceeded": "REJECT_OR_ESCALATE",
    }.get(eligibility["status"], "APPROVE" if authorized else "APPROVE_WITH_AUTHORIZATION")

    return {
        "decision_id": f"DEC-{scenario.id}",
        "scenario": scenario.id,
        "type": "discount_approval",
        "as_of": as_of,
        "corpus": scenario.corpus,
        "subject": {"customer": cust.id, "product": req.product},
        "request": {
            "id": req.id,
            "requested_discount": req.requested_discount,
            "requestor": requestor.id,
        },
        "commercial_eligibility": eligibility,
        "authority": {
            "policy": policy.id,
            "requestor": {
                "employee": requestor.id,
                "maximum_discount": limit,
                "authorized": authorized,
            },
            "required": {"role": band.role, "maximum_discount": band.max_inclusive},
            "approver": {"employee": approver.id, "name": approver.name, "authorized": True},
        },
        "decision": {"outcome": outcome},
        "input": {"conflicts": conflicts},
        "reason": reasons,
        "evidence": evidence,
    }


# -- credit-limit increase (experiment 5, lab extension) -----------------------------------
APPROVALS = ("APPROVE", "APPROVE_WITH_AUTHORIZATION")


def resolve_credit_request(truth: Truth, scenario: Scenario) -> CreditRequest:
    spec = dict(scenario.request or {})
    base = truth.credit_request(spec.pop("base"))
    return base.model_copy(update=spec)


def late_invoices(truth: Truth, customer: str, as_of: date, policy: CreditPolicy) -> list[str]:
    """Invoices due in the lookback window that were paid, or are still unpaid, more than the
    policy allows past their due date, as known on ``as_of``. Background invoices of truth
    customers are never late (tested), so the truth's invoices decide."""
    start = as_of - timedelta(days=policy.lookback_days)
    return [
        i.id
        for i in truth.invoices
        if i.customer == customer
        and start <= i.due_date <= as_of
        and i.days_late(as_of) > policy.max_days_late
    ]


def credit_approver(truth: Truth, requestor: Employee, role: str, sod: bool) -> Employee:
    """As for discounts (up the requestor's chain, else any holder), except that under separation
    of duties a requestor who holds the role passes it to their manager."""
    holder = _approver(truth, requestor, role)
    if sod and holder.id == requestor.id:
        assert requestor.manager is not None, requestor.id
        return truth.employee(requestor.manager)
    return holder


def decide_credit(truth: Truth, scenario: Scenario, available: frozenset[str]) -> dict[str, Any]:
    assert scenario.as_of is not None
    as_of = scenario.as_of
    req = resolve_credit_request(truth, scenario)
    cust = truth.customer(req.customer)
    requestor = truth.employee(req.requestor)
    reasons: list[str] = []
    evidence: list[str] = []

    submitted = dict(scenario.submitted or {})
    unknown = set(submitted) - set(type(req).model_fields)
    if unknown:
        raise ValueError(f"{scenario.id}: submitted fields not on a request: {sorted(unknown)}")
    conflicts = sorted(k for k, v in submitted.items() if getattr(req, k) != v)
    if conflicts:
        reasons.append(
            "the submitted record conflicts with the system of record on " + ", ".join(conflicts)
        )

    account = truth.account_for(cust.id)
    tier = account.tier if account else "Standard"
    if cust.source_ids["crm"] in available:
        evidence.append(cust.source_ids["crm"])
    if cust.source_ids["erp"] in available:
        evidence.append(cust.source_ids["erp"])
    evidence += [k for k in ("erp_credit", "erp_invoices") if k in available]

    policy = truth.credit_policy_on(as_of)
    if policy is None or policy.id not in available:
        raise ValueError(f"{scenario.id}: no credit policy evidenced on {as_of}")

    # -- eligibility: payment history, then the tier cap raised by a guarantee in force ----------
    late = late_invoices(truth, cust.id, as_of, policy)
    guarantee = next(
        (g for g in truth.guarantees
         if g.customer == cust.id and g.active_on(as_of) and g.id in available),
        None,
    )  # fmt: skip
    cap = policy.caps[tier]
    eligibility: dict[str, Any]
    if late:
        eligibility = {"status": "ineligible", "maximum_limit": None, "basis": None,
                       "payment_history": {"ok": False, "late_invoices": late}}  # fmt: skip
        reasons.append("an invoice was paid more than the policy allows past its due date")
    elif req.basis == "guarantee" and guarantee is None:
        eligibility = {"status": "unknown", "maximum_limit": None, "basis": None,
                       "payment_history": {"ok": True, "late_invoices": []},
                       "missing_evidence": ["a guarantee covering this customer"]}  # fmt: skip
        reasons.append("request relies on a guarantee that no available evidence establishes")
    else:
        maximum = cap + (guarantee.amount_usd if guarantee else 0)
        needs_guarantee = req.requested_limit_usd > cap
        basis = guarantee.id if needs_guarantee and guarantee else f"cap:{tier}"
        if needs_guarantee and guarantee:
            evidence.append(guarantee.id)
        status = "eligible" if req.requested_limit_usd <= maximum else "exceeded"
        eligibility = {"status": status, "maximum_limit": maximum, "basis": basis,
                       "payment_history": {"ok": True, "late_invoices": []}}  # fmt: skip
        reasons.append(
            "the requested limit is within the customer's maximum"
            if status == "eligible"
            else "the requested limit exceeds the customer's maximum"
        )

    # -- authority: the band on the new limit, concurrence, separation of duties -------------
    evidence.append(policy.id)
    if "organization_chart" in available:
        evidence.append("organization_chart")
    evidence.append(req.id)
    band = policy.band_for(req.requested_limit_usd)
    limit = policy.limit_for(requestor.role) or 0.0
    authorized = req.requested_limit_usd <= limit and not policy.separation_of_duties
    outcome = {
        "unknown": "REQUEST_EVIDENCE",
        "ineligible": "REJECT_OR_ESCALATE",
        "exceeded": "REJECT_OR_ESCALATE",
    }.get(eligibility["status"], "APPROVE" if authorized else "APPROVE_WITH_AUTHORIZATION")
    approvers: list[dict[str, Any]] = []
    if outcome in APPROVALS:
        sod = policy.separation_of_duties
        a = credit_approver(truth, requestor, band.role, sod)
        approvers.append({"employee": a.id, "name": a.name, "role": a.role, "kind": "approval"})
        reasons.append(f"{a.name} approves as {truth.role_title(band.role)}")
        for c in policy.concurrence:
            if tier in c.tiers and req.requested_limit_usd > c.min_exclusive:
                b = credit_approver(truth, requestor, c.role, sod)
                approvers.append(
                    {"employee": b.id, "name": b.name, "role": b.role, "kind": "concurrence"}
                )
                reasons.append(f"{b.name} concurs for {truth.role_title(c.role)}")

    return {
        "decision_id": f"DEC-{scenario.id}",
        "scenario": scenario.id,
        "type": "credit_limit_increase",
        "as_of": as_of,
        "corpus": scenario.corpus,
        "subject": {"customer": cust.id},
        "request": {
            "id": req.id,
            "current_limit": req.current_limit_usd,
            "requested_limit": req.requested_limit_usd,
            "requestor": requestor.id,
        },
        "eligibility": eligibility,
        "authority": {
            "policy": policy.id,
            "requestor": {
                "employee": requestor.id,
                "maximum_limit": limit,
                "authorized": authorized,
            },
            "required": {"role": band.role, "maximum_limit": band.max_inclusive},
            "approvers": approvers,
        },  # fmt: skip
        "decision": {"outcome": outcome},
        "input": {"conflicts": conflicts},
        "reason": reasons,
        "evidence": evidence,
    }


def select_facts(truth: Truth, scenario: Scenario, available: frozenset[str]) -> dict[str, Any]:
    assert scenario.subject is not None
    cust, prod = scenario.subject["customer"], scenario.subject["product"]
    probes = []
    for p in scenario.probes:
        x = applicable_exception(truth, cust, prod, p.as_of, available)
        probes.append(
            {
                "as_of": p.as_of,
                "exception": x.id if x else None,
                "maximum_discount": x.maximum_discount if x else None,
            }
        )
    preserved = sorted(x.id for x in truth.exceptions if x.customer == cust and x.id in available)
    return {
        "scenario": scenario.id,
        "type": "fact_selection",
        "probes": probes,
        "preserved": preserved,
    }


def trace_provenance(truth: Truth, scenario: Scenario, artifacts: list[Artifact]) -> dict[str, Any]:
    assert scenario.subject is not None and scenario.as_of is not None
    available = available_keys(artifacts)
    x = applicable_exception(
        truth, scenario.subject["customer"], scenario.subject["product"], scenario.as_of, available
    )
    keys = {x.id, x.contract} if x else set()
    return {
        "scenario": scenario.id,
        "type": "provenance",
        "basis": x.id if x else None,
        "contract": x.contract if x else None,
        "authoritative": sorted(a.id for a in artifacts if keys & set(a.supports)),
        "hearsay": sorted(
            a.id for a in artifacts if keys & set(a.mentions) and not keys & set(a.supports)
        ),
    }


def resolve_identity(truth: Truth, scenario: Scenario) -> dict[str, Any]:
    wanted = set(scenario.expected["same_as"])
    return {
        "scenario": scenario.id,
        "type": "identity",
        "same_as": {c.id: list(c.source_ids.values()) for c in truth.customers if c.id in wanted},
    }


def check(truth: Truth, scenario: Scenario, result: dict[str, Any]) -> list[str]:
    """Differences between the oracle's result and the scenario's hand-authored expectation."""
    exp = scenario.expected
    got: dict[str, Any]
    if scenario.kind == "discount_decision":
        got = {
            "outcome": result["decision"]["outcome"],
            "commercial_eligibility": result["commercial_eligibility"]["status"],
            "eligibility_basis": result["commercial_eligibility"]["basis"],
            "requestor_authorized": result["authority"]["requestor"]["authorized"],
            "required_role": result["authority"]["required"]["role"],
            "approver": result["authority"]["approver"]["employee"],
            "evidence": result["evidence"],
            "input_conflicts": result["input"]["conflicts"],
        }
        return [f"{k}: expected {exp[k]!r}, oracle {got[k]!r}" for k in exp if exp[k] != got[k]]
    if scenario.kind == "sla_decision":
        northstar = sorted(
            [o["duty"], o["role"], o["holder"], o["due"]]
            for o in result["obligations"] if o["party"] == "northstar"
        )  # fmt: skip
        cust = sorted([o["duty"], o["status"]] for o in result["obligations"]
                      if o["party"] == "customer")  # fmt: skip
        got = {
            "outcome": result["decision"]["outcome"],
            "scope": result["scope"],
            "true_severity": result["severity"]["true"],
            "response": result["breach"]["response"],
            "restoration": result["breach"]["restoration"],
            "credit_usd": result["remedy"]["credit_usd"],
            "northstar": northstar,
            "customer": cust,
        }
        want = dict(exp)
        for k in ("northstar", "customer"):
            if k in want:
                want[k] = sorted([str(x) for x in row] for row in want[k])
        got = {k: ([[str(x) for x in row] for row in v] if k in ("northstar", "customer") else v)
               for k, v in got.items()}  # fmt: skip
        return [f"{k}: expected {want[k]!r}, oracle {got[k]!r}" for k in want if want[k] != got[k]]
    if scenario.kind == "credit_decision":
        got = {
            "outcome": result["decision"]["outcome"],
            "eligibility": result["eligibility"]["status"],
            "eligibility_basis": result["eligibility"]["basis"],
            "requestor_authorized": result["authority"]["requestor"]["authorized"],
            "required_role": result["authority"]["required"]["role"],
            "approvers": [[a["employee"], a["kind"]] for a in result["authority"]["approvers"]],
            "evidence": result["evidence"],
            "input_conflicts": result["input"]["conflicts"],
        }
        return [f"{k}: expected {exp[k]!r}, oracle {got[k]!r}" for k in exp if exp[k] != got[k]]
    if scenario.kind == "fact_selection":
        out = []
        for probe, res in zip(scenario.probes, result["probes"], strict=True):
            if (probe.expected_exception, probe.expected_maximum) != (
                res["exception"],
                res["maximum_discount"],
            ):
                out.append(
                    f"probe {probe.as_of}: expected {probe.expected_exception}, "
                    f"oracle {res['exception']}"
                )
        if sorted(exp["preserved"]) != result["preserved"]:
            out.append(f"preserved: expected {exp['preserved']}, oracle {result['preserved']}")
        return out
    if scenario.kind == "provenance":
        out = [
            f"{k}: expected {exp[k]!r}, oracle {result[k]!r}"
            for k in ("basis", "contract")
            if exp[k] != result[k]
        ]
        missing = set(exp["must_cite"]) - set(result["authoritative"])
        wrong = set(exp["must_not_cite_as_basis"]) & set(result["authoritative"])
        out += [f"not authoritative: {m}" for m in sorted(missing)]
        out += [f"hearsay treated as basis: {w}" for w in sorted(wrong)]
        return out
    return [
        f"same_as {cid}: expected {ids}, oracle {result['same_as'].get(cid)}"
        for cid, ids in exp["same_as"].items()
        if sorted(ids) != sorted(result["same_as"].get(cid, []))
    ]
