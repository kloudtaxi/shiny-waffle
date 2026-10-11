"""What the service adds to the kernel's record (spec §6.2): one version's fixed fields, in the
contract's shapes (`owm-decisions.ts` §5).

`build_version` maps the kernel's result and the service's context to the fields a version keeps
for good. What later events decide (`state`, `executed`, `resolved`, `given`, `declined`) is
derived on read (`state.py`). A kernel value that doesn't fit the contract fails validation here;
the fix is in this mapping, never in the kernel.

The mapping, by type:
- discount: `commercial_eligibility`, and `authority` with `approver` as a `PersonRef`;
- credit: `eligibility` (the kernel's `maximum_limit` is `maximum_limit_usd`), `authority` and
  `registered`;
- SLA: `scope`, `severity`, `breach`, `credit_usd`, `obligations` (a holder that is an employee id
  becomes a `PersonRef`; any other holder, such as `owner:CRM-2048`, is the deferred
  `holder_ref`) and `account_owner` as a `PersonRef`.
A withheld decision (G-32) empties its findings, keeping their types: an empty eligibility reads
as `unknown`, and an empty authority or breach as null.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, Final

from ._lab import ROUTE_TO, KernelResult
from .errors import NotFound
from .models import (
    AgentActor,
    ApprovalRequirement,
    Basis,
    BasisDocument,
    ChoiceJudgment,
    Condition,
    CreditFindings,
    DecidedAction,
    DecisionRecord,
    DecisionType,
    DiscountFindings,
    Flag,
    PersonActor,
    PersonRef,
    Previous,
    RegisterUsed,
    SlaFindings,
    Subject,
    Submitted,
    YesNoJudgment,
)
from .people import People

APPROVING: Final = frozenset({"APPROVE", "APPROVE_WITH_AUTHORIZATION"})
CREDIT_OWED: Final = "BREACH_CREDIT_OWED"
DERIVED: Final = ("state", "executed")  # top-level fields computed on read


@dataclass(frozen=True)
class VersionContext:
    """Everything the service knows about a version besides the kernel's result."""

    decision_id: str
    version: int
    subject: Subject
    submitted: Submitted | None
    requested_by: PersonRef | None
    actor: PersonActor | AgentActor
    requested_at: str
    as_of: str
    decided_at: str
    figures: Mapping[str, Any]  # the figures decided on, by §3.5 names, in contract units
    conditions: Sequence[Condition]
    basis: Basis
    register_used: Sequence[RegisterUsed]
    people: People
    known_ids: frozenset[str]  # the doc_ids and record ids a flag may name
    previous: Previous | None = None


# -- findings -----------------------------------------------------------------------------------
def _person(people: People, name: Any) -> dict[str, Any] | None:
    ref = people.by_name(str(name)) if name else None
    return ref.model_dump() if ref else None


def _employee(people: People, emp_id: Any) -> PersonRef | None:
    try:
        return people.ref(str(emp_id)) if emp_id else None
    except NotFound:
        return None


def _authority(raw: Mapping[str, Any] | None, people: People) -> dict[str, Any] | None:
    if not raw:
        return None
    return {
        "policy": raw.get("policy"),
        "requestor_limit": raw.get("requestor_limit"),
        "requestor_authorized": raw.get("requestor_authorized"),
        "required_role": raw.get("required_role"),
        "approver": _person(people, raw.get("approver")),
    }


def _obligation(o: Mapping[str, Any], people: People) -> dict[str, Any]:
    holder = o.get("holder")
    ref = _employee(people, holder)
    return {
        "party": o["party"],
        "duty": o["duty"],
        "role": o.get("role"),
        "holder": ref.model_dump() if ref else None,
        "holder_ref": None if ref or holder is None else str(holder),
        "due": o.get("due"),
        "status": o.get("status"),
    }


def findings(
    kind: DecisionType, record: Mapping[str, Any], people: People
) -> DiscountFindings | CreditFindings | SlaFindings:
    if kind == "discount":
        ce = record.get("commercial_eligibility") or {}
        return DiscountFindings.model_validate({
            "type": "discount",
            "commercial_eligibility": {"status": ce.get("status") or "unknown",
                                       "maximum_discount": ce.get("maximum_discount"),
                                       "basis": ce.get("basis")},
            "authority": _authority(record.get("authority"), people),
        })  # fmt: skip
    if kind == "credit":
        el = record.get("eligibility") or {}
        return CreditFindings.model_validate({
            "type": "credit",
            "eligibility": {"status": el.get("status") or "unknown",
                            "maximum_limit_usd": el.get("maximum_limit"),
                            "basis": el.get("basis")},
            "authority": _authority(record.get("authority"), people),
            "registered": list(record.get("registered") or []),
        })  # fmt: skip
    return SlaFindings.model_validate({
        "type": "sla",
        "scope": record.get("scope"),
        "severity": record.get("severity"),
        "breach": record.get("breach") or None,
        "credit_usd": record.get("credit_usd"),
        "obligations": [_obligation(o, people) for o in record.get("obligations") or []],
        "account_owner": _person(people, record.get("account_owner")),
    })  # fmt: skip


# -- judgments, flags ---------------------------------------------------------------------------
def judgments(
    record: Mapping[str, Any], about: Sequence[str | None]
) -> list[ChoiceJudgment | YesNoJudgment]:
    """The kernel's judgments with what each is about; the form follows the judgment's shape (a
    `yes` answer, with the kernel's `noul` as `p_yes`, or a choice)."""
    out: list[ChoiceJudgment | YesNoJudgment] = []
    for i, j in enumerate(record.get("judgments") or []):
        a = about[i] if i < len(about) else None
        if "yes" in j:
            out.append(YesNoJudgment.model_validate({
                "q": j["q"], "about": a, "form": "yes_no", "yes": j["yes"], "p_yes": j["noul"],
                "uncertain": j["uncertain"]}))  # fmt: skip
        else:
            out.append(ChoiceJudgment.model_validate({
                "q": j["q"], "about": a, "form": "choice", "choice": j["choice"],
                "probabilities": j["probabilities"], "confidence": j["confidence"],
                "uncertain": j["uncertain"]}))  # fmt: skip
    return out


def flag_about(text: str, known: Iterable[str]) -> list[str]:
    """The known ids a flag's text names as whole ids, in the order the text names them."""
    hits = []
    for k in set(known):
        m = re.search(rf"(?<![\w.-]){re.escape(k)}(?![\w-]|\.\w)", text)
        if m:
            hits.append((m.start(), k))
    return [k for _, k in sorted(hits)]


def flags(items: Sequence[Mapping[str, Any]], known: Iterable[str]) -> list[Flag]:
    """The kernel's flag items (`{code, text, routes}`), each with the ids it names."""
    ids = frozenset(known)
    return [
        Flag.model_validate({"code": i["code"], "text": i["text"], "routes": i["routes"],
                             "about": flag_about(str(i["text"]), ids)})
        for i in items
    ]  # fmt: skip


# -- approvals, actions -------------------------------------------------------------------------
def approvals(roles: Sequence[Mapping[str, Any]], people: People) -> list[ApprovalRequirement]:
    """The kernel's approval roles as people. `expected_actor` is not an approval: it names who
    the decision expects to act (`actions`)."""
    out = []
    for r in roles:
        if r["kind"] == "expected_actor":
            continue
        pf = r.get("passed_from")
        out.append(ApprovalRequirement.model_validate({
            "kind": r["kind"],
            "role": r["role"],
            "person": people.ref(str(r["person_id"])).model_dump(),
            "passed_from": {"person": people.ref(str(pf["person_id"])).model_dump(),
                            "reason": pf["reason"]} if pf else None,
            "given": None,
            "declined": None,
        }))  # fmt: skip
    return out


def actions(
    kind: DecisionType, record: Mapping[str, Any], subject: Subject, figures: Mapping[str, Any],
    roles: Sequence[Mapping[str, Any]], people: People,
) -> list[DecidedAction]:  # fmt: skip
    """What the outcome decides (§5.9): an approving outcome applies the discount or sets the
    limit on the record's figure; a credit owed issues it, expected from the `issue_memo`
    holder. Any other outcome decides no action."""
    outcome = record.get("gated_outcome")
    expected = None
    if kind == "discount" and outcome in APPROVING:
        name, params = "apply_discount", {
            "request_id": subject.request_id, "account_id": subject.account_id,
            "product": subject.product, "discount": figures["requested_discount"]}  # fmt: skip
    elif kind == "credit" and outcome in APPROVING:
        name, params = "set_credit_limit", {
            "request_id": subject.request_id, "customer_id": subject.customer_id,
            "limit_usd": figures["requested_limit_usd"]}  # fmt: skip
    elif kind == "sla" and outcome == CREDIT_OWED:
        name, params = "issue_service_credit", {
            "ticket": subject.ticket, "account_id": subject.account_id,
            "amount_usd": record["credit_usd"]}  # fmt: skip
        holder = next((r for r in roles if r["kind"] == "expected_actor"), None)
        expected = people.ref(str(holder["person_id"])).model_dump() if holder else None
    else:
        return []
    return [DecidedAction.model_validate(
        {"action": name, "params": params, "expected_actor": expected})]  # fmt: skip


# -- basis --------------------------------------------------------------------------------------
Prints = Sequence[tuple[str, str, str]]  # (filename, doc_id, fingerprint) of each corpus document


def basis_documents(
    relied: Sequence[tuple[str, str]], registered: Mapping[str, Mapping[str, Any]], prints: Prints
) -> list[BasisDocument]:
    """The documents the decision relied on, once each (the kernel can list one twice), in the
    kernel's order: a registered one with its registered sha256, any other with its copy's."""
    by_file = {(f, d): p for f, d, p in prints}
    out: list[BasisDocument] = []
    for filename, doc_id in relied:
        if any(x.doc_id == doc_id for x in out):
            continue
        entry = registered.get(doc_id)
        sha = str(entry["sha256"]) if entry else by_file.get((filename, doc_id), "")
        out.append(BasisDocument(doc_id=doc_id, sha256=sha, registered=entry is not None))
    return out


def register_used(
    documents: Sequence[BasisDocument], registered: Mapping[str, Mapping[str, Any]],
    prints: Prints, as_of: date,
) -> list[RegisterUsed]:  # fmt: skip
    """The registered documents among those relied on: revoked when the register shows it revoked
    on or before `as_of`, and whether a copy on file matches the registered version."""
    on_file: dict[str, set[str]] = {}
    for _, doc_id, sha in prints:
        on_file.setdefault(doc_id, set()).add(sha)
    out: list[RegisterUsed] = []
    for d in documents:
        entry = registered.get(d.doc_id)
        if entry is None:
            continue
        revoked = entry.get("revoked_on")
        gone = bool(revoked) and date.fromisoformat(str(revoked)) <= as_of
        out.append(RegisterUsed(
            doc_id=d.doc_id, sha256=str(entry["sha256"]), status="revoked" if gone else "in_force",
            file_matches=str(entry["sha256"]) in on_file.get(d.doc_id, set()),
        ))  # fmt: skip
    return out


# -- the version --------------------------------------------------------------------------------
def build_version(kind: DecisionType, kr: KernelResult, ctx: VersionContext) -> dict[str, Any]:
    """A version's fixed fields as the contract's JSON (absent `?:` fields stay absent). It is
    validated as a whole `DecisionRecord`; the derived fields are left out."""
    r = kr.record
    proc = r["procedure"]
    routed = r["gated_outcome"] == ROUTE_TO[kind] and r.get("outcome") != r["gated_outcome"]
    whole = DecisionRecord.model_validate({
        "decision_id": ctx.decision_id,
        "version": ctx.version,
        "decision_type": kind,
        "subject": ctx.subject,
        "submitted": ctx.submitted,
        "requested_by": ctx.requested_by,
        "actor": ctx.actor,
        "requested_at": ctx.requested_at,
        "as_of": ctx.as_of,
        "decided_at": ctx.decided_at,
        "decided_by": {"kind": "owm",
                       "procedure": {"id": proc["id"], "version": proc["version"],
                                     "sha256": proc["sha256"]},
                       "judgments": len(r.get("judgments") or []),
                       "uncertain": len(r.get("uncertain") or [])},
        "outcome": r.get("outcome"),
        "gated_outcome": r["gated_outcome"],
        "routed": routed,
        "findings": findings(kind, r, ctx.people),
        "judgments": judgments(r, kr.judgment_about),
        "flags": flags(kr.flag_items, ctx.known_ids),
        "conditions": list(ctx.conditions),
        "approvals": approvals(kr.approval_roles, ctx.people),
        "actions": actions(kind, r, ctx.subject, ctx.figures, kr.approval_roles, ctx.people),
        "state": "no_action",  # a placeholder: derived on read
        "basis": ctx.basis,
        "register_used": list(ctx.register_used),
        "floor": None,
        "executed": [],  # derived on read
        "previous": ctx.previous,
    })  # fmt: skip
    out = whole.model_dump(mode="json", exclude_unset=True)
    for k in DERIVED:
        del out[k]
    return out
