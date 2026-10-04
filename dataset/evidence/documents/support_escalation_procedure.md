---
doc_id: SOP-SUPPORT-007
title: Support Escalation Procedure
owner: Customer Support
created: '2024-12-15'
---

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
