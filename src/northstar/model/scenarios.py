"""Scenarios: the decisions the dataset exists to make answerable (doc 02 §1)."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

Outcome = Literal[
    "APPROVE",
    "APPROVE_WITH_AUTHORIZATION",
    "REJECT_OR_ESCALATE",
    "REVIEW_REQUIRED",
    "REQUEST_EVIDENCE",
]


class Probe(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    as_of: date
    expected_exception: str | None
    expected_maximum: float | None


class Scenario(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    slug: str
    title: str
    kind: Literal["discount_decision", "fact_selection", "provenance", "identity"]
    question: str
    teaches: list[str]
    corpus: str
    as_of: date | None = None
    request: dict[str, Any] | None = None
    subject: dict[str, str] | None = None
    probes: list[Probe] = []
    expected: dict[str, Any]
    reasoning: list[str] = []
