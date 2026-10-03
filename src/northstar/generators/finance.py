"""Finance evidence for the credit decision (experiment 5, lab extension).

The Finance-owned credit policies, the Acme parent guarantee, and three ERP exports (credit master,
invoices, credit requests), plus an email that mentions the guarantee without establishing it.

Generated last, with no shared randomness, so every other artifact stays byte-identical. As with
discounts, the policies name roles and never people, and no single artifact contains a
scenario's answer.
"""

from __future__ import annotations

from northstar.artifacts import Artifact
from northstar.export.csv import to_csv
from northstar.export.markdown import document, table, usd
from northstar.factories import Background
from northstar.model import CreditPolicy, Truth

ROLE_WORDS = {
    "AR_SPECIALIST": ("Accounts Receivable Specialists", "Accounts Receivable Specialist"),
    "FINANCE_MANAGER": ("Finance Managers", "Finance Manager"),
    "FINANCE_DIRECTOR": ("Directors of Finance", "Director of Finance"),
    "VP_SALES": ("VPs Sales", "VP Sales"),
}


def generate(truth: Truth, bg: Background) -> list[Artifact]:
    return [
        *(_policy(truth, p) for p in truth.credit_policies),
        _guarantee(truth),
        _credit_master(truth, bg),
        _invoices(truth, bg),
        _credit_requests(truth, bg),
        _email(truth),
    ]


def _bands(p: CreditPolicy) -> list[str]:
    out = []
    for b in p.bands:
        plural, title = ROLE_WORDS[b.role]
        hi = usd(int(b.max_inclusive)) if b.max_inclusive is not None else None
        if b.min_exclusive is None:
            out.append(f"- {plural} may approve credit limits up to and including {hi}.")
        elif hi is not None:
            out.append(f"- Credit limits greater than {usd(int(b.min_exclusive))} and up to and "
                       f"including {hi} require {title} approval.")  # fmt: skip
        else:
            lo = usd(int(b.min_exclusive))
            out.append(f"- Credit limits greater than {lo} require {title} approval.")
    return out


def _policy(truth: Truth, p: CreditPolicy) -> Artifact:
    year = p.valid_from.year
    concurrence = [
        f"- For {' and '.join(c.tiers)} accounts, credit limits greater than "
        f"{usd(int(c.min_exclusive))} also require {ROLE_WORDS[c.role][1]} concurrence."
        for c in p.concurrence
    ] or [f"- No concurrence is required in {year}."]
    caps = "; ".join(f"{usd(v)} for {k} accounts" for k, v in p.caps.items())
    body = f"""
# Northstar Credit Policy {year}

## 1. Purpose

Sets who may approve customer credit limits, and which customers may receive a higher limit, for
calendar {year}.

## 2. Effective period

This policy is effective from {p.valid_from.isoformat()} through {p.valid_to.isoformat()}.
It replaces the previous credit policy in full for requests dated on or after
{p.valid_from.isoformat()}.

## 3. Approval authority

Authority applies to the new total credit limit requested.

{chr(10).join(_bands(p))}

## 4. Concurrence

{chr(10).join(concurrence)}

## 5. Eligibility

- Payment history: no invoice due in the {p.lookback_days // 365 * 12} months before the request
  may have been paid more than {p.max_days_late} days after its due date, or be unpaid more than
  {p.max_days_late} days after it.
- Maximum credit limit: {caps}. Account tiers are as recorded in Northstar CRM.
- A parent-company guarantee in force raises the maximum by the guaranteed amount, for the
  customer the guarantee names.

## 6. Separation of duties

- No one may approve or concur on a credit request they submitted. The approval or concurrence
  passes to the requestor's manager.

## 7. Records

- Credit decisions are recorded in Northstar ERP with the approver and, where required, the
  concurring approver.
"""
    return Artifact(
        id=p.id,
        path=f"documents/{p.id}.md",
        source_system="Northstar Drive",
        description=f"Finance's credit policy for {year}: authority bands, eligibility, duties.",
        content=document(
            {
                "doc_id": f"CREDIT-POLICY-{year}",
                "title": p.title,
                "owner": "Finance",
                "created": f"{year - 1}-12-15",
                "effective_from": p.valid_from.isoformat(),
                "effective_to": p.valid_to.isoformat(),
                "classification": "Internal",
            },
            body,
        ),
        supports=(p.id,),
        asserts=("F22", "F23") if year == 2026 else (),
    )


def _guarantee(truth: Truth) -> Artifact:
    g = truth.guarantees[0]
    cust = truth.customer(g.customer)
    a = cust.address
    body = f"""
# Parent Company Guarantee

**Guarantee reference:** {g.id}

This Guarantee is given by **{g.guarantor}** ("Guarantor"), Milwaukee, Wisconsin, in favour of
**Northstar Industrial Systems** ("Northstar").

## 1. Guaranteed party

The Guarantor guarantees the payment obligations to Northstar of its wholly owned subsidiary
**{cust.erp_name}**, doing business as **{cust.canonical_name}** ("Customer"), {a.street},
{a.city}, {a.state} {a.postal_code}. No other company is covered.

## 2. Amount

The Guarantor's liability under this Guarantee is limited to **{usd(g.amount_usd)}** in aggregate.

## 3. Term

This Guarantee is effective from {g.valid_from.isoformat()} to {g.valid_to.isoformat()}.

## Signatures

{
        table(
            ["For the Guarantor", "Accepted for Northstar"],
            [
                ["Laura Whitfield, Chief Financial Officer", "Northstar Legal"],
                ["2025-12-16", "2025-12-18"],
            ],
        )
    }
"""  # noqa: E501
    return Artifact(
        id="acme_parent_guarantee",
        path="documents/acme_parent_guarantee.md",
        source_system="Northstar Drive",
        description="A parent-company guarantee of a customer's payment obligations.",
        content=document(
            {
                "doc_id": g.id,
                "title": g.title,
                "owner": "Legal",
                "created": "2025-12-18",
                "effective_from": g.valid_from.isoformat(),
                "effective_to": g.valid_to.isoformat(),
            },
            body,
        ),
        supports=(g.id,),
        asserts=("F24",),
    )


def _credit_master(truth: Truth, bg: Background) -> Artifact:
    header = ["erp_customer_id", "credit_limit_usd", "currency", "last_reviewed"]
    rows = [
        [c.source_ids["erp"], c.credit_limit_usd, "USD", "2026-01-15"]
        for c in truth.customers
        if c.credit_limit_usd is not None
    ]
    erp = {c.id: c.erp_id for c in bg.customers}
    rows += [[erp[cid], lim, "USD", "2025-12-31"] for cid, lim in bg.credit_limits.items()]
    rows.sort(key=lambda r: (len(str(r[0])), str(r[0])))
    return Artifact(
        id="erp_credit",
        path="structured/erp_credit.csv",
        source_system="Northstar ERP",
        description="Credit master: each ERP customer's current credit limit.",
        content=to_csv(header, rows),
        supports=("erp_credit",),
        asserts=("F26",),
    )


def _invoices(truth: Truth, bg: Background) -> Artifact:
    header = ["invoice_id", "erp_customer_id", "invoice_date", "due_date", "amount_usd",
              "paid_date", "reference"]  # fmt: skip
    rows = [
        [i.id, truth.customer(i.customer).source_ids["erp"], i.invoice_date.isoformat(),
         i.due_date.isoformat(), i.amount_usd, i.paid_date.isoformat() if i.paid_date else None,
         i.reference]
        for i in truth.invoices
    ] + [
        [i.id, i.erp_customer_id, i.invoice_date.isoformat(), i.due_date.isoformat(),
         i.amount_usd, i.paid_date.isoformat() if i.paid_date else None, i.reference]
        for i in bg.invoices
    ]  # fmt: skip
    rows.sort(key=lambda r: (str(r[2]), str(r[0])))
    return Artifact(
        id="erp_invoices",
        path="structured/erp_invoices.csv",
        source_system="Northstar ERP",
        description="Accounts receivable: invoices with due and paid dates.",
        content=to_csv(header, rows),
        supports=("erp_invoices",),
    )


def _credit_requests(truth: Truth, bg: Background) -> Artifact:
    header = ["request_id", "erp_customer_id", "current_limit_usd", "requested_limit_usd",
              "requested_by", "request_date", "justification", "status", "approved_by",
              "approved_on"]  # fmt: skip
    domain = truth.organization.email_domain
    emails = {e.id: e.email(domain) for e in truth.employees}
    emails |= {e.id: f"{e.name.lower().replace(' ', '.')}@{domain}" for e in bg.employees}
    erp = {c.id: c.erp_id for c in bg.customers}
    rows = [
        [r.id, truth.customer(r.customer).source_ids["erp"], r.current_limit_usd,
         r.requested_limit_usd, emails[r.requestor], r.request_date.isoformat(), r.justification,
         r.status, None, None]
        for r in truth.credit_requests
    ] + [
        [r.id, erp[r.customer], r.current_limit_usd, r.requested_limit_usd, emails[r.requestor],
         r.request_date.isoformat(), "Order growth", r.status,
         emails.get(r.approved_by), r.request_date.isoformat() if r.approved_by else None]
        for r in bg.credit_requests
    ]  # fmt: skip
    return Artifact(
        id="credit_requests",
        path="structured/credit_requests.csv",
        source_system="Northstar ERP",
        description="Credit-limit requests and their approval status.",
        content=to_csv(header, rows),
        supports=tuple(r.id for r in truth.credit_requests),
        asserts=("F25",),
    )


def _email(truth: Truth) -> Artifact:
    req = truth.credit_request("CR-9201")
    sender = truth.employee(req.requestor)
    finance = truth.employee("EMP-401")
    domain = truth.organization.email_domain
    body = f"""
**From:** {sender.name} <{sender.email(domain)}>
**To:** {finance.name} <{finance.email(domain)}>
**Date:** {req.request_date.isoformat()} 10:31 CT
**Subject:** Acme credit limit — {req.id}

Hi {finance.first_name},

Acme's third plant is coming online and their NS-500 orders will step up through Q1. I've raised
{req.id} to take their credit limit from {usd(req.current_limit_usd)} to
{usd(req.requested_limit_usd)}.

If they need more headroom later, Acme Group's parent guarantee should cover it. Gina says it's
still in place.

Thanks,
{sender.first_name}
"""
    return Artifact(
        id="email_sarah_to_priya",
        path="documents/email_sarah_to_priya.md",
        source_system="Email",
        description=f"Email from the account owner to Finance about {req.id}.",
        content=document(
            {
                "doc_id": "MSG-20260923-1031",
                "title": f"Acme credit limit — {req.id}",
                "from": sender.email(domain),
                "to": finance.email(domain),
                "sent": req.request_date.isoformat(),
            },
            body,
        ),
        mentions=(req.id, "GRT-ACME-2026", req.customer),
    )
