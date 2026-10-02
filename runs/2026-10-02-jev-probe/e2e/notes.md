# E2E: the agent retrieves, the hybrid engine decides (2026-10-02)

Pre-registered in `../plan-2.md` (commit `de1e073`).

- **Inputs:** the 102 T1/T2 transcripts. Blind B1n readers searched the scale KBs themselves for
  17 decision scenarios, 3 runs each, in each arm.
- **Evidence sets:** each transcript's set is rebuilt from its tool calls (`run.py`):
  - **read:** documents opened with `get_document`;
  - **seen:** read, plus documents surfaced by a search.
- **Decision:** the hybrid engine (J1's, unchanged except for the document filter) decides from
  that set alone. J1 replays 18/18 after the change.
- **Cost:** no new reader runs, and no new Jev calls (all from J1's recording). Utopia was read
  only.

## Results (`results.md`)

| Evidence set | Retrieval sufficient | Hybrid strict pass | Readers' own strict pass (same transcripts) | Unsafe |
|---|---|---|---|---|
| **seen** | **102/102** | **102/102** | 93/102 | 0 |
| **read** | 87/102 | 94/102 | 93/102 | 0 |

- **On "seen", every transcript the reader failed (9) is passed by the hybrid**, and every one it
  passed stays passed. The nine:
  - T1 S13 ×3 and S15 ×3 (routing);
  - T1 S04 r3 (the DR-9001 date artifact);
  - T2 S18 r2 and r3 (the cited agreement against the one in force).
- **On "read", the hybrid misses 8**, all conservative: `REQUEST_EVIDENCE` or `REVIEW_REQUIRED`.
  In each, a needed agreement or exception was only glimpsed in a search excerpt, never opened.
  The readers passed those from the excerpt.

## Against the predictions

1. **"'Seen' is sufficient in at least 90%":** held: 100%.
2. **"Hybrid on 'seen' passes at least 95 of 102, against the readers' 93":** held: **102/102**.
3. **"Where retrieval missed a needed document, no unsafe approval":** held. 0 unsafe in either
   set.
   - The outcomes were either correct or conservative.
   - Some "insufficient" transcripts still passed, because the engine can recognise an agreement
     from the exception that names it.
4. **"'Read' less often sufficient than 'seen'":** held: 87 against 102.

## What it shows

- **Retrieval was never the bottleneck.** Across 102 runs, the agents surfaced everything the
  decision needed.
- **The agents' misses were all in turning evidence into a decision:**
  - the routing boundary (S13/S15);
  - the cited agreement against the one in force (S18);
  - the input artifact (S04).
- **Split the work the way J1 does, and those misses disappear on the very same evidence.** The
  agent gathers, Jev judges, and code decides. This is the end-to-end version of J1's result, and
  of "keep code in control".
- **What still matters:** the engine needs the *document*, not an excerpt (8 misses on "read"). An
  agent working for the engine should open what it finds, or the foundation should hand over full
  documents. An agents-first tool shaped for this would be "fetch the governing documents for
  request X".

## Limits

- **"Seen" gives the engine the full document** whenever any excerpt of it surfaced. That is
  generous, and "read" is the conservative bound.
- **Authority is held at truth, as in J1.** This tests eligibility evidence only.
- **The engine is handed today's record for each scenario.** S02–S04 now carry their own ids, while
  the T1 readers saw the old DR-9001 records. The S04 artifact therefore can't arise for the
  engine.
- **T1/T2 transcripts only.** Agents whose job is to gather evidence, rather than to answer, have
  not been run.
