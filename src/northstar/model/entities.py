"""Canonical entity types of the Northstar organization.

These mirror the conceptual OWM domain model in ``owm/owm-spec.md``. They are
deliberately plain: the point of the lab is to *discover* the model, so nothing
here is frozen.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Temporal(_Frozen):
    """Anything with a closed validity interval [valid_from, valid_to]."""

    valid_from: date
    valid_to: date

    def active_on(self, when: date) -> bool:
        return self.valid_from <= when <= self.valid_to


class System(_Frozen):
    id: str
    name: str


class Role(_Frozen):
    id: str
    title: str
    department: str
    lab_extension: bool = False


class Organization(_Frozen):
    id: str
    name: str
    industry: str
    headquarters: str
    employees_approx: int
    annual_revenue_usd_approx: int
    operating_model: str
    email_domain: str
    systems: list[System]
    departments: list[str]
    roles: list[Role]


class Address(_Frozen):
    street: str
    city: str
    state: str
    postal_code: str


class Customer(_Frozen):
    id: str
    canonical_name: str
    customer_type: str
    industry: str
    strategic: bool
    segment: str
    aliases: list[str]
    source_ids: dict[str, str]
    erp_name: str
    address: Address
    duns: str
    annual_revenue_usd_approx: int | None = None
    credit_limit_usd: int | None = None  # current limit in the ERP credit master (experiment 5)
    lab_extension: bool = False


class Account(_Frozen):
    id: str
    customer: str
    owner: str
    name: str
    tier: str


class Employee(_Frozen):
    id: str
    name: str
    role: str
    department: str
    manager: str | None
    aliases: list[str] = []
    preferred_name: str | None = None
    responsibility: str | None = None
    note: str | None = None
    lab_extension: bool = False

    @property
    def first_name(self) -> str:
        return self.name.split()[0]

    def email(self, domain: str) -> str:
        return f"{self.name.lower().replace(' ', '.')}@{domain}"


class Product(_Frozen):
    id: str
    sku: str
    name: str
    category: str
    list_price_usd: int


class Contract(Temporal):
    id: str
    title: str
    aliases: list[str]
    customer: str
    covers: list[str]
    grants_approval_authority: bool
    lab_extension: bool = False


class PricingException(Temporal):
    id: str
    title: str
    customer: str
    contract: str
    product: str
    maximum_discount: float
    supersedes: str | None
    grants_approval_authority: bool


class Order(_Frozen):
    id: str
    customer: str
    date: date
    value_usd: int
    status: str


class DiscountRequest(_Frozen):
    id: str
    customer: str
    product: str
    requested_discount: float
    requestor: str
    request_date: date
    list_value_usd: int
    basis: Literal["contract_exception", "standard"]
    basis_ref: str | None
    status: str
    approved_by: str | None
    lab_extension: bool = False

    @property
    def discount_value_usd(self) -> int:
        return round(self.list_value_usd * self.requested_discount)

    @property
    def net_value_usd(self) -> int:
        return self.list_value_usd - self.discount_value_usd


class Band(_Frozen):
    """An authority band: (min_exclusive, max_inclusive]; ``None`` means open-ended."""

    role: str
    min_exclusive: float | None
    max_inclusive: float | None

    def contains(self, discount: float) -> bool:
        above = self.min_exclusive is None or discount > self.min_exclusive
        below = self.max_inclusive is None or discount <= self.max_inclusive
        return above and below


class Policy(Temporal):
    id: str
    title: str
    authority_matrix_document: str | None
    approval_evidence_required_above: float | None
    bands: list[Band]
    rules: list[str]

    def band_for(self, discount: float) -> Band:
        for band in self.bands:
            if band.contains(discount):
                return band
        raise ValueError(f"{self.id}: no authority band covers {discount}")

    def limit_for(self, role: str) -> float | None:
        """Largest discount a role may approve alone; ``None`` if the role has no band."""
        for band in self.bands:
            if band.role == role:
                return band.max_inclusive if band.max_inclusive is not None else 1.0
        return None


class Relationship(_Frozen):
    subject: str
    predicate: str
    object: str
    valid_from: date | None = None
    valid_to: date | None = None


class Fact(_Frozen):
    id: str
    kind: Literal["asserted", "derived"]
    owm_needed: bool
    statement: str


# -- Credit (experiment 5, lab extension): a second decision type ---------------------------


class Guarantee(Temporal):
    """A third party guarantees a customer's obligations up to an amount."""

    id: str
    title: str
    guarantor: str
    customer: str
    amount_usd: int
    lab_extension: bool = True


class Invoice(_Frozen):
    id: str
    customer: str
    invoice_date: date
    due_date: date
    amount_usd: int
    paid_date: date | None
    reference: str

    def days_late(self, as_of: date) -> int:
        """Days past due as known on ``as_of``: a payment made after ``as_of`` is not yet known."""
        if self.paid_date is not None and self.paid_date <= as_of:
            return max(0, (self.paid_date - self.due_date).days)
        return max(0, (as_of - self.due_date).days)


class CreditRequest(_Frozen):
    id: str
    customer: str
    current_limit_usd: int
    requested_limit_usd: int
    requestor: str
    request_date: date
    basis: Literal["guarantee", "standard"]
    basis_ref: str | None
    justification: str
    status: str
    lab_extension: bool = True


class Concurrence(_Frozen):
    """A second sign-off, from another function, above an amount for some account tiers."""

    role: str
    min_exclusive: float
    tiers: list[str]


class CreditPolicy(Temporal):
    id: str
    title: str
    bands: list[Band]
    concurrence: list[Concurrence]
    max_days_late: int
    lookback_days: int
    caps: dict[str, int]  # account tier → maximum credit limit
    separation_of_duties: bool
    rules: list[str]
    lab_extension: bool = True

    def band_for(self, amount: float) -> Band:
        for band in self.bands:
            if band.contains(amount):
                return band
        raise ValueError(f"{self.id}: no authority band covers {amount}")

    def limit_for(self, role: str) -> float | None:
        for band in self.bands:
            if band.role == role:
                return band.max_inclusive if band.max_inclusive is not None else float("inf")
        return None


# -- SLA breach response (experiment 6, lab extension): a non-approval decision -------------
# The rules were written by a subagent that never saw the engine
# (runs/2026-10-03-exp6-sla/rules/rule-sheet.md); these types hold them.

Impact = Literal[
    "production_stopped",  # R14(a), Severity 1 without a workaround
    "all_users_down",  # R14(b), NS-Cloud unavailable to all users, Severity 1 without a workaround
    "degraded",  # R15(a)
    "monitoring_unavailable",  # R15(b)
    "some_users_down",  # R15(c)
    "impaired",  # R16
    "question",  # R17
]


class SupportFee(_Frozen):
    from_month: str  # "YYYY-MM"; applies until the next entry
    monthly_usd: int


class SupportAgreement(_Frozen):
    id: str
    customer: str
    document: str  # the evidence artifact that carries it
    reference: str
    plan: Literal["Platinum", "Silver"]
    products: list[str]
    coverage_start: date  # 00:00 CT
    fees: list[SupportFee]

    def fee_for(self, month: str) -> int:
        return [f.monthly_usd for f in self.fees if f.from_month <= month][-1]


class Target(_Frozen):
    severity: int
    plan: str | None  # None: any plan
    response_minutes: int
    restoration_minutes: int | None
    clock: Literal["24x7", "business"]


class CreditRate(_Frozen):
    severity: int
    target: Literal["response", "restoration"]
    band: int | None  # v2.0 restoration bands; None otherwise
    pct: float


class SlaSchedule(Temporal):
    id: str
    version: str
    title: str
    published: date
    targets: list[Target]
    notice_business_days: int
    credits: list[CreditRate]
    cap_pct: float
    claim_days: int

    def target_for(self, severity: int, plan: str) -> Target:
        return next(t for t in self.targets if t.severity == severity and t.plan in (None, plan))

    def rate(self, severity: int, target: str, band: int | None) -> float:
        return next(
            c.pct for c in self.credits
            if c.severity == severity and c.target == target and c.band == band
        )  # fmt: skip


class MaintenanceNotice(_Frozen):
    id: str
    customer: str
    products: list[str]
    sent: datetime
    window_start: datetime
    window_end: datetime


class Pause(_Frozen):
    start: datetime | None
    end: datetime | None
    note: str


class Note(_Frozen):
    at: datetime
    actor: str
    text: str


class RootCause(_Frozen):
    at: datetime
    attributes_to: Literal["customer", "other"]
    text: str


class Claim(_Frozen):
    received: datetime
    channel: Literal["email", "portal"]
    sender: str
    text: str


class Ticket(_Frozen):
    id: str
    account: str  # the CRM account id on the ticket
    label: str  # the customer as named on the ticket
    site: str
    product: str
    channel: Literal["phone", "portal", "email"]
    caller: str
    opened: datetime
    reported_priority: str
    description: str
    impact: Impact  # the truth's reading of the description (R13–R17)
    workaround: bool
    auto_ack: datetime | None = None
    first_response: datetime | None
    first_response_note: str
    pauses: list[Pause] = []
    restored: datetime | None
    restored_note: str = ""
    notes: list[Note] = []
    exclusion_asserted: datetime | None = None
    root_cause: RootCause | None = None
    claim: Claim | None = None


class ServiceCredit(_Frozen):
    id: str
    ticket: str
    customer: str
    ticket_opened: date
    amount_usd: float
    approved_on: date


class Holiday(_Frozen):
    date: date
    name: str
