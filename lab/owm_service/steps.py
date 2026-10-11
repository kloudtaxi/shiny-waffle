"""The rules a people step on a decision checks first (spec §6.4): DC-1 to DC-5, over the current
version with its derived fields. DC-5 is 409; every other rule is 422. In this order:

1. **DC-1**: an agent never takes a people step: resolve, rerun, approve, decline or withdraw.
2. **DC-5**: the step names the current `decision_version`. A stale view is refused before the
   rest, since the rest is checked against the version the actor didn't see.
3. **A closed decision** (withdrawn, declined or spent) takes no more steps: DC-2, since nothing
   waits on anyone. Its floor stays with the subject.
4. Then, reported together:
   - **DC-2**, the step must name you: a resolution needs a person in the condition's `who`, and
     must fit the condition's source (ruling R28); approving or declining needs the person an
     outstanding approval names, and a decline needs a note; a withdraw needs the requester; a
     re-run needs the requester or any approval's person;
   - **DC-3**, separation of duties: the requester never approves, concurs or declines, and never
     confirms a ratchet; one person never gives two of a version's approvals;
   - **DC-4**: approving or declining is held while a blocking condition is open on the version.

"The requester" is the row's `requested_by`. SLA has none (a ticket isn't anyone's request), so
there DC-3 names nobody, and withdrawing or re-running falls to whoever asked (`owner`).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from .errors import NotFound, Refused
from .models import (
    Actor,
    AgentActor,
    Condition,
    DecisionRecord,
    PersonRef,
    Refusal,
    Resolution,
    RuleCode,
)
from .prepare import principal
from .state import is_live, subject_id

# ruling R28: the resolutions each condition source takes
FITS: Final[Mapping[str, tuple[Resolution, ...]]] = {
    "input_conflict": ("confirmed_record", "corrected_record"),
    "missing_record": ("corrected_record",),
    "ratchet": ("confirmed_lower_level",),
}


def _no(rule: RuleCode, detail: str) -> Refusal:
    return Refusal(rule=rule, detail=detail)


def _raise(refusals: list[Refusal]) -> None:
    if refusals:
        raise Refused(422, refusals)


def _named(people: list[PersonRef]) -> str:
    names = [p.name for p in people]
    if not names:
        return "nobody"
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def requester(rec: DecisionRecord) -> PersonRef | None:
    """Whose request it is (separation of duties): the row's `requested_by`; null for SLA."""
    return rec.requested_by


def owner(rec: DecisionRecord) -> PersonRef | None:
    """Who may withdraw it or ask for a re-run as its requester: the requester, or for SLA the
    person who asked (the agent's principal when an agent asked)."""
    return rec.requested_by or principal(rec.actor)


# -- 1-3: who, which version, still open --------------------------------------------------------
def person(actor: Actor) -> PersonRef:
    """DC-1: the person taking the step; an agent is refused."""
    if isinstance(actor, AgentActor):
        detail = (f"{actor.name} is an agent, and agents never take a people step on a decision. "
                  "A person must take it.")  # fmt: skip
        raise Refused(422, [_no("DC-1", detail)])
    return actor.person


def current(rec: DecisionRecord, version: int) -> None:
    """DC-5: the version the step names is the current one (409)."""
    if version != rec.version:
        raise Refused(409, [_no("DC-5", f"{rec.decision_id} is at version {rec.version}, not "
                                        f"{version}. Read it again, then act on version "
                                        f"{rec.version}.")])  # fmt: skip


def live(rec: DecisionRecord) -> None:
    """A withdrawn, declined or spent decision takes no more steps."""
    if not is_live(rec.state):
        sid = subject_id(rec.subject.model_dump())
        raise Refused(422, [_no("DC-2", f"{rec.decision_id} is {rec.state}: it takes no more "
                                        f"steps, and its floor stays with {sid}. Ask again for a "
                                        "new decision.")])  # fmt: skip


def condition(rec: DecisionRecord, cid: str) -> Condition:
    found = next((c for c in rec.conditions if c.id == cid), None)
    if found is None:
        raise NotFound(f"decision {rec.decision_id} version {rec.version} has no condition {cid}")
    return found


# -- 4: DC-2, DC-3, DC-4, by step ---------------------------------------------------------------
def may_resolve(rec: DecisionRecord, me: PersonRef, c: Condition, resolution: Resolution) -> None:
    out: list[Refusal] = []
    if c.resolved is not None:
        r = c.resolved
        _raise([_no("DC-2", f"{c.id} is already resolved ({r.resolution} by {r.by.name}, re-run "
                            f"as version {r.rerun_version}).")])  # fmt: skip
    if me.id not in {p.id for p in c.who}:
        out.append(_no("DC-2", f"{c.id} is for {_named(c.who)} to resolve, not {me.name}."))
    if resolution not in FITS[c.source]:
        out.append(_no("DC-2", f"{c.id} is a {c.source} condition, and {resolution} doesn't fit "
                               f"it: it takes {' or '.join(FITS[c.source])}."))  # fmt: skip
    asker = requester(rec)
    if c.source == "ratchet" and asker is not None and me.id == asker.id:
        out.append(_no("DC-3", f"{me.name} asked for this decision; the requester never confirms "
                               "a lower approval level on their own request."))  # fmt: skip
    _raise(out)


def blocking(rec: DecisionRecord) -> list[Condition]:
    """The version's open blocking conditions (they hold approving, DC-4)."""
    return [c for c in rec.conditions if c.blocking and c.resolved is None]


def may_approve(rec: DecisionRecord, me: PersonRef, *, declining: bool, note: str | None) -> int:
    """The index of the outstanding approval `me` gives (or declines) on this version."""
    out: list[Refusal] = []
    verb = "decline" if declining else "approve"
    mine = [i for i, a in enumerate(rec.approvals) if a.person is not None and a.person.id == me.id]
    done = [i for i in mine if rec.approvals[i].given or rec.approvals[i].declined]
    todo = [i for i in mine if i not in done]
    if not rec.approvals:
        out.append(_no("DC-2", f"{rec.decision_id} version {rec.version} needs no approval."))
    elif not mine:
        waiting = [a.person for a in rec.approvals if a.person is not None]
        out.append(_no("DC-2", f"No approval on {rec.decision_id} version {rec.version} names "
                               f"{me.name}; it waits on {_named(waiting)}."))  # fmt: skip
    elif not todo:
        out.append(_no("DC-2", f"{me.name} has already given or declined their approval on "
                               f"{rec.decision_id} version {rec.version}."))  # fmt: skip
    if declining and not (note and note.strip()):
        out.append(_no("DC-2", "A decline needs a note: say why, so the requester can act on it."))
    asker = requester(rec)
    if asker is not None and me.id == asker.id:
        out.append(_no("DC-3", f"{me.name} asked for this decision; the requester never approves, "
                               f"concurs or declines on their own request."))  # fmt: skip
    if todo and done:
        out.append(_no("DC-3", f"{me.name} already gave one of this version's approvals; the "
                               "approver and a concurrer are never the same person."))  # fmt: skip
    held = blocking(rec)
    if held:
        what = "; ".join(f"{c.id} ({c.source}, for {_named(c.who)})" for c in held)
        out.append(_no("DC-4", f"Can't {verb} while a blocking condition is open on version "
                               f"{rec.version}: {what}. Resolving it re-runs the "
                               "decision."))  # fmt: skip
    _raise(out)
    return todo[0]


def may_withdraw(rec: DecisionRecord, me: PersonRef) -> None:
    asker = owner(rec)
    if asker is None or me.id != asker.id:
        _raise([_no("DC-2", f"Only the requester ({_named([asker] if asker else [])}) withdraws "
                            f"{rec.decision_id}.")])  # fmt: skip


def may_rerun(rec: DecisionRecord, me: PersonRef) -> None:
    asker = owner(rec)
    allowed = [*([asker] if asker else []), *(a.person for a in rec.approvals if a.person)]
    if me.id not in {p.id for p in allowed}:
        _raise([_no("DC-2", f"A re-run of {rec.decision_id} is for its requester or an approver "
                            f"({_named(allowed)}), not {me.name}.")])  # fmt: skip
