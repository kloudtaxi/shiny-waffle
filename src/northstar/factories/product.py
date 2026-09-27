"""Background products (the rest of the catalogue around NS-500 / NS-Cloud / NS-Edge)."""

from __future__ import annotations

from typing import Literal

from polyfactory import Use
from pydantic import BaseModel, Field

from northstar.factories._base import SeededFactory

Category = Literal["Equipment", "Software", "Service"]
NOUNS: dict[str, tuple[str, ...]] = {
    "Equipment": ("Motion Controller", "Drive Unit", "Sensor Array", "I/O Module", "Gateway"),
    "Software": ("Analytics Add-on", "Historian", "Fleet Manager", "Safety Module"),
    "Service": ("Commissioning Service", "Premium Support Plan", "Training Package"),
}


class BgProduct(BaseModel):
    id: str
    sku: str
    name: str
    category: Category
    # Constraint-aware generation is what Polyfactory is for. No `multiple_of`: with
    # it, polyfactory 3.3 returned the lower bound every time (observed, n=1 version);
    # the builder rounds instead.
    list_price_usd: int = Field(ge=5_000, le=400_000)


class ProductFactory(SeededFactory[BgProduct]):
    sku = Use(lambda: "")
    name = Use(lambda: "")
