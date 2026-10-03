"""The credit-limit-increase spec on the decision kernel (experiment 5).

Written after the kernel was frozen (`runs/2026-10-03-exp5-credit/plan.md`). It holds only what
is particular to credit:
- its questions;
- how it reads its own documents: the credit policy's payment rule and caps, and the guarantee's
  amount and guaranteed party;
- how eligibility follows: payment history from invoices, the account-tier cap, and a guarantee
  that covers the customer;
- its outcome table and its record.

Provenance, validity windows, authority bands, approver resolution, concurrence, separation of
duties, judgments and gating are the kernel's. Every kernel change this spec needed is marked
`K-n (experiment 5)` in `kernel.py`.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from kernel import (
    Doc,
    Engine,
    Evidence,
    Guards,
    KindRule,
    authority_from_evidence,
    concurrences,
    covering,
    gate,
    judge,
    linked,
    screen,
)

APPROVALS = ("APPROVE", "APPROVE_WITH_AUTHORIZATION")
Q_RELIES = {
    "type": "choice",
    "instructions": "What does the credit request in `request` rely on?",
    "criteria": {
        "guarantee": "A guarantee or other credit support from a third party",
        "standard": "The customer's own standing: order volume, growth or payment record",
        "unclear": "The request does not say what it relies on",
    },
}
Q_PARTY = {
    "type": "choice",
    "instructions": (
        "Is the customer in `request_customer` the same legal entity as the company whose "
        "obligations are guaranteed in `document`?"
    ),
    "criteria": {
        "same_legal_entity": (
            "Yes: the same company, possibly under a trading name (doing business as) or a "
            "shortened or differently spelled name"
        ),
        "different_entity": "No: a different company, even if the names look alike",
        "unclear": "The information given cannot tell",
    },
}


def guarantee_amount(doc: Doc) -> float | None:
    m = re.search(r"limited to \**\$([\d,]+)", doc.body)
    return float(m[1].replace(",", "")) if m else None


def guaranteed_party(doc: Doc) -> str:
    for para in re.split(r"\n\s*\n", doc.body):
        if "guarantees the payment obligations" in para:
            return " ".join(para.split())
    return " ".join(doc.body.split())


def payment_rule(pol: Doc) -> tuple[int, int] | None:
    """(lookback in days, days late allowed), from the policy's eligibility section."""
    flat = " ".join(pol.body.split())
    m = re.search(r"in the (\d+) months before the request may have been paid more than (\d+) days",
                  flat)  # fmt: skip
    return (round(int(m[1]) * 365 / 12), int(m[2])) if m else None


def caps(pol: Doc) -> dict[str, float]:
    flat = " ".join(pol.body.split())
    m = re.search(r"Maximum credit limit: (.+?)\. ", flat)
    return {t: float(a.replace(",", "")) for a, t in re.findall(r"\$([\d,]+) for (\w+) accounts",
                                                                 m[1] if m else "")}  # fmt: skip


def late_invoices(
    invoices: list[dict[str, str]], erp_id: str, as_of: date, lookback: int, allowed: int
) -> list[str]:
    """Invoices due in the lookback window paid, or still unpaid, more than ``allowed`` days after
    their due date, as known on ``as_of`` (a later payment isn't known yet)."""
    out = []
    for i in invoices:
        due = date.fromisoformat(i["due_date"])
        if i["erp_customer_id"] != erp_id or not (as_of - timedelta(days=lookback) <= due <= as_of):
            continue
        paid = date.fromisoformat(i["paid_date"]) if i["paid_date"] else None
        known = paid if paid is not None and paid <= as_of else as_of
        if (known - due).days > allowed:
            out.append(i["invoice_id"])
    return out


GUARDS = Guards(
    rules=(
        KindRule("policy", id_prefixes=("CREDIT-POLICY",), title_words=("Credit Policy",)),
        KindRule("guarantee", id_prefixes=("GRT-",), title_words=("Guarantee",)),
    ),
    owners={"policy": {"Finance"}, "guarantee": {"Legal"}},
    value_of=guarantee_amount,
    product_of=lambda d: "",
    graded=("guarantee",),
    approval_kinds=(),
    amending_kinds=(),
    schedule_kinds=(),
)


def decide(
    eng: Engine, ev: Evidence, as_of: date, record: dict[str, str], sid: str
) -> dict[str, Any]:
    """One credit decision on one corpus. ``record`` is the ERP credit request row."""
    used: list[dict[str, Any]] = []
    flags: list[str] = []
    staff = ev.table("employees")
    s = screen(eng, ev.docs(), GUARDS, staff, [], used, flags)
    erp = next(
        c for c in ev.table("customers") if c["erp_customer_id"] == record["erp_customer_id"]
    )
    account = linked(erp, ev.table("crm_accounts"), ("duns_number",))  # K-4
    tier = account["account_tier"] if account else "Standard"
    customer = {"name": erp["customer_name"], "street": erp["bill_to_street"],
                "city": erp["bill_to_city"], "state": erp["bill_to_state"]}  # fmt: skip
    amount = float(record["requested_limit_usd"])
    eligibility: dict[str, Any] = {"status": "unknown", "maximum_limit": None, "basis": None}
    relied: list[Doc] = []
    inforce = covering(s.pols, as_of)

    relies = judge(eng, {"request": {"justification": record["justification"]}}, "relies", Q_RELIES)
    used.append(relies)
    if len(inforce) == 1 and (rule := payment_rule(inforce[0])):
        pol = inforce[0]
        late = late_invoices(ev.table("erp_invoices"), erp["erp_customer_id"], as_of, *rule)
        cap = caps(pol).get(tier)
        guarantee = None
        if not late and cap is not None and (relies["choice"] != "standard" or amount > cap):
            for d in covering(s.good["guarantee"], as_of):  # the kernel's validity windows
                j = judge(eng, {"request_customer": customer, "document": guaranteed_party(d)},
                          "party", Q_PARTY)  # fmt: skip
                used.append(j)
                if j["choice"] == "same_legal_entity":
                    guarantee = d
                    break
        if late:
            eligibility = {"status": "ineligible", "maximum_limit": None, "basis": None,
                           "late_invoices": late}  # fmt: skip
        elif cap is None:
            eligibility = {"status": "unknown", "maximum_limit": None, "basis": None}
        elif relies["choice"] == "guarantee" and guarantee is None:
            eligibility = {"status": "unknown", "maximum_limit": None, "basis": None}
        else:
            extra = (guarantee_amount(guarantee) or 0.0) if guarantee else 0.0
            maximum = cap + extra
            basis = guarantee.doc_id if guarantee and amount > cap else f"cap:{tier}"
            eligibility = {"status": "eligible" if amount <= maximum else "exceeded",
                           "maximum_limit": maximum, "basis": basis}  # fmt: skip
            if guarantee:
                relied.append(guarantee)

    auth = authority_from_evidence(eng, s.pols, staff, as_of, amount, record["requested_by"],
                                   used, flags)  # fmt: skip
    approvers: list[dict[str, str]] = []
    if auth is None:
        outcome = "REQUEST_EVIDENCE"
        auth = {"policy": None, "requestor_limit": None, "requestor_authorized": None,
                "required_role": None, "approver": None}  # fmt: skip
    else:
        pol_doc = auth.pop("_doc")
        relied.append(pol_doc)
        approval = "APPROVE" if auth["requestor_authorized"] else "APPROVE_WITH_AUTHORIZATION"
        by_status = {"unknown": "REQUEST_EVIDENCE", "ineligible": "REJECT_OR_ESCALATE",
                     "exceeded": "REJECT_OR_ESCALATE"}  # fmt: skip
        outcome = by_status.get(eligibility["status"], approval)
        if outcome in APPROVALS:
            approvers = [{"name": str(auth["approver"]), "kind": "approval"}] + [
                {"name": c["full_name"], "kind": "concurrence"}
                for c in concurrences(
                    eng, pol_doc, staff, amount, tier, record["requested_by"], used
                )  # fmt: skip
            ]
    uncertain, gated = gate(outcome, relied, s.inconsistent, used, flags)
    return {
        "scenario": sid,
        "outcome": outcome,
        "gated_outcome": gated,
        "uncertain": uncertain,
        "eligibility": eligibility,
        "authority": auth,
        "approvers": approvers,
        "judgments": used,
        "flags": flags,
    }
