# B1 arm: text retrieval + procedure + request record (2026-09-29)

**Question:** every OWM arm so far used the graph-only reader (B2), and it needed curated facts
to reach 15/15. The all-tools reader (B1) already decided most scenarios without curation or
procedure. Given the OWM's procedure and the request record, does B1 need curation at all?
If not, curation is an artifact of restricting the reader to graph tools, and the foundation's
role in a decision is evidence retrieval, not modelled facts.

## Setup

Same controls as every arm: blind Opus 5.5, fixed system prompt plus
`--procedure owm/procedures/discount-approval.md` (same sha256), questions from
`../request/questions.tsv` (S01–S05 with the request record), fresh temp dir, per-run read
token revoked. Scored by `../../2026-09-28-utopia-aad5b06/procedure/score.py` with the fixed rule.

Scale only. The small KBs can't be returned to an uncurated state: their curation retracted 26
inverted `reports to` edges, and a retraction has no undo.

| Condition | Graph | Reader | Folder | n |
|---|---|---|---|---|
| **B1kPR** | curated (as left by curation + the agreement check) | B1: all 11 tools | `curated/r1..r3/B1` | 3 × 5 |
| **B1PR** | curation withdrawn | B1: all 11 tools | `uncurated/r1..r3/B1` | 3 × 5 |
| **B1nPR** | curation withdrawn | B1n: all tools but `changes` (10) | `uncurated/r1..r3/B1n` | 3 × 5 |

### Withdrawing and restoring the curation (`toggle_curation.py`)

At scale, curation only added facts: no edge was rejected, since the org chart yielded no
`reports to`. So all of it can be withdrawn, through Utopia's designed path:

1. **Withdraw.** A tombstone push (`deleted: true`) for each of the 8 curation documents (5
   base, 3 missing-contract) marks it "not in source". Then
   `POST /kbs/{id}/sources/{sid}/missing/cleanup` deletes them. That retracts every fact whose
   only evidence they were, and drops them from search.
2. **Result.** Live facts went back to **exactly 13,721 and 14,122**, the settled pre-curation
   counts (`../snapshot/settled/*.counts.tsv`). `verify-after-withdraw.txt` shows only
   extracted facts left: no reporting lines, bands or exception values, and the agreement is a
   bare name again. `state-before-withdraw.txt` and `state-after-withdraw.txt` record the
   documents.
3. **Restore.** After the runs, `reapply --apply` pushed the same statements again. Utopia
   answered `updated` for all 8 (the same documents, restored by identity). Live facts returned
   to exactly 13,774 and 14,170, and entities to 2,812 and 2,344, as before the withdrawal.
   There were no new review pairs or merges (`state-after-reapply.txt`).

### The leak, and the control for it

In the uncurated B1 runs, 13 tool results in 11 answers showed withdrawn curation values. The
source was `changes`, the record-time audit feed. It keeps every retraction as a `rejected`
event with the fact's value: the agreement's term, the 2025 band "15%", the exception's "15%
of list price". That's correct audit behaviour, but it means a graph with withdrawn curation
isn't clean for a reader that has `changes`.

**B1n** is the control. It is B1 with `changes` hidden, through a new `blind_reader.py`
variant, so the reader saw 10 tools. Across its 15 answers:

- No tool result mentions a curation document.
- One `search_chunks` call used `as_of` 2026-09-29T00:00Z. That's before any curation existed
  (13:41 UTC), and it returned source-document chunks.

## Results

| S01–S05 on the scale graph | r1 | r2 | r3 | Claude cost | Turns per answer |
|---|---|---|---|---|---|
| B2kPR: graph only, curated (`../request`) | 4/5 | 5/5 | 4/5 | $5.87 | 21–37 |
| B2kPR + agreement term, S03 only (`../agreement`) | — | — | — | $1.12 | 22–25 |
| B2PR: graph only, uncurated (`../request-uncurated`) | 0/5 | — | — | $2.16 | 29–43 |
| **B1kPR: all tools, curated** | **5/5** | **5/5** | **5/5** | $5.04 | 8–25 |
| **B1PR: all tools, uncurated** | **5/5** | **5/5** | **5/5** | $5.44 | 9–26 |
| **B1nPR: all tools but `changes`, uncurated** | **5/5** | **5/5** | **5/5** | $4.05 | 9–25 |

Scores: `scores-curated.json`, `scores-uncurated.json`, `scores-uncurated-nochanges.json`.
Every B1 answer matches the answer key on every scored field: outcome, eligibility,
authorized, required role and approver.

- **Curation adds nothing for a reader with text retrieval.** 15/15 with and without it, and
  15/15 in the control with no route to the withdrawn values. The B1n readers got their facts
  from the source documents: 96 `search_chunks` and 33 `get_document` calls, against 44 graph
  calls. The most-read documents were `discount_requests.csv`, the 2025 and 2026 pricing
  policies, the SOP, the authority matrix, the agreement and the exception.
- **It is also cheaper and shorter.** B1 takes 8–26 turns per decision against 21–43 for
  graph-only. It costs about the same per run, and more than B2PR's refusals, which cost less
  only because they give up.

## What this changes

The boundary conclusion so far said the foundation supplies facts, which needed curation where
extraction failed. For these decisions that holds only when the reader is restricted to the
graph. With retrieval over the source text:

- **The foundation's job is evidence retrieval and identity**: find the right passages, and
  tie CRM-2048 / C-1001 / "Acme" together. It doesn't need to model the facts a decision uses.
- **The OWM still supplies the procedure, the request record and the decision record.** B1
  without the procedure and record (`../arm-b/B1`) got 9 pass and 1 partial over 10 scenarios,
  with S03 framed as "needs VP sign-off" rather than commercial review. With them, all 15
  decisions are right.
- **Curation remains the fix for graph-only consumers.** That matters if the OWM is meant to
  reason over the graph without reading documents.

## Limits

- Scale only, n = 3, five decision scenarios about one request. The small-scale equivalent
  can't be run on the existing KBs.
- B1 with the procedure but *without* the request record, and with the record but *without*
  the procedure, were not run. Each OWM input's share in the B1 result is untested; in the
  graph-only arms the procedure mattered for S03 and S05, and the record for S05.
- These readers read whole documents. The result says nothing about a deterministic decision
  service that consumes graph facts.
