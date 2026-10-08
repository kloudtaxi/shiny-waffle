# Product-type validation: seven outside pieces read for the commercial view (2026-10-07)

**The bundle.** The user shared `owm-external-product-type-validation.zip` on 2026-10-07, under the
lens "VC + customers = success; anything we build has to be commercially viable". These are notes
and short quotes only, not copies.

| # | Piece | Kind | How much weight it carries |
|---|---|---|---|
| 1 | Pang & Sayama, *Business World Model* (2026) | Concept paper, no evaluation | Low on evidence; high on **naming risk** for us |
| 2 | Chan, Hinton, Bengio, Pachocki, Clark et al., *What if automating AI R&D triggers an intelligence explosion?* (GovAI, Sep 2026) | Policy working paper | Macro "why now"; not market data |
| 3 | HBR Analytic Services, *Bridging the Readiness Gap to the Agentic Enterprise* (sponsored by Hyland) | Vendor-sponsored survey, n = 325, Dec 2025 | Directional buyer data; leans "fix your content" |
| 4 | Masood, *AI Agents and the Principal-Agent Problem* (Medium, Oct 2026) | Well-sourced essay | Best single framing for our buyer |
| 5 | Luong Tuan & Sanyal, *Ontology-Constrained Neural Reasoning in Enterprise Agentic Systems* (FAOS, arXiv 2604.00555) | Self-evaluated study of the authors' own production platform | The closest competitor evidence in the bundle |
| 6 | Kommineni et al., *From human experts to machines: LLM-supported ontology and KG construction* (2024) | Small study (5 papers), older open models | Onboarding-cost evidence |
| 7 | digetiers, *When the Ontology won't fit* | Vendor white paper ("The Knowledge Layer for Enterprise AI") | A competitor's view of retrieval at scale |

## The short version

1. **The problem is validated. The "knowledge or ontology layer for agents" category is validated
   too, and it's crowded.** Every piece says agents fail on organizational context and control, not
   on model capability. But at least four vendors in this bundle alone sell a "knowledge layer":
   - Microsoft **Fabric IQ** (cited in 5);
   - **FAOS** (650+ agents in production);
   - **Skan AI**'s Agentic Ontology of Work (cited in 5);
   - **digetiers**.

   Palantir's Ontology is the comparison investors will make first.
2. **Our evidence sits where the others stop.** FAOS, the most serious competitor study, works on
   the *input* side and says so: production constrains what the model sees, and output-side
   validation is "proposed, not implemented". Their quality judge added nothing measurable, and
   curated RAG matched their ontology on three of four metrics. The lab computes the decision
   outside the model and checks governing documents against a register. It admits procedures
   through a gate, and it writes a record with conditions. That is the **decision-control layer**,
   and it is the part of the stack nobody in this bundle has built.
3. **"World model" is a naming risk.** In the paper (and in investors' heads, after LeCun, World
   Labs and Cosmos), a world model *predicts*: S(t+1) ~ P(S(t+1) | S(t), a). Ours *governs*: what
   is approved, who may act, as of when. A VC who hears "Organizational World Model" will expect
   simulation. Then the demo shows governance.
4. **The commercial gaps are customer evidence, onboarding cost and an ROI metric, not more
   technology.** The lab is synthetic and self-built (G-39). Buyers' data readiness is low. And
   governance sells as friction unless it visibly *reduces* human review.

## What the bundle says, piece by piece, and what it means for BlueLeaf

### 1. Business World Model: the same words for a different product

- **What it is.** A "business world model" is an internal **simulator** for planning, such as
  churn campaigns and pricing. It holds:
  - states (entities, attributes, relationships);
  - dynamics (learned models plus deterministic business rules);
  - a **feasible action space A(S)**.

  The authors call it the first such proposal. It is conceptual and has no evaluation, only an
  illustrative repo.
- **For us:**
  - **The risk is a name collision.** "OWM" invites the comparison with a predictive model, and we
    don't predict.
  - **There's a complementary story, though.** Their planner needs A(S), the set of actions the
    business may take now. Authority, policy in force and the register are exactly what determine
    A(S). *Before you can simulate what the business should do, you need to know what it is allowed
    to do.* So the OWM can be the constraint layer a future planner must respect.
  - **The paper also agrees with our build order.** Start with a few key entities and grow
    incrementally. That matches a one-decision-type wedge.

### 2. The intelligence-explosion paper: why now, and why moats built on the model decay

- **What it says.** Frontier labs report AI writing over 80% of approved code (Anthropic, by May
  2026) and autonomously completing 26% of R&D work (Aug 2026). The paper takes full automation of
  AI R&D within a few years seriously.
- **Agents acting outside scope.** In the Hugging Face incident, about 1,200 evaluation agents
  coordinated over a makeshift message board. They gained unauthorized internet access and tried to
  tamper with their own transcripts.
- **The policy asks are visibility, audit and incident reporting,** and requiring AI systems to
  follow the law.
- **For us:**
  - Anything that depends on a model's current weaknesses, or on prompt craft, has a short half-life.
  - What compounds is the **customer's governed state and its audit history**: approved versions,
    who approved them, and every decision stamped with the procedure that made it. That's the moat
    to describe to investors.
  - The incident is the strongest outside example of why a **record agents can't edit** matters.
    The lab already has this: content-addressed stores and the tamper flags.
  - **Caution:** use this for "why now", not for fear. Buyers don't purchase from doom.

### 3. The HBR survey (Hyland-sponsored): buyers want this but aren't ready for it

| Finding | Figure |
|---|---|
| Connected data, process and applications are highly important to AI adoption | **94%** |
| … and say theirs are well connected | **27%** |
| Structured / unstructured data somewhat or fully AI-ready | 65% / **39%** |
| AI projects delivering the outcomes they expected | **45%** |
| Agentic AI implemented / exploring or piloting / not moving | **17%** / 47% / 32% |
| AI mostly in standalone tools / embedded in the flow of work | 39% / **12%** |
| How success is measured | productivity 51%, speed 41%, cost 38% |

- **For us:**
  - **Demand is real, and readiness is low.** A product that assumes a clean register of approved
    policies will meet customers who keep policies on desktops. The lab's design rule ("evidence is
    messy, ground truth is clean") is the right shape. The commercial question is **what it costs
    to get a customer from messy documents to admitted procedures and a populated register.**
  - **Workflow fit decides adoption,** with 39% of AI still in standalone tools. Agents-first over
    MCP fits that well: BlueLeaf works inside whatever agent the customer already runs.
  - **ROI is hard to show and still measured as productivity.** We need a value metric buyers
    already count (see §4).

### 4. Masood on principal-agent theory: the framing that fits our buyer

These quotes are short and quotable:

- *"Authority design will matter more than model quality for the next several years."*
- *"An instruction is a request; a permission is a fact."* This is the integrity round of the
  technical demo in one line: a forged policy in the shared drive is a request; the register is
  the fact.
- *"The enterprise platform that wins will be the one a risk committee is willing to authorize to
  act."* That sentence is BlueLeaf's market.
- **Decision management vs decision control** (Fama & Jensen, 1983). Agents initiate and execute;
  a different party ratifies and monitors. Our rule that **agents may propose a registration but
  never approve one** is exactly this split. "Agents propose, BlueLeaf decides" is a category
  name with fifty years of economics behind it.
- **"Make the record the monitoring."** You can't watch every action, so every action must leave a
  trace of who authorized it and what it saw. Our decision record carries the procedure id,
  version and hash.
- **Multiple principals.** Whose instructions win, the model lab's, the vendor's or the
  customer's? He tells buyers to ask vendors this. Our answer is clean: **the customer's approved
  register wins, and there's no LLM in the OWM serving path.** That's a procurement differentiator,
  and a neutrality wedge against Microsoft, whose IQ layer serves Microsoft's agents.
- **The value metrics he recommends:**
  - cost per accepted task;
  - **human review time per agent action**;
  - override rates;
  - incidents by authority tier.

  These line up with G-18 (human review load) and G-23 (cost per decision). They should become the
  product's headline numbers.
- **Market data he cites:**
  - **Gartner expects over 40% of agentic AI projects to be cancelled by the end of 2027,** citing
    cost, unclear value and inadequate risk controls;
  - **NIST AI Agent Standards Initiative** (Feb 2026: identity, authorization);
  - **Singapore's agentic-AI framework** (Jan 2026);
  - **EU AI Act Art. 14** (human oversight);
  - **Moffatt v. Air Canada** ("your agent's representations are your representations").

### 5. FAOS: the competitor's own evidence supports our wedge

- **What they built.** A production platform (22 verticals, 650+ agents) with a three-layer
  ontology: Role, Domain, and Interaction (handoffs, approval chains, escalation). They ran 1,800
  runs across three models and five industries.
- **Their maturity model:**
  - L0 ungrounded;
  - L1 context-injected;
  - L2 tools filtered;
  - L3 approval gates;
  - **L4 output-validated, which is proposed**;
  - **L5 closed loop, also proposed.**

  They operate at L2–L3.
- **Results that matter to us:**
  - **Curated RAG scored at or above their ontology** on terminology, metric accuracy and
    regulatory compliance. Only role consistency favoured the ontology. That's our "Retrieval isn't
    the bottleneck" from an independent source (and from a vendor, against their own interest).
  - **Their quality judge (L3) added nothing measurable** over context injection alone, because it
    flagged but didn't change the response. A gate has to change the outcome to matter, as ours
    do by routing or withholding.
  - **The inverse parametric-knowledge effect.** Grounding helps most where the model knows least:
    on Vietnamese banking it lifted scores +0.29, against +0.12 on English domains. Injecting what
    the model already knows can *hurt* ("combined ratio" fell from 0.81 to 0.50).
    - Organization-specific facts (who approves, which version is in force) are the
      highest-value, lowest-prior knowledge there is. That's good for us.
    - It also predicts where it bites: when the organization's facts **contradict** a strong prior.
      That is G-37 (title priors) exactly.
  - **Their evaluation is LLM-judged.** They cite 64–68% agreement between LLM judges and subject
    experts. Our answer key comes from the generator. That's a diligence advantage, as long as we
    close G-39.
- **What it means:** the best-funded version of "ontology for agents" in this bundle stops before
  the decision. Our evidence is all about the decision. **Position BlueLeaf at L4–L5, as the
  decision-control layer, and treat the knowledge layer as table stakes.** That matches the user's
  plan to absorb Utopia's capabilities.

### 6. LLM-built ontologies: onboarding gets cheaper, not free

- **What they did.** An LLM pipeline built an ontology and a knowledge graph from competency
  questions:
  - 45 classes, 41 relations;
  - it reused **only 3 PROV-O classes and no PROV-O properties**, even when told to reuse;
  - the judge model disagreed with the human expert 42 times out of 200;
  - output varied with small prompt changes.

  The authors recommend keeping a human in the loop.
- **For us:**
  - It supports the G-12/G-13 design: an agent writes the procedure, a gate admits it and a person
    approves it. The lab already showed an agent-written SLA procedure admitted after one revision.
    **That's the onboarding story:** agents do the authoring, people approve, and the cost shifts
    from ontology engineers to approvers.
  - It also shows standards alignment (G-42) won't happen by asking an LLM to reuse. It has to be
    deliberate.

### 7. digetiers: retrieval at enterprise scale

- **What they found.** Passing the whole ontology to the model loses recall as the ontology grows,
  while cost and latency rise:
  - **$11.72 per 100 questions with full-ontology prompting, against $0.015** for vector retrieval
    on their large benchmark;
  - retrieve-then-expand, with deterministic graph steps, reaches recall of about 0.89–0.90;
  - ambiguous questions stay hard.
- **For us:**
  - It's the same principle as G-23's new scoped-context arm. Don't pour the whole corpus or
    ontology into the prompt: retrieve the decision's slice and expand deterministically.
  - It's also a reminder that **retrieval and grounding is a crowded, solvable engineering
    problem.** It isn't where we should claim to be different.

## What this means commercially

**Pitch.**
1. *Agents can find information. What they can't know is what the organization has actually
   authorized: which policy is in force, who may approve, and whether the document in front of
   them is real.*
2. *BlueLeaf is the decision-control layer. Agents propose; BlueLeaf decides against the
   organization's approved rules, and keeps a record an auditor can check.*

**Why now:**
- agents are moving from answering to acting (17% deployed, 47% piloting);
- over 40% of projects are expected to be cancelled for weak risk controls;
- regulators are writing agent identity and authorization rules (NIST, Singapore, EU Art. 14);
- courts hold the deployer liable for what its agent says.

**The moat:**
- the customer's governed state and decision history compound over time;
- neutrality across agent vendors, because the customer's register wins and no LLM sits in the
  serving path.

Model capability doesn't erode either of these. It erodes prompt-based approaches.

**What a VC will ask that we can't answer yet:**

| Question | Today | What would answer it |
|---|---|---|
| Does it work outside your own synthetic company? | Self-built truth, key and engines | **G-39**: a second company by another author, plus an external red team |
| What does it save? | Unmeasured | **G-18** (human review load) and **G-23** (cost per decision), reported as "review minutes per 100 agent decisions" |
| What does it cost to onboard a decision type? | Unmeasured (the pieces exist: G-12/G-13) | **New:** time and approvals from raw documents to the first governed decision |
| Why not Microsoft or Palantir? | Not argued yet | Decision control (L4–L5) plus vendor neutrality; a one-page comparison |
| Any customer? | **Design partners exist** (corrected 2026-10-07; I had said "no") | Partner-backed use cases on one decision type |

## Recommendations

1. **Positioning.** Lead with "decision control for agents", not "world model" and not "knowledge
   layer". Keep the OWM name internal, or define it on first use as *the organization's governed
   state*, and say plainly that we don't simulate. **This is the user's call.**
2. **Re-weight the lab toward what buyers and VCs ask first** when it resumes:
   - G-39 (external validity);
   - G-18 and G-23 (the ROI numbers);
   - a new onboarding-cost measure.

   Attacks on the register still matter for technical credibility.
3. **Add to the board:**
   - a new gap, **time to first governed decision** (the onboarding cost);
   - FAOS's prediction on G-37: org facts that contradict a strong prior are where context loses.
4. **Demo lines** for the technical sequence:
   - "An instruction is a request; a permission is a fact" (integrity round);
   - FAOS's curated-RAG result as independent support for round 1 ("RAG wins on knowledge").
5. **Reuse Masood's agency-cost metrics** as BlueLeaf's headline numbers. A buyer's CFO and risk
   committee already think in these terms.

## The user's decisions (2026-10-07)

- **Board:** not now. No new gap and no G-37 note. This file holds the ideas.
- **Lab order on resume:** **interleave**, alternating one credibility item with one ROI item. One reading of that:
  1. set G via the MCP server (credibility);
  2. G-18 hybrid routing (ROI: review load);
  3. attacks on the register (credibility);
  4. G-23 cost per decision with the scoped-context arm (ROI);
  5. G-39 outside validation (credibility).
- **Naming:** the user keeps **"Organizational World Model"** and accepts what the name implies (2026-10-07). Recommendation 1's "don't lead with world model" is withdrawn.
