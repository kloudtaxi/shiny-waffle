> **STATUS: PRE-REGISTERED 2026-10-13. Nothing has run yet.** The plan below is fixed before
> any knowledge base is created. Results get appended below it, and the plan stays unchanged.

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
