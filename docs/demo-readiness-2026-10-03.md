# Demo readiness review (2026-10-03)

This review checks the four design docs (01 *OWM + Knowledge Foundation Demo*, 02 *OWM + Utopia
Experiment*, 03 *Domain Model + Ground Truth*, 04 *Synthetic Data Generation*) against what the
lab has built and measured up to commit `c3cc101`.

## Verdict

**Yes, there is enough to build the demo.**

**What we already have:**
- the dataset;
- every scenario the docs ask for;
- the knowledge foundation, loaded;
- the decision engine;
- the proof points.

**What's missing is the stage, not the substance:**
- one screen that walks the audience from evidence to decision;
- an OWM "decide" tool that an agent can call live;
- a decision object in doc 03 §21's exact shape;
- a pinned demo environment with a recorded fallback.

That is about three to four days of work, and Jev costs only cents.

**One correction to doc 01's plan, from our own results.** Doc 01 says that "Utopia plays both
parts". The measurements say Utopia should play only one of them.
- Utopia on its own retrieves well, but it doesn't decide reliably: readers on Utopia got 93/102,
  and its gpt-4o identity governance made 161 false merges.
- The thin OWM stand-in we built on top of it is what gets 102/102 and 0 false merges.

The demo is stronger, and more honest, if it shows that split: **Utopia knows, the OWM decides.**
That split is the thesis of doc 01 anyway.

## What the docs ask for, and where we stand

| Requirement | Doc | Status | Where |
|---|---|---|---|
| A synthetic enterprise: seeded, reproducible, truth hand-authored, Polyfactory/Faker for the noise | 04 | **Done** | `src/northstar/`, `truth/`, `dataset/`. Small scale, plus a large scale of 200 customers and 1,000 requests. |
| Evidence: CRM, ERP, contract, pricing policies (2025/2026), org chart, email, SOP, exception memo | 01, 02 §4 | **Done** | `dataset/evidence/` |
| No single artifact contains the answer; facts are distributed | 02 §4–5 | **Done, and enforced by tests** | Invariants in `tests/` |
| Deliberate ambiguity: identity, temporal, policy vs exception, composed relationships | 02 §5 | **Done** | Trap table in `README.md` |
| The five demo questions | 02 §1 | **Done**, all oracle-proven | S01, S02, S04, S07 (why eligible), S05 |
| The six ground-truth scenarios | 03 §14–19 | **Done** | S01–S06 |
| Experiments A–F (remove the org chart, remove the exception, change the date, 18%, NS-Cloud, a similar customer) | 02 §9 | **5 of 6** | B is the `missing-contract-evidence` corpus; C is S04/S11/S21; D is S02/S20; E is S03/S17; F is S13/S15/S08. **A (no org chart) is not built.** |
| `owm-spec.md` and an ontology, independent of Utopia | 02 §2 | **Done** | `owm/owm-spec.md`, `owm/ontology.yaml` (layer tags as hypotheses) |
| Evidence loaded into Utopia as the knowledge foundation | 02 §6 | **Done** | Small and scale KBs, curated, with MCP live |
| The fact checklist: "Utopia knows X and Y, but not X + Y → Z" | 02 §7 | **Sheet exists, not filled in** | `dataset/evaluation/fact-checklist.csv` (30 facts; the `utopia_result` column is empty) |
| The first OWM decision object | 02 §8, 03 §21 | **Close, but not field for field** | `runs/2026-10-02-jev-probe/j1/hybrid.py`. It has outcome, eligibility (status, max, basis), authority (policy, limit, authorized, role, approver) and judgments. It lacks `decision_id`, `as_of`, `subject`, `request`, the approver's employee id, `reason` and `evidence`. |
| "Eligibility ≠ authority" made explicit | 01, 03 §7 | **Done** | Separate `commercial_eligibility` and `authority` blocks; 18/18 |
| The canonical process (doc 03 §11) as a governed object | 03 §11 | **Done** | `owm/procedures/discount-approval.md`, served by `lab/owm_standin/server.py` (called 102/102) |
| Every decision traceable to evidence | 03 §20 | **Partial** | The engine knows which documents it used, but doesn't emit an `evidence` list yet |
| "What needs human confirmation" | 01 | **Done** | Jev's confidence gate; I2 routes 4% of pairs to a person, with 0 false merges |
| The evergreen layer: continuously enriched | 01 | **Not shown yet** | S21 (the 2027 policy) is the ready-made beat (see below) |
| Demo applications: Discount Approval, Contract Intelligence, Account Intelligence, Policy Reasoning | 01 | **1 of 4 built** | Discount approval only. The other three can be shown as questions (S07 provenance, S08 identity, S04/S11 policy over time), not as applications |
| The OWM contract doesn't depend on Utopia | 01 | **Done** | The hybrid takes documents; Utopia sits behind MCP. This is ports and adapters, as the user ruled. |

## The gunpowder: proof points we can put on screen

All of these are measured, pre-registered where noted, and committed.

| Claim | Number | Source |
|---|---|---|
| Agents find the right evidence | Retrieval sufficient in **102/102** runs | E2E |
| Agents fail at deciding, not finding | Readers decide right **93/102** on that same evidence | E2E |
| The OWM split fixes the decision | Hybrid **102/102**, 0 unsafe | E2E |
| The whole decision runs from the company's records | **18/18** on gold evidence, **102/102** on what agents surfaced, with no answer key | A1 |
| Identity needs types and governance | gpt-4o: **161 / 158** false merges. Jev + one rule: **0 / 0**, across 41,617 pairs | J4, I2 |
| The system knows when to ask a person | Jev's confidence is calibrated (ECE ≤ 0.10); 4% of identity pairs are routed | J2, I2 |
| Agents notice conflicts but act anyway | S22: 3/3 readers stated the conflict, then put APPROVE in the decision block | J3 |
| Decisions must be typed records, not documents | A decision stored as a document became undated facts and was cited as evidence | Item 4 |
| Cost per decision | About $0.27 per Opus reader answer, against well under a cent for the hybrid's Jev calls | CxO doc |

The failures are as useful as the wins: they are the "why an OWM" slide. We have real transcripts
for each of them.

## Gaps, ranked

### Must have

1. **An OWM `decide` tool** on the stand-in MCP server: `evaluate_discount_request(request, as_of)`.
   - It runs the hybrid (Jev judgments, code rules, authority from evidence) and returns the
     decision object.
   - It persists the decision as a typed record. `find_decisions` already serves those.
   - This is also the core of experiment 3, so the demo build and the next experiment share the
     work. About 1 day.
2. **The §21 decision object, field for field.** Add the decision id, as-of date, subject,
   request, the approver's employee id, the reasons, and the evidence (artifact ids such as
   `MSA-ACME-2025`, `pricing_policy_2026`, `DR-9001`). Small: a few hours.
3. **One demo surface that tells the story.** The steps: evidence, then what the knowledge
   foundation knows, then the decision, then live "what-ifs".
   - The what-ifs: change the date, the percentage, the product, or remove the contract.
   - Each what-if shows the lab's answer key agreeing. The oracle stays visibly separate from the
     OWM.
   - This should be a local web console, because a claude.ai page can't reach the local Utopia.
     About 1–2 days.
4. **A pinned demo environment with a fallback.**
   - A snapshot of the KB state, and a parity check against `dataset/`. S02–S04's new request ids
     and the 2027 policy are not in every KB.
   - Jev runs in replay mode, so the demo runs offline if a cloud API drops.
   - A dry run. Half a day.

### Should have

5. **Fill in the fact checklist** (doc 02 §7) from Utopia. It is doc 02's own thesis slide: the
   facts are all ✓, and "Sarah can approve 15%" is the row that says **OWM needed**. Half a day,
   using read-only queries.
6. **An evergreen beat using S21.** Ingest `pricing_policy_2027.md` into the demo KB on stage (cents
   of gpt-4o). Then ask the same question with a 2027 date and watch the answer change. It is the
   only place doc 01's "continuously enriched" can be shown live today.
7. **Experiment A as a corpus** (the org chart removed). Since A1, authority comes from
   `employees.csv` and the policy, so the prediction is that the decision survives. That is a nice
   "the model composes meaning" moment. It needs a corpus variant and a run.

### Could have

8. One live agent moment: Claude, with Utopia MCP and the OWM MCP, answers S01 by calling `decide`.
   It is on message (agents-first), but live LLM runs vary. Keep a recorded take ready.
9. A short identity segment from I2: the order-versus-customer rule, and a routed queue ranked by
   confidence.

## A suggested demo shape (about 12 minutes)

| Act | Shows | Live or recorded |
|---|---|---|
| 1. Meet Northstar | `site/index.html`, then the messy evidence: CRM-2048, C-1001 and ACME-MFG-2025 are one customer, and no file holds the answer | Live, static |
| 2. What the knowledge foundation knows | Utopia's graph and timeline: Acme resolved, the 2025 vs 2026 policy, provenance. The fact checklist: every fact ✓ | Live, Utopia UI (small KB) |
| 3. Ask an agent | A plain agent over Utopia answers well, until it doesn't: the S05 confident approval with no contract, or the S22 conflict noticed and then approved anyway | Recorded transcripts |
| 4. Add the OWM | The same request through `decide`: eligibility YES, Sarah's authority NO, Michael Torres required, `APPROVE_WITH_AUTHORIZATION`, with an evidence trail and a typed record | Live (Jev replay as backup) |
| 5. What-ifs | 18% → `REJECT_OR_ESCALATE`; NS-Cloud → `REVIEW_REQUIRED`; Sept 2025 → `APPROVE`; contract removed → `REQUEST_EVIDENCE`; the conflicting exception picks 15% and keeps the 10% history; Acme Industrial doesn't inherit Acme's terms | Live |
| 6. The organization changes | Ingest the 2027 policy, re-ask with a 2027 date, and the answer follows | Live (cents of gpt-4o) |
| 7. Proof and architecture | The numbers above. Ports and adapters: the knowledge foundation is replaceable, and the OWM contract has no dependency on Utopia | Slides |

## Where the docs and the measurements disagree

These are worth deciding before the narrative is written.

- **"Utopia plays both parts"** (doc 01). We tried putting OWM objects inside Utopia.
  - Curated statements worked for graph-only readers.
  - A decision stored as a document became evidence: contamination.
  - Utopia's own governance made the false merges.
  - The decision role worked as a separate stand-in.

  I recommend presenting it as "Utopia as the knowledge foundation, a virtual OWM on top". That
  is still a stop-gap, and doc 01 already says so.
- **Demo applications** (doc 01 lists four). Only discount approval is built. Call the other three
  "questions the same model answers", not applications.
- **"No LLM in the OWM path"** (earlier canon). The user has amended this: an LLM is allowed for
  OWM's internal judgments. Jev is in the decision path, and the slide should say so plainly.
  Confidence gating is the safety story.
- **Evergreen.** It is promised in doc 01, and only S21 can show it. Decisions feeding back into
  the model (doc 01's last open question) exist only as typed records served for precedent. They
  are not yet shown changing a later decision.

## Risks on demo day

- **Live LLM variance.** Readers are 93/102. Never make a live agent's answer the climax; the climax
  is the OWM's deterministic decision.
- **Dependencies:** Docker Utopia, OpenAI (Utopia's chat and ingestion, with a spend limit hit
  before), the TypeSafe cloud, and Claude. Every live step needs a recorded take. Jev already has
  replay.
- **KB state.** The scale KBs carry about 160 of gpt-4o's order→customer false merges, and the KBs
  have been curated and mutated over two weeks. Use the small KB on stage, or a fresh one ingested
  from `dataset/evidence/` (a few dollars of gpt-4o).
- **Screens.** Utopia's settings page shows API keys, and `_owm-local/` holds tokens. Neither may
  appear on a shared screen.
- **Utopia's mistakes on stage.** Doc 01 frames Utopia's author as a peer. Showing 161 false
  merges is a strong "why types matter" beat, but it lands differently depending on who is in the
  room. It has not been reported upstream either.

## Decisions for you

1. **Audience and length.** Client or prospect, investor, CxO, or Utopia's author? It changes act
   3 and act 7.
2. **Live or recorded.** I recommend a live console with replay fallback, and one optional live
   agent moment.
3. **Naming on screen.** Doc 01 says "Sovera OWM — Organizational Intelligence Layer"; the platform
   name in canon is BlueLeaf.
4. **"Utopia plays both parts"** or **"Utopia + a virtual OWM"**. I recommend the latter.
5. **Whether to show Utopia's governance errors,** and how.

## Suggested build order

1. The §21 decision object, then the `decide` tool on the OWM stand-in, with typed records.
2. The demo console, with what-ifs and the answer-key check.
3. Pin the environment, set up replay, and fill in the fact checklist.
4. The S21 evergreen beat, and Experiment A if there is time.
5. A dry run, recorded takes, and a one-page leave-behind (the CxO doc already covers most of it).

## The user's decisions (2026-10-03)

**Precedence:** docs 01–04 came before shiny-waffle, so they lag it. Where they conflict, this
repo's corpus and decisions win.

1. **Audience: clients.** The demo has to be a high-fidelity, app-like experience that they can
   understand and reason about. No visible tech: no JSON, no model names, no confidence numbers,
   no lab vocabulary.
2. **Live.** The user drives the demo.
3. **The brand on screen is BlueLeaf.**
4. **Utopia doesn't exist as far as the demo is concerned.** It is never named or shown, and
   nobody from it is in the room. The identity story is shown as a guardrail: BlueLeaf won't merge
   two customers on a guess, and asks a person instead. It is not shown as another system's
   errors.

**What this changes in the plan above:**
- Act 3 ("ask an agent", with recorded failures) and the on-screen answer-key check are dropped.
  The answer key becomes the demo's regression test, run before every rehearsal.
- Act 2 becomes BlueLeaf's own view of what it knows about Acme.
- Act 7 becomes outcomes, not architecture.
