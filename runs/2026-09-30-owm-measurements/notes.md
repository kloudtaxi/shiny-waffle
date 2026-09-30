# OWM measurements, items 1–5 (2026-09-30)

> **STATUS: DONE.** All five items ran as pre-registered in `plan.md` (items 1, 2, 3, 5) and
> `04-decision-memory/prereg.md` (item 4). Nothing here decides anything. Each result is evidence
> for an amendment candidate in `docs/owm-overhaul-reconciliation-2026-09-29.md`.

- **System under test:** Utopia `dev` @ `aad5b06`, scale KBs (small KBs for item 3).
- **Reader:** blind Opus 5.5 over MCP, B1n (all Utopia tools except `changes`), fixed system
  prompt, per-run tokens revoked.
- **OWM stand-in:** `lab/owm_standin/server.py`, a stdio MCP server serving procedures and decision
  records. It holds no model and no business logic.

## Results at a glance

| Item | Question | Result | Detail |
|---|---|---|---|
| **1** | Does an agent call for a procedure served as a governed object, and does accuracy hold? | **Yes.** `get_procedure` was called in **102 / 102** answers, unprompted. On S01–S14 accuracy is 29/33 via the tool vs 30/33 with the procedure in the prompt; the one extra miss is conservative. | `01-02-procedure/notes.md` |
| **2** | Does procedure v2 fix the applicability gap without regressions? | **Half.** S13 and S15 went 0/3 → **3/3**, and S16/S17/S19 held. **S18 regressed 3/3 → 1/3**: readers judged the *cited* agreement instead of the one in force. v2 is not adopted. | `01-02-procedure/notes.md` |
| **3** | Can deterministic constraints catch the bad org graph? | **Yes, as flags.** Small graph as ingested: **13/13** inverted lines flagged (C2 + C3), **0/49** correct lines flagged. Scale graph before curation: no edges to conflict with, so it is a coverage gap (25/26). The rank constraint did the work; acyclicity caught nothing. | `03-constraints/notes.md` |
| **4** | Does decision memory work, and does it matter where it lives? | **Retrieval: both carriers work.** Typed record M1 2/3 by rule (3/3 on substance), document 3/3; no memory 0/3. The record is cheaper on M1 but not on the validity question. **No stale reuse:** 9/9 named the 2027 approver. **Unforeseen:** the decision *document* became undated graph facts and was cited as evidence. | `04-decision-memory/notes.md` |
| **5** | What do the misses look like on a split vocabulary? | Over 134 answers, **every miss with procedure + record present is a layer-2 routing disagreement** (`COMMERCIAL_REVIEW` vs `REQUEST_EVIDENCE`), with layer 1 right. **1 unsafe in 134, 0 in 119** once the record is present. | `05-vocabulary/notes.md` |

## What the five say together

1. **Agents-first holds for procedures and decisions.** A reader told nothing about the OWM found and
   used `get_procedure`, and `find_decisions` / `get_decision`, every time they were offered. Serving
   the procedure as a tool costs nothing measurable against injecting it into the prompt.
2. **Procedures need tests, not only wording.** Item 2's fix moved a failure to a neighbouring
   boundary. The lab's oracle plus held-out scenarios is the missing half: an executable,
   test-covered reference beside the prose an agent reads.
3. **Decisions must not be evidence.** Item 4's strongest result was not a score. Stored as a
   document, a decision fed its derived conclusions back into the foundation as timeless facts
   (`Sarah Chen limit 10%`), and later agents cited it as a source. Served as a typed record, it
   was used as precedent and never cited. Decision records need their own provenance class.
4. **Constraints should flag, with the evidence attached.** Item 3's conflict records carry the
   quote the extractor used, and the quote shows the misreading. A silent fix would have hidden it.
5. **The vocabulary amendment should separate decision state from routing**, and define the
   customer-applicability rule that separates the two routing values readers confuse (items 5 + 2).
6. **Nothing unsafe in 129 new answers.**
   - In items 1 and 2, every miss was conservative or a routing disagreement: no answer approved
     what the key does not approve, or named an approver without authority.
   - In item 4, the misses were the (a) row, which failed by construction, and one formatting
     slip.

## Predictions that failed (reported, not tuned away)

- **Item 2:** "v2 does not regress S16–S19." S18 regressed to 1/3.
- **Item 4:** "(c) passes M1 3/3 with fewer turns than (b) on M1 and M2." One M1 answer appended a
  note to the outcome string and fails the exact-value rule. On M2 the typed record took about as
  many turns as the document (10.3 vs 9.7), because both re-check the rules in force.
- **Item 3:** the coverage heuristic raised one false alarm (Elena Novak is a root).

## Cost

- **Claude (reader):** T1 $12.75 + T2 $13.33 (102 answers), plus item 4 $5.08 (27 answers), about
  **$31**. Smoke probes of the stand-in were not metered separately.
- **Utopia gpt-4o:** two small documents ingested into the scale base KB (the 2027 policy and the
  decision log), plus curation re-pushes. That is cents. Utopia logs usage only to a terminal, so
  this is not metered.
- **Items 3 and 5:** no model calls.

## State changes this batch leaves behind

- **Truth:** `pricing_policy_2027` (lab extension, F19–F21) and scenarios S15–S21. The dataset was
  regenerated: 18 artifacts, 21 scenarios. `owm/procedures/discount-approval-v2.md` was added; v1 is
  unchanged.
- **Utopia, scale base KB:** now contains `pricing_policy_2027.md`. The scale missing-contract KB and
  both small KBs do not, so they are one document behind the dataset.
- **Utopia, scale base KB:** the decision-log fixture was ingested for arm (b) and then deleted. 23
  `known_as` name facts stay live (see `04-decision-memory/notes.md`).
- **Curation:** reapplied on both scale KBs after the runs (`curation_log.jsonl`).

## Open for the user

- **Your grading pass** on the ledger is still pending.
- The amendment candidates these results bear on are listed in
  `docs/owm-overhaul-reconciliation-2026-09-29.md` §3, updated with these results.
