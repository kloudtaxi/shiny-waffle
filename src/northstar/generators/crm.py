"""Northstar CRM exports: accounts and discount requests.

CRM speaks in account ids, SKUs and email addresses — never in canonical
customer, product or employee ids. Resolving those is the knowledge foundation's job.
"""

from __future__ import annotations

from northstar.artifacts import Artifact
from northstar.export.csv import to_csv
from northstar.factories import Background
from northstar.model import Truth


def generate(truth: Truth, bg: Background) -> list[Artifact]:
    return [_accounts(truth, bg), _discount_requests(truth, bg)]


def _email(truth: Truth, bg: Background, emp_id: str) -> str:
    domain = truth.organization.email_domain
    names = {e.id: e.name for e in truth.employees} | {e.id: e.name for e in bg.employees}
    return f"{names[emp_id].lower().replace(' ', '.')}@{domain}"


def _name(truth: Truth, bg: Background, emp_id: str) -> str:
    names = {e.id: e.name for e in truth.employees} | {e.id: e.name for e in bg.employees}
    return names[emp_id]


def _accounts(truth: Truth, bg: Background) -> Artifact:
    header = [
        "account_id",
        "account_name",
        "account_tier",
        "segment",
        "industry",
        "billing_street",
        "billing_city",
        "billing_state",
        "duns_number",
        "account_owner",
        "owner_email",
    ]
    rows = []
    for c in truth.customers:
        account = truth.account_for(c.id)
        owner = account.owner if account else bg.truth_customer_owners[c.id]
        rows.append(
            [
                c.source_ids["crm"],
                account.name if account else c.canonical_name,
                account.tier if account else "Standard",
                c.segment,
                c.industry,
                c.address.street,
                c.address.city,
                c.address.state,
                c.duns,
                _name(truth, bg, owner),
                _email(truth, bg, owner),
            ]
        )
    for b in bg.customers:
        rows.append(
            [
                b.crm_id,
                b.name,
                "Standard",
                b.segment,
                b.industry,
                b.street,
                b.city,
                b.state,
                b.duns,
                _name(truth, bg, b.owner),
                _email(truth, bg, b.owner),
            ]
        )
    rows.sort(key=lambda r: r[0])
    return Artifact(
        id="crm_accounts",
        path="structured/crm_accounts.csv",
        source_system="Northstar CRM",
        description="CRM account list with owners, tiers and segments.",
        content=to_csv(header, rows),
        supports=("CRM-2048", "CRM-2091", "account_ownership"),
        asserts=("F01", "F04", "F17"),
    )


def _discount_requests(truth: Truth, bg: Background) -> Artifact:
    header = [
        "request_id",
        "account_id",
        "product_sku",
        "requested_discount_pct",
        "list_value_usd",
        "discount_value_usd",
        "net_value_usd",
        "requested_by",
        "request_date",
        "justification",
        "status",
        "approved_by",
        "approved_on",
    ]
    crm_of = {c.id: c.source_ids["crm"] for c in truth.customers} | {
        b.id: b.crm_id for b in bg.customers
    }
    products = {p.id: p for p in truth.products} | {p.id: p for p in bg.products}
    rows: list[list[object]] = []
    for d in truth.discount_requests:
        justification = (
            f"Contract pricing per {truth.contract(d.basis_ref).title}"
            if d.basis == "contract_exception" and d.basis_ref
            else "Competitive"
        )
        rows.append(
            [
                d.id,
                crm_of[d.customer],
                products[d.product].sku,
                f"{d.requested_discount * 100:.1f}",
                d.list_value_usd,
                d.discount_value_usd,
                d.net_value_usd,
                _email(truth, bg, d.requestor),
                d.request_date.isoformat(),
                justification,
                d.status,
                _email(truth, bg, d.approved_by) if d.approved_by else None,
                d.request_date.isoformat() if d.approved_by else None,
            ]
        )
    for r in bg.discount_requests:
        price = products[r.product].list_price_usd
        disc = round(price * r.requested_discount)
        rows.append(
            [
                r.id,
                crm_of[r.customer],
                products[r.product].sku,
                f"{r.requested_discount * 100:.1f}",
                price,
                disc,
                price - disc,
                _email(truth, bg, r.requestor),
                r.request_date.isoformat(),
                "Competitive",
                r.status,
                _email(truth, bg, r.approved_by),
                r.request_date.isoformat(),
            ]
        )
    rows.sort(key=lambda r: (str(r[8]), str(r[0])))
    return Artifact(
        id="discount_requests",
        path="structured/discount_requests.csv",
        source_system="Northstar CRM",
        description="Discount requests and their approval status.",
        content=to_csv(header, rows),
        supports=("DR-9001",),
        asserts=("F18",),
        # DR-8104 is precedent, not a basis: it mentions the exception, it does not grant it.
        mentions=("DR-8104", "EXC-ACME-NS500-15"),
    )
