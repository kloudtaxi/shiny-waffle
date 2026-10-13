> **STATUS: DONE 2026-10-13.** Pre-registered in 1cb4ac5. The plan below is unchanged, and the
> results follow it. Provisional grades (✓ / ◐ / ✗), luna against gpt-4o:
>
> | Arm | gpt-6-luna | gpt-4o |
> |---|---|---|
> | A | **6 / 3 / 1** | 2 / 1 / 7 |
> | B1 | 9 / 1 / 0 | 9 / 1 / 0 (the same) |
> | B2, three runs | 7/2/1, 6/3/1, 8/1/1 | 6/4/0, 6/4/0, 5/4/1 |
>
> - S08 identity goes from ◐ to ✓ in all three B2 runs.
> - Luna's denser graph also carries the S05 hearsay, which one B2 reader took as fact.

# Run 2026-10-13 · Utopia baseline on gpt-6-luna

## Why

This run replaces gpt-4o as the lab's baseline model. The user, 2026-10-13:

> "I chose the gpt-4o model for the lab when we started weeks ago because Utopia would only
> accept that model with erroring out. They still haven't fixed it so I patched their server to
> make other models works. gpt-4o is not a realistic baseline model."

Garbanzo's BlueLeaf comparison on 2026-10-13 suggested gpt-6-luna builds a better identity graph.
That comparison changed several things at once:
- the extraction model;
- the answer model;
- the corpus (571baac);
- the loading path (api push, not upload);
- governance (off).

So it can't say what the model did. This run changes **only the workspace's model**, against the
gpt-4o baseline `runs/2026-09-28-utopia-aad5b06/`, and repeats that run's arms A, B1 and B2.

## What changes, and what stays fixed

| | gpt-4o baseline (2026-09-28) | This run |
|---|---|---|
| **Model** (extraction, governance, dating, Utopia's chat) | gpt-4o, effort unset | **gpt-6-luna, effort `low`** (the user's setting for luna on this instance) |
| **Utopia** | `dev` @ aad5b06 | aad5b06 **plus the user's uncommitted LLM-client patch**, `git diff \| shasum -a 256` = c4da9cc360511f87… |
| Embeddings | text-embedding-3-small | same |
| Corpus | 976d119 evidence: 17 base files, 14 in the missing-contract variant | the same bytes, from `git show 976d119:`. All 31 sha256 match the gpt-4o bases' documents |
| Loading | multipart upload, one file per request | same (`lab/utopia/utopia.py upload`) |
| KB settings | packs `schema-org`, `w3c-org`; governance, auto-extend, auto type resolution and inferences on; inference every 60 min; visibility open; descriptions empty | same, checked field by field against the gpt-4o bases after creation |
| KB names | "Northstar Industrial Systems", "Northstar — missing contract evidence" | same names, in a new workspace |
| Questions | `questions.tsv`: 10 questions, verbatim | the same texts byte for byte; only the `kb` column changes |
| Reader | `blind_reader.py`, claude-opus-5-5, fixed system prompt, B1 = 11 tools, B2 = 9 (text tools hidden) | same script and controls |

**The patch is not a confound on the gpt-4o side.** It was checked on 2026-10-13: with gpt-4o the client
sends the same request body as aad5b06. The patch is what lets luna run at all, because aad5b06
sends `max_tokens` and temperature 0.0, and luna refuses both.

**Workspace.** A new one, "Northstar Lab (gpt-6-luna)":
- The Default Workspace stays on gpt-4o as the instrument for every earlier result. Nothing in it is
  touched.
- Utopia copies no settings into a new workspace, so the user adds the OpenAI key there once.

## Steps (runbook `docs/experiment-runbook.md` §5, steps 0–6, then arm B)

0. **Freeze the inputs.**
   - Done before this note: the corpus comes from `git show 976d119:` and was checked against the
     gpt-4o bases' sha256.
   - Lab commit: this note's commit.
1. **Smoke test.** A scratch KB with `products.csv`. Go on only if `extract_document` is done and
   the document has facts. Then delete the scratch KB.
2. **Create the two KBs** in the new workspace, and check their settings against the gpt-4o
   bases.
3. **Upload** the 17 and 14 files.
4. **Wait for the pipeline to settle.**
   - Every document ready and graphed, with no failed jobs.
   - Record the same counts as the 09-28 run: entities, open facts, typed facts, merges, and
     identity reviews (kept / merged / pending), plus `doc_time_source` per document.
5. **Snapshot**, after settling and before any question:
   - the Turtle export and ontology of each KB;
   - documents, extraction drops, merges and pending reviews.
6. **Arm A:** the 10 questions through `POST /kbs/{id}/chat`, Utopia's own chat (now luna), each
   in a new conversation.
7. **Arm B:**
   - a probe first: only `mcp__utopia__*` tools (11 for B1, 9 for B2), connected, 0 denials;
   - then **B1 once and B2 three times** (r1–r3).
   - This matches the gpt-4o baseline: B1 n = 1 and B2 pre-correction n = 3.

No corrections, curation, business rules, mappings, manual merges or Review-queue actions.
This run is the uncorrected, uncurated baseline only.

## What gets compared

The same provisional ✓ / ◐ / ✗ first read as `comparison.md`, against the same expected outcomes,
next to the gpt-4o numbers:

| | gpt-4o (2026-09-28) |
|---|---|
| Pipeline, base | 172 entities, 124 open facts, 144 typed facts, 15 merges |
| Pipeline, missing-contract | 192 entities, 124 open facts, 141 typed facts, 8 merges |
| Arm A | 2 / 1 / 7 |
| B1 | 9 / 1 / 0 |
| B2 pre-correction r1–r3 | 6/4/0, 6/4/0, 5/4/1 |

**Secondary measures:**
- per-entity `changes` calls on S01, S02 and S04 (the "dig" in `repeats/notes.md`);
- tools used;
- identity: whether CRM-2048, C-1001 and ACME-MFG-2025 are linked in the graph, and whether Acme
  Industrial stays separate;
- `doc_time_source` coverage (every evidence document states its date).

The grades are Claude's first read. The user's grades go in the Ledger's `grades` collection, as
before. This is a baseline, so there is no pass/fail.

## Guards and cost

- **Utopia spend can't be measured.** Utopia stores no token usage (only `errata_runs`), its
  server logs go to the user's terminal, and the user has no access to the OpenAI console.
  - Estimate: the 09-28 load took 6 minutes for both KBs. At luna's prices ($0.10 / $0.50 per
    million tokens in/out, about 1/25 of gpt-4o), this run's Utopia spend should be well under $1.
- **Stop rules:**
  - A failed job, or any `extract_document` error, stops the run before any question is asked.
  - If either KB hasn't settled after 60 minutes, stop and report.
- **Reader spend** is billed to the Claude Code plan:
  - B1 about $1.5, and each B2 batch $3 to $3.2 (09-28 figures);
  - so about $11 in total, plus about $0.1 for the probes.
  - The actual figures go below.
- **Tokens:** the reader mints a read token per invocation, limited to the run's two KBs, and
  revokes it at the end. No token, key or password is written to this folder.

## Not in this run (next, if the user wants)

- **The scale arm on luna** (the `--scale large` corpus). It's the one that cost ≥ $75 on gpt-4o.
  J4 found gpt-4o governance made 161 false merges there.
- **The current corpus** (39 files at HEAD) as the lab's forward baseline.
- **Corrections, curation, the procedure and the request record** on the luna graph.

---

## Results (appended after the run, 2026-10-13)

### What ran

All times are UTC.

| Step | When | Result |
|---|---|---|
| Workspace | 19:26:53 | "Northstar Lab (gpt-6-luna)" `01a136bb-65c0-7690-a6f1-2e426588845f`: gpt-6-luna, effort `low`, text-embedding-3-small. The user added the OpenAI key in the UI. Utopia's settings test passed (chat OK, embed dim 1536). Default Workspace was checked before and after: gpt-4o, effort unset |
| 1 · smoke | 19:41–19:47 | `products.csv` in a scratch KB: extraction done, 11 entities, 16 open and 16 typed facts (gpt-4o: 9 / 9 / 9). Settled in about 2.5 minutes, 0 failed jobs |
| 2 · KBs | 19:47 | base `01a136ce-24cb-7873-b1cd-50fdb6ec8999`, missing-contract `01a136ce-28f0-7952-baba-76b618339f6b`. Settings match the gpt-4o bases field for field. Ontology imports are the same files, hashes and order (`schema-org.ttl` 320938f094…, `w3c-org.ttl` 3e01f89a17…) |
| 3 · upload | 19:48:05–19:48:07 | 17 + 14 files, every response `"error": null` |
| 4 · settle | 19:57:44 | Both KBs settled in about 10 minutes (gpt-4o: 6), with 0 failed jobs and 0 failed documents |
| 5 · snapshot | 19:58 | `snapshot/` (the same set as 09-28, plus `*.counts.json`; drops and review summary as JSON) |
| 6 · arm A | 19:59:25–19:59:51 | 10 of 10 answered |
| 7 · arm B | 20:01:20–20:17:52 | Probes pass (B1: 11 tools, B2: 9; connected; 0 denials). B1 + B2 r1 in `arm-b/`, B2 r2 and r3 in `repeats/r2`, `repeats/r3` |

**Plan deviation: the scratch KB could not be deleted.** Utopia made it the new workspace's
default KB, and default KBs are undeletable (422 `default_kb_undeletable`). It holds only
`products.csv`. The reader's tokens are limited to the two run KBs, so the reader can't reach it.
Arm A asks each KB directly. Left in place.

### Pipeline (step 4)

| KB | Model | Entities | Open facts | Typed facts | Merges | Reviews (kept / merged / pending) | Dated by content / none |
|---|---|---|---|---|---|---|---|
| base | gpt-4o | 172 | 124 | 144 | 15 | 229 / 15 / 5 | 12 / 5 |
| base | **luna** | 258 | **829** | 268 | 14 | 545 / 14 / 17 | 11 / 6 |
| missing-contract | gpt-4o | 192 | 124 | 141 | 8 | 192 / 8 / 4 | 9 / 5 |
| missing-contract | **luna** | 232 | **836** | 248 | 7 | 513 / 7 / 18 | 8 / 6 |

- **Open facts are almost 7×.** gpt-4o's extraction dropped most CSV rows
  (`docs/upstream/utopia-read-contract.md` §5); luna keeps them.
- **Dating:** the one difference is `discount_requests.csv`, which gpt-4o dated (content) and luna
  left undated.

### Arm A: Utopia's own chat, now on luna

Luna answered every question from the passages Utopia fetches up front, with **0 tool steps**,
in 2–3 s each. gpt-4o took 2–6 graph-only steps per question. So arm A changed its retrieval
path as well as its model.

| Id | Expected | gpt-4o | luna |
|---|---|---|---|
| S01 | APPROVE_WITH_AUTHORIZATION, Michael | ✗ | ◐ eligibility ≠ authority, but no approver named |
| S02 | REJECT_OR_ESCALATE | ✗ | ✓ 18% is above the 15% cap |
| S03 | REVIEW_REQUIRED | ✗ | ◐ won't transfer the NS-500 exception; says "No" |
| S04 | APPROVE (2025 policy) | ✗ | ✗ cites DR-8104 but "can't confirm" |
| S05 | REQUEST_EVIDENCE | ✗ | ◐ won't decide; asks for Deal Desk confirmation and a "current 2026 approval policy" |
| S06a | 15% | ✗ | ✓ |
| S06b | 10% | ✗ ("100%") | ✓ and the cut-over date |
| S06c | none | ✓ | ✓ |
| S07 | the exception under the MSA, not hearsay | ✓ | ✓ MSA Schedule B; eligibility only |
| S08 | the three ids are one customer; Acme Industrial is different | ◐ | ✓ all three linked; Acme Industrial separate (CRM-2091, C-1044) |
| **✓ / ◐ / ✗** | | **2 / 1 / 7** | **6 / 3 / 1** |

### Arm B: the blind Opus reader

**B1 (all tools): 9 ✓ / 1 ◐ / 0 ✗, the same as gpt-4o.**
- The ◐ is S03 both times: it won't transfer the exception, but routes the request to VP sign-off.
- With the text tools, the reader doesn't depend on the graph.

**B2 (graph only), per question.** Each cell lists runs r1, r2, r3.

| Id | gpt-4o pre-correction | luna | What changed |
|---|---|---|---|
| S01 | ◐ ◐ ◐ | ◐ ✓ ✓ | The VP band (>10–20%) is now in the graph, so r2 and r3 name Michael with the band |
| S02 | ✓ ✓ ✓ | ✓ ✓ ✓ | |
| S03 | ◐ ◐ ◐ | ◐ ◐ ◐ | |
| S04 | ✓ ✓ ✗ | ✗ ✗ ✓ | Right only where the reader found the 2025 "up to and including 15%" (r3, after 2 `changes` calls) |
| S05 | ◐ ◐ ◐ | ✓ ◐ ✗ | See the hearsay finding below |
| S06a | ✓ ✓ ✓ | ✓ ✓ ✓ | |
| S06b | ✓ ✓ ✓ | ✓ ◐ ✓ | r2 hedges: "points to 10%", "never states that percentage directly" |
| S06c | ✓ ✓ ✓ | ✓ ✓ ✓ | |
| S07 | ✓ ✓ ✓ | ✓ ✓ ✓ | |
| S08 | ◐ ◐ ◐ | ✓ ✓ ✓ | All three ids linked through the shared DUNS and address; Acme Industrial kept separate |
| **✓ / ◐ / ✗** | 6/4/0 · 6/4/0 · 5/4/1 | **7/2/1 · 6/3/1 · 8/1/1** | |

**Totals over the three runs:**

| | ✓ | ◐ | ✗ |
|---|---|---|---|
| luna | 21 | 6 | 3 |
| gpt-4o | 17 | 12 | 1 |

### Mechanism: the reader stopped digging through `changes`

`scripts/measures.py` counts per-entity `changes` calls. It reproduces the gpt-4o pre r1 row of
`repeats/notes.md` exactly (S01 = 9, S02 = 9, S03 = 4, S04 = 8).

| | S01 | S02 | S03 | S04 |
|---|---|---|---|---|
| gpt-4o pre r1 | 9 | 9 | 4 | 8 |
| luna r1 | 0 | 0 | 0 | 0 |
| luna r2 | 0 | 0 | 0 | 1 |
| luna r3 | 0 | 0 | 0 | 2 |

- **Why:** on luna, `entity_facts` returns the policy terms directly, so the reader no longer
  recovers them from the change log. That fixes S01 in two of three runs.
- **What it costs:** the 2025 policy's 15% limit is still reached only through `changes`, and S04
  now fails in the runs that don't dig. That's the same mechanism as f13.

### Finding: luna extracts hearsay as fact

The account plan in the missing-contract corpus says:

> "Acme negotiated preferential NS-500 pricing in the 2025 agreement — I believe it's 15% … Worth
> confirming with Deal Desk before the Q3 order."

**Luna's graph holds this as facts at 100% confidence, undated:**
- `preferential NS-500 pricing —was→ 15%`
- `Acme —negotiated→ preferential NS-500 pricing`
- `preferential NS-500 pricing —confirming→ Deal Desk`

Each fact keeps its source quote in the export (`snapshot/missing-contract.ttl`). **gpt-4o's graph
holds none of it** (no "Deal Desk", "preferential" or "believe" in its export).

**How the three B2 readers read it:**
- r1 read it right: "Deal Desk was still confirming it".
- r2 read it right: "the Deal Desk was to confirm".
- **r3 read `confirming → Deal Desk` as "which the Deal Desk confirmed"**, didn't ask for the
  contract, and routed DR-9001 to Michael. Graded ✗.

So richer extraction takes S05's trap from the documents into the graph. A graph-only reader now has
to catch hedged statements. Before, it simply didn't see them.

### Identity (graph, no model; `scripts/identity.sql`)

**Luna:**
- **Merges:** governance made 14, all same-name duplicates or aliases, including CRM-2091 into Acme
  Industrial. It did **not** merge Acme Mfg. Holdings into Acme Manufacturing.
- **The identifiers are attribute values:**
  - `account_id = CRM-2048` on Acme Manufacturing;
  - `erp_customer_id = C-1001` on Holdings;
  - both carry DUNS 04-812-7730;
  - ACME-MFG-2025 is linked only from "Schedule B".

**gpt-4o:**
- It merged Holdings into Acme Manufacturing (governed, 0.90).
- It also merged "Acme NS-500" into the NS-500 product.
- CRM-2048 and ACME-MFG-2025 were unreachable (09-28 step 6).

Luna's identity is right, but implicit. The B2 readers resolved it from shared values in 3 of 3
runs, where gpt-4o's merge-based graph gave ◐ in 3 of 3.

### Cost

| Item | Cost |
|---|---|
| **Reader** (Claude Code plan) | **$11.84**: B1 $1.72; B2 $3.20, $3.64 and $3.16; probes $0.12 |
| **Turns** | B1 92; B2 199, 247 and 210 (gpt-4o B2 pre r1: 248) |
| **Utopia** (OpenAI) | **Not measured**, as pre-registered. It stores no token usage, and its logs go to the user's terminal. The pipeline ran for about 10 minutes plus the 2.5-minute smoke test; at luna's prices that's an estimate of well under $1 |

### What this says

1. **Arm A changes most** (2 → 6 ✓). That's Utopia's own chat on a current model. The chat loop
   also changed shape: it now answers from passages fetched up front, with no tool steps. So arm A
   measures the model and its retrieval path together. It still doesn't measure the graph.
2. **B1 is unchanged** (9 / 1 / 0). A strong reader with text access doesn't need a better graph
   on this corpus.
3. **B2 improves, but not cleanly** (✓ 17 → 21, ✗ 1 → 3).
   - The graph now carries what used to be dug out of `changes` (the bands) and what used to be
     missing (the identifiers as values).
   - It also carries hedged statements as 100% facts. The new failures are S04, which still depends
     on the dig, and S05, which is hearsay.
4. **For the lab:** luna is a more realistic baseline, and the foundation/OWM boundary holds.
   - No arm reached 10 of 10.
   - The remaining misses are the OWM's work: which policy applies on a date, who holds authority,
     and whether evidence is confirmed or claimed.
   - The graph getting richer moved one trap (S05) from "absent" to "present but hedged". That makes
     the provenance check on the OWM side matter more, not less.

These are provisional first-read grades. The user's grades belong in the Ledger's `grades`
collection.
