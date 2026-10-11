"""Levels, the subject's floor and the ratchet (spec §6.5, G-46), the self-sourced-basis check
(spec §6.6, ruling R23) and the register's revocations (the `revoked` flag, spec §6.2).

Asking (Task 11) and re-running (Task 12) build a version's floor the same way, through `assess`;
everything under it is a pure function of the registered terms and the log:

- **The level** is the band of the registered policy in force on `as_of` that the figure falls in
  (`requested_discount` as a fraction, `requested_limit_usd`; the submitted figure when the system
  of record has no row), plus, for credit, the concurrences that apply to the customer's tier. It
  never asks the kernel, so a withheld outcome has one too. SLA has none, so no floor.
- **The floor belongs to the subject.** It starts at the first decision's level and rises with any
  later version or decision (the higher band, the union of the concurrences). Only a
  `confirmed_lower_level` resolution lowers it, to the level of the version that carried the
  condition. Withdrawn, declined and spent decisions keep theirs with the subject. Each
  `decision.versioned` event keeps its version's level beside the version (`level`), so the floor
  is rebuilt from the log alone, never from a register that may have changed since.
- **Below the floor** the outcome stands. The version gets a blocking `ratchet` condition for the
  holder of the floor's role, passed up exactly as an approval is (`_lab.pass_up`, separation of
  duties, so never the requester), and a `ratchet` flag.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Final

from . import _lab
from .assemble import ratchet_flag, self_sourced_flag
from .conditions import ratchet_condition
from .events import Event
from .models import Condition, DecisionType, Flag, Floor, PersonRef, SetBy
from .org import Org
from .people import People
from .sor import BASIS_FIELDS
from .state import subject_id

POLICY_KIND: Final[Mapping[str, str]] = {"discount": "pricing_policy", "credit": "credit_policy"}
FIGURE: Final[Mapping[str, str]] = {
    "discount": "requested_discount", "credit": "requested_limit_usd",
}  # fmt: skip
CONFIRMED_LOWER: Final = "confirmed_lower_level"
# a basis column by its §3.5 name
CONTRACT_FIELD: Final[Mapping[str, str]] = {
    "account_id": "customer", "erp_customer_id": "customer", "product_sku": "product",
    "requested_discount_pct": "requested_discount", "requested_limit_usd": "requested_limit_usd",
    "current_limit_usd": "current_limit_usd", "request_date": "request_date",
    "requested_by": "requestor",
}  # fmt: skip
PER: Final[Mapping[str, int]] = {  # a numeric column's divisor into the contract's unit
    "requested_discount_pct": 100, "requested_limit_usd": 1, "current_limit_usd": 1,
}  # fmt: skip


# -- levels -------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Level:
    band: int  # the index of the policy's band
    concurrences: frozenset[str]  # credit: the titles whose concurrence applies
    title: str  # the band's title

    def json(self) -> dict[str, Any]:
        return {"band": self.band, "concurrences": sorted(self.concurrences), "title": self.title}

    @classmethod
    def of(cls, raw: Mapping[str, Any] | None) -> Level | None:
        if raw is None:
            return None
        return cls(int(raw["band"]), frozenset(raw["concurrences"]), str(raw["title"]))


def _above(figure: float, min_exclusive: Any) -> bool:
    return min_exclusive is None or figure > float(min_exclusive)


def _within(figure: float, max_inclusive: Any) -> bool:
    return max_inclusive is None or figure <= float(max_inclusive)


def level_for(kind: str, figure: float, terms: Mapping[str, Any], tier: str | None) -> Level | None:
    """The first band with `min_exclusive < figure <= max_inclusive` (None is open); credit adds
    the titles of the `concurrence` entries with `figure > min_exclusive` whose `tiers` list holds
    `tier` or is empty. None for SLA, or for a figure no band holds."""
    if kind not in FIGURE:
        return None
    found = next(((i, b) for i, b in enumerate(terms.get("bands") or [])
                  if _above(figure, b.get("min_exclusive"))
                  and _within(figure, b.get("max_inclusive"))), None)  # fmt: skip
    if found is None:
        return None
    applies: frozenset[str] = frozenset()
    if kind == "credit":
        applies = frozenset(str(c["title"]) for c in terms.get("concurrence") or []
                            if _above(figure, c.get("min_exclusive"))
                            and (not c.get("tiers") or tier in c["tiers"]))  # fmt: skip
    return Level(found[0], applies, str(found[1]["title"]))


def below(level: Level, floor: Level) -> bool:
    """A lower band, or a concurrence the floor required is missing."""
    return level.band < floor.band or not floor.concurrences <= level.concurrences


def raised(floor: Level, level: Level) -> Level:
    """The higher band (with its title) and the union of the concurrences."""
    top = level if level.band > floor.band else floor
    return Level(top.band, floor.concurrences | level.concurrences, top.title)


# -- the register -------------------------------------------------------------------------------
def _day(x: Any) -> date:
    return x if isinstance(x, date) else date.fromisoformat(str(x))


def _in_window(e: Mapping[str, Any], on: date) -> bool:
    if e.get("revoked_on") and on >= _day(e["revoked_on"]):
        return False
    end = e.get("effective_to")
    return _day(e["effective_from"]) <= on <= (_day(end) if end else date.max)


def in_force(
    entries: Iterable[Mapping[str, Any]], doc_kind: str, on: date
) -> Mapping[str, Any] | None:
    """The one entry of `doc_kind` in force on `on`: inside its window, not revoked on or before
    it, and not superseded by another entry in force (the kernel's `entry_in_force` rule). None
    when none is, or when two are."""
    live = [e for e in entries if e.get("kind") == doc_kind and _in_window(e, on)]
    superseded = {r.get("target") for e in live for r in e.get("relations") or []
                  if r.get("type") == "supersedes"}  # fmt: skip
    live = [e for e in live if e["doc_id"] not in superseded]
    return live[0] if len(live) == 1 else None


def policy_terms(
    kind: str, policy: str | None, entries: Iterable[Mapping[str, Any]], on: date,
    terms_of: Callable[[str], dict[str, Any] | None],
) -> dict[str, Any] | None:  # fmt: skip
    """The terms a level is read from: the registered policy the authority names, else (withheld,
    or a policy the register doesn't hold) the pricing or credit policy in force on `on`."""
    named = terms_of(policy) if policy else None
    if named is not None:
        return named
    entry = in_force(entries, POLICY_KIND[kind], on) if kind in POLICY_KIND else None
    terms = entry.get("terms") if entry else None
    return dict(terms) if isinstance(terms, Mapping) else None


def revoked_by(entries: Iterable[Mapping[str, Any]], on: date) -> dict[str, str]:
    """doc_id -> revocation date, for each entry revoked on or before `on`."""
    return {str(e["doc_id"]): str(e["revoked_on"]) for e in entries
            if e.get("revoked_on") and _day(e["revoked_on"]) <= on}  # fmt: skip


# -- the floor ----------------------------------------------------------------------------------
@dataclass(frozen=True)
class FloorState:
    subject: str
    level: Level
    set_by: tuple[str, int]  # (decision_id, version)
    confirmed_by: PersonRef | None = None

    def model(self) -> Floor:
        did, n = self.set_by
        return Floor(subject=self.subject, level=self.level.band,
                     set_by=SetBy(decision_id=did, version=n),
                     confirmed_by=self.confirmed_by)  # fmt: skip


def after(
    floor: FloorState | None, subject: str, level: Level | None, decision_id: str, version: int
) -> FloorState | None:
    """The subject's floor once a version at `level` is made: it starts there, rises to it, or
    stays (and keeps who set it)."""
    if level is None:
        return floor
    if floor is None:
        return FloorState(subject, level, (decision_id, version))
    up = raised(floor.level, level)
    return floor if up == floor.level else FloorState(subject, up, (decision_id, version))


def floor_from(events: Iterable[Event], subject: str) -> FloorState | None:
    """The subject's floor, rebuilt from `decision.versioned` events (each keeps its version's
    `level`) and `confirmed_lower_level` resolutions, across every decision on the subject."""
    floor: FloorState | None = None
    carried: dict[str, list[tuple[int, Level | None, frozenset[str]]]] = {}
    for e in events:
        if e.kind == "decision.versioned":
            v = e.payload["version"]
            if subject_id(v["subject"]) != subject:
                continue
            did, n = str(v["decision_id"]), int(v["version"])
            level = Level.of(e.payload.get("level"))
            cids = frozenset(str(c["id"]) for c in v.get("conditions") or [])
            carried.setdefault(did, []).append((n, level, cids))
            floor = after(floor, subject, level, did, n)
        elif (e.kind == "condition.resolved"
              and e.payload["resolved"]["resolution"] == CONFIRMED_LOWER):  # fmt: skip
            did = str(e.payload["decision_id"])
            held = [(n, lv) for n, lv, cids in carried.get(did, [])
                    if e.payload["condition_id"] in cids]  # fmt: skip
            n, lowered = held[-1] if held else (0, None)
            if lowered is not None:
                by = PersonRef.model_validate(e.payload["resolved"]["by"])
                floor = FloorState(subject, lowered, (did, n), by)
    return floor


def floor_of(org: Org, subject: str) -> FloorState | None:
    return floor_from(org.log.read(org.org_id, stream=subject), subject)


def first_asked(events: Iterable[Event], subject: str) -> datetime | None:
    """When the subject's first decision was asked for (ruling R23)."""
    versions = [e.payload["version"] for e in events if e.kind == "decision.versioned"]
    return min((datetime.fromisoformat(v["requested_at"]) for v in versions
                if subject_id(v["subject"]) == subject), default=None)  # fmt: skip


def confirmer(org: Org, requester_id: str, floor: Level) -> PersonRef:
    """Who confirms a level below the floor: the holder of the floor's title for this request,
    passed up under separation of duties by the approvals' own code path (`_lab.pass_up`), so a
    ratchet and an approval never name different people. Never the requester."""
    holder = _lab.pass_up(org.evidence.table("employees"), requester_id, floor.title)
    if holder is None:
        raise ValueError(f"nobody holds the {floor.title} for {requester_id}'s request")
    if holder["employee_id"] == requester_id:
        raise ValueError(f"only the requester, {requester_id}, holds the {floor.title}")
    return org.people.ref(holder["employee_id"])


# -- self-sourced basis -------------------------------------------------------------------------
@dataclass(frozen=True)
class Edit:
    field: str  # by its §3.5 name
    was: str  # in the contract's unit
    now: str
    by: str  # who made it
    at: datetime


def _shown(column: str, raw: str, people: People) -> str:
    """A basis column's value as the contract states it (§3.5): the discount as a fraction (15.0
    is 0.15), money as a number, the requester as an employee id."""
    if column in PER:
        try:
            x = round(float(raw) / PER[column], 9)
        except ValueError:
            return raw
        return str(int(x)) if x.is_integer() else repr(x)
    if column == "requested_by":
        who = people.by_email(raw) if raw else None
        return who.id if who else raw
    return raw


def _requesters(actor: Mapping[str, Any] | None, requester: PersonRef) -> str | None:
    """Who made an edit, if it was the requester or an agent acting for them."""
    if not actor:
        return None
    if actor.get("kind") == "agent":
        principal = actor.get("on_behalf_of")
        if isinstance(principal, Mapping) and principal.get("id") == requester.id:
            return f"{actor.get('name') or actor.get('id')} for {requester.name}"
        return None
    person = actor.get("person")
    pid = person.get("id") if isinstance(person, Mapping) else actor.get("id")
    return requester.name if actor.get("kind") == "person" and pid == requester.id else None


def self_sourced(
    edits: Iterable[Event], kind: str, requester: PersonRef | None, since: datetime,
    people: People,
) -> list[Edit]:  # fmt: skip
    """Each `sor.edited` on one of the decision type's basis columns after `since`, by the
    requester or an agent whose principal is the requester, that changed the value."""
    if requester is None or kind not in FIGURE:
        return []
    columns = set(BASIS_FIELDS[kind])
    out = []
    for e in edits:
        p = e.payload
        column = str(p["field"])
        if e.kind != "sor.edited" or column not in columns or e.at <= since:
            continue
        by = _requesters(e.actor, requester)
        was, now = _shown(column, str(p["was"]), people), _shown(column, str(p["now"]), people)
        if by is not None and was != now:
            out.append(Edit(CONTRACT_FIELD[column], was, now, by, e.at))
    return out


# -- a version's level, floor, ratchet and self-sourced flags -----------------------------------
@dataclass(frozen=True)
class Assessment:
    level: Level | None  # kept beside the version in its `decision.versioned` event
    floor: FloorState | None  # the subject's floor once this version is made
    conditions: list[Condition]  # the ratchet's, when the version is below the floor
    flags: list[Flag]  # self_sourced_basis, then ratchet

    def level_json(self) -> dict[str, Any] | None:
        return None if self.level is None else self.level.json()


def assess(
    org: Org, *, kind: DecisionType, subject: str, table: str, decision_id: str, version: int,
    requester: PersonRef | None, figures: Mapping[str, Any], row: Mapping[str, str],
    authority: Mapping[str, Any] | None, as_of: date, requested_at: datetime, cid: str,
) -> Assessment:  # fmt: skip
    """Version `version` of `decision_id`: its level, the subject's floor before and after it, the
    ratchet when it is below that floor, and the requester's own edits to its basis since the
    subject's first ask. `figures` are by §3.5 names in contract units, `row` is the record the
    kernel was given (the credit tier is read from it), `authority` the kernel's, `cid` the id a
    ratchet condition takes."""
    events = org.log.read(org.org_id, stream=subject)
    prior = floor_from(events, subject)
    auth = authority or {}
    level = None
    figure = figures.get(FIGURE.get(kind, ""))
    if figure is not None:
        terms = policy_terms(kind, auth.get("policy"), org.register_state().entries, as_of,
                             org.policy_terms)  # fmt: skip
        tier = _lab.credit_tier(org.evidence, row) if kind == "credit" else None
        level = level_for(kind, float(figure), terms, tier) if terms else None
    since = min(t for t in (first_asked(events, subject), requested_at) if t is not None)
    flags = [self_sourced_flag(subject, x.field, x.was, x.now, x.by, x.at)
             for x in self_sourced(org.sor.edits(table, subject), kind, requester, since,
                                   org.people)]  # fmt: skip
    conditions = []
    if level is not None and prior is not None and below(level, prior.level):
        if requester is None:
            raise ValueError(f"{subject} is below its floor and has no requester")
        fv, title = prior.set_by[1], prior.level.title
        desc = (f"within {requester.name}'s own authority" if auth.get("requestor_authorized")
                else f"at the {level.title}")  # fmt: skip
        conditions.append(ratchet_condition(cid, fv, title, version, desc,
                                            confirmer(org, requester.id, prior.level)))  # fmt: skip
        flags.append(ratchet_flag(subject, fv, title))
    return Assessment(level, after(prior, subject, level, decision_id, version), conditions, flags)
