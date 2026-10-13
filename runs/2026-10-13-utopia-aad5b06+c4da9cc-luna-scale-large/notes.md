> **STATUS: DONE 2026-10-13.** Pre-registered in e7ca644. The plan below is unchanged, and the
> results follow it. luna against the gpt-4o scale run (reader grades are provisional ✓ / ◐ / ✗):
>
> | Measure | gpt-6-luna | gpt-4o |
> |---|---|---|
> | Identity: false merges (base / missing-contract) | **0 / 2** | 161 / 158 |
> | Identity: missed merges | 40 / 40 | 53 / 44 |
> | B1 (all tools) | 9 / 1 / 0 | 9 / 1 / 0 |
> | B2 (graph only), r1 · r2 · r3 | **7/2/1 · 8/1/1 · 6/3/1** | 2 / 7 / 1 (n = 1) |
> | B2PR (auto: pass / partial / fail) | **3 / 1 / 1** | 0 / 1 / 4 |

# Scale run on gpt-6-luna (`--scale large`)

## Why

The user chose this as the next arm on 2026-10-13. The small luna baseline
(`runs/2026-10-13-utopia-aad5b06+c4da9cc-luna/`, 79ad21c) left two questions open:

1. **Does luna's identity behaviour hold at 10× the noise?**
   - On gpt-4o, Utopia's governance made **161 and 158 false merges** on the two scale bases,
     mostly orders merged into customers (I2, `runs/2026-10-02-jev-probe/i2/`).
   - On the small corpus, luna merged only same-name duplicates.
2. **How does the graph-only reader do at scale?** On gpt-4o it fell from 6 / 4 / 0 to 2 / 7 / 1,
   because the 15% clause didn't survive extraction.

## What changes, and what stays fixed

The comparison is with `runs/2026-09-28-utopia-aad5b06-scale-large/` (gpt-4o), uncurated arms
only.

| | gpt-4o scale run | This run |
|---|---|---|
| **Model** | gpt-4o, effort unset | **gpt-6-luna, effort `low`**: workspace "Northstar Lab (gpt-6-luna)" `01a136bb-65c0-7690-a6f1-2e426588845f` |
| **Utopia** | aad5b06 | aad5b06 plus the user's LLM-client patch, `c4da9cc360511f87…` |
| Corpus | `--scale large`, seed 20260923: 17 base files, 14 missing-contract | **the same bytes**, from that run's committed `dataset/`. All 31 sha256 match the gpt-4o scale bases' documents (checked 2026-10-13) |
| Loading, KB settings, names | upload; packs `schema-org`, `w3c-org`; defaults (governance on) | the same, checked field by field against the gpt-4o scale bases after creation |
| Questions | `questions.tsv` (10) and `request/questions.tsv` (5, B2PR) | the same texts; only the `kb` column changes |
| B2PR procedure | `owm/procedures/discount-approval.md` at sha256 `6e72951c…` | **that version**, from `git show a9189a9:`. HEAD's version (c033091) is newer and is not used |
| Reader | `blind_reader.py`, claude-opus-5-5 | the same |
| Auto-scorer (B2PR) | `runs/2026-09-28-utopia-aad5b06/procedure/score.py` | the same. The fields it compares for S01–S05 are unchanged between 976d119 and HEAD (checked) |

**A known difference on the gpt-4o side.** Its run hit the OpenAI spend limit:
- `discount_requests.csv` partly failed in both KBs, so about 84 background rows were missing in
  base, and DR-9001 lost its justification in missing-contract;
- governance stalled until the limit was lifted.

Its uncurated reader arms ran after governance had cleared. Luna won't hit that limit, so any
difference on those rows is partly the spend limit's doing, not the model's.

## Steps

1. **Create the two KBs** in the luna workspace, named "Northstar (scale large)" and
   "Northstar (scale large) — missing contract evidence". Check the settings and ontology
   imports against the gpt-4o scale bases.
2. **Upload** the 17 and 14 files, CSVs first, as before.
3. **Settle.** This is the definition used here:
   - every document is ready and graphed;
   - no job for either KB is pending or running, for 60 s;
   - **and governance has cleared its backlog**: no pending identity review lacks an agent
     decision, or that count is unchanged across one full hourly `govern` cycle.
4. **Snapshot**, as in the small luna run:
   - counts, documents, merges, pending reviews, the review summary, extraction drops and the
     ontology;
   - the Turtle export. gpt-4o's base export failed with a 422; record either outcome.
5. **Identity (primary measure for this arm).** Label every governance decision with I2's code,
   unchanged (`j4/build_pairs.py` `label_all`, the lab resolver over this corpus). Map Utopia's
   decision with J4's `gpt_call`. Then count:
   - false merges;
   - missed merges;
   - pairs routed to a person;
   - unlabelled pairs.

   Compare with I2's gpt-4o figures: base 161 false merges, 53 missed, 230 routed; replication
   158 false merges.
6. **Reader arms (uncurated):**
   - probes;
   - **B1 once and B2 three times** (gpt-4o had n = 1 for each: B1 9/1/0, B2 2/7/1; r1 is the
     like-for-like comparison, and r2–r3 measure variance);
   - **B2PR once** (graph only, plus the procedure and the request record; gpt-4o 0 pass,
     1 partial, 4 fail), auto-scored.
7. **Graph checks** from the gpt-4o scale findings:
   - does the 15% clause survive extraction?
   - is the bare "Acme" in `email_sarah_to_michael.md` attached to Acme Industrial Supply?
   - does the org chart yield reporting lines?
   - the S05 hearsay (the small-luna finding).

No corrections, curation, rules, manual merges or Review-queue actions.

## Guards and cost

- **Stop rules:**
  - If the KBs haven't settled after **4 hours**, stop and report.
  - A terminal failed job (one that won't retry) is recorded. If it hits any of the 17 / 14
    evidence documents, the reader arms don't run until the user decides.
- **Utopia spend can't be measured** (as in the small run).
  - gpt-4o spent at least $75 on this corpus, including the stalled governance.
  - At luna's prices (about 1/20 to 1/25), the estimate is **$3–6**.
- **Reader**, on the Claude Code plan: B1 about $1.6, B2 3 × about $3.2, B2PR about $2.2, so
  **about $14**.
- **Tokens and the Default Workspace:** per-invocation read tokens, revoked at the end. The
  Default Workspace isn't touched.

---

## Results (appended after the run, 2026-10-13)

### What ran

All times are UTC.

| Step | When | Result |
|---|---|---|
| 1 · KBs | 20:35:52–20:35:57 | base `01a136fa-8e1d-77c0-b01d-bfc6423990b4`, missing-contract `01a136fa-a00d-7421-b90b-4ad99714585b`. Settings and ontology imports match the gpt-4o scale bases |
| 2 · upload | 20:36:16–20:36:20 | 17 + 14 files, every response `"error": null` |
| 3 · settle | 22:55:17 | **2 h 19 min** (gpt-4o: 95 min, stalled by the spend limit). 0 failed jobs, 0 failed documents. The last document was base's `discount_requests.csv` (334 chunks), whose extraction ran 20:36–22:47 (missing-contract's copy finished at 22:46). **Governance backlog: 0 pending reviews without an agent decision** in either KB at settle, so the third condition held without waiting a cycle |
| 4 · snapshot | 22:56 | `snapshot/`, as the small luna run, with the large files gzipped as the gpt-4o scale run did. **Base Turtle export refused:** `422 unexported_target — fact.object(merged): 22 row(s); fact.subject(merged): 3 row(s)` (`snapshot/base.export-error.txt`; gpt-4o: 152 rows, upstream issue 6). Missing-contract exported (`missing-contract.ttl.gz`) |
| 5 · identity | 22:58 | `identity.json` (`scripts/identity.py`); kind breakdown in `identity-breakdown.json` (`scripts/identity_breakdown.py`, added after the run) |
| 6 · readers | 23:00–23:06 | Probes pass (B1: 11 tools, B2: 9; connected; 0 denials). B1 + B2 r1 in `arm-b/`, B2 r2 and r3 in `repeats/`, B2PR in `request/arm-b/r1/`. The four batches ran in parallel, each with its own token, all revoked |
| 7 · graph checks | 23:05 | `graph-checks.md` (`scripts/graph_checks.py`, read-only SQL) |

**Deviations:** none from the plan. `scripts/snapshot.py` is the small run's snapshot script with
one change: an export refusal is written to `<prefix>.export-error.txt` instead of stopping the
snapshot.

### Pipeline

| KB | Model | Live entities | Live facts (open + typed) | Merges | Waiting for a human |
|---|---|---|---|---|---|
| base | gpt-4o (settled) | 2,812 | 13,721 | 222 | 232 |
| base | **luna** | 2,621 | **20,844** (17,848 + 2,996) | 80 | 224 |
| missing-contract | gpt-4o (settled) | 2,344 | 14,122 | 212 | 203 |
| missing-contract | **luna** | 2,552 | **20,705** (17,616 + 3,089) | 82 | 103 |

Luna raised about 12,700 and 11,700 identity reviews and decided all of them without a stall
(kept / merged / pending: 12,417 / 86 / 224 and 11,538 / 86 / 103).

### Identity (the primary measure)

I2's labelling (`j4/build_pairs.py` `label_all`) and J4's mapping, unchanged.

| KB | Model | Labelled pairs | Truly the same | Merged | Routed (share) | **False merges** | Missed merges | Right when acting |
|---|---|---|---|---|---|---|---|---|
| base | gpt-4o | 21,661 | 108 | 215 | 230 (1.1%) | **161** | 53 | 99.00% |
| base | **luna** | 12,523 | 155 | 80 | 204 (1.6%) | **0** | 40 | 99.68% |
| missing-contract | gpt-4o | 19,956 | 93 | 206 | 202 (1.0%) | **158** | 44 | 98.98% |
| missing-contract | **luna** | 11,601 | 154 | 85 | 97 (0.8%) | **2** | 40 | 99.64% |

Labelled pairs: luna 12,523 of 12,705 decisions in base and 11,601 of 11,726 in missing-contract.
The pair sets differ between models (different extraction), so compare rates, not pairs.

- **False merges almost vanish.** gpt-4o's 161 were mostly orders merged into customers. Luna
  merged no order into anything. The 2 in missing-contract are Faker near-namesakes:
  "Wilson-Wilson LLC" and "Wilson-Wilson" into "Wilson LLC", at 0.99.
- **Missed merges stay**, 40 in each KB. Most are background customers against their legal-form
  variants ("Smith Inc" / "Smith Inc LLC", "Weiss Ltd" / "Weiss Ltd Holdings": base 38 customer,
  2 product; missing-contract 30 customer, 10 product). Missing-contract also keeps ACME
  Manufacturing and Acme Mfg. Holdings apart (0.97); base merged them (0.91).
- **Jev + guard, for reference** (I2, τ = 0.9): 0 false and 0 missed merges, but 4.4% routed.
  Luna's governance now matches its safety on false merges, routes less, and misses more.

**What this changes:** I2's "the foundation's own governance is unsafe on identity" was a gpt-4o
result. On a current model, Utopia's governance is safe on false merges at this scale. The
remaining identity gap is missed merges.

### Arm B: the blind Opus reader

**B1 (all tools): 9 ✓ / 1 ◐ / 0 ✗,** the same as gpt-4o and the small runs. The ◐ is S03 again
(no exception transfer, but routed to VP sign-off instead of commercial review).

**B2 (graph only).** Each cell lists r1, r2, r3.

| Id | Expected | luna scale | Note |
|---|---|---|---|
| S01 | APPROVE_WITH_AUTHORIZATION, Michael | ✓ ✓ ◐ | r3 names Michael "at least", unsure whether 15% is the CRO's band |
| S02 | REJECT_OR_ESCALATE | ✓ ✓ ✓ | 18% is above the 15% cap |
| S03 | REVIEW_REQUIRED | ◐ ◐ ◐ | No transfer of the NS-500 exception; routed to the VP, not to review |
| S04 | APPROVE (2025 policy) | ✗ ✗ ✗ | All apply the 2026 bands (≤10%) to 2025. 0 `changes` digs in all three runs |
| S05 | REQUEST_EVIDENCE | ✓ ✓ ✓ | All three treat the Deal Desk note as unconfirmed and ask for the contract |
| S06a | 15% | ✓ ✓ ✓ | |
| S06b | 10% | ✓ ✓ ✓ | |
| S06c | none | ✓ ✓ ✓ | |
| S07 | the exception under the MSA, not hearsay | ◐ ✓ ◐ | r1 and r3 say the MSA is *not* the basis; it is (§3.2, Schedule B) |
| S08 | one customer; Acme Industrial different | ✓ ✓ ✓ | All three ids linked; ACME-MFG-2025 flagged as the weakest link |
| **✓ / ◐ / ✗** | | **7/2/1 · 8/1/1 · 6/3/1** | gpt-4o scale r1: 2 / 7 / 1 |

Totals over three runs: **21 ✓ / 6 ◐ / 3 ✗**, the same totals as the small luna run. At scale
the graph-only reader no longer degrades (gpt-4o: 6/4/0 small, 2/7/1 scale).

**S04's mechanism:** the 2025 policy's limit is in the graph only as an evidence quote
("Enterprise Account Executives may approve discounts up to and including 15%" on the fact
`Enterprise Account Executives —may approve→ discounts`). The number isn't a value, so a reader
that doesn't read quotes or dig through `changes` finds only the 2026 bands. The `changes` dig is
gone (`scripts/measures.py`: S04 = 0 in r1–r3).

**B2PR (graph only + procedure a9189a9 + request record), auto-scored** (`request/scores.json`):

| | S01 | S02 | S03 | S04 | S05 |
|---|---|---|---|---|---|
| gpt-4o scale | fail | fail | fail | fail | partial |
| **luna scale** | **pass** | **pass** | **pass** | fail | partial |

- gpt-4o's reader refused to decide anything (REQUEST_EVIDENCE on all five) because the exception's
  maximum, dates and bands were missing. On luna they're in the graph.
- **S04 fails safe:** the reader noticed the question's date (2025-09-23) differs from the record's
  (2026-09-23), decided on the record's date, and routed to Michael. It never approves.
- **S05 is partial** for the same reason as gpt-4o: right outcome, but requestor-authorized left
  `null`.

### Graph checks (step 7)

Full tables in `graph-checks.md`.

| Check | gpt-4o scale | luna scale |
|---|---|---|
| 1. The 15% clause | No fact from the agreement or exception carries a 15% quote | **Survives.** Base: the MSA's §3.2 sentence is the quote on `Customer —is eligible for→ discounts`, and the exception has `maximum eligible discount → 15% of list price` as a value. (Neither document is in missing-contract, by design) |
| 2. Bare "Acme" in Sarah's email | Attached to **Acme Industrial Supply Co.** in both KBs | **Not attached to it.** Base: "Acme" became a name of Acme Manufacturing (correct). Missing-contract: "Acme" stays its own entity, kept apart from Acme Industrial Supply (0.64) |
| 3. Org chart reporting lines | None at all | **Present, half right.** Sales: 20 of 20 under Michael (2 in base land on employee-id entities, `EMP-520`, `EMP-536`) and Michael → David. Finance: 2 of 22 right; **19 attached to a peer, Bryan Yoder** (an AR specialist), 1 missing. Same in both KBs. The lines the scenarios need (Sarah → Michael → David) are right |
| 4. The S05 hearsay | Not in the graph | **In the graph at 1.00**, as in the small luna run: `preferential NS-500 pricing —was/is→ 15%`, `—confirming→ Deal Desk`, in both KBs. All three B2 S05 runs read it as unconfirmed this time (small luna r3 didn't) |

The Finance error looks like a chunk-boundary effect: the indented list continues into a chunk
that no longer shows Elena Novak. That's a hypothesis; it wasn't tested.

### Cost

| Item | Cost |
|---|---|
| **Reader** (Claude Code plan) | **$17.12**: B1 $1.99; B2 $4.08, $4.14, $3.95; B2PR $2.83; probes $0.13 (estimate was about $14) |
| **Turns** | B1 97; B2 229, 232, 213; B2PR 169 |
| **Utopia** (OpenAI) | **Not measured**, as pre-registered. Luna extracted about 41,500 live facts and decided about 24,400 identity reviews in 2 h 19 min. The pre-registered estimate was $3–6 |

### What this says

1. **The scale result was mostly gpt-4o.** At 10× the noise, luna keeps the small run's reader
   results (B2 21 / 6 / 3 over three runs, both scales). gpt-4o lost the 15% clause, the reporting
   lines and the bare "Acme" at scale; luna keeps the first two and gets the third right.
2. **Identity at scale is safe on false merges** (0 and 2 against 161 and 158). This weakens I2's
   case for the OWM guarding the foundation's merges *as a safety fix*. The guard's remaining value
   is the routed share and the missed merges (40 per KB), and it is no longer a contrast against
   gpt-4o.
3. **What's left is the OWM's work, as at small scale:** which policy applies on a date (S04 fails
   in every graph-only run), who holds authority (S03 routes to the wrong reviewer), and whether a
   statement is confirmed or claimed (the hearsay is in the graph at full confidence; the reader
   caught it 3 of 3 times here, 2 of 3 before).
4. **New, smaller failures to watch:** the Finance reporting lines (19 of 22 under a peer) and the
   reader denying that the MSA is the basis for the 15% (S07 r1, r3).

These are provisional first-read grades. The user's grades belong in the Ledger's `grades`
collection.
