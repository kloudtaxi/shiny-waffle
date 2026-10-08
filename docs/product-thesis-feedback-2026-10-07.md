# Feedback: "Sovera OWM — Product thesis" (2026-10-07)

**What this is.** Claude's review of the user's product thesis (shared 2026-10-07). It's read
against three things:
- the lab's evidence;
- the outside reading (`docs/reading-list-notes-2026-10-07.md`,
  `docs/product-type-validation-notes-2026-10-07.md`);
- the user's test: "VC + customers = success".

The thesis isn't copied here; only short phrases are quoted.

## The short version

- **The core is right, and the lab backs it.** The central question ("what the organization
  recognizes as true, applicable, authorized, and safe to act on") is the strongest sentence in
  the document. The "governing principle" distinctions are excellent, and each maps to a lab
  result.
- **The headline sells the crowded part and buries the defensible part.** "Organizational
  Intelligence Layer" and "OWM understands" put Sovera in the same category as Microsoft's Fabric
  IQ, digetiers' "Knowledge Layer for Enterprise AI", FAOS and Palantir. The parts nobody else has
  built sit in the middle of the document: governing artifacts, decision records with conditions,
  procedures as admitted data. Those parts carry all the lab's numbers.
- **Governance is drawn outside OWM, but it's the moat.** "OWM understands. Agents reason and
  execute. Governance controls." This splits off the layer where every lab result lives: the
  register, the admission gate, decision validity and the record.
- **It's a platform pitch with no wedge, buyer or "why now".** Eleven "experiences" and no first
  use case. There's no named buyer and no onboarding story. VCs and customers both look for these
  first.
- **The moat claim rests on the least-tested part.** "Accumulated, governed organizational
  understanding" through the memory loop is untested at scale (G-19). What's proven is
  governance.

## What's strong, and the lab result behind each part

| Thesis claim | Lab status | Evidence |
|---|---|---|
| Retrieval is necessary, not sufficient | **Proven** (and independently supported) | Capable agents reconstruct the reasoning on curated evidence; failures appear at governance. FAOS found curated RAG matched their ontology on 3 of 4 metrics |
| "A document can exist without being authoritative" (governing artifacts) | **Proven**: the lab's strongest result | Register: **0/47** attacks worked, against 25/47 for agents alone, across six rounds |
| "A policy can exist without being in force" (time) | **Proven** for "in force on date D" | Time scenarios; procedures in force by date (G-13) |
| "What did the organization believe when…" | **Untested** | G-38 ("as known at") |
| Identity ("Which customer is this?") | **Proven, at a cost** | 0 wrong merges in 41,600 pairs (319 for general-purpose cleanup), but about 4% of pairs routed to people (G-18) |
| "A person can hold a role without having authority" | **Proven within Northstar**, with a confound | Authority is resolved by role from documents. Title priors could explain agents' successes (G-37) |
| Separation of duties | **Partly** | The registrar refuses self-approval and non-employees (G-13). Not yet attacked |
| Decision record (evidence, artifacts, judgments, procedure version) | **Built** | Records are stamped with `procedure: {id, version, sha256}` (G-13) |
| Conditions ("what must happen before action") | **Proven, one rule pending** | Before the `conditions` field, 59/757 answers contradicted their own text. With it, holds reached the record 26/26 on fresh cases, but the blocking flag was wrong on 3 of 8 holds in the re-baseline |
| Procedures as data; "the execution machinery remains generic" | **Proven** | One kernel runs three decision types from YAML. An agent-written SLA procedure was admitted after one revision (G-12/G-13) |
| "AI can propose… OWM governs what becomes state" | **Designed and partly built** | Agents may propose a registration but never approve one. The admission gate exists; the register's own controls haven't been attacked |
| "OWM should not become a giant rules engine" | **Consistent with the build** | The generic kernel plus narrow judgments made 102/102 decisions, against 93/102 for agents |
| Meaning and definitions across systems | **Partial** | G-33 term fidelity is partial |
| The memory loop; "accumulated understanding" as the moat | **Untested at scale** | G-19. On 09-30, a decision stored as a document became undated "facts" cited as evidence; only the typed record avoided stale reuse |
| One OWM, many experiences (search, BI, copilots, simulation…) | **Untested** | Only decision-type experiences have been tested |

## What I'd change

### 1. Lead with the defensible claim, not the crowded category

- **The problem.** "The Organizational Intelligence Layer for AI" and "OWM understands" are the
  words a buyer has already heard from Microsoft (an "IQ layer"), from knowledge-layer vendors,
  and from Palantir. "Understands" is also unmeasurable: a technical buyer will ask "how do you
  know?".
- **What the lab measures instead.** Decisions right, attacks blocked, wrong merges avoided,
  records consistent with their text. Those are *governance* outcomes.
- **Suggested headline options:**
  - "Sovera: **decision control** for enterprise AI";
  - "The layer that decides what AI may treat as true and act on";
  - "**Governed organizational state** for enterprise AI".

  The second keeps the thesis's own best idea.
- **Suggested shortest version:** *"AI can find the answer. Sovera establishes whether the
  organization recognizes it as true, applicable and authorized — and keeps the record."*
- **The technical version you already have is better than the "understands" version:** "RAG
  retrieves. GraphRAG connects. Agents act. **OWM establishes organizational state.**" Use it
  everywhere and drop "OWM understands".
- **Avoid "Sovera teaches it how the organization works".** Enterprise buyers hear "teaches" as
  "trains models on our data", which is the objection you least want.

### 2. Put governance inside the boundary

- **The problem.** The OWM / agent runtime / governance split reads as if governance (identity,
  authorization, policy, decision validity, audit) is someone else's box. But:
  - the "governing artifacts" section;
  - the decision record;
  - and the "Trust is part of the product" section

  are all governance. So are all of the lab's numbers.
- **The fix:**
  - OWM owns **governance of state and decisions**: what becomes recognized state, which artifacts
    govern, whether a decision is valid, and the record.
  - Agent runtimes own execution.
  - The customer's IAM owns credentials and enforcement at the point of action. Sovera supplies
    the decision those systems enforce.
- **Your own stack diagram already says this.** It places Governance between Decision/Agent and
  Action. That's the picture: *agents propose, Sovera decides, systems act.* It's also decision
  management versus decision control (Fama & Jensen), which buyers' risk committees already
  understand.

### 3. Name the wedge, the buyer and "why now"

- **Wedge.** Pick one decision class to land with: **governed approvals for agents**, such as
  discount, credit limit or SLA credit decisions. They're high-frequency, rule-bound, audited, and
  costly when wrong. Keep "one OWM, many experiences" as the expansion path, not the opening.
  Eleven experiences reads as a platform before the first product.
- **Buyer.** The person who must authorize agents to act: the risk committee, the CIO or CTO, the
  CFO for financial approvals. In Masood's words, "the platform a risk committee is willing to
  authorize to act."
- **Why now:**
  - agents are moving from answering to acting (17% deployed, 47% piloting);
  - Gartner expects over 40% of agentic projects to be cancelled by 2027, partly for weak risk
    controls;
  - regulators are writing agent identity and authorization rules (NIST, Singapore, EU AI Act
    Art. 14);
  - courts hold the deployer liable (Moffatt v. Air Canada).
- **Value metric.** Add one sentence on how a customer measures it: human review minutes per 100
  agent decisions, unauthorized actions blocked, decisions with a complete audit trail. These are
  G-18 and G-23 in the lab.

### 4. Narrow the moat to what's proven, and close a gap in the memory loop

- **The claim.** "The moat is accumulated, governed organizational understanding."
- **What I'd claim today:**
  1. **The customer's governed state and decision history**: the approved register, procedure
     versions, and stamped decisions an auditor relies on. This compounds, and it's costly to
     leave.
  2. **Neutrality**: the customer's approved register wins over any model vendor's instructions,
     and there's no LLM in the serving path. Microsoft's IQ layer serves Microsoft's agents. This
     answers Masood's "whose instructions win?" procurement question.
- **The gap.** The memory loop says "every execution can become another source of organizational
  knowledge". It skips the promotion gate the lifecycle section requires. Without that gate, the
  loop is how errors and poisoned outcomes become state; that's how the 09-30 failure happened.
  Suggested wording: **"Every outcome becomes evidence, never state, until it is promoted."**

### 5. Add the evidence (three numbers and one caveat)

The "What our experiments have changed" section is qualitative. A technical or investor reader
will want these:

| Measure | Agents alone | With the OWM |
|---|---|---|
| Decisions right (102) | 93 | 102 |
| Forged or altered governing documents that worked (47) | 25 | 0 |
| Wrong identity merges (41,600 pairs) | 319 | 0 |

**The caveat, stated plainly:** one synthetic company, built by us, three decision types. An
outside red team and a second company by another author come next (G-39). Stating this up front
reads as confidence.

### 6. Smaller points

- **"World Model."** Investors hear "world model" as prediction and simulation (LeCun, World Labs,
  Cosmos; the 2026 *Business World Model* paper). The thesis even lists "simulation" among the
  experiences. Either define OWM on first use as *the organization's governed state* and drop
  "simulation" until there's a plan, or rename it. This is the user's call; it's already flagged.
- **Brand.** The thesis uses **Sovera** as the platform. The client demo and the platform canon
  use **BlueLeaf** (OWM as its kernel). Decide which name each audience sees; perhaps Sovera is the
  company and BlueLeaf the product.
- **Agno.** Naming a runtime in a thesis dates it, and there's no evidence behind the choice yet.
  "Any agent runtime (over MCP)" says the same thing more strongly, and fits agents-first.
- **The knowledge foundation.** The thesis says what OWM is not (RAG, a knowledge graph). Buyers
  will then ask who provides retrieval. Say that the platform **includes** the knowledge
  foundation as table stakes. Don't name the current one.
- **"With what confidence."** Keep confidence on narrow judgments, where it's calibrated. Don't
  promise calibrated confidence on whole decisions, because confidence isn't correctness. The
  thesis's better phrase is already there: "what remains uncertain, and what must happen before
  action." That's `conditions`; make it a named concept. *"A decision isn't just an outcome; it
  carries the conditions under which it's valid"* is distinctive, and nobody else in the reading
  has it.
- **Length and negations.** "Not X, not Y, not Z" appears three times, and the core sentence
  appears three times. A tighter version would be about half the length.

## A suggested one-paragraph version

> **Sovera is the decision-control layer for enterprise AI.** Agents can already find, connect
> and reason over information; what they cannot establish is what the organization recognizes as
> true, applicable and authorized. Sovera's Organizational World Model holds the organization's
> **governed state** — identity, policies in force, authority, obligations and the governing
> documents it actually approved — and decides against it with procedures the organization owns
> as data. Agents propose; Sovera decides, records the evidence, version and conditions, and
> hands systems a decision they can act on and an auditor can check. In our tests, agents alone
> got 93 of 102 decisions right and were fooled by 25 of 47 forged documents; with the OWM, 102
> and 0.
