"""Canonical entity types of the Northstar organization.

These mirror the conceptual OWM domain model in ``owm/owm-spec.md``. They are
deliberately plain: the point of the lab is to *discover* the model, so nothing
here is frozen.
"""

from __future__ import annotations

from datetime import date
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
