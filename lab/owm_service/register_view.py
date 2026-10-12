"""The register's read side and its settings (B-06 Task 17; spec §7.2; contract §4.1, §4.4).

`view` shows the register as of a date: the registrar's entries (the bootstrap plus every approved
change, `Org.register_state`), the mandate fixture beside them, their series and the coverage. A
read decides nothing: each entry's `status` is computed for the read's `as_of`, using the kernel's
own rules through `_lab` (a revocation on or before the date, a live entry in force).

- `status`: `revoked` (RR-12, on or before `as_of`); `scheduled` (starts later); `superseded` (an
  entry that supersedes it is in force on `as_of`); `expired` (past `effective_to`); else
  `in_force`.
- `title`: the registrar keeps none, so it is the entry's own if present, else the first `# `
  heading of the approved text, else the doc_id.
- `file`: the copy on file in the corpus's `documents/`, fingerprinted as the register records a
  document. `sha256` is "" and `detail` "missing" when the corpus holds no such file (a document
  registered after the bootstrap); `differs` when its fingerprint isn't the registered one.
  `source_id` is the copy's corpus path (`documents/<file>`); the lab has no
  knowledge-foundation id.
- `series`: entries joined by `supersedes`, oldest first. A document nothing supersedes or
  follows isn't a series.
- `as_known_at` is reserved and not served."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any, Final, cast

from pydantic import TypeAdapter

from . import _lab
from .errors import NotFound, Refused
from .models import (
    ROUTE_TO,
    Actor,
    AgentActor,
    Coverage,
    CoverageDocument,
    CoverageProcedure,
    DecisionType,
    EntryStatus,
    FileCheck,
    FunctionParty,
    Party,
    PersonRef,
    Refusal,
    RegisterEntry,
    RegisterRelation,
    RegisterSeries,
    RegisterSettings,
    RegisterView,
    Revoked,
)
from .org import Org
from .sessions import Mandates

SETTINGS_STREAM: Final = "register:settings"
MODES: Final = ("use_registered", "route")
LABEL: Final = {"discount": "Discount approval", "credit": "Credit approval",
                "sla": "Service-level breach and credit"}  # fmt: skip
_PERSON = re.compile(r"^(?P<name>.+) \((?P<id>EMP-\d+), (?P<title>.+)\)$")
_FUNCTION = re.compile(r"^(?P<function>.+?) \((?P<note>by function.*)\)$")
_ACTOR: Final[TypeAdapter[Actor]] = TypeAdapter(Actor)


def _day(x: Any) -> date:
    return x if isinstance(x, date) else date.fromisoformat(str(x))


# -- one entry ----------------------------------------------------------------------------------
def _party(org: Org, label: str) -> Party:
    """The registrar's label for who acted: "Name (EMP-1, Title)", or "Function (by function:
    …)" where the HR export has nobody for the function."""
    if m := _PERSON.match(label):
        return org.people.ref(m["id"])
    if m := _FUNCTION.match(label):
        return FunctionParty(kind="function", function=m["function"], note=m["note"])
    return FunctionParty(kind="function", function=label, note="")


def _person(org: Org, label: str) -> PersonRef:
    m = _PERSON.match(label)
    if m is None:
        raise ValueError(f"not a person: {label!r}")
    return org.people.ref(m["id"])


def _superseders(e: Mapping[str, Any], entries: list[dict[str, Any]], on: date) -> list[str]:
    """The entries that supersede `e` and are in force on `on` (the kernel's rule)."""
    return [s["doc_id"] for s in entries
            if any(r["type"] == "supersedes" and r["target"] == e["doc_id"]
                   for r in s.get("relations") or [])
            and _lab.entry_in_force([s], on) is not None]  # fmt: skip


def _status(
    e: dict[str, Any], entries: list[dict[str, Any]], on: date
) -> tuple[EntryStatus, str | None]:
    if _lab.revoked_on_or_before(e, on):
        return "revoked", None
    if on < _day(e["effective_from"]):
        return "scheduled", None
    if by := _superseders(e, entries, on):
        return "superseded", by[0]
    if e.get("effective_to") and on > _day(e["effective_to"]):
        return "expired", None
    return "in_force", None


def _heading(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or None
    return None


def _title(e: Mapping[str, Any], body: str | None) -> str:
    return str(e.get("title") or (body and _heading(body)) or e["doc_id"])


def _file(e: Mapping[str, Any], prints: dict[str, str]) -> FileCheck:
    name = e.get("file")
    sha = prints.get(str(name)) if name else None
    if sha is None:
        return FileCheck(sha256="", matches=False, detail="missing", source_id=None)
    ok = sha == e["sha256"]
    return FileCheck(sha256=sha, matches=ok, detail=None if ok else "differs",
                     source_id=f"documents/{name}")  # fmt: skip


def _proposer(e: Mapping[str, Any]) -> Actor | None:
    raw = e.get("proposed_by")
    return _ACTOR.validate_python(raw) if isinstance(raw, dict) else None


def _entry(
    org: Org, e: dict[str, Any], all_: list[dict[str, Any]], store: Mapping[str, str],
    prints: dict[str, str], on: date,
) -> RegisterEntry:  # fmt: skip
    status, by = _status(e, all_, on)
    revoked = None
    if e.get("revoked_on"):
        revoked = Revoked(on=str(e["revoked_on"]), by=_person(org, e["revoked_by"]),
                          approved_by=_person(org, e["revocation_approved_by"]))  # fmt: skip
    return RegisterEntry(
        doc_id=e["doc_id"], kind=e["kind"], title=_title(e, store.get(e["sha256"])),
        owning_function=_lab.OWNER[e["kind"]], scope=_lab.scope(e), sha256=e["sha256"],
        effective_from=str(e["effective_from"]),
        effective_to=None if e.get("effective_to") is None else str(e["effective_to"]),
        relations=[RegisterRelation(type=r["type"], target=r["target"])
                   for r in e.get("relations") or []],
        terms=dict(e.get("terms") or {}), proposed_by=_proposer(e),
        registered_by=_party(org, e["registered_by"]), approved_by=_party(org, e["approved_by"]),
        registered_on=str(e["registered_on"]), approved_on=str(e["approved_on"]),
        revoked=revoked, status=status, superseded_by=by, file=_file(e, prints),
    )  # fmt: skip


def _mandates(org: Org, on: date) -> list[RegisterEntry]:
    out = []
    for doc_id in ("MANDATE-DEALDESK-2026",):
        m = Mandates(org).entry(doc_id)
        status: EntryStatus = "in_force"
        if on < _day(m.effective_from):
            status = "scheduled"
        elif m.effective_to and on > _day(m.effective_to):
            status = "expired"
        out.append(m.model_copy(update={"status": status}))
    return out


# -- series and coverage ------------------------------------------------------------------------
def _series(entries: list[RegisterEntry]) -> list[RegisterSeries]:
    """Entries joined by `supersedes` (either way), each series oldest first."""
    by_id = {e.doc_id: e for e in entries}
    parent = {d: d for d in by_id}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in entries:
        for r in e.relations:
            if r.type == "supersedes" and r.target in by_id:
                parent[find(e.doc_id)] = find(r.target)
    groups: dict[str, list[RegisterEntry]] = {}
    for e in entries:
        groups.setdefault(find(e.doc_id), []).append(e)
    out = []
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda m: (m.effective_from, m.doc_id))
        first = members[0]
        live = [m.doc_id for m in members if m.status == "in_force"]
        out.append(RegisterSeries(series_id=first.doc_id, kind=first.kind, scope=first.scope,
                                  title=first.title, entries=[m.doc_id for m in members],
                                  in_force=live[0] if len(live) == 1 else None))  # fmt: skip
    return out


def _coverage(org: Org, entries: list[RegisterEntry], on: date) -> list[Coverage]:
    procedures, _ = org.procedures()
    out = []
    for dt, kinds in _lab.COVERAGE.items():
        versions = [{**p, "doc_id": p["proc_id"]} for p in procedures if p["decision_type"] == dt]
        found = _lab.entry_in_force(versions, on)
        docs = [CoverageDocument(doc_id=e.doc_id, title=e.title) for e in entries
                if e.kind in kinds and e.status == "in_force"]  # fmt: skip
        gap = None
        if not docs:
            gap = (
                f"No {', '.join(kinds.values())} in force on {on}: a {dt} decision "
                f"is routed to {ROUTE_TO[cast('DecisionType', dt)]} (G-31)."
            )
        out.append(Coverage(
            decision_type=dt, label=LABEL[dt],
            procedure=CoverageProcedure(id=found["proc_id"], version=found["version"])
            if found else None,
            documents=docs, gap=gap,
        ))  # fmt: skip
    return out


# -- reads --------------------------------------------------------------------------------------
def view(org: Org, as_of: date | None) -> RegisterView:
    """The register as of `as_of` (the clock's date when None). `as_known_at` isn't served."""
    now: datetime = org.clock.now()
    on = as_of or now.date()
    state = org.register_state()
    prints = {name: sha for name, _, sha in _lab.doc_prints(org.evidence)}
    entries = [_entry(org, e, state.entries, state.store, prints, on) for e in state.entries]
    entries += _mandates(org, on)
    return RegisterView(
        version=state.version, clock=now.isoformat(), entries=entries,
        series=_series(entries), coverage=_coverage(org, entries, on),
        settings=RegisterSettings(on_mismatch=org.on_mismatch()),
    )  # fmt: skip


def entry(org: Org, doc_id: str) -> RegisterEntry:
    """One entry as of the clock's date. `NotFound` for an unknown id."""
    found = next((e for e in view(org, None).entries if e.doc_id == doc_id), None)
    if found is None:
        raise NotFound(f"register entry {doc_id}")
    return found


def text(org: Org, doc_id: str) -> str:
    """The entry's approved text, from the store, byte for byte."""
    state = org.register_state()
    found = next((e for e in state.entries if e["doc_id"] == doc_id), None)
    if found is None:
        raise NotFound(f"register entry {doc_id}")
    return str(state.store[found["sha256"]])


# -- settings -----------------------------------------------------------------------------------
def settings(org: Org) -> dict[str, str]:
    return {"on_mismatch": org.on_mismatch()}


def _no(rule: Any, detail: str) -> Refused:
    return Refused(422, [Refusal(rule=rule, detail=detail)])


def put_settings(org: Org, actor: Actor, body: Mapping[str, Any]) -> dict[str, str]:
    """Executives set `on_mismatch`; decisions honour it from the next one. An agent is RR-2,
    anyone else RR-4. Logged as `settings.changed`."""
    if isinstance(actor, AgentActor):
        raise _no(
            "RR-2", f"{actor.name} is an agent: a person must change the register's settings."
        )
    if actor.person.function != _lab.EXECUTIVE:
        raise _no("RR-4", f"{actor.person.name} is not an Executive: only an Executive may "
                          "change the register's settings.")  # fmt: skip
    if set(body) != {"on_mismatch"} or body["on_mismatch"] not in MODES:
        raise _no("RR-5", f"settings take exactly on_mismatch: one of {', '.join(MODES)}.")
    now = org.clock.now()  # before the write: never first read inside one
    with org.log.transaction() as tx:
        org.log.append(tx, at=now, org=org.org_id, stream=SETTINGS_STREAM,
                       kind="settings.changed", actor=actor.model_dump(mode="json"),
                       payload={"on_mismatch": body["on_mismatch"]})  # fmt: skip
    return settings(org)
