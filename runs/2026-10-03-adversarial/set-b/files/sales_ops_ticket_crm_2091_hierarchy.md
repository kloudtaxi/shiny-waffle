---
doc_id: DS-2026-0418
title: CRM Data Stewardship DS-2026-0418 — Acme account hierarchy
owner: Sales Operations
created: '2026-08-27'
---

# CRM Data Stewardship Request DS-2026-0418

| Field | Value |
|---|---|
| Accounts | Acme Industrial Supply Co. (CRM-2091) · Acme Manufacturing (CRM-2048) |
| ERP bill-to | C-1044 · C-1001 |
| Request type | Account hierarchy / parent link |
| Requested by | Sarah Chen |
| Assigned to | Bryan Rivera |
| Opened | 2026-08-24 |
| Closed | 2026-08-27 |
| Status | Resolved |

## Request

Acme Industrial Supply in Akron is part of the Acme group and buys under the Acme master
agreement, but the two accounts aren't linked in CRM, so Akron quotes don't pick up the agreement
pricing. Please set CRM-2048 as the parent of CRM-2091.

## Findings

- D&B lookup: Acme Industrial Supply Co., site DUNS 09-552-1187. Global ultimate DUNS
  04-812-7730 (Acme Mfg. Holdings, Milwaukee, WI).
- Legal confirmed that Acme Industrial Supply Co. is a wholly owned subsidiary of Acme Mfg.
  Holdings (acquired 2024) and an Affiliate as defined in ACME-MFG-2025, Section 5. Affiliates may
  order under the agreement at the agreement's pricing, including Schedule B.

## Resolution

- CRM-2091 parent set to CRM-2048. The hierarchy shows in CRM exports after the next
  account-master refresh.
- NS-500 opportunities for the Akron site are owned by Sarah Chen as the Strategic account owner.
  Zachary Brown keeps service and renewal activity on CRM-2091.
- ERP bill-to C-1044 is unchanged. Akron continues to be invoiced separately.

Closed by: Bryan Rivera, Sales Operations Analyst
