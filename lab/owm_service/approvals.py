"""`GET /approvals` (contract §8, spec §4): the work items waiting on the viewer, those waiting on
someone else that the viewer follows, and what the viewer has done.

Each source of work yields its open items, with who follows each, and the viewer's done items.
`view` sorts them into the three lists the same way for every source:
- **waiting on you**: an open item whose `waiting_on` names the viewer. Only a person can be
  waited on: an agent never takes a people step (DC-1), so nothing waits on an agent;
- **waiting on others**: any other open item the viewer follows: one they asked for, one that is
  their request, or (for an agent) one waiting on the person it acts for;
- **done**: what the viewer resolved, approved or declined, most recent first.

The decision source (this module) gives two kinds of item, over every live decision's current
version:
- `decision_approval`: an approval, concurrence or claim decision not yet given or declined. Its
  `held_by` lists the version's open blocking conditions, which hold approving (DC-4);
- `condition`: an open condition, ratchet confirmations included, waiting on its `who`.
The register adds two kinds, as another source (`register_items`), over every change:
- `register_change`: a pending change, waiting on its approvers (RR-4). Its id is the change's id
  and its `href` the change's URL. Done: approved or declined by the viewer;
- `register_draft` (B-11): an agent's draft, waiting on everyone in the function that owns its
  kind and on the person the agent drafted for (who may dismiss it, ruling R42); a person's own
  draft waits on that person alone. Done: submitted or dismissed by the viewer.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final

from pydantic import TypeAdapter

from .changes import Change, named
from .decisions import Decisions
from .models import (
    Actor,
    ApprovalRequirement,
    ApprovalsView,
    Condition,
    DecidedAction,
    DecisionRecord,
    DoneWorkItem,
    HeldBy,
    PersonActor,
    PersonRef,
    WorkItem,
)
from .org import Org
from .prepare import principal
from .register_queue import RegisterQueue
from .state import decision_of, is_live, subject_id

# imperative (the item's title) and present tense (its detail), by approval kind
ASK: Final = {
    "approval": "Approve", "concurrence": "Concur on", "claim_decision": "Decide the claim on",
}  # fmt: skip
DOES: Final = {
    "approval": "approves", "concurrence": "concurs on", "claim_decision": "decides the claim on",
}  # fmt: skip
TITLE: Final = {
    "input_conflict": "Confirm the {field} on {subject}",
    "missing_record": "Add {subject} to the system of record",
    "ratchet": "Confirm the lower approval level on {subject}",
}
STEPS: Final = ("condition.resolved", "decision.approved", "decision.declined")


@dataclass(frozen=True)
class Viewer:
    """Who is looking: `you`, the person things may wait on (None for an agent), and `follows`,
    whose work the session follows (the person, or the person an agent acts for)."""

    you: str | None
    follows: str | None

    @classmethod
    def of(cls, actor: Actor) -> Viewer:
        p = principal(actor)
        return cls(actor.person.id if isinstance(actor, PersonActor) else None,
                   p.id if p else None)  # fmt: skip


@dataclass(frozen=True)
class Open:
    """An open work item, and the people who follow it (it waits on others, for them)."""

    item: WorkItem
    followers: frozenset[str]


Source = Callable[[Org, Viewer], tuple[list[Open], list[DoneWorkItem]]]


def view(org: Org, actor: Actor) -> ApprovalsView:
    viewer = Viewer.of(actor)
    opened: list[Open] = []
    done: list[DoneWorkItem] = []
    for source in SOURCES:
        o, d = source(org, viewer)
        opened += o
        done += d
    order = sorted(opened, key=lambda o: (_when(o.item.raised_at), o.item.id))
    yours = [o.item for o in order if viewer.you in _ids(o.item.waiting_on)]
    others = [o.item for o in order if viewer.you not in _ids(o.item.waiting_on)
              and viewer.follows is not None and viewer.follows in o.followers]  # fmt: skip
    latest = sorted(done, key=lambda d: (_when(d.at), d.id), reverse=True)
    return ApprovalsView(waiting_on_you=yours, waiting_on_others=others, done=latest)


def _ids(people: Iterable[PersonRef]) -> set[str]:
    return {p.id for p in people}


def _when(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


# -- decisions ----------------------------------------------------------------------------------
def decision_items(org: Org, viewer: Viewer) -> tuple[list[Open], list[DoneWorkItem]]:
    decisions = Decisions(org)
    opened: list[Open] = []
    for rec in decisions.list():
        if is_live(rec.state):
            opened += _open_items(decisions, rec)
    return opened, _done_items(org, decisions, viewer)


def _followers(rec: DecisionRecord, waiting_on: Sequence[PersonRef]) -> frozenset[str]:
    """The decision's requester, the person who asked (or the agent's principal), and whoever it
    waits on (so an agent acting for them follows it)."""
    asker = principal(rec.actor)
    people = [rec.requested_by, asker, *waiting_on]
    return frozenset(p.id for p in people if p is not None)


def _open_items(decisions: Decisions, rec: DecisionRecord) -> list[Open]:
    blocking = [c for c in rec.conditions if c.blocking and c.resolved is None]
    held = [HeldBy(condition_id=c.id, what=c.what, who=c.who) for c in blocking]
    out = []
    for i, a in enumerate(rec.approvals):
        if a.given is None and a.declined is None:
            item = _approval_item(rec, i, a, held)
            out.append(Open(item, _followers(rec, item.waiting_on)))
    for c in rec.conditions:
        if c.resolved is None:
            item = _condition_item(decisions, rec, c)
            out.append(Open(item, _followers(rec, item.waiting_on)))
    return out


def _approval_item(
    rec: DecisionRecord, i: int, a: ApprovalRequirement, held: list[HeldBy]
) -> WorkItem:
    did, sid = rec.decision_id, subject_id(rec.subject.model_dump())
    detail = f"The {a.role} {DOES[a.kind]} version {rec.version} of {did} ({rec.gated_outcome})"
    detail += "".join(f": {_action(x)}" for x in rec.actions[:1]) + "."
    if a.passed_from is not None:
        detail += f" Passed up from {a.passed_from.person.name}: separation of duties."
    if held:
        verb = "is" if len(held) == 1 else "are"
        detail += f" Held until {', '.join(h.condition_id for h in held)} {verb} resolved (DC-4)."
    return WorkItem(
        kind="decision_approval", id=f"{did}:v{rec.version}:approvals[{i}]",
        title=f"{ASK[a.kind]} {did} ({sid})", detail=detail, raised_by=rec.actor,
        raised_at=rec.decided_at, waiting_on=[a.person] if a.person else [], held_by=held,
        href=_href(did),
    )  # fmt: skip


def _condition_item(decisions: Decisions, rec: DecisionRecord, c: Condition) -> WorkItem:
    did, sid = rec.decision_id, subject_id(rec.subject.model_dump())
    opened = rec if c.opened_in_version == rec.version else decisions.get(did, c.opened_in_version)
    field = (c.field or "figure").replace("_", " ")
    return WorkItem(
        kind="condition", id=f"{did}:{c.id}",
        title=TITLE[c.source].format(field=field, subject=sid), detail=c.what,
        raised_by=rec.actor, raised_at=opened.decided_at, waiting_on=c.who, held_by=[],
        href=_href(did),
    )  # fmt: skip


def _done_items(org: Org, decisions: Decisions, viewer: Viewer) -> list[DoneWorkItem]:
    """What the viewer resolved, approved or declined, from the decision events."""
    if viewer.you is None:
        return []
    out: list[DoneWorkItem] = []
    for e in org.log.read(org.org_id, kinds=STEPS):
        did = decision_of(e)
        if did is None:
            continue
        if e.kind == "condition.resolved":
            r = e.payload["resolved"]
            if r["by"]["id"] != viewer.you:
                continue
            rec = decisions.get(did, int(r["rerun_version"]) - 1)
            c = next(x for x in rec.conditions if x.id == e.payload["condition_id"])
            item = _condition_item(decisions, rec, c)
            out.append(DoneWorkItem(**_fields(item), result=str(r["resolution"]), at=r["at"]))
            continue
        step = e.payload["given"] if e.kind == "decision.approved" else e.payload["declined"]
        if step["by"]["id"] != viewer.you:
            continue
        rec = decisions.get(did, int(e.payload["version"]))
        i = int(e.payload["index"])
        item = _approval_item(rec, i, rec.approvals[i], [])
        result = "approved" if e.kind == "decision.approved" else "declined"
        out.append(DoneWorkItem(**_fields(item), result=result, at=step["at"]))
    return out


def _fields(item: WorkItem) -> dict[str, Any]:
    return {k: getattr(item, k) for k in WorkItem.model_fields}


def _href(decision_id: str) -> str:
    return f"/api/v1/decisions/{decision_id}"


def _action(a: DecidedAction) -> str:
    """What the action does, in a few words."""
    p = a.params
    if a.action == "apply_discount":
        return f"a {float(p['discount']) * 100:g}% discount on {p['request_id']}"
    if a.action == "set_credit_limit":
        return f"a ${float(p['limit_usd']):,.0f} credit limit for {p['customer_id']}"
    return f"a ${float(p['amount_usd']):,.2f} service credit on {p['ticket']}"


# -- the register ------------------------------------------------------------------------------
_ACTOR: Final[TypeAdapter[Actor]] = TypeAdapter(Actor)


def register_items(org: Org, viewer: Viewer) -> tuple[list[Open], list[DoneWorkItem]]:
    queue = RegisterQueue(org)
    opened: list[Open] = []
    done: list[DoneWorkItem] = []
    for c in queue.changes():
        if c.state == "pending":
            item = _change_item(c)
            opened.append(Open(item, _register_followers(c, item.waiting_on)))
        elif c.state == "draft":
            item = _draft_item(c, queue.draft_waiting(c))
            opened.append(Open(item, _register_followers(c, item.waiting_on)))
        if viewer.you is not None:
            done += _register_done(queue, c, viewer.you)
    return opened, done


def _register_followers(c: Change, waiting_on: Sequence[PersonRef]) -> frozenset[str]:
    """Whoever it waits on, its submitter, and the person who drafted it (or the agent's)."""
    people = [*waiting_on, *c.drafters(), c.submitter()]
    return frozenset(str(p.id if isinstance(p, PersonRef) else p) for p in people if p)


def _change_item(c: Change) -> WorkItem:
    assert c.submitted_by is not None and c.submitted_at is not None  # pending: submitted
    who = c.submitted_by["name"]
    detail = f"{who} submitted {c.what()} for the {c.owning_function} function"
    detail += f" against register version {c.base_version}; it waits on {named(c.approvers)}."
    return WorkItem(
        kind="register_change", id=c.change_id, title=f"Approve {c.what()}", detail=detail,
        raised_by=PersonActor(kind="person", person=PersonRef.model_validate(c.submitted_by)),
        raised_at=c.submitted_at, waiting_on=[PersonRef.model_validate(p) for p in c.approvers],
        held_by=[], href=_change_href(c.change_id),
    )  # fmt: skip


def _draft_item(c: Change, waiting_on: list[PersonRef]) -> WorkItem:
    assert c.proposed_by is not None and c.proposed_at is not None  # a stored draft
    drafter = _ACTOR.validate_python(c.proposed_by)
    name = drafter.person.name if isinstance(drafter, PersonActor) else drafter.name
    owner = c.owning_function or "no function (the registrar doesn't know its kind)"
    detail = f"{name} drafted {c.what()}; {owner} owns it: submit it or dismiss it."
    if c.checks:
        detail += f" The rules would refuse it now ({c.checks[0]['rule']}): {c.checks[0]['detail']}"
    return WorkItem(
        kind="register_draft", id=c.change_id, title=f"Submit or dismiss {c.what()}",
        detail=detail, raised_by=drafter, raised_at=c.proposed_at, waiting_on=waiting_on,
        held_by=[], href=_change_href(c.change_id),
    )  # fmt: skip


def _register_done(queue: RegisterQueue, c: Change, you: str) -> list[DoneWorkItem]:
    """What the viewer did with a change: approved or declined it (their item as an approver),
    or submitted or dismissed a draft."""
    out: list[DoneWorkItem] = []
    if c.approved_by and c.approved_by["id"] == you:
        out.append(DoneWorkItem(**_fields(_change_item(c)), result="approved",
                                at=str(c.approved_at)))  # fmt: skip
    if c.declined and c.declined["by"]["id"] == you:
        out.append(DoneWorkItem(**_fields(_change_item(c)), result="declined",
                                at=str(c.declined["at"])))  # fmt: skip
    if c.refused_by and c.refused_by["id"] == you:  # any rule refused at their approval
        out.append(DoneWorkItem(**_fields(_change_item(c)), result="refused",
                                at=str(c.refused_at)))  # fmt: skip
    if c.proposed_by is not None:  # a stored draft
        draft = _draft_item(c, queue.draft_waiting(c))
        if c.submitted_by and c.submitted_by["id"] == you:
            out.append(DoneWorkItem(**_fields(draft), result="submitted",
                                    at=str(c.submitted_at)))  # fmt: skip
        if c.withdrawn and c.submitted_by is None and c.withdrawn["by"]["id"] == you:
            out.append(DoneWorkItem(**_fields(draft), result="dismissed",
                                    at=str(c.withdrawn["at"])))  # fmt: skip
    return out


def _change_href(change_id: str) -> str:
    return f"/api/v1/register/changes/{change_id}"


SOURCES: Final[tuple[Source, ...]] = (decision_items, register_items)
