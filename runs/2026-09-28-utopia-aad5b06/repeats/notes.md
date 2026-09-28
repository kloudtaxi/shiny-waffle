# Repeats: B2 on the corrected graph, n = 3 (2026-09-28)

**Setup:** identical to arm B / B2 (see `../notes.md`, "Arm B"). A blind Opus 5.5 reader with
the text tools hidden, on the KBs as corrected at 17:25 UTC. Runs `r2/` and `r3/` sit
alongside run 1 (`../correction/arm-b/B2`), so B2c has n = 3.

- **Integrity check:** before the runs, the graph was unchanged: 267 and 264 live facts, 23
  and 17 merges, no facts recorded after the correction, and only routine
  `materialize_inferences` jobs.
- **Run checks:** all 20 runs saw 9 tools with 0 permission denials.
- **Tokens:** `northstar-repeat-r2` and `northstar-repeat-r3`, both revoked.
- **Cost:** $2.78 + $2.88 = $5.66. Turns: 218 + 238.

## Grades (provisional, Claude's first read)

| | S01 | S02 | S03 | S04 | S05 | S06a | S06b | S06c | S07 | S08 | ✓ / ◐ / ✗ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B2 pre-correction r1 | ◐ | ✓ | ◐ | ✓ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 6 / 4 / 0 |
| B2c r1 | ✗ | ✗ | ◐ | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 4 / 3 / 3 |
| B2c r2 | ✗ | ✗ | ◐ | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 4 / 3 / 3 |
| B2c r3 | ✗ | ◐ | ◐ | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 4 / 4 / 2 |

**B2c is stable.** S01 and S04 fail in all three runs. S04 leans the *wrong* way in r2 and
r3 ("points toward no"; the answer key is APPROVE under the 2025 policy). The pre-correction
run is the outlier.

## This corrects an earlier claim

`../correction/comparison.md` said the post-correction B2 drop was **reader-strategy
variance, not the correction**. With n = 3 that no longer holds. The drop is reproducible
on the corrected graph, and it coincides with a strategy change:

**Per-entity `changes` calls, per question** (✚ = the percentage quotes reached the reader):

| | S01 | S02 | S03 | S04 | S05 | S06a | S06b | S06c | S07 | S08 |
|---|---|---|---|---|---|---|---|---|---|---|
| B2 pre r1 | 9✚ | 9✚ | 4✚ | 8✚ | 0 | 1✚ | 1✚ | 0 | 2✚ | 0 |
| B2c r1 | 0 | 0 | 0 | 0 | 0 | 2✚ | 1✚ | 1 | 2✚ | 0 |
| B2c r2 | 0 | 0 | 7✚ | 0 | 0 | 1✚ | 1✚ | 1✚ | 2✚ | 0 |
| B2c r3 | 0 | 0 | 4✚ | 0 | 12 | 1✚ | 1✚ | 1✚ | 2✚ | 0 |

- **The authority questions (S01, S02, S04):** 8–9 calls before the correction, **0 in 9 of
  9** runs after. That's where the grades dropped.
- **Where the question is directly about Acme's discount (S06, S07):** the reader reaches
  for `changes` every time, before and after, and those questions pass throughout.
- **The two post-correction runs that did dig on an authority question (S03 r2 and r3):**
  both reached the 10% limit and gave a verdict.

## Hypothesis: consolidated identity made the graph look complete

In the pre-correction S01 trace, the reader walked a run of thin, duplicated entities
("VP Sales" with 1 fact, "Enterprise Account Executives" with 1 fact, twice) before
switching to `changes` per entity, where the source quotes live. After correction, its
first `entity_facts` reads returned richer entities (Sarah Chen 3 facts, NS-500 7, the Acme
exception 5). It judged the graph sufficient, never opened the audit feed, and answered
"can't confirm".

If this holds, cleaning identity **lowered** graph-only accuracy by removing the friction
that led the reader to the evidence. The foundation-level cause is unchanged:
`entity_facts` carries document ids but **not quotes**, so graph-only answers depend on an
undocumented use of a record-time audit tool. The fix belongs in the read contract (quotes
or chunk ids on facts), not in identity review.

**The caveat:** pre-correction is n = 1. The proper test is pre-correction repeats:
temporarily revert the 17 correction merges (Utopia supports reverting merges), run B2 twice
more, then re-apply. That costs about $5.50 and briefly changes the KBs. Until then, f13 is a
hypothesis.
