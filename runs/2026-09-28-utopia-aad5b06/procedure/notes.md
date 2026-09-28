# Procedure arm (2026-09-28)

**Question:** curated facts fixed the authority questions but made S05 (missing contract)
confidently wrong. Is the missing piece the organization's *decision procedure*?

## Setup

This is the same blind graph-only B2 reader (`lab/utopia/blind_reader.py`), on the **curated**
graph (unchanged since the curation arm: 269 and 262 facts, nothing queued), with one change:
`--procedure owm/procedures/discount-approval.md` is appended to the fixed system prompt
(sha256 `6e72951c…`, recorded in each `setup-B2.json`).

**The procedure** is the corpus's own SOP (`sales_discount_sop.md`: 10 steps and 4
principles) plus doc 03 §11, the five outcome types, and a decision-record JSON for decision
answers. It contains no names, customers, products or percentages (checked). The SOP is in
the corpus as a document, but extraction didn't model it (9 `object_undeclared` drops), so a
graph-only reader had never seen it. Giving it to the reader is exactly the OWM-level input
being tested.

**Scoring.** `score.py` auto-scores S01–S05 against `dataset/answer-key/expected-results.yaml`,
field by field, with a rule fixed before the results were seen:

- **pass:** outcome, eligibility status and requestor-authorized all match, plus the approver
  whenever the expected outcome is an approval
- **partial:** the outcome matches but another field doesn't
- **fail:** the outcome doesn't match

S06–S08 are graded by reading. Full results are in `scores.json`.

**Runs:** `arm-b/r1..r3/B2` (n = 3, started 22:38 UTC). Every run saw 9 tools with 0
denials; tokens `northstar-procedure-r1..3` are revoked. Cost $2.56 + $2.56 + $2.46; turns
175 + 179 + 181.

## Results

| | S01 | S02 | S03 | S04 | S05 | S06a | S06b | S06c | S07 | S08 | ✓ / ◐ / ✗ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B2 curated (no procedure, ×3) | ✓ | ✓ | ◐ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ◐ | 7/2/1 ×3 |
| **+ procedure, r1** | ✓ | ✓ | **✓** | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ◐ | **8/1/1** |
| **+ procedure, r2** | ✓ | ✓ | **✓** | ✓ | **✓** | ✓ | ✓ | ✓ | ✓ | ◐ | **9/1/0** |
| **+ procedure, r3** | ✓ | ✓ | **✓** | ✓ | **✓** | ✓ | ✓ | ✓ | ✓ | ◐ | **9/1/0** |
| B1 (all tools, text; no procedure) | ✓ | ✓ | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 9/1/0 |

S01–S05 in the procedure rows are **automatic** (answer-key match); every other cell is
Claude's provisional read.

1. **S03 is right for the first time in any condition** (REVIEW_REQUIRED, eligibility
   `not_covered`, 3 of 3). Every earlier reader, including B1 with full text, framed it as
   "needs VP sign-off". The outcome definitions ("special terms do not transfer") are what
   separate the two.
2. **S05 returns REQUEST_EVIDENCE in 2 of 3.** All three runs recorded the request basis as
   `unknown` and listed the contract as missing evidence. Run 1 then *assumed standard
   pricing* and approved with authorization, saying "if it relies on an Acme contract term …
   the answer changes to asking for that document first".
3. **Nothing regressed.** S01, S02 and S04 pass the answer-key check in all runs, and the
   decision JSON appeared only for discount questions.
4. **Graph-only + curated facts + procedure matches the full-text reader** (9/1/0) and beats
   it on S03, in ~180 turns against B1's ~85. The reader walks the graph step by step instead
   of reading documents.

## What's left, and what it means

- **The remaining S05 miss is a missing input, not missing reasoning.** The graph lost
  DR-9001's own record to CSV truncation (upstream issue 5), including its justification
  "Contract pricing per Acme MSA". With the request's basis unknown, the procedure leaves
  the reader a judgement call. An OWM should take the **request record, with its stated
  basis,** as a first-class input (from the CRM), not hope to find it in the graph.
- **The boundary, as this lab now sees it.** The foundation supplies facts, and it needs
  curation where extraction fails. The OWM supplies three things:
  - the **procedure** and its **outcome definitions** (the organization's decision logic),
    which a foundation doesn't hold even when its source document is in the corpus
  - the **decision record** (auto-scorable, persistent)
  - the **inputs a decision requires** (the request record)

  Each of the three was necessary in some run: facts for S01/S02/S04, the procedure for S03
  and S05, and the request record for the last S05 case.
