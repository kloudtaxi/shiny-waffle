"""Reference procedure for SLA breach response (experiment 6, lab extension): the lab's oracle.

It implements the blind subagent's rule sheet (`runs/2026-10-03-exp6-sla/rules/rule-sheet.md`,
R1–R55) over the truth in `truth/support.yaml`. As with discounts, this is the laboratory's check
on its own coherence, not the OWM. Every scenario's hand-authored expectation must follow from it,
or the build refuses to write.

The record follows the decision envelope (`runs/2026-10-03-exp6-sla/plan.md`): an outcome from the
SLA vocabulary, and `obligations[]`, each one either Northstar's (a duty with a holder and a due
time) or the customer's (with whether it was met).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from northstar.model import Scenario, Ticket, Truth

CT = ZoneInfo("America/Chicago")
OPEN, CLOSE = time(8, 0), time(18, 0)  # R2
OUTCOMES = ("BREACH_CREDIT_OWED", "BREACH_NO_CREDIT", "NO_BREACH", "OUT_OF_SCOPE", "CANNOT_DECIDE")
Interval = tuple[datetime, datetime]


class Calendar:
    """Business hours (R2) with the holiday list (R3), all in CT."""

    def __init__(self, holidays: set[date]) -> None:
        self.holidays = holidays

    def business_day(self, d: date) -> bool:
        return d.weekday() < 5 and d not in self.holidays

    def minutes(self, a: datetime, b: datetime) -> int:
        """Business minutes in [a, b]."""
        a, b = a.astimezone(CT), b.astimezone(CT)
        total, d = 0, a.date()
        while d <= b.date():
            if self.business_day(d):
                lo = max(a, datetime.combine(d, OPEN, CT))
                hi = min(b, datetime.combine(d, CLOSE, CT))
                if hi > lo:
                    total += int((hi - lo).total_seconds() // 60)
            d += timedelta(days=1)
        return total

    def next_start(self, t: datetime) -> datetime:
        """``t`` if inside business hours, else the next 08:00 CT on a business day (R24(b))."""
        t = t.astimezone(CT)
        d = t.date()
        if self.business_day(d) and OPEN <= t.time() < CLOSE:
            return t
        if not (self.business_day(d) and t.time() < OPEN):
            d += timedelta(days=1)
            while not self.business_day(d):
                d += timedelta(days=1)
        return datetime.combine(d, OPEN, CT)

    def add(self, start: datetime, minutes: int) -> datetime:
        """The moment ``minutes`` business minutes after ``start``."""
        t, left = self.next_start(start), minutes
        while True:
            end = datetime.combine(t.date(), CLOSE, CT)
            room = int((end - t).total_seconds() // 60)
            if left <= room:
                return t + timedelta(minutes=left)
            left -= room
            t = self.next_start(end)

    def nth_business_day_after(self, d: date, n: int) -> date:
        while n:
            d += timedelta(days=1)
            if self.business_day(d):
                n -= 1
        return d


class Clock:
    """One ticket clock: 24×7 or business hours, minus excluded intervals (R4, R26, R30)."""

    def __init__(self, cal: Calendar, business: bool, start: datetime, excl: list[Interval]):
        self.cal, self.business, self.start, self.excl = cal, business, start, excl

    def _span(self, a: datetime, b: datetime) -> int:
        if b <= a:
            return 0
        if self.business:
            return self.cal.minutes(a, b)
        return int((b - a).total_seconds() // 60)

    def elapsed(self, t: datetime) -> int:
        if t <= self.start:
            return 0
        out = self._span(self.start, t)
        for lo, hi in self.excl:
            out -= self._span(max(lo, self.start), min(hi, t))
        return out

    def moment(self, minutes: int) -> datetime:
        """When the clock reaches ``minutes``."""
        t = (
            self.cal.add(self.start, minutes)
            if self.business
            else self.start + timedelta(minutes=minutes)
        )
        while (short := minutes - self.elapsed(t)) > 0:
            t = self.cal.add(t, short) if self.business else t + timedelta(minutes=short)
        return t


def severity_of(t: Ticket) -> int:
    """R13–R17, from the truth's reading of the recorded business impact."""
    if t.impact in ("production_stopped", "all_users_down"):
        return 2 if t.workaround else 1
    if t.impact in ("degraded", "monitoring_unavailable", "some_users_down"):
        return 2
    return 3 if t.impact == "impaired" else 4


def holder(truth: Truth, role: str) -> str:
    return truth.holders_of(role)[0].id


def iso(t: datetime) -> str:
    return t.astimezone(CT).isoformat()


def decide_sla(truth: Truth, scenario: Scenario, available: frozenset[str]) -> dict[str, Any]:
    t = truth.ticket(str(scenario.ticket))
    cal = Calendar({h.date for h in truth.holidays})
    asof = scenario.decided_at
    opened = t.opened.astimezone(CT)
    cust = truth.customer_by_crm(t.account)
    northstar: list[dict[str, Any]] = []
    customer: list[dict[str, Any]] = []
    reasons: list[str] = []
    evidence: list[str] = [k for k in ("service_tickets", "ticket_events") if k in available]
    director = holder(truth, "CUSTOMER_SUPPORT_DIRECTOR")
    owner = f"owner:{t.account}"

    def duty(kind: str, role: str, who: str, due: datetime | date) -> None:
        northstar.append(
            {
                "duty": kind,
                "role": role,
                "holder": who,
                "due": due.isoformat()
                if isinstance(due, date) and not isinstance(due, datetime)
                else iso(due),
            }
        )

    claim_due = (t.claim.received.astimezone(CT).date() + timedelta(days=30)) if t.claim else None
    severity = severity_of(t)

    # -- scope (R9–R12) ------------------------------------------------------------------------
    agreement = next(
        (a for a in truth.support_agreements
         if cust and a.customer == cust.id and t.product in a.products
         and a.coverage_start <= opened.date() and a.document in available),
        None,
    )  # fmt: skip
    if agreement is None:
        reasons.append("out of scope: no support agreement covers this customer and product")
        duty("notify", "ACCOUNT_OWNER", owner, cal.add(cal.next_start(opened), 600))  # R12(d)
        if claim_due:
            duty("decide_claim", "CUSTOMER_SUPPORT_DIRECTOR", director, claim_due)  # R12(e), R41
        return _record(scenario, t, cust, "OUT_OF_SCOPE", "out", severity, "not_applicable",
                       "not_applicable", 0.0, northstar, customer, reasons, evidence)  # fmt: skip
    evidence.append(agreement.document)

    # -- version, plan, targets (R20–R23) ---------------------------------------------------
    sched = next(s for s in truth.sla_schedules
                 if s.active_on(opened.date()) and s.id in available)  # fmt: skip
    evidence.append(sched.id)
    target = sched.target_for(severity, agreement.plan)
    business = target.clock == "business"

    # -- clock start and exclusions (R24, R26, R29, R30) -----------------------------------------
    start = cal.next_start(opened) if business else opened
    windows: list[Interval] = []
    for n in truth.maintenance_notices:
        if n.customer != agreement.customer or t.product not in n.products:
            continue
        sent, ws, we = (x.astimezone(CT) for x in (n.sent, n.window_start, n.window_end))
        days, d = 0, sent.date()
        while d < ws.date():
            d += timedelta(days=1)
            days += cal.business_day(d)
        if days < sched.notice_business_days or "maintenance_notices" not in available:
            continue
        evidence.append("maintenance_notices")
        if ws <= opened < we:
            start = max(we, cal.next_start(we)) if business else we  # R30(a)
        elif we > start:
            windows.append((ws, we))  # R30(b)
    pauses = [(p.start, p.end) for p in t.pauses if p.start and p.end]  # R26(c)
    resp_clock = Clock(cal, business, start, windows)
    rest_clock = Clock(cal, business, start, windows + pauses)

    # -- breach (R5, R25, R31, R32) ------------------------------------------------------------
    resp: str
    if t.first_response is None:
        resp = "cannot_decide"
    elif (
        t.first_response <= start or resp_clock.elapsed(t.first_response) <= target.response_minutes
    ):
        resp = "met"
    else:
        resp = "missed"
    rest: str
    band: int | None = None
    restoration_target = target.restoration_minutes
    if restoration_target is None:
        rest = "not_applicable"
    elif t.restored is None:
        rest = "cannot_decide"
    else:
        rest = "decide"
        if t.exclusion_asserted:
            deadline = datetime.combine(
                cal.nth_business_day_after(t.restored.astimezone(CT).date(), 10), CLOSE, CT
            )
            duty("record_root_cause", "SUPPORT_ENGINEERING_LEAD",
                 holder(truth, "SUPPORT_ENGINEERING_LEAD"), deadline)  # fmt: skip
            rc = t.root_cause
            known = rc if rc and rc.at <= deadline and (asof is None or rc.at <= asof) else None
            if known and known.attributes_to == "customer":
                rest = "not_applicable"
                reasons.append("customer-caused: the restoration target does not apply")
            elif known is None and (asof is not None and asof < deadline):
                rest = "cannot_decide"
                reasons.append("cannot decide restoration: missing the root-cause finding")
        if rest == "decide":
            el = rest_clock.elapsed(t.restored)
            if el <= restoration_target:
                rest = "met"
            else:
                band = (2 if el > 2 * restoration_target else 1) if sched.version != "1.0" else None
                rest = f"missed_band{band}" if band else "missed"

    # -- credits (R33–R40, R43) -------------------------------------------------------------------
    credit: float | None = 0.0
    breach = resp == "missed" or rest.startswith("missed")
    if resp == "cannot_decide" or rest == "cannot_decide":
        credit = None
    elif severity in (1, 2) and breach:
        rate_sev = 2 if severity == 1 and t.channel != "phone" else severity  # R37
        pct = sched.rate(rate_sev, "response", None) if resp == "missed" else 0.0
        if rest.startswith("missed"):
            pct += sched.rate(rate_sev, "restoration", band)
        month = opened.strftime("%Y-%m")
        fee = agreement.fee_for(month)
        used = sum(c.amount_usd for c in truth.service_credits if c.customer == agreement.customer
                   and c.ticket_opened.strftime("%Y-%m") == month)  # fmt: skip
        if used:
            evidence.append("service_credits")
        amount = round(min(pct * fee, max(0.0, sched.cap_pct * fee - used)), 2)
        assert t.restored is not None
        window_end = t.restored.astimezone(CT).date() + timedelta(days=sched.claim_days)
        if t.claim is None:
            credit = 0.0
            reasons.append(f"no claim yet: {amount:.2f} would be owed if claimed by {window_end}")
        elif t.claim.received.astimezone(CT).date() <= window_end:
            credit = amount
        else:
            credit = 0.0
            reasons.append(f"claim received after the window closed on {window_end}")
    if t.claim and agreement:
        w_end = (t.restored.astimezone(CT).date() + timedelta(days=sched.claim_days)
                 if t.restored else None)  # fmt: skip
        timely = w_end is not None and t.claim.received.astimezone(CT).date() <= w_end
        customer.append({"duty": "claim", "status": "met" if timely else "not_met"})

    # -- escalation (R45–R52), on the ticket's clocks, ignoring the exclusion (R46(b)) ----------
    def not_restored(at: datetime) -> bool:
        return t.restored is None or t.restored > at

    if severity == 1:
        customer.insert(0, {"duty": "phone_report",
                            "status": "met" if t.channel == "phone" else "not_met"})  # fmt: skip
        duty("engage", "SUPPORT_ESCALATION_MANAGER", holder(truth, "SUPPORT_ESCALATION_MANAGER"),
             resp_clock.moment(15))  # fmt: skip
        duty("notify", "ACCOUNT_OWNER", owner, resp_clock.moment(30))
        assert restoration_target is not None
        half, full = (
            rest_clock.moment(restoration_target // 2),
            rest_clock.moment(restoration_target),
        )
        if not_restored(half):
            duty("notify", "CUSTOMER_SUPPORT_DIRECTOR", director, half)
        if not_restored(full):
            duty("notify", "VP_SALES", holder(truth, "VP_SALES"), full)
            account = truth.account_for(agreement.customer)
            if account and account.tier == "Strategic":
                duty("notify", "CRO", holder(truth, "CRO"), full)
    elif severity == 2:
        rmoment = resp_clock.moment(target.response_minutes)
        if t.first_response is None or t.first_response > rmoment:
            duty("notify", "SUPPORT_ESCALATION_MANAGER",
                 holder(truth, "SUPPORT_ESCALATION_MANAGER"), rmoment)  # fmt: skip
        assert restoration_target is not None
        full = rest_clock.moment(restoration_target)
        if not_restored(full):
            duty("notify", "CUSTOMER_SUPPORT_DIRECTOR", director, full)
            duty("notify", "ACCOUNT_OWNER", owner, full)
    elif severity == 3 and restoration_target is not None:
        full = rest_clock.moment(restoration_target)
        if not_restored(full):
            duty("notify", "SUPPORT_ESCALATION_MANAGER",
                 holder(truth, "SUPPORT_ESCALATION_MANAGER"), full)  # fmt: skip
    if claim_due:
        duty("decide_claim", "CUSTOMER_SUPPORT_DIRECTOR", director, claim_due)  # R41
        if credit:
            duty("issue_memo", "SUPPORT_BILLING_MANAGER", holder(truth, "SUPPORT_BILLING_MANAGER"),
                 claim_due)  # fmt: skip

    if credit is None:
        outcome = "CANNOT_DECIDE"
    elif breach:
        outcome = "BREACH_CREDIT_OWED" if credit > 0 else "BREACH_NO_CREDIT"
    else:
        outcome = "NO_BREACH"
    return _record(scenario, t, cust, outcome, "in", severity, resp, rest, credit, northstar,
                   customer, reasons, evidence)  # fmt: skip


def _record(
    scenario: Scenario, t: Ticket, cust: Any, outcome: str, scope: str, severity: int, resp: str,
    rest: str, credit: float | None, northstar: list[dict[str, Any]],
    customer: list[dict[str, Any]], reasons: list[str], evidence: list[str],
) -> dict[str, Any]:  # fmt: skip
    obligations = [{"party": "northstar", **o} for o in northstar]
    obligations += [{"party": "customer", **o} for o in customer]
    return {
        "decision_id": f"DEC-{scenario.id}",
        "scenario": scenario.id,
        "type": "sla_response",
        "as_of": (scenario.decided_at or t.opened).astimezone(CT).date(),
        "corpus": scenario.corpus,
        "subject": {"ticket": t.id, "account": t.account,
                    "customer": cust.id if cust else None, "product": t.product},
        "decision": {"outcome": outcome},
        "scope": scope,
        "severity": {"true": severity, "reported": t.reported_priority},
        "breach": {"response": resp, "restoration": rest},
        "remedy": {"credit_usd": credit},
        "obligations": obligations,
        "reason": reasons,
        "evidence": evidence,
    }  # fmt: skip
