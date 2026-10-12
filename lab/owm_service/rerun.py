"""Version n+1 of a re-run decision (spec §6.4, contract §6.1): its conditions, its level and floor,
and the one line that says what changed.

A resolution or a `/rerun` re-reads the row as it is now, keeps `as_of`, and runs the kernel with
the decision's id as its `sid` (`decisions.py` does those, outside the write lock). This module
takes the kernel's result from there:

1. the conditions carry forward (`conditions.carry_forward`): the resolution being made is applied
   to the condition it resolves, so it is carried as resolved, with `rerun_version` n+1;
2. the level, the floor, the ratchet and the self-sourced flags come from `ratchet.assess`, under
   the decision's real id (the wording of a floor this decision set is the bare `version N`). The
   floor counts the resolution being made: its `condition.resolved` event is passed as pending,
   and the write appends it with the version, in one transaction;
3. the open ratchet conditions are kept with their ids while the version is still below the
   floor at the same level, for the same confirmers (`conditions.carry_ratchet`). After one of a
   round's confirmations (R61, R63), the line says who it still needs;
4. `previous.what_changed`: the cause (who confirmed what, what the record now says and who
   changed it, or who asked for the re-run), then where the version stands.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from . import _lab, ratchet
from .conditions import (
    SYSTEM,
    carry_forward,
    carry_ratchet,
    in_order,
    input_conflicts,
    next_number,
    same,
    show,
    what_changed,
)
from .events import Event
from .models import Condition, ConditionResolved, DecisionRecord, PersonRef
from .org import Org
from .prepare import TABLE, Prepared, editor
from .state import subject_id


@dataclass(frozen=True)
class Resolving:
    """The resolution a `resolve` makes: the condition as version n holds it, and its `resolved`."""

    condition: Condition
    resolved: ConditionResolved


@dataclass(frozen=True)
class Next:
    conditions: list[Condition]
    assessment: ratchet.Assessment
    what_changed: str


def resolution_payload(decision_id: str, r: Resolving) -> dict[str, Any]:
    """The `condition.resolved` payload (`state.py`)."""
    return {"decision_id": decision_id, "condition_id": r.condition.id,
            "resolved": r.resolved.model_dump(mode="json")}  # fmt: skip


def next_version(
    org: Org, rec: DecisionRecord, versions: Sequence[Mapping[str, Any]],
    levels: Mapping[int, Any], prep: Prepared, kr: _lab.KernelResult,
    submitted: Mapping[str, Any] | None, by: PersonRef, resolving: Resolving | None, at: datetime,
) -> Next:  # fmt: skip
    """Version `rec.version + 1`'s conditions, assessment and `what_changed`. `rec` is the current
    version with its derived fields, `versions` every stored version of the decision (for the
    next free condition id), `levels` each version's stored level by number, `by` who caused the
    re-run, `at` when."""
    kind, did, n = rec.decision_type, rec.decision_id, rec.version
    sid = subject_id(rec.subject.model_dump())
    previous = [
        c.model_copy(update={"resolved": resolving.resolved})
        if resolving is not None and c.id == resolving.condition.id else c
        for c in rec.conditions
    ]  # fmt: skip
    carried: list[Condition] = []
    next_n = next_number(versions)
    if kind != "sla":
        assert prep.requester is not None
        found = [] if prep.row is None else input_conflicts(kind, submitted, prep.figures)
        missing = dict(submitted or {}) if prep.row is None else None
        carried, next_n = carry_forward(kind, sid, previous, found, missing, prep.requester, n + 1,
                                        next_n)  # fmt: skip
    pending = [] if resolving is None else [Event(
        seq=0, at=at, wall=at, org=org.org_id, stream=sid, kind="condition.resolved",
        actor=None, payload=resolution_payload(did, resolving))]  # fmt: skip
    rk = ratchet.assess(
        org, kind=kind, subject=sid, table=TABLE[kind], decision_id=did, version=n + 1,
        requester=prep.requester, figures=prep.figures, row=prep.inputs.get("record") or {},
        authority=kr.record.get("authority"), as_of=date.fromisoformat(rec.as_of),
        requested_at=datetime.fromisoformat(rec.requested_at), next_n=next_n, pending=pending,
    )  # fmt: skip

    def same_level(c: Condition) -> bool:
        return ratchet.Level.of(levels.get(c.opened_in_version)) == rk.level

    ratchets = carry_ratchet(previous, rk.conditions, same_level)
    conditions = in_order([*carried, *ratchets])
    confirming = resolving is not None and resolving.condition.source == "ratchet"
    kept = {c.id for c in previous}
    line = what_changed(
        _cause(org, rec, prep, by, resolving),
        below=bool(ratchets),
        was_below=any(c.source == "ratchet" and c.resolved is None for c in rec.conditions),
        open_ids=[c.id for c in conditions if c.blocking and c.resolved is None],
        awaiting=[p.name for c in ratchets if confirming and c.id in kept for p in c.who],
    )  # fmt: skip
    return Next(conditions, rk, line)


def _cause(
    org: Org, rec: DecisionRecord, prep: Prepared, by: PersonRef, resolving: Resolving | None
) -> str:
    """What caused the re-run, in a few words."""
    if resolving is None:
        return f"{by.name} asked for a re-run"
    c, resolution = resolving.condition, resolving.resolved.resolution
    if resolution == "confirmed_lower_level":
        return f"{by.name} confirmed the lower approval level"
    kind, sid = rec.decision_type, subject_id(rec.subject.model_dump())
    system = SYSTEM[kind]
    if c.source == "missing_record":
        return f"{system} now holds {sid}" if prep.row else f"{system} still has no record of {sid}"
    field = str(c.field)
    if resolution == "confirmed_record":
        return f"{by.name} confirmed {system}'s {show(field, c.on_record)}"
    now = prep.figures.get(field)
    if now is None or same(field, now, c.on_record):
        return (f"{by.name} said {system} was corrected, but it still says "
                f"{show(field, c.on_record)}")  # fmt: skip
    who = _changed_by(org, rec, prep, field)
    return f"{system} now says {show(field, now)}" + (f", changed by {who}" if who else "")


def _changed_by(org: Org, rec: DecisionRecord, prep: Prepared, field: str) -> str | None:
    """Who last edited the column behind a §3.5 figure: `the requester` (or their agent), or a
    name; None when the record shows no edit."""
    columns = {col for col in prep.row or {} if ratchet.CONTRACT_FIELD.get(col, col) == field}
    sid = subject_id(rec.subject.model_dump())
    edits = [e for e in org.sor.edits(TABLE[rec.decision_type], sid)
             if e.payload["field"] in columns]  # fmt: skip
    who = editor(org, edits[-1].actor) if edits else None
    if who is None:
        return None
    return "the requester" if prep.requester and who.id == prep.requester.id else who.name
