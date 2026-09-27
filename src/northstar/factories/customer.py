"""Background customers (ERP master + CRM account in one object)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from polyfactory import Use
from pydantic import BaseModel

from northstar.factories._base import SeededFactory

Industry = Literal[
    "Automotive Components",
    "Food & Beverage",
    "Chemicals",
    "Energy & Utilities",
    "Aerospace",
    "Packaging",
    "Pharmaceuticals",
    "Building Materials",
]
Segment = Literal["Central Enterprise", "Midwest Mid-Market", "East Enterprise", "West Mid-Market"]
PaymentTerms = Literal["Net 30", "Net 45", "Net 60"]


class BgCustomer(BaseModel):
    id: str
    name: str
    erp_name: str
    industry: Industry
    segment: Segment
    street: str
    city: str
    state: str
    postal_code: str
    duns: str
    payment_terms: PaymentTerms
    created_on: date
    crm_id: str
    erp_id: str
    owner: str
    strategic: bool = False


class CustomerFactory(SeededFactory[BgCustomer]):
    name = Use(lambda: CustomerFactory.fake().company())
    street = Use(lambda: CustomerFactory.fake().street_address())
    # Faker invents city names and pairs them with any state; the builder
    # substitutes a real city and a postal code valid for its state.
    city = Use(lambda: "")
    state = Use(lambda: "")
    postal_code = Use(lambda: "")
    duns = Use(lambda: CustomerFactory.fake().numerify("##-###-####"))
    created_on = Use(lambda: CustomerFactory.date_in_window(date(2018, 1, 1), date(2024, 12, 31)))
    strategic = False
    # ERP legal names drift from CRM display names — that drift is the point.
    erp_name = Use(lambda: "")


LEGAL_SUFFIXES = ("Inc.", "LLC", "Holdings", "Corp.", "Co.")
CITIES = (
    ("Chicago", "IL"),
    ("Rockford", "IL"),
    ("Peoria", "IL"),
    ("Detroit", "MI"),
    ("Grand Rapids", "MI"),
    ("Columbus", "OH"),
    ("Cleveland", "OH"),
    ("Toledo", "OH"),
    ("Madison", "WI"),
    ("Green Bay", "WI"),
    ("Minneapolis", "MN"),
    ("Des Moines", "IA"),
    ("Kansas City", "MO"),
    ("Louisville", "KY"),
    ("Fort Wayne", "IN"),
    ("Pittsburgh", "PA"),
)
