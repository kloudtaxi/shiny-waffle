"""A decision's derived fields and state (spec §5 and §6.3).

A version is stored whole, without what later events decide: `state`, `executed`, each
condition's `resolved`, and each approval's `given` and `declined`. They are derived on read
from the decision's later events and the `executions` projection, so rebuilding never re-runs the
kernel.

Every decision event sits on the stream named for its subject (`DR-9001`, `CR-9201`,
`SR-39385`), so the subject's last `seq` moves on any write to any of its decisions. The events
this module reads, by payload (the steps that write them come later):
- `decision.versioned`: `{version: <the fixed fields>, kernel, kernel_extra}`;
- `condition.resolved`: `{decision_id, condition_id, resolved: <Condition.resolved>}`. A condition
  id is unique within its decision across versions, so a resolution holds in every version that
  carries the condition;
- `decision.approved`: `{decision_id, version, index, given: <ApprovalRequirement.given>}` and
  `decision.declined`: `{decision_id, version, index, declined: <…declined>}`, where `index` is
  the approval's place in that version's `approvals`. Approvals bind to a version;
- `decision.withdrawn`: `{decision_id, version}`.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

from .events import Event, ExecutionRow
from .models import DecisionState

NOT_LIVE: Final[frozenset[str]] = frozenset({"withdrawn", "declined", "spent"})


def is_live(state: DecisionState) -> bool:
    """Live unless withdrawn, declined or spent (DC-6: one live decision per subject)."""
    return state not in NOT_LIVE


def subject_id(subject: Mapping[str, Any]) -> str:
    """The id a decision is keyed by: the request id (discount, credit) or the ticket (SLA)."""
    return str(subject.get("request_id") or subject.get("ticket"))


def decision_of(e: Event) -> str | None:
    """The decision an event belongs to, or None."""
    if e.kind == "decision.versioned":
        return str(e.payload["version"]["decision_id"])
    d = e.payload.get("decision_id")
    return d if isinstance(d, str) else None


def resolutions(events: Iterable[Event], decision_id: str) -> dict[str, dict[str, Any]]:
    """Each resolved condition's `resolved`, by condition id."""
    return {
        str(e.payload["condition_id"]): e.payload["resolved"]
        for e in events
        if e.kind == "condition.resolved" and decision_of(e) == decision_id
    }


def approval_steps(
    events: Iterable[Event], decision_id: str, version: int
) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    """(given, declined) for `version`'s approvals, each by the approval's index."""
    given: dict[int, dict[str, Any]] = {}
    declined: dict[int, dict[str, Any]] = {}
    for e in events:
        if decision_of(e) != decision_id or e.payload.get("version") != version:
            continue
        if e.kind == "decision.approved":
            given[int(e.payload["index"])] = e.payload["given"]
        elif e.kind == "decision.declined":
            declined[int(e.payload["index"])] = e.payload["declined"]
    return given, declined


def withdrawn(events: Iterable[Event], decision_id: str) -> bool:
    return any(e.kind == "decision.withdrawn" and decision_of(e) == decision_id for e in events)


def executed(version: Mapping[str, Any], executions: Iterable[ExecutionRow]) -> list[ExecutionRow]:
    """The executions on the version's subject, by any decision (§5.9)."""
    subject = subject_id(version["subject"])
    return [x for x in executions if x.subject == subject]


def spent(version: Mapping[str, Any], executions: Iterable[ExecutionRow]) -> bool:
    """Every action the version decided has been executed on its subject, by any decision."""
    done = {x.action for x in executed(version, executions)}
    actions = version["actions"]
    return bool(actions) and all(a["action"] in done for a in actions)


def derive_state(
    version: Mapping[str, Any], events: Sequence[Event], executions: Sequence[ExecutionRow]
) -> DecisionState:
    """Spec §6.3, first match wins. `events` are the decision's own (others are ignored) and
    `executions` the projection's rows (only the subject's count)."""
    did, n = str(version["decision_id"]), int(version["version"])
    if withdrawn(events, did):
        return "withdrawn"
    if spent(version, executions):
        return "spent"
    if not version["actions"]:
        return "no_action"
    res = resolutions(events, did)
    if any(c["blocking"] and c.get("resolved") is None and c["id"] not in res
           for c in version["conditions"]):  # fmt: skip
        return "not_ready"
    given, declined = approval_steps(events, did, n)
    if declined:
        return "declined"
    if any(i not in given and a.get("given") is None for i, a in enumerate(version["approvals"])):
        return "awaiting_approval"
    return "ready"


def with_derived(
    version: Mapping[str, Any], events: Sequence[Event], executions: Sequence[ExecutionRow]
) -> dict[str, Any]:
    """The stored version with its derived fields filled in: a whole `DecisionRecord`."""
    out = copy.deepcopy(dict(version))
    did, n = str(out["decision_id"]), int(out["version"])
    res = resolutions(events, did)
    for c in out["conditions"]:
        c["resolved"] = res.get(c["id"], c.get("resolved"))
    given, declined = approval_steps(events, did, n)
    for i, a in enumerate(out["approvals"]):
        a["given"] = given.get(i, a.get("given"))
        a["declined"] = declined.get(i, a.get("declined"))
    out["executed"] = [
        {"action": x.action, "decision_id": x.decision_id, "version": x.version,
         "clearance_id": x.clearance_id, "redeemed_at": x.redeemed_at,
         "report": None, "incident_id": None}  # reports and incidents: the clearance step
        for x in executed(version, executions)
    ]  # fmt: skip
    out["state"] = derive_state(version, events, executions)
    return out
