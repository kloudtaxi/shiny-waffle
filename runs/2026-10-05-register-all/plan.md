# One register for all three decision types (G-30): pre-registration, 2026-10-05

The user approved G-30 on 2026-10-05: register the discount and SLA governing documents, as credit's
already are (`runs/2026-10-05-register`). G-01 is decided as well: the register lives in the OWM;
the owning function registers each document and a second person approves it; documents carry
structured terms; and `on_mismatch` is configurable, with **proceeding on the approved version as
the default**. This file is committed before any G-30 code.

## The design

**One register per company** (corpus), covering every governing document any decision type
reads. That is 17 documents in the base company:

| Decision type | Kind (global name) | Documents | Owner |
|---|---|---|---|
| Credit | `credit_policy`, `guarantee` | CREDIT-POLICY-2025, -2026; GRT-ACME-2026 | Finance; Legal |
| Discount | `pricing_policy` | PRICING-POLICY-2025, -2026, -2027 | Revenue Operations |
| Discount | `agreement` | ACME-MFG-2025 | Legal |
| Discount | `exception` | EXC-ACME-NS500-15, EXC-ACME-NS500-10 | Deal Desk |
| SLA | `sla_schedule` | SLA-SCHEDULE-1.0, -2.0 | Customer Support |
| SLA | `support_terms` | SUP-ACME-C, SUP-BRL-2025, SUP-CHS-2025 | Legal |
| SLA | `severity_guide`, `escalation_procedure` | SUP-SEVERITY-GUIDE, SOP-SUPPORT-007 | Customer Support |
| SLA | `holiday_calendar` | HR-HOLIDAYS-2025-26 | People Operations |

A company registers what it has:
- the missing-contract company has no agreement and no exceptions;
- the missing-guarantee company has no guarantee.

**Kind names are global.** Credit's "policy" and discount's "policy" are different things. A spec
maps its own kinds onto the register's, for example
`registered_kinds: {policy: pricing_policy, agreement: agreement, exception: exception}`. A list
still means the same names. Credit's register kind becomes `credit_policy`, so `credit_v3.yaml`
and the credit harness change accordingly, and **every committed credit result must still
reproduce**.

**Explicit relations (G-02):**
- each pricing policy supersedes its predecessor;
- EXC-ACME-NS500-15 supersedes EXC-ACME-NS500-10, and is `under` ACME-MFG-2025;
- SLA-SCHEDULE-2.0 supersedes 1.0;
- SUP-ACME-C is `under` ACME-MFG-2025 (its Schedule C);
- credit as before.

**Structured terms, from truth.** The registrar transcribes them correctly, and checks key values
against the text:

| Kind | Terms |
|---|---|
| Pricing policy | Bands (HR title, lower, upper), and the evidence threshold |
| Agreement | Customer by registered ids (CRM account, ERP customer, DUNS), products by SKU, window |
| Exception | Customer ids, product SKU, maximum discount, window |
| SLA schedule | Targets, credits, cap, claim period, notice days |
| Support terms | Customer ids, plan, products, coverage start |
| Holiday calendar | The holidays |
| Severity guide, escalation procedure | **No structured terms yet** (prose only). Their approved text is registered and fingerprinted |

**The store:** every approved text goes into the content-addressed store. Under the default,
prose-reading specs read approved versions, so they need no new code.

## Engines

| Engine | What it is |
|---|---|
| discount | `specs/discount.yaml`, frozen (experiment 4's v3, as data) |
| **discount+Ru** | The same, plus one declaration (the `registered_kinds` mapping), under the default (proceed on the approved version) |
| **discount+R** | The same with `on_mismatch: route` |
| sla | `specs/sla.yaml`, frozen |
| **sla+Ru / sla+R** | As for discount |
| credit (all) | The register harness's nine engines plus v2+Ru, re-pointed to the shared register |

## Checks

| # | Check | Expected |
|---|---|---|
| K1 | Existing specs unchanged (`check_equivalence.py`, `check_behaviour.py`, the SLA replay) | identical |
| K2 | The registrar: key values appear in each document; the rebuild is identical; the store matches | ✓ |
| K3 | discount+Ru and +R on experiment 4's clean 18 scenarios; sla+Ru and +R on S36–S45 | **identical** to the frozen specs (every decision field) |
| K4 | Credit on the shared register: sets C, D and E re-run, every engine's committed rows | **reproduce exactly** |
| K5 | CRLF re-save of every registered document | discount+Ru and sla+Ru unchanged; prose engines without the register may change (measured) |

## Attacks

**Experiment 4's sets A and B (discount)** on discount, discount+R and discount+Ru. Experiment 4's
v3 (= discount.yaml) already had 0 unsafe on both, so this is a no-regression check plus a measure
of routing.

| # | Prediction |
|---|---|
| A-a | discount+Ru and +R: **0 unsafe** on targets and side effects |
| A-b | discount+Ru routes **no more** decisions than discount.yaml, and fewer wherever the guards routed on an unregistered or tampered document |

There is no SLA attack set yet. The fresh test for discount and SLA is the user's next set (G-31),
which will cover all three decision types.

## Cost

Jev: cents (replays, plus any new judgments on attacked text). No reader, no Utopia.
