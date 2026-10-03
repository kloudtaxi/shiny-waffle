"""Background credit data (experiment 5): invoices, current limits and credit requests.

Noise around the credit truth, under the same rules as the rest of the background:
- it is seeded, with its own factories;
- it is generated after every other factory, so the existing random streams don't move;
- it never contradicts the truth.

Invoices of truth customers are never paid late, so their credit history is decided by the truth's
invoices alone. Every background credit request is decided by the credit policy in force on its
date.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from polyfactory import Use
from pydantic import BaseModel

from northstar.factories._base import WINDOW_END, SeededFactory

StepUsd = Literal[25000, 50000, 75000, 100000]
TERMS_DAYS = {"Net 30": 30, "Net 45": 45, "Net 60": 60}


class BgInvoice(BaseModel):
    id: str
    erp_customer_id: str
    invoice_date: date
    due_date: date
    amount_usd: int
    paid_date: date | None
    reference: str


class InvoiceFactory(SeededFactory[BgInvoice]):
    """Only its random stream is used: payment delays."""


class BgCreditRequest(BaseModel):
    id: str
    customer: str  # a background CUST id
    current_limit_usd: int  # set in date order: each approval raises the next request's base
    step_usd: StepUsd
    request_date: date
    requestor: str
    approved_by: str
    status: str

    @property
    def requested_limit_usd(self) -> int:
        return self.current_limit_usd + self.step_usd


class CreditRequestFactory(SeededFactory[BgCreditRequest]):
    request_date = Use(lambda: CreditRequestFactory.date_in_window())
    status = ""


def invoice_for(
    order_id: str, erp_id: str, order_date: date, value: int, terms: str, delay: int
) -> BgInvoice:
    """An order's invoice, paid ``delay`` days after its due date (unknown if after the window)."""
    due = order_date + timedelta(days=TERMS_DAYS[terms])
    paid = due + timedelta(days=delay)
    return BgInvoice(
        id="",
        erp_customer_id=erp_id,
        invoice_date=order_date,
        due_date=due,
        amount_usd=value,
        paid_date=paid if paid <= WINDOW_END else None,
        reference=order_id,
    )
