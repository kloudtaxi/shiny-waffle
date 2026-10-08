# Reading-list notes: what the user's agent reading list means for the lab (2026-10-07)

**Source:** the five pieces the user shared on 2026-10-07, read against shiny-waffle's results. The
articles aren't copied here; these are notes and citations only.

| # | Piece | Author | In one line |
|---|---|---|---|
| 1 | *Why Agentic Systems Need Ontologies* | Frank Coyle | Hallucination is a property; sequential reliability multiplies; non-probabilistic ontology constraints must hold the line, at the step that produced the error |
| 2 | *The Ontologies You Shouldn't Build Yourself* | Konrad Kaliciński | Reuse governed standards (FIBO, SNOMED, GS1/EPCIS, SCOR, W3C PROV, LKIF); take a slice, keep the ids, extend only where you're novel |
| 3 | *AI Ontology: The Missing Semantic Foundation* (summary) | — | Ontology → knowledge graph → context fabric → small decision-scoped context graph → agent → validated action. OWL infers in an open world; SHACL validates in a closed one |
| 4 | *I tested Jev on entity resolution* | Kervin Hu | Jev F1 0.943 (Opus 0.967) at about 1/100 of the cost. Jev, with the uncertain band sent to Opus, reached F1 0.972 at 17% of Opus's cost. A schema-valid JSON field with the wrong *meaning* merged 330 people into 197 |
| 5 | *Jev: Putting AI Decisions Inside Software* | Han Heloir Yan | Use Jev for bounded judgments. Keep dates, arithmetic and long indirection in code. Confidence isn't a correctness probability. Treat vendor speedups as vendor results |

## Where the reading independently confirms our results

| The reading says | The lab found |
|---|---|
| A probabilistic core needs a symbolic layer that "can't be talked into anything" (1, 3, 5) | The split design: Jev answers narrow questions, code decides. **102/102**, against the agents' 93/102. Register-backed engines **0/47** under attack |
| **Disjointness** constraints catch role or type confusion (1: "payout sent to support desk") | **"An order is never a customer"**, one line of code, decided 1,628 pairs with none a true match. It covered over 90% of GPT-4o's 161 wrong merges |
| **The meaning of a valid field** can be wrong, and "a schema cannot check" it (4: Luna's `probability: 0.99` on `false`) | **G-16 / G-35:** 59 of 757 answers had a valid decision block saying "approve" while meaning "approve once X is confirmed". Fixed with a `conditions` field that has one meaning |
| Validate where the error enters, not at the end of the chain (1) | Step-level gates: provenance, tamper, lineage (L1–L3) and register (R1–R3) checks run before the rules. The admission gate checks procedures before they run |
| OWL's open world (missing ≠ false) against SHACL's closed world (is this data acceptable?) (3) | **G-31:** an agent read "no guarantee in the served register" as *unknown*, and believed a forged one (E3). The fix was a closed-world declaration: "this register governs guarantees; this company has **none**" |
| Don't trust LLM-written ontologies without expert review (3) | **G-07 / G-13:** an AI-written procedure runs only after the admission gate and a person's approval. The gate refused the first SLA procedure; the revision passed |
| Keep dates and arithmetic in code. Adversarial content can steer the model (5, citing TypeSafe's own limitations) | Clocks, bands and windows are kernel code. The register screens governing documents **before** Jev judges anything, so a forged policy never reaches a judgment |
| Pin the model version, record the wording, freeze the threshold before testing (5) | `jev-1.13.0` is pinned. Every request and response is recorded by hash. τ = 0.9 was chosen on one knowledge base and replicated on the other unchanged (I2) |
| Ground truth from the generator beats references produced by an LLM (4, 5: TypeSafe's evaluations average two LLMs) | Our truth and key come from the generator, not a model. The caveat is ours to own: we built the generator too (G-39) |

These belong in the technical demo's Q&A ("isn't this just your own benchmark?"). Independent
authors, in different domains, report the same mechanisms.

## Ideas we haven't tried

1. **Hybrid identity routing (from 4), for G-18.**
   - Today our identity operating point routes almost every true match to a person: 3 of 108 were
     merged automatically on the base knowledge base.
   - Hu's pattern sends Jev's uncertain band to a frontier model, and only what's *still*
     uncertain to a person.
   - **The test:** our 41,600 labelled pairs, with the guard on. Jev, then Opus on the 0.3–0.9
     band, then a person. Pre-register it.
   - **What it would settle:** whether human review load falls from about 4% of pairs toward
     under 1%, with 0 wrong merges.
   - **Cost:** cents of Jev plus roughly the band size in Opus calls.
2. **Compounding reliability (from 1).**
   - A decision is a chain: gather evidence → about N Jev judgments → rules → record. Errors
     multiply along it.
   - **The analysis:** per-judgment error (J2's calibration) and judgments per decision predict a
     decision error rate. Compare that with the observed rate (0/102 on the split design).
   - **What it shows:** how much the gates and routing buy, and why the agent-alone chain (93/102)
     degrades.
   - **Cost:** free; it's analysis.
3. **A decision-scoped context, for agents (from 3), with G-23.**
   - Our reader arms put the **whole corpus**, about 73,000 characters, into every prompt.
   - The article's "small context graph" principle says to serve the decision's slice instead: the
     procedure, the served register, and only the documents that slice names.
   - **The test:** in the cheap-agent pipeline, does a scoped context keep safety (83/84) while
     cutting cost and latency? It's also the natural shape for the MCP server's `owm` arm.
4. **Executable constraints from the ontology (from 2 and 3).**
   - `owm/ontology.yaml` is descriptive (layer tags as hypotheses). The kernel holds the semantics
     in code.
   - "Loading an ontology isn't reasoning with it" applies.
   - **A small step:** express the constraints we already enforce as SHACL-style shapes and check
     them from the ontology:
     - one manager, no cycles, rank;
     - order ⊓ customer = ∅;
     - one policy in force;
     - the coverage and "none" declarations.
5. **Align with standards where they exist; build only what's novel (from 2).** Candidates:

   | Standard | What it covers for us |
   |---|---|
   | **W3C PROV-O** | Evidence → judgment → decision; `registered_by` / `approved_by` |
   | **ODRL** (not in the article, but the obvious one for policies) | Permissions, prohibitions and **duties**, which map onto our obligations and conditions |
   | **FIBO**, a slice | Legal entity, guarantee, credit facility, for credit decisions |
   | **LKIF** | Obligations and permissions in policy text |

   Keep their identifiers so the OWM can map outward. What no standard covers is ours: the
   decision record with conditions, the procedure as data with admission, and the register of
   approved versions.

## Cautions the reading raises for us

- **Transitive merges** (4): "one wrong relationship can join two otherwise correct groups". If
  the OWM ever closes identity merges transitively, it needs cluster-level checks: no two
  disjoint types in one cluster.
- **Calibration is per task** (4, 5). Hu saw an S-shaped curve (too eager around 0.4, too cautious
  around 0.7). Our J2 calibration held for *our* question types; a new type needs its own check
  before its thresholds are trusted.
- **Confidence ≠ correctness** (5). Choice and Score confidence summarize the distribution; they
  don't promise accuracy. Our routing uses the Noul probability and a threshold validated on
  held-out data, which is the right shape. Keep it that way for new question types.
- **Vendor figures** (5): the launch's "193.6× faster, 444.6× cheaper" came from TypeSafe's own
  workflows. We cite only what we measured (a fraction of a cent per decision).

## Suggested board changes

| Gap | Change |
|---|---|
| **G-18** (identity operating point) | Add the hybrid-routing test as its next step |
| **G-23** (cheap-agent pipeline) | Add the decision-scoped context arm |
| **G-40** (new): compounding reliability | Analysis only; P3 |
| **G-41** (new): executable ontology constraints | P3 |
| **G-42** (new): standards alignment (PROV-O, ODRL, a FIBO slice) | Product, P3 |

All five were added to the Lab Ledger on 2026-10-07 at the user's go-ahead.
