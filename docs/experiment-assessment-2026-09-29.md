# Where the Northstar × Utopia experiment stands (2026-09-29)

This is Claude's assessment after two runs: small, and scale with 10× noise. It covers what is
solid, what is weaker than the headline numbers suggest, and what would firm it up. The
evidence is in `runs/2026-09-28-utopia-aad5b06/` and `runs/2026-09-28-utopia-aad5b06-scale-large/`.

## The result in one table

Decision scenarios S01–S05, blind Opus 5.5 reader over Utopia MCP:

| Reader and inputs | Small | Scale (10× noise) |
|---|---|---|
| Utopia's own chat (arm A), all 10 scenarios | 2 pass, 1 partial, 7 fail | not run |
| B1: text + graph tools, nothing else | 9 pass, 1 partial (of 10) | 9 pass, 1 partial |
| B2: graph tools only | 6 pass, 4 partial (of 10) | 2 pass, 7 partial, 1 fail |
| B2 + curated facts | 7/2/1 ×3; **S05 confidently wrong** | not run |
| B2 + curated facts + OWM procedure | S01–S04 3/3, S05 2/3 | not run |
| B2 + curated facts + procedure + request record | **15/15** | 13/15 → **15/15** with one more curated fact |
| B2 + procedure + request record, *uncurated* | not run | 0/1/4, all REQUEST_EVIDENCE (safe) |
| **B1 + procedure + request record**, curated / uncurated / uncurated leak-free control | not run | **15/15 · 15/15 · 15/15** |

Rows with 10 scenarios are graded provisionally by Claude; the decision rows (S01–S05) are
auto-scored against the answer key.

## What I think is solid

1. **The instrument works.** A seeded, byte-reproducible corpus with an oracle and an answer key
   made every arm comparable and the decision arms auto-scorable. Most of this experiment's
   value comes from that, and it's reusable.
2. **What the OWM contributes is clear, and it held at scale:**
   - the decision procedure with its outcome definitions
   - the decision's inputs (the request record from the system of record)
   - a structured decision record

   Each was necessary somewhere: the procedure for S03 and S05, the record for S05's basis. It
   took all of them to reach 15/15.
3. **The procedure makes failures safe.** Without it, curated facts produced a confident wrong
   approval (S05). With it, every miss at either scale was REQUEST_EVIDENCE or REVIEW_REQUIRED,
   never an approval. For a product, "missing facts become an evidence request, not a guess"
   may matter more than the pass rate.
4. **Graph-side changes act on the reader in non-obvious ways.** The identity correction made
   the graph-only reader *worse*, because it stopped digging `changes` for quotes (8/9 vs 0/9,
   p≈0.0002). Any "improve the graph" step needs a reader re-test, not an assumption.
5. **Extraction quality, not the reader, is what degrades with noise.** B1 didn't move at 10×;
   B2 did. The one scale miss after curation came down to one dropped fact.

## What is weaker than the numbers suggest

1. **Curation was informed by knowing the answers.** Every curated fact was chosen *after*
   seeing a failure, by someone who could read the truth and the answer key: the bands, the
   exception values, the reporting lines, and now the agreement's term. Each was stated in the
   KB's own corpus, so nothing was invented. But choosing *which* facts to curate is where the
   leakage is. "15/15 with curation" is an upper bound. The product question, whether curation
   can be done without the answer key, is untested. This is the biggest threat to validity.
2. **B1 may make curation unnecessary.** *(Tested after this was written; see the update below.)* B1 (text retrieval, no
   curation, no procedure) already gets S05 right at both scales. It found the SOP in the
   corpus and applied its "ask for the document" rule itself. So "the OWM must supply the
   procedure" is really "the *graph* doesn't model procedures"; retrieval surfaces them.
   B1 + procedure + request record on the *uncurated* graph is the missing arm. If it reaches
   15/15, curation is an artifact of restricting the reader to graph tools, and the boundary
   moves: the foundation's job becomes evidence retrieval with quotes, not modelled facts.
3. **The sample is small and a little circular.**
   - Five decision scenarios cover one customer, one request (DR-9001, varied) and one product
     family. 15/15 is 5 scenarios × 3 repeats, and the repeats aren't independent cases.
   - The procedure's five outcomes come from the same process (doc 03 §11) that the oracle
     implements. That's legitimate, since an organization's OWM would be authored from its own
     SOP. But it means the test is "can the reader follow the procedure over this graph", not
     "does the procedure generalize".
4. **Scale was one ingestion, so scale effects are confounded with extraction randomness.**
   Each corpus was ingested once, with gpt-4o. Differences I attributed to scale might be
   nondeterminism: the agreement losing its facts, the org chart losing its reporting lines,
   "Acme" attaching to the wrong customer. CSV truncation disappearing looks structural
   (tables chunked about 3 rows per chunk), but nothing has been replicated.
5. **The grades on non-decision scenarios are mine.** S06–S08, and B1/B2 generally, carry
   Claude's provisional grades. There is no human calibration yet (steps 7–8).
6. **The "OWM" is a prompt, not a system.** Every OWM arm is a strong reader given
   instructions. Whether a built decision service behaves the same, deterministically, with a
   weaker or cheaper reader, is open. Finding f01 ("the reader is the largest variable") says
   that matters.

## Update: the B1 arm answered weakness 2 (same day)

`runs/2026-09-28-utopia-aad5b06-scale-large/b1/notes.md`. The all-tools reader, with the
procedure and the request record, decides S01–S05 correctly on every scored field in 3 of 3
runs on each graph state: curated, curation withdrawn, and curation withdrawn with `changes`
hidden. The last is needed because withdrawn values stay readable there as `rejected` events.
That's 45 of 45. The readers took their facts from the source documents.

That turns weakness 1 into a smaller problem. Curation informed by the answer key only
inflated the *graph-only* result; the retrieval reader doesn't need curation at all. The
boundary, restated:

- **Foundation:** evidence retrieval with provenance, and identity (CRM-2048 ≡ C-1001 ≡ Acme
  Manufacturing). Modelled facts are needed only by graph-only consumers.
- **OWM:** the procedure and its outcome definitions, the decision's inputs (the request
  record), and the decision record.

Weaknesses 3–6 still stand: five scenarios about one request, one ingestion per scale,
provisional grades, and the OWM being a reader with a prompt.

## What I'd do next, in order

1. **Held-out scenarios:** add 3–5 decisions the procedure wasn't developed against, through
   `truth/scenarios/`. Ideas: a different customer, a delegation memo, an expired exception, a
   CRO-band request. This is now the biggest open question. New documents would be extracted
   into the *small* KBs only, which costs little.
2. **Human grading (steps 7–8)** in the ledger.
3. **Split the OWM inputs for B1:** procedure without the record, and record without the
   procedure. It's cheap and shows what each contributes when retrieval is available.
4. **Then** build the persisted OWM decision service, retrieval-based.
5. Blind curation matters only if the service is meant to reason over the graph alone.

## Cost so far

| | Spend | What drove it |
|---|---|---|
| Claude readers | **$68.27** for 243 answers (as of the B1 arm) | Graph-only readers take 20–40 turns per question; retrieval readers 8–26 |
| Utopia / OpenAI gpt-4o | **≥ $75** (the user's figure mid-scale-run) plus the settling calls after | Ingestion: extraction per chunk, adjudication per candidate pair, governance per queued pair. It scales with corpus size, not with questions |
| This Claude Code session | not visible to me | Orchestration, grading, write-ups |

**No next step needs gpt-4o again unless we re-ingest.** Idle KBs cost nothing. The hourly
"materialize inferences" job makes no model calls, and governance has no pairs to look at.
Reader runs touch Utopia's model only for query embeddings (fractions of a cent). A
curation push costs cents. A re-ingestion is the only expensive step, and only needed to
separate scale effects from extraction randomness.
