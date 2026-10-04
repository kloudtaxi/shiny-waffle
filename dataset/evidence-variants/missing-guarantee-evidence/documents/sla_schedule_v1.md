---
doc_id: SLA-SCHEDULE-1.0
title: Northstar Support Service Level Schedule v1.0
owner: Customer Support
created: '2025-01-01'
effective_from: '2025-01-01'
effective_to: '2026-03-31'
---

# Northstar Support Service Level Schedule v1.0

## 1. Application

This version applies to tickets opened from 2025-01-01 00:00 CT through 2026-03-31 23:59 CT. The version is chosen by the ticket's **open time in Central
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

| Severity | Initial response | Restoration | Clock |
|---|---|---|---|
| 1 | 1 hour | 8 hours | 24×7 |
| 2, Platinum plan | 4 hours | 24 hours | 24×7 |
| 2, Silver plan | 4 business hours | 24 business hours | Business hours |
| 3 | 8 business hours | 50 business hours | Business hours |
| 4 | 20 business hours | No restoration target | Business hours |

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
affected, at least **3 business days** before the window starts. Count the
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

| Missed target | Severity 1 | Severity 2 |
|---|---|---|
| Initial response | 5% | 2% |
| Restoration | 10% | 5% |

6.2 The response credit and the restoration credit for one ticket are added together. Severity 3
and 4 tickets earn no service credits.

6.3 Severity 1 credit percentages apply only if the customer reported the incident by telephone to
the Support hotline before restoration. Otherwise the Severity 2 percentages apply, while whether
each target was missed (and any restoration band) is still measured against the Severity 1 targets.

6.4 **Monthly cap.** Total credits for one customer, for all tickets opened in one CT calendar month,
may not exceed **20%** of that month's support fee. Credits count toward the cap in the
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

7.1 The customer must report a Severity 1 incident by telephoning the Support hotline, (312) 555-0187,
staffed 24×7. A portal submission or email is not a telephone report, and neither is a call from
Northstar to the customer.

7.2 A credit claim must be in writing (email to support-credits@northstar.example, or a portal
credit claim) and name the ticket. It must be received no later than 23:59 CT on the last day of
the window: **60 calendar days** after the restoration date (the day after is day 1).
Weekends and holidays count and do not extend the window. A late claim earns no credit.

7.3 The customer must provide the information and access Northstar needs, and on a Severity 1
ticket keep a technical contact reachable by telephone until restoration.
