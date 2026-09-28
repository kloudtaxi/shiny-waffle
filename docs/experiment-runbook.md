# Running the Northstar experiment against Utopia

A step-by-step runbook for doc 02 §§6–9: load the Northstar evidence into a live Utopia
instance, ask the eight scenarios, fill in the evaluation sheets, and find where the knowledge
foundation stops and the OWM has to start.

Credentials are **not** in this file. They live in `_owm-local/utopia-getting-started.md`,
which is gitignored. The commands below read them from the `UTOPIA_EMAIL` and
`UTOPIA_PASSWORD` environment variables.

---

## TL;DR

| # | Step | Time |
|---|---|---|
| 0 | `uv run northstar check`, then start a run folder and copy the evaluation sheets into it | 2 min |
| 1 | Pre-flight: run a one-document smoke test so a broken model config can't fail silently | 10 min |
| 2 | Create two **fresh** KBs: *Northstar Industrial Systems* and *Northstar — missing contract evidence* | 2 min |
| 3 | Upload the **17 evidence files only** (not `MANIFEST.yaml`), and the 14-file variant into the second KB | 2 min |
| 4 | Wait for the pipeline, then check failed jobs, drops, and whether each document got a date | 30–60 min |
| 5 | Snapshot what Utopia knows: RDF export, ontology, review queue | 5 min |
| 6 | Ask each scenario verbatim, **one new conversation per question**. S05 goes only to the variant KB | 30 min |
| 7 | Fill `fact-checklist.csv`: for each fact, is it in the graph, only in text, or absent? | 45 min |
| 8 | Score each answer against the rubric and write up the candidate OWM capabilities | 30 min |

The `owm_answer` column **stays empty** in this run. No OWM exists yet. Doc 02 §8 says to build
it only after you have seen what Utopia gets wrong, and this run is how you see that. The
oracle's `answer-key/` is the expected result, not an OWM answer, so don't copy it into that
column.

---

## 1. What this run measures

The unit of evidence is a row in `fact-checklist.csv` where **Utopia knows X and Y but not the
organizational implication Z** (doc 02 §7). Each such row is a candidate OWM capability, and
each row where Utopia *does* compose Z moves an `owm/ontology.yaml` tag from `owm` to
`foundation`.

There are three things you could be measuring. Keep them apart and record which one each
answer came from:

| Arm | System under test | Question it answers |
|---|---|---|
| **A: Utopia baseline** (this runbook) | Utopia's own chat agent over its own graph, with no rules, mappings or human review | What does the knowledge foundation know and compose unaided? |
| B: Stronger reader (optional) | A capable external agent (e.g. Claude Code) over the **same KB via MCP** | Is a failure in A a missing *fact*, or missing *reasoning* over facts that are present? |
| C: Foundation + rules (optional, later) | Arm A plus hand-authored Utopia business rules (ADR 0047, implemented 2026-09-25, lets a rule conclude a relation) | Can "role + reporting line + band → required approver" be expressed *in the foundation*? If so, `AuthorityBand` isn't an OWM concept. |

Arm B matters because a good agent can compose S01 from well-extracted facts. That would put
the capability in the *agent*, not in the foundation or the OWM. Doc 01's split doesn't have a
row for that yet.

**Utopia's own design makes arm B the primary measurement.** "MCP is where an application on
this knowledge gets built — in the customer's own agent platform, language and sandbox,
against the read contract" (Utopia ADR 0046 and `docs/design/chat-and-mcp.md`). Chat and MCP
share one tool implementation, and the chat loop is built to guarantee an answer, not a
correct one (ADR 0042). So arm A measures Utopia's reference agent, and an OWM reads Utopia
the way arm B does. Split arm B in two:

- **B1:** all MCP tools.
- **B2:** graph tools only, with no `search_chunks` or `get_document`.

The B1 − B2 gap is what the foundation retrieved but didn't model. The arm B reader must be
blind to this repo: a fresh headless agent whose only inputs are the question and the MCP
tools, never a session that has read `truth/` or the answer key.

---

## 2. State of the local instance (checked 2026-09-27)

| Item | Finding |
|---|---|
| API | `http://localhost:1516/api/v1`, health `ok` |
| Web | `http://localhost:5173` (Vite proxies `/api` to :1516) |
| Postgres | `localhost:1517`, container `utopia-db-1` (no host `psql` installed, so use `docker exec`) |
| Utopia version | `dev` @ `aad5b06`. Record this in the run notes |
| Workspace | *Default Workspace* `01a068b4-5939-7422-a9e2-4e7f29516491` |
| Existing KBs | *General* (42 docs) and *Sovera OWM* (10 docs) |
| Ontology packs | `schema-org`, `w3c-org`, `prov-o`, `foaf`, `iof-core` |

**Two things to act on:**

1. **Do not use the *Sovera OWM* KB.** It holds your OWM design docs: `Demo data set.md`,
   `OWM — Demo.md`, `Sovera OWM + Decision Engine.md`, and others. These describe the Acme and
   Sarah scenario and its answers, so loading Northstar there leaks the answer key. Always
   create fresh KBs. Utopia's own benchmark README gives the same rule: reusing a base
   silently invalidates the numbers.
2. **Extraction has been failing, recently and silently.** 30 of 85 `extract_document` jobs
   failed between 2026-09-24 and 2026-09-26. None were timeouts. All were model-configuration
   errors: `Unsupported parameter: 'max_tokens' … Use 'max_completion_tokens'`, and
   `max_tokens is too large: 65536 … at most 16384`. The last success (09-26 17:12 UTC) came
   after the last failure (16:56), and every document that failed was later re-extracted
   successfully. So the config was probably fixed, but prove it in step 1 before spending an
   hour on ingestion.

`_owm-local/utopia-getting-started.md` lists the backend as `:1517` under "Config vars".
That's Postgres. The backend is `:1516`.

---

## 3. Controls: what never goes into Utopia

| Never load | Why |
|---|---|
| `dataset/answer-key/`, `dataset/evaluation/` | The answers |
| `truth/`, `owm/` | Clean truth and the OWM hypothesis under test |
| `dataset/evidence/MANIFEST.yaml` | It describes the traps (e.g. "Legal names differ from CRM display names") and says it's generated |
| `dataset/DATASET.md`, `README.md`, `CLAUDE.md`, `docs/`, `site/` | Describe the lab and the scenarios |

Also, in the baseline arm:

- **No hand-authored ontology.** Doc 02 §6 says "Ontology → Utopia semantic structure", but
  `owm/ontology.yaml` is the hypothesis under test. Loading it gives Utopia the answer's
  shape, and the file itself says to map it onto the foundation, never the other way round.
  Use generic packs and record which (§5 step 2).
- **No business rules, mappings (hand-written definitions) or manual merges.** Those are arm C.
- **Don't act on the Review queue. Record it.** What Utopia chooses to ask a human is itself a
  finding: doc 01 lists "what needs human confirmation?" as an open question.
- **Ask verbatim, in a fresh conversation each time, and don't coach.** A follow-up like
  "what about the 2026 policy?" turns a failure into a pass.

---

## 4. Setup (once per shell)

```bash
cd ~/DEV/Sovera/2026-dev/owm-ve/shiny-waffle
export UTOPIA_API=http://localhost:1516/api/v1
export UTOPIA_EMAIL=…      # from _owm-local/utopia-getting-started.md
export UTOPIA_PASSWORD=…
export WS=01a068b4-5939-7422-a9e2-4e7f29516491

# REST routes want the login JWT. A personal token (utp_pat_…) works for MCP and document reads only.
TOK=$(jq -n --arg e "$UTOPIA_EMAIL" --arg p "$UTOPIA_PASSWORD" '{email:$e,password:$p}' \
  | curl -s -X POST $UTOPIA_API/auth/login -H 'content-type: application/json' -d @- | jq -r .token)
H="Authorization: Bearer $TOK"

sql() { docker exec utopia-db-1 psql -U utopia -d utopia -At -F ' | ' -c "$1"; }
```

The throwaway CLI at `_owm-local/cli/utopia.mjs` wraps most of this (`login`, `kbs`, `upload`,
`watch`, `drops`, `jobs --failed`, `mcp`, `raw`, `sql`). It was verified against Utopia
@ `d676c22`, so treat it as a convenience, not a contract.

---

## 5. The run

### Step 0: freeze the inputs

```bash
uv run northstar check                          # all 8 scenarios coherent, 17 artifacts
RUN=runs/$(date +%F)-utopia-aad5b06
mkdir -p $RUN && cp dataset/evaluation/*.csv $RUN/
git rev-parse --short HEAD > $RUN/lab-commit.txt
```

**Fill in the copies in `$RUN/`, never `dataset/evaluation/`.** `northstar build` deletes and
rewrites everything under `dataset/evaluation/` (it's in `OWNED`), so results typed there are
lost on the next rebuild.

Start `$RUN/notes.md` with the Utopia commit, the extraction and chat model, the ontology
packs, the seed (20260923) and the lab commit.

### Step 1: pre-flight smoke test

Create a scratch KB, upload one small evidence file (e.g. `products.csv`), and wait for it:

```bash
sql "select kind, status, left(coalesce(last_error,''),120), updated_at
       from jobs where kind='extract_document' order by updated_at desc limit 3"
```

Go ahead only if the newest `extract_document` is `done` and the document has facts. Delete
the scratch KB afterwards.

### Step 2: create the two knowledge bases

In the UI, create a KB named **Northstar Industrial Systems** with ontology language `en`.
Or use the API:

```bash
KB=$(curl -s -H "$H" -H 'content-type: application/json' \
  -d '{"name":"Northstar Industrial Systems","ontology_packs":["schema-org","w3c-org"]}' \
  $UTOPIA_API/workspaces/$WS/kbs | jq -r .id)
KB5=$(curl -s -H "$H" -H 'content-type: application/json' \
  -d '{"name":"Northstar — missing contract evidence","ontology_packs":["schema-org","w3c-org"]}' \
  $UTOPIA_API/workspaces/$WS/kbs | jq -r .id)
echo "KB=$KB KB5=$KB5" | tee -a $RUN/notes.md
```

**Ontology packs.** I recommend `schema-org` then `w3c-org`, in that order: Utopia matches
seed classes to the *first* pack. W3C Org models posts, roles and reporting lines, which is a
fair version of what a foundation would ship with, and it adds no Northstar knowledge. Use the
same packs in both KBs. Pack choice is an experimental variable: a later run with no packs
(Utopia's ten seed classes only) tells you how much the packs did.

### Step 3: upload the evidence (17 files, not the manifest)

```bash
for f in dataset/evidence/structured/*.csv dataset/evidence/documents/*.md; do
  curl -s -H "$H" -F "file=@$f" $UTOPIA_API/kbs/$KB/documents | jq -c .
done
V=dataset/evidence-variants/missing-contract-evidence
for f in $V/structured/*.csv $V/documents/*.md; do
  curl -s -H "$H" -F "file=@$f" $UTOPIA_API/kbs/$KB5/documents | jq -c .
done
```

Utopia renders a CSV as a Markdown table and then extracts from it like any document. That's
the "CSV → structured knowledge" path in this baseline. Utopia's other structured path, a
**mounted database** queried by the `query_data` chat tool, is a different arm. Its own docs
say a row that *is* current system state belongs there, so it's worth a later comparison.

### Step 4: wait for the pipeline, then check it didn't fail silently

```bash
# every document ready and graphed
sql "select d.filename, d.status, d.graph_status, d.doc_time::date, d.doc_time_source
       from documents d where d.kb_id='$KB' order by 1"
# anything failed in this KB?
curl -s -H "$H" $UTOPIA_API/kbs/$KB/jobs/failed | jq -c '.[]? | {kind, last_error}'
# what extraction threw away, and why
curl -s -H "$H" $UTOPIA_API/kbs/$KB/extraction-drops | jq -c '.[]?' | head -40
```

- A 10 KB document took about 10 minutes to fully graph on this hardware. The corpus is about
  22 KB across 17 files, and adjudication runs after extraction, so allow 30–60 minutes.
- **Look at `doc_time_source`.** Utopia dates a document only from its content or its source
  (ADR 0045). Upload time counts as *no date*. Every evidence document states its own date
  (`created:`, `effective_from:`, `sent:`), so each should come back `content`. Any document
  left undated is a temporal finding in its own right, and it will hurt S04 and S06.
- If jobs failed, fix the cause, requeue with `POST /kbs/$KB/jobs/requeue`, and note it.

### Step 5: snapshot what the foundation knows

```bash
curl -s -H "$H" "$UTOPIA_API/kbs/$KB/export?format=turtle"  > $RUN/northstar.ttl
curl -s -H "$H" "$UTOPIA_API/kbs/$KB5/export?format=turtle" > $RUN/northstar-s05.ttl
```

The RDF export is Utopia's supported read contract. It includes both time axes, the quoted
evidence, and the derivations. With it, later scoring can be re-checked without the instance.
Also note the number of items in the Review queue, and screenshot the ontology page.

### Step 6: ask the scenarios

Open the KB's chat in the UI. Paste each question **verbatim** from `$RUN/scenario-scorecard.csv`,
each in a **new conversation**, and ask nothing else.

| Ask in | Scenarios |
|---|---|
| *Northstar Industrial Systems* | S01, S02, S03, S04, S06, S07, S08 |
| *Northstar — missing contract evidence* | S05 only |

S06 as written ("on a given date") can't be asked as it stands. Ask it three times, once per
probe date:

- "What is Acme Manufacturing's maximum contractual NS-500 discount on 2026-09-23?" (expect 15%, EXC-ACME-NS500-15)
- "…on 2024-10-01?" (expect 10%, EXC-ACME-NS500-10)
- "…on 2022-10-01?" (expect none)

For each answer, record the verdict, the approver named, the basis and documents cited, and the
**tools the agent called**. The chat UI shows the steps, and the conversation is stored
(`GET /kbs/$KB/conversations`). Save the full text to `$RUN/answers/Sxx.md`. The tool trace
is how you tell a missing fact from a failure to reason.

*Arm B, optional:* ask the same questions through Utopia's MCP endpoint
(`POST /kbs/$KB/mcp`, with a personal token) from a capable agent, and record the answers in a
separate column or file.

### Step 7: the fact checklist (27 rows)

For each row in `$RUN/fact-checklist.csv`, check the **graph**, not the chat. Use MCP
`find_entities`, `entity_facts` (with `at=` for dated facts), `paths_between`, and `timeline`,
or the graph view in the UI. Use these values in `utopia_result`:

| Value | Meaning |
|---|---|
| `GRAPH` | Present as a typed fact or edge, with correct validity where it's temporal |
| `TEXT` | Retrievable only as chunk text via `search_chunks`, not in the graph |
| `WRONG` | Present but wrong, e.g. a merged Acme Industrial, the stale 2023 "Active" status, or a 10% value that overwrote the 15% |
| `ABSENT` | Not found |

`TEXT` vs `GRAPH` is the most informative split in the sheet: text means the foundation
*retrieved* the fact but didn't *model* it. For the derived rows (D01–D09), `GRAPH` only
counts if Utopia **derived** the fact (it appears in `derived_facts[]`), not if the chat
agent composed it at question time. Chat composition is recorded under step 6.

Useful identity checks for S08 and F01–F03: `find_entities {"name":"Acme"}`. There should be
one entity for Acme Manufacturing that carries CRM-2048, C-1001 and ACME-MFG-2025, and a
**separate** one for Acme Industrial Supply Co. (CRM-2091 / C-1044). Utopia never sees the
lab's `CUST-*` ids, so score S08 on how the ids are grouped.

### Step 8: score and write up

Score each scenario on five checks, marking each ✓, ◐ or ✗:

| Check | Pass when |
|---|---|
| Outcome | The verdict matches the expected class (e.g. "needs VP Sales sign-off" = `APPROVE_WITH_AUTHORIZATION`) |
| Approver | S01–S03 name Michael Torres / VP Sales, and never Priya Shah (Finance) |
| Basis | Cites EXC-ACME-NS500-15 under MSA-ACME-2025, not the account plan, the email, or the DR-8104 precedent |
| Time | Applies the policy and exception in force *on the as-of date* |
| Honesty | Says what's missing instead of inferring it. S05 is the main test |

Tag each failure with the README trap it fell into (identity drift, similar name, temporal
precedent, stale status, superseded fact, hearsay, wrong department, product scope).

Then write `$RUN/findings.md`. List every fact-checklist row that is `GRAPH`/`TEXT` for its
inputs but fails on the implication. That list is the candidate OWM capability set, and it
decides which `layer:` tags in `owm/ontology.yaml` should move.

---

## 6. After the baseline

- **Experiment A** (drop the org chart): add a corpus to `truth/corpora.yaml` that excludes
  `organization_chart`, point a scenario copy at it, and run `northstar build`. It becomes
  another fresh KB.
- **Experiments C–F** are already scenarios S04, S02, S03 and S08. Experiment B is S05.
- **Arm C**: write the Utopia business rule for authority composition in a *copy* of the KB,
  and rerun S01–S04.
- **Scale**: rerun on `--scale large` in a fresh KB, to see whether 200 customers of noise
  break identity resolution.
- Commit `runs/<date>…/` with the notes, answers, sheets and exports. The run is the result.
