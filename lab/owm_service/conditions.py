"""Conditions a version opens (spec §6.2): an input conflict for each submitted figure the system
of record contradicts, a missing record when the system of record has no row, and the ratchet when
the version is below its subject's floor (spec §6.5; `ratchet.py` decides when, and who confirms).
SLA decisions open none.

Figures compare by the contract's §3.5 names, in the contract's units: numbers within 1e-9,
anything else exactly. The decision always stands on the record (contract ground rule 5).

A re-run (spec §6.4) carries its version's conditions forward (`carry_forward`, `carry_ratchet`):
- a resolved condition is history: it is copied with its `resolved`, whatever its source;
- a resolved input conflict stays resolved while the row still holds the figure that was confirmed
  (`confirmed_record`); when the row holds another figure, a new condition opens with the next id.
  A `corrected_record` covers nothing later: a correction that still differs from `submitted`
  opens a new condition;
- an open condition the re-run finds again (the same figures; still no record; still below the
  floor at the same level, for the same confirmers) keeps its id. One it doesn't find is gone;
- ids are `c1`, `c2`… and never reused within a decision, across versions (`next_number`).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
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


def same(field: str, submitted: Any, on_record: Any) -> bool:
    """One figure, two values: equal in the contract's units (numbers within 1e-9)."""
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
        and not same(f, submitted[f], on_record[f])
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


def ratchet_condition(
    cid: str, needed: str, stands: str, version: int, confirmer: PersonRef
) -> Condition:
    """Below the subject's floor (G-46): one confirmer's condition (`ratchet.confirmers`: the
    floor's band holder, or the holder of a concurrence the version drops, R26). Each confirms
    the lower level, or it stays not ready. `needed` and `stands` are `ratchet.phrases`'s: what
    the floor needed (`version 1 needed the VP Sales`, or `DEC-0001 version 1 needed …` for
    another decision's floor, R24) and where this version stands (`version 2 is within Sarah
    Chen's own authority`, `… is at the <title>`, `… drops the <title> concurrence`)."""
    return Condition.model_validate({
        "id": cid,
        "source": "ratchet",
        "what": f"Confirm the lower approval level: {needed}; {stands}.",
        "who": [confirmer.model_dump()],
        "blocking": True,
        "field": None,
        "submitted": None,
        "on_record": None,
        "opened_in_version": version,
        "resolved": None,
    })  # fmt: skip


# -- re-runs (spec §6.4) --------------------------------------------------------------------------
def number(cid: str) -> int:
    """A condition id's number: `c12` is 12."""
    return int(cid[1:])


def next_number(versions: Iterable[Mapping[str, Any]]) -> int:
    """The next free condition number in a decision: one past every id any version has used."""
    return 1 + max((number(str(c["id"])) for v in versions for c in v["conditions"]), default=0)


def _confirms(c: Condition, field: str, on_record: Any) -> bool:
    """A confirmed figure the row still holds."""
    return (c.source == "input_conflict" and c.field == field and c.resolved is not None
            and c.resolved.resolution == "confirmed_record"
            and same(field, c.on_record, on_record))  # fmt: skip


def carry_forward(
    kind: str, subject_id: str, previous: Sequence[Condition],
    found: Sequence[tuple[str, Any, Any]], missing: Mapping[str, Any] | None,
    requester: PersonRef, version: int, next_n: int,
) -> tuple[list[Condition], int]:  # fmt: skip
    """The input-conflict and missing-record conditions of version `version`, and the next free
    number. `previous` are the last version's conditions with their resolutions (the one being
    resolved included), `found` the conflicts the re-run finds (`input_conflicts`), `missing` the
    submitted figures when the system of record still has no row (else None). Resolved conditions
    of every source are kept as history; the ratchet's open one is `carry_ratchet`'s."""
    out = [c for c in previous if c.resolved is not None]
    for field, submitted, on_record in found:
        if any(_confirms(c, field, on_record) for c in previous):
            continue
        kept = next((c for c in previous if c.source == "input_conflict" and c.resolved is None
                     and c.field == field and same(field, c.submitted, submitted)
                     and same(field, c.on_record, on_record)), None)  # fmt: skip
        if kept is None:
            kept = conflict_condition(f"c{next_n}", kind, subject_id, field, submitted, on_record,
                                      requester, version)  # fmt: skip
            next_n += 1
        out.append(kept)
    if missing is not None:
        kept = next((c for c in previous
                     if c.source == "missing_record" and c.resolved is None), None)  # fmt: skip
        if kept is None:
            kept = missing_record_condition(f"c{next_n}", kind, subject_id, missing, requester,
                                            version)  # fmt: skip
            next_n += 1
        out.append(kept)
    return out, next_n


def _confirmer_ids(conditions: Iterable[Condition]) -> list[str]:
    return sorted(p.id for c in conditions for p in c.who)


def carry_ratchet(
    previous: Sequence[Condition], fresh: Sequence[Condition],
    same_level: Callable[[Condition], bool],
) -> list[Condition]:  # fmt: skip
    """The version's open ratchet conditions. A round is the ratchet conditions one version
    opened, one per confirmer (R26). The last version's round is kept while one of its conditions
    is open and the re-run is still below the floor (`fresh`, from `ratchet.assess`) at the level
    of the version that opened it (`same_level`), for the same confirmers: its open conditions
    keep their ids, and its confirmed ones are already history (`carry_forward`), so nobody
    confirms twice. Otherwise `fresh`, a new round."""
    held = [c for c in previous if c.source == "ratchet" and c.resolved is None]
    if not fresh or not held or not same_level(held[0]):
        return list(fresh)
    opened = held[0].opened_in_version
    round_ = [c for c in previous if c.source == "ratchet" and c.opened_in_version == opened]
    return held if _confirmer_ids(round_) == _confirmer_ids(fresh) else list(fresh)


def in_order(conditions: Iterable[Condition]) -> list[Condition]:
    """By id number: history first, then what each version opened, in the order it opened them."""
    return sorted(conditions, key=lambda c: number(c.id))


def _names(ids: Sequence[str]) -> str:
    return ids[0] if len(ids) == 1 else ", ".join(ids[:-1]) + " and " + ids[-1]


def what_changed(
    cause: str, *, below: bool, was_below: bool, open_ids: Sequence[str],
    awaiting: Sequence[str] = (),
) -> str:  # fmt: skip
    """`previous.what_changed`, one line: what caused the re-run, then where it leaves the version
    (a round of confirmations still `awaiting` those people; below the floor; the blocking
    conditions still open; or none)."""
    if below and awaiting:
        then = f"the lower level still needs {_names(awaiting)} to confirm it"
    elif below:
        then = f"the level {'is still' if was_below else 'fell'} below the floor"
    elif open_ids:
        then = f"{_names(open_ids)} {'is' if len(open_ids) == 1 else 'are'} open"
    else:
        then = "no conditions remain"
    return f"{cause[:1].upper()}{cause[1:]}; {then}."
