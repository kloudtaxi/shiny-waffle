"""The SLA-breach-response spec on the decision kernel (experiment 6): a non-approval decision.

Written after the kernel was frozen at `47238c6` (`runs/2026-10-03-exp6-sla/plan.md`). The rules
were written by a subagent that never saw the kernel. The decision is event-triggered (a ticket,
no requestor). Its answer is a set of obligations with deadlines.

What is particular to SLA, and lives here:
- its questions (severity from the recorded impact; whether a note asserts the customer-caused
  exclusion);
- how it reads its own documents (the schedule's targets, credits, cap and windows; the terms'
  plan, products, coverage and fees; the holiday calendar; the escalation procedure's numbers);
- its rules for breach, credit, claim and escalation;
- its outcome vocabulary.

What the kernel does:
- provenance (G1) and validity windows (G2);
- tamper signs (G3) and gating, with the routing outcome as a parameter (K-8);
- identity by registered key (K-4);
- products named in text;
- role mapping (Jev);
- clocks (K-5);
- obligations (K-6);
- routing without a requestor (K-7).
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from kernel import (
    Calendar,
    Clock,
    Doc,
    Engine,
    Evidence,
    Guards,
    Interval,
    KindRule,
    Obligation,
    covering,
    gate,
    holder,
    in_force,
    judge,
    linked,
    map_role,
    owner_of,
    products_in,
    row,
    screen,
)

OUTCOMES = ("BREACH_CREDIT_OWED", "BREACH_NO_CREDIT", "NO_BREACH", "OUT_OF_SCOPE", "CANNOT_DECIDE")
Q_ASSERTS = {
    "type": "noul",
    "instructions": (
        "The note in `note` asserts that the incident was caused by the customer (it invokes the "
        "customer-caused exclusion)."
    ),
}
Q_ATTRIBUTES = {
    "type": "noul",
    "instructions": "The root-cause finding in `finding` attributes the incident to the customer.",
}
GUARDS = Guards(
    rules=(
        KindRule(
            "schedule", id_prefixes=("SLA-SCHEDULE",), title_words=("Service Level Schedule",)
        ),
        KindRule("guide", title_words=("Severity Guide",)),
        KindRule("procedure", title_words=("Escalation Procedure",)),
        KindRule("calendar", title_words=("Holiday Calendar",)),
        KindRule("terms", id_prefixes=("SUP-",), title_words=("Support Terms",)),
    ),
    owners={
        "schedule": {"Customer Support"},
        "guide": {"Customer Support"},
        "procedure": {"Customer Support"},
        "calendar": {"People Operations"},
        "terms": {"Legal"},
    },
    value_of=lambda d: None,
    product_of=lambda d: "",
    policy_kind="schedule",
    graded=("guide", "procedure", "calendar", "terms"),
    approval_kinds=(),
    amending_kinds=(),
    schedule_kinds=(),
)


# -- reading its own documents ------------------------------------------------------------------
def _flat(d: Doc) -> str:
    return " ".join(d.body.split())


def duration(text: str) -> int | None:
    """ "30 minutes" → 30; "4 hours" / "12 business hours" → minutes; "No restoration target" →
    None."""
    if m := re.search(r"(\d+) minutes", text):
        return int(m[1])
    if m := re.search(r"(\d+) (?:business )?hours?", text):
        return int(m[1]) * 60
    return None


def targets(sched: Doc) -> dict[tuple[int, str | None], tuple[int, int | None, bool]]:
    """(severity, plan or None) → (response minutes, restoration minutes, business clock)."""
    m = re.search(r"## 3\. Targets\n(.*?)(?=\n## )", sched.body, re.S)
    out = {}
    for line in (m[1] if m else "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or not cells[0][:1].isdigit():
            continue
        sev, _, plan = cells[0].partition(",")
        plan_name = plan.replace("plan", "").strip() or None
        resp = duration(cells[1])
        assert resp is not None, line
        out[(int(sev), plan_name)] = (resp, duration(cells[2]), "Business" in cells[3])
    return out


def credit_rates(sched: Doc) -> dict[tuple[int, str, int | None], float]:
    """(severity, "response" | "restoration", band or None) → fraction of the monthly fee."""
    m = re.search(r"## 6\. Service credits\n(.*?)(?=\n## )", sched.body, re.S)
    out: dict[tuple[int, str, int | None], float] = {}
    for line in (m[1] if m else "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or not cells[1].endswith("%"):
            continue
        kind = "response" if cells[0].startswith("Initial response") else "restoration"
        band = int(b[1]) if (b := re.search(r"band (\d)", cells[0])) else None
        for sev, pct in ((1, cells[1]), (2, cells[2])):
            out[(sev, kind, band)] = int(pct.rstrip("%")) / 100
    return out


def schedule_terms(sched: Doc) -> dict[str, Any]:
    f = _flat(sched)
    zone = re.search(r"\((America/[A-Za-z_]+)\)", f)
    hours = re.search(r"Business hours\*\* are (\d\d):(\d\d) to (\d\d):(\d\d)", f)
    notice = re.search(r"at least \*\*(\d+) business days\*\*", f)
    cap = re.search(r"may not exceed \*\*(\d+)%\*\*", f)
    claim = re.search(r"\*\*(\d+) calendar days\*\* after the restoration date", f)
    assert zone and hours and notice and cap and claim, sched.doc_id
    return {"zone": ZoneInfo(zone[1]), "opens": time(int(hours[1]), int(hours[2])),
            "closes": time(int(hours[3]), int(hours[4])), "notice_days": int(notice[1]),
            "cap": int(cap[1]) / 100, "claim_days": int(claim[1]),
            "version": str(sched.front.get("doc_id", "")).rsplit("-", 1)[-1]}  # fmt: skip


def holidays(cal: Doc | None) -> frozenset[date]:
    if cal is None:
        return frozenset()
    return frozenset(date.fromisoformat(d) for d in re.findall(r"^\| (\d{4}-\d\d-\d\d) \|",
                                                               cal.body, re.M))  # fmt: skip


def terms_of(d: Doc, products: list[dict[str, str]]) -> dict[str, Any]:
    fee_text = row(d, "Monthly support fee") or ""
    return {
        "duns": (re.search(r"DUNS ([\d-]+)", d.body) or [None, None])[1],
        "plan": (row(d, "Support plan") or "").split(": ", 1)[-1],
        "products": products_in(row(d, "Covered products") or "", products),
        "fees": [(mo, float(a.replace(",", ""))) for a, mo in
                 re.findall(r"\$([\d,]+) per month from (\d{4}-\d\d)", fee_text)],
    }  # fmt: skip


def severity_question(guide: Doc) -> dict[str, Any]:
    sections = re.findall(r"## Severity (\d): \w+\n\n(.*?)(?=\n## |\Z)", guide.body, re.S)
    return {
        "type": "choice",
        "instructions": (
            "Which severity level does the business impact recorded in `ticket` meet? Test the "
            "definitions in order; the severity is the first one the impact meets."
        ),
        "criteria": {f"severity_{n}": " ".join(text.split()) for n, text in sections},
    }


def procedure_numbers(proc: Doc) -> dict[str, int]:
    f = _flat(proc)
    mins = [int(x) for x in re.findall(r"no later than (\d+) minutes after clock start", f)]
    pct = [int(x) for x in re.findall(r"not restored when (\d+)% of the restoration target", f)]
    oos = re.search(r"no later than (\d+) business hours after the open time", f)
    assert len(mins) == 2 and len(pct) == 2 and oos, proc.doc_id
    return {"lead": mins[0], "owner": mins[1], "half": pct[0], "full": pct[1],
            "out_of_scope": int(oos[1])}  # fmt: skip


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


# -- the decision -----------------------------------------------------------------------------
def decide(
    eng: Engine, ev: Evidence, ticket_id: str, decided_at: datetime | None, sid: str
) -> dict[str, Any]:
    used: list[dict[str, Any]] = []
    flags: list[str] = []
    staff, products = ev.table("employees"), ev.table("products")
    s = screen(eng, ev.docs(), GUARDS, staff, products, used, flags)
    t = next(r for r in ev.table("service_tickets") if r["ticket_id"] == ticket_id)
    events = [e for e in ev.table("ticket_events") if e["ticket_id"] == ticket_id]
    opened = dt(t["opened_at"])
    obligations: list[Obligation] = []
    relied: list[Doc] = []
    roles: dict[str, str | None] = {}

    def person(role_words: str) -> str | None:
        """The holder of the role the procedure names (Jev maps the words to an HR title)."""
        if role_words not in roles:
            who = holder(staff, map_role(eng, role_words, staff, used))  # K-7
            roles[role_words] = who["employee_id"] if who else None
        return roles[role_words]

    def owe(duty: str, role: str, who: str | None, due: datetime | date, cal: Calendar) -> None:
        stamp = cal.local(due).isoformat() if isinstance(due, datetime) else due.isoformat()
        obligations.append(Obligation("organization", duty, role, who, stamp))  # K-6

    first_sched = in_force(s.pols, opened.date(), flags)  # G2
    proc = next(iter(s.good["procedure"]), None)
    guide = next(iter(s.good["guide"]), None)
    calendar_doc = next(iter(s.good["calendar"]), None)
    if first_sched is not None:
        terms = schedule_terms(first_sched)
        cal = Calendar(
            terms["zone"], terms["opens"], terms["closes"], holidays(calendar_doc)
        )  # K-5
        opened = cal.local(opened)
    # the version is chosen by the open date in the schedule's own zone
    sched = in_force(s.pols, opened.date(), flags) if first_sched else None
    if sched is None or proc is None or guide is None:
        flags.append("cannot decide: the schedule in force, the procedure or the guide is missing")
        return _record(sid, ticket_id, t, "CANNOT_DECIDE", None, None, "cannot_decide",
                       "cannot_decide", None, [], used, flags, [])  # fmt: skip
    terms = schedule_terms(sched)
    relied += [sched, proc, guide]
    nums = procedure_numbers(proc)
    director = "Director of Customer Support"
    claims = [e for e in events if e["event"] == "credit_claim"]
    claim_at = cal.local(dt(claims[0]["at"])) if claims else None
    claim_due = (claim_at.date() + timedelta(days=30)) if claim_at else None

    # -- severity (Jev, from the recorded impact) ---------------------------------------------
    sev_j = judge(eng, {"ticket": {"description": t["description"]}}, "severity",
                  severity_question(guide))  # fmt: skip
    used.append(sev_j)
    severity = int(sev_j["choice"].split("_")[1])

    # -- scope: identity by registered key (DUNS), then the terms' products and coverage -------
    crm = next((r for r in ev.table("crm_accounts") if r["account_id"] == t["account_id"]), None)
    sku = t["product_sku"]
    agreement = None
    for d in covering(s.good["terms"], opened.date()):  # coverage in force (K-9: open-ended)
        tm = terms_of(d, products)
        same = crm and linked({"duns_number": str(tm["duns"])}, [crm], ("duns_number",))  # K-4
        if same and sku in tm["products"]:
            agreement = (d, tm)
    owner = owner_of(crm, staff)  # K-7: the account owner, from the CRM row
    owner_key = f"owner:{t['account_id']}"
    if agreement is None:
        flags.append("out of scope: no support terms cover this customer and product")
        due = cal.add(cal.next_open(opened), nums["out_of_scope"] * 60)
        owe("notify", "ACCOUNT_OWNER", owner_key, due, cal)
        if claim_due:
            owe("decide_claim", "CUSTOMER_SUPPORT_DIRECTOR", person(director), claim_due, cal)
        uncertain, gated = gate("OUT_OF_SCOPE", relied, s.inconsistent, used, flags,
                                route_to="CANNOT_DECIDE")  # fmt: skip
        return _record(sid, ticket_id, t, "OUT_OF_SCOPE", gated, severity, "not_applicable",
                       "not_applicable", 0.0, obligations, used, flags, uncertain, "out",
                       owner)  # fmt: skip
    terms_doc, tm = agreement
    relied.append(terms_doc)
    tgt = targets(sched)
    resp_min, rest_min, business = tgt.get((severity, tm["plan"])) or tgt[(severity, None)]

    # -- clocks: start, maintenance windows, pauses (K-5) --------------------------------------
    start = cal.next_open(opened) if business else opened
    windows: list[Interval] = []
    for n in ev.table("maintenance_notices"):
        if n["account_id"] != t["account_id"] or sku not in n["products"].split(";"):
            continue
        sent, ws, we = (cal.local(dt(n[k])) for k in ("sent_at", "window_start", "window_end"))
        if cal.working_days_between(sent.date(), ws.date()) < terms["notice_days"]:
            continue
        if ws <= opened < we:
            start = max(we, cal.next_open(we)) if business else we
        elif we > start:
            windows.append((ws, we))
    pauses: list[Interval] = []
    began: datetime | None = None
    for e in events:
        if e["event"] == "status_change" and "Awaiting Customer" in e["detail"]:
            began = dt(e["at"])
        elif e["event"] == "status_change" and began and "In Progress" in e["detail"]:
            pauses.append((began, dt(e["at"])))
            began = None
    resp_clock = Clock(cal, business, start, windows)
    rest_clock = Clock(cal, business, start, windows + pauses)

    # -- breach ---------------------------------------------------------------------------------
    first = next((dt(e["at"]) for e in events if e["event"] == "engineer_response"), None)
    restored = dt(t["restored_at"]) if t["restored_at"] else None
    if first is None:
        resp = "cannot_decide"
    else:
        resp = "met" if first <= start or resp_clock.elapsed(first) <= resp_min else "missed"
    rest, band = "not_applicable", None
    if rest_min is not None:
        rest = "cannot_decide" if restored is None else "decide"
    asserted = []
    for e in events:
        if e["event"] == "note":
            j = judge(eng, {"note": e["detail"]}, "asserts_exclusion", Q_ASSERTS)
            used.append(j)
            if j["yes"]:
                asserted.append(e)
    if asserted and restored is not None:
        deadline = datetime.combine(cal.working_days_after(cal.local(restored).date(), 10),
                                    cal.closes, cal.zone)  # fmt: skip
        owe("record_root_cause", "SUPPORT_ENGINEERING_LEAD", person("Support Engineering Lead"),
            deadline, cal)  # fmt: skip
        cutoff = min(deadline, decided_at) if decided_at else deadline
        found = [e for e in events
                 if e["event"] == "root_cause_finding" and dt(e["at"]) <= cutoff]  # fmt: skip
        if found:
            j = judge(eng, {"finding": found[0]["detail"]}, "attributes_customer", Q_ATTRIBUTES)
            used.append(j)
            if j["yes"] and rest == "decide":
                rest = "not_applicable"
        elif decided_at is not None and decided_at < deadline and rest == "decide":
            rest = "cannot_decide"
            flags.append("cannot decide restoration: missing the root-cause finding")
    if rest == "decide":
        assert restored is not None and rest_min is not None
        el = rest_clock.elapsed(restored)
        if el <= rest_min:
            rest = "met"
        else:
            banded = any(k[2] for k in credit_rates(sched))
            band = (2 if el > 2 * rest_min else 1) if banded else None
            rest = f"missed_band{band}" if band else "missed"

    # -- credit and claim -----------------------------------------------------------------------
    breach = resp == "missed" or rest.startswith("missed")
    credit: float | None = 0.0
    phoned = t["channel"] == "phone"
    if "cannot_decide" in (resp, rest):
        credit = None
    elif severity in (1, 2) and breach:
        rates = credit_rates(sched)
        rate_sev = 2 if severity == 1 and not phoned else severity
        pct = rates[(rate_sev, "response", None)] if resp == "missed" else 0.0
        if rest.startswith("missed"):
            pct += rates[(rate_sev, "restoration", band)]
        month = opened.strftime("%Y-%m")
        fee = [a for mo, a in tm["fees"] if mo <= month][-1]
        used_cap = sum(float(c["amount_usd"]) for c in ev.table("service_credits")
                       if c["account_id"] == t["account_id"]
                       and c["ticket_opened"][:7] == month)  # fmt: skip
        amount = round(min(pct * fee, max(0.0, terms["cap"] * fee - used_cap)), 2)
        assert restored is not None
        window_end = cal.local(restored).date() + timedelta(days=terms["claim_days"])
        if claim_at is None:
            credit = 0.0
            flags.append(f"no claim yet: {amount:.2f} would be owed if claimed by {window_end}")
        elif claim_at.date() <= window_end:
            credit = amount
        else:
            credit = 0.0
            flags.append(f"claim received after the window closed on {window_end}")

    # -- the counterparty's obligations ---------------------------------------------------------
    counterparty: list[Obligation] = []
    if severity == 1:
        counterparty.append(Obligation("counterparty", "phone_report",
                                       status="met" if phoned else "not_met"))  # fmt: skip
    if claim_at is not None and restored is not None:
        w_end = cal.local(restored).date() + timedelta(days=terms["claim_days"])
        met = "met" if claim_at.date() <= w_end else "not_met"
        counterparty.append(Obligation("counterparty", "claim", status=met))

    # -- escalation, on the ticket's clocks, ignoring the exclusion ---------------------------
    def open_at(m: datetime) -> bool:
        return restored is None or restored > m

    if severity == 1 and rest_min is not None:
        owe("engage", "SUPPORT_ESCALATION_MANAGER", person("Support Escalation Manager"),
            resp_clock.moment(nums["lead"]), cal)  # fmt: skip
        owe("notify", "ACCOUNT_OWNER", owner_key, resp_clock.moment(nums["owner"]), cal)
        half = rest_clock.moment(rest_min * nums["half"] // 100)
        full = rest_clock.moment(rest_min * nums["full"] // 100)
        if open_at(half):
            owe("notify", "CUSTOMER_SUPPORT_DIRECTOR", person(director), half, cal)
        if open_at(full):
            owe("notify", "VP_SALES", person("VP Sales"), full, cal)
            if crm and crm.get("account_tier") == "Strategic":
                owe("notify", "CRO", person("Chief Revenue Officer"), full, cal)
    elif severity == 2 and rest_min is not None:
        rmoment = resp_clock.moment(resp_min)
        if first is None or first > rmoment:
            owe("notify", "SUPPORT_ESCALATION_MANAGER", person("Support Escalation Manager"),
                rmoment, cal)  # fmt: skip
        full = rest_clock.moment(rest_min)
        if open_at(full):
            owe("notify", "CUSTOMER_SUPPORT_DIRECTOR", person(director), full, cal)
            owe("notify", "ACCOUNT_OWNER", owner_key, full, cal)
    elif severity == 3 and rest_min is not None:
        full = rest_clock.moment(rest_min)
        if open_at(full):
            owe("notify", "SUPPORT_ESCALATION_MANAGER", person("Support Escalation Manager"),
                full, cal)  # fmt: skip
    if claim_due:
        owe("decide_claim", "CUSTOMER_SUPPORT_DIRECTOR", person(director), claim_due, cal)
        if credit:
            owe("issue_memo", "SUPPORT_BILLING_MANAGER", person("Support Billing Manager"),
                claim_due, cal)  # fmt: skip

    if credit is None:
        outcome = "CANNOT_DECIDE"
    elif breach:
        outcome = "BREACH_CREDIT_OWED" if credit > 0 else "BREACH_NO_CREDIT"
    else:
        outcome = "NO_BREACH"
    uncertain, gated = gate(outcome, relied, s.inconsistent, used, flags, route_to="CANNOT_DECIDE")
    return _record(sid, ticket_id, t, outcome, gated, severity, resp, rest, credit,
                   obligations + counterparty, used, flags, uncertain, "in", owner)  # fmt: skip


def _record(
    sid: str, ticket_id: str, t: dict[str, str], outcome: str, gated: str | None,
    severity: int | None, resp: str, rest: str, credit: float | None,
    obligations: list[Obligation], used: list[dict[str, Any]], flags: list[str],
    uncertain: list[str], scope: str | None = None, owner: dict[str, str] | None = None,
) -> dict[str, Any]:  # fmt: skip
    return {
        "scenario": sid,
        "type": "sla_response",
        "subject": {"ticket": ticket_id, "account": t["account_id"]},
        "outcome": outcome,
        "gated_outcome": gated or outcome,
        "uncertain": uncertain,
        "scope": scope,
        "severity": severity,
        "breach": {"response": resp, "restoration": rest},
        "credit_usd": credit,
        "obligations": [o.record() for o in obligations],
        "account_owner": owner["full_name"] if owner else None,
        "judgments": used,
        "flags": flags,
    }
