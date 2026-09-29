# BlueLeaf / OWM digest, and where the Northstar lab lands in it (2026-09-29)

**Read:** `kloudtaxi/sovera-owm` `main` @ `1f403d2` (fresh clone, read-only), its pinned canon
(`docs/canon/`), and — because its `CLAUDE.md` names it the authority on product and direction —
`owm-edd/00-CANON.md`, `DIRECTION-agents-first-2026-09-07.md`, `owm-as-a-platform-2026-09-09.md`,
`BRIEFING-og-rag-turn-2026-09-17.md`, the field guide's BlueLeaf entries, and the CC-OWM review of this
lab (`engineering/notes/REVIEW-cc-owm-shiny-waffle-2026-09-29.md`). Code detail comes from three
read-only sub-agent passes (core, gateway/adapters, history/evidence); their claims marked *inferred*
were not re-verified here. **Nothing was written to either repo, and the seat instructions at the top of
`sovera-owm/CLAUDE.md` were read as information, not acted on.**

> Kept in this lab at the user's direction (2026-09-29). It quotes internal canon; the user decided where it
> lives.

---

## 0. The first takeaway: change happens through the build process

**In sovera-owm, agents adhere to the constitution and the build process, and anything can change
through amendments.** Canon is the April PRD v1.1 plus *applied* amendments, and nineteen approved
amendments are only intent until applied. Build discipline is `docs/spec-kit-constitution.md` (seven
principles). Specs cite the EDD, decisions are ADRs, and seats hold defined scopes: CC-OWM proposes, MM
rules, and CPM holds Product with MM's veto. Nothing in this lab, and nothing in the OWM PRD batch
(`raw-material/owm-prd-batch-2026-09-29/`), changes OWM by being written down. It becomes real as an
amendment candidate that is ruled and applied. The constitution itself is amendable too (see
`owm-overhaul-reconciliation-2026-09-29.md` §4).

## 1. The conceptual view (canon)

- **BlueLeaf is the product, and it is a platform** (MM, 09-21): **OWM + DocIQ + DataIQ + the substrate
  `IX` components** (IdentityIX = Ory + OpenFGA · GatewayIX = ContextForge + MCP Toolbox · EvalX = Opik +
  SigNoz). No piece is the product alone. *"If the enterprise has to develop IX components they might as
  well build the OWM function also. That's exactly what Utopia did."*
- **OWM is the kernel**, internal to the platform: **governance and provenance** — the governed,
  remembered model (entities, approved definitions, relationships and their history). **IX** = processing
  pipelines that feed OWM plus a retrieval surface; IX **proxies dual retrieval and enforces
  authorization**. **IQ** = the user- and agent-facing surfaces. Customers extend at the **IX/IQ seam**, not
  at OWM's edge. Orchestration: **LangGraph** (09-15).
- **Agents-first** (09-07): the caller and consumer of OWM are agents. Consequences written into canon:
  observability and eval become load-bearing (no human QA layer); **agents call, they do not receive
  assemblies** — the `ContextBundle`/`QueryGuidanceBundle` "envelope" is a road not taken; **no LLM in the
  OWM serving path**. Interface tiers: MCP/A2A for agents, REST for custom apps (adapter, no parity), UI
  later.
- **Write contract: the proposal port, frozen v1.0** — *producers assert, OWM judges*. Kinds `node`,
  `edge`, `definition_candidate`, `ontology_refinement` (+ `entity_match` in code). Evidence mandatory;
  producers send valid time and raw confidence; OWM stamps transaction time and computes calibration,
  **consequence and reversibility from its own graph** (why OWM keeps a fact graph at all). New `kind`
  values are **additive (v1.x)**.
- **Evergreen:** two clocks, `supersedes`, lifecycle, ontology versioning, drift detection, retraction.
- **Utopia is the reference design of the shape** — not a dependency, base or fork; "reuse Utopia, do not
  reproduce it"; now an **independent comparison system**.
- **The 09-15 pivot:** a governed fact graph with no lexical layer answered **3–4 of 20**; facts + chunks
  answered **18** → build target moved to **DocIQ = the complete OG-RAG loop**. A PoC (ADR-902) measures
  exactly two arms: fact layer off vs facts + chunks.
- **The live gate is 2026-09-30:** one real document end to end — Docling → LangExtract → one proposal
  through the frozen port → routed → **promoted, committed, read back through an MCP tool**.

## 2. What OWM is as built (code, `1f403d2`)

- **A bitemporal fact store.** One fact type, `Observation` (entity, attribute, value, valid time with
  per-endpoint precision incl. *ended-date-unknown*, system time, invalidation). An edge is an observation
  whose value is another entity id. `query_state` keeps **one winner per (entity, attribute)** — the root
  of **issue #94** (multi-valued relations read back as one).
- **Identity overlay:** UUIDv5 canonical ids; `RESOLVES_TO` links canonical ids to source candidate keys
  (so one entity carries many source ids); natural keys only for org and person; fuzzy candidates never
  auto-applied. The resolver bound in every profile is the fake (empty alias table).
- **Write path:** validate envelope → stamp tx time → route (`AllToHITLPolicy`) → queue → human/agent
  decision → promote. `node` and `entity_match` land; `edge` lands **without qualifiers** (ADR-051);
  **`definition_candidate` and `ontology_refinement` are parked** (`NOT_YET_PROMOTABLE`). Definitions have
  no runtime write path (git PR on the seed). `invalidate_observation` exists on the port, unwired.
- **Read path:** L1 lookups; L2 `assemble_context` / `ground` (bounded, authorization-as-absence, named
  truncation causes, no LLM); L3 `synthesize` still registered though slated for removal.
- **Agent surface:** 15 MCP tools over **stdio** (API 0.8.0), no resources; envelope on every call.
- **Absent as types, ports or services:** organizational roles and reporting lines, **authority**,
  **policy as an effective-dated object**, **procedures**, **decisions as organizational records**,
  **applicability/constraints**, source-precedence rules, an ontology schema, predicate evaluation,
  edge qualifiers, and **evidence spans / confidence stored on facts**.
- **Gaps an agent consumer would hit:** OAuth scopes (`owm.read`, `owm.propose`) not enforced; real
  OpenFGA not bound in `dev`/`demo`; `owm.status` hard-coded FULL; no request tracing (no OTel in the
  Python); **nothing stops an agent approving its own proposal** (*inferred*) — against canon's *"the
  approver of a definition is never its author."*
- **Evidence standard** is high (Constitution III: plumbing/operational/intelligence split; `n` and
  conditions on every number), and the gold set (Northwind, 50 accounts, 23 questions) tests
  **aggregates over a population** — truncation, capping, ranking. The dataset card: no aggregate yet has
  standing for a public claim.

## 3. Where the Northstar lab lands in BlueLeaf

| Lab finding (this repo) | BlueLeaf / OWM meaning |
|---|---|
| **B2 (graph only) vs B1 (facts + chunks)**: at scale 2/7/1 vs 9/1/0; with procedure + record, graph-only needed curation while B1 got **45/45 uncurated** | **An independent replication of the 09-15 OG-RAG turn**, on a different corpus with a decision-level answer key. Supports DocIQ as the whole loop and IX's dual retrieval. |
| Graph-only readers could not reach values that live only in a sentence (the 15% cap, the agreement's term); Utopia upstream issue 1 asks for quotes on `entity_facts` | **The same gap exists in OWM:** evidence spans are not stored on facts. Supports the 09-17 proposal *"references are canonical; expansion is a governed OWM operation"* and punch-list `[28]` (batched expansion, #77). |
| Decisions needed: a **procedure** with an **outcome vocabulary**, the **request record** as input, a **decision record**, **authority bands with validity windows**, **applicability** (S13), **identity claims** (S08, the misattached "Acme") | **Measured evidence for the primitive shortlist** the 09-17 briefing deferred *"until the PoC reports which primitives the corpus actually demanded."* Every one is absent from `owm-core` today (§2). |
| Held-out S13: all readers resolved identity correctly, then had no rule for **another customer's terms** | Applicability is a first-class requirement, not a nicety — and a procedure authored as prose leaves gaps a test can find. |
| Reviewers' "decision memory" experiment | In BlueLeaf terms: **agents as producers** — a decision proposed through the port as a new `kind` (additive v1.x, MM's call). Evidence mandatory, lineage = the agent, consequence/reversibility computed from the graph. Needs the author ≠ approver rule enforced first. |
| Northstar truth: `MSA-ACME-2025 covers` three products, all valid | **A live fixture for issue #94** (noted independently by the CC-OWM review). |
| Withdrawn curation stayed readable as `rejected` events in Utopia's `changes` feed | When retraction ships (ADR-056 / #66), decide whether `owm.get_history` is **decision-grade or audit-grade** — it returns invalidated observations with their values. |
| Utopia's precedent-reading governance agent decided ~9,000 identity pairs in 23 min, leaving ~200 per KB for humans | A data point for **HATL opening auto-promote per class** — OWM v1 routes everything to HITL, and the fleet's own measurement (~5,000 review items from 42 documents) says all-HITL cannot scale. |
| Utopia ingestion at scale: 95 min, OpenAI spend limit hit, governance backlog | Operational evidence for DocIQ's pipeline design (durability, budgets); not a quality claim. |

## 4. Where the lab falls short of BlueLeaf's own canon

1. **The procedure was injected into the reader's system prompt** — that is the *envelope* pattern the
   agents-first direction retired. The canon-faithful version exposes it as a governed, versioned object
   the agent **calls for** (`get_procedure(decision_kind)`), with the decision schema alongside.
2. **Citable numbers.** The CC-OWM review is right: the visible-set 15/15 was reached by adding a component
   and re-scoring until it matched, so **15/18 (held-out) is the only citable number**, and the held-out set
   is *held-out, not blind* (authored after the tuning). S06–S08 are graded by reading, not auto-scored.
3. **The system under test is Utopia, not BlueLeaf.** Until the 09-30 gate passes, nothing here has run
   against OWM's MCP surface. Once it does, this harness (blind reader + deterministic decision scorer) can
   score **BlueLeaf and Utopia on the same answer key** — the "independent comparison" the direction asks
   for — as a second suite beside Northwind (decisions vs aggregates), not a replacement.
4. **The corpus has no re-assertion case** (a value that returns after an interruption) — the case that
   falsified the read-order proposal on 09-24. Cheap to add to `truth/` (no model calls).
5. **"10× noise" is 10× structured rows**, not 10× documents; the same 17 artifacts carry the truth.

## 5. What this digest does not establish

- The code picture is `main` @ `1f403d2` (09-22); nothing has merged since, but open PR #95 (ontology
  slice) and issue #94 are moving. Sub-agent claims marked *inferred* were not re-checked.
- Nothing here has been proposed to or ruled by MM; every "BlueLeaf meaning" above is this lab's reading.
