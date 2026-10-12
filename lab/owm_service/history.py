"""A decision's history as the contract shows it (`GET /decisions/{id}/events`, `DecisionEvent`).

The log keeps a decision's events on two streams: what changes it (versions, resolutions,
approvals, declines, withdrawals, re-runs, redemptions, reports, incidents) on its subject's,
and what decides nothing (clearance attempts and refused redemptions) on its own id's. The history
merges both in log order (`seq`) and words each event for a person. Log event → kind:
- `decision.versioned`: `requested` (at `requested_at`) then `decided` for version 1; `decided`,
  with what changed, for a later version;
- `decision.rerun_requested` → `rerun`; `condition.resolved` → `condition_resolved`, on the
  version it resolved; `decision.approved`, `.declined`, `.withdrawn` → `approved`, `declined`,
  `withdrawn`;
- `clearance.attempted` → `clearance_cleared` when issued, or when a dry run would clear (rulings
  R34 and R64; the detail says nothing was issued); otherwise `clearance_refused`;
- `redeem.refused` → `clearance_refused`, at redemption;
- `clearance.redeemed`, `execution.reported`, `incident.opened` → `clearance_redeemed`,
  `execution_reported`, `incident_raised`.

`decision.failed` (a re-run the kernel couldn't make) changed nothing and has no contract kind, so
it isn't shown. A redemption's or report's actor is the session that drove it (`by`, ruling R35),
or, when the core was called without one, the actor the clearance was issued to: the event's own
actor is the executor's system, which the contract's `Actor` can't carry.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Final

from .clock import DEMO_TZ
from .decisions import Decisions
from .events import Event
from .models import DecisionEvent
from .org import Org
from .state import subject_id

SIDE: Final = ("clearance.attempted", "redeem.refused")  # on the decision's own stream
DID: Final = {"approval": "approved", "concurrence": "concurred on", "claim_decision": "decided"}


def events(org: Org, decisions: Decisions, decision_id: str) -> list[DecisionEvent]:
    """The decision's history, oldest first. NotFound for an unknown decision."""
    own = decisions.events(decision_id)
    side = org.log.read(org.org_id, stream=decision_id, kinds=SIDE)
    versions = {int(e.payload["version"]["version"]): e.payload["version"]
                for e in own if e.kind == "decision.versioned"}  # fmt: skip
    out: list[DecisionEvent] = []
    for e in sorted([*own, *side], key=lambda e: e.seq):
        out += _words(org, e, versions)
    return out


def _event(at: str, actor: Any, version: int, kind: str, detail: str) -> DecisionEvent:
    return DecisionEvent.model_validate(
        {"at": at, "actor": actor, "version": version, "kind": kind, "detail": detail}
    )


def _name(actor: Mapping[str, Any] | None) -> str:
    """A person's name; an agent's, with whom it acts for; a system's id."""
    kind = actor.get("kind") if actor else None
    if actor and kind == "person":
        return str(actor["person"]["name"])
    if actor and kind == "agent":
        principal = actor.get("on_behalf_of")
        return f"{actor['name']} for {principal['name']}" if principal else str(actor["name"])
    return str((actor or {}).get("id") or (actor or {}).get("system") or "the OWM")


def _hhmm(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(DEMO_TZ).strftime("%H:%M")


def _executor(org: Org, e: Event) -> Any:
    """The actor shown for a redemption or report: `by`, else the clearance's bound actor."""
    if "by" in e.payload:
        return e.payload["by"]
    row = org.log.get_clearance(str(e.payload["clearance_id"]))
    return row.bound["actor"] if row else e.actor


def _words(org: Org, e: Event, versions: Mapping[int, Mapping[str, Any]]) -> list[DecisionEvent]:
    if e.kind == "decision.versioned":
        return _versioned(e, e.payload["version"])
    if e.kind == "clearance.attempted":
        return [_attempt(e)]
    said = _step(e, versions) or _execution(org, e)
    return [] if said is None else [_event(e.at.isoformat(), *said)]


Said = tuple[Any, int, str, str]  # (actor, version, kind, detail)


def _step(e: Event, versions: Mapping[int, Mapping[str, Any]]) -> Said | None:
    """A people step: a re-run, a resolution, an approval, a decline or a withdrawal."""
    p, who = e.payload, _name(e.actor)
    match e.kind:
        case "decision.rerun_requested":
            n = int(p["version"])
            return e.actor, n, "rerun", f"{who} asked for a re-run of version {n}."
        case "condition.resolved":
            r = p["resolved"]
            note = f" ({r['note']})" if r.get("note") else ""
            text = f"{r['by']['name']} resolved {p['condition_id']}: {r['resolution']}{note}."
            return e.actor, int(r["rerun_version"]) - 1, "condition_resolved", text
        case "decision.approved" | "decision.declined":
            n, i = int(p["version"]), int(p["index"])
            a = versions[n]["approvals"][i]
            if e.kind == "decision.declined":
                d = p["declined"]
                text = f"{d['by']['name']} ({a['role']}) declined version {n}: {d['note']}"
                return e.actor, n, "declined", text
            g = p["given"]
            note = f" ({g['note']})" if g.get("note") else ""
            text = f"{g['by']['name']} ({a['role']}) {DID[a['kind']]} version {n}{note}."
            return e.actor, n, "approved", text
        case "decision.withdrawn":
            n = int(p["version"])
            return e.actor, n, "withdrawn", f"{who} withdrew it at version {n}."
    return None


def _execution(org: Org, e: Event) -> Said | None:
    """A redemption (or a refused one), a report or an incident; None for anything else, such as
    `decision.failed`, which decided nothing."""
    p = e.payload
    match e.kind:
        case "redeem.refused":
            why = ", ".join(r["code"] for r in p["reasons"])
            text = f"Redeeming {p['clearance_id']} was refused: {why}."
            kind = "clearance_refused"
        case "clearance.redeemed":
            ex = p.get("executor") or {}
            text = (f"{p['clearance_id']} was redeemed: {p['action']} on {p['subject']}, through "
                    f"{ex.get('system')}/{ex.get('adapter')}.")  # fmt: skip
            kind = "clearance_redeemed"
        case "execution.reported":
            detail = f": {p['detail']}" if p.get("detail") else ""
            text = f"{p['clearance_id']} was reported {p['status']}{detail}."
            kind = "execution_reported"
        case "incident.opened":
            text = f"{p['incident_id']} was raised for {p['function']}: {p['detail']}"
            kind = "incident_raised"
        case _:
            return None
    return _executor(org, e), int(p["version"]), kind, text


def _versioned(e: Event, v: Mapping[str, Any]) -> list[DecisionEvent]:
    n = int(v["version"])
    opened = [c for c in v["conditions"] if c["opened_in_version"] == n]
    text = f"Version {n}: {v['gated_outcome']}{' (routed)' if v.get('routed') else ''}."
    if v.get("previous"):
        text += f" {v['previous']['what_changed']}"
    if opened:
        text += " Opened " + ", ".join(f"{c['id']} ({c['source']})" for c in opened) + "."
    decided = _event(e.at.isoformat(), e.actor, n, "decided", text)
    if n != 1:
        return [decided]
    kind, sid = v["decision_type"], subject_id(v["subject"])
    text = f"{_name(e.actor)} asked for a {kind} decision on {sid}."
    return [_event(v["requested_at"], e.actor, 1, "requested", text), decided]


def _attempt(e: Event) -> DecisionEvent:
    p, at = e.payload, e.at.isoformat()
    req, resp = p["request"], p["response"]
    n, action = int(req["decision_version"]), req["action"]
    if p.get("issued"):
        text = (f"{resp['clearance_id']} was issued for {action} on version {n}, single use, "
                f"until {_hhmm(resp['expires_at'])}.")  # fmt: skip
        return _event(at, e.actor, n, "clearance_cleared", text)
    if p.get("dry_run") and not resp["reasons"]:  # R34: a dry run that would clear
        text = f"A dry run of {action} on version {n}: nothing stops it. Nothing was issued."
        return _event(at, e.actor, n, "clearance_cleared", text)
    why = ", ".join(r["code"] for r in resp["reasons"])
    dry = " (dry run)" if p.get("dry_run") else ""
    text = f"{action} on version {n} was refused{dry}: {why}."
    return _event(at, e.actor, n, "clearance_refused", text)
