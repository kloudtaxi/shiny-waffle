# Northstar Support: SLA situations S36 to S45

Expected outcomes for experiment 6. Every outcome follows from `rule-sheet.md` alone, and the
rules are cited as R1 to R55.

How to read these situations:

- Each situation is decided on the facts listed. If a situation states an "as of" time, decide
  it as of that time. Otherwise decide it after all the listed events.
- Unless a situation says otherwise: Northstar did not assert the customer-caused exclusion
  (R32); no maintenance notice covers the ticket (R29); and the "Other credits" row lists every
  credit already approved for that customer for that month (R38).
- Timestamps are given in the zone in which they were recorded, and each one carries its UTC
  offset. Cedar Health Systems (Indianapolis) and Acme Industrial Supply (Akron) record in
  EDT (UTC−04:00).
- All measurement is in CT (R1). In this period CT is CDT (UTC−05:00), and no situation spans
  a daylight-saving change.
- Weekdays: 2026-03-31 is a Tuesday; 2026-05-22 a Friday; 2026-06-10 a Wednesday; 2026-06-16 a
  Tuesday; 2026-07-11 a Saturday; 2026-07-23 a Thursday; 2026-07-28 a Tuesday; 2026-08-10 a
  Monday; 2026-08-17 a Monday; 2026-08-20 a Thursday.

## Index

| # | Customer on ticket | Product | Main thing it tests | Outcome in one line |
|---|---|---|---|---|
| S36 | ACME Mfg (CRM-2048) | NS-500 | A clear breach that earns a credit | Severity 1. Restoration missed, band 2. Credit $4,200 |
| S37 | Cedar Health (CRM-2063) | NS-Cloud | Target met; Memorial Day on a business-hours clock; EDT conversion | Severity 2. Both targets met. Claim declined |
| S38 | BlueRiver Logistics (CRM-2051) | NS-Cloud | Breach excused by a scheduled maintenance window | Severity 1. Both targets met once the window is excluded. Claim declined |
| S39 | Cedar Health Systems Inc. (CRM-2063) | NS-Cloud | Under-reported severity (P3 is really Severity 1); no phone call | Severity 1. Both targets missed. Credit $320 at Severity 2 rates |
| S40 | Blue River Logistics LLC (CRM-2051) | NS-Cloud | Business-hours clock across a night and a weekend; an automated acknowledgment | Severity 2. Both targets missed (band 1). Credit $200 |
| S41 | Acme Manufacturing (CRM-2048) | NS-Edge | Paused clock; met exactly at the boundary; over-reported P1 | Severity 2. Both targets met. Nothing owed |
| S42 | Acme Mfg. Holdings (CRM-2048) | NS-500 | Older schedule version (v1.0) at the version boundary; v1.0 cap and claim window | Severity 1. Response missed. Credit capped at $630 |
| S43 | Acme Industrial (CRM-2091) | NS-Edge | A similarly named company the SLA does not cover | Out of scope. No targets, no credit. Notify Zachary Brown |
| S44 | Cedar Health Systems (CRM-2063) | NS-Edge | Credit claimed one day late (the restoration date must be converted to CT) | Severity 2. Restoration missed (band 2). No credit: late claim |
| S45 | Acme Manufacturing (CRM-2048) | NS-500 | A needed document is missing (root-cause finding pending) | Severity 1. Restoration breach and remedy: cannot decide, root-cause finding missing |

The situations whose answer depends on careful time arithmetic are S37 (holiday), S40 (night and
weekend, missed by 20 and 40 minutes), S41 (net restoration time exactly equals the target) and
S44 (converting the restoration date to CT moves the claim deadline back one day).

---

## S36: Acme Manufacturing, line stopped, restoration missed by more than 2×

**Ticket facts**

| Field | Value |
|---|---|
| Ticket | SR-39385 |
| Customer as named on ticket | ACME Mfg — Milwaukee Plant 2 (CRM-2048) |
| Product | NS-500 Industrial Controller (NS-500) |
| Channel | Telephone call to the Support hotline from Johnny Johnson, Director of Plant Operations |
| Opened | 2026-06-16 02:14 CDT (UTC−05:00), Tuesday |
| Reported priority | P1 |
| Description | "NS-500 controller on stamping line 4 faulted with a hardware watchdog error at 01:58. Line 4 is stopped. No workaround." |
| First human response | 2026-06-16 02:31 CDT. A Northstar engineer phoned Johnny Johnson. |
| Pauses | None recorded |
| Maintenance notice | None |
| Restored | 2026-06-16 10:58 CDT. The failed controller was replaced with the on-site spare, and line 4 is running at full rate. |
| Credit claim | Email from Edward Floyd to support-credits@northstar.example, received 2026-06-24 10:12 CDT, naming SR-39385 |
| Other credits | None approved for Acme for tickets opened in June 2026 |

**Expected outcome**

- **Scope:** CRM-2048 is Acme Manufacturing (Acme Mfg. Holdings). NS-500 is covered, and
  coverage started 2025-04-01. The ticket is in scope. [R9, R10, R11]
- **True severity: Severity 1.** The line is stopped and there is no workaround. [R13, R14(a), R18]
- **Version and targets:** The ticket was opened after 2026-04-01 00:00 CT, so v2.0 applies.
  Severity 1 targets are a 30-minute response and 4-hour restoration, on the 24×7 clock. The
  clock starts at 02:14 CDT. [R20, R22, R23, R24(a)]
- **Breach:**
  - Initial response: 02:14 to 02:31 is 17 minutes, within 30 minutes. **Met.** [R5, R7]
  - Restoration: 02:14 to 10:58 is 8 h 44 min, more than the 4-hour target. **Missed.** It is
    also more than 8 hours (2× the target), so it falls in **band 2**. [R5, R8, R35]
- **Remedy: $4,200 credit.**
  - Acme reported the incident by phone, so Severity 1 rates apply. [R37, R42]
  - 20% × $21,000 (Acme's June 2026 fee) = $4,200. [R11, R33, R35, R36]
  - The cap is 30% × $21,000 = $6,300, and there are no other June credits, so the full $4,200
    is payable. [R38]
  - The claim is timely (see below). The Director of Customer Support approves it, and the
    Support Billing Manager issues the credit memo against Acme's next support invoice, both
    **no later than 2026-07-24**. [R39, R40, R41]
- **Engage and notify** (24×7 clock from 02:14 CDT): [R45, R46, R47, R52]
  - Hannah Lindqvist (Support Escalation Manager), engaged as incident lead by **02:29 CDT**.
  - Sarah Chen (account owner), notified by **02:44 CDT**.
  - Marcus Adeyemi (Director of Customer Support), notified by **04:14 CDT**: the line was not
    restored when 50% of 4 hours had elapsed.
  - Michael Torres (VP Sales) **and** David Morgan (Chief Revenue Officer, because Acme is a
    Strategic account), notified by **06:14 CDT**: the line was not restored when 4 hours had
    elapsed.
  - Marcus Adeyemi sends the written claim decision, and Paul Brennan (Support Billing Manager)
    issues the credit memo, by **2026-07-24**.
- **Customer obligations:**
  - Report Severity 1 by telephone: **met**. [R42]
  - Claim in writing within 30 days after the restoration date of 2026-06-16, so by
    2026-07-16 23:59 CDT: **met** (received 2026-06-24). [R43]
- **Decision status:** Decidable.

---

## S37: Cedar Health, two facilities off NS-Cloud across Memorial Day, both targets met

**Ticket facts** (Cedar's ticket export records times in EDT)

| Field | Value |
|---|---|
| Ticket | SR-39207 |
| Customer as named on ticket | Cedar Health (CRM-2063) |
| Product | NS-Cloud Operations Suite (NS-CLOUD) |
| Channel | Customer portal |
| Opened | 2026-05-22 16:20 EDT (UTC−04:00), Friday |
| Reported priority | P2 |
| Description | "NS-Cloud is unavailable to all users at our Fishers and Carmel outpatient centers (2 of our 14 facilities) since about 16:00. Facility operations at both centers are continuing. The other 12 facilities are working normally." |
| First human response | 2026-05-22 18:10 EDT. An engineer's ticket comment. |
| Pauses | None recorded |
| Maintenance notice | None |
| Restored | 2026-05-26 18:05 EDT, Tuesday |
| Credit claim | Portal credit claim received 2026-06-01 09:30 EDT: "NS-Cloud was down at two sites for four days." |
| Other credits | None for May 2026 |

**Expected outcome**

- **Scope:** CRM-2063 is Cedar Health Systems. NS-Cloud is covered, and coverage started
  2025-12-01. The ticket is in scope. [R9, R10, R11]
- **True severity: Severity 2.** Operations continue, so R14(a) is not met, and not all users
  are affected, so R14(b) is not met. NS-Cloud is unavailable to some, but not all, sites.
  [R13, R14, R15(c)]
- **Version and targets:** v2.0. Cedar is on the Silver plan, so Severity 2 runs on the
  business-hours clock: 2 business hours to respond and 12 business hours to restore.
  [R11, R20, R22, R23]
- **Convert to CT:** opened 15:20 CDT; first response 17:10 CDT; restored 2026-05-26 17:05 CDT.
  [R1]
- **Clock start:** 15:20 CDT on Friday, which is inside business hours. [R24(b)]
- **Breach:**
  - Initial response: the 2-business-hour target elapses at 17:20 CDT on Friday. The response
    came at 17:10 CDT, after 1 h 50 min. **Met.** [R5]
  - Restoration: count the business hours.
    - Friday 15:20 to 18:00: 2 h 40 min.
    - Saturday and Sunday: none.
    - Monday 2026-05-25: none, because it is Memorial Day, a Northstar holiday. [R2, R3]
    - Tuesday from 08:00: the remaining 9 h 20 min, so the target elapses at
      **2026-05-26 17:20 CDT**.
    - The ticket was restored at 17:05 CDT, after 11 h 45 min of business hours. **Met.** [R4, R5]
    - If Memorial Day were counted as a business day, the target would wrongly fall on Monday
      at 17:20 and the ticket would look like a breach.
- **Remedy: none.** No target was missed. The claim is declined, and Marcus Adeyemi (Director of
  Customer Support) must send the written decision **no later than 2026-07-01**. [R36, R39, R41]
- **Engage and notify:** No SLA escalation is required, because both Severity 2 targets were met
  (R48). The only duty is the claim decision: Marcus Adeyemi, by 2026-07-01. [R48, R52]
- **Customer obligations:** No telephone duty, because the ticket is not Severity 1. The claim
  was timely (the window ran to 2026-06-25), but nothing is owed. [R42, R43]
- **Decision status:** Decidable.

---

## S38: BlueRiver, NS-Cloud outage inside a scheduled maintenance window, excused

**Ticket facts**

| Field | Value |
|---|---|
| Ticket | SR-39561 |
| Customer as named on ticket | BlueRiver Logistics (CRM-2051) |
| Product | NS-Cloud Operations Suite (NS-CLOUD) |
| Channel | Telephone call to the Support hotline from BlueRiver's night dispatch supervisor |
| Opened | 2026-07-11 23:20 CDT (UTC−05:00), Saturday |
| Reported priority | P1 |
| Description | "NS-Cloud has been down for all our users since about 23:10. Dispatch can't see any shipments. No workaround." |
| First human response | 2026-07-11 23:35 CDT. An engineer phoned the supervisor. |
| Maintenance notice | MN-2607, sent 2026-06-26 11:00 CDT to BlueRiver's designated support contacts: "NS-Cloud platform upgrade. Window: 2026-07-11 22:00 CDT to 2026-07-12 02:00 CDT. Products affected: NS-Cloud." |
| Engineer note | The outage was caused by the upgrade performed in window MN-2607. |
| Pauses | None recorded |
| Restored | 2026-07-12 05:05 CDT, Sunday |
| Credit claim | Email received 2026-07-14 08:45 CDT: "Claiming the Severity 1 restoration credit for a 5 h 45 min outage on SR-39561." |
| Other credits | None for July 2026 |

**Expected outcome**

- **Scope:** CRM-2051 is BlueRiver Logistics. NS-Cloud is covered. The ticket is in scope.
  [R9, R11]
- **True severity: Severity 1.** NS-Cloud is unavailable to all users, with no workaround.
  [R13, R14(b)]
- **Version and targets:** v2.0. Severity 1: 30 minutes to respond, 4 hours to restore, on the
  24×7 clock. [R20, R22, R23]
- **Maintenance exclusion:** Count the business days after 2026-06-26, up to and including
  2026-07-11: Jun 29, Jun 30, Jul 1, Jul 2, Jul 6, Jul 7, Jul 8, Jul 9, Jul 10. That is 9.
  Jul 3 is a holiday and Jul 11 is a Saturday, so neither counts. Nine is at least the 5 that
  v2.0 requires, so the window **qualifies**. [R3, R29]
- **Clock start:** The ticket was opened inside the window, so both clocks start at the window's
  end, **2026-07-12 02:00 CDT**. [R30(a)]
- **Breach:**
  - Initial response: given at 23:35 CDT, before the clock started, so it counts as elapsed
    time zero. **Met.** [R25]
  - Restoration: 02:00 to 05:05 is 3 h 05 min, within 4 hours. **Met.** [R5, R30(c)]
  - Measured from the open time, the restoration would be 5 h 45 min and would look like a
    band-1 breach. The time inside the window is excluded, even though the maintenance caused
    the outage. [R30]
- **Remedy: none.** The claim is declined. Marcus Adeyemi must send the written decision **no
  later than 2026-08-13**. [R39, R41]
- **Engage and notify** (24×7 clock from the delayed start at 02:00 CDT): [R46(b), R47]
  - Hannah Lindqvist (Support Escalation Manager), engaged by **2026-07-12 02:15 CDT**.
  - Kelly Floyd (account owner), notified by **02:30 CDT**.
  - Marcus Adeyemi (Director of Customer Support), notified by **04:00 CDT**: the service was not
    restored when 50% of 4 hours had elapsed.
  - VP Sales: **not required**, because the service was restored at 05:05, before the 4-hour mark
    at 06:00. Chief Revenue Officer: not required in any case, because BlueRiver is a Standard
    account.
  - Claim decision: Marcus Adeyemi, by 2026-08-13. [R52]
- **Customer obligations:** Report Severity 1 by telephone: **met**. The claim was timely, but
  nothing is owed. [R42, R43]
- **Decision status:** Decidable.

---

## S39: Cedar Health reports "P3" for a total NS-Cloud outage, through the portal

**Ticket facts** (Cedar's ticket export records times in EDT)

| Field | Value |
|---|---|
| Ticket | SR-39340 |
| Customer as named on ticket | Cedar Health Systems Inc. (CRM-2063) |
| Product | NS-Cloud Operations Suite (NS-CLOUD) |
| Channel | Customer portal. Cedar never telephoned the Support hotline about this incident. |
| Opened | 2026-06-10 07:05 EDT (UTC−04:00), Wednesday |
| Reported priority | P3 |
| Description | "NS-Cloud won't load for anyone. None of our 14 facilities can see equipment status or alarms since about 06:15. Please look at it today." |
| First human response | 2026-06-10 09:20 EDT. A Northstar engineer phoned Cedar, confirmed that all users were affected and that no workaround existed, and reclassified the ticket as Severity 1. |
| Pauses | None recorded |
| Maintenance notice | None |
| Restored | 2026-06-10 12:35 EDT |
| Credit claim | Email received 2026-06-29 11:00 EDT, naming SR-39340 |
| Other credits | None for June 2026 |

**Expected outcome**

- **Scope:** In scope, as Cedar with NS-Cloud covered. [R9, R11]
- **True severity: Severity 1** (reported P3). NS-Cloud was unavailable to all users with no
  workaround. The reported priority does not govern. Because the impact was recorded at
  opening, Severity 1 applies from the open time. [R14(b), R18, R19(a)]
- **Version and targets:** v2.0. Severity 1: 30 minutes to respond, 4 hours to restore, on the
  **24×7** clock, not the business-hours clock a Severity 3 would use. [R20, R22, R23]
- **Convert to CT:** opened 06:05 CDT; first response 08:20 CDT; restored 11:35 CDT. The clock
  starts at the open time, **06:05 CDT**. It does not start at the incident start of
  06:15 EDT. [R1, R6, R24(a)]
- **Breach:**
  - Initial response: 06:05 to 08:20 is 2 h 15 min, more than 30 minutes. **Missed.** [R5, R7]
  - Restoration: 06:05 to 11:35 is 5 h 30 min. That is more than 4 hours but no more than
    8 hours, so **missed, band 1**. [R5, R35]
- **Remedy: $320 credit.**
  - Cedar did not report the incident by telephone. Northstar's call to Cedar does not count.
    The credits therefore use the **Severity 2 percentages**, while the band is still measured
    against the Severity 1 targets. [R37, R42]
  - 3% (response) + 5% (restoration, band 1) = 8% × $4,000 = **$320**. [R11, R33, R35, R36]
  - The cap is 30% × $4,000 = $1,200, so the full $320 is payable. [R38]
  - The claim is timely. The credit is approved, and the credit memo is due **no later than
    2026-07-29**. [R41]
  - At Severity 1 rates the credit would have been $600. Under the reported P3 it would have
    been $0.
- **Engage and notify** (Severity 1 escalation, 24×7 clock from 06:05 CDT): [R46(a), R46(b), R47]
  - Hannah Lindqvist (Support Escalation Manager), engaged by **06:20 CDT**.
  - Anthony Day (account owner), notified by **06:35 CDT**.
  - Marcus Adeyemi (Director of Customer Support), notified by **08:05 CDT**: the service was not
    restored when 2 hours had elapsed.
  - Michael Torres (VP Sales), notified by **10:05 CDT**: the service was not restored when
    4 hours had elapsed.
  - Chief Revenue Officer: **not required**, because Cedar is a Standard account.
  - The telephone rule does not change escalation. [R46(b)]
  - Marcus Adeyemi sends the claim decision, and Paul Brennan issues the memo, by 2026-07-29. [R52]
- **Customer obligations:**
  - Report Severity 1 by telephone: **not met**. The consequence is the Severity 2 credit rates
    (R37). [R42]
  - Claim within 30 days after 2026-06-10, so by 2026-07-10: **met**. [R43]
- **Decision status:** Decidable.

---

## S40: BlueRiver, a Silver Severity 2 opened at night, clock across the weekend

**Ticket facts**

| Field | Value |
|---|---|
| Ticket | SR-39881 |
| Customer as named on ticket | Blue River Logistics LLC (CRM-2051) |
| Product | NS-Cloud Operations Suite (NS-CLOUD) |
| Channel | Customer portal, submitted by BlueRiver's operations manager |
| Opened | 2026-08-20 19:45 CDT (UTC−05:00), Thursday |
| Reported priority | P2 |
| Description | "Since about 19:00, NS-Cloud shipment-exception alerts and route dashboards have stopped updating for our St. Louis and Memphis depots (2 of our 6). Dispatchers are phoning drivers to track exceptions. The other depots are fine." |
| Automated acknowledgment | Ticket-creation email sent automatically 2026-08-20 19:46 CDT |
| First human response | 2026-08-21 10:20 CDT, Friday. No Northstar engineer contacted BlueRiver before this. |
| Pauses | None recorded |
| Maintenance notice | None |
| Restored | 2026-08-24 10:40 CDT, Monday |
| Credit claim | Email received 2026-08-28 14:05 CDT, naming SR-39881 |
| Other credits | None for August 2026 |

**Expected outcome**

- **Scope:** In scope, as BlueRiver with NS-Cloud covered. [R9, R11]
- **True severity: Severity 2.** An alerting function is unavailable for 2 of 6 sites, and
  operations continue with manual effort. [R13, R15(b), R15(c)]
- **Version and targets:** v2.0. BlueRiver is on the Silver plan, so Severity 2 runs on the
  business-hours clock: 2 business hours to respond and 12 business hours to restore.
  [R11, R20, R22, R23]
- **Clock start:** The ticket was opened at 19:45 CDT, after business hours, so the clock starts
  at **Friday 2026-08-21 08:00 CDT**. [R2, R24(b)]
- **Breach:**
  - Initial response: the automated acknowledgment at 19:46 does not count. [R7] The target
    elapses at Friday 10:00 CDT. The first human response came at 10:20 CDT, after 2 h 20 min of
    business hours. **Missed.** [R5]
  - Restoration: count the business hours.
    - Friday 08:00 to 18:00: 10 h.
    - Saturday and Sunday: none.
    - Monday from 08:00: the remaining 2 h, so the target elapses at **Monday 2026-08-24 10:00
      CDT**.
    - The ticket was restored at 10:40 CDT, after 12 h 40 min of business hours. **Missed.** That
      is no more than 24 business hours (2× the target), so it is **band 1**. [R4, R5, R35]
    - Measured on the wall clock (86 h 55 min), it would look like band 2. That is wrong for a
      Silver Severity 2.
- **Remedy: $200 credit.**
  - 3% (response) + 5% (restoration, band 1) = 8% × $2,500 = **$200**. [R11, R33, R35, R36]
  - The cap is 30% × $2,500 = $750, so the full $200 is payable. [R38]
  - The claim is timely. The credit memo is due **no later than 2026-09-27**. [R41]
- **Engage and notify:** [R46(b), R48, R52]
  - Hannah Lindqvist (Support Escalation Manager), notified by **2026-08-21 10:00 CDT**, because
    there had been no initial response when the response target elapsed. [R48(a)]
  - Marcus Adeyemi (Director of Customer Support) **and** Kelly Floyd (account owner), notified
    by **2026-08-24 10:00 CDT**, because the ticket was not restored when the restoration target
    elapsed. [R48(b)]
  - Marcus Adeyemi sends the claim decision, and Paul Brennan issues the memo, by 2026-09-27.
- **Customer obligations:** No telephone duty, because the ticket is not Severity 1. Claim within
  30 days after 2026-08-24, so by 2026-09-23: **met**. [R43]
- **Decision status:** Decidable.

---

## S41: Acme, NS-Edge monitoring loss reported as "P1", paused for remote access

**Ticket facts**

| Field | Value |
|---|---|
| Ticket | SR-39644 |
| Customer as named on ticket | Acme Manufacturing (CRM-2048) |
| Product | NS-Edge Monitoring Package (NS-EDGE) |
| Channel | Customer portal, submitted by Johnny Johnson |
| Opened | 2026-07-23 13:10 CDT (UTC−05:00), Thursday |
| Reported priority | P1 |
| Description | "NS-Edge gateways on Plant 2 stopped sending vibration data for presses 1–6 (of 14) at about 12:50. The presses are still running. Maintenance techs are doing manual vibration checks on presses 1–6 every two hours." |
| First human response | 2026-07-23 15:00 CDT. An engineer's ticket comment asking Acme for VPN credentials to reach the Plant 2 gateways remotely. |
| Status history | 2026-07-23 15:00 CDT: status set to **Awaiting Customer** with the request above. 2026-07-24 08:30 CDT: Kelly Ballard (Acme IT Architecture) provided the credentials, recorded in the ticket, and the status went back to In Progress. |
| Maintenance notice | None |
| Restored | 2026-07-24 18:40 CDT, Friday |
| Credit claim | None |

**Expected outcome**

- **Scope:** NS-Edge is a covered product for Acme. The ticket is in scope. [R9, R11]
- **True severity: Severity 2** (reported P1). A condition-monitoring function is unavailable
  for some machines, and production continues. The reported P1 does not govern, so there are
  no Severity 1 targets or Severity 1 escalation. [R13, R15(b), R18, R19(a)]
- **Version and targets:** v2.0. Acme is on the Platinum plan, so Severity 2 runs on the
  **24×7** clock: 2 hours to respond and 12 hours to restore. The clock starts at 13:10 CDT.
  [R11, R20, R22, R23, R24(a)]
- **Breach:**
  - Initial response: the access request at 15:00 counts as the response. 13:10 to 15:00 is
    1 h 50 min, within 2 hours. **Met.** [R5, R7]
  - Pause: Awaiting Customer from 2026-07-23 15:00 to 2026-07-24 08:30 CDT, which is
    17 h 30 min. Both ends are recorded, so the pause counts. [R26(a), R26(c)]
  - Restoration: on the wall clock, 2026-07-23 13:10 to 2026-07-24 18:40 is 29 h 30 min.
    Subtracting the 17 h 30 min pause leaves **12 h 00 min**, which equals the target exactly.
    **Met.** [R4, R5]
  - Without the pause, the restoration would be a band-2 miss.
- **Remedy: none.** No target was missed, and no claim was made. [R36, R39]
- **Engage and notify:** **None required.** The response came before the response target
  elapsed, and the restoration came at the moment the target elapsed, so neither R48(a) nor
  R48(b) is triggered. The ticket is not Severity 1, so R47 does not apply despite the P1
  report. [R46(a), R47, R48]
- **Customer obligations:**
  - Telephone duty: not applicable, because the true severity is 2. [R42]
  - Provide access: Acme provided it. The time Northstar waited is accounted for by the pause.
    [R44, R26]
  - No claim was made, and none would succeed.
- **Decision status:** Decidable.

---

## S42: Acme, Severity 1 opened the night before v2.0 took effect

**Ticket facts**

| Field | Value |
|---|---|
| Ticket | SR-38862 |
| Customer as named on ticket | Acme Mfg. Holdings (CRM-2048) |
| Product | NS-500 Industrial Controller (NS-500) |
| Channel | Telephone call to the Support hotline from Acme's Plant 1 shift supervisor |
| Opened | 2026-03-31 22:50 CDT (UTC−05:00), Tuesday. The system log shows 2026-04-01T03:50Z. |
| Reported priority | P1 |
| Description | "NS-500 controller on the Plant 1 paint line is rebooting in a loop. The paint line is stopped. No workaround." |
| First human response | 2026-03-31 23:58 CDT. An engineer phoned the shift supervisor. |
| Pauses | None recorded |
| Maintenance notice | None |
| Restored | 2026-04-01 05:35 CDT. A firmware rollback was applied and the paint line is running. |
| Credit claim | Email from Edward Floyd received 2026-05-12 09:00 CDT, naming SR-38862 |
| Other credits | Already approved for Acme for tickets opened in March 2026: SR-38655 (opened 2026-03-04), $3,150, approved 2026-04-02; and SR-38790 (opened 2026-03-19), $420, approved 2026-04-20. Total $3,570. |

**Expected outcome**

- **Scope:** In scope. [R9, R11]
- **True severity: Severity 1.** The line is stopped and there is no workaround. [R14(a)]
- **Version: v1.0.** The open time in CT, 2026-03-31 22:50, is before 2026-04-01 00:00 CT.
  Neither the UTC log date (April 1), the restoration date (April 1) nor the claim date (May)
  changes the version. [R1, R20]
- **Targets (v1.0):** Severity 1: 1 hour to respond, 8 hours to restore, on the 24×7 clock. The
  clock starts at 22:50 CDT. [R21, R23, R24(a)]
- **Breach:**
  - Initial response: 22:50 to 23:58 is 1 h 08 min, more than 1 hour. **Missed.** [R5]
  - Restoration: 22:50 to 05:35 is 6 h 45 min, within 8 hours. **Met.** Under v2.0's 4 hours it
    would have been missed, but v2.0 does not apply. [R5, R21]
- **Remedy: $630 credit, after the v1.0 cap.**
  - Acme reported by phone, so Severity 1 rates apply. Under v1.0, a missed Severity 1 response
    earns 5% × $21,000 (Acme's March 2026 fee) = $1,050. [R11, R33, R34, R37]
  - The v1.0 monthly cap is 20% × $21,000 = $4,200. $3,570 was already approved for March
    tickets, leaving $630. The credit is reduced to **$630**, and the other $420 is forfeited.
    [R38]
  - The credit memo is due **no later than 2026-06-11**. [R41]
  - A v2.0 reading would wrongly find both targets missed (5% + 10% = $3,150) and apply a
    30% cap ($6,300 − $3,570 = $2,730 remaining), giving $2,730.
- **Engage and notify** (24×7 clock from 22:50 CDT, with v1.0 thresholds): [R46(e), R47]
  - Hannah Lindqvist (Support Escalation Manager), engaged by **2026-03-31 23:05 CDT**.
  - Sarah Chen (account owner), notified by **2026-03-31 23:20 CDT**.
  - Marcus Adeyemi (Director of Customer Support), notified by **2026-04-01 02:50 CDT**: the line
    was not restored when 50% of 8 hours (4 hours) had elapsed.
  - VP Sales and Chief Revenue Officer: **not required**, because the line was restored at 05:35,
    before the 8-hour mark at 06:50. A v2.0 reading would wrongly require them by 02:50.
  - Marcus Adeyemi sends the claim decision, and Paul Brennan issues the memo, by 2026-06-11. [R52]
- **Customer obligations:**
  - Report Severity 1 by telephone: **met**. [R42]
  - Claim within the v1.0 window of 60 days after 2026-04-01, so by 2026-05-31 23:59 CDT:
    **met** (received 2026-05-12). Under v2.0's 30 days it would have been late, but v1.0
    governs. [R43]
- **Decision status:** Decidable.

---

## S43: "Acme Industrial" asks for the Acme Platinum SLA

**Ticket facts** (the Akron site records times in EDT)

| Field | Value |
|---|---|
| Ticket | SR-39802 |
| Customer as named on ticket | Acme Industrial (CRM-2091). Site: Akron, OH. |
| Product | NS-Edge Monitoring Package (NS-EDGE) |
| Channel | Telephone call to the Support hotline from Amy Barrett |
| Opened | 2026-08-10 06:05 EDT (UTC−04:00), Monday |
| Reported priority | P1 |
| Description | "All NS-Edge gateways at the Akron distribution center have been offline since about 05:30. Conveyor monitoring is dark and picking has halted. No workaround. We're Acme. We have the Acme Platinum support plan." |
| First human response | 2026-08-10 07:40 EDT |
| Restored | 2026-08-10 14:20 EDT |
| Credit claim | Email from Amy Barrett received 2026-08-14 10:00 EDT: "Please apply the Severity 1 restoration credit under Acme's Platinum plan for SR-39802." |

**Expected outcome**

- **Scope: out of scope.** CRM-2091 is Acme Industrial Supply Co. (ERP C-1044, Akron, OH). That
  is a different company from Acme Mfg. Holdings (CRM-2048), and it has no support agreement.
  Acme Manufacturing's Platinum plan does not extend to it, whatever the caller says.
  [R9(a), R10, R11, R12]
- **True severity: Severity 1** by business impact (operations halted, no workaround). This is
  for internal priority only. [R12(a), R14(a)]
- **Breach: not applicable.** No response or restoration target applies. [R12(b)]
- **Remedy: none.** The claim is declined. Marcus Adeyemi (Director of Customer Support) must
  send the written decision **no later than 2026-09-13**. [R12(b), R12(e), R41]
- **Engage and notify:**
  - **Zachary Brown**, the account owner of CRM-2091, must be notified **no later than
    2026-08-10 18:00 CDT** (19:00 EDT). The ticket opened at 05:05 CDT, before business hours,
    so the business-hours clock starts at 08:00 CDT, and 08:00 plus 10 business hours is
    18:00 CDT. [R12(d), R24(b), R50]
  - **No** Support Escalation Manager, Director, VP Sales or Chief Revenue Officer escalation is
    required, because the SLA escalations do not apply. Sarah Chen (Acme Manufacturing's owner)
    has no duty here. [R12(c)]
  - Claim decision: Marcus Adeyemi, by 2026-09-13. [R52]
- **Customer obligations:** None arise under the SLA, because there is no agreement. [R12]
- **Decision status:** Decidable.

---

## S44: Cedar Health, restoration missed, credit claimed one day late

**Ticket facts** (Cedar's ticket export records times in EDT)

| Field | Value |
|---|---|
| Ticket | SR-39690 |
| Customer as named on ticket | Cedar Health Systems (CRM-2063) |
| Product | NS-Edge Monitoring Package (NS-EDGE) |
| Channel | Customer portal |
| Opened | 2026-07-28 10:30 EDT (UTC−04:00), Tuesday |
| Reported priority | P2 |
| Description | "NS-Edge gateways in our central energy plant stopped forwarding chiller alarms at about 10:10. Our engineers are doing hourly manual rounds." |
| First human response | 2026-07-28 12:05 EDT. An engineer's ticket comment. |
| Pauses | None recorded |
| Maintenance notice | None |
| Restored | 2026-07-31 00:50 EDT |
| Credit claim | Email to support-credits@northstar.example received 2026-08-30 09:12 EDT, naming SR-39690 |
| Other credits | None for July 2026 |

**Expected outcome**

- **Scope:** In scope, as Cedar with NS-Edge covered. [R9, R11]
- **True severity: Severity 2.** An alarming function is unavailable for a building, covered by
  manual rounds. [R13, R15(b)]
- **Version and targets:** v2.0. Cedar is on the Silver plan, so Severity 2 runs on the
  business-hours clock: 2 business hours to respond and 12 business hours to restore.
  [R20, R22, R23]
- **Convert to CT:** opened 2026-07-28 09:30 CDT; first response 11:05 CDT; restored
  **2026-07-30 23:50 CDT**; claim received **2026-08-30 08:12 CDT**. [R1]
- **Breach:**
  - Initial response: 09:30 to 11:05 is 1 h 35 min of business hours. **Met.**
  - Restoration: count the business hours.
    - Tuesday 09:30 to 18:00: 8 h 30 min.
    - Wednesday from 08:00: the remaining 3 h 30 min, so the target elapses at
      **2026-07-29 11:30 CDT**.
    - The ticket was restored on Thursday at 23:50 CDT, after business hours. Elapsed business
      hours are 8 h 30 min + 10 h (Wednesday) + 10 h (Thursday) = 28 h 30 min. **Missed.** That
      is more than 24 business hours (2× the target), so it is **band 2**. [R4, R5, R35]
- **Remedy: none, because the claim was late.**
  - The credit would have been 10% × $4,000 = $400. [R35]
  - The restoration date in CT is **2026-07-30**, so the 30-day window ends 2026-08-29 23:59 CDT.
    That day is a Saturday, and weekends do not extend the window.
  - The claim was received 2026-08-30, one day late, so no credit is owed. [R39, R43]
  - Reading the restoration date in EDT (July 31) would wrongly put the deadline on August 30
    and make the claim look timely.
  - Marcus Adeyemi must send the written decline **no later than 2026-09-29**. [R41]
- **Engage and notify:** [R46(b), R48(b), R52]
  - Marcus Adeyemi (Director of Customer Support) **and** Anthony Day (account owner), notified
    by **2026-07-29 11:30 CDT**, because the ticket was not restored when the restoration target
    elapsed.
  - Support Escalation Manager: not required, because the response was met.
  - Claim decision: Marcus Adeyemi, by 2026-09-29.
- **Customer obligations:** Claim within 30 days after the restoration date: **not met**
  (received one day late). No telephone duty, because the ticket is not Severity 1. [R42, R43]
- **Decision status:** Decidable.

---

## S45: Acme, Severity 1 restoration over target, customer-caused exclusion pending

**Ticket facts.** Decide **as of 2026-08-24 17:00 CDT**.

| Field | Value |
|---|---|
| Ticket | SR-39857 |
| Customer as named on ticket | Acme Manufacturing (CRM-2048) |
| Product | NS-500 Industrial Controller (NS-500) |
| Channel | Telephone call to the Support hotline from Kelly Ballard (Acme IT Architecture) |
| Opened | 2026-08-17 09:20 CDT (UTC−05:00), Monday |
| Reported priority | P1 |
| Description | "NS-500 controllers on Plant 1 assembly line 2 lost communication with the line HMI at about 09:05. Line 2 is stopped. No workaround." |
| First human response | 2026-08-17 09:38 CDT. An engineer phoned Kelly Ballard. |
| Pauses | None recorded |
| Maintenance notice | None |
| Restored | 2026-08-17 15:05 CDT. Communication was restored and line 2 is running. |
| Engineer note, 2026-08-17 15:30 CDT | "Comms came back after Acme reverted a VLAN change their network contractor made on 2026-08-16. Suspect customer-caused. Asserting the customer-caused exclusion; root-cause finding to follow from Support Engineering." |
| Root-cause finding | **None recorded** as of 2026-08-24 17:00 CDT |
| Credit claim | Email from Edward Floyd received 2026-08-20 08:40 CDT, naming SR-39857 |
| Other credits | None for August 2026 |

**Expected outcome**

- **Scope:** In scope. [R9, R11]
- **True severity: Severity 1.** The line is stopped and there is no workaround. [R14(a)]
- **Version and targets:** v2.0. Severity 1: 30 minutes to respond, 4 hours to restore, on the
  24×7 clock. The clock starts at 09:20 CDT. [R20, R22, R23, R24(a)]
- **Breach:**
  - Initial response: 09:20 to 09:38 is 18 minutes. **Met**, so no response credit is owed in
    any case. [R5, R31]
  - Restoration: **cannot decide: missing the root-cause finding.** The elapsed time, 09:20 to
    15:05, is 5 h 45 min, which is more than 4 hours. But Northstar has asserted the
    customer-caused exclusion, and no root-cause finding has been recorded. The finding's
    deadline has not passed: it is 18:00 CDT on the 10th business day after 2026-08-17, which
    is **2026-08-31 18:00 CDT** (Aug 18, 19, 20, 21, 24, 25, 26, 27, 28, 31). Until the finding
    is recorded, it cannot be decided whether the restoration target applies. The engineer's
    suspicion is not a finding. [R31, R32(c), R54]
- **Remedy: cannot decide: missing the root-cause finding (SR-39857).**
  - If the finding attributes the incident to Acme (R31(i)): no credit.
  - If it attributes it otherwise, or no finding is recorded by 2026-08-31 18:00 CDT: the
    restoration is a band-1 miss, and the credit is 10% × $21,000 = **$2,100** at Severity 1
    rates (Acme phoned). The credit memo is due by 2026-09-19.
  - [R32(a), R32(b), R33, R35, R37, R41]
- **Engage and notify:** These are decidable, because the exclusion does not affect escalation
  (R46(b)). Times are on the 24×7 clock from 09:20 CDT. [R45, R46, R47, R51, R52]
  - Hannah Lindqvist (Support Escalation Manager), engaged by **09:35 CDT**.
  - Sarah Chen (account owner), notified by **09:50 CDT**.
  - Marcus Adeyemi (Director of Customer Support), notified by **11:20 CDT**.
  - Michael Torres (VP Sales) **and** David Morgan (Chief Revenue Officer, because Acme is a
    Strategic account), notified by **13:20 CDT**: the line was not restored at the 4-hour mark.
  - **Owen Takahashi (Support Engineering Lead)** must record the root-cause finding **no later
    than 2026-08-31 18:00 CDT**.
  - Marcus Adeyemi must send the written claim decision **no later than 2026-09-19**. If the
    credit is approved, Paul Brennan issues the memo by the same date.
- **Customer obligations:**
  - Report Severity 1 by telephone: **met**. [R42]
  - Claim within 30 days after 2026-08-17, so by 2026-09-16: **met** (received 2026-08-20).
    [R43]
- **Decision status:** Partly decidable. Restoration breach and remedy: **cannot decide: missing
  the root-cause finding** (R32(c), R54). Everything else is decided above.
