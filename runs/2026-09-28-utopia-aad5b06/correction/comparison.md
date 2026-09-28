# Correction run: before vs after identity review

Same blind Opus 5.5 reader and setup as `../arm-b/` (see `../notes.md`, "Arm B"). The only
change is the 18 identity corrections applied at 17:25 UTC (see `../notes.md`, "Correction
run"). Transcripts are in `arm-b/B1`, `arm-b/B2`; the post-correction graph is in `snapshot/`.

|  | B1 before | B1 after | B2 before | B2 after |
|---|---|---|---|---|
| ✓ / ◐ / ✗ (provisional) | 9 / 1 / 0 | 9 / 1 / 0 | 6 / 4 / 0 | **4 / 3 / 3** |
| Cost | $1.45 | $1.49 | $3.19 | $2.71 |
| Turns | 85 | 86 | 248 | 229 |

| Id | B2 before | B2 after | Why it changed |
|---|---|---|---|
| S01 | ◐ right "no", approver only "obvious" | ✗ "can't confirm", no percentages found | reader strategy (below) |
| S02 | ✓ exceeds the 15% cap | ✗ no verdict, "percentage wasn't captured" | reader strategy |
| S03 | ◐ | ◐ no NS-Cloud exception ✓, authority unknown | same |
| S04 | ✓ APPROVE under the 2025 policy | ✗ "can't confirm"; leans toward "unlikely" | reader strategy |
| S05 | ◐ asks for the authority limits, not the contract | ◐ same | same |
| S06a/b/c | ✓ ✓ ✓ | ✓ ✓ ✓ | same |
| S07 | ✓ | ✓ | same |
| S08 | ◐ C-1001 found but unlinked; Acme Industrial different ✓ | ◐ "none of the IDs recorded anywhere, not even as an alias" | **the correction: the merge erased C-1001's name** |

B1 was unchanged on every question. It answers from document text, so graph identity
barely touches it.

## Findings

1. **Identity review bought nothing measurable on these ten questions.** Every
   identity-sensitive answer that B1 got right, it got right before and after. B2's binding
   constraints are **missing facts**, not identities: the VP Sales band, the percentages as
   values, and dated roles. No identity decision can supply those, and the Review queue never
   surfaced them. Human review in Utopia today reaches identity; the gaps that decide these
   answers sit in extraction.

2. **One correction made things worse.** Merging the ID entity `C-1001` (and `CRM-2048` in
   the missing-contract KB) into Acme moved the right facts but erased the ID as a findable
   name. The source entities had a canonical name but no name fact (see `../notes.md`,
   finding under "Correction run"). B2's S08 regressed from "C-1001 exists, unlinked" to
   "not recorded anywhere". A correct human action, through Utopia's own merge path, removed
   the evidence S08 needs.

3. **B2's pre-correction score depended on the reader discovering an undocumented trick.**
   Before: in S01, S02 and S04 the reader called `changes` about 10 times, per entity, with
   `since: 2026-09-28` (the ingestion day), and got every fact about that entity **with its
   source quote**, including "up to 15%" and "up to and including 10%". `entity_facts`
   carries `document_ids` but no quote, so in graph-only mode that audit feed is the only
   route to the percentages. After: in the same questions it called `changes` once (a
   generic "corrected / rejected / merged since 2025" query), found nothing useful, and never
   tried the per-entity form. **The correction didn't hide the quotes; this run just didn't
   find them.** `changes` is a record-time audit tool (MCP docs: "what the graph learned or
   revised in a window of record time"), and using it as a quote retriever works only
   because every fact was recorded on one day.

4. **With one run per cell, variance dominates.** The B2 before/after swing (6 → 4 right) is
   larger than any effect the correction could have had, and it's explained by tool
   strategy, not graph state. **No before/after claim about B2 is valid without repeats.**
   B1 was stable (9 → 9) because text search is a robust path.

## What this means for the OWM

- **Where human effort pays off here is fact curation, not identity review.** The review
  surface never showed the inverted reporting edges, the missing VP band or the missing
  percentages. An OWM that owns authority bands, dated roles and exception values as
  structured, validated facts is doing the work the review queue cannot.
- **The foundation↔OWM read contract needs quotes on facts.** Evidence text reachable only
  through a record-time audit feed isn't a contract an OWM can build on. `entity_facts`
  returning the supporting quote, or at least a stable chunk id (listed in Utopia's own
  "read-contract gaps", `chat-and-mcp.md`), would make graph-side reads deterministic.
- **Identity merges must preserve identifiers.** For an OWM, source-system ids (CRM, ERP,
  contract refs) are the identity keys. A merge that drops them is data loss, whatever the
  UI shows.

## Next

Before any more before/after runs: **repeat runs**, n = 3 per question for B2 at least, to
measure variance. Then either a **curation arm** (fix the VP band, the percentages and the
reporting direction, and measure B2) or the **scale arm**.
