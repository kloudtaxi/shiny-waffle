"""Background ERP sales orders."""

from __future__ import annotations

from datetime import date
from typing import Literal

from polyfactory import Use
from pydantic import BaseModel, Field

from northstar.factories._base import SeededFactory

OrderStatus = Literal["Completed", "Invoiced", "Open", "Cancelled"]


class BgOrder(BaseModel):
    id: str
    erp_customer_id: str
    order_date: date
    order_value_usd: int = Field(ge=15_000, le=900_000)  # see product.py on multiple_of
    status: OrderStatus


class OrderFactory(SeededFactory[BgOrder]):
    order_date = Use(lambda: OrderFactory.date_in_window())
