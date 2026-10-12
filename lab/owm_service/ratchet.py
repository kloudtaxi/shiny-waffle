"""Levels, the subject's floor and the ratchet (spec §6.5, G-46), the self-sourced-basis check
(spec §6.6, ruling R23) and the register's revocations (the `revoked` flag, spec §6.2).

Asking (Task 11) and re-running (Task 12) build a version's floor the same way, through `assess`;
everything under it is a pure function of the registered terms and the log:

- **The level** is the band of the registered policy in force on `as_of` that the figure falls in
  (`requested_discount` as a fraction, `requested_limit_usd`; the submitted figure when the system
  of record has no row), plus, for credit, the concurrences that apply to the customer's tier. It
  never asks the kernel, so a withheld outcome has one too. SLA has none, so no floor.
- **The floor belongs to the subject.** It starts at the first decision's level and rises with any
  later version or decision (the higher band, the union of the concurrences). Only
  `confirmed_lower_level` resolutions lower it, to the level of the version that opened the
  ratchet, once every ratchet condition that version opened is confirmed (R61). Withdrawn,
  declined and spent decisions keep theirs with the subject. Each
  `decision.versioned` event keeps its version's level beside the version (`level`), so the floor
  is rebuilt from the log alone, never from a register that may have changed since.
- **Below the floor** the outcome stands. The version gets a `ratchet` flag and a round of
  blocking `ratchet` conditions, one per confirmer (`confirmers`): the holder of the floor's role
  and, for credit, the holder of each concurrence the floor required that this level drops (R61,
  contract v1.3's R26). Each is passed up exactly as an approval is (`_lab.pass_up`, separation of
  duties, so never the requester), and one person never confirms twice.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
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


# -- the register (the kernel's own rules, through `_lab`, so they can't drift) -----------------
def in_force(
    entries: Iterable[Mapping[str, Any]], doc_kind: str, on: date
) -> Mapping[str, Any] | None:
    """The one entry of `doc_kind` in force on `on`, by `kernel.entry_in_force`: inside its
    window, not revoked on or before it, and not superseded by another entry in force. None when
    none is, or when two are."""
    return _lab.entry_in_force([e for e in entries if e.get("kind") == doc_kind], on)


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
    """doc_id -> revocation date, for each entry revoked on or before `on` (RR-12, by the kernel's
    `Register.as_of`)."""
    return {str(e["doc_id"]): str(e["revoked_on"]) for e in entries
            if _lab.revoked_on_or_before(e, on)}  # fmt: skip


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


Made = list[tuple[str, int, "Level | None"]]  # (decision_id, version, level), in log order


def floor_from(events: Iterable[Event], subject: str) -> FloorState | None:
    """The subject's floor, rebuilt from `decision.versioned` events (each keeps its version's
    `level`) and `confirmed_lower_level` resolutions of ratchet conditions, across every decision
    on the subject. A round (the ratchet conditions one version opened) lowers it once all of its
    conditions are confirmed, by the resolution that completes it (R61). How many confirmers a
    round needs is read from the log too: one, plus one per concurrence the floor in force just
    before the opening version required and that version's level drops. So a round opened before
    v1.3, with the band holder alone, never completes without the concurrence's holder; a re-run
    opens a full round."""
    floor: FloorState | None = None
    made: Made = []
    ratchets: dict[tuple[str, str], int] = {}  # (decision_id, condition id) -> opened_in_version
    confirmed: set[tuple[str, str]] = set()  # (decision_id, condition id)
    needs: dict[tuple[str, int], int] = {}  # (decision_id, opening version) -> confirmers needed
    for e in events:
        if e.kind == "decision.versioned":
            v = e.payload["version"]
            if subject_id(v["subject"]) != subject:
                continue
            did, n = str(v["decision_id"]), int(v["version"])
            level = Level.of(e.payload.get("level"))
            made.append((did, n, level))
            opens = False
            for c in v.get("conditions") or []:
                if c.get("source") == "ratchet":
                    ratchets.setdefault((did, str(c["id"])), int(c["opened_in_version"]))
                    opens = opens or int(c["opened_in_version"]) == n
            if opens and floor is not None and level is not None:
                needs[(did, n)] = 1 + len(floor.level.concurrences - level.concurrences)
            floor = after(floor, subject, level, did, n)
        elif (e.kind == "condition.resolved"
              and e.payload["resolved"]["resolution"] == CONFIRMED_LOWER):  # fmt: skip
            confirmed.add((str(e.payload["decision_id"]), str(e.payload["condition_id"])))
            floor = _confirmed(floor, subject, made, ratchets, confirmed, needs, e.payload)
    return floor


def _confirmed(
    floor: FloorState | None, subject: str, made: Made, ratchets: Mapping[tuple[str, str], int],
    confirmed: set[tuple[str, str]], needs: Mapping[tuple[str, int], int],
    resolution: Mapping[str, Any],
) -> FloorState | None:  # fmt: skip
    """A confirmed lower level, honoured only on a ratchet's condition, and only once its round
    is complete: every ratchet condition opened in the same version of the same decision is in
    `confirmed`, and there are as many as the round `needs` (R61). The floor then drops to the
    level of the version that opened the round (by decision and `opened_in_version`, not by log
    order), and every version logged after that one raises it as it would have. So the floor is
    the same whether the resolution is logged before or after the re-run's version."""
    did = str(resolution["decision_id"])
    opened = ratchets.get((did, str(resolution["condition_id"])))
    round_ = {key for key, n in ratchets.items() if key[0] == did and n == opened}
    if opened is None or len(round_) < needs.get((did, opened), 1) or not round_ <= confirmed:
        return floor
    at = next((i for i, (d, n, _) in enumerate(made) if (d, n) == (did, opened)), None)
    level = None if at is None else made[at][2]
    if at is None or opened is None or level is None:
        return floor
    by = PersonRef.model_validate(resolution["resolved"]["by"])
    lowered: FloorState | None = FloorState(subject, level, (did, opened), by)
    for d, n, lv in made[at + 1 :]:
        lowered = after(lowered, subject, lv, d, n)
    return lowered


def floor_of(org: Org, subject: str) -> FloorState | None:
    return floor_from(org.log.read(org.org_id, stream=subject), subject)


def first_asked(events: Iterable[Event], subject: str) -> datetime | None:
    """When the subject's first decision was asked for (ruling R23)."""
    versions = [e.payload["version"] for e in events if e.kind == "decision.versioned"]
    return min((datetime.fromisoformat(v["requested_at"]) for v in versions
                if subject_id(v["subject"]) == subject), default=None)  # fmt: skip


def _holder(org: Org, requester_id: str, title: str) -> PersonRef:
    """The holder of `title` for this request, passed up under separation of duties by the
    approvals' own code path (`_lab.pass_up`), so a ratchet and an approval never name different
    people. Never the requester."""
    holder = _lab.pass_up(org.evidence.table("employees"), requester_id, title)
    if holder is None:
        raise ValueError(f"nobody holds the {title} for {requester_id}'s request")
    if holder["employee_id"] == requester_id:
        raise ValueError(f"only the requester, {requester_id}, holds the {title}")
    return org.people.ref(holder["employee_id"])


def confirmers(org: Org, requester_id: str, floor: Level, level: Level) -> list[PersonRef]:
    """Who confirms `level` below `floor`, one ratchet condition each: the holder of the floor's
    title, then (credit, R61: R26 in contract v1.3) the holder of each concurrence the floor
    required that `level` drops, by title. Never the requester, and never one person twice: they
    would be confirming their own check, so that fails closed (R62)."""
    titles = [floor.title, *sorted(floor.concurrences - level.concurrences)]
    people = [_holder(org, requester_id, t) for t in titles]
    for i, p in enumerate(people):
        twice = next((titles[j] for j in range(i) if people[j].id == p.id), None)
        if twice is not None:
            raise ValueError(f"{p.name} would confirm as both the {twice} and the {titles[i]}; "
                             "the confirmers are never the same person")  # fmt: skip
    return people


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
    authority: Mapping[str, Any] | None, as_of: date, requested_at: datetime, next_n: int,
    pending: Sequence[Event] = (),
) -> Assessment:  # fmt: skip
    """Version `version` of `decision_id`: its level, the subject's floor before and after it, the
    ratchet when it is below that floor, and the requester's own edits to its basis since the
    subject's first ask. `figures` are by §3.5 names in contract units, `row` is the record the
    kernel was given (the credit tier is read from it), `authority` the kernel's, `next_n` the
    number the first ratchet condition's id takes (`c{next_n}`, then on, one per confirmer).
    `pending` are events the same command will append with this version
    (a re-run's `condition.resolved`): the floor counts them, and `floor_from` doesn't depend on
    where they land in the log."""
    events = [*org.log.read(org.org_id, stream=subject), *pending]
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
        needed, stands = phrases(prior, level, decision_id, version, requester.name,
                                 bool(auth.get("requestor_authorized")))  # fmt: skip
        dropped = [None, *sorted(prior.level.concurrences - level.concurrences)]
        for i, (who, title) in enumerate(
            zip(confirmers(org, requester.id, prior.level, level), dropped, strict=True)
        ):
            conditions.append(ratchet_condition(f"c{next_n + i}", needed, stands, version, who,
                                                concurrence=title))  # fmt: skip
        flags.append(ratchet_flag(subject, needed))
    return Assessment(level, after(prior, subject, level, decision_id, version), conditions, flags)


def _concurrence(titles: Iterable[str]) -> str:
    names = sorted(titles)
    joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    return f"the {joined} concurrence{'' if len(names) == 1 else 's'}"


def phrases(
    floor: FloorState, level: Level, decision_id: str, version: int, requester: str,
    authorized: bool,
) -> tuple[str, str]:  # fmt: skip
    """The ratchet's wording for a version below `floor`: what the floor needed and where this
    version stands. A floor set by another decision names it (ruling R24); one set by this
    decision keeps the bare `version N`. A floor that needed concurrences names them, and a
    version that is below only because it drops one (its band isn't lower) says which."""
    did, fv = floor.set_by
    same = did == decision_id
    need = floor.level.title
    if floor.level.concurrences:
        need += f" with {_concurrence(floor.level.concurrences)}"
    needed = f"{'' if same else did + ' '}version {fv} needed the {need}"
    this = f"version {version}" if same else f"this decision's version {version}"
    if level.band >= floor.level.band:
        return needed, f"{this} drops {_concurrence(floor.level.concurrences - level.concurrences)}"
    where = f"within {requester}'s own authority" if authorized else f"at the {level.title}"
    return needed, f"{this} is {where}"
