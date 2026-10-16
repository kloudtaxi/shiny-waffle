# Today's foundation on the practice set: baseline pre-registration (2026-10-16)

**Status: pre-registered, not run.** Two items wait on the user (§7). Nothing is spent until both are
answered.

**Decided:** the user, 2026-10-16 (`docs/foundation-bench-assessment-2026-10-16.md`): practice set
plus a re-run baseline.

**Scoring plan this registers against:** glowing-garbanzo d06740c,
`owm/docs/b20-practice-set-scoring.md`.

## 1. What runs

| | |
|---|---|
| **System** | Utopia at **aad5b06**: the binary the live instance runs. It's a **second server process** on 127.0.0.1:1526, against an **ephemeral database `utopia_bench`** on the same Postgres server (the user's choice, 2026-10-16). It has its own data directory and its own workspace keys. The live database is never written. `utopia_bench` is dropped once both scorers have read it |
| **Models** | Chat `gpt-6-luna`, embeddings `text-embedding-3-small`, as for BlueLeaf's base |
| **Base settings** | **BlueLeaf's base's own settings**, read on 2026-10-16: `auto_extend_ontology` on, `ontology_lang` en, `materialize_inferences` on, `auto_type_resolution` on, **`governance` off**. A new base's default turns governance on; that is a labelled variant (§3) |
| **Declarations** | **None** (condition 1): no declared types, no uniqueness, no functional relations. B-20 declares nothing either |
| **Bases** | A fresh base for every run (the bench's own rule). Each base is kept until both scorers have read it, then the instance is deleted |
| **Judge** | None in the four scores. If recall's `judge_open` runs, its judge isn't `gpt-6-luna` |

## 2. The sets

| Set | Files | Loaded as | Questions |
|---|---|---|---|
| **Identity** | `corpora/identity/d00..d11` (12 files, mostly Chinese), as they are | In the bench's order with each file's `doc_time`, then a second base in reverse order | 21 anchors, 8 entities |
| **Temporal** | `temporal/corpus.json`, three waves | Wave by wave with `doc_time`. The queue drains before each wave's record time is taken. The bench's post-ingest operations run through Utopia's REST API, labelled as hooks (G3, G4) | 37 (23 world axis, 14 record axis), as the bench scores them; its known-gap questions are reported apart |
| **Recall** | The 4 NVIDIA filings `fetch-sec-filings.mjs` names, fetched at run time | Once | 52 items |
| **Contracts** | The Blackbaud HQ lease chain as `lease_bench.py setup` loads it, **without the 2016 base lease** (the bench's default) | Once, with the file dates the bench assigns | 18 |

The SEC files are fetched once, kept outside git, and their sha256 values are recorded in the run's notes,
so both foundations read the same bytes.

## 3. Runs

| Arm | Sets | Runs | Bases |
|---|---|---|---|
| **A. Like-for-like** (§1) | All four | 2 each | identity 4 (two orders × 2), temporal 2, recall 2, contracts 2 |
| **B. Declared** (labelled) | Temporal, contracts: the types and uniqueness the bench declares | 2 each | 4 |
| **C. Governance on** (labelled) | Identity | 2 | 4 |

Arm A is the baseline. Arms B and C are reported beside it and never replace it. If the spend guard
stops the run, B and C are dropped first.

## 4. Scoring

- **Through the contract** (recall, temporal, identity): garbanzo's scorers in B-20's `evaluation/`
  read web-next's adapter over the throwaway instance, with a read token scoped to it. The adapter's
  three fixes (qualifiers, the K15 list without a name, the open statements) land first.
- **The bench's own scorer, on the same bases, for every set.** This is the reference for today's
  foundation. For recall, identity and temporal, the contract-path score must equal it. A gap
  means the adapter loses something, and it's fixed before any comparison with B-20. An
  adapter that loses facts would under-count the baseline and flatter B-20.
- **Contracts:** the bench's own scorer only, until contract G1 lands. B-20 gets a port with the same
  rules, and both results are labelled.
- **Noise:** report every run, never only the best. A gap smaller than the bench's noise (recall
  SD 2.7 of 52, contracts ±3 of 18, temporal chat ±2) is reported as no difference.

## 5. Spend guard

- **Measured from the instance's own server log** (`llm usage` lines, as the bench's
  `llmUsageByCall` reads them), per set and per run. Dollars come from OpenAI's usage page afterwards.
- **Calibration first.** Run identity and temporal (small) first. Then project recall and contracts
  from their measured text sizes, and the cost per KB from those first runs.
- **Stop line: a projected total above $30** stops the run before recall and contracts, and I report.
  This is a rough guess: today's foundation can spend far more tokens than the text it reads (the
  bench measured 31k tokens per 270-token Re-DocRED document with alignment on), and `gpt-6-luna`'s
  price per token isn't in the lab's notes. My earlier "a few dollars" was too confident.
- Spend is on the user's Utopia OpenAI key, under the standing approval, and reported after the
  run.

## 6. Records

- **Results:** `runs/<run date>-utopia-aad5b06-bench-baseline/`, with `notes.md` first, this
  pre-registration copied in, the SEC files' hashes, the server log's usage lines, and both scorers'
  outputs. Runs are results: added to, never rewritten.
- **Never in a demo or UI:** today's foundation is not named. If results reach a client, it's
  "another foundation, on its own public bench".

## 7. Waiting on the user

1. ~~The instance~~: answered 2026-10-16. A second server on the same Postgres server, with an
   ephemeral database. It's up (no spend yet).
2. ~~The SEC contact~~: answered 2026-10-16. A project address, kept in the run's environment only,
   never committed.
3. **The OpenAI key for the bench instance's workspace.** Workspace keys are sealed per instance, so
   the live one's can't be reused. The user saves the key to a local file under `_owm-local/`, and
   the lab sets it through the instance's API without printing it.
