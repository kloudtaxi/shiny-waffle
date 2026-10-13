> **STATUS: PRE-REGISTERED 2026-10-13. Nothing has run yet.** The plan below is fixed before
> any knowledge base is created. Results get appended below it, and the plan stays unchanged.

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
