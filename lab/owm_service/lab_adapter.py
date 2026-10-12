"""The demo adapter (spec §8.3): `POST /lab/adapter/execute` closes the loop the way an executor
holding a system's credential would. Lab-only, outside the contract.

`execute` does three things:
1. **redeems** the clearance with the params it is bound to. A refused redemption writes no effect
   and returns the refusal (`{redeemed: false, reasons}`);
2. **writes the effect** into the systems-of-record overlay, as actor `{kind: system, id:
   adapter}`, in one transaction:
   - `apply_discount`: the request's `status` becomes Approved, with `approved_by` (the approver's
     email, or the requester's when no approval was needed) and `approved_on` (the clock's date);
   - `set_credit_limit`: the credit request's `status`, `approved_by` and `approved_on`, alike;
   - `issue_service_credit`: a `service_credits` row whose `credit_id` is the CLR id, with
     `amount_usd`, so the SLA cap counts it next time;
3. **reports** `applied`, or `failed` when `fail` is set.

The effect never changes a column a kernel judgment reads (the discount and credit specs ask Jev
about the request's `justification`), so a later ask on the subject replays and comes back
`spent`. The clearance id needs no note in the row: `clearance.redeemed` and `execution.reported`
carry it.

With `fail`, nothing is written: a failed execution changed nothing in the system, and the report
raises the incident. If the overlay refuses the write (the row is gone, a value doesn't fit), the
action is still spent, since it was redeemed, so the adapter reports `failed` with the reason. Any
other error after redeeming (a bug, a lock timeout) is reported `failed` too and then re-raised:
redeemed always means reported, and the bug still surfaces.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

from .clearance import Clearances
from .errors import NotFound, Refused
from .models import (
    Actor,
    ClearanceBound,
    DecisionRecord,
    Executor,
    NotRedeemed,
    RedeemRequest,
    ReportRequest,
)
from .org import Org

ADAPTER: Final[dict[str, Any]] = {"kind": "system", "id": "adapter"}
NAME: Final = "lab-adapter"
SYSTEM: Final[Mapping[str, str]] = {
    "apply_discount": "crm", "set_credit_limit": "erp", "issue_service_credit": "service",
}  # fmt: skip
REQUESTS: Final[Mapping[str, str]] = {
    "apply_discount": "discount_requests", "set_credit_limit": "credit_requests",
}  # fmt: skip


def execute(
    org: Org, clearances: Clearances, clearance_id: str, *, fail: bool, by: Actor | None = None
) -> dict[str, Any]:
    """Redeem, write the effect, report. `by` is the session that asked (ruling R35)."""
    row = org.log.get_clearance(clearance_id)
    if row is None or row.org != org.org_id:
        raise NotFound(f"clearance {clearance_id}")
    bound = ClearanceBound.model_validate(row.bound)
    executor = Executor(system=SYSTEM[bound.action], adapter=NAME)
    redeemed = clearances.redeem(
        clearance_id, RedeemRequest(params=bound.params, executor=executor), by=by)  # fmt: skip
    if isinstance(redeemed, NotRedeemed):
        out: dict[str, Any] = redeemed.model_dump(mode="json", exclude_unset=True)
        return out
    effect: dict[str, Any] | None = None
    detail: str | None = "The lab adapter was asked to fail; it wrote nothing." if fail else None
    if not fail:
        try:
            rec = clearances.decisions.get(bound.decision_id, bound.decision_version)
            effect = _write(org, clearance_id, bound, rec)
        except (NotFound, Refused) as e:
            detail = f"The system refused the write: {e}"
        except Exception as e:
            # redeemed always means reported: report the failure (it opens the incident), then let
            # the bug surface
            why = f"The adapter failed after redeeming: {type(e).__name__}: {e}"
            _report(clearances, clearance_id, None, why, by)
            raise
    report = _report(clearances, clearance_id, effect, detail, by)
    return {"redeemed": True, "at": redeemed.at, "effect": effect, "report": report.status,
            "incident_id": report.incident_id}  # fmt: skip


@dataclass(frozen=True)
class _Reported:
    status: str
    incident_id: str | None


def _report(
    clearances: Clearances, clearance_id: str, effect: dict[str, Any] | None,
    detail: str | None, by: Actor | None,
) -> _Reported:  # fmt: skip
    """`applied` with a reference to what was written, or `failed` with why."""
    status = "failed" if effect is None else "applied"
    ref = None if effect is None else f"{effect['table']}/{effect['id']}"
    body = ReportRequest.model_validate({"status": status, "external_ref": ref, "detail": detail})
    return _Reported(status, clearances.report(clearance_id, body, by=by).incident_id)


def _write(
    org: Org, clearance_id: str, bound: ClearanceBound, rec: DecisionRecord
) -> dict[str, Any]:
    """The action's effect in the overlay, as the adapter; what was written."""
    now = org.clock.now()  # before the write: never first read inside one
    today, p = now.date().isoformat(), bound.params
    if bound.action == "issue_service_credit":
        ticket = org.sor.row("service_tickets", str(p["ticket"]))
        if ticket is None:
            raise NotFound(f"service_tickets {p['ticket']}")
        credit = {"credit_id": clearance_id, "ticket_id": str(p["ticket"]),
                  "account_id": str(p["account_id"]), "ticket_opened": ticket["opened_at"][:10],
                  "amount_usd": f"{float(p['amount_usd']):.2f}", "approved_on": today}  # fmt: skip
        with org.log.transaction() as tx:
            org.sor.insert(tx, "service_credits", credit, actor=ADAPTER, at=now)
        return {"system": "service", "table": "service_credits", "id": clearance_id,
                "row": credit}  # fmt: skip
    table, key = REQUESTS[bound.action], str(p["request_id"])
    current = org.sor.row(table, key)
    if current is None:
        raise NotFound(f"{table} {key}")
    fields = {"status": "Approved", "approved_by": _approver_email(org, rec),
              "approved_on": today}  # fmt: skip
    with org.log.transaction() as tx:
        org.sor.edit(tx, table, key, fields, actor=ADAPTER, at=now)
    return {"system": SYSTEM[bound.action], "table": table, "id": key, "fields": fields}


def _approver_email(org: Org, rec: DecisionRecord) -> str:
    """Who approved, as the request tables record it: the email of the person who gave the
    version's approval, or the requester's when the request was within their own authority."""
    given = next((a.given.by for a in rec.approvals if a.kind == "approval" and a.given), None)
    who = given or rec.requested_by
    if who is None:
        return ""
    staff = org.sor.table("employees")
    return next((r["email"] for r in staff if r["employee_id"] == who.id), "")
