# Northstar Support: Service Level Rules (rule sheet)

Ground truth for experiment 6 (SLA breach response). The company is the fictional Northstar
Industrial Systems, Chicago, Illinois.

These rules decide six things for one support ticket:

1. the ticket's true severity;
2. whether a service level was breached;
3. what Northstar owes the customer as a remedy, and by when;
4. who at Northstar must be engaged or notified, and by when;
5. what the customer must do, and whether it did;
6. whether the decision can be made from the record, and if not, what is missing.

The rules cover tickets opened from 2025-01-01 00:00 CT to 2026-09-30 23:59 CT. Every rule
is numbered (R1 to R55) so it can be cited. Where a rule says "these rules", it means this sheet.

---

## Part A: Conventions

**R1. Time zone.** All SLA times, business hours, deadlines and calendar dates are in US
Central Time (America/Chicago), written "CT":

- Central Standard Time (CST) is UTC−06:00. Central Daylight Time (CDT) is UTC−05:00.
- CDT applied from 2025-03-09 to 2025-11-02, and again from 2026-03-08 to the end of the period
  these rules cover. CST applied at all other times in the period.
- A timestamp recorded in another zone is converted to CT before anything is measured.
  Examples are Eastern Daylight Time (EDT, UTC−04:00, one hour ahead of CDT), used by Cedar
  Health Systems (Indianapolis, IN) and Acme Industrial Supply Co. (Akron, OH), and UTC in
  system logs.
- "Date" (for example the restoration date, the claim date or a notice date) always means the
  CT calendar date of the timestamp after conversion.

**R2. Business hours.** Business hours are 08:00 to 18:00 CT, Monday to Friday, except
Northstar holidays (R3). A business day is a Monday-to-Friday date that is not a Northstar
holiday. Every business day has exactly 10 business hours.

**R3. Northstar holidays.** This list is complete for the period these rules cover. No other
day is a holiday.

| Date | Day | Holiday |
|---|---|---|
| 2025-01-01 | Wednesday | New Year's Day |
| 2025-05-26 | Monday | Memorial Day |
| 2025-07-04 | Friday | Independence Day |
| 2025-09-01 | Monday | Labor Day |
| 2025-11-27 | Thursday | Thanksgiving Day |
| 2025-11-28 | Friday | Day after Thanksgiving |
| 2025-12-25 | Thursday | Christmas Day |
| 2026-01-01 | Thursday | New Year's Day |
| 2026-05-25 | Monday | Memorial Day |
| 2026-07-03 | Friday | Independence Day (observed; July 4 is a Saturday) |
| 2026-09-07 | Monday | Labor Day |

**R4. Clocks.** Every ticket has a **response clock** and a **restoration clock**. Both start
together (R24).

- A **24×7 clock** counts all elapsed time. Where an interval spans a daylight-saving change,
  it counts the actual elapsed time.
- A **business-hours clock** counts only time inside business hours (R2).
- All elapsed time is measured in whole minutes.
- Pauses (R26, R27) apply only to the restoration clock. Maintenance exclusions (R30) apply
  to both clocks.

**R5. Met or missed.** A target "elapses" at the moment its clock reaches the target
duration. A target is **met** if the event (initial response or restoration) happens at or
before that moment, and **missed** if it happens after it. An event exactly at the moment
the target elapses meets it.

**R6. Ticket and open time.** Every support request is a ticket in Northstar Service, numbered
`SR-nnnnn`. The ticket's **open time** is set by how the request arrived:

- by telephone to the Support hotline: the moment the call is answered;
- by the customer portal: the moment the submission is received;
- by email to support@northstar.example: the moment the email is received.

When an incident actually began (if earlier) is not the open time and starts no clock.

**R7. Initial response.** The initial response is the first communication to the customer, by
telephone or as a ticket comment, from a Northstar support engineer that addresses the
specific issue.

- A request from an engineer for information, access or an action counts as the initial
  response.
- Automated acknowledgments, auto-replies and ticket-creation notices do not count.
- A call made by the customer does not count.

**R8. Restoration.** Restoration is the moment the affected product is returned to production
use, as recorded in Northstar Service. That can happen through a fix, or through a workaround
that removes the business impact on which the ticket's severity was based.

- (a) A later permanent fix is not measured.
- (b) For a Severity 1 ticket, a workaround that lets production or operations resume counts as
  restoration even if it needs ongoing manual effort. In that case the ticket is reclassified as
  Severity 2 at the restoration moment, and R19(b) applies to the remaining impact.

---

## Part B: Scope

**R9. When the SLA applies.** These rules' targets, credits and SLA escalations apply to a
ticket only if all three of the following are true:

- (a) the ticket's customer is one of the covered customers in R11, identified as R10 requires;
- (b) the ticket is about a product listed as covered for that customer in R11;
- (c) the ticket was opened on or after the date that customer's coverage starts (R11).

A ticket that fails any of (a) to (c) is **out of scope** and is handled under R12.

**R10. Customer identity.** A customer is identified by its CRM account id, its ERP customer id
or its DUNS number, and never by name alone. Display names, legal names and similar names
are not identifiers.

- Acme Manufacturing appears under several names: "ACME Manufacturing", "Acme Mfg.", "ACME Mfg"
  and its legal name "Acme Mfg. Holdings". All of them are CRM-2048, ERP C-1001, DUNS
  04-812-7730, Milwaukee, WI.
- **Acme Industrial Supply Co.**, also shown as "Acme Industrial", is a **different company**:
  CRM-2091, ERP C-1044, DUNS 09-552-1187, Akron, OH. It has no support agreement. Acme
  Manufacturing's support agreement does not cover it, whatever the ticket or the caller says.
- Acme Manufacturing's coverage does not extend to its parent, Acme Group Holdings, Inc., or to
  any other affiliate.
- R11 is the complete list of covered customers. Buying any Northstar product, including the
  NS-760 Premium Support Plan item, does not by itself create coverage under these rules.

**R11. Covered customers.** The monthly support fee is the base for service credits (R33).

| | Acme Manufacturing | BlueRiver Logistics | Cedar Health Systems |
|---|---|---|---|
| Legal name (ERP) | Acme Mfg. Holdings | Blue River Logistics LLC | Cedar Health Systems Inc. |
| CRM account | CRM-2048 | CRM-2051 | CRM-2063 |
| ERP customer | C-1001 | C-1002 | C-1003 |
| DUNS | 04-812-7730 | 07-331-9025 | 02-906-4418 |
| Location (time zone) | Milwaukee, WI (Central) | St. Louis, MO (Central) | Indianapolis, IN (Eastern) |
| CRM account tier | Strategic | Standard | Standard |
| Account owner (CRM) | Sarah Chen | Kelly Floyd | Anthony Day |
| Support agreement | Schedule C (Support and Service Levels) to ACME-MFG-2025 | SUP-BRL-2025 | SUP-CHS-2025 |
| Coverage starts | 2025-04-01 00:00 CT | 2025-01-01 00:00 CT | 2025-12-01 00:00 CT |
| Coverage ends | Not within the period these rules cover | Not within the period | Not within the period |
| Support plan | **Platinum** | **Silver** | **Silver** |
| Covered products | NS-500 Industrial Controller (NS-500); NS-Edge Monitoring Package (NS-EDGE) | NS-Cloud Operations Suite (NS-CLOUD) | NS-Cloud Operations Suite (NS-CLOUD); NS-Edge Monitoring Package (NS-EDGE) |
| Monthly support fee | $18,000 for each month from 2025-04 to 2025-12; $21,000 for each month from 2026-01 | $2,500 for each month from 2025-01 | $4,000 for each month from 2025-12 |

Notes:

- Acme Manufacturing had no support agreement before 2025-04-01.
- NS-Cloud is **not** a covered product for Acme Manufacturing. It could be added only by a
  signed amendment to Schedule C, and no such amendment exists in the period.
- The account owner of the out-of-scope customer Acme Industrial Supply Co. (CRM-2091) is
  Zachary Brown. R12(d) uses this.
- The support plan ("Platinum" or "Silver") is a support term. It is unrelated to the CRM
  account tier ("Strategic" or "Standard").

**R12. Out-of-scope tickets.** For a ticket that fails R9:

- (a) Northstar handles it on a best-effort basis. Northstar still classifies its severity under
  Part C, but only to set internal priority.
- (b) No response target or restoration target applies, so nothing can be breached and no
  service credit is owed.
- (c) The SLA escalation duties in R47 to R49 do not apply.
- (d) Northstar Support must notify the account owner of the ticket's CRM account no later than
  10 business hours after the open time. The business-hours clock starts under R24(b).
- (e) Any credit claim is declined, and the decision is sent under R41.

---

## Part C: Severity

**R13. Severity levels.** There are four severity levels, 1 (highest) to 4. Test the
definitions in order R14, R15, R16, R17. The ticket's severity is the first definition its
recorded business impact meets.

**R14. Severity 1: Critical.** A Northstar product failure that does either of the following,
with **no workaround available**:

- (a) stops the customer's production or operations, meaning a production line, a plant process,
  or a distribution, dispatch or facility-operations activity cannot continue; or
- (b) makes NS-Cloud unavailable to **all** of the customer's users.

**R15. Severity 2: High.** Not Severity 1, and any one of the following:

- (a) production or operations continue but are materially degraded, for example a line or
  process running below normal output;
- (b) a control, alarming or condition-monitoring function is unavailable (not merely
  intermittent) for one or more machines, lines, buildings or sites, whether or not the customer
  covers it with manual checks;
- (c) NS-Cloud is unavailable to some, but not all, of the customer's users or sites;
- (d) a Severity 1 condition with a workaround in place that needs ongoing manual effort.

**R16. Severity 3: Medium.** Not Severity 1 or 2, and a function is impaired with no reduction
in production output and no loss of a control, alarming or monitoring function. Examples:
intermittent faults where the data is backfilled, slow performance, a failing report, an error
that affects a single user.

**R17. Severity 4: Low.** Not Severity 1, 2 or 3. A question, how-to request, documentation
issue, cosmetic defect or enhancement request, with no effect on operations.

**R18. Who classifies, and from what.** Northstar Support classifies severity from the business
impact recorded in the ticket (its description and notes).

- The customer's reported priority (P1 to P4, entered in the portal or stated on a call) is
  only the customer's view. It does not set the severity and has no effect on targets, credits
  or escalations.
- Northstar may correct the severity up or down at any time.
- The severity that R13 to R17 give is the ticket's **true severity**.

**R19. Effect of a correction.**

- (a) **Impact recorded at opening.** If the business impact recorded at opening meets a
  different severity from the one first assigned or reported, the true severity governs from
  the open time, as if it had been assigned at opening. Its clock type, clock start, targets,
  credits and escalations all apply retroactively.
- (b) **Impact changes after opening.** If the business impact changes after opening, Northstar
  reclassifies the ticket at the moment the change is recorded.
  - From that moment, the new severity's restoration target and its escalations run on the new
    severity's clock.
  - An initial response already given counts as the initial response for the new severity.
    If none has been given, the new severity's response target also runs from that moment.

---

## Part D: Service level schedule

**R20. Schedule versions.** The Northstar Support Service Level Schedule has two versions in
the period. The version is chosen by the ticket's **open time in CT**, and nothing else:

| Version | Applies to tickets opened | Published |
|---|---|---|
| **v1.0** | 2025-01-01 00:00 CT through 2026-03-31 23:59 CT | in force on 2025-01-01 |
| **v2.0** | on or after 2026-04-01 00:00 CT | 2026-02-16 |

A ticket keeps its version for its whole life, including credits, cap and claim window, even if
it is restored, claimed or decided after the next version takes effect. The UTC date of the
open time, the restoration date and the claim date do not change the version.

These values depend on the version:

| Item | v1.0 | v2.0 | Rule |
|---|---|---|---|
| Response and restoration targets | see R21 | see R22 | R21, R22 |
| Maintenance notice lead time | 3 business days | 5 business days | R29 |
| Credit percentages | see R34 | see R35 | R34, R35 |
| Monthly credit cap | 20% of the monthly fee | 30% of the monthly fee | R38 |
| Credit claim window | 60 calendar days | 30 calendar days | R43 |

All other rules, including the escalation procedure (Part I), apply to both versions. Where an
escalation threshold refers to a target, it means the target of the ticket's own version.

**R21. Targets, v1.0.**

| Severity | Initial response | Restoration | Clock |
|---|---|---|---|
| 1 | 1 hour | 8 hours | 24×7 |
| 2, Platinum plan | 4 hours | 24 hours | 24×7 |
| 2, Silver plan | 4 business hours | 24 business hours | Business hours |
| 3 | 8 business hours | 50 business hours | Business hours |
| 4 | 20 business hours | No restoration target | Business hours |

**R22. Targets, v2.0.**

| Severity | Initial response | Restoration | Clock |
|---|---|---|---|
| 1 | 30 minutes | 4 hours | 24×7 |
| 2, Platinum plan | 2 hours | 12 hours | 24×7 |
| 2, Silver plan | 2 business hours | 12 business hours | Business hours |
| 3 | 8 business hours | 30 business hours | Business hours |
| 4 | 20 business hours | No restoration target | Business hours |

**R23. Which clock.** Severity 1 always runs on the 24×7 clock, on every plan. Severity 2 runs
on the 24×7 clock under the Platinum plan and on the business-hours clock under the Silver
plan. Severities 3 and 4 always run on the business-hours clock.

---

## Part E: Clock rules

**R24. Clock start.** Both clocks start:

- (a) on a 24×7 clock, at the open time;
- (b) on a business-hours clock, at the open time if that is inside business hours. Otherwise
  they start at the next start of business hours (08:00 CT on the next business day).

R19 (correction) and R30 (maintenance) can change the clock start.

**R25. Events before the clock starts.** An initial response or restoration that happens before
the clock starts is treated as happening at elapsed time zero, so the target is met.

**R26. Pause: awaiting customer.**

- (a) The **restoration clock** (not the response clock) pauses while the ticket is in "Awaiting
  Customer" status. The pause starts when a Northstar engineer records in the ticket a request
  to the customer for information, access or an action that Northstar needs in order to
  continue. It ends when the customer's reply, or the requested access or action, is recorded.
- (b) The restoration clock also pauses when the customer asks in writing that Northstar stop
  work until a stated time. The pause runs from the request until that time, or until the
  customer asks to resume, if that is earlier.
- (c) A pause counts only if both its start and its end are recorded in the ticket. A pause
  with either one missing does not count.
- (d) Waiting on anything else never pauses either clock. That includes waiting on Northstar
  staff, spare parts, Northstar's vendors or a Northstar software release.
- (e) On a business-hours clock, a pause removes only the business hours that fall inside it.

**R27. Pause: Severity 1 contact unreachable.** On a Severity 1 ticket, suppose Northstar records
a failed telephone attempt to reach the customer's designated technical contact. The
restoration clock then pauses from that failed attempt until contact is re-established, as
recorded. R26(c) applies.

---

## Part F: Exclusions

**R28. Exclusions are complete.** Only the two exclusions in R29 to R32 exist: scheduled
maintenance and customer-caused incidents. No other circumstance excuses a missed target.

**R29. Scheduled maintenance: when a window qualifies.** A maintenance window qualifies only if
Northstar sent the customer's designated support contacts a written notice that:

- states the window's start and end times and the products affected; and
- was sent at least **N business days** before the window starts. N is 3 under v1.0 and 5
  under v2.0, using the version of the ticket being measured.

To count, take the business days after the notice's sent date, up to and including the
window's start date. The notice qualifies if that count is N or more.

Notices are recorded in Northstar Service with an `MN-nnnn` number and the sent timestamp.
Maintenance announced with less notice, including emergency maintenance, does not qualify.
If there is no notice record, there is no exclusion.

**R30. Scheduled maintenance: effect.** For the products named in a qualifying notice, time
inside the window is not counted on either clock for that customer's tickets about those
products.

- (a) For a ticket opened inside the window, both clocks start at the window's end. On a
  business-hours clock they start at the later of the window's end and the next start of
  business hours.
- (b) For a ticket already open when a window starts, the time inside the window is not counted.
- (c) Time after the window ends counts normally, even if the maintenance caused the incident.

**R31. Customer-caused incidents.** An incident is customer-caused if it was caused by any of
the following:

- (i) a change to the product's configuration, firmware or network settings that the customer
  or its contractors made without Northstar's written approval;
- (ii) a failure of infrastructure the customer provides (power, network or servers);
- (iii) use contrary to Northstar's documentation.

When this exclusion applies (as decided under R32):

- the restoration target does not apply, so there is no restoration breach and no restoration
  credit;
- the response target and any response credit still apply;
- escalation duties are not affected (R46(b)).

**R32. Root-cause finding.** Northstar can apply the customer-caused exclusion only if it
asserts the exclusion in the ticket and the Support Engineering Lead records a root-cause
finding that names the cause.

- The finding must be recorded no later than 18:00 CT on the 10th business day after the
  restoration date. The first business day after the restoration date is day 1.
- (a) If the finding attributes the incident to the customer under R31, the exclusion applies.
- (b) If the finding attributes the incident to anything else, or no finding is recorded by
  the deadline, the exclusion does not apply. The ticket is then decided as if the exclusion
  had never been asserted.
- (c) Suppose the exclusion has been asserted, no finding is recorded yet, and the deadline has
  not passed. Then neither whether the restoration target was breached nor any restoration
  credit can be decided (R54).
- If Northstar never asserted the exclusion, no finding is needed and the exclusion does not
  apply.

---

## Part G: Service credits

**R33. Credit base.** A service credit is a percentage of the customer's monthly support fee
(R11) for the CT calendar month in which the ticket was **opened**.

**R34. Credit percentages, v1.0.**

| Missed target | Severity 1 | Severity 2 |
|---|---|---|
| Initial response | 5% | 2% |
| Restoration | 10% | 5% |

**R35. Credit percentages, v2.0.** The restoration credit depends on the restoration elapsed
time, measured against the restoration target.

| Missed target | Severity 1 | Severity 2 |
|---|---|---|
| Initial response | 5% | 3% |
| Restoration, band 1: elapsed time more than the target and no more than 2× the target | 10% | 5% |
| Restoration, band 2: elapsed time more than 2× the target | 20% | 10% |

**R36. Combining credits.** The response credit and the restoration credit for one ticket are
added together. Severity 3 and Severity 4 tickets earn no service credits under either version.

**R37. Severity 1 reported without a phone call.** Severity 1 credit percentages apply only if
the customer reported the incident by telephone to the Support hotline (R42) at some time
before restoration. If it did not:

- the credits are calculated with the **Severity 2 percentages** of the ticket's version;
- whether each target was missed, and the v2.0 restoration band, are still measured against
  the **Severity 1 targets**;
- the true severity, the targets and the escalations do not change.

**R38. Monthly cap.** The total credits for one customer, for all tickets opened in one CT
calendar month, may not exceed **20%** (v1.0) or **30%** (v2.0) of that month's support fee.

- The version boundary falls on a month boundary, so every month has exactly one cap.
- Credits count toward the cap in the order they are approved. A credit that would take the
  month's total above the cap is reduced to the amount remaining under the cap.
- Any excess is forfeited and is not carried into another month.

**R39. A claim is required.** No credit is owed unless the customer submits a timely claim
(R43). Northstar does not apply credits automatically.

**R40. Form of the remedy.** Service credits are the customer's sole and exclusive remedy for a
missed target. A credit is issued as a credit memo against the customer's next support invoice
and is never paid in cash. Amounts are rounded to the nearest cent.

**R41. Claim decision and credit memo.**

- The Director of Customer Support decides every credit claim, including a claim from an
  out-of-scope customer.
- The Director sends a written decision (approved with the amount, or declined with the
  reason) no later than the 30th calendar day after the date the claim was received.
- For an approved credit, the Support Billing Manager issues the credit memo no later than the
  30th calendar day after the date the claim was received.
- The day after the receipt date is day 1.

---

## Part H: Customer obligations

**R42. Report a Severity 1 incident by telephone.** The customer must report a Severity 1
incident by telephoning the Northstar Support hotline, **(312) 555-0187**, which is staffed
24×7. A portal submission or an email is not a telephone report. A call from Northstar to the
customer is not a telephone report by the customer. If the customer does not phone, R37 applies.
Failing to phone does not change the severity, the targets or the escalations.

**R43. Claim a credit in writing, in time.**

- A claim must be in writing, either by email to support-credits@northstar.example or as a
  credit claim in the customer portal, and must name the ticket.
- It must be received no later than 23:59 CT on the last day of the window. The window is
  **60 calendar days** (v1.0) or **30 calendar days** (v2.0) after the restoration date. The day
  after the restoration date is day 1.
- Weekends and holidays count, and they do not extend the window.
- A claim received after the window earns no credit.
- A claim cannot be made before restoration.

**R44. Cooperate.** The customer must provide the information, remote access and on-site access
that Northstar needs. On a Severity 1 ticket, the customer must keep a technical contact
reachable by telephone until restoration. Time Northstar spends waiting on the customer is
handled only through the pauses in R26 and R27.

---

## Part I: Escalation

**R45. Escalation roles and holders.** This list is complete. Each role has exactly one holder
for the whole period these rules cover. No other role or person is an escalation target.

| Role | Holder | Email | Duties under these rules |
|---|---|---|---|
| Support Escalation Manager | **Hannah Lindqvist** | hannah.lindqvist@northstar.example | Incident lead on Severity 1 (R47(a)); notified when a Severity 2 response target is missed (R48(a)) or a Severity 3 restoration target is missed (R49) |
| Director of Customer Support | **Marcus Adeyemi** | marcus.adeyemi@northstar.example | Notified at the Severity 1 50% threshold (R47(c)) and when a Severity 2 restoration target is missed (R48(b)); decides every credit claim (R41) |
| Support Engineering Lead | **Owen Takahashi** | owen.takahashi@northstar.example | Records root-cause findings (R32, R51) |
| VP Sales | Michael Torres | michael.torres@northstar.example | Notified when a Severity 1 restoration target is missed (R47(d)) |
| Chief Revenue Officer | David Morgan | david.morgan@northstar.example | Notified as well when a Severity 1 restoration target is missed, for Strategic accounts only (R47(d)) |
| Support Billing Manager | **Paul Brennan** | paul.brennan@northstar.example | Issues credit memos against the customer's next support invoice (R41) |
| Account owner | The account owner recorded in CRM (R11): Sarah Chen for Acme Manufacturing, Kelly Floyd for BlueRiver Logistics, Anthony Day for Cedar Health Systems, Zachary Brown for Acme Industrial Supply Co. | (CRM) | Notified under R47(b), R48(b) and R50 |

**R46. How escalation is timed.**

- (a) Escalation follows the ticket's **true severity** (R18, R19).
- (b) Escalation deadlines are measured on the ticket's own clocks under Parts D to F:
  - deadlines tied to the response (R47(a), R47(b), R48(a)) are measured on the response clock;
  - deadlines tied to restoration (R47(c), R47(d), R48(b), R49) are measured on the restoration
    clock, so paused time does not count;
  - a qualifying maintenance window delays both clocks (R30);
  - the customer-caused exclusion (R31, R32) and the telephone rule (R37) do **not** affect
    escalation.
- (c) Each deadline is the latest compliant time. Acting earlier is compliant.
- (d) "Engage" means assign the person to the ticket and confirm it there. "Notify" means send
  the person a message that is recorded in the ticket.
- (e) The 50% and 100% thresholds use the restoration target of the ticket's version
  (R21, R22).

**R47. Severity 1 escalation.**

- (a) Engage the Support Escalation Manager as incident lead no later than **15 minutes**
  after clock start.
- (b) Notify the account owner no later than **30 minutes** after clock start.
- (c) If the ticket is not restored when **50%** of the Severity 1 restoration target has
  elapsed, notify the Director of Customer Support no later than that moment. That is 4 hours
  under v1.0 and 2 hours under v2.0.
- (d) If the ticket is not restored when **100%** of the Severity 1 restoration target has
  elapsed, notify the VP Sales no later than that moment. That is 8 hours under v1.0 and 4 hours
  under v2.0. If the customer's CRM account tier is **Strategic**, also notify the Chief
  Revenue Officer by the same moment.

**R48. Severity 2 escalation.**

- (a) If there has been no initial response when the response target elapses, notify the
  Support Escalation Manager no later than that moment.
- (b) If the ticket is not restored when the restoration target elapses, notify the Director of
  Customer Support and the account owner no later than that moment.

**R49. Severity 3 and 4 escalation.** On a Severity 3 ticket, if it is not restored when the
restoration target elapses, notify the Support Escalation Manager no later than that moment.
Severity 4 tickets have no escalation.

**R50. Out-of-scope tickets.** The only escalation duty is R12(d): notify the account owner no
later than 10 business hours after the open time.

**R51. Root-cause duty.** When Northstar asserts the customer-caused exclusion, the Support
Engineering Lead must record the root-cause finding by the deadline in R32.

**R52. Credit-claim duties.** For every claim, the Director of Customer Support sends the
written decision, and for an approved credit the Support Billing Manager issues the credit
memo, both by the deadlines in R41.

---

## Part J: Deciding

**R53. Order of decision.**

1. Identify the customer by its identifiers (R10).
2. Check scope (R9). If the ticket is out of scope, apply R12 and stop.
3. Determine the true severity (R13 to R19).
4. Determine the version (R20) and the plan (R11). From those, take the targets and clock type
   (R21 to R23).
5. Set the clock start (R24, R30).
6. Apply the pauses (R26, R27).
7. Apply the exclusions (R28 to R32).
8. Measure the initial response and the restoration against their targets (R4, R5, R25).
9. Calculate the credits (R33 to R37), then apply the cap (R38).
10. Check the claim (R39, R43) and set the decision and credit-memo deadlines (R41).
11. Set the escalations (R45 to R51).
12. Record the decision (R55).

**R54. When a decision cannot be made.** A determination cannot be made when a fact it depends
on is missing from the ticket record and these rules give no default for that fact. Record
"cannot decide: missing X" for that determination and for every determination that depends on
it, and make all the other determinations.

These facts have **no default**. If one is missing, the determinations that depend on it cannot
be made:

- the customer's identifiers, when the ticket's names are ambiguous;
- the open time;
- the initial-response time;
- the restoration time;
- the business-impact description;
- a root-cause finding, while R32(c) applies.

These absences **have a default**, so the determination can still be made:

- no recorded pause: there is no pause (R26(c));
- no qualifying notice record: there is no maintenance exclusion (R29);
- the customer-caused exclusion was not asserted: it does not apply (R32);
- no telephone report recorded: the incident was not reported by telephone (R37, R42);
- no claim yet: no credit is owed yet. State the credit that would be owed and the last day to
  claim it.

**R55. Decision record.** Each decision records:

1. **True severity**, with the reported priority if it differs.
2. **Breach**, for each of the initial response and restoration: met, missed (with the v2.0
   band), not applicable, or cannot decide.
3. **Remedy**: the credit amount and the credit-memo deadline. Otherwise "none", with the reason.
4. **Engagements and notifications**: each role, its holder and the latest time.
5. **Customer obligations**: each one that applies, and whether it was met.
6. **Decision status**: decidable, or "cannot decide: missing X" for the parts affected.

---

## Appendix: where these rules would live as Northstar documents

This appendix is for authoring evidence. It is not a rule.

| Rules | Natural home |
|---|---|
| R1 to R8, R24 to R27 | Northstar Support Service Level Schedule (definitions and clock rules; the same text in both versions) |
| R20 to R23, R29, R34, R35, R38, R43 | Service Level Schedule v1.0 and v2.0 (version-specific values) |
| R9 to R11 | Each customer's support agreement (Acme: Schedule C to ACME-MFG-2025; SUP-BRL-2025; SUP-CHS-2025) |
| R13 to R19 | Support severity guide |
| R12, R45 to R52 | Support escalation procedure (an SOP) and the support organization chart |
| R3 | Northstar holiday calendar |
