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

---

# Pre-correction repeats: B2 on the replayed pre-correction graph, n = 3

**Why a revert, not a replay.** Utopia is bitemporal, so the first idea was to replay the
pre-correction graph by stamping `as_of: 2026-09-28T17:25:00Z` onto the reader's MCP calls
through a proxy. It would only have been a half replay, because record-time reads aren't
uniform on MCP:

- **`find_entities` has no `as_of`,** although the store function under it
  (`graph::search_entities`) supports one. So merged-away entities can't be *found*.
- **`changes` windows are whole days,** so the 17:25 merges can't be excluded.

That's a read-contract gap worth raising upstream.

**What was done instead.** The steps are in `toggle_correction.py`, and all 34 operations are
logged in `toggle_log.jsonl`.

1. **Revert.** The correction's 17 merges were reverted newest-first through Utopia's own
   `POST /kbs/{id}/merges/{merge_id}/revert` (20:48:28–29 UTC). A human merge's revert moves
   the facts back and restores the entity under its original id; it doesn't reopen reviews or
   wake governance (`governance::after_revert` settles only agent decisions).
2. **Verify** against the pre-correction snapshot: live facts 268 / 265, merges 15 / 8, live
   entities 157 / 184. Every scenario entity came back with its old fact count (Acme Mfg.
   Holdings 14, NS-500 twins 11 and 1, C-1001 with its fact, the email entities separate).
   No jobs were queued.
3. **Run.** `lab/utopia/blind_reader.py` ran B2 twice, into `pre-r2/` and `pre-r3/`
   (started 20:48:52 UTC; tokens `northstar-pre-r2` and `northstar-pre-r3`, revoked). Cost
   $2.99 + $3.06; turns 246 + 240. Every run saw 9 tools with 0 denials.
4. **Re-apply** the same 17 source → target pairs oldest-first as manual merges (20:54:06–07
   UTC). The graph was un-corrected for under 6 minutes.
5. **Verify** against the post-correction snapshot: live facts 267 / 264, merges 23 / 17,
   entities 149 / 175. No queued jobs, and nothing new in Review.

**Caveat.** During the pre-correction runs, `changes` also listed today's merge and revert
events, which is noise the original pre-correction run (r1) didn't have. The results
replicate r1 anyway.

## Results (provisional grades)

| | S01 | S02 | S03 | S04 | S05 | S06a | S06b | S06c | S07 | S08 | ✓ / ◐ / ✗ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **pre r1** | ◐ | ✓ | ◐ | ✓ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 6 / 4 / 0 |
| **pre r2** | ◐ | ✓ | ◐ | ✓ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 6 / 4 / 0 |
| **pre r3** | ◐ | ✓ | ◐ | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 5 / 4 / 1 |
| post r1 | ✗ | ✗ | ◐ | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 4 / 3 / 3 |
| post r2 | ✗ | ✗ | ◐ | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 4 / 3 / 3 |
| post r3 | ✗ | ◐ | ◐ | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 4 / 4 / 2 |

**Per-entity `changes` calls** (✚ = the percentage quotes reached the reader):

| | S01 | S02 | S03 | S04 | S05 | S06a | S06b | S06c | S07 | S08 |
|---|---|---|---|---|---|---|---|---|---|---|
| pre r1 | 9✚ | 9✚ | 4✚ | 8✚ | 0 | 1✚ | 1✚ | 0 | 2✚ | 0 |
| pre r2 | 9✚ | 6✚ | 0 | 11✚ | 0 | 1✚ | 1✚ | 1✚ | 2✚ | 0 |
| pre r3 | 9✚ | 9✚ | 5✚ | 0 | 0 | 4✚ | 1✚ | 1✚ | 2✚ | 2✚ |
| post r1 | 0 | 0 | 0 | 0 | 0 | 2✚ | 1✚ | 1 | 2✚ | 0 |
| post r2 | 0 | 0 | 7✚ | 0 | 0 | 1✚ | 1✚ | 1✚ | 2✚ | 0 |
| post r3 | 0 | 0 | 4✚ | 0 | 12 | 1✚ | 1✚ | 1✚ | 2✚ | 0 |

## What this settles

1. **The correction changed the reader's behaviour, and with it the accuracy.** On the
   authority questions (S01, S02, S04), the reader dug through per-entity `changes` in **8 of
   9 pre-correction runs and 0 of 9 post-correction runs**. Same KBs, reader, questions and
   prompt; only the identity state differs. One-sided Fisher exact p ≈ 0.0002.
   - Correct answers: pre 6, 6, 5 against post 4, 4, 4.
   - Wrong answers: pre 0, 0, 1 against post 3, 3, 2.
2. **The dig decides S04.** It's right in exactly the runs that dug (pre r1, pre r2) and
   wrong in all four that didn't (pre r3, post r1–r3). S01 and S02 get a verdict when the
   reader digs, and "can't confirm" when it doesn't.
3. **The mechanism is still an inference, but a well-supported one.** Consolidated entities
   return richer-looking `entity_facts`, the reader judges the graph sufficient, and it never
   opens the audit feed where the source quotes live. The robust conclusion doesn't depend on
   the mechanism: **graph-only answers ride on an undocumented path** (quotes reachable only
   through `changes`). Improving identity closed that path by accident. The fix belongs in
   the read contract: quotes or chunk ids on `entity_facts`.
4. **Silent repair isn't universal.** In 3 of the 60 B2 answers (pre r3 S04, pre r3 S05,
   post r3 S01) the reader *flagged* the inverted reporting edge ("looks reversed … I'd treat
   the reporting lines as unreliable"). In the others it silently used title priors or didn't
   mention it.

For the OWM: a foundation fix that looks like pure improvement (cleaner identity) degraded
the one reader path that reached the evidence. Changes to the foundation need a regression
eval over the scenarios, which is what the OWM regression harness in
`docs/tracking-mlflow-review.md` is for.
