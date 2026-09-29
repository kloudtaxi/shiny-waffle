# S03 agreement check (2026-09-29)

**Question:** on the curated scale graph with the procedure and the request record (B2kPR),
S03 was right in 1 of 3 runs. The other two answered REQUEST_EVIDENCE instead of
REVIEW_REQUIRED. The suspected cause is that the scale graph holds the "Master Supply
Agreement" as a bare name, so no active contract can be established. Does restoring the one
agreement fact the small graph had close the split?

## Setup

- **Graph change:** a single statement, pushed by `agreement.py push --apply` through the scale
  curation's Statements source (base KB only; logged in `../curation/curation_log.jsonl`):
  "Master Supply Agreement **is effective** from April 1, 2025 to March 31, 2028", valid
  2025-04-01..2028-03-31. It is §1 of `acme_master_supply_agreement.md`, which is
  byte-identical in both corpora. In the small graph it was the agreement's only fact (value
  "March 31, 2028", quote "This Agreement is effective April 1, 2025 and expires March 31,
  2028 …"). Nothing else from the agreement was added: not its products, not §3.2, not §3.3.
- **Result of the push:** the fact attached to the existing entity
  (`01a0ea56-844c-7190-a85b-495616ce080b`). No new entity, no review pair, no merge.
  Processing took about 5 minutes (4 `align_phrases`, 4 `align_types`).
- **Governance** had been off since 13:31 UTC. It was switched back on at 16:14 UTC, before the
  runs; the user had meant to turn it on, but the setting hadn't saved. It ran one round in
  30 ms and did nothing (no pairs it hadn't looked at).
- **Reader:** unchanged from B2kPR. Blind Opus 5.5, graph-only tools (9, 0 denials),
  `--procedure owm/procedures/discount-approval.md`, and the S03 question with its request
  record. `questions.tsv` is the S03 row of `../request/questions.tsv`, verbatim.
- **Runs:** `arm-b/r1..r3/B2`, run in parallel. Tokens `northstar-scale-agreement-r1..3` are
  revoked. Cost $0.38 + $0.44 + $0.30 ($1.12).
- **Scoring:** `agreement.py score` applies the same rule as `../../2026-09-28-utopia-aad5b06/procedure/score.py`,
  by importing it, to S03 only. Output: `scores.json`.

## Result

| S03 on the curated scale graph | r1 | r2 | r3 |
|---|---|---|---|
| B2kPR (`../request/arm-b`) | ✗ REQUEST_EVIDENCE | ✓ REVIEW_REQUIRED | ✗ REQUEST_EVIDENCE |
| **+ the agreement's term** | **✓ REVIEW_REQUIRED** | **✓ REVIEW_REQUIRED** | **✓ REVIEW_REQUIRED** |

All three match the answer key on every scored field: outcome REVIEW_REQUIRED, eligibility
`not_covered`, requestor not authorized, VP Sales, Michael Torres. Each run now reasons the
way the small run did:

1. "The Master Supply Agreement runs from 2025-04-01 to 2028-03-31, so it was in force on
   2026-09-23."
2. The only Acme discount term is the NS-500 exception, which "does not apply to any other
   Northstar product".
3. So nothing covers NS-Cloud: commercial review.

**The scale miss was the foundation dropping one fact, not reader noise.** With it restored,
the decision scenarios are 15 of 15 on the curated scale graph: S01, S02, S04 and S05 from the
B2kPR runs, and S03 from this check.

## Limits

- n = 3, S03 only. S01, S02 and S04 run on the same base KB and were not re-run with the
  agreement fact. It can only add support there, but that is untested. S05 runs on the
  missing-contract KB, which this check didn't touch.
- This shows *which* fact mattered. It doesn't make that fact any easier to find. Curation
  needs the per-KB check that found the gap (compare the small and scale graphs, entity by
  entity, for the facts a decision depends on).
