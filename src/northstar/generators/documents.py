"""Northstar Drive / Service documents.

Design rule (doc 02 §5): facts are *distributed*. The authority matrix names
roles, never people; the org chart names people, never percentages; the
contract grants eligibility, never authority. Composing them is the experiment.
"""

from __future__ import annotations

from datetime import date, timedelta

from faker import Faker

from northstar.artifacts import Artifact
from northstar.export.markdown import document, pct, table, usd
from northstar.factories import Background
from northstar.model import Band, Policy, Truth

DRIVE = "Northstar Drive"


def generate(truth: Truth, bg: Background, fake: Faker) -> list[Artifact]:
    acme_contacts = [fake.name() for _ in range(3)]
    return [
        _policy(truth, truth.policy("pricing_policy_2025"), date(2024, 12, 10), ("F11",)),
        _policy(
            truth, truth.policy("pricing_policy_2026"), date(2025, 12, 8), ("F08", "F09", "F10")
        ),
        _authority_matrix(truth),
        _org_chart(truth, bg),
        _msa(truth, acme_contacts[0]),
        _exception_current(truth),
        _exception_2023(truth),
        _sop(truth),
        _account_strategy(truth, acme_contacts),
        _service_ticket(truth, fake),
    ]


def _band_sentence(truth: Truth, band: Band) -> str:
    who = truth.role_title(band.role)
    lo, hi = band.min_exclusive, band.max_inclusive
    if lo is None and hi is not None:
        return f"{who}s may approve discounts up to and including {pct(hi)}."
    if lo is not None and hi is None:
        return f"Discounts greater than {pct(lo)} require {who} approval."
    assert lo is not None and hi is not None
    return (
        f"Discounts greater than {pct(lo)} and up to and including {pct(hi)} "
        f"require {who} approval."
    )


def _policy(truth: Truth, p: Policy, created: date, asserts: tuple[str, ...]) -> Artifact:
    year = p.valid_from.year
    previous = next((q for q in truth.policies if q.valid_to.year == year - 1), None)
    lines = [
        f"# {p.title}",
        "",
        "## 1. Purpose",
        "",
        f"Sets discount approval authority for direct enterprise sales for calendar {year}.",
        "",
        "## 2. Effective period",
        "",
        f"This policy is effective from {p.valid_from.isoformat()} through "
        f"{p.valid_to.isoformat()}.",
    ]
    if previous:
        lines.append(
            f"It replaces the {previous.title} in full for requests dated on or "
            f"after {p.valid_from.isoformat()}."
        )
    lines += ["", "## 3. Approval authority", ""]
    lines += [f"- {_band_sentence(truth, b)}" for b in p.bands]
    if p.authority_matrix_document:
        lines += [
            "",
            "The Approval Authority Matrix is the operational reference for these thresholds.",
        ]
    lines += ["", "## 4. Rules", ""] + [f"- {r}" for r in p.rules]
    return Artifact(
        id=p.id,
        path=f"documents/{p.id}.md",
        source_system=DRIVE,
        description=f"{p.title}.",
        content=document(
            {
                "doc_id": p.id.upper().replace("_", "-"),
                "title": p.title,
                "owner": "Revenue Operations",
                "created": created.isoformat(),
                "effective_from": p.valid_from.isoformat(),
                "effective_to": p.valid_to.isoformat(),
                "classification": "Internal",
            },
            "\n".join(lines),
        ),
        supports=(p.id,),
        asserts=asserts,
    )


def _authority_matrix(truth: Truth) -> Artifact:
    p = truth.policy("pricing_policy_2026")

    def band_text(b: Band) -> str:
        if b.min_exclusive is None and b.max_inclusive is not None:
            return f"≤{pct(b.max_inclusive)}"
        if b.max_inclusive is None and b.min_exclusive is not None:
            return f">{pct(b.min_exclusive)}"
        assert b.min_exclusive is not None and b.max_inclusive is not None
        return f">{pct(b.min_exclusive)} and ≤{pct(b.max_inclusive)}"

    rows = [[truth.role_title(b.role), band_text(b)] for b in p.bands]
    body = "\n".join(
        [
            "# Approval Authority Matrix — Enterprise Discounts (2026)",
            "",
            f"Applies to discount requests governed by the {p.title}.",
            "",
            table(["Role", "Discount authority"], rows),
            "",
            "Notes:",
            "",
            "- Authority attaches to the role, not to the individual or the account.",
            "- Discounts are measured against current list price.",
            f"- Approvals above {pct(p.approval_evidence_required_above or 0)} must be recorded in "
            "Northstar CRM.",
        ]
    )
    return Artifact(
        id="approval_authority_matrix",
        path="documents/approval_authority_matrix.md",
        source_system=DRIVE,
        description="2026 enterprise discount authority by role.",
        content=document(
            {
                "doc_id": "APP-MATRIX-2026",
                "title": "Approval Authority Matrix — Enterprise Discounts",
                "owner": "Revenue Operations",
                "created": "2025-12-08",
                "effective_from": p.valid_from.isoformat(),
                "effective_to": p.valid_to.isoformat(),
            },
            body,
        ),
        supports=("approval_authority_matrix",),
        asserts=("F08", "F09", "F10"),
    )


def _org_chart(truth: Truth, bg: Background) -> Artifact:
    people: dict[str, tuple[str, str, str | None]] = {
        e.id: (e.name, truth.role_title(e.role), e.manager) for e in truth.employees
    }
    people |= {e.id: (e.name, e.title, e.manager) for e in bg.employees}
    children: dict[str | None, list[str]] = {}
    for pid, (_, _, mgr) in people.items():
        children.setdefault(mgr, []).append(pid)

    lines: list[str] = []

    def walk(pid: str, depth: int) -> None:
        name, title, _ = people[pid]
        lines.append(f"{'  ' * depth}- **{name}** — {title}")
        for child in sorted(children.get(pid, []), key=lambda c: (people[c][1], people[c][0])):
            walk(child, depth + 1)

    for root in sorted(children[None]):
        walk(root, 0)
    body = "\n".join(
        [
            "# Northstar Industrial Systems — Organization Chart (Revenue & Finance)",
            "",
            "Reporting lines as of 2026-09-01. Indentation shows who reports to whom.",
            "",
            *lines,
        ]
    )
    return Artifact(
        id="organization_chart",
        path="documents/organization_chart.md",
        source_system=DRIVE,
        description="Reporting lines and titles for the revenue and finance organizations.",
        content=document(
            {
                "doc_id": "ORG-CHART-2026-09",
                "title": "Organization Chart — Revenue & Finance",
                "owner": "People Operations",
                "created": "2026-09-01",
            },
            body,
        ),
        supports=("organization_chart",),
        asserts=("F05", "F06", "F07"),
    )


def _msa(truth: Truth, acme_signatory: str) -> Artifact:
    c = truth.contract("MSA-ACME-2025")
    cust = truth.customer(c.customer)
    x = truth.exception("EXC-ACME-NS500-15")
    ns500 = truth.product(x.product)
    cro = truth.holders_of("CRO")[0]
    covered = "\n".join(f"- {truth.product(p).name} ({truth.product(p).sku})" for p in c.covers)
    body = f"""
# Master Supply Agreement

**Agreement reference:** {c.aliases[0]}

This Master Supply Agreement is entered into between **{truth.organization.name}**
("Northstar"), {truth.organization.headquarters}, and **{cust.erp_name}**, doing business as
**{cust.canonical_name}** ("Customer"), {cust.address.street}, {cust.address.city},
{cust.address.state} {cust.address.postal_code}.

## 1. Term

This Agreement is effective {c.valid_from:%B} {c.valid_from.day}, {c.valid_from.year} and
expires {c.valid_to:%B} {c.valid_to.day}, {c.valid_to.year}, unless terminated earlier under
Section 9.

## 2. Products

Northstar will supply the following products under this Agreement:

{covered}

## 3. Pricing

3.1 Prices are Northstar's current list prices less any discount agreed in an Order.

3.2 **Strategic account pricing.** Customer is eligible for discounts of up to
**{pct(x.maximum_discount)}** on the {ns500.name}, as set out in the pricing exception attached as
Schedule B.

3.3 Customer's contractual pricing eligibility does not modify Northstar's internal approval
authority. Each discount remains subject to approval under Northstar's internal policies.

## 9. Termination

Either party may terminate for material breach on 60 days' written notice.

## Signatures

| For Northstar | For Customer |
|---|---|
| {cro.name}, {truth.role_title(cro.role)} | {acme_signatory}, VP Procurement |
| {c.valid_from - _days(12):%Y-%m-%d} | {c.valid_from - _days(10):%Y-%m-%d} |
"""
    return Artifact(
        id="acme_master_supply_agreement",
        path="documents/acme_master_supply_agreement.md",
        source_system=DRIVE,
        description="Master supply agreement with Acme, incl. the strategic-pricing clause.",
        content=document(
            {
                "doc_id": c.aliases[0],
                "title": "Master Supply Agreement — Acme",
                "owner": "Legal",
                "created": (c.valid_from - _days(12)).isoformat(),
                "effective_from": c.valid_from.isoformat(),
                "effective_to": c.valid_to.isoformat(),
            },
            body,
        ),
        supports=(c.id,),
        asserts=("F02", "F03", "F12", "F14"),
        mentions=(x.id,),
    )


def _exception_current(truth: Truth) -> Artifact:
    x = truth.exception("EXC-ACME-NS500-15")
    old = truth.exception(x.supersedes or "")
    cust = truth.customer(x.customer)
    contract = truth.contract(x.contract)
    prod = truth.product(x.product)
    ae = truth.employee(truth.account_for(cust.id).owner)  # type: ignore[union-attr]
    cro = truth.holders_of("CRO")[0]
    body = f"""
# Pricing Exception — {x.title}

**Schedule B to agreement {contract.aliases[0]}**

| Field | Value |
|---|---|
| Exception ID | {x.id} |
| Customer | {cust.canonical_name} |
| Product | {prod.name} ({prod.sku}) only |
| Maximum eligible discount | {pct(x.maximum_discount)} of list price |
| Effective | {x.valid_from.isoformat()} |
| Expires | {x.valid_to.isoformat()} |

## Scope

This exception applies only to the product identified above. It does not apply to any other
Northstar product.

## Relationship to earlier exceptions

Supersedes {old.id} for requests dated on or after {x.valid_from.isoformat()}.

## Authority

This exception establishes commercial eligibility only. It does not grant approval authority
to any Northstar employee.

Prepared by: {ae.name}
Exception approved by: {cro.name}, {truth.role_title(cro.role)}, {x.valid_from - _days(12):%Y-%m-%d}
"""
    return Artifact(
        id="acme_pricing_exception",
        path="documents/acme_pricing_exception.md",
        source_system=DRIVE,
        description="The current Acme NS-500 strategic account pricing exception.",
        content=document(
            {
                "doc_id": x.id,
                "title": x.title,
                "owner": "Deal Desk",
                "created": (x.valid_from - _days(12)).isoformat(),
                "effective_from": x.valid_from.isoformat(),
                "effective_to": x.valid_to.isoformat(),
            },
            body,
        ),
        supports=(x.id,),
        asserts=("F12", "F13", "F16"),
        mentions=(contract.id, old.id),
    )


def _exception_2023(truth: Truth) -> Artifact:
    x = truth.exception("EXC-ACME-NS500-10")
    contract = truth.contract(x.contract)
    prod = truth.product(x.product)
    cust = truth.customer(x.customer)
    # Written in 2023 and never updated: its "Status: Active" is stale, not false.
    body = f"""
# {cust.canonical_name} — NS-500 Volume Pricing Exception

Agreement: {contract.aliases[0]}
Status: Active

{cust.canonical_name} may receive up to **{pct(x.maximum_discount)}** off list price on the
{prod.name} ({prod.sku}) for orders placed from {x.valid_from.isoformat()} to
{x.valid_to.isoformat()}.

Exception ID: {x.id}
"""
    return Artifact(
        id="acme_pricing_exception_2023",
        path="documents/acme_pricing_exception_2023.md",
        source_system=DRIVE,
        description="The earlier (2023) Acme NS-500 pricing exception.",
        content=document(
            {
                "doc_id": x.id,
                "title": "Acme NS-500 Volume Pricing Exception",
                "owner": "Deal Desk",
                "created": (x.valid_from - _days(20)).isoformat(),
            },
            body,
        ),
        supports=(x.id, contract.id),
        asserts=("F15",),
    )


def _sop(truth: Truth) -> Artifact:
    steps = [
        "Receive the discount request in Northstar CRM.",
        "Identify the customer (CRM account and ERP customer may use different names).",
        "Identify the product by SKU.",
        "Check for an active customer contract on the request date.",
        "Check for a pricing exception covering *this* product on the request date.",
        "Determine the pricing policy in effect on the request date.",
        "Determine the requestor's approval authority under that policy.",
        "Determine the required approver from the Approval Authority Matrix.",
        "Approve, reject, or escalate.",
        "Record the decision and the evidence relied on in Northstar CRM.",
    ]
    body = "\n".join(
        [
            "# SOP — Sales Discount Requests",
            "",
            "## Procedure",
            "",
            *[f"{i}. {s}" for i, s in enumerate(steps, 1)],
            "",
            "## Principles",
            "",
            *[f"- {p}" for p in truth.principles],
            "- A pricing exception is scoped to the product and dates it names.",
            "- If a request relies on a contract term that cannot be located, ask for the document "
            "before deciding.",
        ]
    )
    return Artifact(
        id="sales_discount_sop",
        path="documents/sales_discount_sop.md",
        source_system=DRIVE,
        description="Standard operating procedure for discount requests.",
        content=document(
            {
                "doc_id": "SOP-SALES-014",
                "title": "SOP — Sales Discount Requests",
                "owner": "Revenue Operations",
                "created": "2025-12-15",
                "version": "3.0",
            },
            body,
        ),
        supports=("sales_discount_sop",),
    )


def _account_strategy(truth: Truth, contacts: list[str]) -> Artifact:
    cust = truth.customer("CUST-1001")
    account = truth.account_for(cust.id)
    assert account is not None
    ae = truth.employee(account.owner)
    orders = sum(o.value_usd for o in truth.orders if o.customer == cust.id)
    revenue = usd(cust.annual_revenue_usd_approx or 0)
    body = f"""
# ACME Manufacturing — Account Strategy 2026

Author: {ae.name} · Last edited 2026-02-10

## Snapshot

- CRM account: {account.id} ({account.tier}, {cust.segment})
- ERP bill-to: {cust.erp_name} ({cust.source_ids["erp"]})
- HQ: {cust.address.city}, {cust.address.state} · ~{revenue} revenue
- Industry: {cust.industry}

## Relationship

Acme is one of our strategic accounts. They standardised on the NS-500 controller across two
plants in 2025 and are evaluating NS-Cloud for plant-floor analytics.

Key contacts: {contacts[0]} (VP Procurement), {contacts[1]} (Director of Plant Operations),
{contacts[2]} (IT Architecture).

## 2026 plan

- Third-plant NS-500 rollout (Q3). Expect 2–3 controller orders plus follow-on.
- Land NS-Cloud pilot on one line.
- Target FY26 bookings above {usd(orders)}.

## Commercial notes

Acme negotiated preferential NS-500 pricing in the 2025 agreement — I believe it's 15%, same as
what we approved for them last September. Worth confirming with Deal Desk before the Q3 order.
"""
    return Artifact(
        id="acme_account_strategy",
        path="documents/acme_account_strategy.md",
        source_system=DRIVE,
        description="Account plan for Acme written by the account owner.",
        content=document(
            {
                "doc_id": "ACCT-PLAN-CRM-2048-2026",
                "title": "ACME Manufacturing — Account Strategy 2026",
                "owner": ae.name,
                "created": "2026-02-10",
            },
            body,
        ),
        supports=("acme_account_strategy",),
        asserts=("F02", "F17"),
        mentions=("EXC-ACME-NS500-15", "MSA-ACME-2025", "DR-8104"),
    )


def _service_ticket(truth: Truth, fake: Faker) -> Artifact:
    cust = truth.customer("CUST-1044")
    edge = truth.product("PROD-003")
    contact = fake.name()
    body = f"""
# Service Request SR-40418

| Field | Value |
|---|---|
| Account | {cust.aliases[0]} ({cust.source_ids["crm"]}) |
| Site | {cust.address.city}, {cust.address.state} |
| Product | {edge.name} ({edge.sku}) |
| Opened | 2026-09-14 |
| Priority | P3 |
| Contact | {contact} |

Customer reports intermittent sensor dropouts on two gateways after a firmware update. Remote
diagnostics scheduled. No change to commercial terms requested.
"""
    return Artifact(
        id="service_ticket_acme_industrial",
        path="documents/service_ticket_acme_industrial.md",
        source_system="Northstar Service",
        description="Service ticket for a similarly named but different customer.",
        content=document(
            {
                "doc_id": "SR-40418",
                "title": f"Service Request SR-40418 — {cust.aliases[0]}",
                "owner": "Customer Support",
                "created": "2026-09-14",
            },
            body,
        ),
        supports=("CRM-2091",),
    )


def _days(n: int) -> timedelta:
    return timedelta(days=n)
