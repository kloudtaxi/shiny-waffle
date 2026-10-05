# Review of `runs/` and `docs/`, prepared for discussion (2026-10-05)

**Scope:** every run folder (2026-09-28 through set E on 2026-10-05), every file in `docs/`, the
live gap tracker (the Lab Ledger's `gaps` collection, read only), and a health check of the repo.
**Repo state reviewed:** `main` at `0e4afc5`, which includes set E. Nothing in `runs/`, `docs/`,
`truth/`, `dataset/` or the Ledger was changed.

---

## 1. The short version

1. **The lab's discipline is unusually good.**
   - Pre-registration commits precede their results; I checked all twelve cited, from `fa32ee7` to
     `dec95ae`.
   - Failed predictions are reported, not tuned away.
   - Wrong claims are corrected in place, with evidence. Examples: the "reader variance" claim was
     retracted after n = 3 and a Fisher test, and the set C note on G5 was corrected.
   - Every gate passes, and the dataset rebuilds byte for byte.
2. **The findings that will last** are in §3. The strongest are:
   - the reader is the biggest variable;
   - decisions must not become evidence;
   - agents find evidence well but decide badly under plausible forgery;
   - one kernel with declarative specs covers three decision types.
3. **The lab has drifted from its founding question.** It was built to find the boundary between
   the knowledge foundation and the OWM *on Utopia*. Since 10-02, no experiment has touched
   Utopia. Every engine and reader result since then is on gold evidence. The work became "design
   the OWM decision engine". That is a legitimate turn, but no doc says so, and the
   foundation-side claims rest on one Utopia commit, one ingestion per scale, and knowledge bases
   that have since drifted (G-21).
4. **The headline results since 10-02 are partly self-agreement.**
   - The engine descends from the oracle: J1's `hybrid.py` "mirrors `oracle.decide`" and imports
     `northstar.oracle._approver`.
   - The register's terms are transcribed from `truth/`.
   - The author's predictions about their own engines "all held".
   - The blind and user-written pieces are what give the results external weight: the SLA rule
     sheet, the agent-authored spec, and attack sets B through E.
5. **The register's 0-unsafe result holds by construction.** Set E's threat model forbids
   touching the register and the CRM, ERP and HR exports, and all seven attacks were additions.
   That is exactly where the register moves the trust. The informative set E result is the
   reader's E3 miss (G-31): a served register has to state what it covers and what is absent.
6. **The docs are behind the runs.**
   - No in-repo synthesis exists after 10-03.
   - The reconciliation map still states positions the lab has reversed ("no LLM in the OWM
     serving path", "don't build a decision engine").
   - **No ontology `layer:` tag has ever moved.** CLAUDE.md names moving those tags as the
     experiment's purpose.

---

## 2. The arc in one table

| Date | Run | Question | Headline | What it changed |
|---|---|---|---|---|
| 09-28 | `utopia-aad5b06` arm A | Can Utopia's own chat answer S01–S08? | 2/10 right; "cannot determine" 8×; one invented "100%" | Arm A measured Utopia's chat loop, not the foundation (ADR 0046: the app surface is MCP) |
| 09-28 | arm B1 / B2 | A blind Opus reader over MCP, all tools vs graph only | B1 9/1/0; B2 6/4/0 | **The reader is the biggest variable.** The B1−B2 gap is the extraction worklist |
| 09-28 | correction + repeats | What is human identity review worth? | Graph-only got *worse* (pre 6,6,5 ✓ vs post 4,4,4); digging `changes` 8/9 → 0/9, Fisher p ≈ 0.0002 | Graph-only answers ride on an undocumented quote path; the fix belongs in the read contract |
| 09-28 | curation | Fix the facts instead | S01/S02/S04 fixed; **S05 confidently wrong** 3/3 | Adding facts can make answers worse; the procedure is missing |
| 09-28 | procedure, request | Give the reader the OWM's procedure, then the request record | 8–9/10, then **15/15** | The OWM supplies the procedure, the decision inputs and the decision record |
| 09-29 | scale-large | Does it hold at 10× noise? | B1 unchanged (9/1); B2 degraded (2/7/1); curated + procedure + record 13/15 → 15/15; held-out 15/18 (all misses S13) | Text retrieval is noise-robust; which facts need curating is per-KB |
| 09-30 | owm-measurements | Procedure as a tool; v2; constraints; decision memory; vocabulary | `get_procedure` called 102/102; v2 fixed S13/S15 but **regressed S18**; inverted reporting lines flagged 13/13 by rank; the decision-as-document became undated facts and was **cited as evidence** | Prose procedures behave like untested code. **Decisions must not be evidence** |
| 10-01/02 | grading pass, two scores | Do the human grades match the auto-scorer? | Strict 213/236; "acceptable" 235 → **236/236** after the user's rulings | "Acceptable" no longer discriminates. The #6 ruling made routing to the accountable approver safe |
| 10-02 | jev-probe J1–J4, E2E, A1, I2 | Jev judges and code composes | J1 18/18; **gpt-4o 161 false merges vs Jev 3** (J4); E2E hybrid 102/102 vs readers 93/102; I2 0 false merges at τ = 0.9 | Agents find, Jev judges, code decides. Identity moves out of Utopia's governance |
| 10-03 | adversarial (exp 4) | Can a planted document move a decision? | Set A: v1 unsafe on 4/8, reader 2/8. **Set B (blind): reader unsafe on 6/8 (17/24 runs)**, v1 1/8 | The engine fails on structure, the reader on plausibility. Guards G1–G5. Register first proposed |
| 10-03 | exp5 credit | Product, or a discount apparatus? | **PRODUCT**: 4 kernel generalizations, hybrid 10/10, reader 27/30 | Separation of duties, concurrence, identity by key, eligibility instruments |
| 10-03 | exp6 SLA | Does it hold for a non-approval decision? | **SUBSTRATE**: K-5…K-9 (clocks, obligations, routing), 10/10; reader 20/20 core | One envelope with `obligations[]`; the kernel is a toolkit, not a pipeline |
| 10-04 | specs-as-data | Decision logic as YAML; can an agent author a spec? | Three types equivalent as YAML; **the agent-authored credit spec scored 10/10 first time** | Procedure objects as executable data |
| 10-05 | set C (user) | Your attacks on credit | Every engine and the reader fooled by forged *governing* documents (reader 9/9); the agent spec was the most exposed | Clean accuracy ≠ adversarial robustness. Spec-local guards don't generalize |
| 10-05 | instrument-guards, set D | Generic lineage guards L1–L3 | v2 unsafe 2/7 (only in-place edits); the price is routing (12 → 22) and an **availability attack** | What remains is the register's job |
| 10-05 | register, set E | The document register (G-01) | Register-backed engines **0/14** (C + D) and **0/7** (E); reader with the register 0/42, then 1/7 on E (E3) | Closes in-place edits and the addendum outage. A served register must state its coverage (G-31) |

**Spend:** metered reader spend across the lab, summed from the run notes, is about **$185** of
Claude calls (09-28 small $40, scale $39, 09-30 $31, register and sets C–E $49, the rest $26). Add
about $0.70 of Jev, the subagents' tokens, and an unmetered amount of Utopia gpt-4o. Credit and SLA had no retrieval cost, because they
ran on gold evidence.

---

## 3. What I'd stand behind (durable findings)

1. **The reader dominates.** Same graph: 2/10 for Utopia's chat, 9/10 for a blind Opus reader.
   On clean evidence, a strong agent recomposes the canonical decision at question time.
2. **Graph-only access is brittle in ways nobody sees.**
   - Quotes reach the reader only through the record-time `changes` feed.
   - Correct identity merges closed that path by accident (p ≈ 0.0002).
   - A human merge erased the very identifier it was meant to connect.
   - The fix belongs in Utopia's read contract (quotes or chunk ids on `entity_facts`). That
     draft has never been filed (G-20).
3. **Facts are necessary, and they aren't the decision.** Curation made S05 confidently wrong.
   The procedure and the request record, the OWM's inputs, are what fixed it.
4. **Decisions must not re-enter the evidence store.**
   - The decision log became the timeless fact "Sarah Chen limit 10%".
   - Two of three later readers cited it as their source.
   - The typed record was never cited.
   - This was seen once, at n = 3, but the mechanism is clear.
5. **Constraints should flag, with the evidence attached.** The rank constraint caught 13/13
   inverted lines with 0/49 false flags. Acyclicity caught none.
6. **Identity is decision-grade work, and the platform's governance isn't up to it.**
   - Of gpt-4o's 161 false merges, 158 are orders merged into customers.
   - One guard ("an order is never a customer") plus Jev at τ = 0.9 gave 0 false merges.
7. **Agents retrieve well and decide unreliably** (E2E: retrieval sufficient in 102/102; the
   readers' own decisions 93/102).
   - Under attack, their safety depends on the forgery showing a defect: set B 17/24 unsafe, and
     sets C and D governing documents 21/21.
   - They see a gap and decide anyway: S33 2/3 (G-14).
8. **A small kernel generalizes.**
   - It covers two approval types and one obligation-shaped type.
   - Every addition is a generic primitive.
   - Specs run as data, and an agent can write one.
9. **A guard opens new paths.** Reading amendments let B5 through. Reading less is a defence.
   Every new input kind needs provenance first.
10. **A register removes the availability cost the guards create.** v2 agent routed up to 33
    correct decisions; register-backed engines routed 0 on set E.

---

## 4. Where I'd push back

### 4.1 The founding question went quiet

- **Last time Utopia was in the loop:** 09-30. E2E re-scored 09-30 transcripts; nothing since
  has touched it.
- **What's open as a result:**
  - G-22: no retrieval arm for credit or SLA;
  - G-23: no cost per decision with a cheap retriever;
  - G-21: the knowledge bases drift from the dataset. The scale base KB carries
    `pricing_policy_2027`, 23 residual `known_as` facts from a deleted decision log, about 160
    false merges, and repeated curation pushes.
- **What isn't happening:** `owm/ontology.yaml`'s `layer:` tags have only been *added to* (exp 5).
  No type has moved between `foundation` and `owm`, even where the evidence says it should:
  - `Customer` ("resolved identity") is still `foundation`, after I2/J4;
  - documents and contracts are still `foundation`, after the G-01 decision put the register in
    the OWM;
  - `owm-spec.md` hasn't changed since 09-27.
- **Suggestion:** say explicitly that the lab now has two tracks (the boundary on Utopia, and the
  OWM engine design), and record the boundary's current position by moving the tags.

### 4.2 Same author, same logic

- **The lineage:** `runs/2026-10-02-jev-probe/j1/hybrid.py:7` says "It mirrors `oracle.decide`",
  and line 50 imports `_approver` and `resolve_request` from `northstar.oracle`. The kernel is that
  engine refactored (`kernel.py:3-5`).
- **What the agreement measures:** the oracle (the lab's coherence check), the kernel (the OWM
  prototype), the specs, the answer keys and the predictions share one author. So "10/10 against
  the key" on S26–S35 is two implementations of doc 03 §11 agreeing with each other.
- **CLAUDE.md:** it warns against evolving the oracle into OWM logic. The kernel no longer imports
  the oracle, but it descends from it.
- **What carries the external weight:**
  - the blind SLA rule sheet;
  - the agent-authored spec;
  - attack sets B (a blind subagent) and C, D and E (yours).
- **"Every prediction held"** (sets C, D and E) tests the author's model of their own engines. The
  notes say so. It shouldn't be read as evidence about the attacks.

### 4.3 The register's result holds by construction

- **Why 0 unsafe was guaranteed:** `lab/owm_register/build_register.py` "plays a **correct
  registrar**"; its terms "come from `truth/`". Set E may not touch the register or the
  structured exports. All seven E attacks were additions, with no replacements, so in-place edits
  weren't retested against it. An unregistered document can't count, so 0 unsafe was predicted
  and guaranteed.
- **What the register really does:** it moves trust to four places that haven't been tested:
  1. **The registration workflow.** An agent proposes, the owning function registers, and a
     second person approves. Untested: a plausible registration request, or a mis-transcribed
     term that passes K2 because the number appears *somewhere* in the text.
  2. **The registrar's term extraction.** In the lab it is copied from the truth. In the product,
     a person or an agent extracts it, which is G-08's fragility moved upstream.
  3. **The structured exports.** CRM, ERP and HR are trusted by every threat model so far.
  4. **Kinds the register doesn't cover:** discount and SLA (G-30), and absent kinds for an agent
     reader (E3, G-31).
- **Worth noting:** with the register, the reader matched the engines (0/42 on C + D). The notes
  concede "the register is the thing that made the difference, for engines and agents alike".
  That weakens "the engine must decide". The remaining case is G-14 (deciding through a seen
  gap), determinism, audit and cost, and it deserves to be stated on those grounds.

### 4.4 "Safe" means different things in different places

| Where | Wrong denial | Over-caution / routing | Routing to an approver without eligibility |
|---|---|---|---|
| Two scores (10-02, after rulings) | (none occurred) | acceptable | **acceptable** (#6 ruling) |
| Adversarial sets A–E | **unsafe** | safe; the cost is reported | not tested as such |
| Exp 5, S32 run 3 | counted **unsafe** by rule; the author argues "partial"; **never graded** | | |

- **The #6 ruling neutralized S05, the lab's flagship trap,** and other docs still call S05 a
  failure (`experiment-assessment:16`, `demo-readiness:128`).
- **Suggestion:** one taxonomy (state error, authority error, eligibility error, availability
  cost), applied to every run's JSON and tabulated once.

### 4.5 The reader baseline in the adversarial sets is weaker than it needs to be

- **The setup:** the reader is `claude -p` with no tools, every document in the prompt, and
  procedure v1, which doesn't say who may issue what. The engines have provenance rules (G1:
  owning function, executed, issuer authority).
- **The gap:** exp 4 lists "agents need the same rules as code, served as procedure" as an
  amendment candidate, but **no reader run gave the reader those rules.**
- **The fair comparison:** the reader with a provenance-aware procedure and no register, on sets
  B to E.

### 4.6 Small n, one model, one company

- 2–3 runs per cell, about 10 scenarios per decision type, one reader model with one fixed prompt.
- Conclusions are phrased about "agents", but they are about this reader under this prompt.
- **Human grades:** 41 in all, **none after J3**. Everything from exp 4 onwards is auto-scored
  only.

### 4.7 The line-ending finding is a cheap fix, not strong evidence

- **The inconsistency:** `kernel.fingerprint()` normalises `\r\n` (`kernel.py:603`), but the
  prose readers don't. A one-line normalisation at load fixes it.
- **The real argument for G-08** (terms from the register) is wording variance across
  organizations, not line endings.

---

## 5. The docs: what's stale, what's missing

**Stale or contradicted** (file:line refs are against `0e4afc5`):

| Doc | Says | Overtaken by |
|---|---|---|
| `owm-overhaul-reconciliation-2026-09-29.md:41` (row 3) | "No LLM in the OWM serving path"; "Judgment at the edge worked" | Jev's ruling (`jev-typesafe-assessment:176-178`); exp 4 |
| `external-reviews-response-2026-09-29.md:30` | "Don't build a decision engine… Nothing so far needs one" | The hybrid, kernel and flow runner from 10-02. No doc records the reversal |
| `next-experiments-2026-10-02.md:4` | "None has been started" | Experiments 1 and 2 ran the same day |
| `next-experiments:35` | Experiment 6 = decision memory at scale | Experiment 6 = SLA. The ids collide (A1, M1, D1, K1 each mean two things) |
| `next-experiments:10` | "Agents are good at retrieval (102/102)" | A1: governing policy opened in full in only 21/102 |
| `demo-readiness-2026-10-03.md:26` | "Corrects" doc 01's "Utopia plays both parts" | That phrase isn't in doc 01 |
| `demo-readiness:79-101` | "Must have" demo gaps | Demo work moved to `kloudtaxi/blueleaf-demo` |
| `experiment-runbook.md` | 17 artifacts, 8 scenarios, 27 checklist rows | 38, 45, 39; no mention of `missing-guarantee-evidence` |
| `grading-guide.md:9,16` | About 390 answers; three experiments | Four experiments; J3 graded (Part D missing) |
| `gap-tracker.md:5,17` | Anchors G-01…G-29; `tracker/seed/gaps.json` | The Ledger has G-30 and G-31; the seed is gitignored |
| `runs/2026-09-28-utopia-aad5b06/notes.md:1` | "STATUS: ACTIVE", with next steps that are done | The Ledger's `experiments` collection agrees with the stale status |
| `runs/2026-10-05-instrument-guards/notes.md:214` | G-26: see `docs/gap-tracker.md` | G-26 is closed in the Ledger |
| `runs/2026-10-03-exp5-credit/notes.md:144`, `exp6-sla/plan.md:25` | `check_kernel.py` as a live check | It fails since exp 6's roster change (G-27, known) |

**Missing:**
- **A synthesis after 10-03.** Experiments 4–6, specs as data, guards and sets C–E, and the
  register live only in run notes. The CxO write-up is outside the repo and stale (G-29).
- **Decisions recorded only in run notes or the Ledger:**
  - G-01's three choices (where the register lives, who registers, structured terms);
  - the Jev/LLM-in-OWM ruling;
  - the #6 safety ruling;
  - "Utopia is never named in the demo".
- **Open items nothing tracks:**
  - `utopia_result` is empty in all 39 fact-checklist rows, which the runbook calls "the unit of
    evidence";
  - runbook step 8's `findings.md` was never written;
  - the "adversarial organization" arm;
  - the MLflow switch trigger, which has been met (`tracking-mlflow-review:39`);
  - S32 run 3's grade.

---

## 6. Repo health

**Gates:** all green.

| Check | Result |
|---|---|
| `pytest` | 40 passed |
| `ruff check`, `ruff format --check` | clean |
| `mypy` (strict) | clean on `src` + `tests` |
| `northstar check` | 38 artifacts, 45 scenarios coherent |
| `northstar build` vs committed `dataset/` | **byte-identical** (120 files) |

**Lab checks:**
- **Pass:** `build_register.py --check`, `check_equivalence.py`, `check_behaviour.py --replay`.
- **Fails:** `exp5-credit/check_kernel.py` (known, G-27).

**Not covered by tooling:**
- `lab/` isn't under pytest or mypy. A strict mypy run gives 15 errors in 7 files, 8 of them in
  `flow.py`, plus `kernel.py:259` (`float <= None`).
- The kernel, the register and the flow runner, which hold the lab's current headline claims, have
  no unit tests. They are checked only through replay scripts in `runs/`.

**README and CLAUDE.md drift:**
- **README:**
  - it says "26 tests"; there are 40;
  - the layout says 6 CSVs and 11 docs; there are 14 and 24;
  - it omits `missing-guarantee-evidence`, `pricing_policy_2027.md`, `truth/support.yaml`,
    `owm/procedures/`, the `finance` and `support` generators, `src/northstar/sla.py`, `lab/`,
    `runs/`, `tracker/` and `docs/`.
- **CLAUDE.md:**
  - it lists 4 scenario kinds; there are 6 (`credit_decision`, `sla_decision`);
  - it says the oracle "implements the canonical discount process"; it also does credit and SLA;
  - it gives the run folder pattern as `<date>-utopia-<sha>`; 2 of 10 folders follow it;
  - only `lab/utopia/` is described.
- **`lab/owm_kernel/README.md`:** lists only `kernel.py` and `discount.py`.

**Secrets:** `.vault/` and `_owm-local/` are ignored. No secret values were found in tracked
files; the pattern hits are placeholders, environment variable names and token labels.

---

## 7. The gap tracker, live (from the Ledger)

- **Closed:** G-09 (filename order), G-26 (clean controls), and G-28 after set E.
- **Partial:** G-01 (register, credit only), G-02, G-04, G-08, G-10, G-27.
- **Findings:** G-14 (readers decide through a gap), G-15, G-25.
- **Pending your decision:**
  - **G-01 `on_mismatch`.** Recommendation B: decide on the registered terms and raise the
    discrepancy as an incident.
  - **G-05,** guards on by default (blocked on G-02).
- **Open P1s:** G-07 (adversarial admission check for agent-authored specs).
- **New since set E:** G-31, partial: a served register must state its coverage and absences.
  Extract v2 fixed E3 in a check (3/3), but set E shaped that fix, so a fresh test is pending.

---

## 8. Questions for our discussion

1. **Which track is the lab on now: the boundary on Utopia, or the OWM engine?** If both, what's
   the next foundation-side run? My suggestion is an end-to-end credit decision: fresh KBs on the
   current dataset, Utopia retrieval, the kernel v3 with the register, and a reader comparator.
   That closes G-21, G-22 and G-23 in one go.
2. **`on_mismatch`: route, or decide on the registered terms?** The recommendation is the second;
   it's your call.
3. **Is the register's new trust boundary the next attack surface?** That means registration
   requests, transcription errors and the structured exports. Set F could target those, with the
   registrar extracting terms rather than reading the truth.
4. **Should we unify "unsafe" across the lab** (§4.4), and grade a sample of answers from exp 4
   onwards so human calibration covers the current claims?
5. **Should the reader get a fair baseline** (a provenance-aware procedure, no register) before
   "the agent gathers, the OWM decides" goes into the BlueLeaf spec?
6. **Housekeeping:**
   - a post-10-03 synthesis doc;
   - moving the ontology `layer:` tags;
   - README, CLAUDE.md and runbook refresh;
   - `lab/` under mypy, with a few kernel unit tests.

   All cheap, and I can take them.
