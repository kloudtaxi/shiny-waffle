"""Kernel additions for the OWM service (B-06, `docs/superpowers/plans/2026-10-11-owm-service.md`,
Task 1; contract v1.2 §12.1 items 4 and 5).

New functions only. Nothing here changes a record the kernel returns: the service calls them beside
`governed.decide`, so every record the lab's harnesses produce stays byte-identical.
- `capture` and `judgment_about`: what each judgment is about (a document, a role, or the
  decision's subject), recorded beside the judgment by `kernel.judge` and never sent to Jev;
- `flag_items`: each flag string as `{code, text, routes}`, by the contract's §5.5 table.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import kernel


@dataclass
class Capture:
    """What each judgment made during a capture is about, keyed by the judgment's `id()`."""

    about: dict[int, str | None] = field(default_factory=dict)


@contextmanager
def capture(subject: str | None = None) -> Iterator[Capture]:
    """Record what each judgment is about while the block runs. `subject` (the request id or the
    ticket) is what a judgment is about when it reads neither a document nor a role."""
    cap = Capture()
    judged = kernel.JUDGED.set(cap.about)
    subj = kernel.SUBJECT.set(subject)
    read = kernel.LAST_READ.set(None)  # nothing read before the capture counts
    try:
        yield cap
    finally:
        kernel.LAST_READ.reset(read)
        kernel.SUBJECT.reset(subj)
        kernel.JUDGED.reset(judged)


def judgment_about(record: dict[str, Any], cap: Capture) -> list[str | None]:
    """One entry per `record["judgments"]` item, in order. `record` must be the one the kernel
    returned inside the capture (a copy's judgments are other objects, and come out as None)."""
    return [cap.about.get(id(j)) for j in record.get("judgments") or []]


# the contract's §5.5 table, in order, first match wins: (regex, code, when the flag routes).
# Rules: "always", "never", "routed" (if the decision routed), "route_mode" (if on_mismatch: route)
FLAG_CODES: tuple[tuple[str, str, str], ...] = (
    (r"^routed:", "routed", "always"),
    (r"^withheld:", "withheld", "routed"),
    (r"^incident", "incident", "never"),
    (r"^conflict: (?:policies|registered [A-Z]|exceptions)", "conflict", "never"),
    (r"^conflict:|; terms not confirmed", "conflict", "always"),
    (r"^tamper signs in", "tamper", "always"),
    (r"document on file is (?:mismatch|missing) against registered version", "mismatch",
     "route_mode"),
    (r"; set aside", "set_aside", "never"),
    (r"not on file", "not_on_file", "routed"),
    # SLA: word-bounded prefixes, so sla.yaml's "cannot decide restoration: …" counts (ruling R9)
    (r"^cannot decide\b", "cannot_decide", "routed"),
    (r"^out of scope\b", "out_of_scope", "routed"),
    (r"^no claim yet\b", "note", "routed"),
)  # fmt: skip
OTHER = ("note", "never")


def flag_items(flags: list[str], *, route_mode: bool, routed: bool) -> list[dict[str, Any]]:
    """Each flag as `{code, text, routes}`, in order, with `text` the flag string unchanged.
    `route_mode`: the procedure routes on a mismatch; `routed`: the decision went to route_to."""
    when = {"always": True, "never": False, "routed": routed, "route_mode": route_mode}
    out = []
    for text in flags:
        code, rule = next(((c, r) for p, c, r in FLAG_CODES if re.search(p, text)), OTHER)
        out.append({"code": code, "text": text, "routes": when[rule]})
    return out


# -- approval roles (contract §5.8; ruling R4) --------------------------------------------------
class ApprovalConflict(ValueError):  # noqa: N818 (the name the contract and plan fix)
    """The record's approvers disagree with the people the staff list resolves, or one person
    would hold both `approval` and `concurrence`."""


def pass_up(staff: list[dict[str, str]], requester_id: str, title: str) -> dict[str, str] | None:
    """The holder of `title` for a request by `requester_id`, under separation of duties: the
    first holder up the manager chain, and a requester who would approve their own request passes
    it to their manager. The one code path for `passed_from` and for the ratchet's confirmer."""
    me = next((e for e in staff if e["employee_id"] == requester_id), None)
    return None if me is None else kernel.resolve_approver(staff, me, title, sod=True)


def _passed_from(staff: list[dict[str, str]], role: str, person_id: str) -> dict[str, str] | None:
    held = kernel.holder(staff, role)
    if held is None or held["employee_id"] == person_id:
        return None
    return {"person_id": held["employee_id"], "reason": "separation_of_duties"}


def _item(
    kind: str, role: str, person_id: str, passed_from: dict[str, str] | None = None
) -> dict[str, Any]:
    return {"kind": kind, "role": role, "person_id": person_id, "passed_from": passed_from}


def approval_roles(
    decision_type: str,
    record: dict[str, Any],
    staff: list[dict[str, str]],
    requested_by: str | None,
    policy_terms: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Who must approve (or decide), by employee id. Discount and credit give `approval` (and
    credit `concurrence`) only for APPROVE_WITH_AUTHORIZATION; SLA gives `claim_decision` and
    `expected_actor` only for BREACH_CREDIT_OWED; any other outcome gives `[]`. Raises
    `ApprovalConflict` when the record's approver is not who `pass_up` resolves, or one person
    would hold both `approval` and `concurrence`."""
    outcome = record.get("gated_outcome")
    if decision_type == "sla":
        if outcome != "BREACH_CREDIT_OWED":
            return []
        titles = {e["employee_id"]: e["title"] for e in staff}
        duties = {"decide_claim": "claim_decision", "issue_memo": "expected_actor"}
        return [
            _item(duties[o["duty"]], titles[o["holder"]], o["holder"])
            for o in record.get("obligations") or []
            if o.get("duty") in duties and o.get("holder") in titles
        ]
    if outcome != "APPROVE_WITH_AUTHORIZATION":
        return []
    me = next((e for e in staff if e["email"].lower() == (requested_by or "").lower()), None)
    if me is None:
        raise ApprovalConflict(f"no staff member requested this: {requested_by!r}")
    by_name = {e["full_name"].lower(): e for e in staff}
    auth = record.get("authority") or {}
    role = auth.get("required_role")
    approver = pass_up(staff, me["employee_id"], role) if role else None
    named = by_name.get(str(auth.get("approver") or "").lower())
    if approver is None or named is None or approver["employee_id"] != named["employee_id"]:
        raise ApprovalConflict(f"the approver for {role!r} is not {auth.get('approver')!r}")
    out = [_item("approval", role, approver["employee_id"],
                 _passed_from(staff, role, approver["employee_id"]))]  # fmt: skip
    titles = [c["title"] for c in (policy_terms or {}).get("concurrence") or []]
    for a in record.get("approvers") or []:
        if a.get("kind") != "concurrence":
            continue
        person = by_name.get(str(a.get("name") or "").lower())
        title = next(
            (t for t in titles
             if person and (p := pass_up(staff, me["employee_id"], t))
             and p["employee_id"] == person["employee_id"]),
            None,
        )  # fmt: skip
        if person is None or title is None:
            raise ApprovalConflict(f"no policy concurrence resolves to {a.get('name')!r}")
        if person["employee_id"] == approver["employee_id"]:
            raise ApprovalConflict(f"{a.get('name')!r} would both approve and concur")
        out.append(_item("concurrence", title, person["employee_id"],
                         _passed_from(staff, title, person["employee_id"])))  # fmt: skip
    return out
