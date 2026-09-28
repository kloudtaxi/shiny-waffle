# Request-record arm (2026-09-28)

**Question:** with the procedure, S05 still failed once, because the graph lost DR-9001's
own record and so the request's basis was unknown. Does giving the reader the request *as the
OWM would receive it* close that?

## Setup

This is the procedure arm (`../procedure/notes.md`) unchanged: blind graph-only B2, curated
graph, `--procedure owm/procedures/discount-approval.md`. The one change is to the question.
After the verbatim question comes **the request as recorded in Northstar CRM**, the DR-9001
row from the corpus's own `discount_requests.csv` with each scenario's change applied from
its truth file:

| Scenario | Change to the record | Recomputed |
|---|---|---|
| S01, S05 | none | |
| S02 | requested discount 18% | discount $45,000, net $205,000 |
| S03 | product NS-CLOUD | list price $120,000 (products.csv), discount $18,000 |
| S04 | request date 2025-09-23 | |

Every record keeps the CRM's own `justification`: "Contract pricing per Acme Master Supply
Agreement". `questions.tsv` holds the exact question text. Only the decision scenarios run
(S01–S05); S06–S08 are unaffected.

**Runs:** `arm-b/r1..r3/B2` (n = 3). Every run saw 9 tools with 0 denials; tokens
`northstar-request-r1..3` are revoked. Cost $1.67 + $1.68 + $1.63 ($4.98). Auto-scored by
`../procedure/score.py --out scores.json` with the same fixed rule.

## Results

| | S01 | S02 | S03 | S04 | S05 |
|---|---|---|---|---|---|
| procedure only (×3) | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✗✓✓ |
| **procedure + request record (×3)** | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ | **✓✓✓** |

**All 15 decisions match the answer key on every scored field:** outcome, eligibility status,
requestor authorized, required role and approver.

- S05 is REQUEST_EVIDENCE in 3 of 3, for the right reason. Each run takes the basis from the
  record (`contract_exception`), sets eligibility to `unknown`, and lists as missing the
  Master Supply Agreement and any NS-500 exception on the date. Two also ask for the
  CRM-2048 → ERP mapping, the identity link the graph lacks.
- The record costs nothing extra: S01–S05 took 121–125 turns and $1.63–1.68, against
  123–127 turns and $1.67–1.78 without it.

## Where the whole run lands

| Arm | What changed | Graph-only reader on S01–S05 |
|---|---|---|
| B2, as ingested | — | quotes found only by digging `changes`; right when it dug |
| B2, identity corrected | 18 merges | worse (the dig stopped; f13) |
| B2, facts curated | bands, exception values, reporting lines | S01/S02/S04 right; **S05 confidently wrong** |
| B2 + procedure | the OWM's decision procedure | S01–S04 right; S05 2 of 3 |
| **B2 + procedure + request record** | the OWM's decision inputs | **15 of 15 right** |

For this corpus, the boundary between the knowledge foundation and the OWM is mapped:

- **Foundation:** entities, facts with evidence, and time. It needed curation where
  extraction failed: authority bands, exception values, reporting direction.
- **OWM:** three things.
  - **The decision procedure and its outcome definitions** (the organization's logic). The
    foundation doesn't model them even when the SOP is in the corpus.
  - **The decision's inputs**, the request record from the system of record.
  - **The decision record**, structured, auto-scorable and persistable.

  Each was necessary: facts for S01/S02/S04, the procedure for S03/S05, the record for S05.

**What this doesn't show yet:**

- Whether it holds under noise (the scale arm).
- Whether Claude's provisional grades on the non-decision scenarios agree with a human's
  (steps 7–8).
- Whether a persisted decision service behaves like a reader given the procedure. This arm
  used a reader with instructions, not a built OWM.
