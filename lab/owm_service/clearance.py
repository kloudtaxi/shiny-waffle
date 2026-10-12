"""Clearance, redemption and reporting (spec §6.7, contract §5.9 and §7).

**Asking** (`Clearances.ask`). A body `decision_id` that differs from the path's is 422 (DC-2); a
body `actor` that differs from the session's is 403 (RR-1). Then, in one write transaction, every
check runs against the decision's current version and every failure is returned, in the
contract's order:
1. `stale`: the decision was withdrawn; the version asked about isn't current; a basis field
   differs from the system of record now (for SLA, the digest of the ticket's events, ruling R17);
   a registered basis document's sha256 differs from the register now, or one read unregistered
   is registered now; or a document in `register_used` is revoked on or before the clock's date
   (the kernel's RR-12 rule). A superseding document doesn't make it stale;
2. `spent`: the action was executed on the subject, by any decision;
3. `suspended`: the agent, or its version, is in OWM_SUSPENDED;
4. `outside_mandate`, agents only: no mandate; a version it doesn't allow; an action it doesn't
   list, or a decision type that action isn't listed for; a `per_day` limit reached (the
   clearances issued to the agent on the clock's date); or a limit the OWM can't evaluate.
   `may_ask` is never checked: asking grants nothing;
5. `differs`: each param must equal the decided one, unless the agent's mandate matches it
   `at_most` and the asked value is a number from 0 to the decided one, which the clearance then
   binds. People aren't mandate-checked, so theirs are exact;
6. `condition_open`, one per open blocking condition, and 7. `awaiting_approval`, one per approval
   not given, both only while the decision is live: once it is closed nothing waits on anyone
   (the contract's `laterDecisionRefused` is `spent` alone);
8. `declined`, one per declined approval.
A decision that isn't `ready` never clears, even if no check above names why (`stale`, fail
closed). Otherwise the clearance binds the decision, version, action, params and the session's
actor, is single use and expires after `clearance_ttl` seconds. A dry run checks and logs, and
issues nothing. It answers with its own shape, `{dry_run: true, would_clear, reasons}` (contract
v1.3, R34), so it never says `cleared` and never carries a clearance id.

**Redeeming** (`Clearances.redeem`), one write transaction, in this order: mark the clearance used
(`used` if it already was, and nothing else is checked); `expired`; `mismatch`; the re-checks
`stale`, `spent`, `condition_open` and `suspended` (of the bound actor); then the `executions`
insert, whose UNIQUE (org, subject, action) refuses a second redemption as `spent`; then
`clearance.redeemed`. Failures from `expired` to the re-checks are returned together. Any refusal
rolls back to before the mark, so a refused clearance stays unused (and a used one stays used),
and logs `redeem.refused`.

**Reporting** (`Clearances.report`): once per redeemed clearance, and only by the actor that
redeemed it (ruling R58, contract v1.3 §7.2): any actor may redeem, but a report whose `by`
differs from the `by` on `clearance.redeemed` is 422 DC-2. `by` is the actor, not the token: the
same person, or the same agent acting for the same principal, so a fresh sign-in can still
report. CLR ids are sequential, so holding one proves nothing; this stops another actor
reporting `failed` first, which would open a false incident and block the real report. `failed`
opens `INC-…` for the decision type's owning function (discount Sales, credit Finance, SLA
Customer Support). The action stays spent either way, and with no report at all.

**Streams.** `clearance.redeemed`, `execution.reported` and `incident.opened` change decisions'
derived fields (`state`, `executed`), so they go on the subject's stream (ruling R33), where a
step's write re-check sees them. `clearance.attempted` and `redeem.refused` decide nothing, so
they go on the decision's own stream (its id): an agent trying to act never makes an approver's
write 409. Payloads:
- `clearance.attempted`: `{issued, dry_run, decision_id, request, response}`, plus `clearance`
  (the `ClearanceRow` fields, `events.py` projects them) when issued;
- `redeem.refused`: `{clearance_id, decision_id, version, params, executor, reasons}`;
- `clearance.redeemed`: the `ExecutionRow` fields plus `executor`;
- `execution.reported`: `{clearance_id, decision_id, version, subject, action, status,
  external_ref, detail}`, and `incident.opened` the same keys but `status` and `external_ref`,
  plus `incident_id` and `function` (`state.py` reads `status` and `incident_id`).
`redeem.refused`, `clearance.redeemed`, `execution.reported` and `incident.opened` also carry
`by`, the session's actor, when the caller passes one (ruling R35: the HTTP layer always does).
The event's own actor stays the system the executor acts in.
"""

from __future__ import annotations

import dataclasses
import json
import math
import sqlite3
from collections.abc import Mapping
from datetime import date, datetime, timedelta
from typing import Any, Final, Protocol

from . import _lab, steps
from .clock import DEMO_TZ
from .decisions import Decisions
from .errors import NotFound, Refused
from .events import ClearanceRow, ExecutionRow
from .models import (
    Actor,
    AgentActor,
    ClearanceAttempt,
    ClearanceBound,
    ClearanceReason,
    ClearanceRequest,
    Cleared,
    DecisionRecord,
    DecisionType,
    DryRun,
    NotCleared,
    NotRedeemed,
    Redeemed,
    RedeemReason,
    RedeemRequest,
    Refusal,
    ReportRequest,
    ReportResponse,
    RuleCode,
)
from .org import Org
from .prepare import EVENTS, events_digest
from .sessions import Mandates, MandateTerms, suspended
from .state import is_live, subject_id

# who owns a failed execution's incident, by decision type (spec §6.7)
FUNCTION: Final[Mapping[DecisionType, str]] = {
    "discount": "Sales", "credit": "Finance", "sla": "Customer Support",
}  # fmt: skip
PERCENT: Final = frozenset({"discount"})  # params that are fractions, shown as percentages
DOLLARS: Final = frozenset({"limit_usd", "amount_usd"})
VERB: Final[Mapping[str, str]] = {
    "approval": "approves", "concurrence": "concurs", "claim_decision": "decides the claim",
}  # fmt: skip


class MandateBook(Protocol):
    """Where an agent's mandate is looked up (`sessions.Mandates`)."""

    def for_agent(self, agent_id: str) -> MandateTerms | None: ...


def _hhmm(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(DEMO_TZ).strftime("%H:%M")


def _number(x: Any) -> bool:
    return isinstance(x, int | float) and not isinstance(x, bool) and math.isfinite(x)


def _same(a: Any, b: Any) -> bool:
    """Equal as JSON values: a bool never equals a number."""
    return isinstance(a, bool) == isinstance(b, bool) and bool(a == b)


def _up_to(asked: Any, decided: Any) -> bool:
    """A mandate's `at_most`: `asked` is a number from 0 up to the decided one."""
    return _number(asked) and _number(decided) and 0 <= asked <= decided


def _show(param: str, v: Any) -> str:
    if _number(v) and param in PERCENT:
        return f"{v * 100:g}%"
    if _number(v) and param in DOLLARS:
        return f"${v:,.0f}" if float(v).is_integer() else f"${v:,.2f}"
    return v if isinstance(v, str) and v else json.dumps(v)


def _differs(param: str, decided: Any, asked: Any, at_most: bool) -> str:
    name = "" if param in PERCENT | DOLLARS else f"{param} "
    text = f"{name}{_show(param, decided)} was decided; {_show(param, asked)} was asked for."
    return text + (" The mandate allows from 0 up to the decided figure." if at_most else "")


def _spent(x: ExecutionRow) -> str:
    return (f"{x.action} on {x.subject} was executed by {x.decision_id} under {x.clearance_id} "
            f"at {_hhmm(x.redeemed_at)}.")  # fmt: skip


def _json(m: Any) -> dict[str, Any]:
    """As the service serves it (ruling R13): absent `?:` fields stay absent."""
    out: dict[str, Any] = m.model_dump(mode="json", exclude_unset=True)
    return out


def _system(executor: dict[str, Any]) -> dict[str, Any]:
    """The event actor for what the adapter does: the system it acts in."""
    return {"kind": "system", **executor}


def _by(actor: Actor | None) -> dict[str, Any]:
    """The payload key naming the session behind a redemption or report (ruling R35), if any."""
    return {} if actor is None else {"by": actor.model_dump(mode="json")}


def _as_served(attempt: Mapping[str, Any]) -> Any:
    """A logged attempt's response as v1.3 serves it (R64): a dry run logged before v1.3, as
    `{cleared: false, reasons}`, comes back as `{dry_run: true, would_clear, reasons}`."""
    resp = attempt["response"]
    if attempt.get("dry_run") and "dry_run" not in resp:
        return {"dry_run": True, "would_clear": not resp["reasons"], "reasons": resp["reasons"]}
    return resp


def _same_actor(a: Any, b: Any) -> bool:
    """Ruling R58 (contract v1.3 §7.2): the same person, or the same agent acting for the same
    principal. An agent's version and mandate don't count. With no actor on either side (a core
    call without a session, never the HTTP layer, R35) they match, as before."""

    def who(x: Any) -> tuple[str, ...] | None:
        if not isinstance(x, Mapping):
            return None
        if x.get("kind") == "person":
            return ("person", str(x["person"]["id"]))
        principal = x.get("on_behalf_of")
        return ("agent", str(x.get("id")),
                str(principal.get("id")) if isinstance(principal, Mapping) else "")  # fmt: skip

    return who(a) == who(b)


def _refused(rule: RuleCode, detail: str, status: int = 422) -> Refused:
    return Refused(status, [Refusal(rule=rule, detail=detail)])


class Clearances:
    def __init__(self, org: Org, decisions: Decisions, mandates: MandateBook | None = None) -> None:
        self.org, self.decisions = org, decisions
        self.mandates: MandateBook = mandates if mandates is not None else Mandates(org)

    # -- asking -------------------------------------------------------------------------------
    def ask(
        self, actor: Actor, decision_id: str, req: ClearanceRequest
    ) -> Cleared | NotCleared | DryRun:
        if req.decision_id != decision_id:
            raise _refused("DC-2", f"decision_id: the body names {req.decision_id} and the path "
                                   f"{decision_id}; they must be the same.")  # fmt: skip
        if req.actor is not None and req.actor.model_dump() != actor.model_dump():
            raise _refused("RR-1", "actor: the body's differs from the session's. The OWM acts "
                                   "for the session's actor; leave it out.", 403)  # fmt: skip
        now = self.org.clock.now()  # before the write: never first read inside one
        org = self.org.org_id
        with self.org.log.transaction() as tx:
            rec = self.decisions.get(decision_id)  # 404 for an unknown decision
            reasons, params = self._checks(actor, rec, req, now, tx)
            row: ClearanceRow | None = None
            resp: Cleared | NotCleared | DryRun
            if req.dry_run:
                resp = DryRun(dry_run=True, would_clear=not reasons, reasons=reasons)
            elif reasons:
                resp = NotCleared(cleared=False, reasons=reasons)
            else:
                cid = self.org.log.next_id(tx, org, "CLR", 5)
                bound = ClearanceBound(decision_id=decision_id, decision_version=rec.version,
                                       action=req.action, params=params, actor=actor)  # fmt: skip
                expires = (now + timedelta(seconds=self.org.settings.clearance_ttl)).isoformat()
                resp = Cleared(cleared=True, clearance_id=cid, bound=bound, expires_at=expires,
                               single_use=True)  # fmt: skip
                row = ClearanceRow(
                    id=cid, org=org, decision_id=decision_id, decision_version=rec.version,
                    action=req.action, subject=subject_id(rec.subject.model_dump()),
                    bound=bound.model_dump(mode="json"), expires_at=expires,
                )  # fmt: skip
                self.org.log.put_clearance(tx, row)
            payload: dict[str, Any] = {"issued": row is not None, "dry_run": bool(req.dry_run),
                                       "decision_id": decision_id, "request": _json(req),
                                       "response": _json(resp)}  # fmt: skip
            if row is not None:
                payload["clearance"] = dataclasses.asdict(row)
            self.org.log.append(tx, at=now, org=org, stream=decision_id,
                                kind="clearance.attempted", actor=actor.model_dump(mode="json"),
                                payload=payload)  # fmt: skip
        return resp

    def attempts(self, decision_id: str) -> list[ClearanceAttempt]:
        """Every clearance asked for on the decision, issued, refused or dry run, in order."""
        self.decisions.events(decision_id)  # 404 for an unknown decision
        evs = self.org.log.read(self.org.org_id, stream=decision_id, kinds=("clearance.attempted",))
        return [
            ClearanceAttempt.model_validate({"at": e.at.isoformat(), "actor": e.actor,
                                             "request": e.payload["request"],
                                             "response": _as_served(e.payload)})
            for e in evs
        ]  # fmt: skip

    def _checks(
        self, actor: Actor, rec: DecisionRecord, req: ClearanceRequest, now: datetime,
        tx: sqlite3.Connection,
    ) -> tuple[list[ClearanceReason], dict[str, Any]]:  # fmt: skip
        """Every failing check, in the contract's order, and the params a clearance would bind."""
        at_most, mandate = self._mandate(actor, rec, req.action, now, tx)
        differs, params = self._params(rec, req.action, req.params, at_most)
        out = [*self._stale(rec, req.decision_version, now.date()), *self._spent(rec, req.action),
               *self._suspended(actor), *mandate, *differs]  # fmt: skip
        if is_live(rec.state):
            out += [*self._open(rec), *self._awaiting(rec)]
        out += self._declined(rec)
        return self._ready(rec, out), params

    # -- the checks ---------------------------------------------------------------------------
    def _stale(self, rec: DecisionRecord, version: int, today: date) -> list[ClearanceReason]:
        did = rec.decision_id
        why: list[str] = []
        if rec.state == "withdrawn":
            why.append(f"{did} was withdrawn; it no longer stands.")
        if version != rec.version:
            why.append(f"{did} is at version {rec.version}, not {version}. Read it again.")
        why += self._basis_moved(rec)
        why += self._register_moved(rec, today)
        return [ClearanceReason(code="stale", detail=w) for w in why]

    def _basis_moved(self, rec: DecisionRecord) -> list[str]:
        """The basis fields that differ from the system of record now."""
        did, out = rec.decision_id, []
        for r in rec.basis.records:
            row = self.org.sor.row(r.table, r.id)
            if row is None:
                out.append(f"{r.id} is no longer in {r.table}.")
                continue
            for field, was in r.fields.items():
                if rec.decision_type == "sla" and field == EVENTS:
                    if events_digest(self.org, r.id) != was:
                        out.append(f"{r.id}'s events changed after {did} was decided.")
                elif row.get(field, "") != was:
                    now = row.get(field, "")
                    out.append(f"{r.id} {field} was {was or 'blank'} when {did} was decided; "
                               f"it is {now or 'blank'} now.")  # fmt: skip
        return out

    def _register_moved(self, rec: DecisionRecord, today: date) -> list[str]:
        """The basis documents the register no longer holds as they were, and the documents in
        `register_used` revoked on or before `today`."""
        did, out = rec.decision_id, []
        registered = {str(e["doc_id"]): e for e in self.org.register_state().entries}
        for d in rec.basis.documents:
            e = registered.get(d.doc_id)
            if d.registered and e is None:
                out.append(f"{d.doc_id} is no longer in the register.")
            elif d.registered and e is not None and str(e["sha256"]) != d.sha256:
                out.append(f"{d.doc_id} changed in the register after {did} was decided.")
            elif not d.registered and e is not None:
                out.append(f"{d.doc_id} was registered after {did} was decided.")
        for u in rec.register_used:
            e = registered.get(u.doc_id)
            if e is not None and _lab.revoked_on_or_before(e, today):
                out.append(f"{u.doc_id} is revoked from {e.get('revoked_on')}, on or before "
                           f"{today.isoformat()}.")  # fmt: skip
        return out

    def _executions(self, subject: str, action: str) -> list[ExecutionRow]:
        return [x for x in self.org.log.executions() if x.org == self.org.org_id
                and x.subject == subject and x.action == action]  # fmt: skip

    def _spent(self, rec: DecisionRecord, action: str) -> list[ClearanceReason]:
        sid = subject_id(rec.subject.model_dump())
        return [ClearanceReason(code="spent", detail=_spent(x))
                for x in self._executions(sid, action)]  # fmt: skip

    def _suspended(self, actor: Actor) -> list[ClearanceReason]:
        if isinstance(actor, AgentActor) and suspended(actor, self.org.settings):
            detail = f"{actor.name} ({actor.id}, version {actor.version}) is suspended."
            return [ClearanceReason(code="suspended", detail=detail)]
        return []

    def _mandate(
        self, actor: Actor, rec: DecisionRecord, action: str, now: datetime,
        tx: sqlite3.Connection,
    ) -> tuple[frozenset[str], list[ClearanceReason]]:  # fmt: skip
        """The params the agent's mandate matches `at_most`, and how the action falls outside the
        mandate. People aren't mandate-checked; `may_ask` never is."""
        if not isinstance(actor, AgentActor):
            return frozenset(), []
        terms = self.mandates.for_agent(actor.id)
        if terms is None:
            return frozenset(), [ClearanceReason(code="outside_mandate", detail=(
                f"{actor.name} ({actor.id}) has no mandate, so it may do nothing."))]  # fmt: skip
        why: list[str] = []
        if actor.version not in terms.versions:
            why.append(f"{actor.id} version {actor.version} isn't allowed to run under its "
                       f"mandate (only {', '.join(terms.versions)}).")  # fmt: skip
        may = next((m for m in terms.may_do if m.action == action), None)
        at_most: frozenset[str] = frozenset()
        if may is None:
            why.append(f"{actor.id}'s mandate doesn't let it {action}.")
        else:
            at_most = frozenset(k for k, v in may.match.items() if v == "at_most")
            if rec.decision_type not in may.decision_types:
                why.append(f"{actor.id}'s mandate lets it {action} on "
                           f"{' or '.join(may.decision_types)} decisions, not "
                           f"{rec.decision_type}.")  # fmt: skip
            for name, limit in (may.limits or {}).items():
                if name != "per_day":
                    why.append(f"{actor.id}'s mandate sets a limit the OWM can't check ({name}), "
                               "so it refuses.")  # fmt: skip
                elif (n := self._issued_today(actor.id, now, tx)) >= limit:
                    why.append(f"{actor.id} has had {n} clearances today; its mandate allows "
                               f"{limit:g} a day (per_day).")  # fmt: skip
        return at_most, [ClearanceReason(code="outside_mandate", detail=w) for w in why]

    def _issued_today(self, agent_id: str, now: datetime, tx: sqlite3.Connection) -> int:
        """The clearances issued to the agent on the clock's date (dry runs issue none)."""
        today = now.astimezone(DEMO_TZ).date()
        return sum(
            1 for e in self.org.log.read(self.org.org_id, kinds=("clearance.attempted",), tx=tx)
            if e.payload.get("issued") is True and e.actor is not None
            and e.actor.get("kind") == "agent" and e.actor.get("id") == agent_id
            and e.at.astimezone(DEMO_TZ).date() == today
        )  # fmt: skip

    def _params(
        self, rec: DecisionRecord, action: str, asked: Mapping[str, Any], at_most: frozenset[str]
    ) -> tuple[list[ClearanceReason], dict[str, Any]]:
        """`differs`, one per param that doesn't match, and the params a clearance binds."""
        decided = next((a for a in rec.actions if a.action == action), None)
        if decided is None:
            what = " and ".join(a.action for a in rec.actions) or f"no action ({rec.gated_outcome})"
            detail = f"{rec.decision_id} version {rec.version} decided {what}, not {action}."
            return [ClearanceReason(code="differs", detail=detail)], {}
        want, why, bound = decided.params, [], {}
        for k in [*want, *(k for k in asked if k not in want)]:
            if k not in asked:
                why.append(f"{k} {_show(k, want[k])} was decided; none was asked for.")
            elif k not in want:
                why.append(f"{k} wasn't decided; {_show(k, asked[k])} was asked for.")
            elif k in at_most and _up_to(asked[k], want[k]):
                bound[k] = asked[k]  # a mandate's at_most: the clearance binds the lower value
            elif _same(want[k], asked[k]):
                bound[k] = want[k]
            else:
                why.append(_differs(k, want[k], asked[k], k in at_most))
        return [ClearanceReason(code="differs", detail=w) for w in why], bound

    def _open(self, rec: DecisionRecord) -> list[ClearanceReason]:
        return [ClearanceReason(code="condition_open", detail=c.what, waiting_on=c.who,
                                condition_id=c.id) for c in steps.blocking(rec)]  # fmt: skip

    def _awaiting(self, rec: DecisionRecord) -> list[ClearanceReason]:
        return [ClearanceReason(code="awaiting_approval", detail=f"The {a.role} {VERB[a.kind]}.",
                                waiting_on=[a.person] if a.person else [])
                for a in rec.approvals if a.given is None and a.declined is None]  # fmt: skip

    def _declined(self, rec: DecisionRecord) -> list[ClearanceReason]:
        return [ClearanceReason(code="declined", detail=(
                    f"{a.declined.by.name} declined version {rec.version}: {a.declined.note}"))
                for a in rec.approvals if a.declined is not None]  # fmt: skip

    def _ready(self, rec: DecisionRecord, reasons: list[ClearanceReason]) -> list[ClearanceReason]:
        """Fail closed: a decision that isn't ready never clears, whatever named it."""
        if reasons or rec.state == "ready":
            return reasons
        detail = f"{rec.decision_id} is {rec.state}; only a ready decision is cleared."
        return [ClearanceReason(code="stale", detail=detail)]

    # -- redeeming ----------------------------------------------------------------------------
    def redeem(
        self, clearance_id: str, req: RedeemRequest, *, by: Actor | None = None
    ) -> Redeemed | NotRedeemed:
        """Redeem a clearance. `by` is the session that asked (ruling R35): recorded beside the
        executor on the event this writes, never checked against the clearance's actor. It is
        then the one actor that may report on the clearance (ruling R58)."""
        now = self.org.clock.now()  # before the write: never first read inside one
        at, org = now.isoformat(), self.org.org_id
        executor = req.executor.model_dump(mode="json")
        caller = _by(by)
        with self.org.log.transaction() as tx:
            row = self.org.log.get_clearance(clearance_id, tx=tx)
            if row is None or row.org != org:
                raise NotFound(f"clearance {clearance_id}")
            # `redeemed_at` is the very ISO string `mark_used` stores, so a rebuild equals this
            ex = ExecutionRow(org=org, subject=row.subject, action=row.action,
                              decision_id=row.decision_id, version=row.decision_version,
                              clearance_id=row.id, redeemed_at=at)  # fmt: skip
            tx.execute("SAVEPOINT redeem")
            reasons = self._redeem(tx, row, ex, req.params, now)
            if reasons:
                tx.execute("ROLLBACK TO redeem")  # un-marks it, if this redemption marked it
                tx.execute("RELEASE redeem")
                self.org.log.append(tx, at=now, org=org, stream=row.decision_id,
                                    kind="redeem.refused", actor=_system(executor), payload={
                    "clearance_id": row.id, "decision_id": row.decision_id,
                    "version": row.decision_version, "params": req.params, "executor": executor,
                    "reasons": [r.model_dump(mode="json") for r in reasons], **caller})  # fmt: skip
                return NotRedeemed(redeemed=False, reasons=reasons)
            tx.execute("RELEASE redeem")
            payload = {**dataclasses.asdict(ex), "executor": executor, **caller}
            self.org.log.append(tx, at=now, org=org, stream=row.subject, kind="clearance.redeemed",
                                actor=_system(executor), payload=payload)  # fmt: skip
        return Redeemed(redeemed=True, at=at)

    def _redeem(
        self, tx: sqlite3.Connection, row: ClearanceRow, ex: ExecutionRow,
        params: Mapping[str, Any], now: datetime,
    ) -> list[RedeemReason]:  # fmt: skip
        """The redemption's steps up to and including the `executions` insert of `ex`; any reason
        refuses it."""
        if not self.org.log.mark_used(tx, row.id, now):  # stores ex.redeemed_at, now's ISO string
            assert row.used_at is not None  # read in this transaction, so marked by another
            return [RedeemReason(code="used", detail=f"{row.id} was redeemed at "
                                                     f"{_hhmm(row.used_at)}.")]  # fmt: skip
        bound = ClearanceBound.model_validate(row.bound)
        out: list[RedeemReason] = []
        if now > datetime.fromisoformat(row.expires_at):
            detail = f"{row.id} expired at {_hhmm(row.expires_at)}."
            out.append(RedeemReason(code="expired", detail=detail))
        moved = sorted(k for k in set(params) | set(bound.params)
                       if k not in params or k not in bound.params
                       or not _same(params[k], bound.params[k]))  # fmt: skip
        if moved:
            detail = f"The params differ from those {row.id} is bound to: {', '.join(moved)}."
            out.append(RedeemReason(code="mismatch", detail=detail))
        rec = self.decisions.get(row.decision_id)
        checks = [*self._stale(rec, row.decision_version, now.date()),
                  *self._spent(rec, row.action)]  # fmt: skip
        if is_live(rec.state):
            checks += self._open(rec)
        checks += self._suspended(bound.actor)
        # the re-checks' codes are all redemption codes; validation refuses any other loudly
        out += [RedeemReason.model_validate({"code": r.code, "detail": r.detail})
                for r in self._ready(rec, checks)]  # fmt: skip
        if out:
            return out
        if not self.org.log.insert_execution(tx, ex):  # UNIQUE (org, subject, action): the guard
            first = self._executions(row.subject, row.action)
            detail = _spent(first[0]) if first else f"{row.action} on {row.subject} was executed."
            return [RedeemReason(code="spent", detail=detail)]
        return []

    # -- reporting ----------------------------------------------------------------------------
    def report(
        self, clearance_id: str, req: ReportRequest, *, by: Actor | None = None
    ) -> ReportResponse:
        """The adapter's report on a redeemed clearance. `failed` opens an incident for the
        decision type's owning function; the action stays spent. `by` is recorded as in
        `redeem`, and must be the actor that redeemed it (ruling R58): another is DC-2."""
        now = self.org.clock.now()  # before the write: never first read inside one
        org = self.org.org_id
        caller = _by(by)
        row = self.org.log.get_clearance(clearance_id)
        if row is None or row.org != org:
            raise NotFound(f"clearance {clearance_id}")
        kind = self.decisions.get(row.decision_id, row.decision_version).decision_type
        incident: str | None = None
        with self.org.log.transaction() as tx:
            evs = self.org.log.read(org, stream=row.subject, tx=tx,
                                    kinds=("clearance.redeemed", "execution.reported"))  # fmt: skip
            mine = [e for e in evs if e.payload.get("clearance_id") == clearance_id]
            redeemed = next((e for e in mine if e.kind == "clearance.redeemed"), None)
            done = next((e for e in mine if e.kind == "execution.reported"), None)
            if redeemed is None:
                raise _refused("DC-2", f"{clearance_id} hasn't been redeemed, so there is nothing "
                                       "to report.")  # fmt: skip
            if not _same_actor(redeemed.payload.get("by"), caller.get("by")):
                raise _refused("DC-2", f"Only the person or agent that redeemed {clearance_id} "
                                       "may report on it.")  # fmt: skip
            if done is not None:
                when = _hhmm(done.at.isoformat())
                raise _refused("DC-2", f"{clearance_id} was already reported "
                                       f"{done.payload['status']} at {when}.")  # fmt: skip
            base = {"clearance_id": clearance_id, "decision_id": row.decision_id,
                    "version": row.decision_version, "subject": row.subject,
                    "action": row.action}  # fmt: skip
            self.org.log.append(tx, at=now, org=org, stream=row.subject, actor=redeemed.actor,
                                kind="execution.reported", payload={
                **base, "status": req.status, "external_ref": req.external_ref,
                "detail": req.detail, **caller})  # fmt: skip
            if req.status == "failed":
                incident = self.org.log.next_id(tx, org, "INC", 4)
                why = req.detail or "no detail given"
                detail = (f"{row.action} on {row.subject} failed after {clearance_id} was "
                          f"redeemed: {why}. It stays spent.")  # fmt: skip
                self.org.log.append(tx, at=now, org=org, stream=row.subject, actor=redeemed.actor,
                                    kind="incident.opened", payload={
                    **base, "incident_id": incident, "function": FUNCTION[kind],
                    "detail": detail, **caller})  # fmt: skip
        return ReportResponse(incident_id=incident)
