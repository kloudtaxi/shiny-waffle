"""The decision lifecycle (spec §6): asking, which makes version 1; the people steps, which
resolve, re-run, approve, decline or withdraw it; and reading decisions back.

Asking (spec §6.1), in order:
1. the subject's id must fit the type: a `request_id` starting `DR-` (discount) or `CR-`
   (credit), a `ticket` for SLA; anything else is 422 naming `subject`;
2. DC-6: a live decision on the subject is refused with 409 and its id as `existing`;
3. the subject's row is read through the systems-of-record overlay. With no row, a discount or
   credit decision stands on the submitted figures when they name the customer, the product
   (discount) and the requested figure, and opens a `missing_record` condition; otherwise 404.
   Its requester is the session's person or the agent's principal, never a submitted
   `requestor` (ruling R22); a session that acts for nobody is 404 too;
4. `as_of`: the row's `request_date` (discount, credit), the service's date when the row is
   missing, the service clock for SLA. Never from the body (S23's trap);
5. the kernel runs outside any write transaction;
6. Jev unavailable, a kernel error, or a row or result the service can't put in the contract's
   terms: 503, a `decision.failed` event on the subject's stream, and no version (ruling R19);
7. the version's level, the subject's floor, the ratchet and the self-sourced-basis flags
   (`ratchet.assess`, spec §6.5-6.6), read from the subject's stream, which step 8 keeps current;
8. the write (`BEGIN IMMEDIATE`) re-checks DC-6 and the subject's last event, 409 if either
   moved, then takes the next `DEC-` id and appends `decision.versioned` with the whole version
   and its level.
The contract's `DecisionRequest` carries no principal, so there is none to compare with the
session's: an extra body field fails validation (422).

The people steps (spec §6.4), each `(actor, decision_id, body)` to the current `DecisionRecord`:
1. the rules first (`steps.py`): DC-1, DC-5 (409), a closed decision, then DC-2 to DC-4 together;
2. `resolve` and `rerun` re-run the decision: the row as it is now, version 1's `as_of` (for SLA,
   the kernel's `decided_at` is the clock now), the kernel outside any write transaction with the
   decision's id as its `sid`, a requester the row still names (else 503: the decision is its
   requester's), and version n+1 from `rerun.next_version`. A kernel that can't decide is 503 with
   a `decision.failed` event naming the decision, and nothing else written;
3. every write (`BEGIN IMMEDIATE`) re-checks that the version is still current (DC-5) and the
   subject's last event unchanged, 409 if either moved; a resolution appends `condition.resolved`
   then the `decision.versioned` it produced, a re-run `decision.rerun_requested` then the version,
   approving `decision.approved`, declining `decision.declined`, withdrawing `decision.withdrawn`.
Approvals bind to a version: a re-run's version starts with nothing given or declined.

Every decision event is appended to its subject's stream (`state.py` lists the payloads).
`submitted` is kept as sent and compared, never used (contract ground rule 5). `prepare.py` puts
the row (or the submitted figures) to the kernel and reads the basis; `assemble.py` maps the
result to the contract.
"""

from __future__ import annotations

import builtins
import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Final

from . import _lab, ratchet, steps
from .assemble import VersionContext, build_version
from .conditions import conflict_condition, input_conflicts, missing_record_condition
from .errors import CannotDecide, NotFound, Refused
from .events import Event, ExecutionRow
from .models import (
    Actor,
    ApprovalGiven,
    Basis,
    Condition,
    ConditionResolved,
    DecisionRecord,
    DecisionRequest,
    DecisionType,
    Declined,
    PersonRef,
    Previous,
    Refusal,
    RequestSubject,
    RerunRequest,
    ResolveRequest,
    StepRequest,
    Submitted,
    TicketSubject,
)
from .org import Org
from .prepare import PENDING, TABLE, Prepared, documents, prepare, principal, require_figures
from .rerun import Resolving, next_version, resolution_payload
from .state import decision_of, derive_state, is_live, subject_id, with_derived

PREFIX: Final[Mapping[DecisionType, str]] = {"discount": "DR-", "credit": "CR-"}
FILTERS: Final = frozenset({"decision_type", "subject", "state"})


def _dc6(subject: str, existing: str) -> Refused:
    return Refused(409, [Refusal(
        rule="DC-6", existing=existing,
        detail=f"{subject} already has a live decision. Re-run it, or withdraw it first; its "
               f"floor stays with {subject}.",
    )])  # fmt: skip


def _submitted(s: Submitted | None) -> dict[str, Any] | None:
    """The submission by §3.5 names, as sent; a null figure counts as not sent."""
    if s is None:
        return None
    return {k: v for k, v in s.model_dump(exclude_unset=True).items() if v is not None}


@dataclass(frozen=True)
class _Current:
    """A decision as a step reads it: the current version and what the write re-checks."""

    record: DecisionRecord  # the current version, with its derived fields
    events: list[Event]  # the decision's own events
    subject: str
    seen: int  # the subject's last seq when read


def _plain(x: Any) -> Any:
    """JSON-plain: dates as ISO strings, sets as lists. NaN refuses."""

    def default(o: Any) -> Any:
        if isinstance(o, date | datetime):
            return o.isoformat()
        if isinstance(o, set | frozenset):
            return sorted(o)
        raise TypeError(f"{type(o).__name__} is not JSON-serialisable")

    return json.loads(json.dumps(x, default=default, allow_nan=False))


class Decisions:
    def __init__(self, org: Org) -> None:
        self.org = org

    # -- asking -----------------------------------------------------------------------------
    def ask(self, actor: Actor, req: DecisionRequest) -> DecisionRecord:
        kind = req.decision_type
        sid = self._subject(kind, req)
        seen = self.org.log.last_seq(self.org.org_id, sid)
        existing = self._live(sid)
        if existing:
            raise _dc6(sid, existing)
        submitted = _submitted(req.submitted)
        requested_at = self.org.clock.now()
        row = self.org.sor.row(TABLE[kind], sid)
        if row is None:
            require_figures(kind, sid, submitted, actor)
        try:
            prep = prepare(self.org, kind, sid, row, submitted or {}, principal(actor),
                           requested_at)  # fmt: skip
        except Exception as e:  # noqa: BLE001 - R19: the row can't be put to the kernel
            raise self._failed(actor, kind, sid, f"inputs: {e}") from e
        kr = self._run(actor, kind, sid, prep)
        decided_at = self.org.clock.now()  # before the write: never first read inside one
        try:
            conditions = self._conditions(kind, sid, prep, submitted)
            rk = ratchet.assess(
                self.org, kind=kind, subject=sid, table=TABLE[kind], decision_id=PENDING,
                version=1, requester=prep.requester, figures=prep.figures,
                row=prep.inputs.get("record") or {}, authority=kr.record.get("authority"),
                as_of=date.fromisoformat(prep.as_of), requested_at=requested_at,
                cid=f"c{len(conditions) + 1}",
            )  # fmt: skip
            payload = self._payload(
                kind, kr, prep, submitted, actor=actor, requested_at=requested_at.isoformat(),
                decided_at=decided_at, decision_id=PENDING, version=1,
                conditions=[*conditions, *rk.conditions], rk=rk, previous=None,
            )  # fmt: skip
        except Exception as e:  # noqa: BLE001 - the result doesn't fit the contract
            raise self._failed(actor, kind, sid, f"result: {e}") from e
        return self.get(self._write(actor, sid, seen, payload, decided_at))

    def _subject(self, kind: DecisionType, req: DecisionRequest) -> str:
        """The subject's id, if it fits the decision type (Review Focus 4)."""
        s = req.subject
        shown = s.model_dump()
        if kind == "sla":
            if isinstance(s, TicketSubject) and s.ticket.strip():
                return s.ticket
            want = "an sla decision names a ticket"
        else:
            if isinstance(s, RequestSubject) and s.request_id.startswith(PREFIX[kind]):
                return s.request_id
            want = f"a {kind} decision names a request_id starting {PREFIX[kind]}"
        raise Refused(422, [Refusal(rule="DC-2", detail=f"subject: {want}, not {shown}")])

    def _run(
        self, actor: Actor, kind: DecisionType, sid: str, prep: Prepared, *,
        decision: tuple[str, int] | None = None,
    ) -> _lab.KernelResult:  # fmt: skip
        """The kernel, outside any write transaction. Jev unavailable or a kernel error is 503
        with a `decision.failed` event (ruling R19); a re-run's names its decision."""
        try:
            return self._decide(kind, prep)
        except _lab.JevUnavailable as e:
            raise self._failed(actor, kind, sid, f"Jev unavailable: {e}", decision) from e
        except CannotDecide as e:
            raise self._failed(actor, kind, sid, f"kernel: {e.detail}", decision) from e
        except Exception as e:  # noqa: BLE001 - the register or procedures couldn't be read
            raise self._failed(actor, kind, sid, f"kernel: {e}", decision) from e

    def _decide(self, kind: DecisionType, prep: Prepared) -> _lab.KernelResult:
        entries, store = self.org.procedures()
        return _lab.decide(
            kind, evidence=self.org.evidence, inputs=prep.inputs, at=prep.at,
            register=self.org.kernel_register(), entries=entries, store=store,
            engine=self.org.engine, staff=self.org.evidence.table("employees"),
            requested_by=prep.requester_email, policy_terms=self.org.policy_terms,
            route_mode=self.org.on_mismatch() == "route", specs=self.org.procedure_specs,
        )  # fmt: skip

    def _payload(
        self, kind: DecisionType, kr: _lab.KernelResult, prep: Prepared,
        submitted: Mapping[str, Any] | None, *, actor: Actor, requested_at: str,
        decided_at: datetime, decision_id: str, version: int, conditions: Sequence[Condition],
        rk: ratchet.Assessment, previous: Previous | None,
    ) -> dict[str, Any]:  # fmt: skip
        """The `decision.versioned` payload: the version's fixed fields, the kernel's record as
        it came back, the kernel's additions, and the version's level."""
        as_of = date.fromisoformat(prep.as_of)
        docs = documents(self.org, kr, as_of)
        records = [] if prep.basis is None else [prep.basis]
        named = prep.subject.model_dump(include={"request_id", "ticket", "account_id",
                                                 "customer_id"}, exclude_none=True)  # fmt: skip
        ctx = VersionContext(
            decision_id=decision_id, version=version, subject=prep.subject,
            submitted=None if submitted is None else Submitted.model_validate(submitted),
            requested_by=prep.requester, actor=actor, requested_at=requested_at,
            as_of=prep.as_of, decided_at=decided_at.isoformat(), figures=prep.figures,
            conditions=list(conditions), previous=previous,
            basis=Basis(records=records, documents=docs.basis),
            register_used=docs.register_used, people=self.org.people,
            known_ids=frozenset({d for _, d, _ in docs.prints} | set(docs.registered)
                                | set(named.values())),
            floor=None if rk.floor is None else rk.floor.model(), service_flags=rk.flags,
            revoked=ratchet.revoked_by(docs.registered.values(), as_of),
        )  # fmt: skip
        extra = {"judgment_about": kr.judgment_about, "flag_items": kr.flag_items,
                 "approval_roles": kr.approval_roles, "relied": kr.relied,
                 "relied_entries": kr.relied_entries}  # fmt: skip
        return {"version": build_version(kind, kr, ctx), "kernel": _plain(kr.record),
                "kernel_extra": _plain(extra), "level": rk.level_json()}  # fmt: skip

    def _conditions(
        self, kind: DecisionType, sid: str, prep: Prepared, submitted: dict[str, Any] | None
    ) -> builtins.list[Condition]:
        if kind == "sla":
            return []
        assert prep.requester is not None
        if prep.row is None:
            return [missing_record_condition("c1", kind, sid, submitted or {}, prep.requester, 1)]
        return [
            conflict_condition(f"c{i}", kind, sid, field, s, r, prep.requester, 1)
            for i, (field, s, r) in enumerate(input_conflicts(kind, submitted, prep.figures), 1)
        ]

    def _failed(
        self, actor: Actor, kind: DecisionType, sid: str, reason: str,
        decision: tuple[str, int] | None = None,
    ) -> CannotDecide:  # fmt: skip
        """Log a decision the kernel couldn't make (for the audit), and the 503 to raise. A
        failed re-run names its decision and the version it would have followed."""
        at = self.org.clock.now()
        payload: dict[str, Any] = {"decision_type": kind, "subject": sid, "reason": reason}
        if decision is not None:
            payload |= {"decision_id": decision[0], "version": decision[1]}
        with self.org.log.transaction() as tx:
            self.org.log.append(tx, at=at, org=self.org.org_id, stream=sid,
                                kind="decision.failed", actor=actor.model_dump(mode="json"),
                                payload=payload)  # fmt: skip
        return CannotDecide(reason)

    def _write(
        self, actor: Actor, sid: str, seen: int, payload: dict[str, Any], at: datetime
    ) -> str:
        """Version 1, if nothing moved on the subject while the kernel ran."""
        with self.org.log.transaction() as tx:
            existing = self._live(sid, tx)
            if existing:
                raise _dc6(sid, existing)
            if self.org.log.last_seq(self.org.org_id, sid, tx=tx) != seen:
                raise Refused(409, [Refusal(
                    rule="DC-6",
                    detail=f"{sid} changed while this decision was being made. Ask again.",
                )])  # fmt: skip
            did = self.org.log.next_id(tx, self.org.org_id, "DEC", 4)
            payload["version"]["decision_id"] = did
            floor = payload["version"]["floor"]
            if floor and floor["set_by"]["decision_id"] == PENDING:  # set by this version
                floor["set_by"]["decision_id"] = did
            self.org.log.append(tx, at=at, org=self.org.org_id, stream=sid,
                                kind="decision.versioned", actor=actor.model_dump(mode="json"),
                                payload=payload)  # fmt: skip
        return did

    # -- the people steps (spec §6.4) ---------------------------------------------------------
    def resolve(
        self, actor: Actor, decision_id: str, cid: str, body: ResolveRequest
    ) -> DecisionRecord:
        """Resolve one of the current version's conditions, which re-runs the decision."""
        me = steps.person(actor)
        cur = self._current(decision_id)
        rec = cur.record
        steps.current(rec, body.decision_version)
        steps.live(rec)
        c = steps.condition(rec, cid)
        steps.may_resolve(rec, me, c, body.resolution)
        resolved = ConditionResolved(by=me, at=self.org.clock.now().isoformat(),
                                     resolution=body.resolution, note=body.note,
                                     rerun_version=rec.version + 1)  # fmt: skip
        return self._rerun(actor, me, cur, Resolving(c, resolved))

    def rerun(self, actor: Actor, decision_id: str, body: RerunRequest) -> DecisionRecord:
        """Re-run the current version on the row as it is now: version n+1."""
        me = steps.person(actor)
        cur = self._current(decision_id)
        steps.current(cur.record, body.decision_version)
        steps.live(cur.record)
        steps.may_rerun(cur.record, me)
        return self._rerun(actor, me, cur, None)

    def approve(self, actor: Actor, decision_id: str, body: StepRequest) -> DecisionRecord:
        """Give the approval (or concurrence, or claim decision) that names the actor."""
        me = steps.person(actor)
        cur = self._current(decision_id)
        rec = cur.record
        steps.current(rec, body.decision_version)
        steps.live(rec)
        i = steps.may_approve(rec, me, declining=False, note=body.note)
        given = ApprovalGiven(by=me, at=self.org.clock.now().isoformat(), note=body.note)
        self._step(actor, cur, "decision.approved", {
            "decision_id": decision_id, "version": rec.version, "index": i,
            "given": given.model_dump(mode="json")})  # fmt: skip
        return self.get(decision_id)

    def decline(self, actor: Actor, decision_id: str, body: StepRequest) -> DecisionRecord:
        """Decline the approval that names the actor, with a note. The decision is then closed,
        and its floor stays with the subject."""
        me = steps.person(actor)
        cur = self._current(decision_id)
        rec = cur.record
        steps.current(rec, body.decision_version)
        steps.live(rec)
        i = steps.may_approve(rec, me, declining=True, note=body.note)
        declined = Declined(by=me, at=self.org.clock.now().isoformat(), note=str(body.note))
        self._step(actor, cur, "decision.declined", {
            "decision_id": decision_id, "version": rec.version, "index": i,
            "declined": declined.model_dump(mode="json")})  # fmt: skip
        return self.get(decision_id)

    def withdraw(self, actor: Actor, decision_id: str, body: StepRequest) -> DecisionRecord:
        """The requester withdraws a live decision. Its floor stays with the subject."""
        me = steps.person(actor)
        cur = self._current(decision_id)
        rec = cur.record
        steps.current(rec, body.decision_version)
        steps.live(rec)
        steps.may_withdraw(rec, me)
        self._step(actor, cur, "decision.withdrawn",
                   {"decision_id": decision_id, "version": rec.version})  # fmt: skip
        return self.get(decision_id)

    def _current(self, decision_id: str) -> _Current:
        first = self._first(decision_id)
        stream = self.org.log.read(self.org.org_id, stream=first.stream)
        mine = [e for e in stream if decision_of(e) == decision_id]
        fixed = self._version(mine, decision_id, None).payload["version"]
        record = DecisionRecord.model_validate(
            with_derived(fixed, mine, self._executions(first.stream), stream))  # fmt: skip
        return _Current(record, mine, first.stream, stream[-1].seq)

    def _recheck(self, tx: sqlite3.Connection, cur: _Current) -> None:
        """In the write: the version is still current (DC-5) and nothing else moved on the
        subject since the step read it (409 either way)."""
        if self.org.log.last_seq(self.org.org_id, cur.subject, tx=tx) == cur.seen:
            return
        did, n = cur.record.decision_id, cur.record.version
        now = max(e.payload["version"]["version"]
                  for e in self.org.log.read(self.org.org_id, stream=cur.subject, tx=tx)
                  if e.kind == "decision.versioned" and decision_of(e) == did)  # fmt: skip
        if now != n:
            detail = f"{did} moved to version {now} while this step was taken on version {n}."
        else:
            detail = f"{did} changed while this step was taken ({cur.subject}). Read it again."
        raise Refused(409, [Refusal(rule="DC-5", detail=detail)])

    def _step(self, actor: Actor, cur: _Current, kind: str, payload: dict[str, Any]) -> None:
        """One step's event, if nothing moved since the step read the decision."""
        at = self.org.clock.now()  # before the write: never first read inside one
        with self.org.log.transaction() as tx:
            self._recheck(tx, cur)
            self.org.log.append(tx, at=at, org=self.org.org_id, stream=cur.subject, kind=kind,
                                actor=actor.model_dump(mode="json"), payload=payload)  # fmt: skip

    def _rerun(
        self, actor: Actor, me: PersonRef, cur: _Current, resolving: Resolving | None
    ) -> DecisionRecord:
        """Spec §6.4: re-read the row, keep `as_of`, run the kernel outside the lock, carry the
        conditions forward, assess the floor, and write version n+1 with what changed."""
        rec, sid = cur.record, cur.subject
        kind, did, n = rec.decision_type, rec.decision_id, rec.version
        versions = [e.payload for e in cur.events if e.kind == "decision.versioned"]
        stored = next(v["version"] for v in versions if v["version"]["version"] == n)
        submitted: dict[str, Any] | None = stored.get("submitted")
        now = self.org.clock.now()
        try:
            prep = prepare(self.org, kind, sid, self.org.sor.row(TABLE[kind], sid),
                           submitted or {}, rec.requested_by, now,
                           as_of=date.fromisoformat(rec.as_of), kernel_sid=did)  # fmt: skip
            asker = rec.requested_by
            if asker is not None and (prep.requester is None or prep.requester.id != asker.id):
                named = prep.requester.name if prep.requester else "nobody"
                raise ValueError(f"the row now names {named} as the requester; {did} is "
                                 f"{asker.name}'s. Withdraw it and ask again.")  # fmt: skip
        except Exception as e:  # noqa: BLE001 - R19: the row can't be put to the kernel
            raise self._failed(actor, kind, sid, f"inputs: {e}", (did, n)) from e
        kr = self._run(actor, kind, sid, prep, decision=(did, n))
        decided_at = self.org.clock.now()
        try:
            nxt = next_version(
                self.org, rec, [v["version"] for v in versions],
                {int(v["version"]["version"]): v.get("level") for v in versions}, prep, kr,
                submitted, me, resolving, decided_at,
            )  # fmt: skip
            payload = self._payload(
                kind, kr, prep, submitted, actor=rec.actor, requested_at=rec.requested_at,
                decided_at=decided_at, decision_id=did, version=n + 1,
                conditions=nxt.conditions, rk=nxt.assessment,
                previous=Previous(version=n, what_changed=nxt.what_changed),
            )  # fmt: skip
        except Exception as e:  # noqa: BLE001 - the result doesn't fit the contract
            raise self._failed(actor, kind, sid, f"result: {e}", (did, n)) from e
        if resolving is not None:
            first = ("condition.resolved", resolution_payload(did, resolving))
        else:
            first = ("decision.rerun_requested", {"decision_id": did, "version": n})
        with self.org.log.transaction() as tx:
            self._recheck(tx, cur)
            for kind_, body in (first, ("decision.versioned", payload)):
                self.org.log.append(tx, at=decided_at, org=self.org.org_id, stream=sid,
                                    kind=kind_, actor=actor.model_dump(mode="json"),
                                    payload=body)  # fmt: skip
        return self.get(did)

    # -- the subject --------------------------------------------------------------------------
    def _executions(self, sid: str) -> builtins.list[ExecutionRow]:
        return [x for x in self.org.log.executions()
                if x.org == self.org.org_id and x.subject == sid]  # fmt: skip

    def _live(self, sid: str, tx: Any = None) -> str | None:
        """The subject's live decision, if it has one (DC-6)."""
        evs = self.org.log.read(self.org.org_id, stream=sid, tx=tx)
        latest: dict[str, dict[str, Any]] = {}
        for e in evs:
            if e.kind == "decision.versioned":
                latest[str(decision_of(e))] = e.payload["version"]
        executions = self._executions(sid)
        for did, version in latest.items():
            mine = [e for e in evs if decision_of(e) == did]
            if is_live(derive_state(version, mine, executions)):
                return did
        return None

    # -- reading ------------------------------------------------------------------------------
    def _first(self, decision_id: str) -> Event:
        """The decision's first `decision.versioned` event; its stream is the subject's."""
        first = next((e for e in self.org.log.read(self.org.org_id, kinds=("decision.versioned",))
                      if decision_of(e) == decision_id), None)  # fmt: skip
        if first is None:
            raise NotFound(f"decision {decision_id}")
        return first

    def _stream(self, decision_id: str) -> builtins.list[Event]:
        """The decision's subject's stream: its events and every other decision's on it."""
        return self.org.log.read(self.org.org_id, stream=self._first(decision_id).stream)

    def events(self, decision_id: str) -> builtins.list[Event]:
        """The decision's events, in order (its clearances' attempts are on its own stream)."""
        return [e for e in self._stream(decision_id) if decision_of(e) == decision_id]

    def _version(self, evs: builtins.list[Event], decision_id: str, version: int | None) -> Event:
        versions = [e for e in evs if e.kind == "decision.versioned"]
        found = versions[-1] if version is None else next(
            (e for e in versions if e.payload["version"]["version"] == version), None)  # fmt: skip
        if found is None:
            raise NotFound(f"decision {decision_id} version {version}")
        return found

    def get(self, decision_id: str, version: int | None = None) -> DecisionRecord:
        """A version (the current one by default), with its derived fields."""
        stream = self._stream(decision_id)
        evs = [e for e in stream if decision_of(e) == decision_id]
        fixed = self._version(evs, decision_id, version).payload["version"]
        executions = self._executions(subject_id(fixed["subject"]))
        return DecisionRecord.model_validate(with_derived(fixed, evs, executions, stream))

    def kernel_record(self, decision_id: str, version: int) -> dict[str, Any]:
        """The kernel's record for a version, exactly as it came back: for the acceptance check
        and the audit. Never served over the contract."""
        record: dict[str, Any] = self._version(self.events(decision_id), decision_id,
                                               version).payload["kernel"]  # fmt: skip
        return record

    def list(self, **filters: str) -> builtins.list[DecisionRecord]:
        """Every decision's current version, by id, filtered by `decision_type`, `subject` or
        `state`."""
        unknown = sorted(set(filters) - FILTERS)
        if unknown:
            raise ValueError(f"unknown filter: {', '.join(unknown)}")
        ids = sorted(
            {
                str(decision_of(e))
                for e in self.org.log.read(self.org.org_id, kinds=("decision.versioned",))
            }
        )
        out = []
        for did in ids:
            r = self.get(did)
            have = {"decision_type": r.decision_type, "state": r.state,
                    "subject": subject_id(r.subject.model_dump())}  # fmt: skip
            if all(have[k] == v for k, v in filters.items()):
                out.append(r)
        return out
