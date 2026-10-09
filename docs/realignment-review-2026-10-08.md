# Realignment review: the lab since 6 October, against the UX work (2026-10-08)

**What this is.** A catch-up on shiny-waffle (25 commits on `main` since `5a1c1d9`, plus the BlueLeaf
MCP branch), read against the UX work in `kloudtaxi/glowing-garbanzo`, branch `v1/use-manage-operate`
(`ad34c11`, web-next v1.1). It lists where the two have drifted and what to settle before either moves
on.

## 1. Catch-up: what changed

### Decisions (the user's, 2026-10-07)

| Topic | Decision | Source |
|---|---|---|
| Utopia | Never named. Absorbed, then replaced by our own knowledge foundation | `demo-sequencing-technical` |
| Where the demo lives | web-next, in glowing-garbanzo; rebranded in place, **after it works** | same |
| The OWM API (#16–#20) | A lab session builds it in shiny-waffle as a **separate service** that web-next reaches through `OWM_API_URL`. **The contract is web-next's `lib/types.ts`** | same |
| The demo organization | **Northstar** at sign-in (Priya and Elena for Finance; Hannah and Marcus for Support), on computed data, not the Sample organization | same |
| Demo style | Predictable, not scripted: deterministic OWM, audience picks inputs, baseline run ×5 with tallies, labelled replays as fallback | same |
| Knowledge foundation | **First-party: Docling + langextract**, with byte-range references. Design partners asked for it | `product-thesis-feedback` |
| Agent runtime | **Agno** | same |
| Name | Keep **Organizational World Model** | same; `product-type-validation-notes` |
| The value | **"AI trust with confidence"**; conditions become a named concept | `product-thesis-feedback` |
| Lab order on resume | Interleave credibility and ROI: set G (MCP) → G-18 → register attacks → G-23 → G-39 | `product-type-validation-notes` |

### Results

| Run | Result |
|---|---|
| **G-18** hybrid identity routing | **Done.** Two-judge agreement (R2) sends 0.79% / 0.94% of pairs to a person, with 0 false and 0 missed merges. Fresh-seed data waits for the user |
| **G-23** cost per decision | **Done.** The OWM-served slice cuts Opus cost 68% ($0.304 → $0.096) with identical safety. Haiku isn't a safe decider. **The OWM path (kernel + Jev, no agent) held 28/28 at ≤ $0.00026 per decision.** Product shape: *the OWM decides; the agent gathers, explains and acts.* The schema addendum (Haiku with an enforced record) is pre-registered, but no answers are committed yet |
| **G-37** title priors | **Done.** No title-prior dependence, with or without the procedure (0 answers name the VP where the new holder is required) |
| **Register attacks** | The registrar is built and frozen (RR-1 to RR-14, revocation), self-check 20/20, regressions clean. **Waiting on the user to write the sealed attack set** (about 24 cases, `runs/2026-10-08-register-attacks/sealed/BRIEF.md`) |

### Builds

- **BlueLeaf MCP** (`skunkworks/blueleaf-mcp`): plan ruled (D-1 to D-8, option A on all eight). Only
  the scaffold is in code so far: `service/__init__.py`, `_lab.py`, `errors.py` (B-01 of 24).
- **The OWM API** for web-next: not started. Nothing on either branch serves #16–#20 yet.

## 2. Where we need to realign

### 2.1 The contract (#16–#20) no longer matches the lab

The lab named web-next's v1.1 shapes as the contract. They were designed on 7 October, before the
registrar existed, around the Lumen demo. Against `lab/owm_register/registrar.py` and
`lab/owm_kernel/flow.py`:

| v1.1 says | The lab does | Consequence |
|---|---|---|
| A version is **pending** until approved; approvers can **return** it with a note | A change is **atomic**: submitted and approved in one step. There is no pending state and no return | The Approvals flow and RV-301 have nothing to call. The service needs a pending-change queue, or the UI drops the two-step flow |
| One named approver per document ("only the Finance Director") | **RR-4:** the head of the owning function **or any Executive**, never the submitter. Pricing policies, agreements and exceptions are owned by **Sales**, not Finance | `approver_role` / `approver` is too narrow, and the reasons the UI shows would be wrong |
| No revocation | **Revoke** is one of the two changes (`revoked_on`, RR-12), and the served register shows it | The register needs a *revoked* status and a revoke action |
| No submit flow, so no refusals shown | Every refusal names its rule (RR-1 … RR-14): no backdating, no silent overlap, stale base, text ⊆ terms, ids that resolve | "Register a version" with rule-named refusals is missing from Manage |
| The decision record is discount-shaped: `eligibility`, one `approver`, and an invented `ROUTED` outcome | `commercial_eligibility`, `evidence`, `missing_evidence`; credit has `approvers[]` with approval or concurrence; SLA has its own fields. Route mode sets **flags** (incident, routed, withheld fields), not an outcome | `DecisionRecord` must cover three decision types and carry `flags` |
| No narrow judgments | The demo's close is "evidence → **narrow judgments (with confidence)** → rules → outcome → approver → conditions" | The decision panel has no place for Jev's judgments or their confidence |

**Proposed:** I revise `lib/types.ts` into a v1.2 contract from the lab's actual objects, with the
three points above that need your call (§3, items 1 and 2), **before** the lab session starts
building. Otherwise it builds to shapes we already know are wrong.

### 2.2 The demo organization: Lumen → Northstar

- **Name collisions.** Lumen's **Priya Raman** (Sales Ops) and **Marcus Reid** (platform on-call)
  share first names with Northstar's **Priya Shah** (Finance Manager) and **Marcus Adeyemi** (Director
  of Customer Support). Both will be on the same sign-in page. Lumen's invented **Rosa Alvarez** has
  Northstar's **Elena Novak**'s job; **Nadia Okafor** clashes with G-37's **Dana Okafor**.
- **Operate has no Northstar persona.** Running the platform isn't a Northstar job. Either the
  Northstar demo adds an IT or platform admin, or Operate stays out of it.
- **The foundation side needs Northstar too.** Ask, Sources, Explore, Pipelines and Runs read the
  knowledge foundation. A whole-app Northstar demo needs `dataset/evidence` loaded there as well as
  the OWM service.
- **Usability round 2** is written for Lumen.

### 2.3 The foundation is changing, and so is the name

- **Utopia's shape is baked into web-next.** Its "live" endpoints, its pipeline (parse → index →
  extract → project → reason) and its graph-projection runs are all Utopia's. With Docling +
  langextract, those stages change. **Stop deepening Utopia-specific screens.** In particular, drop
  v1's adopt criterion "port Ontology, Mappings and Rules into Manage › Structure". Put a
  foundation-neutral contract (documents, passages with byte ranges, facts, stages) in front of the
  screens.
- **Byte ranges are an opportunity:** *Why this answer?* can highlight the exact span in the source.
  That is "trust with confidence" made visible.
- **Rebranding is bigger than "about a dozen strings":** about 26 component lines and 18 demo-data
  lines, including "Utopia procedure agent" that v1.1 added. Before an outside showing they all go,
  but **to what name**: BlueLeaf (the client demo's brand) or Sovera (the thesis)?

### 2.4 Who decides: the OWM, not the chat model; and agents are missing from the IA

- **v1.1 shows decisions as something the answer produces** (RUN-1238 has a model deciding). G-23
  says the opposite: the kernel and Jev decide, at a fraction of a cent; the agent explains. The
  decision record should say *decided by the OWM (rules + N judgments)* and show the agent as the
  explainer.
- **Agents aren't actors anywhere in the IA.** With Agno chosen and "thousands of agents" in the
  value statement, the UI needs to answer: which agents exist, what each may propose or act on, and
  what they did. Most likely that's an *Agents* area in Manage (what they may do) and agent runs in
  Operate (what they did). This is a new IA decision, not a screen tweak.

### 2.5 "Trust with confidence": what the UI shows, and what it claims

- **An overclaim to fix now.** Approvals says "Nothing acts on the decision until it's resolved".
  The lab says plainly that **executors that honour blocking conditions aren't built**. Reword it to
  what's true ("systems that honour conditions won't act until…"), or mark it as roadmap.
- **Show confidence where it's calibrated:** on the narrow judgments in the decision record, and on
  Review's identity cards ("sent to you because the two judges disagreed", G-18 R2).
- **Show the ROI numbers buyers ask for** on Manage › Usage:
  - review minutes per 100 agent decisions (G-18);
  - cost per decision (G-23);
  - attacks blocked.

### 2.6 Where the proof rounds run

The technical demo wants baseline-against-OWM tallies (×5) "in the product UI, not a lab console",
fed by the MCP server's experimenter mode. web-next's IA has no place for a baseline, and shouldn't:
a comparison with a deliberately ungoverned agent isn't a product screen.

**Proposed:** a presenter route group in web-next (`/present`), behind a demo flag and outside the
product navigation, that reads the MCP and OWM run logs and shows the tallies and the labelled
replays.

## 3. Decisions needed from you

| # | Decision | My recommendation |
|---|---|---|
| 1 | **The registration workflow.** Keep submit-then-approve (a pending queue in the OWM service), or make the UI single-step like the registrar? | **Keep two steps** in the service. Run the RR checks at submit and again at approval (RR-4, RR-13). A rule failure comes back as a refusal naming the rule; an approver's "no" on substance stays a decline with a note |
| 2 | **Agents' proposals.** Can an agent's draft sit in the queue for a person to submit? | Yes: the service records `proposed_by` (an agent) and a person submits it (RR-2 already allows this) |
| 3 | **Lumen's future** | Northstar for every demo. Keep Lumen only as an offline usability fixture until the OWM API lands, with the colliding names changed |
| 4 | **Operate in the Northstar demo** | Add one platform-admin persona, outside Northstar's org chart |
| 5 | **Brand for web-next** | Needed before the rebrand. BlueLeaf for the product, if Sovera is the company |
| 6 | **Agents in the IA** | An Agents area in Manage, plus agent runs in Operate. I'd sketch it before building |
| 7 | **Proof rounds** | `/present` in web-next, behind a flag |
| 8 | **Your action:** the sealed register attack set | It blocks the next credibility item. The brief is ready |

## 4. Proposed order

1. **Now (UX):**
   - fix the conditions overclaim;
   - write the v1.2 contract (§2.1) and agree it with the lab;
   - add `OWM_API_URL` routing and the Northstar sign-in to web-next.
2. **Lab session:** the OWM service for #16–#20 against v1.2, on the modules the MCP `service/` core
   reuses.
3. **UX:** switch the governance screens to live Northstar data, so the Sample badges go; then the
   decision record (judgments, flags, three types); then `/present`.
4. **After it works:** the rebrand and the foundation-neutral contract.
5. **In parallel:** your attack set → register attacks; set G once the MCP build reaches it; G-39.

## 5. Already settled

My v1.1 open questions (glowing-garbanzo, `ux-v1-use-manage-operate.md` §11.6):

- **#1, approval rights:** they come from the OWM's org data (the department head or an Executive),
  not from a UI role system. What's left is binding a web-next sign-in to an employee id (RR-1's
  `acting_as`).
- **#2, two services:** decided. web-next uses `OWM_API_URL` alongside the foundation proxy.
- **#6, how to read old answers:** this is **G-38** ("as known at"), on the board and untested. Don't
  build more on it until it runs.

## 6. Housekeeping

- `docs/review-runs-and-docs-2026-10-05.md` on `claude/blissful-darwin-4va0gx` is a dated record
  that was never merged. It now carries this review too. Merge it, or leave it on the branch.
- The client demo (`kloudtaxi/blueleaf-demo`) is pinned at `dataset-2026-10-03`, which predates the
  register and `conditions`. The sequencing feedback already lists the requests to the lab.

## 7. Since this review (2026-10-09)

### The user's decision: blocking conditions (Lab Ledger G-45)

- **Now:** web-next says only what the record does ("marked not ready to act on"). Done in
  glowing-garbanzo at `cecc8e9`. That covers the three lines G-45 quotes, plus two of the same
  class.
- **In the OWM API** (shiny-waffle, on the `owm-decisions` contract), a **clearance check** rather
  than an "act" endpoint:
  - `POST /decisions/{id}/clearance {action, actor}` returns either a logged clearance, or a refusal
    that lists the open conditions;
  - #19 holds an approval request while a blocking condition is open;
  - resolving a condition re-runs the decision.
- **When it ships,** web-next adds a **Try to act** button that shows the refusal, labelled as the
  OWM's own check. Until then, the reworded copy stays. web-next lists it as endpoint #21
  (`owm/docs/ops-api-gaps.md`).

### What changed on `main` that this review should note

- **The contract (§2.1):** the demo API uses the future `owm-decisions` contract from day one
  (`docs/sovera-owm-vs-semantica-and-rebuild-2026-10-09.md`). The v1.2 shapes proposed in §2.1 are
  therefore written against `owm-decisions`, with web-next adapting to them, not the other way round.
- **§3 item 8 is done:** the user wrote the sealed attack set, and the run admitted 0 of 14 attacks
  (`runs/2026-10-08-register-attacks`; follow-up on G-44).

### The user's answers to §3 (2026-10-09)

1. **Registration workflow:** two steps (a pending queue in the OWM service).
2. **Agents' proposals:** covered by the agents sketch (below); `proposed_by` may be an agent.
3. **Lumen:** an offline test fixture only.
4. **Operate:** add a platform-admin persona, outside Northstar's org chart.
5. **Brand:** BlueLeaf is the product; Sovera is the company.
6. **Agents:** sketch before building, "and don't hold back". See
   `owm/docs/ux-v1.2-agents-sketch.md` in glowing-garbanzo, branch `v1/use-manage-operate`.
7. **Proof rounds:** `/present` in web-next, behind a flag.
8. **The attack set:** done (see above).

### The agents sketch, reviewed and corrected (2026-10-09)

- The lab reviewed it (`docs/agents-sketch-review-2026-10-09.md`).
- The user decided:
  - phase 0 (who acted, in the contract) now;
  - phase 1 (clearance) with the OWM API;
  - phases 2–3 held until mandates are lab-tested.
- Three fixes are applied in glowing-garbanzo `3974d2e`:
  - the re-run ratchet (G-46);
  - exact match by default;
  - clearance bound to `{decision_id, decision_version, action, params, actor}` (G-45).
- **Next:** the v1.2 contract on `owm-decisions`, phase 0 plus clearance.
