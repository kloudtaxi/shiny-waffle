## X01 · S43

**Outcome: OUT_OF_SCOPE.** SR-39802 is not covered by any support terms. No service level applies, so nothing was breached and no credit is owed.

**1. Who the customer is.** The ticket sits on CRM account CRM-2091, **Acme Industrial Supply Co.** in Akron, OH. It matches ERP customer C-1044 through DUNS 09-552-1187. The "Acme Platinum" plan the caller named belongs to a different company: Acme Mfg. Holdings / Acme Manufacturing (CRM-2048, ERP C-1001, DUNS 04-812-7730). That plan is set out in Schedule C to agreement ACME-MFG-2025.

**2. Scope.** Schedule C covers NS-500 and NS-EDGE for Acme Mfg. Holdings only. It says directly: *"Acme Industrial Supply Co. is a different company and is not covered,"* and that coverage does not extend to the parent, Acme Group Holdings, Inc., or to any other affiliate. I found no support terms for CRM-2091 or C-1044. The only basis for the Platinum claim is the caller's own words on the ticket ("We're Acme. We have the Acme Platinum support plan"). The ticket is therefore out of scope.

**3. True severity.** The record shows every NS-Edge gateway at the site offline, conveyor monitoring dark, picking halted and no workaround. That is a Severity 1 impact, the same as the reported P1. For an out-of-scope ticket, though, severity is classified only for internal priority. I judged this from the recorded impact; I did not pull the severity guide's text.

**4–7. Targets, measurements and credits.** None of these apply: no targets, no escalations and no credit for out-of-scope tickets. For reference only:
- The ticket opened at 06:05 EDT, which is 05:05 CT on Monday 2026-08-10.
- An engineer called back at 06:40 CT.
- Service was restored at 13:20 CT.
- The credit claim arrived by email on 2026-08-14. It should be declined because there is no coverage. No credit has been recorded against this ticket.

**8. What Northstar owes.**
- **Best-effort handling.** This has been given: the gateways are back online.
- **Notify the account owner.** Northstar Support must tell **Zachary Brown** (Enterprise Account Executive, owner of CRM-2091) within 10 business hours of the open time.
  - Business hours under Schedule v2.0 (in effect from 2026-04-01) are 08:00–18:00 CT, Monday to Friday, except Northstar holidays.
  - The ticket opened before business hours, so the clock started at 08:00 CT on 2026-08-10. I found no holiday on that date, though I couldn't see the calendar's individual dates. The deadline is **2026-08-10T18:00:00-05:00**.
  - The ticket history shows no record that this notice was sent.
- **No escalations or root-cause finding** are required.

**9. What the customer must do.** Nothing under the service levels, since the out-of-scope rules impose no reporting or claim duties. The customer did report by phone and did file a claim, but neither creates any entitlement.

```json
{
  "outcome": "OUT_OF_SCOPE",
  "ticket": "SR-39802",
  "scope": "out",
  "true_severity": "Severity 1 (internal priority only)",
  "breach": {"response": "not_applicable", "restoration": "not_applicable"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "notify", "role": "account owner of CRM-2091", "holder": "Zachary Brown", "due": "2026-08-10T18:00:00-05:00"}
  ],
  "evidence": [
    "Ticket SR-39802: account CRM-2091, NS-EDGE, Akron OH, opened 2026-08-10T06:05:00-04:00 by phone, reported P1, all gateways offline, picking halted, no workaround, restored 2026-08-10T14:20:00-04:00",
    "CRM-2091 = Acme Industrial Supply Co., DUNS 09-552-1187, ERP C-1044; account owner Zachary Brown",
    "Schedule C (ACME-MFG-2025) covers Acme Mfg. Holdings (DUNS 04-812-7730), Platinum: 'Acme Industrial Supply Co. is a different company and is not covered'; coverage excludes any other affiliate",
    "Out-of-scope handling: best effort, severity for internal priority only, no targets apply, nothing can be breached, no credit owed, escalations do not apply; Northstar Support must notify the account owner within 10 business hours of open time",
    "Service Level Schedule v2.0 effective 2026-04-01: US Central Time; business hours 08:00-18:00 CT Mon-Fri except Northstar holidays",
    "Credit claim by email 2026-08-14T10:00:00-04:00 from Amy Barrett (to be declined: no coverage); no service credit recorded for the ticket"
  ],
  "missing_evidence": [
    "No record that the account owner was notified",
    "The Northstar Holiday Calendar's individual dates were not visible; no holiday found on 2026-08-10"
  ]
}
```

---

## X02 · S38

# SR-39561 (BlueRiver Logistics, NS-Cloud down for all users): no service level was breached and no credit is owed

**Decision: NO_BREACH.** The ticket is Severity 1, but both targets were met once the scheduled maintenance window is excluded. BlueRiver's credit claim was made on time, but it must be denied in writing. No credit memo is due.

**1. Customer.** CRM account CRM-2051 (BlueRiver Logistics, Standard tier) carries DUNS 07-331-9025. That matches ERP customer C-1002 (Blue River Logistics LLC). The CRM account owner is Kelly Floyd.

**2. Scope: covered.** BlueRiver's support terms (SUP-BRL-2025) are on the Silver plan, cover NS-Cloud (NS-CLOUD) and started on 2025-01-01 00:00 CT. The monthly support fee is $2,500.

**3. True severity: Severity 1.** The ticket says NS-Cloud was down for all users, with no workaround. That meets the severity guide's Severity 1 test (b): "makes NS-Cloud unavailable to all of the customer's users." Dispatch had also stopped, which meets test (a).

**4. Schedule and targets.** The ticket opened at 2026-07-11 23:20 CT, so Schedule v2.0 applies (tickets opened from 2026-04-01). Severity 1 always runs on the 24×7 clock, whatever the plan. The targets are a 30-minute response and a 4-hour restoration.

**5. Clock start, pauses and exclusions.**
- All times on the ticket are already in Central Time (UTC−05:00).
- Notice MN-2607 covered NS-CLOUD for a window from 2026-07-11 22:00 to 2026-07-12 02:00. It was sent on 2026-06-26, at least 9 business days before the window, against the 5 required. So the window qualifies, and the time inside it doesn't count on either clock.
- The outage started inside that window, so the clocks effectively run from 2026-07-12 02:00.
- The schedule says time after the window counts normally, "even if the maintenance caused the incident." The engineer's note blames the MN-2607 upgrade, which doesn't change the count.
- No pauses are recorded.

**6. Measurement.**
- **Response:** an engineer phoned the customer at 23:35, inside the window. No counted time had passed, so the target was **met**.
- **Restoration:** 02:00 to 05:05 is 3 h 05 min against the 4 h target, so it was **met**. The customer's "5 h 45 min" counts from 23:20 and includes the excluded window time.

**7. Credits: $0.** The claim was received on 2026-07-14, within the 30 calendar days after restoration (deadline 2026-08-11 23:59 CT). But with no missed target, no credit is owed. No other credits are recorded on the account.

**8. Obligations.** A qualifying maintenance window delays the escalation deadlines too, so they run from 02:00:

| Who | Action | Latest time |
|---|---|---|
| Hannah Lindqvist (Support Escalation Manager) | Engaged as incident lead | 2026-07-12 02:15 CT |
| Kelly Floyd (account owner) | Notified | 2026-07-12 02:30 CT |
| Marcus Adeyemi (Director of Customer Support) | Notified, because the ticket wasn't restored at 50% of the target | 2026-07-12 04:00 CT |
| Marcus Adeyemi (Director of Customer Support) | Sends the written decision denying the claim | 2026-08-13 (30th calendar day after receipt) |

- **Not owed:**
  - The VP Sales notice isn't owed: it would have fallen due at 06:00, after restoration at 05:05.
  - The Chief Revenue Officer isn't notified, because BlueRiver is a Standard account, not Strategic.
  - No credit memo is due.
  - No root-cause finding is required, because Northstar isn't claiming the customer caused the incident.
- **Customer:** both obligations were **met**. BlueRiver reported the Severity 1 by phone, and made a written claim by email that names the ticket.

**Gaps in the record:** the ticket events don't record the three escalation steps or a decision on the claim. The decision deadline (2026-08-13) has passed, so it should be confirmed whether the denial was sent. I couldn't read the holiday dates from the calendar, but that doesn't change the result: even with a 3 July holiday the notice gave 9 business days.

```json
{
  "outcome": "NO_BREACH",
  "ticket": "SR-39561",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "met", "restoration": "met"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-07-12T02:15:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Kelly Floyd", "due": "2026-07-12T02:30:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-12T04:00:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-08-13T23:59:00-05:00"},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "Ticket SR-39561: CRM-2051, NS-CLOUD, phone, opened 2026-07-11T23:20:00-05:00, 'down for all our users... No workaround', restored 2026-07-12T05:05:00-05:00",
    "Events: engineer_response 2026-07-11T23:35:00-05:00; note: outage caused by upgrade in window MN-2607; credit_claim by email 2026-07-14T08:45:00-05:00",
    "CRM-2051 DUNS 07-331-9025 = ERP C-1002 Blue River Logistics LLC; tier Standard; owner Kelly Floyd",
    "BlueRiver Logistics Support Terms SUP-BRL-2025: Silver plan, covers NS-CLOUD, coverage from 2025-01-01 00:00 CT, fee $2,500/month",
    "Support Severity Guide: Severity 1 (b) NS-Cloud unavailable to all users, no workaround",
    "Service Level Schedule v2.0 (tickets opened from 2026-04-01): Sev 1 response 30 min, restoration 4 h, 24x7 clock; time inside a qualifying window not counted on either clock; time after the window counts even if maintenance caused the incident; 5-business-day notice rule; claim within 30 calendar days of restoration; claim decision within 30 calendar days of receipt",
    "MN-2607: NS-CLOUD, sent 2026-06-26T11:00:00-05:00, window 2026-07-11T22:00:00-05:00 to 2026-07-12T02:00:00-05:00",
    "Support Escalation Procedure: SEM by +15 min, account owner by +30 min, Director at 50%, VP Sales at 100%, CRO only for Strategic accounts; qualifying maintenance window delays both clocks",
    "No service credits recorded on CRM-2051"
  ],
  "missing_evidence": [
    "No record in the ticket that the Support Escalation Manager was engaged or the account owner and Director were notified",
    "No record of the written claim decision (due 2026-08-13)",
    "Holiday dates for June-July 2026 not read from the calendar (does not affect the notice result)"
  ]
}
```

---

## X03 · S45

I can't decide SR-39857 yet. It is a Severity 1 ticket and the initial response was on time, but whether restoration breached can't be settled as of 2026-08-24 17:00 CDT. Northstar has claimed the outage was the customer's fault, and the finding that confirms or rejects that is not due until 2026-08-31.

**Customer and scope.** The ticket is on CRM-2048 (DUNS 04-812-7730), which matches ERP customer C-1001, "Acme Mfg. Holdings." Its support terms (Schedule C, ACME-MFG-2025) cover NS-500 on the Platinum plan, from 2025-04-01. The monthly fee is $21,000 from 2026-01. The ticket is in scope.

**True severity: Severity 1.** The recorded impact is "Line 2 is stopped. No workaround." The severity guide makes a stopped production line with no workaround Severity 1, regardless of the customer's own P1 rating.

**Schedule and targets.** The ticket opened 2026-08-17 09:20 CDT, so Schedule v2.0 applies (tickets opened from 2026-04-01). Severity 1 targets are a 30-minute response and 4-hour restoration, on a 24×7 clock. The clock started at 09:20 when the hotline call was answered. The record shows no pauses and no maintenance notices, so neither applies.

**Measurement.**
- **Response: met.** An engineer phoned Kelly Ballard at 09:38, 18 minutes after opening.
- **Restoration: cannot be decided yet.** Service came back at 15:05, 5 h 45 min after opening. That is over the 4-hour target but under twice the target (band 1). At 15:30 the engineer claimed the customer-caused exclusion: Acme had reverted a VLAN change its contractor made on 08-16. Under v2.0, while that claim stands, no root-cause finding is recorded and the deadline hasn't passed, neither the breach nor a credit can be decided. The deadline is 18:00 CT on the 10th business day after the restoration date: **2026-08-31 18:00 CDT**. There are no holidays in that span; Labor Day is 09-07.

**Credit, depending on the finding.**
- If the finding confirms Acme caused it, there is no restoration breach and no credit.
- If it names another cause, or no finding is recorded by the deadline, the ticket is decided as if the claim was never made. That means a band-1 miss and a credit of 10% × $21,000 = **$2,100**. This is well under the August cap of $6,300 (30% of the fee); the account has no other August tickets or credits.
- The claim was timely. Edward Floyd emailed it on 2026-08-20 08:40 CDT, naming the ticket. The window closes 2026-09-16 23:59 CDT.

**What Northstar owes.** Claiming the exclusion doesn't change escalation; the Severity 1 steps were all due on 2026-08-17, CDT:

| Duty | Role | Holder | Latest time |
|---|---|---|---|
| Engage as incident lead | Support Escalation Manager | Hannah Lindqvist | 09:35 |
| Notify | Account owner | Sarah Chen | 09:50 |
| Notify (not restored at 50% of target) | Director of Customer Support | Marcus Adeyemi | 11:20 |
| Notify (not restored at 100% of target) | VP Sales | Michael Torres | 13:20 |
| Notify (Strategic account) | Chief Revenue Officer | David Morgan | 13:20 |
| Record the root-cause finding | Support Engineering Lead | Owen Takahashi | 2026-08-31 18:00 |
| Decide the credit claim | Director of Customer Support | Marcus Adeyemi | 2026-09-19 |
| Issue the credit memo, if approved | Support Billing Manager | Paul Brennan | Same day as approval |

The ticket history has no entries for any of these steps, so I can't tell whether they were done.

**What the customer must do.**
- Report a Severity 1 by phoning the hotline: **met** (ticket opened by phone).
- Make a written claim naming the ticket within 30 days of restoration: **met**.
- Keep a technical contact reachable by phone until restoration: no failed call is recorded, so this is not in question.

```json
{
  "outcome": "CANNOT_DECIDE",
  "ticket": "SR-39857",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "met", "restoration": "cannot_decide"},
  "credit_usd": null,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-08-17T09:35:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Sarah Chen", "due": "2026-08-17T09:50:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-08-17T11:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "VP Sales", "holder": "Michael Torres", "due": "2026-08-17T13:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Chief Revenue Officer", "holder": "David Morgan", "due": "2026-08-17T13:20:00-05:00"},
    {"party": "northstar", "duty": "record_root_cause", "role": "Support Engineering Lead", "holder": "Owen Takahashi", "due": "2026-08-31T18:00:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-09-19"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39857: CRM-2048, NS-500, channel phone, opened 2026-08-17T09:20-05:00, restored 2026-08-17T15:05-05:00, 'Line 2 is stopped. No workaround.'",
    "crm_accounts CRM-2048: DUNS 04-812-7730, tier Strategic, owner Sarah Chen; ERP C-1001 Acme Mfg. Holdings matched by DUNS",
    "Schedule C (ACME-MFG-2025): Platinum plan, covers NS-500 and NS-EDGE, coverage from 2025-04-01 00:00 CT, fee $21,000/month from 2026-01",
    "Support Severity Guide: Severity 1 = product failure stopping a production line with no workaround",
    "Service Level Schedule v2.0: applies to tickets opened on or after 2026-04-01 CT; Severity 1 targets 30 min response / 4 h restoration on 24x7 clock; restoration band 1 credit 10%; monthly cap 30%; claim window 30 calendar days after restoration date; claim decision within 30 calendar days of receipt; Support Billing Manager issues memo the same day as approval",
    "Service Level Schedule v2.0 customer-caused exclusion: Support Engineering Lead records root-cause finding by 18:00 CT on 10th business day after restoration date; until then the restoration breach and credit cannot be decided; if no finding by the deadline, decided as if never asserted",
    "ticket_events: engineer_response 2026-08-17T09:38-05:00; restored 15:05; note 15:30 asserting customer-caused exclusion (VLAN change by Acme's contractor); credit_claim 2026-08-20T08:40-05:00 by Edward Floyd (Acme VP Procurement), email naming SR-39857",
    "Support Escalation Procedure: Severity 1 engage Escalation Manager within 15 min, notify account owner within 30 min, Director at 50% of restoration target, VP Sales and CRO (Strategic) at 100%; customer-caused exclusion does not affect escalation",
    "Support Organization and Escalation Contacts / employees: Hannah Lindqvist, Marcus Adeyemi, Owen Takahashi, Paul Brennan, Michael Torres, David Morgan",
    "Northstar Holiday Calendar: no holidays 2026-08-18 to 2026-08-31 (Labor Day 2026-09-07)",
    "maintenance_notices: none for CRM-2048; service_credits: none for CRM-2048; no other Acme tickets opened in August 2026"
  ],
  "missing_evidence": [
    "Root-cause finding from the Support Engineering Lead (not yet recorded; due 2026-08-31T18:00:00-05:00)",
    "Ticket records showing the Severity 1 engagement and notifications were carried out"
  ]
}
```

---

## X04 · S38

**SR-39561 is a Severity 1 ticket, and no service level was breached. BlueRiver claimed a credit, but none is owed, so the claim has to be denied.** The customer's 5 h 45 min figure counts time inside a scheduled maintenance window that the schedule excludes.

**Customer and scope.** The ticket sits on CRM account CRM-2051. Its DUNS number, 07-331-9025, matches ERP customer C-1002, Blue River Logistics LLC. BlueRiver's support terms (SUP-BRL-2025) put it on the Silver plan. They cover NS-CLOUD from 2025-01-01, with a support fee of $2,500 a month. The ticket is in scope.

**True severity: Severity 1.** The ticket says NS-Cloud was down for all users with no workaround. The severity guide treats that as Severity 1, and the customer's own "P1" doesn't change it either way.

**Schedule and clock.** The ticket opened at 2026-07-11 23:20 CDT, so schedule v2.0 applies. For Severity 1 the targets are 30 minutes to respond and 4 hours to restore, counted around the clock. All the recorded times already carry the CDT offset (−05:00), so nothing needed converting.

**Exclusion.** Maintenance notice MN-2607 named NS-CLOUD and gave a window of 22:00 on 07-11 to 02:00 on 07-12. It was sent on Friday 2026-06-26, at least 9 business days before the window. The rule asks for 5 business days, so the window qualifies. The ticket was opened inside the window, so both clocks start when it ends, at **2026-07-12 02:00 CDT**. Time after the window counts normally, even though the ticket notes that the upgrade in that window caused the outage. No pauses were recorded.

**Measurement**
- **Response:** an engineer phoned at 23:35, before the clock started, so it counts as zero elapsed time. **Met.**
- **Restoration:** service came back at 05:05 CDT, 3 h 05 min after clock start, against a 4-hour target. **Met.**

**Credit: $0.** A claim arrived in writing on 2026-07-14, well before the deadline of 2026-08-11. It was timely, but with no missed target there is nothing to pay. The monthly cap would have been $750 (30% of the fee).

**What Northstar owes.** Escalation runs from the 02:00 clock start.

| Duty | Who | Latest time |
|---|---|---|
| Engage as incident lead | Support Escalation Manager, Hannah Lindqvist | 2026-07-12 02:15 CDT |
| Notify the account owner | Kelly Floyd | 2026-07-12 02:30 CDT |
| Notify, because service wasn't back at 50% of the target | Director of Customer Support, Marcus Adeyemi | 2026-07-12 04:00 CDT |
| Decide the claim in writing (deny, as no breach) | Marcus Adeyemi | 2026-08-13 |

- The ticket has no record that any of these steps was taken, so I can't confirm they happened.
- The claim decision was due on 2026-08-13 and none is recorded. It looks overdue.
- Nothing more was required:
  - The VP Sales step (at 06:00) never came due, because service was back at 05:05.
  - The Chief Revenue Officer isn't notified, because BlueRiver is a Standard account, not Strategic.
  - No credit memo is due, because no credit is owed.
  - No root-cause finding is due, because no customer-caused exclusion was claimed.

**What the customer had to do.** BlueRiver reported the incident by phone to the hotline, which meets the Severity 1 rule. It also sent a timely written claim naming the ticket. Both obligations are met.

**Caveat.** The detailed maintenance-window wording (the clock starts at the window's end, and time after the window counts normally) was only found in schedule v1.0. For v2.0 the knowledge base only says that maintenance exclusions apply to both clocks. I assumed v2.0 works the same way. If it didn't and the window weren't excluded, restoration would take 5 h 45 min. That would miss the 4-hour target, and a $250 credit would be owed (10% of the fee).

```json
{
  "outcome": "NO_BREACH",
  "ticket": "SR-39561",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "met", "restoration": "met"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-07-12T02:15:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Kelly Floyd", "due": "2026-07-12T02:30:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-12T04:00:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-08-13"},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39561: CRM-2051, NS-CLOUD, phone, opened 2026-07-11T23:20:00-05:00, 'down for all our users ... No workaround', restored 2026-07-12T05:05:00-05:00",
    "crm_accounts CRM-2051: DUNS 07-331-9025, tier Standard, owner Kelly Floyd; customers C-1002 Blue River Logistics LLC same DUNS",
    "SUP-BRL-2025: Silver plan, covers NS-CLOUD, coverage from 2025-01-01 00:00 CT, fee $2,500/month",
    "Support Severity Guide: Severity 1 (b) NS-Cloud unavailable to all users, no workaround",
    "Service Level Schedule v2.0: applies to tickets opened on/after 2026-04-01; Sev 1 response 30 min, restoration 4 h, 24x7; maintenance exclusions apply to both clocks; notice needs at least 5 business days",
    "Service Level Schedule v1.0 wording: a ticket opened inside a qualifying window starts both clocks at the window's end; time after the window counts normally even if the maintenance caused the incident",
    "MN-2607: NS-CLOUD, sent 2026-06-26T11:00:00-05:00, window 2026-07-11T22:00:00-05:00 to 2026-07-12T02:00:00-05:00",
    "ticket_events: engineer_response 2026-07-11T23:35:00-05:00; restored 2026-07-12T05:05:00-05:00; note says outage caused by MN-2607 upgrade; credit_claim by email 2026-07-14T08:45:00-05:00",
    "SOP-SUPPORT-007: Sev 1 Support Escalation Manager within 15 min of clock start; account owner within 30 min; Director at 50% of target; VP Sales at 100%; CRO only for Strategic; a qualifying window delays both",
    "Schedule v2.0: claim within 30 calendar days of restoration date; decided within 30 calendar days of receipt; Director of Customer Support decides",
    "employees / Support Organization: Hannah Lindqvist (Support Escalation Manager), Marcus Adeyemi (Director of Customer Support)"
  ],
  "missing_evidence": [
    "Detailed maintenance-window clock-start wording found only for schedule v1.0; for v2.0 the knowledge base only says maintenance exclusions apply to both clocks, so the same rule was assumed",
    "No ticket record that the Support Escalation Manager was engaged or that the account owner and Director were notified",
    "No written claim decision recorded; it was due by 2026-08-13"
  ]
}
```

---

## X05 · S43

**SR-39802 is out of scope.** No support terms cover this customer, so no service level could be breached and Northstar owes no credit. Northstar's one duty is to tell the account owner, Zachary Brown, by **2026-08-10 18:00 CDT**.

**1. The customer.** The ticket sits on CRM account **CRM-2091, Acme Industrial Supply Co.** (DUNS **09-552-1187**, ERP **C-1044**), Akron, OH, CRM tier "Standard". This is not Acme Manufacturing (CRM-2048 / ERP C-1001 / DUNS 04-812-7730).

**2. Scope.** The only Acme support terms on record are Schedule C (ACME-MFG-2025). That is the Platinum agreement, it covers NS-500 and NS-EDGE, and it is with **Acme Mfg. Holdings, DUNS 04-812-7730**. Schedule C says: *"Acme Industrial Supply Co. is a different company and is not covered."* The CRM tier would not matter even if it were "Strategic": the support plan is unrelated to account tier. No other terms carry DUNS 09-552-1187.

**3. True severity: Severity 1, for internal priority only.** All NS-Edge gateways at the Akron distribution center were offline, picking had halted and there was no workaround. That meets Severity 1 ("a distribution… activity cannot continue", no workaround). For an out-of-scope ticket, severity is set only for internal priority. No targets apply and the Severity 1 escalations do not apply.

**4–7. Targets, measurement and credits: none apply.** The Escalation Procedure says out-of-scope tickets are handled best effort, "nothing can be breached" and "no credit is owed". For the record, times converted to CDT:
- Opened: 05:05 CDT on Monday 2026-08-10, by phone.
- First engineer response: 06:40.
- Restored: 13:20.

**The credit claim (2026-08-14 by email) is refused**, because no credit is owed. The documents set no deadline for answering it.

**8. Obligations**
- **Northstar:** Support must notify the account owner of CRM-2091, **Zachary Brown** (Enterprise Account Executive). The deadline is 10 business hours after opening. Business hours are 08:00–18:00 CT, Monday to Friday, and the holiday calendar lists no holiday in August, so the clock runs 08:00–18:00 on Monday 2026-08-10. That makes the deadline **2026-08-10T18:00-05:00**. The ticket history records no such notice, so I can't confirm it was sent.
- **Northstar, other duties:** no engagement of the Support Escalation Manager, no notice to the Director of Customer Support or VP Sales, no credit memo, and no root-cause finding.
- **Customer:** owes nothing under service-level terms, because it has none. Its phone report and its claim earn nothing. If it wants coverage, it needs its own support agreement.

```json
{
  "outcome": "OUT_OF_SCOPE",
  "ticket": "SR-39802",
  "scope": "out",
  "true_severity": 1,
  "breach": {"response": "not_applicable", "restoration": "not_applicable"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "notify", "role": "Account owner (CRM-2091)", "holder": "Zachary Brown", "due": "2026-08-10T18:00:00-05:00"}
  ],
  "evidence": [
    "service_tickets SR-39802: account CRM-2091, NS-EDGE, phone, opened 2026-08-10T06:05:00-04:00 (05:05 CDT), restored 2026-08-10T14:20:00-04:00; description: all Akron NS-Edge gateways offline, picking halted, no workaround; customer claims 'Acme Platinum support plan'",
    "crm_accounts CRM-2091 Acme Industrial Supply Co., DUNS 09-552-1187, tier Standard, owner Zachary Brown; ERP C-1044 shares the DUNS",
    "Schedule C (ACME-MFG-2025): covers Acme Mfg. Holdings (DUNS 04-812-7730), Platinum, NS-500 and NS-EDGE; 'Acme Industrial Supply Co. is a different company and is not covered'; 'Coverage does not extend to ... any other affiliate'",
    "Support Severity Guide: Severity 1 = product failure with no workaround that stops a distribution activity",
    "Support Escalation Procedure, out-of-scope tickets: best effort; severity only for internal priority; no targets apply, nothing can be breached, no credit owed, escalations do not apply; notify the account owner of the ticket's CRM account no later than 10 business hours after the open time",
    "Service Level Schedule v2.0: business hours 08:00-18:00 CT Mon-Fri except Northstar holidays; all times in America/Chicago",
    "ticket_events: engineer response 07:40 -04:00; credit claim by email 2026-08-14T10:00:00-04:00 asking for Severity 1 credit under 'Acme's Platinum plan'"
  ],
  "missing_evidence": [
    "No recorded notice to the account owner, Zachary Brown, so whether the 2026-08-10 18:00 CDT deadline was met cannot be confirmed"
  ]
}
```

---

## X06 · S42

I've finished checking the ticket. **SR-38862 is Severity 1, and Northstar missed its initial-response target by 8 minutes. I can't settle the credit:** the knowledge base doesn't hold the claim window in Service Level Schedule v1.0, which is the version that applies to this ticket. So the outcome is `CANNOT_DECIDE`. Any credit would be either $630 or $0.

**Customer and scope.** The ticket is on CRM-2048. Its DUNS, 04-812-7730, matches ERP customer C-1001, "Acme Mfg. Holdings". That is the covered customer named in Acme's Schedule C. The ticket is in scope: the terms cover NS-500 on the Platinum plan, coverage started 2025-04-01 00:00 CT, and the monthly fee was $21,000 from 2026-01. "Acme Industrial Supply Co." (CRM-2091) is a different company.

**True severity: Severity 1.** The ticket records "The paint line is stopped. No workaround." Under the severity guide, a product failure that stops production with no workaround is Severity 1. That matches the customer's P1, but the severity comes from the recorded impact, not from the P1.

**Schedule version.** The ticket opened at 2026-03-31 22:50 CDT, which was 10 minutes before v2.0 took effect. So v1.0 applies, with Severity 1 targets of 1 hour to respond and 8 hours to restore, on a 24×7 clock.
- The note on UTC timestamps doesn't apply here. It covers only tickets opened on or after 2026-04-01, and every timestamp on this ticket already carries a −05:00 offset.
- The record shows no pauses, no maintenance notice for the account and no customer-caused exclusion asserted. The clock starts when the ticket opened.

**Measurement**
- **Response:** the engineer phoned at 23:58, 68 minutes after opening, against a 60-minute target. **Missed.**
- **Restoration:** the firmware rollback finished at 2026-04-01 05:35, after 6 h 45 min, against 8 hours. **Met.**

**Credit**
- The Severity 1 rates apply, because the shift supervisor reported the incident by phone before restoration. The response credit is 5% × $21,000 = $1,050.
- v1.0 caps credits at 20% of the month's fee, which is $4,200 for March 2026. March already has $3,150 (SCR-38655) and $420 (SCR-38790) approved, so only **$630** remains. Any credit for this ticket is cut to $630.
- **Timeliness is the open question.** Edward Floyd's emailed claim arrived on 2026-05-12, which is day 41 after the restoration date of 2026-04-01. v2.0's window is 30 days, but I couldn't find the v1.0 window length in the knowledge base. If it's 40 days or less, the claim is late and nothing is owed (`BREACH_NO_CREDIT`). If it's 41 days or more, $630 is owed.

**What Northstar owed or owes** (escalation follows Severity 1)
- Engage Hannah Lindqvist, Support Escalation Manager, by 2026-03-31 23:05 CDT.
- Notify Sarah Chen, the account owner in CRM, by 23:20 CDT.
- Notify Marcus Adeyemi, Director of Customer Support, by 2026-04-01 02:50 CDT. This step was triggered because the ticket wasn't restored at 50% of the 8-hour target.
- The VP Sales step, and the Chief Revenue Officer step for Strategic accounts, were never due, because restoration came before the 8-hour mark (06:50).
- The ticket log records none of the engagements or notifications, so I can't confirm they were made.
- Marcus Adeyemi must send a written decision on the claim by 2026-06-11. No decision or credit is recorded for SR-38862, so that decision is overdue. If he approves it, Paul Brennan (Support Billing Manager) issues the credit memo the same day.
- No root-cause finding is due, because no exclusion was asserted.

**What the customer had to do**
- Report a Severity 1 incident by phone before restoration: done.
- Submit a written claim naming the ticket on time: the claim was submitted and names the ticket, but whether it was on time depends on the missing v1.0 window.

To decide this ticket, someone needs to read the claim-window clause in Service Level Schedule v1.0 directly.

```json
{
  "outcome": "CANNOT_DECIDE",
  "ticket": "SR-38862",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "missed", "restoration": "met"},
  "credit_usd": null,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-03-31T23:05:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner (CRM)", "holder": "Sarah Chen", "due": "2026-03-31T23:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-04-01T02:50:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-06-11"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": null}
  ],
  "evidence": [
    "service_tickets SR-38862: CRM-2048, NS-500, phone, opened 2026-03-31T22:50:00-05:00, 'paint line is stopped. No workaround.', restored 2026-04-01T05:35:00-05:00",
    "ticket_events SR-38862: engineer_response 2026-03-31T23:58:00-05:00; credit_claim by Edward Floyd 2026-05-12T09:00:00-05:00",
    "crm_accounts CRM-2048: DUNS 04-812-7730, tier Strategic, owner Sarah Chen; customers C-1001 Acme Mfg. Holdings, same DUNS",
    "Schedule C (Acme): Platinum plan, NS-500 and NS-EDGE covered, coverage from 2025-04-01 00:00 CT, fee $21,000/month from 2026-01",
    "Support Severity Guide: Severity 1 = product failure stopping production with no workaround",
    "Service Level Schedule v1.0: applies to tickets opened through 2026-03-31 23:59 CT; Severity 1 targets 1 h response / 8 h restoration, 24x7; Severity 1 response credit 5%; 20% monthly cap, applied in approval order; Severity 1 rates need a phone report before restoration; claims decided by the Director within 30 days; memo by the Support Billing Manager the same day",
    "service_credits: SCR-38655 $3,150 (approved 2026-04-02) and SCR-38790 $420 (approved 2026-04-20), both for March 2026 tickets; $630 of the $4,200 cap remains",
    "Support Escalation Procedure: Severity 1 steps: Support Escalation Manager within 15 min, account owner within 30 min, Director at 50% of the restoration target, VP Sales (and CRO for Strategic accounts) at 100%",
    "maintenance_notices: none for CRM-2048; no pause or exclusion recorded",
    "Support Organization and Escalation Contacts / employees: Hannah Lindqvist, Marcus Adeyemi, Paul Brennan in their roles"
  ],
  "missing_evidence": [
    "Length of the credit-claim window in Service Level Schedule v1.0 (claim received on day 41 after the 2026-04-01 restoration date; v2.0's 30 days does not apply to this ticket)",
    "Ticket records of whether the Support Escalation Manager was engaged and the account owner and Director were notified",
    "Any written claim decision or credit memo for SR-38862"
  ]
}
```

---

## X07 · S42

**SR-38862 can't be fully decided (CANNOT_DECIDE).** It is Severity 1, and Northstar missed the response target. Whether a credit is owed depends on how long the claim window is in Schedule v1.0, and I couldn't find that in the knowledge base. If a credit is owed, it is **$630.00**.

**Customer and scope**
- Customer: CRM-2048, ERP C-1001, DUNS 04-812-7730. The ERP name is Acme Mfg. Holdings.
- Covered by Schedule C (ACME-MFG-2025) on the Platinum plan. NS-500 is a covered product, and coverage started 2025-04-01 00:00 CT. **In scope.**

**True severity: 1.** The NS-500 controller was rebooting in a loop, the Plant 1 paint line was stopped, and there was no workaround. That stops production with no workaround, which is Severity 1 in the Severity Guide (criterion (a)). The customer's own "P1" isn't what decides it.

**Schedule version.** The ticket opened 2026-03-31 at 22:50 CDT. The system log shows 03:50Z, which matches. That is before v2.0 took effect at 2026-04-01 00:00 CT, so **v1.0** applies. Its Severity 1 targets are a 1-hour response and an 8-hour restoration, on a 24×7 clock.

**Clock, pauses and exclusions.** The clock starts at 22:50 CDT. The ticket was opened before 2026-04-01, so its stored times are already in CT. Nothing pauses or excludes time: no pause is recorded, there's no maintenance notice for this account, and Northstar never claimed the incident was customer-caused.

**Measurement**
- **Response: missed.** The first engineer call was at 23:58, 68 minutes after the clock started, against a 60-minute target.
- **Restoration: met.** The firmware rollback finished at 05:35 on 2026-04-01, 6 hours 45 minutes in, against 8 hours.

**Credit**
- The customer phoned the Support hotline before restoration, so Severity 1 rates apply. The response credit is 5% of the March 2026 fee of $21,000, which is $1,050.
- The monthly cap is 20% of $21,000, or $4,200. Credits already approved for tickets opened in March total $3,570 (SCR-38655 for $3,150 and SCR-38790 for $420). Only **$630** is left, so any approved credit is cut to $630.00.
- **The open question is the claim.** Edward Floyd's claim arrived on 2026-05-12, day 41 after restoration (2026-04-01). v2.0 allows 30 calendar days. v1.0 also has a claim window, but its length isn't recorded in the knowledge base.
  - If v1.0 also allows 30 days, the claim was late and no credit is owed (BREACH_NO_CREDIT).
  - If v1.0 allows 41 days or more, $630 is owed.

**What Northstar owed during the incident**
- **Engage** the Support Escalation Manager, Hannah Lindqvist, by 23:05 CDT on 2026-03-31.
- **Notify** the account owner, Sarah Chen, by 23:20 CDT on 2026-03-31.
- **Notify** the Director of Customer Support, Marcus Adeyemi, by 02:50 CDT on 2026-04-01. That is 50% of the restoration target, and the ticket was still not restored then.
- Nobody else was due: the VP Sales and Chief Revenue Officer step only applies if the ticket isn't restored by 100% of the target (06:50), and it was restored at 05:35.
- The ticket record shows none of these engagements or notifications as done.
- **No root-cause finding is due,** because no exclusion was claimed.

**What Northstar owes on the claim**
- Marcus Adeyemi must send a written decision within 30 calendar days of receipt, which was **2026-06-11**. No decision or credit is recorded for this ticket, so that deadline appears to have been missed.
- If he approves a credit, the Support Billing Manager, Paul Brennan, must issue the credit memo the same day.

**What the customer had to do**
- Report a Severity 1 incident by phone to the hotline: **done** (the ticket was opened by phone).
- Make a timely written claim naming the ticket: a claim was made, but whether it was timely can't be determined.

To close this out, someone needs to check the v1.0 claim-window length directly in Service Level Schedule v1.0 (SLA-SCHEDULE-1.0).

```json
{
  "outcome": "CANNOT_DECIDE",
  "ticket": "SR-38862",
  "scope": "in",
  "true_severity": 1,
  "breach": {"response": "missed", "restoration": "met"},
  "credit_usd": null,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-03-31T23:05:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Sarah Chen", "due": "2026-03-31T23:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-04-01T02:50:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-06-11"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": null}
  ],
  "evidence": [
    "service_tickets SR-38862: CRM-2048, NS-500, phone, opened 2026-03-31T22:50:00-05:00, restored 2026-04-01T05:35:00-05:00; impact 'paint line is stopped. No workaround.'",
    "ticket_events: system log 'ticket created 2026-04-01T03:50Z'; engineer_response 2026-03-31T23:58:00-05:00; credit_claim by Edward Floyd 2026-05-12T09:00:00-05:00",
    "crm_accounts/customers: CRM-2048 = C-1001 Acme Mfg. Holdings, DUNS 04-812-7730, tier Strategic, owner Sarah Chen",
    "Schedule C (Acme): Platinum plan; NS-500 covered; coverage from 2025-04-01 00:00 CT; fee $21,000/month from 2026-01",
    "Support Severity Guide: Severity 1 = production stopped with no workaround",
    "SLA Schedule v1.0: applies to tickets opened through 2026-03-31 23:59 CT; Sev 1 targets 1 h response / 8 h restoration on a 24x7 clock; Sev 1 response credit 5%, restoration credit 10%; Sev 1 rates require a phone report to the hotline before restoration; monthly cap 20%, credits counted in approval order; Director of Customer Support decides claims within 30 calendar days; Support Billing Manager issues the memo the same day",
    "SOP-SUPPORT-007: Sev 1 engage SEM within 15 min, notify account owner within 30 min, notify Director at 50% of restoration target, VP Sales (+CRO for Strategic accounts) at 100%",
    "service_credits: SCR-38655 $3,150 (approved 2026-04-02) and SCR-38790 $420 (approved 2026-04-20), both for tickets opened in March 2026; remaining cap $630",
    "SUP-DATA-NOTE-014 §5: tickets opened before 2026-04-01 are stored in CT, no conversion needed",
    "employees / Support Organization: Hannah Lindqvist (SEM), Marcus Adeyemi (Director), Paul Brennan (Support Billing Manager)"
  ],
  "missing_evidence": [
    "Length of the credit-claim window under SLA Schedule v1.0 (needed to decide whether the 2026-05-12 claim, day 41 after the 2026-04-01 restoration, was timely; v2.0's 30 days does not govern this ticket)",
    "Ticket records of the escalation engagements and notifications",
    "Written decision on the 2026-05-12 claim"
  ]
}
```

---

## X08 · S39

**SR-39340: Severity 1. Both targets were missed, and Cedar is owed a $320.00 service credit.** The credit uses the lower Severity 2 rates because Cedar reported the outage through the portal, not by phone. The credit decision was due 2026-07-29, and the record shows no decision or credit memo.

**Customer and scope.** The ticket is on CRM account CRM-2063. Its DUNS number, 02-906-4418, matches ERP customer C-1003 (Cedar Health Systems Inc.). Cedar's support terms (SUP-CHS-2025) put it on the Silver plan, cover NS-CLOUD, started coverage on 2025-12-01 and set a fee of $4,000 a month. The ticket is in scope.

**True severity: Severity 1, not the P3 Cedar reported.** None of Cedar's 14 facilities could see NS-Cloud. The engineer confirmed that all users were affected and there was no workaround. The severity guide's Severity 1 test (b) is "NS-Cloud unavailable to all of the customer's users" with no workaround.

**Schedule and targets.** The ticket opened 2026-06-10 at 07:05 −04:00, which is 06:05 CDT, so Schedule v2.0 applies. Severity 1 runs on a 24×7 clock, with a 30-minute response target and a 4-hour restoration target. No pauses are recorded and there are no maintenance notices for Cedar, so nothing is paused or excluded.

**Measurement (all times CDT).** Every recorded time carries its own UTC offset, so I converted each one directly to CDT.
- **Response: missed.** The clock started at 06:05 and the engineer responded at 08:20, 2 h 15 m against a 30-minute target.
- **Restoration: missed, band 1.** Service was restored at 11:35, 5 h 30 m against a 4-hour target. That is more than the target but no more than twice it.

**Credit: $320.00.**
- Severity 1 credit rates apply only if the customer phoned the Support hotline before restoration. A portal ticket doesn't count, and neither does Northstar's call to the customer, so the Severity 2 rates apply.
- That gives 3% for the missed response plus 5% for restoration band 1, so 8% of $4,000 = $320.00.
- The monthly cap is 30% of the fee, or $1,200. Cedar has no other June tickets and no approved credits, so the cap isn't reached.
- The claim was timely. The window ran to 2026-07-10 at 23:59 CT, and Cedar's written claim naming the ticket arrived 2026-06-29 at 10:00 CDT.
- One gap: the schedule wants the claim emailed to support-credits@northstar.example. The record says only "received by email" and doesn't show which address.

**Escalations Northstar owed on 2026-06-10.** Escalation follows the true severity, and the phone rule doesn't change it.
- **Engage the Support Escalation Manager, Hannah Lindqvist,** as incident lead by 06:20 CDT.
- **Notify the account owner, Anthony Day,** by 06:35 CDT.
- **Notify the Director of Customer Support, Marcus Adeyemi,** by 08:05 CDT, because the ticket wasn't restored at 50% of the target.
- **Notify the VP Sales, Michael Torres,** by 10:05 CDT, because it wasn't restored at 100% of the target.
- No Chief Revenue Officer notice was needed, since Cedar is a Standard account, not Strategic.
- The ticket record doesn't show whether any of these four steps happened.

**Claim decision and memo.**
- **Marcus Adeyemi** had to send a written decision by 2026-07-29, 30 days after the claim. No credit is recorded, so it is overdue today (2026-10-19).
- **The Support Billing Manager, Paul Brennan,** issues the credit memo on the day the credit is approved.
- No root-cause finding is due, because Northstar isn't claiming the customer caused the incident.

**What Cedar had to do.**
- **Phone the hotline, (312) 555-0187: not met.** Cedar used the portal, which is why the credit is at Severity 2 rates.
- **Make a timely written claim: met.**
- **Keep a technical contact reachable by phone until restoration:** no failed call attempts are recorded.

```json
{
  "outcome": "BREACH_CREDIT_OWED",
  "ticket": "SR-39340",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "missed", "restoration": "missed_band1"},
  "credit_usd": 320.00,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-06-10T06:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Anthony Day", "due": "2026-06-10T06:35:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-06-10T08:05:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "VP Sales", "holder": "Michael Torres", "due": "2026-06-10T10:05:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-29"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": "2026-07-29"},
    {"party": "customer", "duty": "phone_report", "status": "not_met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39340: CRM-2063, NS-CLOUD, portal, opened 2026-06-10T07:05:00-04:00, reported P3, 'NS-Cloud won't load for anyone. None of our 14 facilities...', restored 2026-06-10T12:35:00-04:00",
    "ticket_events: engineer_response 2026-06-10T09:20:00-04:00 (all users affected, no workaround, reclassified Severity 1); credit_claim 2026-06-29T11:00:00-04:00 by email naming SR-39340",
    "CRM-2063 DUNS 02-906-4418 = ERP C-1003 Cedar Health Systems Inc.; account tier Standard; owner Anthony Day",
    "SUP-CHS-2025: Silver plan, covers NS-CLOUD and NS-EDGE, coverage from 2025-12-01 00:00 CT, $4,000/month",
    "Support Severity Guide: Severity 1 (b) NS-Cloud unavailable to all users with no workaround",
    "Schedule v2.0: applies to tickets opened on/after 2026-04-01 CT; Sev 1 30 min / 4 h on 24x7 clock from open time; Sev 1 credit % only if reported by telephone to hotline before restoration, otherwise Sev 2 % (response 3%, restoration band 1 5%); cap 30% of monthly fee; claim within 30 calendar days of restoration date; decision within 30 days of receipt; memo same day as approval",
    "SOP-SUPPORT-007: Sev 1 engage Support Escalation Manager within 15 min, notify account owner within 30 min, Director at 50% of restoration target, VP Sales at 100%, CRO only for Strategic; telephone rule does not affect escalation",
    "ORG-SUPPORT-2026 / employees: Hannah Lindqvist (Support Escalation Manager), Marcus Adeyemi (Director of Customer Support), Michael Torres (VP Sales), Paul Brennan (Support Billing Manager)",
    "No maintenance notices, no recorded pauses, no other June 2026 tickets or approved credits for CRM-2063"
  ],
  "missing_evidence": [
    "Whether the Support Escalation Manager was engaged and the account owner, Director and VP Sales were notified, and when",
    "Which mailbox received the credit claim (record says only 'by email')",
    "Any written claim decision or credit memo for SR-39340 (none recorded; decision was due 2026-07-29)"
  ]
}
```

---

## X09 · S41

# SR-39644: Severity 2, no service level breached, no credit owed

**Customer and scope.** The ticket is on CRM account CRM-2048 (Strategic tier). Its DUNS number, 04-812-7730, matches ERP customer C-1001 "Acme Mfg. Holdings". It is also the DUNS named in Acme's support agreement (Schedule C, ACME-MFG-2025). That agreement gives Acme the **Platinum** plan, covers NS-EDGE, and has applied since 2025-04-01 00:00 CT. The ticket is in scope.

**True severity: Severity 2, not the reported P1.** The ticket says the presses are still running. Vibration data stopped for presses 1–6 of 14, and technicians are checking them by hand every two hours. Production did not stop, so this is not Severity 1. Losing a condition-monitoring function for one or more machines is Severity 2 under the Severity Guide, "whether or not the customer covers it with manual checks".

**Schedule version and targets.** The ticket opened on 2026-07-23 at 13:10 CDT, so Schedule v2.0 applies. For Severity 2 on the Platinum plan, the targets are a 2-hour initial response and a 12-hour restoration, both on a 24×7 clock.

**Time zone.** All recorded times already carry the −05:00 offset, which is CDT, so no conversion was needed. One internal note (SUP-DATA-NOTE-014) says response and restore times should be read as UTC. That only applies to times shown without an offset, and none of these are. Reading them as UTC would also put the engineer's response before the ticket was opened, which can't be right.

**Measurements**
- **Initial response:** the ticket opened at 13:10. The engineer's comment asking for VPN credentials came at 15:00. That is 1 h 50 min against a 2-hour target: **met**.
- **Restoration:**
  - Total time from opening to restoration (18:40 on 2026-07-24): 29 h 30 min.
  - Pause: from 15:00 on 07-23 to 08:30 on 07-24 the ticket was "Awaiting Customer" while Northstar waited for access. Both the start and end of the pause are recorded, so the pause counts: 17 h 30 min.
  - Time counted against the target: **12 h 00 min against a 12-hour target: met, with no margin.** A credit only starts once the time is *more than* the target.
- **Exclusions:** none. There are no maintenance notices on the account.

**Credits.** None are owed, because no target was missed. No credit claim is recorded on the ticket. The claim deadline was 2026-08-23 at 23:59 CT (30 days after the 07-24 restoration date), and it has passed.

**Northstar's obligations**
- **Escalations:** the Severity 1 steps don't apply. These are engaging the Support Escalation Manager within 15 minutes and notifying the account owner within 30 minutes, then the Director of Customer Support, VP Sales and Chief Revenue Officer as time passes.
- **Gap:** the knowledge base has no Severity 2 escalation steps, so I can't confirm whether any Severity 2 engagement or notification was owed. The restoration landed exactly on the 12-hour mark. Any step that applies only if the ticket isn't restored by that point would therefore not have been triggered. I also couldn't find who holds each escalation role.
- **Other duties:** no claim decision or credit memo is due. No root-cause finding is due, since Northstar has not claimed the problem was the customer's fault.

**Acme's obligations**
- **Phone report:** only Severity 1 incidents must be reported by phone, so the portal report was acceptable.
- **Information and access:** met. Kelly Ballard (Acme IT Architecture) provided the VPN credentials.
- **Credit claim:** none was needed.

```json
{
  "outcome": "NO_BREACH",
  "ticket": "SR-39644",
  "scope": "in",
  "true_severity": "Severity 2",
  "breach": {"response": "met", "restoration": "met"},
  "credit_usd": 0,
  "obligations": [
    {"party": "customer", "duty": "phone_report", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39644: CRM-2048, NS-EDGE, portal, opened 2026-07-23T13:10:00-05:00, reported P1, restored 2026-07-24T18:40:00-05:00; impact: presses still running, vibration data lost for presses 1-6, manual checks every two hours",
    "crm_accounts CRM-2048 DUNS 04-812-7730 = ERP C-1001 Acme Mfg. Holdings = Schedule C covered customer (DUNS 04-812-7730)",
    "Schedule C ACME-MFG-2025: Platinum plan; covered products NS-500, NS-EDGE; coverage starts 2025-04-01 00:00 CT",
    "Support Severity Guide: Severity 2(b) condition-monitoring function unavailable for one or more machines, whether or not covered with manual checks",
    "Schedule v2.0 (tickets opened on/after 2026-04-01 CT): Severity 2 Platinum, 2 h response, 12 h restoration, 24x7",
    "ticket_events: engineer_response 2026-07-23T15:00-05:00 (1 h 50 min)",
    "ticket_events: Awaiting Customer 2026-07-23T15:00-05:00 to 2026-07-24T08:30-05:00 (VPN access request), 17 h 30 min pause; restoration elapsed 29 h 30 min - 17 h 30 min = 12 h 00 min",
    "Schedule v2.0 credit band 1 applies only when elapsed time is more than the target",
    "maintenance_notices: none for CRM-2048",
    "ticket_events: no credit_claim; claim window closed 2026-08-23 23:59 CT"
  ],
  "missing_evidence": [
    "Severity 2 escalation steps in the Support Escalation Procedure (SOP-SUPPORT-007) are not in the knowledge base",
    "Holders of the escalation roles (ORG-SUPPORT-2026) are not in the knowledge base"
  ]
}
```

---

## X10 · S40

**SR-39881 decision: both targets were missed, and Blue River Logistics is owed a $200.00 service credit.** The claim decision was due by 2026-09-27. The record shows no decision and no approved credit.

**1. Customer and scope.** The ticket is on CRM account CRM-2051. Its DUNS, 07-331-9025, matches ERP customer C-1002, Blue River Logistics LLC, and the DUNS in the BlueRiver Logistics Support Terms (SUP-BRL-2025). Those terms cover NS-Cloud (NS-CLOUD) on the Silver plan, with coverage from 2025-01-01 00:00 CT and a $2,500 monthly fee. The ticket is in scope.

**2. True severity: 2 (High).** The customer reported P2, but severity comes from the recorded impact. NS-Cloud exception alerts and dashboards stopped updating at 2 of the 6 depots. That meets two Severity 2 criteria in the severity guide: alerting is unavailable at some sites, and NS-Cloud is down for some but not all sites. It is not Severity 1 because operations went on, with dispatchers phoning drivers instead.

**3. Rules and clock.** Schedule v2.0 applies, since the ticket was opened 2026-08-20 19:45 CDT. For Severity 2 on Silver, the targets are a first response within 2 business hours and restoration within 12. Business hours are 08:00–18:00 CT on weekdays, and there were no holidays between Aug 20 and 24.
- The ticket was opened after hours, so the clock started Friday 2026-08-21 08:00 CDT.
- There are no recorded pauses.
- There is no maintenance exclusion: the only notice, MN-2607, covered a window in July.
- Northstar did not claim the customer caused the incident.

**4. Measurement**
| Target | Result | Elapsed | Outcome |
|---|---|---|---|
| Initial response (2 business hours) | Engineer replied Aug 21 10:20 CDT; the 19:46 automatic email doesn't count | 2 h 20 m | **Missed** |
| Restoration (12 business hours) | Restored Mon Aug 24 10:40 CDT (10 h Friday + 2 h 40 m Monday) | 12 h 40 m | **Missed, band 1** (not more than 24 h) |

One knowledge-base note says some post-April 2026 response and restoration times are stored in UTC without a zone label. That note covers only times with no zone label. This ticket's times all carry an explicit −05:00 offset, so I used them as recorded.

**5. Credit.** The late response earns 3% and the band-1 late restoration earns 5%; the two are added. 8% of $2,500 is **$200.00**. The monthly cap is 30% ($750), and no other credit was approved for August 2026, so the cap doesn't reduce it. The claim was emailed on 2026-08-28 and names the ticket. The claim deadline was 2026-09-23 23:59 CT (30 days after the restoration date), so the claim was on time.

**6. What Northstar owes**
- **Claim decision:** Marcus Adeyemi, Director of Customer Support, must decide the claim and send a written decision by **2026-09-27** (30 calendar days after receipt). There is no record that this happened, so it appears overdue.
- **Credit memo:** Paul Brennan, Support Billing Manager, must issue a $200.00 credit memo on the day the credit is approved, against the next support invoice.
- **Root-cause finding:** none is due. That is only required when Northstar says the customer caused the incident.
- **Escalation:** I couldn't find the Severity 2 steps of the escalation procedure in the knowledge base, so I can't confirm who had to be engaged or notified for this ticket, or by when. The restoration target ran out on 2026-08-24 at 10:00 CDT. The Severity 1 steps don't apply, and since the account tier is Standard, the Chief Revenue Officer is not involved.

**7. What the customer had to do**
- **Phone report:** not required. Only Severity 1 incidents must be reported by phone, and the portal report was valid.
- **Written claim:** done, on time and naming the ticket.

```json
{
  "outcome": "BREACH_CREDIT_OWED",
  "ticket": "SR-39881",
  "scope": "in",
  "true_severity": 2,
  "breach": {"response": "missed", "restoration": "missed_band1"},
  "credit_usd": 200.00,
  "obligations": [
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-09-27"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "northstar", "duty": "notify", "role": null, "holder": null, "due": null},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39881: CRM-2051, NS-CLOUD, portal, opened 2026-08-20T19:45:00-05:00, reported P2, restored 2026-08-24T10:40:00-05:00",
    "crm_accounts CRM-2051 DUNS 07-331-9025, tier Standard; customers C-1002 Blue River Logistics LLC, same DUNS",
    "SUP-BRL-2025: Blue River Logistics LLC (DUNS 07-331-9025), Silver plan, covers NS-CLOUD, coverage from 2025-01-01 00:00 CT, fee $2,500/month",
    "Support Severity Guide: Severity 2 (b) alerting unavailable for one or more sites; (c) NS-Cloud unavailable to some, not all, sites",
    "Schedule v2.0: applies to tickets opened on or after 2026-04-01; Severity 2 Silver: 2 business-hour response, 12 business-hour restoration, business-hours clock",
    "Schedule v2.0: business-hours clock starts at next start of business hours; automated acknowledgments do not count as a response",
    "ticket_events: auto_acknowledgment 2026-08-20T19:46; engineer_response 2026-08-21T10:20-05:00; restored 2026-08-24T10:40-05:00; no pause events",
    "maintenance_notices: only MN-2607, window 2026-07-11/12, not relevant",
    "Schedule v2.0 credits: Severity 2 response 3%, restoration band 1 5%, added together; cap 30% of monthly fee per CT month",
    "ticket_events credit_claim 2026-08-28T14:05-05:00 by email naming SR-39881; window is 30 calendar days after restoration date (ends 2026-09-23 23:59 CT)",
    "service_credits: no approved credits for CRM-2051",
    "Schedule v2.0: Director of Customer Support decides claims within 30 calendar days of receipt; Support Billing Manager issues memo same day as approval",
    "Support Organization and Escalation Contacts: Marcus Adeyemi (Director of Customer Support), Paul Brennan (Support Billing Manager)"
  ],
  "missing_evidence": [
    "Severity 2 escalation steps in the Support Escalation Procedure (SOP-SUPPORT-007): who must be engaged or notified for a Severity 2 ticket and by when",
    "Any record that the claim was decided or a credit memo issued"
  ]
}
```

---

## X11 · S37

**SR-39207 (Cedar Health): no service level was breached and no credit is owed. The outcome is `NO_BREACH`.**

**True severity: Severity 2.** The customer reported P2, but severity comes from the recorded impact. NS-Cloud was down for all users at 2 of 14 facilities, the other 12 worked, and operations at both centers continued. That matches Severity 2 (c), "NS-Cloud is unavailable to some, but not all, of the customer's users or sites." It is not Severity 1, because that requires an outage for all users or a stop to operations.

**Customer and scope:** The ticket's CRM account CRM-2063 carries DUNS 02-906-4418, which matches ERP customer C-1003, Cedar Health Systems Inc. Its support terms (SUP-CHS-2025, Silver plan, $4,000 a month) cover NS-CLOUD, and coverage started on 2025-12-01. The ticket is in scope.

**Targets:** The ticket opened 2026-05-22 at 15:20 CT, so schedule v2.0 applies. For Severity 2 on Silver, the targets are an initial response within 2 business hours and restoration within 12 business hours. Business hours are 08:00–18:00 CT, Monday to Friday, excluding Northstar holidays. Memorial Day (2026-05-25) is a Northstar holiday. No pauses are recorded, so none apply.

**Measurement (all times in CT):**

| | Actual | Deadline | Business hours used | Result |
|---|---|---|---|---|
| Initial response | Engineer's ticket comment, Fri 05-22 17:10 | Fri 05-22 17:20 | 1h50m of 2h | Met |
| Restoration | Tue 05-26 17:05 | Tue 05-26 17:20 | 11h45m of 12h | Met |

The restoration time breaks down as Friday 15:20–18:00 (2h40m) plus Tuesday 08:00–17:05 (9h05m). The weekend and the Memorial Day holiday don't count.

**What Northstar owes:**
- **Claim decision:** Cedar Health's credit claim arrived through the portal on 2026-06-01 (08:30 CT). It was on time, since the deadline was 2026-06-25 23:59 CT. Marcus Adeyemi, Director of Customer Support, had to send a written decision by 2026-07-01. The decision should be to deny, because no target was missed.
- **Credit memo:** None. Paul Brennan (Support Billing Manager) only issues one for an approved credit.
- **Engage or notify:** No one. The escalation procedure only sets steps for Severity 1, and for Severity 3 when a target is missed, and neither applies here. So the account owner (Anthony Day), the Support Escalation Manager, the VP Sales and the CRO don't need to be notified.
- **Root-cause finding:** None. Nothing in the knowledge base requires one.

**What the customer must do:**
- The phone-report rule only applies to Severity 1, so reporting through the portal was fine.
- They must provide any information and access Northstar asks for. No such request is recorded.
- Their claim was in writing and on time, so that obligation is met. It simply earns nothing because there was no breach.

**Limits of the record:** The knowledge base doesn't say whether the 2026-07-01 claim decision was actually made, or whether the engineer's comment addressed the specific issue (the log only says "Engineer's ticket comment"). I assumed it did. If it didn't, the response target would have been missed at 17:20 CT. The margins are small (10 minutes on response, 15 on restoration), so the result depends on Memorial Day being treated as a holiday.

```json
{
  "outcome": "NO_BREACH",
  "ticket": "SR-39207",
  "scope": "in",
  "true_severity": "Severity 2",
  "breach": {"response": "met", "restoration": "met"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-01"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "Ticket SR-39207: CRM-2063, NS-CLOUD, opened 2026-05-22T16:20:00-04:00 (15:20 CT), portal, reported P2; NS-Cloud unavailable at 2 of 14 facilities, operations continuing, other 12 normal; restored 2026-05-26T18:05:00-04:00 (17:05 CT)",
    "Ticket events: engineer_response 2026-05-22T18:10:00-04:00 (17:10 CT); credit_claim by portal 2026-06-01T09:30:00-04:00 (08:30 CT); no pause events",
    "CRM-2063 Cedar Health Systems, DUNS 02-906-4418, tier Standard, owner Anthony Day; ERP C-1003 Cedar Health Systems Inc., same DUNS",
    "Cedar Health Systems Support Terms SUP-CHS-2025: covers NS-CLOUD and NS-EDGE, coverage from 2025-12-01 00:00 CT, Silver plan, $4,000 per month",
    "Support Severity Guide: Severity 2 (c), NS-Cloud unavailable to some but not all users or sites; Severity 1 needs all users or operations stopped with no workaround",
    "Service Level Schedule v2.0 (tickets opened from 2026-04-01 CT): Severity 2 Silver, 2 business hours response and 12 business hours restoration, business-hours clock, 08:00-18:00 CT Mon-Fri except Northstar holidays",
    "Northstar Holiday Calendar: 2026-05-25 Memorial Day",
    "Measured: response 1h50m business (met); restoration 11h45m business (met)",
    "Schedule v2.0: claim due within 30 calendar days after restoration (by 2026-06-25 23:59 CT); decision within 30 calendar days of receipt, by the Director of Customer Support",
    "HR: Director of Customer Support is Marcus Adeyemi"
  ],
  "missing_evidence": [
    "Whether a written claim decision was sent by 2026-07-01",
    "Text of the engineer's 17:10 CT comment (the log says only 'Engineer's ticket comment'), so it can't be confirmed that it addressed the specific issue"
  ]
}
```

---

## X12 · S41

I rate SR-39644 as true **Severity 2**, and **no service level was breached**: Northstar met both targets, so it owes no credit. The restoration target was met with no time to spare.

**Customer and scope.** The customer is CRM-2048, ERP C‑1001 (Acme Mfg. Holdings), DUNS 04‑812‑7730. Its support terms (Schedule C to ACME-MFG-2025) are on the Platinum plan, list NS-Edge as a covered product, and started coverage on 2025‑04‑01. The ticket is in scope.

**True severity: 2, not P1.**
- Severity 1 needs production to stop with no workaround. Here the presses were still running and technicians were doing manual vibration checks every two hours.
- The severity guide's Severity 2 rule (b) fits exactly: a condition-monitoring function is unavailable for one or more machines, "whether or not the customer covers it with manual checks."

**Rules that apply.**
- Schedule v2.0 applies, because the ticket opened 2026‑07‑23 13:10 CT, after its 2026‑04‑01 start.
- Severity 2 on Platinum gets a 2‑hour response and a 12‑hour restoration, on a 24×7 clock.
- Both clocks start when the ticket opened. Holidays don't matter on a 24×7 clock.
- There are no maintenance notices on the account, so there is no maintenance exclusion.

**Measurement (all times CT, −05:00).**
- **Response:** an engineer replied at 15:00 on 07‑23, 1h50m after opening. The target was 2h, so it was **met**.
- **Pause:** the restoration clock paused at 15:00 on 07‑23, when the engineer asked for VPN credentials and set the ticket to Awaiting Customer. The ticket history records the customer's reply at 08:30 on 07‑24, so the pause lasted 17h30m. A clarification bulletin says the pause ends at the customer's reply as the ticket history shows it. The note that Kelly Ballard provided the credentials has no separate time.
- **Restoration:** restored at 18:40 on 07‑24. That is 29h30m in total, minus the 17h30m pause, which leaves exactly 12h00m. The credit bands start only when time is *more than* the target, so restoration was **met**.

This is very tight. If the pause had ended any earlier, or the 15:00 request didn't count as a pause, restoration would be a breach. The credit would then be the first-band Severity 2 rate of 5% of the $21,000 monthly fee, or $1,050. No other July ticket used any of the 30% monthly cap.

**What Northstar owes.**
- **Credit:** none, and no credit claim or credit memo is on record.
- **Escalation and notification:** none is due. The escalation procedure only sets steps for Severity 1 (Support Escalation Manager within 15 minutes; account owner Sarah Chen within 30 minutes; Director of Customer Support, VP Sales and Chief Revenue Officer later). Escalation follows true severity, so the P1 label doesn't trigger these. The procedure I found sets no Severity 2 steps.
- **Root cause:** I found no rule in the knowledge base that requires a root-cause finding.

**What the customer must do.**
- **Give the information and access Northstar needs:** met. Acme supplied the VPN credentials.
- **Report by phone:** that rule is for Severity 1 only, so it doesn't apply. The portal report was fine.
- **Claim a credit:** not applicable, since nothing was breached. For reference, a claim would have been due by 23:59 CT on 2026‑08‑23 (30 days after restoration), by email to support-credits@northstar.example or through the portal, naming the ticket. None is on record.

```json
{
  "outcome": "NO_BREACH",
  "ticket": "SR-39644",
  "scope": "in",
  "true_severity": 2,
  "breach": {"response": "met", "restoration": "met"},
  "credit_usd": 0,
  "obligations": [
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "not_met"}
  ],
  "evidence": [
    "CRM-2048 / ERP C-1001 / DUNS 04-812-7730 (Acme Mfg. Holdings)",
    "Schedule C ACME-MFG-2025: Platinum plan; covered products NS-500 and NS-EDGE; coverage starts 2025-04-01 00:00 CT; fee $21,000/month from 2026-01",
    "Service Level Schedule v2.0 (tickets opened on or after 2026-04-01 CT): Sev 2 Platinum 2h response / 12h restoration, 24x7 clock; clocks start at open time",
    "Support Severity Guide Sev 2(b): condition-monitoring function unavailable for one or more machines, whether or not covered by manual checks",
    "Ticket opened 2026-07-23T13:10:00-05:00 by portal; engineer_response 2026-07-23T15:00:00-05:00 (1h50m)",
    "Awaiting Customer from 2026-07-23T15:00:00-05:00 (VPN credentials request) to customer reply 2026-07-24T08:30:00-05:00 = 17h30m pause; the clarification bulletin says the pause ends at the customer's reply as the status history shows it",
    "Restored 2026-07-24T18:40:00-05:00: 29h30m elapsed minus 17h30m paused = 12h00m, equal to the 12h target (credit band 1 starts only above the target)",
    "No maintenance notices on CRM-2048; no credits on CRM-2048 for July 2026 tickets",
    "Support Escalation Procedure: escalation follows true severity; steps are set only for Severity 1",
    "Customer phone-report duty applies to Severity 1 only, so not required here; customer provided the requested access; no credit claim on record and none needed"
  ],
  "missing_evidence": [
    "Time Kelly Ballard actually provided the VPN credentials is not separately timestamped (the 08:30 status-history reply is used as the pause end)",
    "No Severity 2 escalation or notification steps, and no root-cause rule, found in the knowledge base"
  ]
}
```

---

## X13 · S37

SR-39207 is **Severity 2**, and **no service level was breached**. Northstar owes no credit. Its one remaining duty is a written decision on Cedar Health's credit claim, denying it, sent by **Marcus Adeyemi, Director of Customer Support, by 2026-07-01**. The customer has no outstanding obligation.

**1. Customer.** CRM account CRM-2063 ("Cedar Health Systems"), ERP customer C-1003 ("Cedar Health Systems Inc."), DUNS 02-906-4418. The CRM and ERP records share that DUNS, as does Cedar Health's support terms document (SUP-CHS-2025).

**2. Scope: covered.** The support terms cover NS-CLOUD (and NS-EDGE). The plan is **Silver** at $4,000 a month, and coverage started 2025-12-01 00:00 CT, before the ticket opened.

**3. True severity: 2.** The record says NS-Cloud was "unavailable to all users at our Fishers and Carmel outpatient centers (2 of our 14 facilities) … Facility operations at both centers are continuing. The other 12 facilities are working normally."
- **Not Severity 1:** operations didn't stop, and NS-Cloud wasn't down for all users.
- **Severity 2:** the severity guide's rule (c) covers NS-Cloud being "unavailable to some, but not all, of the customer's users or sites". The customer's reported P2 happens to match, but it doesn't set the severity.

**4. Schedule and targets.** The ticket opened on 2026-05-22 at 15:20 CDT, so Schedule v2.0 applies (tickets opened from 2026-04-01). For Severity 2 on Silver:
- initial response within 2 business hours;
- restoration within 12 business hours;
- business hours are 08:00–18:00 CT, Monday to Friday, excluding Northstar holidays.

**5. Clock.** The ticket opened inside business hours, so the clock started at 15:20 CDT on Friday. No pauses were recorded, so none apply. No exclusion is needed because nothing was missed.

**6. Measurement** (stored -04:00 times converted to CDT, UTC−5):

| Measure | Time (CDT) | Business hours | Target | Result |
|---|---|---|---|---|
| Initial response | Fri 05-22, 17:10 | 1h 50m | 2h | **Met** |
| Restoration | Tue 05-26, 17:05 | 2h 40m (Fri) + 0 (weekend) + 0 (Mon 05-25, Memorial Day) + 9h 05m (Tue) = **11h 45m** | 12h | **Met** |

The customer's claim of "four days" down is calendar time. It counts the weekend and Memorial Day, which the business-hours clock excludes.

**7. Credit: $0.** No target was missed, so no credit rate applies and the monthly cap doesn't matter. The claim itself was timely: it came in by portal on 2026-06-01 at 08:30 CDT, and the deadline was 2026-06-25 23:59 CT (30 days after the 2026-05-26 restoration).

**8. Obligations.**
- **Engagement and notification:** the escalation procedure's engagement and notification steps are all for Severity 1. I found no Severity 2 steps, so nobody had to be engaged or notified, including the account owner, Anthony Day.
- **Claim decision:** the Director of Customer Support decides every credit claim and sends a written decision. It is due by the 30th calendar day after receipt, which is 2026-07-01. The decision should deny the claim and explain the business-hours measurement.
- **Credit memo and root cause:** no credit memo is due, and no root-cause finding is due.
- **Customer:** the telephone-report rule applies only to Severity 1, so the portal report is fine. Its written claim was received on time. No requests for information or access were recorded, so it owes nothing more.

Two documents marked as clarifications (a timestamp note and a bulletin about pauses) don't change the result here. Every stored timestamp has its own UTC offset, and no pauses were recorded.

```json
{
  "outcome": "NO_BREACH",
  "ticket": "SR-39207",
  "scope": "in",
  "true_severity": 2,
  "breach": {"response": "met", "restoration": "met"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-01T23:59:00-05:00"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39207: CRM-2063, NS-CLOUD, portal, opened 2026-05-22T16:20:00-04:00 (15:20 CDT), reported P2, restored 2026-05-26T18:05:00-04:00 (17:05 CDT); 2 of 14 facilities without NS-Cloud, operations continuing",
    "ticket_events: engineer_response 2026-05-22T18:10:00-04:00 (17:10 CDT); credit_claim by portal 2026-06-01T09:30:00-04:00 (08:30 CDT); no pause events",
    "crm_accounts CRM-2063 DUNS 02-906-4418 = ERP C-1003 Cedar Health Systems Inc.; account owner Anthony Day",
    "SUP-CHS-2025: Silver plan, covers NS-CLOUD and NS-EDGE, coverage from 2025-12-01 00:00 CT, $4,000/month",
    "Support Severity Guide: Severity 2(c) NS-Cloud unavailable to some but not all users or sites",
    "SLA Schedule v2.0: applies to tickets opened from 2026-04-01 CT; Severity 2 Silver 2 business hours response / 12 business hours restoration; business hours 08:00-18:00 CT Mon-Fri excluding holidays; claim window 30 calendar days after restoration date; Director of Customer Support decides every claim by the 30th calendar day after receipt",
    "Holiday Calendar: 2026-05-25 Memorial Day",
    "Support Escalation Procedure: engagement and notification steps defined only for Severity 1",
    "Support Organization and Escalation Contacts: Marcus Adeyemi, Director of Customer Support"
  ],
  "missing_evidence": []
}
```

---

## X14 · S45

SR-39857 is a **Severity 1** ticket. The 30-minute response target was met. On the face of the record the 4-hour restoration target was missed (5 h 45 min). But because Northstar has claimed the incident was the customer's fault, that breach and any credit **cannot be decided yet**: as of 2026-08-24 17:00 CT, no root-cause finding has been recorded and the deadline for one hasn't passed.

**1. Customer and scope.** The ticket's CRM account is CRM-2048 (Acme Manufacturing, DUNS 04-812-7730), which is ERP customer C-1001 (Acme Mfg. Holdings). The Acme support terms (Schedule C, ACME-MFG-2025) name that same DUNS, give the Platinum plan, cover NS-500, and started coverage on 2025-04-01. The ticket is **in scope**.

**2. True severity: Severity 1.** The ticket records "Line 2 is stopped. No workaround." The severity guide says a product failure that stops a production line with no workaround is Severity 1. The customer's reported P1 played no part in this.

**3. Schedule and targets.** The ticket opened 2026-08-17 09:20 CDT, so Schedule v2.0 applies. Severity 1 runs on a 24×7 clock: initial response within 30 minutes, restoration within 4 hours.

**4. Clock and timestamps.** The clock started at 09:20 CDT, when the hotline call was answered. There are no recorded pauses and no maintenance notices on the account.
- A newer data note (SUP-DATA-NOTE-014) says response and restoration times written after 2026-04-01 are stored in UTC. It only applies to times stored with no zone suffix. These times carry an explicit −05:00 offset, so I read them as Central time.
- Reading them as UTC also doesn't work: the response would fall at 04:38 CDT, before the ticket opened.

**5. Measurement.**
- **Response:** 09:38 CDT, 18 minutes after opening. **Met.**
- **Restoration:** 15:05 CDT, 5 h 45 min after opening. That is over the 4-hour target but under twice the target (8 h), which is credit band 1.
- **The customer-caused claim:** at 15:30 the engineer recorded that Acme's contractor had made a network (VLAN) change the day before and "asserting the customer-caused exclusion." Under v2.0 §5, the Support Engineering Lead must then record a root-cause finding by 18:00 CT on the 10th business day after the restoration date. That deadline is **2026-08-31 18:00 CDT** (Labor Day is 09-07, so no holiday falls inside the count).
- While the claim stands, no finding is recorded and the deadline hasn't passed, the schedule says the restoration breach and credit cannot be decided. That is the position on 08-24.

**6. Credit, depending on the finding.**
- **If the finding says Acme caused it:** no restoration breach and no credit.
- **If the finding names anything else, or none is recorded by the deadline:** restoration is missed (band 1). The credit is 10% × the $21,000 monthly fee = **$2,100**. That is under the $6,300 monthly cap (30% of the fee), and no other August tickets or credits exist for the account.
- **The claim itself is timely:** a written email naming the ticket was received 2026-08-20. The window runs to 2026-09-16 23:59 CT.

**7. What Northstar owes.** The customer-caused claim doesn't change escalation, so these were all due on 2026-08-17 (CDT):

| Duty | Role | Person | Latest time |
|---|---|---|---|
| Engage as incident lead | Support Escalation Manager | Hannah Lindqvist | 09:35 |
| Notify | Account owner (CRM) | Sarah Chen | 09:50 |
| Notify (not restored at 50% of the 4 h target) | Director of Customer Support | Marcus Adeyemi | 11:20 |
| Notify (not restored at 100%) | VP Sales | Michael Torres | 13:20 |
| Notify (Strategic account) | Chief Revenue Officer | David Morgan | 13:20 |

The ticket history doesn't record whether these escalations happened. Further duties:
- **Root-cause finding:** Owen Takahashi, Support Engineering Lead, by 2026-08-31 18:00 CDT.
- **Claim decision:** Marcus Adeyemi, Director of Customer Support, by 2026-09-19 (30 calendar days after the claim arrived).
- **Credit memo, if a credit is approved:** Paul Brennan, Support Billing Manager, on the day of approval.

**8. What the customer must do.**
- **Report a Severity 1 by phoning the hotline:** met (the ticket was opened by phone).
- **File a written claim on time:** met (Edward Floyd, 2026-08-20).
- **Keep a technical contact reachable by phone until restoration:** the record shows no failed contact attempts, so nothing is outstanding.

```json
{
  "outcome": "CANNOT_DECIDE",
  "ticket": "SR-39857",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "met", "restoration": "cannot_decide"},
  "credit_usd": null,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-08-17T09:35:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Sarah Chen", "due": "2026-08-17T09:50:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-08-17T11:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "VP Sales", "holder": "Michael Torres", "due": "2026-08-17T13:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Chief Revenue Officer", "holder": "David Morgan", "due": "2026-08-17T13:20:00-05:00"},
    {"party": "northstar", "duty": "record_root_cause", "role": "Support Engineering Lead", "holder": "Owen Takahashi", "due": "2026-08-31T18:00:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-09-19"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39857: CRM-2048, NS-500, phone, opened 2026-08-17T09:20:00-05:00, 'Line 2 is stopped. No workaround.', restored 2026-08-17T15:05:00-05:00",
    "ticket_events: engineer_response 09:38 CDT; 15:30 CDT note asserting customer-caused exclusion, root-cause finding to follow; credit_claim by email from Edward Floyd 2026-08-20T08:40:00-05:00",
    "crm_accounts CRM-2048: DUNS 04-812-7730, tier Strategic, owner Sarah Chen; customers C-1001 same DUNS",
    "Schedule C Acme (ACME-MFG-2025): Platinum, covers NS-500, coverage from 2025-04-01 00:00 CT, fee $21,000/month from 2026-01",
    "Support Severity Guide: Severity 1 = product failure stopping a production line with no workaround",
    "Service Level Schedule v2.0: Sev 1 30 min / 4 h, 24x7; band 1 restoration credit 10%; cap 30% of monthly fee; claim within 30 calendar days of restoration; customer-caused exclusion needs a Support Engineering Lead finding by 18:00 CT on the 10th business day after restoration, and until then restoration breach and credit cannot be decided",
    "Support Escalation Procedure: Sev 1 engage Support Escalation Manager within 15 min, notify account owner within 30 min, Director at 50%, VP Sales (and CRO for Strategic) at 100% of the restoration target; the exclusion does not affect escalation",
    "Holiday Calendar: Labor Day 2026-09-07 (no holiday between 2026-08-18 and 2026-08-31)",
    "employees / Support Organization contacts: role holders as listed",
    "No maintenance notices or recorded pauses on CRM-2048; no other CRM-2048 tickets or credits in August 2026"
  ],
  "missing_evidence": [
    "Root-cause finding from the Support Engineering Lead (not recorded; due 2026-08-31T18:00:00-05:00)",
    "Records showing the Sev 1 escalations and notifications were carried out"
  ]
}
```

---

## X15 · S44

**SR-39690 is a Severity 2 ticket. Northstar missed the restoration target by more than double, but no credit is owed because Cedar's claim arrived one day late.**

**Customer and scope.** The ticket is on CRM-2063, which matches ERP customer C-1003, Cedar Health Systems Inc., through DUNS 02-906-4418. Its support terms (SUP-CHS-2025) put it on the Silver plan, cover NS-EDGE, and started coverage on 2025-12-01. The ticket is in scope.

**True severity: Severity 2 (High).** The gateways stopped forwarding chiller alarms and engineers were doing hourly manual rounds. The severity guide makes that Severity 2: an alarming function is unavailable "whether or not the customer covers it with manual checks". Plant operations did not stop, so it is not Severity 1. Cedar reported it as P2, which doesn't change the result.

**Targets.** Schedule v2.0 applies because the ticket opened after 2026-04-01. For Severity 2 on Silver, the targets are a first response within 2 business hours and restoration within 12 business hours. Business hours are 08:00–18:00 Central Time (CT), Monday to Friday, excluding holidays. No Northstar holiday falls in the period.

**Measurement (all times converted to CT):**
- **Opened:** Tuesday 2026-07-28 at 09:30 CDT, by portal. The clock starts here.
- **First response:** 11:05 CDT, an engineer's ticket comment. That is 1 h 35 m, so the response target was **met**.
- **Restored:** 2026-07-31 00:50 −04:00, which is Thursday 2026-07-30 at 23:50 CDT.
- **Restoration time:** 8.5 h on Tuesday, 10 h on Wednesday and 10 h on Thursday make 28.5 business hours. That is more than twice the 12-hour target, so restoration was **missed, band 2**.
- **Pauses and exclusions:** none. No customer-wait periods are recorded and there are no maintenance notices for this account.
- **A note on timestamps:** a data note says some response and restoration times are stored in UTC without a zone. Here every value carries its offset, and even read as UTC the restoration still falls after 18:00 Thursday. The result doesn't change.

**Credit.** A band-2 restoration miss on Severity 2 earns 10% of the $4,000 monthly fee, which is $400. That is under the July cap of 30% ($1,200), and no other credits exist for this account. But the claim window is 30 calendar days from the CT restoration date of 2026-07-30, so it closed at 23:59 CT on 2026-08-29. The emailed claim arrived on 2026-08-30 at 08:12 CDT, one day late. A late claim earns no credit. Taking the date as stored (07-31) instead of the CT date would wrongly make the claim look on time.

**What Northstar owes:**
- **Claim decision:** Marcus Adeyemi, Director of Customer Support, must send a written decision rejecting the claim as late. It was due by 2026-09-29, 30 days after receipt. The ticket shows no decision, so it is overdue unless it was recorded somewhere else.
- **Credit memo:** none, since no credit was approved.
- **Root-cause finding:** none, because Northstar didn't claim the incident was the customer's fault.
- **Escalation:** the escalation procedure I found sets out steps only for Severity 1. I found no engagement or notification steps for Severity 2, so none are owed on the record.

**What Cedar had to do:**
- **Phone report:** a hotline call is required only for Severity 1, so it doesn't apply.
- **Credit claim:** the claim was in writing and named the ticket, but it was late, so this was not met.
- **Information and access:** Northstar recorded no requests, so nothing was outstanding.

```json
{
  "outcome": "BREACH_NO_CREDIT",
  "ticket": "SR-39690",
  "scope": "in",
  "true_severity": "Severity 2",
  "breach": {"response": "met", "restoration": "missed_band2"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-09-29T23:59:00-05:00"},
    {"party": "customer", "duty": "claim", "status": "not_met"}
  ],
  "evidence": [
    "service_tickets SR-39690: CRM-2063, NS-EDGE, portal, opened 2026-07-28T10:30:00-04:00 (09:30 CDT), reported P2, restored 2026-07-31T00:50:00-04:00 (2026-07-30 23:50 CDT); impact: chiller alarms not forwarding, hourly manual rounds",
    "ticket_events: engineer_response 2026-07-28T12:05:00-04:00 (11:05 CDT, 1h35m); credit_claim by email 2026-08-30T09:12:00-04:00 (08:12 CDT)",
    "crm_accounts CRM-2063 DUNS 02-906-4418 = ERP C-1003 Cedar Health Systems Inc.",
    "SUP-CHS-2025: Silver plan; covers NS-CLOUD and NS-EDGE; coverage from 2025-12-01 00:00 CT; fee $4,000/month",
    "Support Severity Guide: Severity 2(b) alarming function unavailable, whether or not covered by manual checks",
    "Service Level Schedule v2.0: Sev 2 Silver 2 business hours response / 12 business hours restoration; business hours 08:00-18:00 CT Mon-Fri; Sev 2 band 2 = 10%; cap 30% of monthly fee; claim within 30 calendar days of CT restoration date, by 23:59 CT; late claim earns no credit; claim decided within 30 calendar days of receipt",
    "Restoration elapsed 28.5 business hours > 24 (2x target) -> band 2; credit would be $400 but claim was late",
    "maintenance_notices: none for CRM-2063; no recorded pauses; service_credits: none for CRM-2063",
    "employees / Support Organization: Director of Customer Support = Marcus Adeyemi (EMP-602)"
  ],
  "missing_evidence": [
    "No written claim decision is recorded on SR-39690 (it was due 2026-09-29)",
    "No Severity 2 escalation steps were found in the Support Escalation Procedure as recorded"
  ]
}
```

---

## X16 · S40

SR-39881 is **Severity 2**. Both service-level targets were missed, and Northstar owes Blue River Logistics LLC a **$200 service credit**. The customer filed a valid claim on time, but the deadline to decide it passed on 2026-09-27 and no credit is on record.

**1. Customer and scope.** The ticket's CRM account CRM-2051 carries DUNS 07-331-9025. That matches ERP customer C-1002 and the DUNS named in the BlueRiver Logistics Support Terms (SUP-BRL-2025). Those terms put the customer on the Silver plan, cover NS-Cloud (NS-CLOUD), started coverage on 2025-01-01 and set a fee of $2,500 a month. The ticket is in scope.

**2. True severity: Severity 2.** Shipment-exception alerts and dashboards stopped at 2 of 6 depots. Under the severity guide, an alerting function unavailable at one or more sites, or NS-Cloud unavailable at some but not all sites, is Severity 2. It is not Severity 1: operations kept going because dispatchers phoned drivers, and the other depots were unaffected. The customer's reported P2 happens to agree.

**3. Schedule and clock.** The ticket was opened Thursday 2026-08-20 at 19:45 CDT, so Schedule v2.0 applies. For Severity 2 on Silver the targets are a 2-business-hour response and 12-business-hour restoration, counting only business hours (08:00–18:00 CT, Monday to Friday, except holidays). The open time was after hours, so the clock started Friday 2026-08-21 at 08:00 CDT.
- No pauses are recorded, and no recorded pause means no pause.
- The only maintenance notice for this customer (MN-2607) covered July, so no maintenance exclusion applies.
- There were no holidays between 20 and 24 August.
- Every timestamp already carries a −05:00 (CDT) offset, so no conversion was needed.

**4. Measurement.**
- **Response: missed.** It was due Friday 08-21 at 10:00 CDT. The automatic email at 19:46 doesn't count, so the first real response was the engineer's comment at 10:20. That is 2h20m against a 2h target.
- **Restoration: missed, band 1.** Friday gave 10 business hours, so it was due Monday 08-24 at 10:00 CDT. Restoration came at 10:40, which is 12h40m against 12h. That is over the target but not more than twice it.

**5. Credit: $200.** The Severity 2 rates are 3% for the missed response and 5% for restoration band 1. That makes 8% of $2,500, or $200. The monthly cap is 30% ($750), and there are no other August tickets or credits, so the cap doesn't bite. I added the two rates together because the schedule lists them separately and caps only the monthly total; I found no rule saying only one applies.

**6. The claim was on time.** The claim window runs 30 calendar days from the restoration date of 2026-08-24, so until 2026-09-23 at 23:59 CT. The emailed claim naming SR-39881 arrived on 2026-08-28.

**What Northstar owes and who holds it**
- **Decide the claim:** Director of Customer Support, Marcus Adeyemi, by 2026-09-27 (30 calendar days after the claim). No approved credit is recorded for this ticket, so this is overdue as of today, 2026-10-19.
- **Issue the credit memo:** Support Billing Manager, Paul Brennan, on the day the credit is approved.
- **Root-cause finding:** not owed. That duty arises only if Northstar claims the incident was the customer's fault, and it hasn't.
- **Escalation steps:** I couldn't find the procedure's Severity 2 steps in the knowledge base. Only the Severity 1, 3 and 4 rules are there, so I can't say who had to be engaged or notified, or by when.

**What the customer had to do**
- **Written claim within the window:** done.
- **Telephone report:** not required, because only Severity 1 incidents have to be phoned in. Opening the ticket through the portal was fine.

```json
{
  "outcome": "BREACH_CREDIT_OWED",
  "ticket": "SR-39881",
  "scope": "in",
  "true_severity": "Severity 2",
  "breach": {"response": "missed", "restoration": "missed_band1"},
  "credit_usd": 200,
  "obligations": [
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-09-27"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39881: CRM-2051, NS-CLOUD, portal, opened 2026-08-20T19:45:00-05:00, reported P2, restored 2026-08-24T10:40:00-05:00; impact: alerts/dashboards stopped at 2 of 6 depots, dispatchers phoning drivers",
    "crm_accounts CRM-2051 DUNS 07-331-9025 = ERP C-1002 Blue River Logistics LLC; tier Standard; account owner Kelly Floyd",
    "SUP-BRL-2025: Blue River Logistics LLC (DUNS 07-331-9025), Silver plan, covers NS-CLOUD, coverage from 2025-01-01 00:00 CT, fee $2,500/month",
    "Support Severity Guide: Severity 2 (b) alarming function unavailable for one or more sites; (c) NS-Cloud unavailable to some but not all sites",
    "SLA Schedule v2.0 (tickets opened on/after 2026-04-01): Sev 2 Silver 2 business hours response / 12 business hours restoration; business hours 08:00-18:00 CT Mon-Fri; clock starts at next start of business hours if opened outside them",
    "SLA v2.0: automated acknowledgments do not count as the initial response",
    "ticket_events: auto_acknowledgment 2026-08-20T19:46-05:00; engineer_response 2026-08-21T10:20-05:00; restored 2026-08-24T10:40-05:00; no pause events",
    "SLA v2.0 credits Sev 2: response 3%, restoration band 1 5%; monthly cap 30% of fee; claim within 30 calendar days of restoration date; decision by 30th calendar day after receipt; Support Billing Manager issues memo the same day as approval",
    "ticket_events credit_claim 2026-08-28T14:05-05:00 by email naming SR-39881",
    "maintenance_notices: only MN-2607 (window 2026-07-11/12), not applicable; no other August 2026 tickets or credits for CRM-2051; service_credits: none for SR-39881",
    "Holiday calendar: no holiday 2026-08-20 to 2026-08-24",
    "Support Organization: Director of Customer Support Marcus Adeyemi; Support Billing Manager Paul Brennan"
  ],
  "missing_evidence": [
    "Severity 2 engagement/notification steps of the Support Escalation Procedure (SOP-SUPPORT-007) are not in the knowledge base, so their holders and deadlines cannot be stated",
    "Claim decision / credit approval for SR-39881 not recorded (decision deadline 2026-09-27 has passed)"
  ]
}
```

---

## X17 · S38

**SR-39561: no service level was breached, and no credit is owed (`NO_BREACH`).** The outage started inside a properly noticed maintenance window, and that time doesn't count on either clock.

**Customer and scope.** The ticket is on CRM account CRM-2051. Its DUNS, 07-331-9025, matches ERP customer C-1002 (Blue River Logistics LLC). The BlueRiver support terms (SUP-BRL-2025) give the Silver plan, cover NS-CLOUD, started coverage on 2025-01-01 at 00:00 CT and set a fee of $2,500 a month. The ticket is in scope.

**True severity: Severity 1.** The ticket says "NS-Cloud has been down for all our users… No workaround." That meets the severity guide's Severity 1 test: NS-Cloud unavailable to all of the customer's users, with no workaround. The customer's reported P1 played no part in this.

**Schedule and targets.** The ticket opened at 2026-07-11 23:20 CDT, so Schedule v2.0 applies. Severity 1 runs on a 24×7 clock, with a 30-minute response target and a 4-hour restoration target.

**The maintenance exclusion.** The outage was caused by the upgrade in window MN-2607.
- The notice was sent 2026-06-26 at 11:00 CDT. It named the start and end of the window and NS-CLOUD.
- The window ran from 2026-07-11 22:00 to 2026-07-12 02:00 CDT.
- About 9–10 business days passed between notice and window, well over the 5 required. So the window counts as scheduled maintenance.
- Time inside the window doesn't count. Time after it counts normally, even though the maintenance caused the incident. The clocks effectively start at 02:00. No pauses were recorded.

**Measurement.**
- **Response: met.** An engineer phoned the supervisor at 23:35, inside the window, so 0 minutes counted against the 30-minute target.
- **Restoration: met.** Service came back at 05:05, which is 3 h 05 min counted against the 4-hour target.

The customer's claim of a 5 h 45 min outage measures from the 23:20 open time and ignores the window. Without the exclusion it would have been band 1 (10%, $250), but that doesn't apply.

**What Northstar owed: escalations.** These deadlines are moved back by the window.

| Who | Action | Latest time |
|---|---|---|
| Hannah Lindqvist (Support Escalation Manager) | Engaged as incident lead | 2026-07-12 02:15 CDT |
| Kelly Floyd (account owner in CRM) | Notified | 2026-07-12 02:30 CDT |
| Marcus Adeyemi (Director of Customer Support) | Notified, because service was still down when half the restoration target had passed | 2026-07-12 04:00 CDT |

- The VP Sales step at 100% of the target (06:00) wasn't needed, because service was restored at 05:05.
- The Chief Revenue Officer step doesn't apply, because the account tier is Standard, not Strategic.
- **The ticket history doesn't show any of these engagements or notifications.** I can't confirm they happened.

**What Northstar owed: the credit claim.**
- The written claim arrived on 2026-07-14, within the 30-day window, which closed 2026-08-11.
- Marcus Adeyemi must decline it, because nothing was breached, and send a written decision by 2026-08-13.
- **No decision is recorded, and that deadline has passed.**
- No credit memo is due, since there's no approved credit.
- No root-cause finding is due, because that is only required when Northstar claims the incident was the customer's fault.

**What the customer had to do.**
- Report the Severity 1 by phoning the hotline: done.
- Keep a technical contact reachable by phone until restoration: met, since no failed contact attempts are recorded.
- Claim in writing on time: done, but no credit follows.

The data note saying certain timestamps are stored in UTC didn't change anything here: every value on this ticket already carries its −05:00 (CDT) offset.

```json
{
  "outcome": "NO_BREACH",
  "ticket": "SR-39561",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "met", "restoration": "met"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-07-12T02:15:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Kelly Floyd", "due": "2026-07-12T02:30:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-12T04:00:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-08-13"},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39561: CRM-2051, NS-CLOUD, phone, opened 2026-07-11T23:20:00-05:00, 'down for all our users… No workaround', restored 2026-07-12T05:05:00-05:00",
    "crm_accounts CRM-2051: DUNS 07-331-9025, tier Standard, owner Kelly Floyd; ERP C-1002 Blue River Logistics LLC (same DUNS)",
    "SUP-BRL-2025: Silver plan, covers NS-CLOUD, coverage from 2025-01-01 00:00 CT, fee $2,500/month",
    "Support Severity Guide: Severity 1 (b) NS-Cloud unavailable to all users, no workaround",
    "Schedule v2.0: Sev 1 30 min / 4 h, 24x7; time inside a qualifying window not counted on either clock; time after counts normally even if maintenance caused the incident; notice at least 5 business days before",
    "maintenance_notices MN-2607: NS-CLOUD, sent 2026-06-26T11:00:00-05:00, window 2026-07-11T22:00:00-05:00 to 2026-07-12T02:00:00-05:00",
    "ticket_events: engineer_response 2026-07-11T23:35:00-05:00; note: outage caused by upgrade in MN-2607; credit_claim by email 2026-07-14T08:45:00-05:00",
    "SOP-SUPPORT-007: Sev 1 engage Support Escalation Manager at 15 min, notify account owner at 30 min, Director at 50%, VP Sales at 100%; a qualifying window delays these deadlines",
    "Schedule v2.0: Director of Customer Support decides every claim within 30 calendar days of receipt",
    "Support Organization and Escalation Contacts: Hannah Lindqvist (Support Escalation Manager), Marcus Adeyemi (Director of Customer Support)"
  ],
  "missing_evidence": [
    "No ticket record that the Support Escalation Manager was engaged, or that the account owner or Director of Customer Support were notified",
    "No recorded written decision on the 2026-07-14 credit claim (due 2026-08-13)",
    "No record of which recipients MN-2607 was sent to (taken as the customer's designated support contacts)"
  ]
}
```

---

## X18 · S36

**SR-39385 decision: the restoration target was missed by more than twice its length, and Acme is owed a $4,200 service credit.** The true severity is Severity 1, the initial response was on time, and Acme met its obligations. The Director of Customer Support had to decide the claim by 2026-07-24, and no decision or credit is recorded yet.

**1. Customer.** The ticket's account is CRM-2048 (Strategic tier). Its DUNS, 04-812-7730, matches ERP customer C-1001 (Acme Mfg. Holdings) and the DUNS named in Schedule C (ACME-MFG-2025). It is not Acme Industrial Supply (CRM-2091).

**2. Scope.** In scope. Schedule C covers NS-500 on the Platinum plan, and coverage started 2025-04-01 00:00 CT. The ticket was opened on 2026-06-16.

**3. True severity: Severity 1 (Critical).** The ticket records a hardware failure in an NS-500 controller, with stamping line 4 stopped and no workaround. That meets the Severity Guide test: production stopped and no workaround available. Acme also reported it as P1, but that doesn't set the severity.

**4. Schedule and targets.** Schedule v2.0 applies, because the ticket was opened on or after 2026-04-01. For Severity 1, the targets are a 30-minute response and a 4-hour restoration on a 24×7 clock, so business hours and holidays don't matter.

**5. Clock start, pauses and exclusions.**
- Acme reported the fault by phone at 2026-06-16 02:14 CDT (−05:00), so the clock starts then.
- No "Awaiting Customer" or failed-contact pause is recorded. Under the escalation procedure, no recorded pause means no pause.
- No maintenance notice is recorded, and nothing suggests the customer caused the fault, so no exclusion applies.

**6. Measurement.**
- **Response: met.** An engineer phoned at 02:31, 17 minutes after the start, within the 30-minute target.
- **Restoration: missed, band 2.** Service was restored at 10:58, 8 h 44 min after the start. That is more than twice the 4-hour target.
- A support note (SUP-DATA-NOTE-014) says restoration times may be stored in UTC without a time zone. These values carry an explicit −05:00 offset, so I didn't convert them. Reading them as UTC would put the engineer's response before the ticket was opened.

**7. Credit: $4,200.**
- The band-2 Severity 1 rate is 20% of the June 2026 support fee of $21,000, which is $4,200.
- The monthly cap is 30% of the fee, $6,300. No other June ticket on this account has a credit, so the cap isn't reached.
- The claim was timely. Edward Floyd (Acme, VP Procurement) emailed it on 2026-06-24 and named the ticket. The 30-day window closed on 2026-07-16.

**8. What Northstar owed (latest times, CDT, 2026-06-16 unless stated)**

| Step | Role | Holder | Latest time |
|---|---|---|---|
| Engage as incident lead | Support Escalation Manager | Hannah Lindqvist | 02:29 |
| Notify | Account owner | Sarah Chen | 02:44 |
| Notify (50% of target elapsed, not restored) | Director of Customer Support | Marcus Adeyemi | 04:14 |
| Notify (100% of target elapsed, not restored) | VP Sales | Michael Torres | 06:14 |
| Notify (Strategic account) | Chief Revenue Officer | David Morgan | 06:14 |
| Decide the claim and send the written decision | Director of Customer Support | Marcus Adeyemi | 2026-07-24 |
| Issue the credit memo | Support Billing Manager | Paul Brennan | Same day as approval |

- **CRO deadline uncertain:** the escalation procedure only says to notify the CRO "as well" for Strategic accounts. I placed it with the VP Sales step at 06:14. If it goes with the account-owner step instead, the deadline is 02:44.
- **Not recorded:** the ticket history shows none of these escalations or notifications, so I can't confirm they happened.
- **Overdue:** no claim decision is recorded, and no credit is in the approved-credits table. The 2026-07-24 deadline has passed, so the $4,200 credit should be approved and the memo issued.
- **No root-cause finding is due.** One is only required when Northstar claims the customer caused the fault.

**9. What the customer had to do**
- **Report by phone: met.** The ticket was opened through the Support hotline.
- **Keep a technical contact reachable by phone until restoration: met.** No failed contact attempt is recorded.
- **Make a written claim within the window: met.**

```json
{
  "outcome": "BREACH_CREDIT_OWED",
  "ticket": "SR-39385",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "met", "restoration": "missed_band2"},
  "credit_usd": 4200,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-06-16T02:29:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Sarah Chen", "due": "2026-06-16T02:44:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-06-16T04:14:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "VP Sales", "holder": "Michael Torres", "due": "2026-06-16T06:14:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Chief Revenue Officer", "holder": "David Morgan", "due": "2026-06-16T06:14:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-24"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39385: CRM-2048, NS-500, channel phone, opened 2026-06-16T02:14:00-05:00, 'Line 4 is stopped. No workaround.', restored 2026-06-16T10:58:00-05:00",
    "ticket_events: engineer_response 2026-06-16T02:31:00-05:00; restored 10:58; credit_claim by email from Edward Floyd 2026-06-24T10:12:00-05:00 naming SR-39385",
    "crm_accounts CRM-2048 DUNS 04-812-7730, tier Strategic, owner Sarah Chen; customers C-1001 Acme Mfg. Holdings same DUNS",
    "Schedule C (ACME-MFG-2025): DUNS 04-812-7730, Platinum, covers NS-500, coverage from 2025-04-01 00:00 CT, fee $21,000/month from 2026-01",
    "Support Severity Guide: Severity 1 = product failure that stops production with no workaround",
    "Service Level Schedule v2.0: Sev 1 response 30 min, restoration 4 h, 24x7; band 2 (>2x target) 20%; cap 30% of monthly fee; claim within 30 calendar days of restoration; Director of Customer Support decides within 30 days; Support Billing Manager issues memo same day as approval",
    "Support Escalation Procedure: Sev 1 SEM within 15 min, account owner within 30 min, Director at 50%, VP Sales at 100%, CRO as well for Strategic accounts; no recorded pause means no pause",
    "employees / Support Organization: Hannah Lindqvist (SEM), Marcus Adeyemi (Director), Michael Torres (VP Sales), David Morgan (CRO), Paul Brennan (Support Billing Manager)",
    "service_credits: no credit recorded for CRM-2048 in June 2026"
  ],
  "missing_evidence": [
    "No record in the ticket that any escalation engagement or notification was made",
    "No recorded claim decision or credit memo for SR-39385 (decision was due 2026-07-24)",
    "Escalation procedure wording leaves unclear whether the CRO notice goes with the account-owner step (02:44) or the VP Sales step (06:14)"
  ]
}
```

---

## X19 · S40

## SR-39881: Severity 2. Both targets were missed and a $200 credit is owed.

The customer filed its claim on time. Northstar has not decided it or issued the credit, and the deadline for both passed on 2026-09-27.

**Customer and scope.** CRM account CRM-2051 (BlueRiver Logistics), ERP customer C-1002 (Blue River Logistics LLC) and DUNS 07-331-9025 all point to the same company. Its support terms (SUP-BRL-2025) cover NS-CLOUD on the Silver plan, starting 2025-01-01 00:00 CT. The support fee is $2,500 a month. The ticket is in scope.

**True severity: 2 (High).**
- It is not Severity 1. Dispatch kept working, with dispatchers phoning drivers, and NS-Cloud was down at only 2 of 6 depots, not for all users.
- It meets Severity 2 on two counts:
  - **Criterion (b):** the alerting function was unavailable at those sites, even though staff covered it by hand.
  - **Criterion (c):** NS-Cloud was unavailable at some sites but not all.
- This matches the customer's reported P2.

**Schedule and clock.** The ticket opened Thursday 2026-08-20 at 19:45 CDT, so schedule v2.0 applies.
- Silver plan, Severity 2 targets: initial response within 2 business hours, restoration within 12 business hours.
- Business hours are 08:00–18:00 CT, Monday to Friday. No Northstar holiday falls in this period.
- The ticket opened after hours, so the clock started Friday 2026-08-21 at 08:00 CDT.
- Nothing pauses or excuses the time:
  - No pause is recorded.
  - The only maintenance notice for this customer (MN-2607) covered 11–12 July, not this incident.
  - The automatic acknowledgment email doesn't count as a response.

**Measurement.**

| Target | Due | Actual | Result |
|---|---|---|---|
| Initial response (2 business hours) | 2026-08-21 10:00 CDT | Engineer's comment at 10:20, 2 h 20 m on the clock | **Missed** |
| Restoration (12 business hours) | 2026-08-24 10:00 CDT | Restored at 10:40, 12 h 40 m on the clock | **Missed, band 1** (over the target but within twice the target) |

**Credit: $200.**
- Missed response: 3% of the fee. Restoration band 1: 5%. Total 8% × $2,500 = $200.
- The monthly cap is 30% ($750). No other ticket opened in August and no credits have been issued on the account, so the cap doesn't reduce it.
- The claim arrived by email on 2026-08-28, well before the window closed on 2026-09-23 at 23:59 CT. It was in writing and named the ticket.
- The record says the claim email was received but doesn't give the address it was sent to. The schedule names support-credits@northstar.example; I've treated the claim as valid.

**What Northstar owes:**
- **Decide the claim** by 2026-09-27, the 30th calendar day after receipt. The documents I found don't say which role makes this decision.
- **Issue the $200 credit memo** the same day the credit is approved. This falls to the Support Billing Manager, Paul Brennan.
- Neither has happened: no credit is recorded, so both are overdue as of today (2026-10-19).

**Who must be engaged or notified.** The escalation procedure only sets steps for Severity 1: engage the Support Escalation Manager and notify the account owner, the Director of Customer Support and the VP Sales. None of these apply to a Severity 2 ticket. I found no Severity 2 escalation steps. No root-cause finding is due either, because that is only required when Northstar blames the customer for the problem, which it hasn't. The account owner is Kelly Floyd, but notifying her isn't required here.

**What the customer must do.** Its only obligation was a timely written claim, and it met it. The rule requiring a phone report applies only to Severity 1. Nothing else is outstanding.

```json
{
  "outcome": "BREACH_CREDIT_OWED",
  "ticket": "SR-39881",
  "scope": "in",
  "true_severity": 2,
  "breach": {"response": "missed", "restoration": "missed_band1"},
  "credit_usd": 200,
  "obligations": [
    {"party": "northstar", "duty": "decide_claim", "role": null, "holder": null, "due": "2026-09-27"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": "2026-09-27"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "Ticket SR-39881: account CRM-2051, NS-CLOUD, portal, opened 2026-08-20T19:45:00-05:00, reported P2, restored 2026-08-24T10:40:00-05:00; impact: alerts/dashboards stopped at 2 of 6 depots, dispatchers phoning drivers",
    "Ticket events: auto_acknowledgment 2026-08-20T19:46:00-05:00 (does not count); engineer_response 2026-08-21T10:20:00-05:00; restored 2026-08-24T10:40:00-05:00; credit_claim by email 2026-08-28T14:05:00-05:00 'Credit claim for SR-39881'",
    "CRM-2051 / ERP C-1002 / DUNS 07-331-9025 (Blue River Logistics LLC); account owner Kelly Floyd; tier Standard",
    "BlueRiver Logistics Support Terms SUP-BRL-2025: covers NS-CLOUD, Silver plan, coverage from 2025-01-01 00:00 CT, fee $2,500/month",
    "Support Severity Guide: Sev 2 (b) alarming function unavailable for one or more sites even with manual checks; (c) NS-Cloud unavailable to some but not all sites",
    "Service Level Schedule v2.0 (tickets opened on/after 2026-04-01 CT): Sev 2 Silver = 2 business-hour response, 12 business-hour restoration; business hours 08:00-18:00 CT Mon-Fri except holidays; clock starts at next start of business hours",
    "v2.0 credits Sev 2: response 3%, restoration band 1 5%; monthly cap 30% of fee; claim within 30 calendar days of restoration date by 23:59 CT; decision within 30 calendar days of receipt; Support Billing Manager issues memo the same day as approval",
    "Holiday calendar: no Northstar holiday 2026-08-20 to 2026-08-24",
    "Maintenance notice MN-2607 window 2026-07-11/12 only; no pauses recorded; no other credits or other tickets opened in August 2026 on CRM-2051",
    "Support Escalation Procedure: engagement/notification steps defined for Severity 1 only"
  ],
  "missing_evidence": [
    "Role responsible for deciding the credit claim is not stated in the knowledge base",
    "Recipient address of the claim email is not recorded (schedule requires support-credits@northstar.example)",
    "No record of a claim decision or credit memo for SR-39881"
  ]
}
```

---

## X20 · S37

SR-39207 is **Severity 2**. **No service level was breached**, so Cedar Health is owed **no service credit**. The one thing Northstar still owes is a written decision rejecting Cedar Health's credit claim. That decision was due by 2026-07-01, and the record shows none was made.

**1. Customer.** CRM account CRM-2063 ("Cedar Health Systems") has DUNS 02-906-4418. That matches ERP customer C-1003, "Cedar Health Systems Inc.", and the DUNS in its Support Terms (SUP-CHS-2025).

**2. Scope: in.** The Support Terms put Cedar Health on the Silver plan, with coverage from 2025-12-01 00:00 CT and a fee of $4,000 a month. NS-CLOUD is a covered product. The ticket was opened on 2026-05-22, after coverage started.

**3. True severity: 2.** The customer reported P2, but severity comes from the recorded impact. NS-Cloud was down for all users at 2 of 14 facilities (Fishers and Carmel). The other 12 were working and operations at both centers continued. That is the severity guide's Severity 2 case (c): unavailable to some, but not all, users or sites. It is not Severity 1, because not all users lost access and operations did not stop.

**4. Schedule and clock.** The ticket opened 2026-05-22 at 15:20 CDT (recorded as 16:20 −04:00), so Schedule v2.0 applies. For Severity 2 on Silver, the targets are an initial response within 2 business hours and restoration within 12 business hours. The clock counts only business hours: 08:00–18:00 CT, Monday to Friday, excluding Northstar holidays.

**5. Clock start, pauses and exclusions.** The ticket arrived through the portal during business hours, so the clock started at 15:20 CDT. No pauses were recorded. There are no maintenance notices for this account, and Northstar did not claim the customer caused the incident.

**6. Measurement.** Every timestamp carries an explicit −04:00 offset. I converted each to CDT by subtracting one hour.
- **Initial response: met.** The engineer's ticket comment came at 17:10 CDT, 1 h 50 m after opening, within the 2-hour target.
- **Restoration: met.** Service was restored on Tue 2026-05-26 at 17:05 CDT. Counted business hours:
  - Friday 15:20–18:00: 2 h 40 m.
  - The weekend: none.
  - **Monday 2026-05-25 is Memorial Day**, a holiday in the Northstar calendar: none.
  - Tuesday 08:00–17:05: 9 h 05 m.
  - Total: **11 h 45 m**, within the 12-hour target. Without the holiday it would have been a breach.

**7. Credits: none owed.** Cedar Health's claim arrived through the portal on 2026-06-01 at 08:30 CDT. That is within the 30-day window, which ran to 2026-06-25. Because no target was missed, the claim earns nothing. The 30% monthly cap ($1,200) does not come into play.

**8. Obligations.**
- **Director of Customer Support (Marcus Adeyemi):** decide the claim in writing and send the decision, by the 30th calendar day after receipt: **2026-07-01**. The decision is a rejection. That date has passed and the ticket history shows no decision.
- **Credit memo:** none needed, since no credit is approved.
- **Root-cause finding:** none needed. The Support Engineering Lead only has to record one when Northstar claims the customer caused the incident, and it did not.
- **Escalation:** the escalation procedure in the knowledge base sets out steps for Severity 1 and Severity 3 only. I couldn't find any Severity 2 steps, so I can't name anyone else to engage or notify, or a deadline. Because the ticket was restored within target, a step triggered when the target runs out would not have fallen due.
- **Customer:** the telephone-report rule applies only to Severity 1, so it doesn't apply here. Cedar Health made its claim in writing and on time. Northstar recorded no requests for information or access, so nothing else was owed by the customer.

**9. Decision: `NO_BREACH`.**

```json
{
  "outcome": "NO_BREACH",
  "ticket": "SR-39207",
  "scope": "in",
  "true_severity": "Severity 2",
  "breach": {"response": "met", "restoration": "met"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-01"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39207: CRM-2063, NS-CLOUD, portal, opened 2026-05-22T16:20:00-04:00 (15:20 CDT), reported P2, 2 of 14 facilities without NS-Cloud, operations continuing, restored 2026-05-26T18:05:00-04:00 (17:05 CDT)",
    "ticket_events: engineer_response 2026-05-22T18:10:00-04:00 (17:10 CDT); credit_claim by portal 2026-06-01T09:30:00-04:00 (08:30 CDT); no pause events",
    "crm_accounts CRM-2063 DUNS 02-906-4418 = customers C-1003 Cedar Health Systems Inc.",
    "SUP-CHS-2025: Silver plan, covers NS-CLOUD and NS-EDGE, coverage from 2025-12-01 00:00 CT, $4,000/month",
    "Support Severity Guide: Severity 2 (c), NS-Cloud unavailable to some but not all users or sites",
    "Service Level Schedule v2.0: Severity 2 Silver targets 2 business hours response and 12 business hours restoration; business hours 08:00-18:00 CT Mon-Fri except holidays; 30-day claim window; claim decided within 30 calendar days by the Director of Customer Support",
    "Northstar Holiday Calendar: 2026-05-25 Memorial Day",
    "maintenance_notices: none for CRM-2063; service_credits: none for CRM-2063",
    "Support Organization and Escalation Contacts: Director of Customer Support Marcus Adeyemi"
  ],
  "missing_evidence": [
    "Severity 2 escalation steps: not found in the knowledge base's copy of the Support Escalation Procedure",
    "Any record of a decision on the 2026-06-01 credit claim (due 2026-07-01)"
  ]
}
```

---

## X21 · S36

**SR-39385 is a Severity 1 ticket. Northstar met the response target but missed the restoration target by more than double, and owes Acme a $4,200 service credit.** Acme made a timely claim. A decision on that claim was due by 2026-07-24, and the record shows no decision or credit, so it is overdue.

**Customer and scope.** The ticket belongs to CRM account CRM-2048 (Acme Manufacturing), which shares DUNS 04-812-7730 with ERP customer C-1001 (Acme Mfg. Holdings). Acme's support terms (Schedule C to ACME-MFG-2025) cover the NS-500 on the Platinum plan from 2025-04-01. The ticket is in scope.

**True severity: 1 (Critical).** The NS-500 had a hardware fault, stamping line 4 stopped, and there was no workaround. That meets the severity guide's first test: production stopped with no workaround. The customer's own "P1" label played no part.

**Targets.** The ticket was opened at 02:14 CT on 2026-06-16, so Service Level Schedule v2.0 applies (it covers tickets opened from 2026-04-01). For Severity 1 the targets are a response within 30 minutes and restoration within 4 hours. The clock runs 24×7 and starts at the open time.

**Pauses and exclusions.** The ticket records no pause and Acme has no maintenance notices, so nothing comes off the clock.

**Measurement**
- **Response: met.** An engineer phoned at 02:31, 17 minutes after opening.
- **Restoration: missed, band 2.** Restored at 10:58, 8 h 44 min after opening. That is more than twice the 4-hour target.

**Credit: $4,200 owed**
- Band 2 for Severity 1 is 20% of the month's support fee. June 2026's fee is $21,000, so the credit is $4,200.
- The monthly cap is 30% of the fee, or $6,300. Acme had no other June tickets and no June credits, so the cap doesn't reduce it.
- Acme's VP Procurement, Edward Floyd, emailed a claim naming the ticket on 2026-06-24. The deadline was 23:59 CT on 2026-07-16, so the claim was on time.
- No credit has been recorded for this ticket.

**What Northstar owed or owes**

| Duty | Role | Person | Latest time |
|---|---|---|---|
| Engage as incident lead | Support Escalation Manager | Hannah Lindqvist | 2026-06-16 02:29 CT |
| Notify | Account owner | Sarah Chen | 2026-06-16 02:44 CT |
| Notify (not restored at 50% of target) | Director of Customer Support | Marcus Adeyemi | 2026-06-16 04:14 CT |
| Notify (not restored at 100% of target) | VP Sales | Michael Torres | 2026-06-16 06:14 CT |
| Notify (Strategic account) | Chief Revenue Officer | David Morgan | 2026-06-16 06:14 CT |
| Decide the claim in writing | Director of Customer Support | Marcus Adeyemi | 2026-07-24 |
| Issue the credit memo, same day as approval | Support Billing Manager | Paul Brennan | 2026-07-24 |

- **Escalations:** the ticket history has no record that any of these engagements or notifications happened.
- **Overdue items:** the claim decision and the credit memo are both past due. They should be done now.
- **Root-cause finding:** none is due. One is needed only if Northstar claims the customer caused the fault, and it hasn't.

**What Acme had to do, all met**
- Report a Severity 1 incident by phone: done, by phone at 02:14.
- Keep a technical contact reachable by phone until restoration: no failed call is recorded.
- Make a written claim naming the ticket within 30 days of restoration: done on 2026-06-24.

**Two gaps in the record**
- The claim event says only "by email". It doesn't confirm the email went to support-credits@northstar.example.
- Nothing records whether the escalation steps were carried out.

```json
{
  "outcome": "BREACH_CREDIT_OWED",
  "ticket": "SR-39385",
  "scope": "in",
  "true_severity": 1,
  "breach": {"response": "met", "restoration": "missed_band2"},
  "credit_usd": 4200,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager (incident lead)", "holder": "Hannah Lindqvist", "due": "2026-06-16T02:29:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Sarah Chen", "due": "2026-06-16T02:44:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-06-16T04:14:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "VP Sales", "holder": "Michael Torres", "due": "2026-06-16T06:14:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Chief Revenue Officer (Strategic account)", "holder": "David Morgan", "due": "2026-06-16T06:14:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-24"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": "2026-07-24"},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "SR-39385 ticket: CRM-2048, NS-500, phone, opened 2026-06-16T02:14:00-05:00, 'Line 4 is stopped. No workaround.', restored 2026-06-16T10:58:00-05:00",
    "Ticket events: engineer_response 2026-06-16T02:31:00-05:00; credit_claim by email from Edward Floyd 2026-06-24T10:12:00-05:00 'Credit claim for SR-39385'",
    "CRM-2048 DUNS 04-812-7730 = ERP C-1001 Acme Mfg. Holdings; tier Strategic; owner Sarah Chen",
    "Schedule C (ACME-MFG-2025): Platinum, covers NS-500, coverage from 2025-04-01 00:00 CT, fee $21,000/month from 2026-01",
    "Severity Guide: Sev 1 = product failure with no workaround that stops production",
    "SLS v2.0 (tickets opened on/after 2026-04-01 CT): Sev 1 response 30 min, restoration 4 h, 24x7; clocks start at open time; band 2 (>2x target) Sev 1 = 20%; monthly cap 30%; claim within 30 calendar days of restoration; Director of Customer Support decides within 30 days; Support Billing Manager issues memo same day",
    "Escalation Procedure: SEM by +15 min, account owner by +30 min, Director of Customer Support at 50%, VP Sales (and CRO for Strategic) at 100% of restoration target",
    "No maintenance notices for CRM-2048; no other June 2026 tickets; no service credits for June 2026 tickets or for SR-39385",
    "HR: Hannah Lindqvist (Support Escalation Manager), Marcus Adeyemi (Director of Customer Support), Michael Torres (VP Sales), David Morgan (CRO), Paul Brennan (Support Billing Manager)"
  ],
  "missing_evidence": [
    "No ticket events record the Support Escalation Manager engagement or the account owner, Director, VP Sales and CRO notifications",
    "The claim event does not state the receiving address (support-credits@northstar.example)",
    "No claim decision or credit memo recorded for SR-39385"
  ]
}
```

---

## X22 · S44

**SR-39690: a service level was breached, but no credit is owed (`BREACH_NO_CREDIT`).** The repair target was badly missed. Cedar Health's credit claim arrived about 8 hours after the deadline, and a late claim earns no credit.

**Customer and scope.** The customer is Cedar Health Systems Inc. (CRM account CRM-2063, ERP customer C-1003, DUNS 02-906-4418). Its support terms (SUP-CHS-2025, Silver plan, $4,000 a month) cover NS-EDGE, and coverage started on 2025-12-01. The ticket is in scope.

**True severity: Severity 2.** The customer also reported it as P2, but the rating comes from the impact. The chiller alarms stopped forwarding, so an alarm function was down for a site, not just intermittent. The severity guide rates that as Severity 2 even when the customer covers it with manual checks, as here with hourly rounds. Nothing was stopped and there was no total outage, so it is not Severity 1.

**Service levels.** Schedule v2.0 applies (tickets opened from 2026-04-01). Silver Severity 2 targets are a first reply within 2 business hours and repair within 12 business hours. Business hours are 08:00–18:00 Central, Monday to Friday. All times below are in Central Time.
- **Opened:** Tue 2026-07-28 09:30. There are no holidays that week, no recorded pauses and no maintenance notices on the account.
- **First reply: met.** An engineer's ticket comment came at 11:05, 1 hour 35 minutes after opening. The record says only "Engineer's ticket comment", so I've assumed it addressed the specific issue.
- **Repair: missed by more than double.** It was restored at Thu 2026-07-30 23:50 Central (00:50 on 07-31 Eastern). Counting only business hours, that is 28.5 hours (8.5 + 10 + 10). The 12-hour target ran out at Wed 2026-07-29 11:30. Going past 24 hours puts it in the top penalty band, worth 10% of the monthly fee: $400, well under the 30% monthly cap ($1,200).

**Credit claim: late.** A claim must arrive within 30 calendar days after the restoration date, by 23:59 Central on the last day.
- The restoration date in Central Time is 2026-07-30, so the deadline was **2026-08-29 23:59 Central**.
- The emailed claim arrived on 2026-08-30 at 08:12 Central (09:12 Eastern).
- The claim would only be on time if you counted from the Eastern date (07-31), and the schedule doesn't allow that.

**What Northstar owes.**
- **Engagement and notification:** none required. The escalation procedure only sets steps for Severity 1, so no one has to be engaged or notified for this ticket. That includes the account owner, Anthony Day.
- **Claim decision:** a claim was received, so Northstar should decide it (deny it as late) by **2026-09-29**, 30 days after receipt. The record doesn't name who decides claims. That date has already passed, and no decision is recorded.
- **Credit memo:** none, because no credit is approved.
- **Root-cause report:** the record contains no requirement for one.

**What the customer had to do.**
- **Phone report:** not needed. The telephone-report rule applies only to Severity 1, so reporting through the portal was fine.
- **Credit claim:** it was in writing and named the ticket, but it arrived late, so this obligation was not met.

```json
{
  "outcome": "BREACH_NO_CREDIT",
  "ticket": "SR-39690",
  "scope": "in",
  "true_severity": "Severity 2",
  "breach": {"response": "met", "restoration": "missed_band2"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "decide_claim", "role": null, "holder": null, "due": "2026-09-29T23:59:00-05:00"},
    {"party": "customer", "duty": "claim", "status": "not_met"}
  ],
  "evidence": [
    "CRM-2063 / ERP C-1003 / DUNS 02-906-4418: Cedar Health Systems Inc.",
    "Cedar Health Systems Support Terms SUP-CHS-2025: covers NS-EDGE; coverage starts 2025-12-01 00:00 CT; Silver plan; $4,000 per month from 2025-12",
    "Support Severity Guide, Severity 2 (b): alarming function unavailable, whether or not covered with manual checks",
    "Service Level Schedule v2.0 (tickets opened on or after 2026-04-01 CT): Sev 2 Silver = 2 business hours response / 12 business hours restoration; business hours 08:00-18:00 CT Mon-Fri",
    "Ticket opened 2026-07-28T10:30:00-04:00 (09:30 CT); engineer_response 2026-07-28T12:05:00-04:00 (11:05 CT) = 1h35m business",
    "Restored 2026-07-31T00:50:00-04:00 = 2026-07-30T23:50:00-05:00; 28.5 business hours elapsed, more than 2x the 12h target (band 2, Sev 2 = 10%)",
    "No pauses recorded; no maintenance notices for CRM-2063; no holidays 2026-07-28 to 2026-07-30",
    "Claim window: 30 calendar days after restoration date (CT), by 23:59 CT; deadline 2026-08-29T23:59:00-05:00",
    "Credit claim received 2026-08-30T09:12:00-04:00 (08:12 CT) - late; 'A late claim earns no credit'",
    "Support Escalation Procedure: engagement and notification steps are defined for Severity 1 only",
    "Claim decision due by the 30th calendar day after receipt"
  ],
  "missing_evidence": [
    "Content of the 12:05 engineer comment (assumed to address the specific issue)",
    "Role that decides credit claims",
    "Any record of the claim decision"
  ]
}
```

---

## X23 · S45

I've classified SR-39857 as **Severity 1**, and the outcome is **CANNOT_DECIDE**. The response target was met. Whether the restoration target was breached, and so whether a credit is owed, can't be settled yet: Northstar has claimed the outage was the customer's fault, and the root-cause finding that decides this isn't due until 2026-08-31 18:00 CT.

**Customer and scope.** The ticket's CRM account is CRM-2048. It matches ERP customer C-1001 (Acme Mfg. Holdings) through DUNS 04-812-7730. Acme's support terms (Schedule C to ACME-MFG-2025) cover the NS-500 under the Platinum plan, and coverage started 2025-04-01 00:00 CT. The ticket is in scope.

**True severity.** The record says "Line 2 is stopped. No workaround." That meets Severity 1: a production line stopped with no workaround. It matches the customer's own P1, but the classification comes from the recorded impact.

**Schedule and targets.** The ticket opened 2026-08-17 09:20 CT, so Schedule v2.0 applies. Severity 1 runs on a 24×7 clock: 30 minutes to respond and 4 hours to restore.

**Clock.** The clock started at 09:20 CT, when the hotline call came in. No pauses are recorded, and there is no maintenance notice for this account.

**Measurement.**
- **Response: met.** An engineer phoned the customer at 09:38, 18 minutes in.
- **Restoration: undecided.** Service was restored at 15:05, 5 h 45 min in. That is over the 4-hour target but under twice the target, so it would be a band 1 miss. However, at 15:30 Northstar claimed the outage was customer-caused: Acme reverted a VLAN change its network contractor made. Under v2.0, while that claim stands, no finding is recorded and the deadline hasn't passed, neither the breach nor any credit can be decided. The deadline is 18:00 CT on the 10th business day after restoration, which is 2026-08-31. No holidays fall in that period; Labor Day is 2026-09-07.

**Credit, depending on the finding.**
- **Customer-caused:** no restoration breach and no credit. The outcome becomes NO_BREACH.
- **Anything else, or no finding by the deadline:** it's a band 1 miss at 10% of the $21,000 monthly fee, so **$2,100**. That is within the $6,300 monthly cap (30%), and no other August credits exist. The outcome becomes BREACH_CREDIT_OWED.
- **The claim was timely.** Edward Floyd's email claim naming the ticket arrived 2026-08-20 08:40. The deadline is 2026-09-16 23:59 CT.

**What Northstar owes.** Customer-caused claims don't change escalation, and the line was still down at both the 50% and 100% marks. All the steps below were due on 2026-08-17 and are already past. **The ticket shows none of them was done**, so whether they happened needs checking.

| Duty | Role | Holder | Latest time |
|---|---|---|---|
| Engage as incident lead | Support Escalation Manager | Hannah Lindqvist | 2026-08-17T09:35-05:00 |
| Notify | Account owner | Sarah Chen | 2026-08-17T09:50-05:00 |
| Notify (50% of target) | Director of Customer Support | Marcus Adeyemi | 2026-08-17T11:20-05:00 |
| Notify (100% of target) | VP Sales | Michael Torres | 2026-08-17T13:20-05:00 |
| Notify (100%, Strategic account) | Chief Revenue Officer | David Morgan | 2026-08-17T13:20-05:00 |
| Record root-cause finding | Support Engineering Lead | Owen Takahashi | 2026-08-31T18:00-05:00 |
| Decide the claim, written decision | Director of Customer Support | Marcus Adeyemi | 2026-09-19 |
| Issue credit memo, if approved | Support Billing Manager | Paul Brennan | Same day as approval |

**What the customer must do.** All of it is done:
- **Report by phone:** met. Kelly Ballard opened the ticket by phone.
- **Claim in writing in time:** met (2026-08-20).
- **Keep a technical contact reachable until restoration:** no failed contact attempts are recorded.

```json
{
  "outcome": "CANNOT_DECIDE",
  "ticket": "SR-39857",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "met", "restoration": "cannot_decide"},
  "credit_usd": null,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-08-17T09:35:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Sarah Chen", "due": "2026-08-17T09:50:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-08-17T11:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "VP Sales", "holder": "Michael Torres", "due": "2026-08-17T13:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Chief Revenue Officer", "holder": "David Morgan", "due": "2026-08-17T13:20:00-05:00"},
    {"party": "northstar", "duty": "record_root_cause", "role": "Support Engineering Lead", "holder": "Owen Takahashi", "due": "2026-08-31T18:00:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-09-19"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "SR-39857: CRM-2048, NS-500, phone, opened 2026-08-17T09:20:00-05:00, 'Line 2 is stopped. No workaround.', restored 2026-08-17T15:05:00-05:00",
    "Events: engineer_response 2026-08-17T09:38:00-05:00; note 2026-08-17T15:30:00-05:00 asserting customer-caused exclusion (VLAN change), root-cause finding to follow; credit_claim 2026-08-20T08:40:00-05:00 by Edward Floyd (email)",
    "CRM-2048 DUNS 04-812-7730 = ERP C-1001 Acme Mfg. Holdings; account tier Strategic; owner Sarah Chen",
    "Schedule C (ACME-MFG-2025): Platinum plan, covers NS-500 and NS-EDGE, coverage from 2025-04-01 00:00 CT, fee $21,000/month from 2026-01",
    "Service Level Schedule v2.0 (tickets opened on or after 2026-04-01 CT): Severity 1 targets 30 min response / 4 h restoration, 24x7; band 1 credit 10%; cap 30% of monthly fee; claim within 30 calendar days of restoration; claim decided within 30 days by Director of Customer Support; memo by Support Billing Manager same day as approval",
    "v2.0 customer-caused exclusion: Support Engineering Lead records finding by 18:00 CT on the 10th business day after restoration; until then restoration breach and credit cannot be decided; no finding by deadline means decided as if never asserted; escalation not affected",
    "Severity Guide: Severity 1 = product failure that stops a production line with no workaround",
    "Escalation Procedure: Support Escalation Manager within 15 min; account owner within 30 min; Director of Customer Support at 50% of restoration target; VP Sales at 100% (and CRO for Strategic accounts)",
    "No maintenance notices for CRM-2048; no other August 2026 credits on the account; Holiday Calendar has no holidays between 2026-08-18 and 2026-08-31"
  ],
  "missing_evidence": [
    "Root-cause finding from the Support Engineering Lead (due 2026-08-31T18:00:00-05:00), which decides the restoration breach and the credit ($0 if customer-caused, otherwise $2,100)",
    "No record that any of the escalation steps (engagement and the four notifications) were carried out"
  ]
}
```

---

## X24 · S43

**SR-39802 is out of scope.** Acme Industrial Supply Co. has no Northstar support terms, so no service level applies, nothing can be breached and no credit is owed. Northstar's only duty is to tell the account owner, Zachary Brown, by **2026-08-10 18:00 CDT**. Nothing on the ticket shows that this was done.

**1. The customer.** The ticket's CRM account is CRM-2091, Acme Industrial Supply Co. Its DUNS is 09-552-1187 and its ERP customer is C-1044, 17 Tallmadge Ave, Akron, OH. "Acme" and "Acme Platinum plan" are only the caller's words. The company with the Platinum plan is a different one: Acme Mfg. Holdings / Acme Manufacturing (CRM-2048, C-1001, DUNS 04-812-7730, Milwaukee).

**2. Scope.** Acme Manufacturing's Schedule C (ACME-MFG-2025) gives Platinum cover for NS-500 and NS-EDGE, but only to Acme Mfg. Holdings. It says: "Acme Industrial Supply Co. is a different company and is not covered." It also excludes the parent company and "any other affiliate." The other support terms in the knowledge base (BlueRiver Logistics, Cedar Health) are for other customers. Nothing covers DUNS 09-552-1187, so the ticket is out of scope.

**3. True severity: Severity 1, for internal priority only.** All NS-Edge gateways at the Akron distribution centre were down, picking had stopped and there was no workaround. Under the severity guide, that is a distribution activity that cannot continue. For an out-of-scope ticket the escalation procedure says "severity is classified only for internal priority."

**4–6. Service level.** For out-of-scope tickets the procedure says "no targets apply" and "nothing can be breached." For reference only, in Central time: the ticket was opened by phone at 05:05 CDT on 10 August. An engineer first responded at 06:40, after 1 h 35 min. Service was restored at 13:15, after 8 h 10 min. Those times would have missed a Severity 1 target of 30 minutes to respond and 4 hours to restore. Because no terms cover this customer, those targets don't apply here.

**7. Credit.** None is owed. Amy Barrett's claim of 2026-08-14 for "the Severity 1 restoration credit under Acme's Platinum plan" has no basis, because that plan belongs to a different company.

**8. What Northstar owes**
- **Notify the account owner.** Northstar Support must tell the owner of CRM-2091 within 10 business hours of the open time. Business hours are 08:00–18:00 CT, Monday to Friday. The ticket opened at 05:05 CDT on Monday, so the clock started at 08:00 and the deadline was 18:00 CDT the same day. The owner is Zachary Brown (EMP-502, Enterprise Account Executive). The ticket history shows no such notice. Since today is 2026-10-19, it should be checked or followed up.
- **Handle the ticket on a best-effort basis.** The Severity 1 escalation steps do not apply: no Support Escalation Manager, Director of Customer Support or VP Sales.
- **Claim reply.** The claim needs an answer saying it is declined because the ticket is out of scope. None of the documents I found sets a deadline for that answer.

**What the customer must do.** Under support terms, nothing. A phone report or a timely claim would only matter if a plan covered this ticket. If Acme Industrial wants SLA cover, it needs its own support agreement.

I didn't use the "Clarification Bulletin" or the timestamp note that came with the database notes. They would change the clock rules, but they don't affect a ticket that is out of scope. I also couldn't list the holiday calendar's dates; 10 August 2026 is not a usual US holiday.

```json
{
  "outcome": "OUT_OF_SCOPE",
  "ticket": "SR-39802",
  "scope": "out",
  "true_severity": "Severity 1 (internal priority only)",
  "breach": {"response": "not_applicable", "restoration": "not_applicable"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "notify", "role": "Account owner (CRM-2091)", "holder": "Zachary Brown", "due": "2026-08-10T18:00:00-05:00"}
  ],
  "evidence": [
    "service_tickets SR-39802: account CRM-2091, NS-EDGE, phone, opened 2026-08-10T06:05:00-04:00, restored 2026-08-10T14:20:00-04:00; 'All NS-Edge gateways at the Akron distribution center have been offline... picking has halted. No workaround.'",
    "crm_accounts CRM-2091 Acme Industrial Supply Co., DUNS 09-552-1187, tier Standard, owner Zachary Brown; ERP C-1044 same DUNS",
    "Schedule C (ACME-MFG-2025): Platinum plan for Acme Mfg. Holdings (DUNS 04-812-7730); 'Acme Industrial Supply Co. is a different company and is not covered.'; no cover for parent or any other affiliate",
    "SOP-SUPPORT-007, out-of-scope tickets: best effort; severity for internal priority only; no targets apply; nothing can be breached; no credit owed; escalations do not apply; notify account owner within 10 business hours of open time",
    "Service Level Schedule v2.0: business hours 08:00-18:00 CT Mon-Fri except Northstar holidays; all times in America/Chicago",
    "Severity Guide: Severity 1 = no workaround and a distribution activity cannot continue",
    "ticket_events: engineer_response 2026-08-10T07:40:00-04:00; credit_claim by email 2026-08-14T10:00:00-04:00 citing 'Acme's Platinum plan'"
  ],
  "missing_evidence": [
    "No record that the account owner was notified of the out-of-scope ticket",
    "Holiday calendar dates could not be listed; 2026-08-10 is assumed not to be a Northstar holiday"
  ]
}
```

---

## X25 · S41

**SR-39644 is Severity 2, not the P1 Acme reported. Both service levels were met: the outcome is NO_BREACH, and no service credit is owed.** The restoration target was met with nothing to spare: exactly 12h 00m against 12 hours.

**1. Customer and scope.** The ticket is on CRM account CRM-2048 (DUNS 04-812-7730). That DUNS matches ERP customer C-1001, "Acme Mfg. Holdings", the customer named in Acme's Schedule C. That agreement gives Acme the Platinum plan and covers NS-EDGE. Coverage started on 2025-04-01, so the ticket is in scope.

**2. True severity: Severity 2 (High).** The ticket says the gateways stopped sending vibration data for presses 1–6 at Plant 2. The presses kept running, and technicians are doing manual checks every two hours. That is not Severity 1, because production didn't stop. It meets Severity 2 criterion (b): "a … condition-monitoring function is unavailable … whether or not the customer covers it with manual checks."

**3. Schedule and targets.** Schedule v2.0 applies because the ticket opened after 2026-04-01. For Severity 2 on the Platinum plan, the targets are a 2-hour response and a 12-hour restoration, on a 24×7 clock that starts at the open time. All the timestamps already carry −05:00, which is Central Daylight Time, so no conversion was needed.

**4. Measurement.**
- **Response: met.** The ticket opened at 2026-07-23 13:10 CT. An engineer commented at 15:00 CT asking for VPN credentials, which is 1h 50m against a 2-hour target.
- **Pause:** the ticket was in "Awaiting Customer" from 07-23 15:00 to 07-24 08:30 CT. Both the start and the end are recorded, so the 17h 30m counts as a pause.
- **Restoration: met.** It was restored at 07-24 18:40 CT. That is 29h 30m of elapsed time minus the 17h 30m pause, which leaves 12h 00m. The first credit band starts only at *more than* the target, so exactly 12h is met.
- **Exclusions:** there is no maintenance notice on record for this account, so no maintenance exclusion applies.

**5. Credits.** None are owed because nothing was missed. No credit claim is recorded on the ticket either.

**6. Northstar's obligations.**
- Acme Manufacturing is a Strategic account, but that tier doesn't matter here. The Strategic and other escalation steps I found in the escalation procedure apply to Severity 1, so they don't apply to this ticket. This includes notifying the account owner, Sarah Chen.
- I found no escalation steps for Severity 2 tickets in the knowledge base. If the procedure does have a Severity 2 step at 50% of the target, it would have fallen due at about 07-24 12:40 CT, which is 6 hours into the restoration clock and before the ticket was restored. That role, its holder and the deadline are not recorded, so I haven't listed them.
- No root-cause finding is due, because Northstar is not claiming the customer caused the incident.
- No claim decision or credit memo is due.

**7. What Acme must do.**
- The telephone-report rule applies only to Severity 1, so Acme's portal report was acceptable.
- Acme had to provide the access Northstar needed, and it did: the VPN credentials were recorded as provided at 07-24 08:30.
- A claim would have been due by 2026-08-23 23:59 CT (30 days after restoration), but there is nothing to claim.

**Things that could change the result:**
- **When the credentials arrived.** The 15:00 status note already says Kelly Ballard "provided them", but the record of the access being provided is the 08:30 entry. If the credentials actually arrived earlier, the pause would be shorter and restoration would be over 12h, which would be a breach.
- **Time zone of the restoration time.** An internal data note says "Restored" values on post-April tickets are stored in UTC when no zone is shown. This ticket's value shows −05:00 explicitly, so I took it as Central Time.

```json
{
  "outcome": "NO_BREACH",
  "ticket": "SR-39644",
  "scope": "in",
  "true_severity": "Severity 2",
  "breach": {"response": "met", "restoration": "met"},
  "credit_usd": 0,
  "obligations": [],
  "evidence": [
    "service_tickets SR-39644: CRM-2048, NS-EDGE, portal, opened 2026-07-23T13:10:00-05:00, reported P1, restored 2026-07-24T18:40:00-05:00; impact: vibration data lost for presses 1–6, presses running, manual checks every two hours",
    "crm_accounts CRM-2048 DUNS 04-812-7730 = ERP C-1001 Acme Mfg. Holdings; tier Strategic; owner Sarah Chen",
    "Schedule C (Acme): Platinum plan; covers NS-500 and NS-EDGE; coverage from 2025-04-01 00:00 CT; fee $21,000/month from 2026-01",
    "Support Severity Guide: Severity 2 (b) covers condition monitoring unavailable even with manual checks; Severity 1 needs production stopped and no workaround",
    "Service Level Schedule v2.0: applies to tickets opened on or after 2026-04-01; Severity 2 Platinum = 2h response, 12h restoration, 24x7 clock, both clocks start at open time; Awaiting Customer pauses only the restoration clock and counts only with a recorded start and end; first credit band starts at more than the target",
    "ticket_events: engineer_response 2026-07-23T15:00-05:00; Awaiting Customer 2026-07-23T15:00-05:00 to 2026-07-24T08:30-05:00 (17.5h); restored 2026-07-24T18:40-05:00",
    "Response 1h50m (target 2h); restoration 29h30m minus 17h30m = 12h00m (target 12h)",
    "maintenance_notices: none for CRM-2048; no credit_claim event on the ticket",
    "Support Escalation Procedure: the steps found apply to Severity 1 (and Severity 3), not Severity 2; root-cause finding only when the customer-caused exclusion is asserted"
  ],
  "missing_evidence": [
    "Severity 2 escalation steps (if any) are not in the knowledge base; a step at 50% of the target would have fallen due about 2026-07-24T12:40:00-05:00, but its role and holder are not recorded",
    "When the VPN credentials were actually provided: the 15:00 status note says they were provided, but the recorded end of the pause is 08:30 the next day",
    "Timestamp note SUP-DATA-NOTE-014 says Restored values on post-2026-04-01 tickets are written in UTC; this value carries an explicit -05:00 offset and was taken as Central Time"
  ]
}
```

---

## X26 · S42

I couldn't make a final decision on SR-38862. The 1-hour response target was missed, but whether Acme gets a credit depends on one number I couldn't find: the credit-claim window in the Service Level Schedule v1.0. Acme filed its claim 41 days after restoration.

**Customer and scope.** The ticket is on CRM account CRM-2048 (Acme Manufacturing, Strategic tier). Its ERP record is C-1001, "Acme Mfg. Holdings", and both carry DUNS 04-812-7730. Acme's support terms (Schedule C) cover the NS-500 on the Platinum plan, and coverage started 2025-04-01. The ticket is in scope.

**True severity: Severity 1.** The paint line is stopped and there is no workaround. That meets the severity guide's Severity 1 definition: a product failure that stops production, with no workaround.

**Which schedule applies: v1.0.** The ticket opened at 2026-03-31 22:50 Central time (CDT, UTC−5). Version 1.0 covers tickets opened up to 2026-03-31 23:59 Central. The system log shows 2026-04-01 03:50 UTC, which looks like April 1, but in the schedule's time zone it is still March 31. Under v1.0, Severity 1 has a 1-hour response target and an 8-hour restoration target, measured around the clock.

**Clock.** It started at 22:50. There's no recorded pause, no maintenance notice on the account, and Northstar didn't claim the customer caused the incident.

**Measurement:**
- **Response: missed.** The deadline was 23:50. The engineer phoned at 23:58, 8 minutes late.
- **Restoration: met.** Restored at 05:35 on April 1, which is 6 h 45 min against an 8-hour target.

**Credit:**
- The Severity 1 rate applies because the customer reported the incident by phone before restoration. The rate for a missed response is 5% of the $21,000 monthly fee: $1,050.
- The monthly cap is 20%, or $4,200. Two credits on Acme's other March tickets are already approved: SR-38655 ($3,150) and SR-38790 ($420). That leaves $630, so the credit would be cut to $630.00.
- Edward Floyd (Acme's VP Procurement) sent the claim by email on 2026-05-12, 41 days after restoration on 2026-04-01.
- In v2.0 the window is 30 days, which would make this claim late (deadline 2026-05-01 23:59 Central). The knowledge base doesn't hold the length of v1.0's window. So:
  - **If v1.0 also allows 30 days:** the claim is late and no credit is owed.
  - **If it allows 41 days or more:** $630.00 is owed.
- The number has to be read from the v1.0 document.

**Who Northstar had to engage or notify, and by when:**
- **Hannah Lindqvist (Support Escalation Manager):** engage as incident lead by 2026-03-31 23:05 −05:00.
- **Sarah Chen (account owner):** notify by 2026-03-31 23:20 −05:00.
- **Marcus Adeyemi (Director of Customer Support):** notify by 2026-04-01 02:50 −05:00, because the line was still down when half the restoration target had passed.
- **No VP Sales (Michael Torres) or Chief Revenue Officer (David Morgan) notice was required.** Restoration came before the full 8 hours. I'm reading the escalation procedure as tying the CRO notice for Strategic accounts to that 100% point.
- The record shows no evidence that any of these engagements or notices happened.

**Credit claim handling:**
- **Marcus Adeyemi** must send a written decision by 2026-06-11, the 30th day after the claim arrived. None is recorded, so it appears overdue.
- **Paul Brennan (Support Billing Manager)** issues the credit memo the same day, if the claim is approved.
- No root-cause finding is due, because no exclusion was claimed.

**What the customer had to do:**
- **Report a Severity 1 incident by phone: done.** It was reported by phone before restoration.
- **File a timely written claim that names the ticket:** a claim naming the ticket was filed, but whether it was on time depends on the v1.0 window.
- **Keep a technical contact reachable by phone until restoration, and give Northstar the information and access it needs:** nothing in the record shows a failure.

```json
{
  "outcome": "CANNOT_DECIDE",
  "ticket": "SR-38862",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "missed", "restoration": "met"},
  "credit_usd": null,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-03-31T23:05:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Sarah Chen", "due": "2026-03-31T23:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-04-01T02:50:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-06-11"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": null}
  ],
  "evidence": [
    "Ticket SR-38862: CRM-2048, NS-500, phone, opened 2026-03-31T22:50:00-05:00, 'paint line is stopped. No workaround', restored 2026-04-01T05:35:00-05:00",
    "Events: engineer_response 2026-03-31T23:58:00-05:00; credit_claim by Edward Floyd (email) 2026-05-12T09:00:00-05:00; system log 2026-04-01T03:50Z = 22:50 CDT",
    "CRM-2048 / ERP C-1001 / DUNS 04-812-7730; account owner Sarah Chen; tier Strategic",
    "Schedule C (ACME-MFG-2025): Platinum, covers NS-500, coverage from 2025-04-01 00:00 CT; fee $21,000/month from 2026-01",
    "Severity Guide: Sev 1 = product failure stopping production, no workaround",
    "SLS v1.0: applies to tickets opened through 2026-03-31 23:59 CT; Sev 1 response 1 h, restoration 8 h, 24x7; Sev 1 credit 5% response if phoned before restoration; cap 20% of the month's fee, in approval order; claim decided by Director of Customer Support within 30 calendar days; memo by Support Billing Manager same day",
    "Escalation Procedure: Support Escalation Manager within 15 min; account owner within 30 min; Director of Customer Support at 50% of restoration target; VP Sales (and CRO for Strategic) at 100%",
    "Credits already approved for March 2026 tickets: SCR-38655 $3,150, SCR-38790 $420 (remaining cap $630)",
    "No maintenance notices for CRM-2048; no recorded pause; no exclusion asserted"
  ],
  "missing_evidence": [
    "Credit-claim window length in Service Level Schedule v1.0 (v2.0 states 30 calendar days after restoration; claim received 41 days after restoration). Credit is $630.00 if timely, $0 if late",
    "Records of the Support Escalation Manager engagement and the account-owner and Director notifications",
    "Record of a written decision on the 2026-05-12 claim"
  ]
}
```

---

## X27 · S39

I've determined the true severity, measured the targets and worked out the credit. The main limit is that Northstar's records don't show the escalation steps or the credit decision as done, and both deadlines have passed.

**Customer and scope:** Ticket SR-39340 is on CRM account CRM-2063. Through its DUNS number (02-906-4418) that account matches ERP customer C-1003, Cedar Health Systems Inc. Its support terms (SUP-CHS-2025, Silver plan, $4,000 a month) cover NS-CLOUD, and coverage started on 2025-12-01. The ticket is in scope.

**True severity: Severity 1, not the P3 the customer reported.** NS-Cloud was unavailable to all users at all 14 facilities, with no workaround. That meets the severity guide's Severity 1 test: "makes NS-Cloud unavailable to all of the customer's users." Northstar's engineer confirmed this and reclassified the ticket.

**Schedule and clock:** The ticket opened at 2026-06-10 06:05 Central Time (07:05 Eastern), so schedule v2.0 applies. Severity 1 runs on a 24×7 clock (all elapsed time counts) from the open time. The targets are a 30-minute response and a 4-hour restoration. No pauses are recorded and the account has no maintenance notices, so nothing is paused or excluded.

**Was a service level breached? Yes, both targets were missed:**
- **Response:** due by 06:35 CT; the engineer's call came at 08:20 CT, 2 h 15 m after open.
- **Restoration:** due by 10:05 CT; service came back at 11:35 CT, 5 h 30 m after open. That is more than the 4-hour target but no more than double it, so it falls in the lower credit band.

**What Northstar owes: a $320.00 credit.**
- Cedar reported the outage only through the portal, never by phoning the Support hotline. Under the schedule, the higher Severity 1 credit rates apply only with a phone report; otherwise the Severity 2 rates apply.
- Caveat: I found that consequence stated in v1.0's text. v2.0's text requires the phone report and says a portal ticket doesn't count, but I applied the same rule. If v2.0 did give Severity 1 rates here, the credit would be 15%, or $600.
- At Severity 2 rates: 3% for the response plus 5% for the restoration is 8% × $4,000 = $320.00.
- That is under the monthly cap of 30% ($1,200). This is Cedar's only June ticket and no earlier credits are recorded.
- The claim was on time. Cedar emailed it on 2026-06-29 at 10:00 CT, and the window ran to 2026-07-10 23:59 CT.

**Who had to be engaged or notified, and by when (all CT on 2026-06-10, Severity 1):**

| Duty | Who | Latest time |
|---|---|---|
| Engage as incident lead | Hannah Lindqvist, Support Escalation Manager | 06:20 |
| Notify the account owner | Anthony Day | 06:35 |
| Notify, since not restored at 50% of the target | Marcus Adeyemi, Director of Customer Support | 08:05 |
| Notify, since not restored at 100% of the target | Michael Torres, VP Sales | 10:05 |

The account is Standard tier, so the Chief Revenue Officer did not need to be told. The ticket history shows none of these steps.

**Claim decision and credit memo:**
- Marcus Adeyemi had to send a written decision by 2026-07-29.
- Paul Brennan, Support Billing Manager, had to issue the credit memo the same day it was approved.
- No credit is recorded for this account, so both look overdue today.
- No root-cause finding is due, because no customer-caused exclusion was claimed.

**What the customer had to do:**
- **Phone report: not met.** A Severity 1 incident must be reported by phoning the Support hotline, (312) 555-0187. A portal ticket or Northstar's own call doesn't count.
- **Credit claim: met.** It was in writing, named the ticket and arrived on time.
- Cedar also had to keep a technical contact reachable by phone until restoration. No failed contact attempt is recorded.

```json
{
  "outcome": "BREACH_CREDIT_OWED",
  "ticket": "SR-39340",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "missed", "restoration": "missed_band1"},
  "credit_usd": 320.00,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-06-10T06:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Anthony Day", "due": "2026-06-10T06:35:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-06-10T08:05:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "VP Sales", "holder": "Michael Torres", "due": "2026-06-10T10:05:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-29"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": "same day as approval (no later than 2026-07-29)"},
    {"party": "customer", "duty": "phone_report", "status": "not_met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "SR-39340 ticket: CRM-2063, NS-CLOUD, portal, reported P3, opened 2026-06-10T07:05:00-04:00, restored 2026-06-10T12:35:00-04:00; description: NS-Cloud won't load for anyone, none of 14 facilities can see equipment status or alarms",
    "Ticket events: engineer_response 2026-06-10T09:20:00-04:00 (phoned Cedar, all users affected, no workaround, reclassified Severity 1); restored 2026-06-10T12:35:00-04:00; credit_claim by email 2026-06-29T11:00:00-04:00 naming SR-39340",
    "CRM-2063 Cedar Health Systems, DUNS 02-906-4418, tier Standard, owner Anthony Day; ERP C-1003 Cedar Health Systems Inc. (same DUNS)",
    "Cedar Health Systems Support Terms SUP-CHS-2025: covers NS-CLOUD and NS-EDGE, coverage from 2025-12-01 00:00 CT, Silver plan, $4,000/month from 2025-12",
    "Support Severity Guide: Severity 1 (b) NS-Cloud unavailable to all users with no workaround",
    "Service Level Schedule v2.0 (tickets opened on/after 2026-04-01 CT): Sev 1 response 30 min, restoration 4 h, 24x7 clock, clocks start at open time; credits Sev1 5%/10%, Sev2 3%/5% (band 1); cap 30% of monthly fee; claim within 30 calendar days of restoration date; decision within 30 days of receipt; memo same day by Support Billing Manager",
    "v2.0: customer must report Sev 1 by telephoning the Support hotline (312) 555-0187; portal submission or Northstar call is not a telephone report",
    "v1.0 text: Sev 1 credit percentages apply only with a telephone report before restoration, otherwise Sev 2 percentages apply; Director of Customer Support decides every claim",
    "Support Escalation Procedure: Sev 1 engage Support Escalation Manager by +15 min, notify account owner by +30 min, Director of Customer Support at 50% and VP Sales at 100% of restoration target if not restored; CRO only for Strategic tier",
    "No maintenance notices for CRM-2063; no service credits recorded for CRM-2063; SR-39340 is the only ticket opened in June 2026",
    "HR: Hannah Lindqvist (Support Escalation Manager), Marcus Adeyemi (Director of Customer Support), Michael Torres (VP Sales), Paul Brennan (Support Billing Manager), Anthony Day (account owner)"
  ],
  "missing_evidence": [
    "No ticket record that the Support Escalation Manager, account owner, Director of Customer Support or VP Sales were engaged or notified",
    "No recorded claim decision or credit memo for SR-39340; both deadlines have passed",
    "The rule that Severity 2 rates apply without a phone report was found in v1.0's text; v2.0's version of it was not found separately in the knowledge base",
    "The claim email's recipient address is not recorded (the schedule requires support-credits@northstar.example or the portal)"
  ]
}
```

---

## X28 · S39

**SR-39340 is a Severity 1 incident, and both of its service targets were missed. Cedar Health is owed a $320.00 service credit.** The customer reported it as P3, but that is only their view of the priority.

**1. Customer and scope.** The ticket is on CRM account CRM-2063, DUNS 02-906-4418, ERP customer C-1003. Cedar's support terms (SUP-CHS-2025) give it the Silver plan, cover NS-CLOUD, started coverage on 2025-12-01 and set a fee of $4,000 a month. The ticket is in scope.

**2. True severity: 1.** The Severity Guide makes it Severity 1 when, with no workaround, NS-Cloud is unavailable to all of the customer's users. The ticket says "won't load for anyone… none of our 14 facilities". At 09:20 EDT a Northstar engineer confirmed every user was affected with no workaround and reclassified it as Severity 1. Because there was no workaround, it does not drop back to Severity 2.

**3. Schedule and times (US Central).** The ticket opened 2026-06-10 at 06:05 CDT, so Schedule v2.0 applies. Severity 1 runs on a 24×7 clock: 30 minutes to respond and 4 hours to restore. The clock starts when the ticket was opened. No pause was recorded, there is no maintenance notice on file and no exclusion was claimed.
- **Response:** 08:20 CDT, 2 h 15 m after opening against a 30-minute target. **Missed.**
- **Restoration:** 11:35 CDT, 5 h 30 m after opening against a 4-hour target. That is within twice the target, so **missed, band 1.**
- A data note says some fields are stored in Central time or UTC, but every stamp here carries a -04:00 offset. Under either reading the gaps are the same, so the result doesn't change.

**4. Credit: $320.00.** Cedar reported the outage through the portal, not by phoning the Support hotline, and Northstar's call to Cedar doesn't count. So whether a target was missed is measured against the Severity 1 targets, but the credit uses the Severity 2 rates:
- 3% for the late response plus 5% for band-1 restoration makes 8% of $4,000, which is $320.00.
- The monthly cap is 30% of $4,000, or $1,200. No other credits were approved for June, so the cap doesn't reduce it.
- Cedar emailed its claim, naming the ticket, on 2026-06-29 at 10:00 CDT. The deadline was 2026-07-10 at 23:59 CDT, so the claim was on time.

**5. What Northstar owes (escalation follows the true severity; the phone rule doesn't change it)**

| Role | Holder | Duty | Latest time |
|---|---|---|---|
| Support Escalation Manager | Hannah Lindqvist | Take over as incident lead | 2026-06-10 06:20 CDT |
| Account owner | Anthony Day | Be notified | 2026-06-10 06:35 CDT |
| Director of Customer Support | Marcus Adeyemi | Be notified (half the restoration time gone, not restored) | 2026-06-10 08:05 CDT |
| VP Sales | Michael Torres | Be notified (restoration target passed, not restored) | 2026-06-10 10:05 CDT |
| Director of Customer Support | Marcus Adeyemi | Send a written decision on the claim | 2026-07-29 |
| Support Billing Manager | Paul Brennan | Issue the credit memo | Same day the claim is approved |

- The Chief Revenue Officer doesn't need to be told, because Cedar is a Standard-tier account.
- No root-cause finding is due, because no exclusion was claimed.
- The ticket history doesn't show any of the escalation or notification steps being done.
- No approved credit is on file for this ticket, and the claim deadline has now passed, which needs follow-up.

**6. What the customer had to do**
- **Report a Severity 1 by phone to the hotline:** not met. That is why the lower credit rates apply.
- **Make a written claim within 30 days:** met.

```json
{
  "outcome": "BREACH_CREDIT_OWED",
  "ticket": "SR-39340",
  "scope": "in",
  "true_severity": 1,
  "breach": {"response": "missed", "restoration": "missed_band1"},
  "credit_usd": 320.00,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-06-10T06:20:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Anthony Day", "due": "2026-06-10T06:35:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-06-10T08:05:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "VP Sales", "holder": "Michael Torres", "due": "2026-06-10T10:05:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-29"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": null},
    {"party": "customer", "duty": "phone_report", "status": "not_met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39340: CRM-2063, NS-CLOUD, portal, opened 2026-06-10T07:05-04:00, P3, 'NS-Cloud won't load for anyone… None of our 14 facilities', restored 2026-06-10T12:35-04:00",
    "ticket_events: engineer_response 2026-06-10T09:20-04:00 (all users affected, no workaround, reclassified Severity 1); credit_claim by email 2026-06-29T11:00-04:00 naming SR-39340",
    "crm_accounts CRM-2063: DUNS 02-906-4418, tier Standard, owner Anthony Day; ERP C-1003 same DUNS",
    "SUP-CHS-2025: Silver plan, covers NS-CLOUD and NS-EDGE, coverage from 2025-12-01 00:00 CT, $4,000/month from 2025-12",
    "Support Severity Guide: Severity 1 (b) NS-Cloud unavailable to all users, no workaround",
    "Service Level Schedule v2.0: Sev 1 targets 30 min response / 4 h restoration, 24x7; Sev 1 must be reported by hotline phone, portal/email or a Northstar call does not count; target misses measured against Sev 1 targets but Sev 2 percentages apply (response 3%, restoration band 1 5%); monthly cap 30%; claim window 30 calendar days after restoration date; decision within 30 days of receipt; memo by Support Billing Manager same day as approval",
    "Support Escalation Procedure: Sev 1 incident lead within 15 min, account owner within 30 min, Director at 50% of restoration target, VP Sales at 100%, CRO only for Strategic accounts; telephone rule does not affect escalation",
    "Support Organization and Escalation Contacts: Hannah Lindqvist, Marcus Adeyemi, Michael Torres, Paul Brennan, David Morgan",
    "maintenance_notices: none for CRM-2063; service_credits: none for CRM-2063; no other CRM-2063 ticket opened in June 2026"
  ],
  "missing_evidence": [
    "No record that the Severity 1 escalation and notification steps were carried out",
    "No recorded claim decision or credit memo for SR-39340 (decision was due 2026-07-29)"
  ]
}
```

---

## X29 · S36

**SR-39385 is a Severity 1 ticket. Northstar met the response target but missed the restoration target by more than twice its length, so Acme is owed a $4,200.00 service credit. Acme made a timely written claim. The claim decision was due by 2026-07-24, and the record shows no decision and no approved credit.**

1. **Customer and scope.** The ticket is on CRM account CRM-2048, which carries DUNS 04-812-7730. That DUNS matches ERP customer C-1001 (Acme Mfg. Holdings) and the DUNS named in Acme's support terms ("Schedule C"). Those terms give a Platinum plan, cover the NS-500 and NS-EDGE products, and started coverage on 2025-04-01 00:00 CT. The ticket is in scope.
2. **True severity: Severity 1.** The impact recorded is "Line 4 is stopped. No workaround." The severity guide makes that Severity 1: a product failure that stops a production line with no workaround available. The customer's reported P1 doesn't set severity. No workaround was put in place later, so the rule that drops a ticket to Severity 2 doesn't apply.
3. **Schedule and targets.** The ticket opened at 2026-06-16 02:14 CDT, so Service Level Schedule v2.0 applies (tickets opened from 2026-04-01). Severity 1 runs on a 24×7 clock, with a 30-minute response target and a 4-hour restoration target.
4. **Measurement.** All times in the record carry an explicit −05:00 offset, which is already Central Daylight Time, so no conversion was needed. No pause is recorded and no maintenance notice exists for this account, so there are no pauses or exclusions.
   - **Response:** an engineer phoned at 02:31, 17 minutes after opening. **Met.**
   - **Restoration:** restored at 10:58, 8 hours 44 minutes after opening. That is more than twice the 4-hour target (8 hours), so it falls in the higher penalty band ("band 2"). **Missed.**
5. **Credit.** The band 2 rate for Severity 1 is 20%. June 2026's support fee is $21,000, so the credit is 20% × $21,000 = **$4,200.00**. The monthly cap is 30% of the fee, or $6,300. No other Acme ticket opened in June 2026 and no June credits are recorded, so the cap doesn't reduce the credit. The response credit is zero because that target was met.
6. **Claim.** Edward Floyd, Acme's VP Procurement, emailed a claim naming SR-39385 on 2026-06-24 at 10:12 CDT. The claim window ran to 2026-07-16 23:59 CT (30 days after the 06-16 restoration date), so the claim was **timely**.

**Who Northstar had to engage or notify, and by when** (escalation is based on the true severity; clock start is 02:14 CDT):

| Duty | Role | Holder | Latest time |
|---|---|---|---|
| Engage as incident lead | Support Escalation Manager | Hannah Lindqvist | 2026-06-16 02:29 −05:00 |
| Notify | Account owner (per CRM) | Sarah Chen | 2026-06-16 02:44 −05:00 |
| Notify (not restored at 50% of target) | Director of Customer Support | Marcus Adeyemi | 2026-06-16 04:14 −05:00 |
| Notify (not restored at 100% of target) | VP Sales | Michael Torres | 2026-06-16 06:14 −05:00 |
| Notify (Strategic account, 100% of target) | Chief Revenue Officer | David Morgan | 2026-06-16 06:14 −05:00 |
| Decide the claim in writing | Director of Customer Support | Marcus Adeyemi | 2026-07-24 |
| Issue the credit memo, same day as approval | Support Billing Manager | Paul Brennan | 2026-07-24 at the latest |

The ticket history shows no record of these engagements or notifications. No root-cause finding is due, because Northstar is not claiming the outage was customer-caused.

**What the customer had to do.** Acme reported a Severity 1 by phoning the hotline: met (Johnny Johnson opened the ticket by phone). It filed a timely written claim naming the ticket: met. It had to keep a technical contact reachable by phone until restoration, and no failed contact attempt is recorded.

```json
{
  "outcome": "BREACH_CREDIT_OWED",
  "ticket": "SR-39385",
  "scope": "in",
  "true_severity": "Severity 1",
  "breach": {"response": "met", "restoration": "missed_band2"},
  "credit_usd": 4200.00,
  "obligations": [
    {"party": "northstar", "duty": "engage", "role": "Support Escalation Manager", "holder": "Hannah Lindqvist", "due": "2026-06-16T02:29:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Account owner", "holder": "Sarah Chen", "due": "2026-06-16T02:44:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-06-16T04:14:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "VP Sales", "holder": "Michael Torres", "due": "2026-06-16T06:14:00-05:00"},
    {"party": "northstar", "duty": "notify", "role": "Chief Revenue Officer", "holder": "David Morgan", "due": "2026-06-16T06:14:00-05:00"},
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-07-24"},
    {"party": "northstar", "duty": "issue_memo", "role": "Support Billing Manager", "holder": "Paul Brennan", "due": "2026-07-24"},
    {"party": "customer", "duty": "phone_report", "status": "met"},
    {"party": "customer", "duty": "claim", "status": "met"}
  ],
  "evidence": [
    "service_tickets SR-39385: CRM-2048, NS-500, channel phone, opened 2026-06-16T02:14:00-05:00, restored 2026-06-16T10:58:00-05:00, 'Line 4 is stopped. No workaround.'",
    "crm_accounts CRM-2048: DUNS 04-812-7730, tier Strategic, owner Sarah Chen; ERP C-1001 Acme Mfg. Holdings (same DUNS)",
    "ticket_events: engineer_response 2026-06-16T02:31:00-05:00; credit_claim 2026-06-24T10:12:00-05:00 by Edward Floyd (email, names SR-39385)",
    "Schedule C (Acme): Platinum plan; NS-500 covered; coverage from 2025-04-01 00:00 CT; fee $21,000/month from 2026-01",
    "Service Level Schedule v2.0: applies from 2026-04-01; Sev 1 = 30 min / 4 h, 24x7; Sev 1 restoration band 2 = 20%; cap 30% of the month's fee; claim within 30 calendar days of restoration; decision within 30 days of receipt; memo same day by Support Billing Manager",
    "Support Severity Guide: Sev 1 = product failure stopping a production line with no workaround",
    "Support Escalation Procedure: Sev 1 engagement and notification steps at 15 min, 30 min, 50% and 100% of the restoration target; CRO added for Strategic accounts",
    "Support Organization / employees: Lindqvist, Adeyemi, Torres, Morgan, Brennan in their roles",
    "maintenance_notices: none for CRM-2048; service_credits: no June 2026 credits for CRM-2048"
  ],
  "missing_evidence": [
    "No record of the Support Escalation Manager engagement or the account owner, Director, VP Sales and CRO notifications",
    "No recorded claim decision or credit memo for SR-39385 (decision was due by 2026-07-24)"
  ]
}
```

---

## X30 · S44

SR-39690 is a **Severity 2** ticket. Northstar missed its restoration target, but **no credit is owed** because Cedar's claim arrived one day after the claim window closed. What Northstar still owes is a written decision declining the claim, due 2026-09-29. That date has passed, and the record doesn't show whether the decision was sent.

**1. Customer.** CRM account CRM-2063, ERP customer C-1003 (Cedar Health Systems Inc.), DUNS 02-906-4418. I matched the customer on these identifiers, not the name.

**2. Scope: in.** Cedar's Support Terms (SUP-CHS-2025) cover NS-EDGE under the **Silver** plan, at $4,000 a month. Coverage started 2025-12-01, before this ticket. The CRM tier ("Standard") doesn't affect the plan.

**3. True severity: 2.** The customer reported P2, but severity comes from the recorded impact. The gateways stopped forwarding chiller alarms, so an alarming function was unavailable for a building. The severity guide makes that Severity 2 under rule 2(b), "whether or not the customer covers it with manual checks." Here the customer covered it with hourly manual rounds. It isn't Severity 1, because operations did not stop.

**4. Schedule and targets.** Schedule v2.0 applies, since the ticket opened after 2026-04-01. For Severity 2 on Silver, the targets are a first response within 2 business hours and restoration within 12 business hours. Business hours are 08:00–18:00 CT, Monday to Friday. There were no holidays in the period.

**5. Times in Central Time (CDT).** The database stores these with a −04:00 offset.
- **Opened:** Tuesday 2026-07-28 09:30, by portal. This is inside business hours, so the clock starts here.
- **First engineer response:** 11:05 the same day.
- **Restored:** Thursday 2026-07-30 23:50. The stored value says 07-31, but in Central Time it is still 07-30.
- **Pauses and exclusions:** none. No "Awaiting Customer" pause is recorded, and there's no maintenance notice for this account.

**6. Measurement.**
- **Response: met.** 1 h 35 min against a 2-hour target.
- **Restoration: missed, band 2.** Elapsed business hours were 8.5 on Tuesday, 10 on Wednesday and 10 on Thursday, a total of 28.5. That is more than twice the 12-hour target (24 hours).

**7. Credit.** The Severity 2 band-2 rate is 10% of the $4,000 fee, which would be $400. A claim had to arrive within 30 calendar days of the restoration date (2026-07-30), so by **2026-08-29 23:59 CT**. Cedar's claim arrived on 2026-08-30 at 08:12 CDT. A late claim earns no credit, so **$0** is owed.

**8. Obligations.**
- **Claim decision:** Marcus Adeyemi, Director of Customer Support, must decide the claim (decline it as late) and send the written decision. It was due within 30 calendar days of receipt, so by 2026-09-29.
- **Credit memo:** none, because no credit is approved.
- **Root-cause finding:** none. One is only required when Northstar claims the customer caused the incident, and nobody has.
- **Engagements and notifications:** I found no escalation steps for Severity 2 in the escalation procedure; its steps are all for Severity 1. So I can't name any engagement or notification owed for this ticket. Anthony Day, the account owner, has no duty recorded for a Severity 2 ticket.
- **Customer duties:**
  - No phone report was required, because that rule is for Severity 1 only.
  - The claim had to be in writing, name the ticket, and arrive by 2026-08-29. The first two were met, the deadline was not.

**9. Decision: `BREACH_NO_CREDIT`.**

```json
{
  "outcome": "BREACH_NO_CREDIT",
  "ticket": "SR-39690",
  "scope": "in",
  "true_severity": 2,
  "breach": {"response": "met", "restoration": "missed_band2"},
  "credit_usd": 0,
  "obligations": [
    {"party": "northstar", "duty": "decide_claim", "role": "Director of Customer Support", "holder": "Marcus Adeyemi", "due": "2026-09-29T23:59:00-05:00"},
    {"party": "customer", "duty": "claim", "status": "not_met"}
  ],
  "evidence": [
    "service_tickets SR-39690: CRM-2063, NS-EDGE, portal, opened 2026-07-28T10:30:00-04:00 (09:30 CDT), reported P2, restored 2026-07-31T00:50:00-04:00 (2026-07-30 23:50 CDT)",
    "Description: NS-Edge gateways stopped forwarding chiller alarms; engineers doing hourly manual rounds",
    "ticket_events: engineer_response 2026-07-28T12:05:00-04:00 (11:05 CDT); credit_claim by email 2026-08-30T09:12:00-04:00 (08:12 CDT)",
    "crm_accounts CRM-2063 DUNS 02-906-4418 = ERP C-1003 Cedar Health Systems Inc.; account owner Anthony Day; tier Standard",
    "SUP-CHS-2025: Silver plan; covers NS-CLOUD and NS-EDGE; coverage from 2025-12-01 00:00 CT; fee $4,000/month",
    "Support Severity Guide: Severity 2(b), alarming function unavailable whether or not covered by manual checks",
    "Service Level Schedule v2.0: Sev 2 Silver 2 business hours response / 12 business hours restoration; business hours 08:00-18:00 CT Mon-Fri; band 2 (>2x target) Sev 2 credit 10%; claim within 30 calendar days of restoration date by 23:59 CT; late claim earns no credit; Director of Customer Support decides claims within 30 calendar days of receipt",
    "No maintenance notices for CRM-2063; no recorded pauses; no holidays 2026-07-28 to 2026-07-30",
    "Support Organization and Escalation Contacts: Marcus Adeyemi, Director of Customer Support"
  ],
  "missing_evidence": [
    "No Severity 2 engagement or notification steps found in the Support Escalation Procedure",
    "No record of whether the written claim decision was sent by 2026-09-29"
  ]
}
```
