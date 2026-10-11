"""Conditions a version opens when it is asked for (spec §6.2): an input conflict for each
submitted figure the system of record contradicts, and a missing record when the system of record
has no row. SLA decisions open none. (The ratchet's condition comes with the floor.)

Figures compare by the contract's §3.5 names, in the contract's units: numbers within 1e-9,
anything else exactly. The decision always stands on the record (contract ground rule 5).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, Final

from .models import Condition, PersonRef

# §3.5, in the contract's order: conflicts and their condition ids follow it
FIELDS: Final = ("requested_discount", "requested_limit_usd", "current_limit_usd", "request_date",
                 "status", "customer", "product", "requestor")  # fmt: skip
NUMBERS: Final = frozenset({"requested_discount", "requested_limit_usd", "current_limit_usd"})
FRACTIONS: Final = frozenset({"requested_discount"})
USD: Final = frozenset({"requested_limit_usd", "current_limit_usd"})
LABELS: Final[Mapping[str, str]] = {
    "requested_discount": "the discount",
    "requested_limit_usd": "the requested limit",
    "current_limit_usd": "the current limit",
    "request_date": "the request date",
    "status": "the status",
    "customer": "the customer",
    "product": "the product",
    "requestor": "the requester",
}
SYSTEM: Final[Mapping[str, str]] = {"discount": "the CRM", "credit": "the ERP"}
TOLERANCE: Final = 1e-9


def _number(x: Any) -> float | None:
    if isinstance(x, bool):
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _same(field: str, submitted: Any, on_record: Any) -> bool:
    if field in NUMBERS:
        a, b = _number(submitted), _number(on_record)
        return a is not None and b is not None and abs(a - b) <= TOLERANCE
    return str(submitted) == str(on_record)


def input_conflicts(
    kind: str, submitted: Mapping[str, Any] | None, on_record: Mapping[str, Any]
) -> list[tuple[str, Any, Any]]:
    """(field, submitted, on record) for each submitted figure the record contradicts, in §3.5
    order. A field the record doesn't carry, or a null submission, is not compared."""
    if kind == "sla" or not submitted:
        return []
    return [
        (f, submitted[f], on_record[f])
        for f in FIELDS
        if submitted.get(f) is not None and f in on_record
        and not _same(f, submitted[f], on_record[f])
    ]  # fmt: skip


def show(field: str, value: Any) -> str:
    """A figure as the condition states it: a fraction as 8%, USD as $300,000, else as is."""
    n = _number(value)
    if field in FRACTIONS and n is not None:
        return f"{round(n * 100, 9):g}%"
    if field in USD and n is not None:
        return f"${n:,.0f}"
    return str(value)


def conflict_condition(
    cid: str, kind: str, subject_id: str, field: str, submitted: Any, on_record: Any,
    requester: PersonRef, version: int,
) -> Condition:  # fmt: skip
    """An input conflict: the requester confirms the record's figure, or corrects the record."""
    system, s, r = SYSTEM[kind], show(field, submitted), show(field, on_record)
    return Condition.model_validate({
        "id": cid,
        "source": "input_conflict",
        "what": f"Confirm {LABELS[field]} on {subject_id}: submitted {s}, {system} says {r}. "
                f"The decision is on {system}'s {r}.",
        "who": [requester.model_dump()],
        "blocking": True,
        "field": field,
        "submitted": submitted,
        "on_record": on_record,
        "opened_in_version": version,
        "resolved": None,
    })  # fmt: skip


def missing_record_condition(
    cid: str, kind: str, subject_id: str, submitted: Mapping[str, Any], requester: PersonRef,
    version: int,
) -> Condition:  # fmt: skip
    """The system of record has no row for the subject: the decision stands on the submitted
    figures until the requester adds the record or confirms them."""
    system = SYSTEM[kind]
    return Condition.model_validate({
        "id": cid,
        "source": "missing_record",
        "what": f"Confirm {subject_id}: {system} has no record of it. The decision is on the "
                f"submitted figures until {system} holds it.",
        "who": [requester.model_dump()],
        "blocking": True,
        "field": None,
        "submitted": dict(submitted),
        "on_record": None,
        "opened_in_version": version,
        "resolved": None,
    })  # fmt: skip
