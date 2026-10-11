"""The decision lifecycle (spec §6): asking, which makes version 1, and reading decisions back.

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
7. the write (`BEGIN IMMEDIATE`) re-checks DC-6 and the subject's last event, 409 if either
   moved, then takes the next `DEC-` id and appends `decision.versioned` with the whole version.
The contract's `DecisionRequest` carries no principal, so there is none to compare with the
session's: an extra body field fails validation (422).

Every decision event is appended to its subject's stream (`state.py` lists the payloads).
`submitted` is kept as sent and compared, never used (contract ground rule 5).
"""

from __future__ import annotations

import builtins
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Final

from . import _lab
from .assemble import VersionContext, basis_documents, build_version, register_used
from .conditions import (
    NUMBERS,
    SYSTEM,
    conflict_condition,
    input_conflicts,
    missing_record_condition,
)
from .errors import CannotDecide, NotFound, Refused
from .events import Event, ExecutionRow
from .models import (
    Actor,
    Basis,
    BasisRecord,
    Condition,
    DecisionRecord,
    DecisionRequest,
    DecisionType,
    LastChanged,
    PersonActor,
    PersonRef,
    Refusal,
    RequestSubject,
    Subject,
    Submitted,
    TicketSubject,
)
from .org import Org
from .sor import basis_columns, contract_view
from .state import decision_of, derive_state, is_live, subject_id, with_derived

TABLE: Final[Mapping[DecisionType, str]] = {
    "discount": "discount_requests", "credit": "credit_requests", "sla": "service_tickets",
}  # fmt: skip
SOURCE: Final[Mapping[DecisionType, str]] = {"discount": "crm", "credit": "erp", "sla": "service"}
PREFIX: Final[Mapping[DecisionType, str]] = {"discount": "DR-", "credit": "CR-"}
# what the kernel needs from a submission when the system of record has no row
NEEDS: Final[Mapping[DecisionType, tuple[str, ...]]] = {
    "discount": ("customer", "product", "requested_discount"),
    "credit": ("customer", "requested_limit_usd"),
}
EVENTS: Final = "events"  # the SLA basis field: a digest of the ticket's events (ruling R17)
PENDING: Final = "pending"  # the kernel's sid: it only fills the record's `scenario`
FILTERS: Final = frozenset({"decision_type", "subject", "state"})


@dataclass(frozen=True)
class _Prepared:
    """What the kernel is asked, and what the version keeps of the row."""

    subject: Subject
    inputs: dict[str, Any]
    at: date | datetime
    as_of: str
    requester: PersonRef | None
    requester_email: str | None
    figures: dict[str, Any]  # the figures decided on, by §3.5 names, in contract units
    row: dict[str, str] | None
    basis: BasisRecord | None  # read with the row, so it is what the kernel was given


def _dc6(subject: str, existing: str) -> Refused:
    return Refused(409, [Refusal(
        rule="DC-6", existing=existing,
        detail=f"{subject} already has a live decision. Re-run it, or withdraw it first; its "
               f"floor stays with {subject}.",
    )])  # fmt: skip


def _number_text(x: Any) -> str:
    f = float(x)
    return str(int(f)) if f.is_integer() else repr(f)


def _submitted(s: Submitted | None) -> dict[str, Any] | None:
    """The submission by §3.5 names, as sent; a null figure counts as not sent."""
    if s is None:
        return None
    return {k: v for k, v in s.model_dump(exclude_unset=True).items() if v is not None}


def _principal(actor: Actor) -> PersonRef | None:
    """The person a session acts as: its own person, or the agent's principal (ruling R22)."""
    return actor.person if isinstance(actor, PersonActor) else actor.on_behalf_of


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
            self._require_figures(kind, sid, submitted, actor)
        try:
            prep = self._prepare(kind, sid, row, submitted or {}, actor, requested_at)
        except Exception as e:  # noqa: BLE001 - R19: the row can't be put to the kernel
            raise self._failed(actor, kind, sid, f"inputs: {e}") from e
        try:
            kr = self._decide(kind, prep)
        except _lab.JevUnavailable as e:
            raise self._failed(actor, kind, sid, f"Jev unavailable: {e}") from e
        except CannotDecide as e:
            raise self._failed(actor, kind, sid, f"kernel: {e.detail}") from e
        except Exception as e:  # noqa: BLE001 - the register or procedures couldn't be read
            raise self._failed(actor, kind, sid, f"kernel: {e}") from e
        decided_at = self.org.clock.now()  # before the write: never first read inside one
        try:
            payload = self._payload(kind, sid, kr, prep, submitted, actor, requested_at,
                                    decided_at)  # fmt: skip
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

    def _require_figures(
        self, kind: DecisionType, sid: str, submitted: dict[str, Any] | None, actor: Actor
    ) -> None:
        """A subject the system of record doesn't hold is 404 unless the submission names what
        the kernel needs (Review Focus 1) and the session acts for a person, who stands as the
        requester (ruling R22). SLA can't decide on a submission."""
        if kind == "sla":
            raise NotFound(f"{sid}: no such ticket")
        lacking = [f for f in NEEDS[kind] if (submitted or {}).get(f) in (None, "")]
        if lacking:
            raise NotFound(f"{sid}: {SYSTEM[kind]} has no such request, and the submission "
                           f"doesn't give {', '.join(lacking)}")  # fmt: skip
        if _principal(actor) is None:
            raise NotFound(f"{sid}: {SYSTEM[kind]} has no such request, and this session acts "
                           "for nobody who could stand as its requester")  # fmt: skip

    def _prepare(
        self, kind: DecisionType, sid: str, row: dict[str, str] | None,
        submitted: dict[str, Any], actor: Actor, now: datetime,
    ) -> _Prepared:  # fmt: skip
        if kind == "sla":
            assert row is not None
            subject = Subject(ticket=sid, account_id=row["account_id"], product=row["product_sku"])
            return _Prepared(subject, {"sid": PENDING, "ticket_id": sid, "decided_at": now}, now,
                             now.date().isoformat(), None, None, {}, row,
                             self._basis_record(kind, sid, row, now))  # fmt: skip
        if row is not None:
            figures = contract_view(kind, row, self.org.people)
            as_of = date.fromisoformat(row["request_date"])
            email = row["requested_by"]
            requester = self.org.people.by_email(email) if email else None
            if requester is None:
                raise ValueError(f"the requester {email!r} is not in the HR export")
            record = {k: str(v) for k, v in row.items()}
        else:
            requester = _principal(actor)  # never the body's `requestor` (ruling R22)
            if requester is None:
                raise ValueError("no requester: the session acts for nobody")
            email = self._email(requester.id)
            as_of = now.date()
            figures = {k: float(v) if k in NUMBERS else str(v) for k, v in submitted.items()}
            record = self._record(kind, sid, submitted, email, as_of)
        if kind == "discount":
            subject = Subject(request_id=sid, account_id=str(figures["customer"]),
                              product=str(figures["product"]))  # fmt: skip
        else:
            subject = Subject(request_id=sid, customer_id=str(figures["customer"]))
        inputs = {"sid": PENDING, "record": record, "as_of": as_of}
        basis = None if row is None else self._basis_record(kind, sid, row, now)
        return _Prepared(subject, inputs, as_of, as_of.isoformat(), requester, email, figures, row,
                         basis)  # fmt: skip

    def _email(self, emp_id: str) -> str:
        found = next((r["email"] for r in self.org.evidence.table("employees")
                      if r["employee_id"] == emp_id), None)  # fmt: skip
        if not found:
            raise ValueError(f"{emp_id} has no email in the HR export")
        return str(found)

    def _record(
        self, kind: DecisionType, sid: str, submitted: dict[str, Any], email: str, as_of: date
    ) -> dict[str, str]:
        """The row the kernel reads when the system of record has none: the submitted figures,
        in the system's own columns."""
        common = {"request_id": sid, "requested_by": email, "request_date": as_of.isoformat(),
                  "justification": "", "status": str(submitted.get("status") or "")}  # fmt: skip
        if kind == "discount":
            pct = _number_text(round(float(submitted["requested_discount"]) * 100, 9))
            return {
                **common,
                "account_id": str(submitted["customer"]),
                "product_sku": str(submitted["product"]),
                "requested_discount_pct": pct,
            }
        current = submitted.get("current_limit_usd")
        return {
            **common,
            "erp_customer_id": str(submitted["customer"]),
            "requested_limit_usd": _number_text(submitted["requested_limit_usd"]),
            "current_limit_usd": "" if current is None else _number_text(current),
        }

    def _decide(self, kind: DecisionType, prep: _Prepared) -> _lab.KernelResult:
        entries, store = self.org.procedures()
        return _lab.decide(
            kind, evidence=self.org.evidence, inputs=prep.inputs, at=prep.at,
            register=self.org.kernel_register(), entries=entries, store=store,
            engine=self.org.engine, staff=self.org.evidence.table("employees"),
            requested_by=prep.requester_email, policy_terms=self.org.policy_terms,
            route_mode=self.org.on_mismatch() == "route",
        )  # fmt: skip

    def _payload(
        self, kind: DecisionType, sid: str, kr: _lab.KernelResult, prep: _Prepared,
        submitted: dict[str, Any] | None, actor: Actor, requested_at: datetime,
        decided_at: datetime,
    ) -> dict[str, Any]:  # fmt: skip
        """The `decision.versioned` payload: the version's fixed fields, the kernel's record as
        it came back, and the kernel's additions."""
        registered = {str(e["doc_id"]): e for e in self.org.register_state().entries}
        prints = _lab.doc_prints(self.org.evidence)
        documents = basis_documents(kr.relied, registered, prints, kr.relied_entries)
        records = [] if prep.basis is None else [prep.basis]
        named = prep.subject.model_dump(include={"request_id", "ticket", "account_id",
                                                 "customer_id"}, exclude_none=True)  # fmt: skip
        ctx = VersionContext(
            decision_id=PENDING, version=1, subject=prep.subject,
            submitted=None if submitted is None else Submitted.model_validate(submitted),
            requested_by=prep.requester, actor=actor, requested_at=requested_at.isoformat(),
            as_of=prep.as_of, decided_at=decided_at.isoformat(), figures=prep.figures,
            conditions=self._conditions(kind, sid, prep, submitted),
            basis=Basis(records=records, documents=documents),
            register_used=register_used(documents, registered, prints,
                                        date.fromisoformat(prep.as_of)),
            people=self.org.people,
            known_ids=frozenset({d for _, d, _ in prints} | set(registered) | set(named.values())),
        )  # fmt: skip
        extra = {"judgment_about": kr.judgment_about, "flag_items": kr.flag_items,
                 "approval_roles": kr.approval_roles, "relied": kr.relied,
                 "relied_entries": kr.relied_entries}  # fmt: skip
        return {"version": build_version(kind, kr, ctx), "kernel": _plain(kr.record),
                "kernel_extra": _plain(extra)}  # fmt: skip

    def _conditions(
        self, kind: DecisionType, sid: str, prep: _Prepared, submitted: dict[str, Any] | None
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

    def _basis_record(
        self, kind: DecisionType, sid: str, row: dict[str, str], read_at: datetime
    ) -> BasisRecord:
        """The row's basis columns as read, raw (§3.5 maps them), and its last recorded edit."""
        cols = basis_columns(kind, row)
        fields = {c: self._events_digest(sid) if kind == "sla" and c == EVENTS else row.get(c, "")
                  for c in cols}  # fmt: skip
        edits = [e for e in self.org.sor.edits(TABLE[kind], sid) if e.payload["field"] in cols]
        last = edits[-1] if edits else None
        return BasisRecord(
            system=SOURCE[kind], table=TABLE[kind], id=sid, fields=fields,
            read_at=read_at.isoformat(),
            last_changed=LastChanged(by=self._editor(last.actor), at=last.at.isoformat())
            if last else None,
        )  # fmt: skip

    def _events_digest(self, ticket: str) -> str:
        """Ruling R17: sha256 of the ticket's `ticket_events` rows, in table order."""
        rows = [r for r in self.org.sor.table("ticket_events") if r.get("ticket_id") == ticket]
        return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()

    def _editor(self, actor: dict[str, Any] | None) -> PersonRef | None:
        """The person behind a systems-of-record edit, where the edit names one."""
        try:
            if not actor:
                return None
            if isinstance(actor.get("person"), dict):
                return PersonRef.model_validate(actor["person"])
            if isinstance(actor.get("on_behalf_of"), dict):
                return PersonRef.model_validate(actor["on_behalf_of"])
            if actor.get("kind") == "person" and actor.get("id"):
                return self.org.people.ref(str(actor["id"]))
        except (NotFound, ValueError):
            return None
        return None

    def _failed(self, actor: Actor, kind: DecisionType, sid: str, reason: str) -> CannotDecide:
        """Log a decision the kernel couldn't make (for the audit), and the 503 to raise."""
        at = self.org.clock.now()
        with self.org.log.transaction() as tx:
            self.org.log.append(tx, at=at, org=self.org.org_id, stream=sid,
                                kind="decision.failed", actor=actor.model_dump(mode="json"),
                                payload={"decision_type": kind, "subject": sid,
                                         "reason": reason})  # fmt: skip
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
            self.org.log.append(tx, at=at, org=self.org.org_id, stream=sid,
                                kind="decision.versioned", actor=actor.model_dump(mode="json"),
                                payload=payload)  # fmt: skip
        return did

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
    def events(self, decision_id: str) -> builtins.list[Event]:
        """The decision's events, in order."""
        first = next((e for e in self.org.log.read(self.org.org_id, kinds=("decision.versioned",))
                      if decision_of(e) == decision_id), None)  # fmt: skip
        if first is None:
            raise NotFound(f"decision {decision_id}")
        evs = self.org.log.read(self.org.org_id, stream=first.stream)
        return [e for e in evs if decision_of(e) == decision_id]

    def _version(self, evs: builtins.list[Event], decision_id: str, version: int | None) -> Event:
        versions = [e for e in evs if e.kind == "decision.versioned"]
        found = versions[-1] if version is None else next(
            (e for e in versions if e.payload["version"]["version"] == version), None)  # fmt: skip
        if found is None:
            raise NotFound(f"decision {decision_id} version {version}")
        return found

    def get(self, decision_id: str, version: int | None = None) -> DecisionRecord:
        """A version (the current one by default), with its derived fields."""
        evs = self.events(decision_id)
        fixed = self._version(evs, decision_id, version).payload["version"]
        executions = self._executions(subject_id(fixed["subject"]))
        return DecisionRecord.model_validate(with_derived(fixed, evs, executions))

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
