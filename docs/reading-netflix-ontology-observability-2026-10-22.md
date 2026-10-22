# Reading notes: Netflix's ontology-driven observability, against the prototype spec (2026-10-22)

**Source:** *Ontology-Driven Observability: Building an End-to-End Knowledge Graph at Netflix Scale*,
by Prasanna Vijayanathan and Renzo Sanchez-Silva, on the Netflix Technology Blog (October 2026). The
user shared it on 2026-10-22, while the prototype spec was being brainstormed (sections 1–4 approved).
These are notes and citations, not a copy of the article.

**In one line:** cross-system investigations were slow because each tool named the same things
differently. Netflix wrote one machine-readable agreement about its operational entities (RDF, OWL,
SHACL and SPARQL), made model-driven enrichers emit only typed triples, and put agents (AutoRCA) on top
of the resulting graph.

## 1. What the article says

- **The bottleneck is identity, not compute.** One thing is an application in one system, a service in
  a second and a cluster in a third. Joining them took a person who carried the mapping in their head.
  Most of a four-hour investigation went into rebuilding relationships the systems already knew.
- **Identity is modelled first.** They refused a generic `Service` type because the word meant four
  things. Every application resolves to one type and is checked against one software catalog (about
  49,000 entries) before it exists in the graph. Unchecked strings never become applications.
- **Stochastic tools are constrained by types.** An LLM may write any prose, but it can't emit a triple
  that breaks the type system. Each enricher reads noisy input and emits only typed triples, in a fixed
  order, each reading what the earlier ones wrote.
- **Proposals carry their evidence.** The correlation engine proposes causal chains, with a confidence
  score and the graph records that produced them. Weak chains (below 0.6) are dropped.
- **Ontology changes are reviewed.** Agents may propose fixes, enrichers and ontology changes. People
  approve every proposal.
- **Concepts are kept apart from instances.** Concepts change on a human timescale and instances change
  continuously.
- **Enrichment is best-effort.** A slow dependency degrades the graph and never blocks the harvest.
- **Next for them:** joining this domain ontology to *Upper*, the domain-modelling language of Netflix's
  Unified Data Architecture. Upper projects domain models into concrete schemas. They'll start with a
  proof of concept for one entity (incidents) and converge from what they learn.

## 2. Where it confirms the prototype's design

| Their lesson | The prototype's decision |
|---|---|
| One explicit, machine-readable agreement about entities, so specialists share one vocabulary without knowing each other | The core vocabulary in `contract/` (section 3, option A). Packs, agents and foundations meet on it |
| One authoritative catalog per entity kind | The org profile binds each core type to one source per org |
| Separate concepts from instances | Packs and profiles are registered and versioned, approved by two people, on a human timescale. Decisions and records are instances, written continuously |
| Constrain stochastic tools with a narrow output contract | Jev questions are already typed (`type: choice` with fixed criteria in `credit_v3.yaml`). Findings and claims are typed by the pack's schemas |
| Proposals carry the evidence that produced them | A decision's basis names its foundation, document and version. A claim is kept next to the record it was checked against |
| Agents propose, people approve | Agents may propose register entries but never approve them (G-01). Grants are approved by two people |
| Build the domain model first, join the broad one later through a proof of concept | v1's small core now; the broad organizational ontology later (Ledger G-58) |

## 3. What it sharpens (proposals for the spec)

1. **Name core types by one meaning each.** Section 3 listed `party` and `record`.
   - `party` repeats Netflix's `Service` mistake. It could mean customer, supplier or partner, held in
     different catalogs. Both packs need **`customer`**, so `customer` should be the core type.
     Supplier and partner join if a pack needs them.
   - `record` isn't an entity. It is the form of a reference (source, key, version), so it belongs in
     the contract's reference shapes, not in the vocabulary.
   - The core becomes org, person, agent, function, customer and document.
2. **Add a catalog gate on subjects.** A decision opens only on a subject, and a customer, that resolves
   in its authoritative catalog. A subject that doesn't resolve fails closed to the pack's `route_to`
   outcome, with a "no record" finding. Nothing goes ahead on the submitted figures.
   - **This changes the lab's behaviour.** Today, with no row, a discount or credit decision stands on
     the submitted figures. It opens a blocking `missing_record` condition that the requester can
     clear by confirming those figures (`lab/owm_service/decisions.py` step 3,
     `conditions.py:missing_record_condition`). That lets a claim become the basis on the say-so of the
     person who wants the outcome, which section 4's rule forbids. There is also no row for the
     executor to apply the action to.
   - **The cost:** a request must exist in its system of record before it can be decided. The fix is
     to create the record through that system's own process, then decide.
3. **Keep typed judgments as a pack rule.** Every Jev question a pack declares carries its answer type.
   An answer outside that type counts as unavailable, which fails closed (today's 503 path, R19). It is
   never coerced. This is already the lab's practice; the spec should state it as a contract rule.

## 4. Where the prototype deliberately differs

| Netflix | The prototype | Why |
|---|---|---|
| Best-effort enrichment: a slow dependency degrades the graph | **Fail closed:** a slow or unreadable foundation refuses or routes, and never degrades a decision silently (section 5) | Diagnosis tolerates gaps. An authority decision that is quietly missing a document is unsafe |
| The most valuable edges came from discussion | Discussion is a **claim**, or a mention, and never the basis (the lab's `mentions`; S07, hearsay is not a basis) | They are explaining what happened; we are deciding what may happen. The decision record holds the reasoning instead |
| People approve every proposal | Agents may approve low-risk work under registered **grants**, which two people approve | Your call (2026-10-22): people approve the rule, and agents act within its limits |
| Ontology as code: changes arrive as pull requests | Packs and profiles arrive through the **register**: approved, versioned data | A platform onboards a customer by configuration, without a code release. The register is our review gate |
| A knowledge graph with SPARQL is the store | Typed contracts (JSON Schema, the OpenFGA DSL), an event log, and foundations behind ports | v1 has two packs. A triple store is G-58's question, not v1's |

## 5. For G-58, the broad ontology, when it comes

- Upper is the closest public analogue of option C: a broad domain model projected into concrete
  schemas. Netflix is joining its domain ontology to Upper the way we sequenced ours: domain first, then
  a proof of concept on one entity, then converge.
- If C is taken up: build it on open standards (RDF, OWL, SHACL), and reuse governed standards before
  writing our own (the 2026-10-07 reading list, piece 2). Validate with SHACL in a closed world, as
  that reading list's piece 3 says. The OWM's checks are closed-world.
- Align with whatever ontology BlueLeaf's Knowledge Foundation already uses, so the foundations' nouns
  and the OWM's authority meet in one model.

## 6. An idea, not for v1: a decision flywheel that proposes rules

Netflix's flywheel turns repeated patterns into detection rules. The safe OWM version would turn
repeated decisions into **proposed** register changes. For example: "discounts under some figure for
this customer tier were approved every time this quarter", proposed as a grant for two people to
approve. It is never learned silently, because precedent isn't authority (the lab's `mentions`). It
fits the commercial story (trust with confidence, and agents earning scope). It needs its own spec.

## 7. Limits

This is a company blog post. Its numbers are self-reported and nothing in it can be checked from here.
Its domain is diagnosis, not authority: it ranks hypotheses for a person to check, so its tolerance
for wrong answers is higher than an approval path can allow.
