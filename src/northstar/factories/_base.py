"""Shared plumbing for the seeded factories."""

from __future__ import annotations

from datetime import date
from typing import Any, Generic, TypeVar

from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)

# Names the background must never produce: they belong to the truth, and a
# collision would silently change what the corpus means.
RESERVED_TOKENS = ("acme", "blueriver", "blue river", "cedar", "northstar")

# All generated dates stay inside the lab window. Polyfactory's own date
# generation is relative to *today*, which would break reproducibility.
WINDOW_START = date(2025, 1, 2)
WINDOW_END = date(2026, 9, 20)


class SeededFactory(ModelFactory[M], Generic[M]):
    """A ModelFactory with its own Faker so seeding one factory never reseeds another."""

    __is_base_factory__ = True
    __faker__ = Faker("en_US")

    @classmethod
    def reseed(cls, seed: int) -> None:
        cls.__faker__ = Faker("en_US")
        cls.seed_random(seed)

    @classmethod
    def fake(cls) -> Any:
        return cls.__faker__

    @classmethod
    def date_in_window(cls, start: date = WINDOW_START, end: date = WINDOW_END) -> date:
        d: date = cls.__faker__.date_between_dates(date_start=start, date_end=end)
        return d


def is_reserved(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in RESERVED_TOKENS)
