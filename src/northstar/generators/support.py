"""Support evidence for the SLA decision (experiment 6, lab extension).

The rules come from the blind subagent's rule sheet (`runs/2026-10-03-exp6-sla/rules/`), split
across the documents its appendix names:
- the Service Level Schedule, versions 1.0 and 2.0 (definitions, clocks, exclusions, credits and
  customer obligations, with each version's values);
- the severity guide;
- the escalation procedure, which names roles;
- the support organization chart, which names the role holders;
- the holiday calendar;
- each customer's support terms.

Plus four Northstar Service exports: tickets, ticket events, maintenance notices and credits
already approved. Generated last, with no shared randomness, so every other artifact stays
byte-identical. Timestamps are recorded in the zone of the site that recorded them.
"""

from __future__ import annotations

from datetime import datetime

from northstar.artifacts import Artifact
from northstar.export.csv import to_csv
from northstar.export.markdown import document, table, usd
from northstar.factories import Background
from northstar.model import SlaSchedule, SupportAgreement, Ticket, Truth

DRIVE, SERVICE = "Northstar Drive", "Northstar Service"
HOTLINE = "(312) 555-0187"


def generate(truth: Truth, bg: Background) -> list[Artifact]:
    if not truth.sla_schedules:
        return []
    return [
        *(_schedule(truth, s) for s in truth.sla_schedules),
        _severity_guide(),
        _escalation_procedure(),
        _org_chart(truth),
        _holidays(truth),
        *(_terms(truth, a) for a in truth.support_agreements),
        _tickets(truth),
        _events(truth),
        _notices(truth),
        _credits(truth),
    ]


def _hours(minutes: int | None, business: bool) -> str:
    if minutes is None:
        return "No restoration target"
    unit = "business hour" if business else "hour"
    if minutes < 60:
        return f"{minutes} minutes"
    h = minutes // 60
    return f"{h} {unit}{'s' if h != 1 else ''}"


def _schedule(truth: Truth, s: SlaSchedule) -> Artifact:
    v1 = s.version == "1.0"
    rows = []
    for t in s.targets:
        label = f"{t.severity}" + (f", {t.plan} plan" if t.plan else "")
        biz = t.clock == "business"
        clock = "Business hours" if biz else "24×7"
        rows.append([label, _hours(t.response_minutes, biz), _hours(t.restoration_minutes, biz),
                     clock])  # fmt: skip

    def r(severity: int, target: str, band: int | None) -> str:
        return f"{s.rate(severity, target, band):.0%}"

    if v1:
        credit_rows = [
            ["Initial response", r(1, "response", None), r(2, "response", None)],
            ["Restoration", r(1, "restoration", None), r(2, "restoration", None)],
        ]
        credit_note = ""
    else:
        credit_rows = [
            ["Initial response", r(1, "response", None), r(2, "response", None)],
            ["Restoration, band 1: elapsed time more than the target and no more than 2× the "
             "target", r(1, "restoration", 1), r(2, "restoration", 1)],
            ["Restoration, band 2: elapsed time more than 2× the target",
             r(1, "restoration", 2), r(2, "restoration", 2)],
        ]  # fmt: skip
        credit_note = ("The restoration credit depends on the restoration elapsed time, measured "
                       "against the restoration target.\n\n")  # fmt: skip
    applies = (f"tickets opened from {s.valid_from.isoformat()} 00:00 CT through "
               f"{s.valid_to.isoformat()} 23:59 CT" if v1
               else f"tickets opened on or after {s.valid_from.isoformat()} 00:00 CT")  # fmt: skip
    body = f"""
# Northstar Support Service Level Schedule v{s.version}

## 1. Application

This version applies to {applies}. The version is chosen by the ticket's **open time in Central
Time**, and nothing else. A ticket keeps its version for its whole life, including credits, cap
and claim window, even if it is restored, claimed or decided after another version takes effect.
The UTC date of the open time, the restoration date and the claim date do not change the version.

## 2. Definitions

2.1 **Time zone.** All service-level times, business hours, deadlines and calendar dates are in US
Central Time (America/Chicago), written "CT". Central Standard Time is UTC−06:00 and Central
Daylight Time is UTC−05:00. CDT applied from 2025-03-09 to 2025-11-02, and from 2026-03-08. A
timestamp recorded in another zone (for example Eastern Daylight Time, UTC−04:00, or UTC in system
logs) is converted to CT before anything is measured. "Date" (the restoration date, the claim date
or a notice date) means the CT calendar date of the timestamp after conversion.

2.2 **Business hours** are 08:00 to 18:00 CT, Monday to Friday, except Northstar holidays (see the
Northstar holiday calendar). A business day is a Monday-to-Friday date that is not a Northstar
holiday. Every business day has exactly 10 business hours.

2.3 **Clocks.** Every ticket has a response clock and a restoration clock, which start together. A
24×7 clock counts all elapsed time; across a daylight-saving change it counts the actual elapsed
time. A business-hours clock counts only time inside business hours. Elapsed time is measured in
whole minutes. Pauses apply only to the restoration clock; maintenance exclusions apply to both.

2.4 **Met or missed.** A target elapses at the moment its clock reaches the target duration. A
target is met if the event happens at or before that moment, and missed if it happens after it.
An event exactly at the moment the target elapses meets it.

2.5 **Open time.** Every support request is a ticket in Northstar Service (SR-nnnnn). Its open time
is the moment a hotline call is answered, a portal submission is received, or an email to
support@northstar.example is received. When an incident actually began (if earlier) is not the open
time and starts no clock.

2.6 **Initial response** is the first communication to the customer, by telephone or as a ticket
comment, from a Northstar support engineer that addresses the specific issue. A request from an
engineer for information, access or an action counts. Automated acknowledgments, auto-replies and
ticket-creation notices do not count, and neither does a call made by the customer.

2.7 **Restoration** is the moment the affected product is returned to production use, as recorded
in Northstar Service, through a fix or through a workaround that removes the business impact on
which the severity was based. A later permanent fix is not measured. For a Severity 1 ticket, a
workaround that lets production or operations resume counts as restoration even if it needs ongoing
manual effort; the ticket is then reclassified as Severity 2 at that moment.

## 3. Targets

{table(["Severity", "Initial response", "Restoration", "Clock"], rows)}

Severity 1 always runs on the 24×7 clock. Severity 2 runs on the 24×7 clock under the Platinum plan
and on the business-hours clock under the Silver plan. Severities 3 and 4 run on the
business-hours clock.

## 4. Clock start and pauses

4.1 Both clocks start at the open time on a 24×7 clock. On a business-hours clock they start at the
open time if that is inside business hours, and otherwise at the next start of business hours.

4.2 An initial response or restoration that happens before the clock starts is treated as
happening at elapsed time zero, so the target is met.

4.3 The restoration clock (not the response clock) pauses while the ticket is in "Awaiting
Customer" status: from when a Northstar engineer records in the ticket a request to the customer for
information, access or an action Northstar needs, until the customer's reply, or the access or
action, is recorded. It also pauses when the customer asks in writing that Northstar stop work
until a stated time. A pause counts only if both its start and its end are recorded in the ticket.
Waiting on anything else (Northstar staff, spare parts, vendors, a software release) never pauses
either clock. On a business-hours clock, a pause removes only the business hours inside it.

4.4 On a Severity 1 ticket, a recorded failed telephone attempt to reach the customer's designated
technical contact pauses the restoration clock until contact is re-established, as recorded.

## 5. Exclusions

Only these two exclusions exist. No other circumstance excuses a missed target.

5.1 **Scheduled maintenance.** A maintenance window qualifies only if Northstar sent the customer's
designated support contacts a written notice stating the window's start and end and the products
affected, at least **{s.notice_business_days} business days** before the window starts. Count the
business days after the notice's sent date, up to and including the window's start date. Notices are
recorded in Northstar Service with an MN-nnnn number; with no notice record there is no exclusion.
For the products named, time inside a qualifying window is not counted on either clock. A ticket
opened inside the window starts both clocks at the window's end (on a business-hours clock, at the
later of the window's end and the next start of business hours). Time after the window counts
normally, even if the maintenance caused the incident.

5.2 **Customer-caused incidents.** An incident caused by an unapproved customer change to
configuration, firmware or network settings, by customer-provided infrastructure, or by use contrary
to Northstar's documentation, is customer-caused. Then the restoration target does not apply (no
restoration breach or credit); the response target and any response credit still apply; escalation
is not affected. The exclusion applies only if Northstar asserts it in the ticket and the Support
Engineering Lead records a root-cause finding naming the cause, by 18:00 CT on the 10th business
day after the restoration date (the first business day after is day 1). If the finding attributes
the incident to anything else, or no finding is recorded by the deadline, the ticket is decided as
if the exclusion had never been asserted. While the exclusion is asserted, no finding is recorded
and the deadline has not passed, neither the restoration breach nor any restoration credit can be
decided.

## 6. Service credits

6.1 A service credit is a percentage of the customer's monthly support fee for the CT calendar month
in which the ticket was **opened**.

{credit_note}{table(["Missed target", "Severity 1", "Severity 2"], credit_rows)}

6.2 The response credit and the restoration credit for one ticket are added together. Severity 3
and 4 tickets earn no service credits.

6.3 Severity 1 credit percentages apply only if the customer reported the incident by telephone to
the Support hotline before restoration. Otherwise the Severity 2 percentages apply, while whether
each target was missed (and any restoration band) is still measured against the Severity 1 targets.

6.4 **Monthly cap.** Total credits for one customer, for all tickets opened in one CT calendar month,
may not exceed **{s.cap_pct:.0%}** of that month's support fee. Credits count toward the cap in the
order they are approved; a credit that would exceed the cap is reduced to the amount remaining, and
any excess is forfeited.

6.5 No credit is owed unless the customer submits a timely claim; credits are never applied
automatically. Service credits are the sole and exclusive remedy for a missed target, issued as a
credit memo against the next support invoice, rounded to the nearest cent.

6.6 The Director of Customer Support decides every credit claim and sends a written decision
(approved with the amount, or declined with the reason) no later than the 30th calendar day after
the claim was received. For an approved credit, the Support Billing Manager issues the credit memo
by the same day. The day after the receipt date is day 1.

## 7. Customer obligations

7.1 The customer must report a Severity 1 incident by telephoning the Support hotline, {HOTLINE},
staffed 24×7. A portal submission or email is not a telephone report, and neither is a call from
Northstar to the customer.

7.2 A credit claim must be in writing (email to support-credits@northstar.example, or a portal
credit claim) and name the ticket. It must be received no later than 23:59 CT on the last day of
the window: **{s.claim_days} calendar days** after the restoration date (the day after is day 1).
Weekends and holidays count and do not extend the window. A late claim earns no credit.

7.3 The customer must provide the information and access Northstar needs, and on a Severity 1
ticket keep a technical contact reachable by telephone until restoration.
"""  # noqa: E501
    return Artifact(
        id=s.id,
        path=f"documents/{s.id}.md",
        source_system=DRIVE,
        description=f"Support service level schedule, version {s.version}.",
        content=document(
            {
                "doc_id": f"SLA-SCHEDULE-{s.version}",
                "title": s.title,
                "owner": "Customer Support",
                "created": s.published.isoformat(),
                "effective_from": s.valid_from.isoformat(),
                "effective_to": s.valid_to.isoformat(),
            },  # fmt: skip
            body,
        ),
        supports=(s.id,),
    )


def _severity_guide() -> Artifact:
    body = """
# Support Severity Guide

Northstar Support classifies severity from the business impact recorded in the ticket (its
description and notes). Test the definitions in order; the severity is the first one the recorded
impact meets.

## Severity 1: Critical

A Northstar product failure that, with **no workaround available**, either (a) stops the customer's
production or operations (a production line, a plant process, or a distribution, dispatch or
facility-operations activity cannot continue), or (b) makes NS-Cloud unavailable to **all** of the
customer's users.

## Severity 2: High

Not Severity 1, and any one of: (a) production or operations continue but are materially degraded;
(b) a control, alarming or condition-monitoring function is unavailable (not merely intermittent)
for one or more machines, lines, buildings or sites, whether or not the customer covers it with
manual checks; (c) NS-Cloud is unavailable to some, but not all, of the customer's users or sites;
(d) a Severity 1 condition with a workaround in place that needs ongoing manual effort.

## Severity 3: Medium

Not Severity 1 or 2: a function is impaired with no reduction in production output and no loss of a
control, alarming or monitoring function (intermittent faults with backfilled data, slow
performance, a failing report, a single-user error).

## Severity 4: Low

A question, how-to, documentation issue, cosmetic defect or enhancement request, with no effect on
operations.

## Who decides

The customer's reported priority (P1 to P4) is only the customer's view: it does not set the
severity and has no effect on targets, credits or escalations. Northstar may correct the severity
up or down at any time. If the impact recorded at opening meets a different severity, that severity
governs from the open time, with its clock, targets, credits and escalations. If the impact changes
after opening, the ticket is reclassified at the moment the change is recorded.
"""
    return Artifact(
        id="support_severity_guide",
        path="documents/support_severity_guide.md",
        source_system=DRIVE,
        description="How Northstar Support classifies ticket severity.",
        content=document(
            {
                "doc_id": "SUP-SEVERITY-GUIDE",
                "title": "Support Severity Guide",
                "owner": "Customer Support",
                "created": "2024-12-15",
            },
            body,
        ),  # fmt: skip
        supports=("support_severity_guide",),
    )


def _escalation_procedure() -> Artifact:
    body = """
# Support Escalation Procedure

Escalation follows the ticket's true severity and is timed on the ticket's own clocks: deadlines
tied to the response on the response clock, deadlines tied to restoration on the restoration clock
(paused time does not count), and a qualifying maintenance window delays both. The customer-caused
exclusion and the telephone rule do not affect escalation. Each deadline is the latest compliant
time. "Engage" means assign the person to the ticket and confirm it there; "notify" means send a
message recorded in the ticket. Thresholds use the restoration target of the ticket's schedule
version.

## Severity 1

1. Engage the **Support Escalation Manager** as incident lead no later than 15 minutes after clock
   start.
2. Notify the **account owner** (as recorded in Northstar CRM) no later than 30 minutes after clock
   start.
3. If the ticket is not restored when 50% of the restoration target has elapsed, notify the
   **Director of Customer Support** no later than that moment.
4. If the ticket is not restored when 100% of the restoration target has elapsed, notify the
   **VP Sales** no later than that moment, and, for a **Strategic** account (CRM account tier), the
   **Chief Revenue Officer** as well.

## Severity 2

1. If there has been no initial response when the response target elapses, notify the **Support
   Escalation Manager** no later than that moment.
2. If the ticket is not restored when the restoration target elapses, notify the **Director of
   Customer Support** and the **account owner** no later than that moment.

## Severity 3 and 4

On a Severity 3 ticket not restored when the restoration target elapses, notify the **Support
Escalation Manager** no later than that moment. Severity 4 has no escalation.

## Tickets outside a support agreement

A ticket is in scope only if its customer (identified by CRM account id, ERP customer id or DUNS,
never by name alone) has a support agreement covering the ticket's product, and the ticket was
opened on or after the coverage start. Out-of-scope tickets are handled best effort: severity is
classified only for internal priority, no targets apply (nothing can be breached and no credit is
owed), and the escalations above do not apply. Northstar Support must notify the **account owner**
of the ticket's CRM account no later than 10 business hours after the open time. Any credit claim
is declined, and the decision is sent as for any claim.

## Root cause and claims

When Northstar asserts the customer-caused exclusion, the **Support Engineering Lead** records the
root-cause finding by the deadline in the Service Level Schedule. For every credit claim, the
**Director of Customer Support** sends the written decision, and for an approved credit the
**Support Billing Manager** issues the credit memo, by the deadlines in the Service Level Schedule.

## When a decision can't be made

A determination can't be made when a fact it depends on is missing from the ticket record and no
default applies: the customer's identifiers when names are ambiguous, the open time, the
initial-response time, the restoration time, the business-impact description, or a root-cause
finding while one is pending. Record "cannot decide: missing X" for it and for everything that
depends on it, and make all the other determinations. These have defaults: no recorded pause means
no pause; no notice record means no maintenance exclusion; an exclusion not asserted does not apply;
no telephone report recorded means none was made; no claim yet means no credit is owed yet (state
the credit that would be owed and the last day to claim it).
"""
    return Artifact(
        id="support_escalation_procedure",
        path="documents/support_escalation_procedure.md",
        source_system=DRIVE,
        description="Support escalation and claim duties, by role.",
        content=document(
            {
                "doc_id": "SOP-SUPPORT-007",
                "title": "Support Escalation Procedure",
                "owner": "Customer Support",
                "created": "2024-12-15",
            },
            body,
        ),  # fmt: skip
        supports=("support_escalation_procedure",),
    )


def _org_chart(truth: Truth) -> Artifact:
    domain = truth.organization.email_domain
    rows = [[e.name, truth.role_title(e.role), e.email(domain)] for e in truth.employees
            if e.department == "Customer Support"]  # fmt: skip
    rows += [[truth.employee(i).name, truth.role_title(truth.employee(i).role),
              truth.employee(i).email(domain)] for i in ("EMP-200", "EMP-300")]  # fmt: skip
    body = f"""
# Support Organization and Escalation Contacts

Each escalation role has exactly one holder. Account owners are as recorded in Northstar CRM.

{table(["Name", "Role", "Email"], rows)}

The Director of Customer Support leads the support organization; the other support roles report to
the Director.
"""
    return Artifact(
        id="support_org_chart",
        path="documents/support_org_chart.md",
        source_system=DRIVE,
        description="Who holds each support escalation role.",
        content=document(
            {
                "doc_id": "ORG-SUPPORT-2026",
                "title": "Support Organization and Escalation Contacts",
                "owner": "People Operations",
                "created": "2025-01-02",
            },
            body,
        ),  # fmt: skip
        supports=("support_org_chart",),
    )


def _holidays(truth: Truth) -> Artifact:
    rows = [[h.date.isoformat(), h.date.strftime("%A"), h.name] for h in truth.holidays]
    body = f"""
# Northstar Holiday Calendar, 2025–2026

This list is complete. No other day is a Northstar holiday.

{table(["Date", "Day", "Holiday"], rows)}
"""
    return Artifact(
        id="holiday_calendar",
        path="documents/holiday_calendar.md",
        source_system=DRIVE,
        description="Northstar holidays for 2025 and 2026.",
        content=document(
            {
                "doc_id": "HR-HOLIDAYS-2025-26",
                "title": "Northstar Holiday Calendar",
                "owner": "People Operations",
                "created": "2024-11-15",
            },
            body,
        ),  # fmt: skip
        supports=("holiday_calendar",),
    )


def _terms(truth: Truth, a: SupportAgreement) -> Artifact:
    c = truth.customer(a.customer)
    products = ", ".join(f"{truth.product(p).name} ({truth.product(p).sku})" for p in a.products)
    fees = "; ".join(f"{usd(f.monthly_usd)} per month from {f.from_month}" for f in a.fees)
    acme = a.customer == "CUST-1001"
    extra = (
        "\n\nCoverage does not extend to the Customer's parent, Acme Group Holdings, Inc., or to "
        "any other affiliate. Acme Industrial Supply Co. is a different company and is not "
        "covered. NS-Cloud Operations Suite is not a covered product; it could be added only "
        "by a signed amendment to this Schedule."
        if acme else ""
    )  # fmt: skip
    title = (f"Schedule C (Support and Service Levels) — {c.canonical_name}" if acme
             else f"{c.canonical_name} Support Terms")  # fmt: skip
    body = f"""
# {title}

**Reference:** {a.reference}

Northstar Industrial Systems provides support to **{c.erp_name}** (DUNS {c.duns}), {c.address.city},
{c.address.state} ("Customer").

| Term | Value |
|---|---|
| Support plan | {a.plan} |
| Covered products | {products} |
| Coverage starts | {a.coverage_start.isoformat()} 00:00 CT |
| Monthly support fee | {fees} |

Service levels, credits and customer obligations are as set out in the Northstar Support Service
Level Schedule version that applies to each ticket. The support plan is a support term; it is
unrelated to the Customer's account tier.{extra}
"""
    return Artifact(
        id=a.document,
        path=f"documents/{a.document}.md",
        source_system=DRIVE,
        description=f"Support terms for {c.canonical_name}.",
        content=document(
            {
                "doc_id": a.id,
                "title": title,
                "owner": "Legal",
                "created": a.coverage_start.isoformat(),
            },
            body,
        ),  # fmt: skip
        supports=(a.document,),
    )


def _ts(t: datetime | None) -> str | None:
    return t.isoformat() if t else None


def _tickets(truth: Truth) -> Artifact:
    header = ["ticket_id", "account_id", "customer_on_ticket", "site", "product_sku", "channel",
              "contact", "opened_at", "reported_priority", "description", "status",
              "restored_at"]  # fmt: skip
    rows = [[t.id, t.account, t.label, t.site, truth.product(t.product).sku, t.channel, t.caller,
             _ts(t.opened), t.reported_priority, t.description,
             "Restored" if t.restored else "Open", _ts(t.restored)]
            for t in truth.tickets]  # fmt: skip
    return Artifact(
        id="service_tickets",
        path="structured/service_tickets.csv",
        source_system=SERVICE,
        description="Support tickets: account, product, channel, open and restoration times.",
        content=to_csv(header, rows),
        supports=("service_tickets",),
    )


def _ticket_events(t: Ticket) -> list[list[str | None]]:
    ev: list[tuple[datetime, str, str, str]] = [
        (t.opened, "created", t.caller, f"Ticket opened by {t.channel}; reported priority "
                                        f"{t.reported_priority}."),
    ]  # fmt: skip
    if t.auto_ack:
        ev.append((t.auto_ack, "auto_acknowledgment", "system", "Ticket-creation email sent "
                                                                "automatically."))  # fmt: skip
    if t.first_response:
        ev.append((t.first_response, "engineer_response", "Northstar support engineer",
                   t.first_response_note))  # fmt: skip
    for p in t.pauses:
        if p.start:
            ev.append((p.start, "status_change", "Northstar support engineer",
                       "Status set to Awaiting Customer. " + p.note))  # fmt: skip
        if p.end:
            ev.append((p.end, "status_change", t.caller, "Customer provided what was requested; "
                                                         "status set to In Progress."))  # fmt: skip
    for n in t.notes:
        ev.append((n.at, "note", n.actor, n.text))
    if t.restored:
        ev.append((t.restored, "restored", "Northstar support engineer", t.restored_note))
    if t.root_cause:
        ev.append((t.root_cause.at, "root_cause_finding", "Support Engineering Lead",
                   t.root_cause.text))  # fmt: skip
    if t.claim:
        ev.append((t.claim.received, "credit_claim", t.claim.sender,
                   f"Credit claim received by {t.claim.channel}: {t.claim.text}"))  # fmt: skip
    ev.sort(key=lambda e: e[0])
    return [[t.id, e[0].isoformat(), e[1], e[2], e[3]] for e in ev]


def _events(truth: Truth) -> Artifact:
    rows = [r for t in truth.tickets for r in _ticket_events(t)]
    return Artifact(
        id="ticket_events",
        path="structured/ticket_events.csv",
        source_system=SERVICE,
        description="Ticket history: responses, status changes, notes, restoration and claims.",
        content=to_csv(["ticket_id", "at", "event", "actor", "detail"], rows),
        supports=("ticket_events",),
    )


def _notices(truth: Truth) -> Artifact:
    rows = []
    for n in truth.maintenance_notices:
        crm = truth.customer(n.customer).source_ids["crm"]
        skus = ";".join(truth.product(p).sku for p in n.products)
        rows.append([n.id, crm, skus, n.sent.isoformat(), n.window_start.isoformat(),
                     n.window_end.isoformat(), f"{truth.product(n.products[0]).name} platform "
                     "upgrade."])  # fmt: skip
    return Artifact(
        id="maintenance_notices",
        path="structured/maintenance_notices.csv",
        source_system=SERVICE,
        description="Scheduled maintenance notices sent to customers.",
        content=to_csv(
            [
                "notice_id",
                "account_id",
                "products",
                "sent_at",
                "window_start",
                "window_end",
                "notice",
            ],
            rows,
        ),  # fmt: skip
        supports=("maintenance_notices",),
    )


def _credits(truth: Truth) -> Artifact:
    rows = [[c.id, c.ticket, truth.customer(c.customer).source_ids["crm"],
             c.ticket_opened.isoformat(), f"{c.amount_usd:.2f}", c.approved_on.isoformat()]
            for c in truth.service_credits]  # fmt: skip
    return Artifact(
        id="service_credits",
        path="structured/service_credits.csv",
        source_system=SERVICE,
        description="Service credits already approved.",
        content=to_csv(
            ["credit_id", "ticket_id", "account_id", "ticket_opened", "amount_usd", "approved_on"],
            rows,
        ),  # fmt: skip
        supports=("service_credits",),
    )
