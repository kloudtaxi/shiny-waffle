> **STATUS: DONE 2026-09-29.** Graph-only reader + curated facts + OWM procedure + request
> record: **13/15**, 15/15 once the agreement's term is curated (`agreement/notes.md`).
> **All-tools reader + procedure + request record: 15/15 with or without curation** (45 of 45,
> including a leak-free control; `b1/notes.md`). Curation is only needed for graph-only
> consumers. Both scale KBs are curated again and governance is on.

# Scale run: Northstar at `--scale large` (2026-09-28)

**Question:** does the small-run result (curated facts + OWM procedure + request record →
15/15) hold when the corpus carries 10× the noise?

**Dataset:** `uv run northstar build --scale large --out dataset` (seed 20260923): 200
customers, 40 employees, 80 products, 500 orders, 1,000 discount requests. It has the **same
17 artifacts, truth and answer key** as the small run (`expected-results.yaml` is identical),
and the same question text (`questions.tsv`, `request/questions.tsv`; only the KB ids differ).
The DR-9001 CRM row is byte-identical to the small run's.

**KBs:** fresh, with the same packs (schema-org, w3c-org), created 23:25 UTC. The ids are in
`kbs.jsonl`. The small-run KBs are untouched.

## The foundation at scale

Ingestion settled after **95 minutes** (the small run took 6).

| | base | missing-contract |
|---|---|---|
| live facts (open) | 12,895 (10,075) | 12,677 (10,257) |
| live entities | 2,725 | 2,203 |
| merges | 222 | 210 |
| automatic identity decisions | 18,903 | 14,401 |
| **duplicates waiting for a human** | **2,763** | **3,828** |
| agent proposals open | 210 | 156 |
| CSV `truncated_reply` drops | 0 | 0 |

### Findings

1. **The identity-review queue is large, but most of it is the governance agent's unfinished
   backlog.** The Review queue went from 5 trivial items at small scale to 2,763 and 3,828
   pending pairs at settle. *Corrected 2026-09-29:* governance jobs succeeded until 00:34 UTC.
   From 01:08 every hourly run failed on the spend limit. At 13:05 the agent had never looked
   at 2,555 of 2,965 pending pairs in base, or 3,673 of 4,031 in missing-contract. The pending
   count had grown because the requeued extractions were still running. So the queue measures
   stalled governance, not only pairs the agent left for a human. *Settled numbers:* once the
   limit was lifted, governance cleared its whole backlog in 23 minutes (13:08–13:31 UTC). It
   decided 3,570 pairs "keep separate" in base, and 5,462 "keep" plus 4 merges in
   missing-contract. **232 and 203 pairs now wait for a human** (234 and 204 open agent
   proposals). That is about 40–46× the small run's 5, not the 550× the stalled count
   suggested. See "Settling after the spend limit".
2. **No CSV truncation this time.** Every small-run CSV had a `truncated_reply`; here there
   are none, with tables chunked about 3 rows per chunk (334 chunks for 1,000 requests). So
   truncation was not inherent to CSVs. In base, **DR-9001 made it into the graph with its
   justification** ("Contract pricing per Acme Master Supply Agreement"), which the small run
   lost.
3. **The org chart produced no reporting relationships at all.** Its 3 chunks yielded titles
   ("is VP Sales"), 54 `known as` name facts, and 20 facts whose phrase is the em dash
   separator ("—"). At small scale the reporting lines came out inverted; at scale they are
   missing. Same document, different failure.
4. **Utopia's OpenAI project hit its spend limit.** The last extraction rounds of
   `discount_requests.csv` failed in both KBs: 28 of 30 chunks and 46 of 53, error "LLM
   account cannot pay for this request (429)". Both documents are correctly marked
   `graph_status = failed` (`snapshot/*.failed-jobs.tsv`). In base about 84 background rows
   are missing, while DR-9001 and DR-8104 are present. In missing-contract, DR-9001 lost its
   justification (5 facts, none of them the justification).
5. **The RDF export fails at scale.** Base: `422 unexported_target — fact.object(merged):
   152 row(s)`. Facts that point at merged-away entities make Utopia refuse its own declared
   machine-readable contract (ADR 0020). The missing-contract export succeeded
   (`snapshot/missing-contract.ttl.gz`). This is upstream issue 6.

## What the spend limit blocks

| Needs Utopia's OpenAI model | Doesn't |
|---|---|
| Finishing the two failed extractions | B2 graph-only reads (`find_entities`, `entity_facts`, `changes` are SQL) |
| B1 (`search_chunks` embeds each query) | B2PR (procedure + request record, uncurated) |
| Curation (a Statements push is embedded, name-resolved and aligned) | |

**Decision (user, 2026-09-29):** raise the limit and run the full plan.

## Settling after the spend limit (2026-09-29)

1. **Extraction finished.** Both failed `discount_requests.csv` jobs were requeued (`POST
   /kbs/{id}/jobs/requeue {"kind":"extract_document"}`). The requeue resumes only chunks with
   `extracted_at IS NULL`. They completed with no 429s: 0 unextracted chunks, `graph_status =
   done`. All 485 and 481 chunks are embedded.
2. **Governance then ran for real.** It had failed on every hourly run from 01:08 to 12:08.
   From 13:08 it drained the whole backlog in 23 minutes (finding 1). Its gpt-4o cost isn't
   visible from here.
3. **Governance switched off** on both scale KBs at 13:31, after the backlog was already empty.
   This was the user's call ("option 1"): keep the graph still while the readers run, and stop
   any further spend. A difference from the small run: there, governance was still on during
   curation. Here, pairs raised by the curation push go only to `curate.py resolve`.
4. **Settled state** (`snapshot/settled/`):

   | | base | missing-contract |
   |---|---|---|
   | live facts | 13,721 | 14,122 |
   | live entities | 2,812 | 2,344 |
   | merges | 222 | 212 |
   | duplicates waiting for a human | 232 | 203 |
   | RDF export | still refused (`fact.object(merged): 152`) | 11.7 MB |

   DR-9001 is unchanged by the resume. Base has all 9 fields including the justification.
   Missing-contract has 5 fields and no justification: the row's own chunk was extracted
   before the limit, and it lost the justification then.

## Reader arms on the uncurated graph (2026-09-29)

Same controls as the small run (`lab/utopia/README.md`): blind Opus 5.5, fixed system
prompt, fresh temp dir, per-run read token revoked afterwards. Questions are `questions.tsv`
and, for B2PR, `request/questions.tsv`. Every run saw its expected tools (B1 11, B2 9) with 0
permission denials. In B1 S01 the reader's first three calls used bare tool names ("No such
tool") before it switched to the `mcp__utopia__` names. That didn't affect the answer.

| Arm | Folder | n | Claude cost | Grades |
|---|---|---|---|---|
| B1: all tools | `arm-b/B1` | 10 | $1.61 | **9 pass, 1 partial** (read) |
| B2: graph only | `arm-b/B2` | 10 | $3.06 | **2 pass, 7 partial, 1 fail** (read) |
| B2PR: graph only + procedure + request record | `request-uncurated/arm-b/r1/B2` | 5 | $2.16 | **0 pass, 1 partial, 4 fail** (auto, `request-uncurated/scores.json`) |

For comparison, the small run's B1 was 9 pass and 1 partial, and its B2 was 6 pass and 4
partial.

- **Text retrieval doesn't notice the noise.** B1 is identical to the small run, down to the
  same S03 partial ("needs VP sign-off" rather than commercial review).
- **The graph-only reader got worse at scale, for a specific reason.** At small scale one
  fact carried the agreement's sentence "Customer is eligible for discounts of up to 15% on
  the NS-500" as its evidence quote, and digging through `changes` surfaced it. At scale no
  fact from `acme_master_supply_agreement.md` or `acme_pricing_exception.md` carries a 15%
  quote. The 2025 exception came out as structure only (supersedes, applies only to, does not
  grant authority, approved by David Morgan). With nothing to dig for, B2 never finds 15%. It
  also attributes the old exception's dates (2023-04-01..2025-03-31) to the new one, and so
  treats Acme's contract discount as expired.
- **Given the procedure, the uncurated reader refuses to decide.** B2PR answers
  REQUEST_EVIDENCE on all five scenarios. It lists the missing exception maximum, validity
  dates and approval bands, and never approves or rejects. By the fixed rule that is 4 fails
  and 1 partial (S05's outcome is right, but it leaves requestor-authorized `null`). But these
  are **safe** failures: the procedure turns missing facts into an evidence request, not a
  guess.
- **A new identity error at scale.** In both scale KBs the bare "Acme" in
  `email_sarah_to_michael.md` was attached to **Acme Industrial Supply Co.** as a name. In
  missing-contract, "asking for 15% off list" was attached there too. B2 S05 reported it
  ("In the DR-9001 source, 'Acme' was linked to Acme Industrial Supply Co."). The small-run
  KBs don't have this attachment. Curation doesn't touch it, which keeps the small run's scope.

## Curation (2026-09-29)

`curation/curate.py` has the same scope as the small run (`../2026-09-28-utopia-aad5b06/curation/`),
with the reporting lines derived from `organization_chart.md` instead of a fixed list. There
were no inverted edges to reject (the chart produced no `reports to` at scale).

- **Pushed** through a Statements source in each KB (`curation/curation_log.jsonl`): 43
  reporting lines per KB, all unambiguous; the 2025 and 2026 approval bands; and in base only,
  the exception values (10% for 2023-04-01..2025-03-31, 15% for 2025-04-01..2028-03-31).
  `curation/verify.txt` lists the result.
- **Identity:** the push minted duplicate Sarah Chen and David Morgan entities in base. Utopia's
  adjudicator merged both into the existing people (`auto_merged|adjudicated 0.90`), 22 seconds
  after the push, with no review queued. Missing-contract attached every name directly.
  `curate.py resolve` had nothing to do. At small scale the same kind of duplicates waited for
  a human at 0.52–0.54 (small-run finding f16).
- Processing took about 5 minutes (7 `adjudicate_entities`, 8 `align_phrases`, 12
  `align_types` jobs).

## Curated graph + procedure + request record (B2kPR, n = 3)

`request/arm-b/r1..r3/B2`, auto-scored by `../2026-09-28-utopia-aad5b06/procedure/score.py`
into `request/scores.json`. Every run saw 9 tools with 0 denials; tokens
`northstar-scale-request-r1..3` are revoked. Cost $1.98 + $1.83 + $2.06 ($5.87).

| | S01 | S02 | S03 | S04 | S05 |
|---|---|---|---|---|---|
| small run (×3) | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| **scale (×3)** | ✓✓✓ | ✓✓✓ | **✗✓✗** | ✓✓✓ | ✓✓✓ |

**13 of 15** match the answer key on every scored field. Both misses are S03 (NS-Cloud). They
answer **REQUEST_EVIDENCE** where the key says REVIEW_REQUIRED, and the cause is in the graph:

- At scale the "Master Supply Agreement" entity has **no facts beyond its name**. At small
  scale it had one
  ("is effective", with its dates), which let the reader establish an active contract.
- The request cites "Contract pricing per Acme Master Supply Agreement". So r1 and r3 apply
  the procedure's rule "if a request relies on a contract term that cannot be located, ask for
  the document", and ask for the agreement's NS-Cloud clause. r2 reads the NS-500-only
  exception as settling "not covered", and answers REVIEW_REQUIRED.
- Both outcomes decline to approve. The misses are conservative, not unsafe.
- Curation kept the small run's scope (bands, exception values, reporting lines) and added no
  agreement facts. Curating the agreement's term and dates would be the direct test that this
  closes the split.

## What the scale arm shows

| Reader | Small run | Scale |
|---|---|---|
| B1: text + graph, uncurated | 9 pass, 1 partial | **9 pass, 1 partial** |
| B2: graph only, uncurated | 6 pass, 4 partial | **2 pass, 7 partial, 1 fail** |
| B2PR: graph + procedure + record, uncurated | (not run) | **0 pass, 1 partial, 4 fail**, all REQUEST_EVIDENCE |
| B2kPR: curated graph + procedure + record | **15 / 15** | **13 / 15**; both misses ask for evidence |

1. **The boundary holds at 10× noise.** Curated facts plus the OWM's procedure plus the
   request record still decide correctly, and when they miss, they miss towards asking for
   evidence. The OWM's three contributions (procedure, inputs, decision record) are unchanged.
2. **What the foundation delivers changes with scale, and not only for the worse.** CSV
   truncation disappeared, and the 10% AE limit and the 2025 band sentence reached the graph.
   But the agreement's and exception's terms, the reporting lines and one customer identity
   ("Acme") got worse. The curation list stays short, but *which* facts need curating is
   corpus- and scale-specific. It has to be verified per KB, not carried over.
3. **Without curation, the procedure is a safety rail, not a fix.** Given the procedure, the
   uncurated reader asks for evidence on every decision instead of guessing. Compare the small
   run's curation arm without the procedure, where S05 was a confident approval. Correct
   decisions still need the facts.
4. **Text retrieval is noise-robust here.** B1 didn't move. The graph-only reader is what
   depends on extraction quality.
5. **Operations at scale.** Ingestion took 95 minutes and hit the OpenAI spend limit.
   Governance needed 23 minutes of gpt-4o to clear 9,000+ pairs and leaves ~200 per KB for a
   human. The base RDF export is refused. Claude reader spend for this run was **$12.70**
   (B1 $1.61, B2 $3.06, B2PR $2.16, B2kPR $5.87). Utopia's OpenAI spend isn't visible here.

## S03 agreement check (2026-09-29)

`agreement/notes.md` has the full record. The base KB got the one agreement fact the small
graph had: "Master Supply Agreement is effective", 2025-04-01..2028-03-31, from §1 of the
agreement. It was pushed through the curation source and attached to the existing entity, with
no review pair. S03 was then re-run 3 times with the B2kPR setup.

**S03: 3 of 3 REVIEW_REQUIRED** (was 1 of 3), right on every scored field. Each run
establishes the agreement as active, finds no NS-Cloud term, and sends the request to
commercial review. So the scale miss was one dropped fact, and the curated scale graph matches
the small run: 15 of 15 on the decision scenarios. Cost $1.12. Governance was switched back on
(16:14 UTC) before these runs; its round changed nothing.

## B1 arm: text retrieval + procedure + request record (2026-09-29)

`b1/notes.md` has the full record. The all-tools reader (B1) was given the OWM procedure and
the request record, and run 3 times on each graph state:

| Graph | Reader | S01–S05 ×3 | Claude cost |
|---|---|---|---|
| curated | B1 | **15/15** | $5.04 |
| curation withdrawn | B1 | **15/15** | $5.44 |
| curation withdrawn | B1n (`changes` hidden, leak-free control) | **15/15** | $4.05 |

`b1/toggle_curation.py` withdrew the curation (tombstone + missing-cleanup; live facts back to
exactly 13,721 and 14,122), then pushed it back (restored exactly). Withdrawn values stay
readable as `rejected` events in `changes`, which is why the B1n control exists.

**With text retrieval, curation adds nothing to these decisions.** The foundation's job here
is evidence retrieval and identity; the OWM supplies the procedure, the request record and the
decision record. Curation remains the fix only for a consumer that reads the graph alone.
