"""Background CRM discount requests. Approvers are assigned by policy, never at random."""

from __future__ import annotations

from datetime import date
from typing import Literal

from polyfactory import Use
from pydantic import BaseModel

from northstar.factories._base import SeededFactory

DiscountPct = Literal[5, 8, 10, 12, 15, 18, 22]


class BgDiscountRequest(BaseModel):
    id: str
    customer: str
    product: str
    requested_pct: DiscountPct
    request_date: date
    requestor: str
    approved_by: str
    status: str = "Approved"

    @property
    def requested_discount(self) -> float:
        return self.requested_pct / 100


class DiscountRequestFactory(SeededFactory[BgDiscountRequest]):
    request_date = Use(lambda: DiscountRequestFactory.date_in_window())
    status = "Approved"
