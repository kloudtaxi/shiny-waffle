---
doc_id: SUP-DATA-NOTE-014
title: Northstar Service Timestamp Fields — Recording Conventions
owner: Customer Support
created: '2026-05-11'
effective_from: '2026-04-01'
---

# Northstar Service Timestamp Fields — Recording Conventions

**Audience:** Support Operations, Support Billing, Service Level reporting, and anyone reading
ticket exports or ticket record fields from Northstar Service.

## 1. Why this note exists

Since the Northstar Service integration release of 2026-04-01 (the same date Service Level
Schedule v2.0 took effect), ticket timestamps are no longer written by a single component. Readers
have been measuring elapsed times from exports without checking which component wrote each field.
This note records what each field holds. It does not change the Service Level Schedule; Section 2.1
of each Schedule version still requires every time to be converted to CT before anything is measured.
This note tells you which zone to convert *from*.

## 2. Field conventions (tickets opened on or after 2026-04-01 00:00 CT)

| Field | Written by | Zone as stored |
|---|---|---|
| Opened | Agent desktop / hotline telephony | CT (America/Chicago) |
| Status history entries (including "Awaiting Customer" start and end) | Agent desktop | CT |
| First response | Ticket-comment and telephony integration | **UTC** |
| Restored | Monitoring and remote-diagnostics integration | **UTC** |
| Maintenance notice (MN-nnnn) sent date | Notice mailer | **UTC** |
| Claim received | Credits mailbox / portal | CT |

The integration components write UTC and the zone suffix (Z or +00:00) is dropped by the standard
ticket view and by the summary export, so a UTC value often appears as a bare local-looking time.
A bare "First response" or "Restored" value on a post-2026-04-01 ticket is therefore to be read as
UTC and converted to CT (subtract 5 hours while CDT applies, 6 hours while CST applies) before
elapsed time is measured. "Opened" is already CT and is not converted.

## 3. Worked example

Ticket opened 2026-09-14 09:00 (CT). Restored shows 2026-09-14 15:00 with no zone suffix.
Read "Restored" as 15:00 UTC = 10:00 CDT. Restoration elapsed time is 1 hour, not 6 hours.

## 4. Dates

The same rule governs dates. The CT calendar date of a "Restored" or maintenance-notice "sent"
value is taken after converting from UTC; for values stamped between 00:00 and 05:00 UTC the CT date
is the previous calendar day. The claim window and the 10-business-day root-cause deadline run from
that converted date.

## 5. Tickets opened before 2026-04-01

Fields on these tickets were written by the earlier single component and are stored in CT. No
conversion is needed.

## 6. Questions

Direct questions on field definitions to the Support Engineering Lead.
