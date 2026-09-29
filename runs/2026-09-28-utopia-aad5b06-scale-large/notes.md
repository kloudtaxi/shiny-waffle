> **STATUS: PAUSED 2026-09-29, waiting for a decision.** Utopia's OpenAI project hit its
> enforced spend limit near the end of ingestion (429 "configured enforced spend limit"). Two
> extraction jobs failed. Everything after this needs the decision below.

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

1. **Human identity review doesn't scale.** The Review queue went from 5 trivial items at
   small scale to 2,763 and 3,828 pending pairs. The review workflow the correction arm
   relied on isn't a practical control at this size.
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

**Decision pending.** Either raise the OpenAI spend limit, then requeue the two failed
extractions and run the full plan; or run only the arms that need no Utopia model calls.
