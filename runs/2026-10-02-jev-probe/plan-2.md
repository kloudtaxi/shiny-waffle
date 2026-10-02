# Jev probe, part 2: J4 (identity at scale) and E2E (agent retrieval, then the hybrid engine)

Pre-registration, 2026-10-02. The user green-lit "1, 2 and 4" (J4, E2E, ledger) and skipped
laya. Committed before any J4 or E2E Jev call. The engine is `jev-1.13.0`, recorded through
`lab/decision_engine`.

## J4: Jev against gpt-4o on Utopia's duplicate queue

**Population.** The scale base KB (`01a0ea56-61e7…`): every duplicate pair (`resolution_reviews`)
with a governance decision (`agent_decisions`, `target_kind = 'review'`). That is 22,759 pairs:
- 22,295 applied keeps and 226 applied merges;
- 154 "unsure", 82 proposed keeps and 2 proposed merges.

None carries precedents, and every decision is gpt-4o's. Read-only SQL; nothing in Utopia changes.

**Ground truth (`j4/build_pairs.py`).** Each side's name is resolved to a lab object using the
scale corpus.
- The corpus is rebuilt at seed 20260923. Its six structured CSVs are byte-identical to the files
  Utopia ingested (the sha256 values match).
- Resolution rules:

  | Name pattern | Lab object |
  |---|---|
  | `CRM-n`, `C-n`, or a CRM/ERP customer name | that customer, keyed by DUNS |
  | an employee name or email | that employee |
  | a product SKU or name | that product |
  | `SO-n`, including the composite "`SO-n C-m`" | that order |
  | `DR-n` | that request |
  | a bare number | that literal |

- A pair is labelled only if both sides resolve. "Same" means the same kind and the same key.
- Composite "`SO-n C-m`" names are reported separately as well, because what they denote is
  arguable.

**Sample, fixed now.** Every labelable pair whose decision was a merge, unsure or a proposed keep,
plus 1,000 labelable applied keeps chosen at random (seed 20261002).

**Jev's input** is the governance adjudicator's own view, rebuilt as of the decision time:
- For each side: the name, a type label (`untyped` when there is none, as in Utopia), an "also
  known as" line, and the **top four facts**.
- Facts are chosen as `entity_fact_lines` chooses them: confidence first, then recency, with name
  facts excluded, in direction, predicate and other-entity form. They are rebuilt as live at the
  decision time, with any later merge that moved them undone.
- One question:
  - Choice: "Do `record_a` and `record_b` refer to the same real-world thing?"
  - Options: `same` / `different` / `unsure`.

**Jev's decision, fixed now:**
- `same` with confidence ≥ 0.5 means merge.
- `different` with confidence ≥ 0.5 means keep.
- Anything else is routed to a human.

**Measures, for gpt-4o and for Jev on the same pairs:**
- false merges (merged, but the truth says different);
- missed merges (kept, but the truth says same);
- the routed or unsure rate;
- for Jev, ECE on P(`same`).
- **Cost:** Jev's is measured. gpt-4o's is estimated from the rendered adjudication prompt for the
  same pairs (characters ÷ 4) at a stated list price. Its batching is noted as a discount it gets.

**Predictions:**
1. At least 10% of gpt-4o's merges are false merges.
2. Jev makes fewer false merges than gpt-4o on the same pairs.
3. Jev routes at most 20% of pairs to a human.
4. Jev's ECE ≤ 0.10.
5. Jev's cost is under 1% of gpt-4o's estimate.

## E2E: the agent's retrieval, then the hybrid engine's decision

**Inputs.** The 102 T1 and T2 reader transcripts (`../2026-09-30-owm-measurements/01-02-procedure/`):
- 17 scenarios, 3 runs each, per arm;
- blind B1n readers that searched the scale KBs themselves.

No new reader runs.

**The evidence set per transcript**, with documents mapped from Utopia `document_id` to filename
through the `documents` table of the KB the run used:
- **read:** documents the reader opened with `get_document`;
- **seen:** read, plus documents whose chunks came back from `search_chunks` or `search_docs`.

**The decision.** The hybrid engine (`j1/hybrid.py`) is unchanged, except that its candidate
agreements and exceptions are limited to the evidence set. The request record, the CRM account row
and the product row stay as structured inputs, and authority stays at truth, both as in J1.

**Measures:**
- **retrieval sufficiency:** the evidence set holds every agreement or exception document the
  oracle's evidence list needs;
- **strict pass** of the hybrid on each set, against the reader's own strict grade on the same
  transcript;
- **unsafe** (item 6's ruled definition).

**Predictions:**
1. "Seen" is sufficient in at least 90% of transcripts.
2. On "seen", the hybrid passes at least 95 of 102, against the readers' own 93/102 (T1 44, T2 49).
3. Where retrieval missed a needed document, the hybrid answers `REQUEST_EVIDENCE` or
   `REVIEW_REQUIRED`, never an unsafe approval.
4. "Read" is less often sufficient than "seen".

## Cost

- **Jev:** cents. E2E reuses J1's recorded judgments wherever the same documents recur.
- **Claude:** none.
- **Utopia:** read-only.
- **OpenAI:** none.
