> **STATUS: RESUMED 2026-09-28**. B2 repeats (n=3 on the corrected graph) are done; see
> `repeats/notes.md`. B2c is stable (4/3/3, 4/3/3, 4/4/2); the pre-correction B2 run is the
> outlier, which **corrects** the "reader-strategy variance" reading in `correction/comparison.md`.
> Open decision: pre-correction repeats to test hypothesis f13. Still open: steps 7–8, the
> curation arm and the scale arm. Pre-correction state: `snapshot/`, MCP `as_of: 2026-09-28T17:25:00Z`.

# Run 2026-09-28 · Utopia baseline (arm A)

Procedure: `docs/experiment-runbook.md`, steps 0–6. Scoring (steps 7–8) is not done yet.

## Inputs

| Item | Value |
|---|---|
| Lab commit | `976d119`. The working tree also has the new `CLAUDE.md` and runbook, neither of which affects the dataset |
| Dataset | seed `20260923`, scale `small`. `northstar check` is coherent (8 scenarios, 17 artifacts), and `dataset/` matches a fresh build byte for byte (checked 2026-09-27) |
| Utopia | `dev` @ `aad5b06`, API `http://localhost:1516/api/v1` |
| Models | Per `_owm-local` notes: `gpt-4o-mini` (chat and extraction) and `text-embedding-3-small`. **Not verified** in this run: the settings table also holds API keys, so it was not read |
| Workspace | Default Workspace `01a068b4-5939-7422-a9e2-4e7f29516491` |

## Knowledge bases

| KB | Id | Files |
|---|---|---|
| Northstar Industrial Systems | `01a0e787-41f4-71b2-83fb-22aefb8dd650` | 17: `dataset/evidence/{structured,documents}/*` |
| Northstar — missing contract evidence | `01a0e787-457c-7f50-a8f1-e33beb27dfb3` | 14: `dataset/evidence-variants/missing-contract-evidence/{structured,documents}/*` |

Both KBs were created 2026-09-28 10:19 UTC and uploaded at 10:20 UTC, through the REST API
(multipart upload, one file per request).

Settings are the defaults plus the ontology packs:

- `ontology_packs`: `schema-org` then `w3c-org`
- `ontology_lang` en; `auto_extend_ontology`, `auto_type_resolution`, `governance` and
  `materialize_inferences` all true; inference interval 60 min; visibility open
- `data_description`, `data_conventions` and `data_questions` left **empty**, so Utopia is
  not told which questions the base must answer

## Controls applied

- Fresh KBs. The existing *Sovera OWM* KB holds the design docs describing the scenarios, so
  it was not used.
- Not uploaded: `MANIFEST.yaml`, `answer-key/`, `evaluation/`, `truth/`, `owm/`, `docs/`,
  `site/`, `README.md`, `DATASET.md`.
- No business rules, mappings, manual merges, or Review-queue actions.
- Each question asked verbatim, in a new conversation, with no follow-ups (step 6).

## Step 1: smoke test

A scratch KB with `products.csv` only was created at 10:19 and deleted once the check
finished. It was ready and graphed in about a minute, with 9 entities, 9 open facts, 9 typed
facts, and no failed jobs, so extraction works on the current model config.

**Early observation:** from `products.csv` the open layer kept only
`<product> has a list price of $N`. The `product_id`, `sku` and `category` columns produced no
facts. Watch whether SKUs like `NS-500` in `discount_requests.csv` still resolve to
*NS-500 Industrial Controller* in the full KB.

## Step 4: pipeline

Both KBs settled **6 minutes** after upload (10:20 to 10:26 UTC). Every document is `ready`
and `graph_status = done`. There were no failed jobs in either KB; the one `align_types`
failure (`Not found`) belonged to the deleted scratch KB.

| KB | Entities | Open facts | Typed facts | Merges | Identity reviews (kept / merged / pending) |
|---|---|---|---|---|---|
| base | 172 | 124 | 144 | 15 | 229 / 15 / 5 |
| missing-contract | 192 | 124 | 141 | 8 | 192 / 8 / 4 |

Counts are live (non-invalidated) rows at 10:30 UTC. Full tables are in `snapshot/`.

### Findings

1. **Every CSV lost part of its extraction to a truncated model reply.** All six CSVs have a
   `truncated_reply` drop: "the open reply was cut off; kept up to the last complete item".
   A dense table exhausts the completion budget, and the rows after the cut produce no
   facts. No Markdown document was truncated. Structured evidence is the *least* completely
   extracted part of the corpus, which is the opposite of what doc 02 §6 assumes. (Step 7
   should confirm which rows survived, especially Sarah → Michael in `employees.csv` and
   DR-9001 / DR-8104 in `discount_requests.csv`.)
2. **Document dates.** All 11 Markdown documents were dated from their own text
   (`doc_time_source = content`), using the `created:` / `sent:` header rather than
   `effective_from:`. The policies are dated 2024-12-10 and 2025-12-08, not 2025-01-01 and
   2026-01-01. Five of the six CSVs have **no date**. `discount_requests.csv` was dated
   **2025-01-06**, the first row's request date, which is applied to the whole log
   (including DR-9001 of 2026-09-23).
3. **Identity (base KB).** *Acme Manufacturing* was merged into *Acme Mfg. Holdings*, which
   is the CRM↔ERP link S08 needs. *Acme Industrial Supply Co.* was **not** merged into it,
   which is correct.
4. **Identity (missing-contract KB).** *Acme Manufacturing* and *Acme Mfg. Holdings* were
   **not** merged, even though the CRM and ERP rows share DUNS `04-812-7730` and a street
   address. The base KB's merge most likely came from the MSA's "Acme Mfg. Holdings d/b/a
   Acme Manufacturing" sentence, not from the shared identifiers. So removing the contract
   also removed the identity resolution, which S05 didn't set out to test. Single run;
   confirm in step 7.
5. **Questionable merges (base).** *Acme NS-500* was merged into the product *NS-500
   Industrial Controller*. If "Acme NS-500" was the exception's name, Acme's exception has
   been conflated with the product (trap: product scope, S03). Separately, *NS-Cloud* was
   merged into the SKU entity *NS-CLOUD*, but no merge with *NS-Cloud Operations Suite*
   appears. The product may be split.
6. **Extraction drops.** There are 44 drop rows in base. The most common are
   `object_undeclared` (a statement's object was not a listed thing, so it was kept as a
   value) and `unknown_ref`. `erp_orders.csv` alone has 21 `name_not_in_text` drops.
7. **The Review queue asks a human only about background SKU codes** (`NS-830-EQU` vs
   `NS-880 Commissioning Service` and similar, at scores 0.63–0.66). Nothing about Acme,
   authority or the exceptions reached a human, so every identity decision that matters
   here was made automatically (`governed|0.90`–`0.95`).

## Step 5: snapshot

`snapshot/` holds:

- `*.ttl`: the RDF export (Turtle) for each KB
- `*.ontology.json`: the ontology, mostly the imported packs
- `*.graph-overview.json`
- `*.documents.tsv`, `*.extraction-drops.tsv`, `*.entity-merges.tsv`, `*.pending-reviews.tsv`

All were taken after settling and before any question was asked.

## Step 6: the scenarios

Ten questions (`questions.tsv`) were asked 10:27–10:31 UTC through `POST /kbs/{id}/chat`
(Utopia's own chat agent), each in a new conversation, verbatim, with no follow-ups. S05
went only to the missing-contract KB, and S06 was split into three dated probes. Each
`answers/<id>.*` holds the raw SSE stream (`.sse`), a readable answer with the tool trace
(`.md`), and the stored conversation (`.conversation.json`, which has message text only, no
tool outputs). One-line answers are in the `utopia_answer` column of
`scenario-scorecard.csv`.

**This is a first read, not the step 8 scoring.**

| Id | Expected | Utopia said | Tools used |
|---|---|---|---|
| S01 | APPROVE_WITH_AUTHORIZATION (Michael) | Cannot determine; no approver named | graph only |
| S02 | REJECT_OR_ESCALATE | Cannot determine | graph only; wrong time axis |
| S03 | REVIEW_REQUIRED | Cannot determine | graph only; wrong time axis |
| S04 | APPROVE | Cannot determine | graph only |
| S05 | REQUEST_EVIDENCE | Cannot determine; does not name the missing contract | graph only; wrong time axis |
| S06a (2026-09-23) | 15%, EXC-ACME-NS500-15 | No facts | graph only |
| S06b (2024-10-01) | 10%, EXC-ACME-NS500-10 | **"100%"**, valid 2023-04-01 to 2025-03-31 | graph only |
| S06c (2022-10-01) | none | No facts (right, but only because nothing is dated then) | graph only |
| S07 | EXC-ACME-NS500-15 under MSA-ACME-2025, not hearsay | **Correct**: NS-500-only, 2025-04-01 to 2028-03-31, supersedes 10%, cites the exception document | `search_chunks` + `get_document` |
| S08 | CRM-2048 = C-1001 = ACME-MFG-2025; Acme Industrial is different | C-1001 found; CRM-2048 and ACME-MFG-2025 not found; Acme Industrial is different | graph only |

It never fabricated a decision, but it also never reached one. It said "cannot determine"
eight times, gave one correct explanation (S07) and invented one value (S06b).

### Why: agent behaviour

1. **It barely reads documents.** Nine of ten answers used only graph tools. The one that
   searched text (S07) is the one that was right. The graph is too thin to answer from alone
   (below), and the agent doesn't fall back to text.
2. **It confuses Utopia's time axes.** In S02, S03 and S05 it passed the question's date (or
   an arbitrary 2023-10-01) as `as_of`, which is *record* time: "what the base held then".
   Nothing was recorded before 2026-09-28, so every lookup returned 0 facts. This is the
   `at` vs `as_of` confusion Utopia's MCP manual warns about.
3. **It invented a number.** In S06b the only fact returned was "Acme may receive NS-500
   Industrial Controller, valid 2023-04-01 to 2025-03-31", which carries no percentage, and
   the answer says "100%".

### Why: graph state (checked in SQL after the questions)

4. **Every reporting line is inverted.** The graph says Michael Torres "reports to" Sarah
   Chen *and* to all seven other account executives, and David Morgan (CRO) "reports to"
   Michael. Every `reports to` edge points from manager to report. Any composition over this
   graph would find the wrong approver, and it would find it confidently. It probably comes
   from the org chart's indented list; check in step 7 which document the edges cite.
5. **There are no percentages on Acme's exception facts.** Acme has "is eligible for
   discounts of up to → *NS-500 Industrial Controller*" (undated) and "may receive → *NS-500
   Industrial Controller*" (2023-04-01 to 2025-03-31), with no qualifiers. The 15% and 10%
   values never reached the graph. They exist only in text, which is why S07, the one
   text-reading answer, could state them.
6. **The stale exception is dated and the current one isn't.** A date-filtered lookup (`at`)
   excludes undated facts, so on any 2026 date the graph shows *no* exception, while on a
   2024 date it shows the old one. That's the superseded-fact trap in an unexpected form:
   history survived, the present didn't.
7. **Most of the evidence is undated in the graph.** Sarah Chen's facts (role, and the inverted
   reporting line) have no validity, so "facts about Sarah at 2026-09-23" returns 0
   (S01, S04). There is **no** "Sarah owns Acme" fact, and no Sarah↔Michael link in the right
   direction.
8. **The source-system ids aren't entities.** `CRM-2048` and `ACME-MFG-2025` return no
   entity. The CRM↔ERP merge (Acme Manufacturing into Acme Mfg. Holdings) exists as `known as`
   names, not as id links, so S08 can't be answered from ids.

## Not done in this run

Steps 7–8 (fact checklist and scoring), arm B (a stronger agent over MCP) and arm C
(business rules). The first read suggests arm B is the most informative next step: findings
4–8 are **foundation** gaps (extraction and temporal modelling) and findings 1–3 are
**agent** gaps. Separating them is exactly what arm B is for.

## Reframing after reading Utopia's design record (2026-09-28)

Sources: `docs/design/chat-and-mcp.md` and `docs/decisions/0046-the-app-surface-is-mcp.md` in
Utopia `dev` @ `aad5b06`.

- **Utopia says the app surface is MCP.** "MCP is where an application on this knowledge gets
  built — in the customer's own agent platform, language and sandbox, against the read
  contract. This product hosts no app center, no catalog and no sandbox of its own" (0046).
  An OWM that sits above Utopia *is* such an application, so the OWM↔foundation seam is
  Utopia's declared read contract: MCP `structuredContent` plus the RDF export (0020). That
  matches doc 01's rule that the OWM contract must not depend on Utopia internals.
- **So arm A measured Utopia's reference agent, not the foundation.** The chat and MCP
  share one tool implementation (`tools.rs`). The chat loop forces a tool call, then "the
  budget withdraws the tools and orders an answer", and "termination is structural and
  guarantees a decision, not a correct one" (0042). That fits the short "cannot determine"
  answers. Arm B, the same tools behind a capable reader, is therefore the primary
  measurement of the foundation, not an optional extra.
- **Timed questions are pushed onto the graph.** "Retrieval… neither takes `at`", so text
  search can't answer "on 2026-09-23" by itself. A dated read has to go through
  `entity_facts` with `at`, which excludes undated facts, and in this KB the current Acme
  exception and every reporting line are undated (step 6 findings 6–7). The tool design and
  the extraction gaps compound.
- **Caveat for OWM design:** "the layer an app would read is in motion. Extraction writes
  only the open graph, and typed facts come from alignment, whose cuts are landing as this
  is written" (0046). This run agrees: the substance was in the open layer as phrases
  (`reports to`, `may receive`, `is eligible for discounts of up to`), while the typed layer
  held mostly `known as` names. An OWM built now should map open-graph phrases into its own
  ontology through the read contract, and should not bind to Utopia's typed layer.

### Proposed arm B design

- **B1, all tools:** the reader may use any MCP tool, including `search_chunks` and
  `get_document`. This measures foundation-as-retrieval plus a strong reader.
- **B2, graph only:** `find_entities`, `entity_facts`, `neighbors`, `timeline`,
  `paths_between` and `changes`; no text tools. This measures what the foundation has
  actually *modelled*.
- **The B1 − B2 gap** is what is knowable only as text: evidence Utopia retrieved but didn't
  model. Those are the rows that belong to the OWM or to better extraction.
- **The reader must be blind.** This analysis session has read the truth and the answer key,
  so it can't be the reader. Run headless `claude -p` from an empty directory with only the
  Utopia MCP server (`--strict-mcp-config`), all built-in tools disallowed, a read-only
  personal token limited to the two Northstar KBs, and the full stream-JSON transcript saved
  for each question.

## Review queue check (2026-09-28, before arm B)

Saved as `snapshot/*.review-{summary,agent,duplicates,merges}.json`. The agent list is capped
at 200 items per KB, so the base KB's 224 decisions are not all in the file. Live facts are
still 268 (base) and 265 (missing-contract), unchanged since arm A.

### What the Review page counts

The **Duplicates** tab and the **Agent** tab's open proposals are the same items: identity
candidates that Utopia's governance agent (ADR 0025) looked at and left for a human.

| KB | Open | Decided automatically, no human (keep / merge) |
|---|---|---|
| base | 5 | 224 (208 / 16) |
| missing-contract | 4 | 199 (191 / 8) |

**The open items (low stakes).**

- **Base:** all 5 are background SKU codes (`NS-830-EQU`, `NS-400-EQU` and similar). The
  agent is "unsure" on 2, including whether `NS-830-EQU` is the NS-500 (correct answer: keep
  separate). It proposes merging `NS-830-EQU` with an identically named `NS-830-EQU`, but
  didn't apply that.
- **Missing-contract:** 3 SKU items, plus **`Michael Torres ?= Michael Torres`**. The agent
  proposes *keep separate* (70%): "Record A has no facts, and there may be multiple
  individuals". That's wrong; there is one Michael Torres, and S05's approver is split across
  two entities.

**The decisions nobody was asked about (high stakes).** These were applied at 90–95%
confidence without a human:

| Decision | KB | Truth | Scenario hit |
|---|---|---|---|
| keep *NS-CLOUD* ≠ *NS-Cloud Operations Suite* (95%, "'Operations Suite' suggests a specific product variant") | both | same product (NS-CLOUD is its SKU) | S03 product scope |
| keep *Acme Industrial* ≠ *Acme Industrial Supply Co.* | both | same customer (CRM-2091 / C-1044) | S08 |
| keep *Acme Mfg. Holdings* ≠ *ACME Manufacturing* ("Different names and contexts suggest they are distinct entities") | missing-contract | same customer | S05, S08 identity |
| keep *NS-500 controller* ≠ *NS-500 Industrial Controller* ("'Industrial' is a specific qualifier for a different product") | missing-contract | same product | S05 |
| merge *NS-500 Industrial Controller* ← *NS-500 controller* | base | correct | |
| merge *Michael Torres* ← *Michael Torres*; keep *Acme Industrial* ≠ *Acme Mfg. Holdings* | base | correct | |

**Pattern:** the adjudicator decides identity from **name strings**, not shared identifiers.
It never cites DUNS, address, SKU or email, even where the CSVs share them, and it is
confident either way. Identity that only a shared identifier could settle (SKU = product,
CRM name = ERP legal name) was decided *against*, at 90–95%, and filed as automatic.
Identity survived in the base KB only because the contract text states it in words ("d/b/a").
It is also the same model's judgement graded by that model's own confidence (0042's "a
heuristic judged by the model it corrects").

**For the OWM:** "what needs human confirmation?" (doc 01) gets a concrete answer here. The
human queue held the *low*-stakes items, and the high-stakes identity calls were auto-applied.
A queue governed by the model's confidence routes by how sure the model is, not by what the
decision affects.

## Arm B: blind Opus reader over MCP (started 2026-09-28)

The graph is unchanged from arm A, and no Review-queue action was taken. The runner is
`arm_b.py` in the session scratchpad; the full setup is in `arm-b/setup.json`.

**Reader.** `claude -p` headless with `--model claude-opus-5-5`, one process per question, run
from an **empty directory**, with these flags:

- `--tools ""` (no built-in tools)
- `--strict-mcp-config` (Utopia's MCP endpoint for the question's KB only)
- `--setting-sources project` (skips user-level hooks and plugins)
- `--no-session-persistence` and `--max-turns 40`

The system prompt was **replaced**, verbatim: "You answer questions about an organization.
Your only source of information is the organization's knowledge base, which you can reach
through the tools provided. Answer the question you are asked." The question is the same
verbatim text as arm A (`questions.tsv`).

**Token.** A new personal token with `read` scope and `kb_ids` limited to the two Northstar
KBs, so the *Sovera OWM* KB is unreachable. It expires in 2 days, was held in process memory
only (passed through `UTOPIA_MCP_TOKEN`, which the MCP config expands), and was revoked when
the invocation ended.

**Variants.**

- **B1:** all 11 MCP tools: `search_chunks`, `get_document`, `search_docs`, `find_entities`,
  `entity_facts`, `paths_between`, `neighbors`, `timeline`, `list_rules`, `rule_matches`,
  `changes`.
- **B2:** the same minus the two text tools (`search_chunks`, `get_document`).

`search_docs` (Utopia's own manual) stays in B2, since it holds no corpus text.

**Probe (`arm-b/probe.jsonl`, $0.07).**

- The init message lists only the 11 `mcp__utopia__*` tools, and the MCP server is
  `connected`.
- The reader reported no instruction files, memory or project context.
- It saw two standard blocks: the account email reminder, and the environment block. The
  working-directory path in that block contains the repo name (`shiny-waffle`). That's a
  name, not an answer; noted as residual context.
- Its one `find_entities` call returned 8 "Northstar" entities.

### Arm B: results (2026-09-28)

- **B1:** all 10 runs completed, $1.45, 85 turns. No permission denials; 11 tools in the
  reader's context.
- **B2, first attempt (discarded):** the text tools were outside the allowlist but still
  *visible*, so the reader was refused 5 times, knew documents existed, and spent 31 turns.
  Moved to `arm-b/B2-discarded/` with a README.
- **B2, rerun:** text tools hidden with `--disallowedTools`. A probe confirmed 9 tools in
  context and 0 denials. All 10 runs completed, $3.19, 248 turns.
- **Tokens:** each invocation minted its own token and revoked it at the end. Four tokens
  in all: two probes, the B1 + B2 run and the B2 rerun. None remain active.

The first-read comparison and its implications are in `comparison.md`.

**A correction verified from the MCP transcripts:** the inverted `reports to` edges (step 6
finding 4) are what Utopia's read contract actually serves (`entity_facts`, `changes`, citing
`organization_chart.md`). B2's reader silently reversed them in its answer.

## Correction run (2026-09-28)

**Goal:** measure what human review of *identity* is worth. Apply the corrections a reviewer
with access to the source systems would make through Utopia's Review surface, then rerun B1
and B2 unchanged. The script is `correction.py` (session scratchpad); the log is
`correction/actions.jsonl`; the post-correction snapshot is `correction/snapshot/`.

The corrections were applied **2026-09-28 17:25:39–17:25:41 UTC**, in place. The
pre-correction graph stays readable with MCP `as_of: 2026-09-28T17:25:00Z` (record axis),
and is also in `snapshot/`.

**Scope: identity only.** The rule: answer every open Review item; on scenario-relevant
entities (Acme*, NS-500, NS-Cloud, Sarah, Michael, the Acme and Acme Industrial source ids),
overturn wrong automatic decisions and add merges that were never compared. Each action
carries a rationale citing the source row.

**Not touched, deliberately:**

- *Fact* errors: the inverted `reports to` edges, the missing VP Sales band, the missing
  percentages. No Review item surfaced them, and fixing them is curation, not review.
- "Acme NS-500": an extraction artefact from the discount-request rows that mixes customer
  and product. It has no correct identity; the gap is that discount requests have no entity.
- BlueRiver (CRM-2051) and Cedar (CRM-2063), and the background SKU↔name keeps outside the
  queue: not scenario-relevant.

**Actions: 24 attempted, 18 applied, 6 refused.**

| KB | Action | Items |
|---|---|---|
| base | answer proposal | `NS-830-EQU` = `NS-830-EQU` → merge (accepted) |
| base | overturn auto-keep | NS-CLOUD = NS-Cloud Operations Suite; Acme Industrial = Acme Industrial Supply Co. |
| base | manual merge | NS-500 Industrial Controller twin; C-1001 → Acme Mfg. Holdings; C-1044 → Acme Industrial Supply Co.; `sarah.chen@…` → Sarah Chen; `michael.torres@…` → Michael Torres |
| missing-contract | answer proposal | Michael Torres = Michael Torres → merge (overrode the agent's 70% keep); NS-840-SER ≠ NS-500 controller → keep (accepted) |
| missing-contract | overturn auto-keep | Acme Mfg. Holdings = ACME Manufacturing; NS-500 controller = NS-500 Industrial Controller; NS-CLOUD = NS-Cloud Operations Suite; Acme Industrial = Acme Industrial Supply Co. |
| missing-contract | manual merge | C-1001 and CRM-2048 → Acme; C-1044 → Acme Industrial Supply Co.; `michael.torres@…` → Michael Torres |

The **6 refusals** were `422 "cannot keep an agent decision that is superseded"`. After the
first human answer in each KB, Utopia's governance agent re-examined the related open pairs
**using that answer as a precedent** (ADR 0025) and settled them itself at 17:25:43. All six
came out *keep*, which is correct. Both queues ended empty. The base KB records 2 overridden
and 1 accepted; missing-contract records 5 overridden and 1 accepted.

**Resulting identities.** Live facts are 267 (base) and 264 (missing-contract), down one each
from deduplication. Merges went from 15 to 23 (base) and from 8 to 17 (missing-contract);
the `*.entity-merges.tsv` line counts include a header and a "(N rows)" footer.

- **base:** Acme Industrial Supply Co. is known as Acme Industrial, C-1044 and CRM-2091. NS-500
  Industrial Controller is known as NS-500 and NS-500 controller (and "Acme NS-500", the
  earlier auto-merge, left in place). NS-CLOUD is known as NS-Cloud and NS-Cloud Operations
  Suite.
- **missing-contract:** ACME Manufacturing is known as Acme Manufacturing and Acme Mfg.
  Holdings. Michael Torres is one entity, known by his email. NS-500 and NS-Cloud are single
  products.

### Finding: a human merge can erase the identifier it was meant to connect

After the manual merges, **`C-1001` (both KBs), `CRM-2048` (missing-contract) and Michael's
email (base) are no longer findable**. `find_entities` matches `canonical_name` or a name
fact, and these ID entities, created from CSV rows, had a canonical name but **no name
fact**, so the merge carried nothing across. `C-1044` survived because a document attested
it as a name.

This appears to diverge from Utopia ADR 0041 decision 1: "`entities.canonical_name` … is also
one of the entity's name facts", with merges carrying names as name facts. The effect is that
the correct merge moved the facts (the orders now attach to Acme), but an ID that used to be
findable now isn't. Worth raising upstream.

It was **not** worked around. Adding the IDs through `remember` would put the S08 answer into
the KB as text and contaminate B1.

### Correction run: results

B1 and B2 were rerun on the corrected graph (17:27–17:38 UTC). All 20 runs completed with 0
permission denials, and the token (`northstar-arm-b-corrected-2026-09-28`) was revoked.

- **B1:** 9 / 1 / 0, unchanged. $1.49, 86 turns.
- **B2:** 4 / 3 / 3, down from 6 / 4 / 0. $2.71, 229 turns.

The B2 drop is **reader-strategy variance, not the correction**. Before, it retrieved quotes
through per-entity `changes` calls (about 10 per question); after, it made one generic call.
The only genuine correction effect is S08's regression, from the lost `C-1001` name. Details
are in `correction/comparison.md`. The headline: identity review bought nothing measurable,
and repeat runs are needed before any B2 before/after claim.
