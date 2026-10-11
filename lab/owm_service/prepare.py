"""What the kernel is asked, and what a version keeps of the row (spec §6.1-6.2).

- **The kernel's inputs** come from the subject's row, read through the systems-of-record overlay:
  discount and credit get `sid`, `record` and `as_of` (the row's `request_date`); SLA gets `sid`,
  `ticket_id` and `decided_at` (the service clock).
- **Missing-row synthesis.** With no row, a discount or credit decision stands on the submitted
  figures when they name what the kernel needs (`NEEDS`): the record the kernel reads is built
  from them, in the system's own columns, dated the service's day. Its requester is the session's
  person or the agent's principal, never a submitted `requestor` (ruling R22).
- **The basis.** The row's basis columns as read with the row, raw (§3.5 maps them), with the last
  recorded edit of one of them; for SLA the ticket's events are a digest (ruling R17). The
  documents are the kernel's trace (`assemble.basis_documents`, `assemble.register_used`).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Final

from . import _lab
from .assemble import basis_documents, register_used
from .conditions import NUMBERS, SYSTEM
from .errors import NotFound
from .models import (
    Actor,
    BasisDocument,
    BasisRecord,
    DecisionType,
    LastChanged,
    PersonActor,
    PersonRef,
    RegisterUsed,
    Subject,
)
from .org import Org
from .sor import basis_columns, contract_view

TABLE: Final[Mapping[DecisionType, str]] = {
    "discount": "discount_requests", "credit": "credit_requests", "sla": "service_tickets",
}  # fmt: skip
SOURCE: Final[Mapping[DecisionType, str]] = {"discount": "crm", "credit": "erp", "sla": "service"}
# what the kernel needs from a submission when the system of record has no row
NEEDS: Final[Mapping[DecisionType, tuple[str, ...]]] = {
    "discount": ("customer", "product", "requested_discount"),
    "credit": ("customer", "requested_limit_usd"),
}
EVENTS: Final = "events"  # the SLA basis field: a digest of the ticket's events (ruling R17)
PENDING: Final = "pending"  # the kernel's sid: it only fills the record's `scenario`


@dataclass(frozen=True)
class Prepared:
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


def principal(actor: Actor) -> PersonRef | None:
    """The person a session acts as: its own person, or the agent's principal (ruling R22)."""
    return actor.person if isinstance(actor, PersonActor) else actor.on_behalf_of


def number_text(x: Any) -> str:
    f = float(x)
    return str(int(f)) if f.is_integer() else repr(f)


# -- missing-row synthesis ------------------------------------------------------------------------
def require_figures(
    kind: DecisionType, sid: str, submitted: dict[str, Any] | None, actor: Actor
) -> None:
    """A subject the system of record doesn't hold is 404 unless the submission names what the
    kernel needs (Review Focus 1) and the session acts for a person, who stands as the requester
    (ruling R22). SLA can't decide on a submission."""
    if kind == "sla":
        raise NotFound(f"{sid}: no such ticket")
    lacking = [f for f in NEEDS[kind] if (submitted or {}).get(f) in (None, "")]
    if lacking:
        raise NotFound(f"{sid}: {SYSTEM[kind]} has no such request, and the submission "
                       f"doesn't give {', '.join(lacking)}")  # fmt: skip
    if principal(actor) is None:
        raise NotFound(f"{sid}: {SYSTEM[kind]} has no such request, and this session acts "
                       "for nobody who could stand as its requester")  # fmt: skip


def email_of(org: Org, emp_id: str) -> str:
    found = next((r["email"] for r in org.evidence.table("employees")
                  if r["employee_id"] == emp_id), None)  # fmt: skip
    if not found:
        raise ValueError(f"{emp_id} has no email in the HR export")
    return str(found)


def synthesized_row(
    kind: DecisionType, sid: str, submitted: Mapping[str, Any], email: str, as_of: date
) -> dict[str, str]:
    """The row the kernel reads when the system of record has none: the submitted figures, in
    the system's own columns."""
    common = {"request_id": sid, "requested_by": email, "request_date": as_of.isoformat(),
              "justification": "", "status": str(submitted.get("status") or "")}  # fmt: skip
    if kind == "discount":
        pct = number_text(round(float(submitted["requested_discount"]) * 100, 9))
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
        "requested_limit_usd": number_text(submitted["requested_limit_usd"]),
        "current_limit_usd": "" if current is None else number_text(current),
    }


# -- the kernel's inputs --------------------------------------------------------------------------
def prepare(
    org: Org, kind: DecisionType, sid: str, row: dict[str, str] | None,
    submitted: Mapping[str, Any], standing: PersonRef | None, now: datetime, *,
    as_of: date | None = None, kernel_sid: str = PENDING,
) -> Prepared:  # fmt: skip
    """The kernel's inputs for the subject's row (or, with no row, the submitted figures), and what
    the version keeps of it. Any failure here is the caller's 503 (ruling R19).

    `standing` is who stands as the requester when the system of record has no row: the session's
    person or the agent's principal when asking (ruling R22), the decision's requester on a
    re-run; never a submitted `requestor`. A re-run keeps version 1's `as_of` (S23's trap) and
    gives the kernel the decision's id as its `sid`; SLA's `decided_at` is always `now`."""
    if kind == "sla":
        assert row is not None
        subject = Subject(ticket=sid, account_id=row["account_id"], product=row["product_sku"])
        return Prepared(subject, {"sid": kernel_sid, "ticket_id": sid, "decided_at": now}, now,
                        (as_of or now.date()).isoformat(), None, None, {}, row,
                        basis_record(org, kind, sid, row, now))  # fmt: skip
    if row is not None:
        figures = contract_view(kind, row, org.people)
        on = as_of or date.fromisoformat(row["request_date"])
        email = row["requested_by"]
        requester = org.people.by_email(email) if email else None
        if requester is None:
            raise ValueError(f"the requester {email!r} is not in the HR export")
        record = {k: str(v) for k, v in row.items()}
    else:
        requester = standing
        if requester is None:
            raise ValueError("no requester: the session acts for nobody")
        email = email_of(org, requester.id)
        on = as_of or now.date()
        figures = {k: float(v) if k in NUMBERS else str(v) for k, v in submitted.items()}
        record = synthesized_row(kind, sid, submitted, email, on)
    if kind == "discount":
        subject = Subject(request_id=sid, account_id=str(figures["customer"]),
                          product=str(figures["product"]))  # fmt: skip
    else:
        subject = Subject(request_id=sid, customer_id=str(figures["customer"]))
    inputs = {"sid": kernel_sid, "record": record, "as_of": on}
    basis = None if row is None else basis_record(org, kind, sid, row, now)
    return Prepared(subject, inputs, on, on.isoformat(), requester, email, figures, row,
                    basis)  # fmt: skip


# -- the basis ------------------------------------------------------------------------------------
def basis_record(
    org: Org, kind: DecisionType, sid: str, row: dict[str, str], read_at: datetime
) -> BasisRecord:
    """The row's basis columns as read, raw (§3.5 maps them), and its last recorded edit."""
    cols = basis_columns(kind, row)
    fields = {c: events_digest(org, sid) if kind == "sla" and c == EVENTS else row.get(c, "")
              for c in cols}  # fmt: skip
    edits = [e for e in org.sor.edits(TABLE[kind], sid) if e.payload["field"] in cols]
    last = edits[-1] if edits else None
    return BasisRecord(
        system=SOURCE[kind], table=TABLE[kind], id=sid, fields=fields,
        read_at=read_at.isoformat(),
        last_changed=LastChanged(by=editor(org, last.actor), at=last.at.isoformat())
        if last else None,
    )  # fmt: skip


def events_digest(org: Org, ticket: str) -> str:
    """Ruling R17: sha256 of the ticket's `ticket_events` rows, in table order."""
    rows = [r for r in org.sor.table("ticket_events") if r.get("ticket_id") == ticket]
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def editor(org: Org, actor: dict[str, Any] | None) -> PersonRef | None:
    """The person behind a systems-of-record edit, where the edit names one."""
    try:
        if not actor:
            return None
        if isinstance(actor.get("person"), dict):
            return PersonRef.model_validate(actor["person"])
        if isinstance(actor.get("on_behalf_of"), dict):
            return PersonRef.model_validate(actor["on_behalf_of"])
        if actor.get("kind") == "person" and actor.get("id"):
            return org.people.ref(str(actor["id"]))
    except (NotFound, ValueError):
        return None
    return None


@dataclass(frozen=True)
class Documents:
    """What the kernel's trace relied on, against the register as it stands."""

    basis: list[BasisDocument]
    register_used: list[RegisterUsed]
    registered: dict[str, Mapping[str, Any]]  # doc_id -> register entry
    prints: list[tuple[str, str, str]]  # (filename, doc_id, fingerprint) of each corpus document


def documents(org: Org, kr: _lab.KernelResult, as_of: date) -> Documents:
    """The documents the decision relied on (`basis.documents`) and the registered ones among
    them (`register_used`), with the register and the corpus fingerprints they were read from."""
    registered = {str(e["doc_id"]): e for e in org.register_state().entries}
    prints = _lab.doc_prints(org.evidence)
    docs = basis_documents(kr.relied, registered, prints, kr.relied_entries)
    return Documents(docs, register_used(docs, registered, prints, as_of), registered, prints)
