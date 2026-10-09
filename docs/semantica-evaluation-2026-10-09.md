# Semantica as infrastructure or an integration layer for BlueLeaf? (2026-10-09)

**The question.** The user, 2026-10-09: can Semantica (github.com/semantica-agi/semantica) serve
BlueLeaf as reusable infrastructure or an integration layer? This review read the repo at HEAD on
2026-10-09: README, ARCHITECTURE.md, `pyproject.toml`, and the context, provenance, kg,
deduplication, ontology, parse, mcp_server and integrations modules. It also checked GitHub
metadata. It didn't install or run the package.

## The short version

- **Yes, at the edges. No, at the core.** Semantica is a broad, MIT-licensed knowledge
  foundation: connectors, Docling parsing, extraction, a knowledge graph, provenance, bi-temporal
  facts, ontology tooling, and graph and vector stores. Several parts are worth reusing **behind
  BlueLeaf's own interfaces**, on the evidence and knowledge-foundation side.
- **Its "decision intelligence" isn't the OWM's job, and adopting it would undo the lab's main
  result.**
  - A Semantica `Decision` is a **log entry**: a free-text outcome, reasoning and a confidence,
    recorded after an agent or person decides.
  - Its `PolicyEngine` checks `min_`/`max_`/`required_` thresholds on that entry's metadata.
  - It has no authority bands or approver resolution, no register of approved instruments, no
    registration controls, no procedures as admitted data, and no conditions.
  - Its Agno toolkit and MCP server let **the agent record its own decision**, and the MCP server
    also lets it add, update and delete graph nodes, with no authorization.
  - That's the "agent decides" pattern the lab measured failing: 93/102 decisions right, 25/47
    attacks worked, and Haiku 10–12/84 unsafe.
- **It's also a competitor in narrative.**
  - It markets itself as "governed", "decision intelligence" and "accountable AI", an "alternative
    to expensive enterprise platforms".
  - Its growth playbook targets enterprise customers.
  - It already wraps **TypeSafe Jev** and ships an **Agno** toolkit: our stack.

  Buyers will compare. BlueLeaf's answer is the one the lab proved: **Semantica records
  decisions; BlueLeaf governs them.**

## What Semantica is (facts at 2026-10-09)

| | |
|---|---|
| **License** | MIT (commercial embedding fine; keep attribution) |
| **Age, release** | Created 2025-06-25 (about 15 months); latest **v0.7.0** (2026-09-22); roughly monthly releases since v0.3 (March 2026); pre-1.0, with "breaking" mentioned 17 times in the CHANGELOG |
| **Activity** | Commits today (2026-10-09); about 13,900 stars, about 1,600 forks |
| **Maintainers** | One contributor has about 2,066 commits; the next has 286. **High bus factor** |
| **Size** | About 237,000 lines of Python in 944 files (excluding tests); 439 test files |
| **Core install** | 22 dependencies, including numpy, pandas, scipy, scikit-learn, rdflib, networkx, grpcio, protobuf, pillow and pyarrow. More than 70 optional extras (LLMs, databases, graph and vector stores, connectors) |
| **Python** | 3.10–3.13 |
| **Company** | getsemantica.ai, with docs, Discord and a growth playbook aimed at "enterprise customers" |

## Fit, layer by layer

| BlueLeaf need | What Semantica has | Fit | Note |
|---|---|---|---|
| **Connectors** into enterprise systems | Files, databases, Snowflake, Databricks, Salesforce, Dynamics 365, ServiceNow, SAP, Tableau, Looker, Kafka, email, Git, MCP resources | **Strong** | The broadest reusable part. Wrap behind our ingest interface and pin the version |
| **Document understanding** (first-party KF: Docling + langextract) | A `DocumentParser` with a **Docling** backend. Extraction is spaCy or LLM NER/relations with character offsets. **No langextract** | **Partial** | It agrees with our Docling choice. The extraction step is a candidate to bake off against langextract |
| **Provenance** with source references | `ProvenanceEntry`: PROV-O entity, activity and agent; source document, location, **quote**, **start/end character index**; **SHA-256 checksums chained entry to entry** (deletion is detectable); PROV-O export | **Strong** | Close to our byte-range requirement (characters, not bytes; mappable). A candidate for the evidence store's provenance |
| **Time:** "in force on D" and "as known at T" (G-38) | `BiTemporalFact`: valid time plus transaction time (`recorded_at`, `superseded_at`), queries on either axis | **Strong, as design** | It answers G-38's open question directly. Reuse or copy the model |
| **Executable ontology constraints** (G-41) and **standards** (G-42) | OWL, SHACL, SKOS; `run_shacl_validation`; competency questions; RDF/JSON-LD export | **Good** | A head start on G-41 and G-42 |
| **Identity resolution** | Fuzzy similarity, default threshold 0.7, then merge; a **type-mismatch guard** (different types are never duplicates) | **Weak for authority** | It has the same guard as ours, but no calibrated judge, operating point or routing tier (G-18: 0 wrong merges at 0.79% routed). Use it at most for candidate generation |
| **The decision** (governed, reproducible, stamped, with conditions) | A `Decision` log (outcome and reasoning as text, a confidence, the maker); precedent search; causal chains; a `PolicyEngine` of metadata thresholds, with versioned policies but no approval enforcement | **No** | This is the OWM's kernel. Keep it first-party |
| **Register of approved governing documents and its controls** | None. Policies are added by whoever calls `add_policy` | **No** | Our registrar (RR-1–RR-14) and its approved-text store are the moat |
| **Procedures as data, with an admission gate** | None | **No** | First-party (G-07, G-12, G-13) |
| **The agent interface** (agents propose, never approve) | An MCP server over stdio with about 26 tools, including `add_entity`, `update_node`, `delete_node`, `store_document` and `record_decision`, and **no authorization**. An Agno toolkit where the agent records and policy-checks its own decisions. The REST API key is optional and warns when absent | **Conflicts** | Never expose its write tools to agents. If used, put a read-only facade in front, with the OWM's gates |
| **The decision model** (Jev) | A TypeSafe Jev provider (decision-only, no free text) | Aligned | The same vendor; no lock-in either way |
| **Stores** | Vector: FAISS, Qdrant, Weaviate, Milvus, Pinecone, PgVector. Graph: Neo4j, FalkorDB, Apache AGE, Neptune. A triple store; RDF and Cypher export | **Good** | Useful for integration breadth, not for decisions |

## Risks of depending on it

1. **API churn.** It's pre-1.0, ships monthly, and has 17 "breaking" notes. Depend on a few
   modules behind adapters, pin the version, and keep a contract test per adapter.
2. **Bus factor.** One maintainer dominates. MIT allows a fork, but forking 237,000 lines is
   expensive: take only narrow modules.
3. **Dependency weight.** The core pulls in numpy, pandas, scipy, scikit-learn, grpcio, protobuf
   and more. **Keep it out of the OWM kernel's dependency closure.** That's the same rule as the
   lab's for Polyfactory, Faker and Utopia: the kernel stays small and auditable. Use Semantica in
   the knowledge-foundation service, behind an interface.
4. **The security posture of its services.** The MCP server has no authorization and the REST API
   key is optional. That's fine as a library; not as an exposed service without hardening.
   Hygiene looks reasonable: safe YAML loaders, no `eval`, documented pickle-cache risk, an
   OpenSSF scorecard.
5. **Competitive overlap.** Its open-source "governed decision intelligence" sets buyer
   expectations at zero price. Reusing its foundation pieces doesn't change that. Our
   differentiation has to stay where the lab's evidence is:
   - decisions computed, not just recorded;
   - approved instruments in a controlled register;
   - procedures admitted and approved;
   - conditions in the record;
   - 0/47 attacks against 25/47.

## Recommendation

1. **Treat Semantica as a candidate library for the knowledge-foundation side of BlueLeaf, not as
   its kernel or its agent interface.** Reuse candidates:
   - connectors;
   - Docling parsing;
   - provenance (PROV-O, character ranges, hash chain);
   - the bi-temporal fact model;
   - SHACL validation.
2. **Keep first-party:**
   - the register and registrar;
   - procedures, admission and governed decisions;
   - identity's judge, guard and routing;
   - the decision record with conditions;
   - the agent-facing MCP surface, which stays read-mostly and gated.
3. **De-risk with a short spike before committing** (about 1–2 days, about $10–20 of LLM
   extraction):
   - Ingest the Northstar corpus with Semantica (Docling, extraction, provenance). Score it against
     the answer key's asserted facts and evidence map, as proposed for Docling + langextract.
   - That gives one bake-off with two candidates for the first-party foundation, on fact recall
     and precision, source-span accuracy, and no "derived" fact asserted.
   - It also tests the bi-temporal model on the lab's policy windows.
4. **Watch it as a competitor.** Its TypeSafe and Agno integrations mean a buyer can assemble "an
   open-source BlueLeaf-like stack". A one-page comparison for the pitch: Semantica records and
   checks decisions an agent made; BlueLeaf decides, from approved instruments, with controls, and
   proves it under attack.

## Tests run (2026-10-09, at the user's go-ahead)

Three tests, each pre-registered, about $4 in all. They sharpen the recommendation; they don't
change it.

| Test | Result | What it means |
|---|---|---|
| **Extraction bake-off** (`runs/2026-10-09-kf-bakeoff/`): Semantica against langextract against a one-call baseline, same model (Haiku), 84 gold facts, plus a Docling PDF round | All found 98–100%. **Semantica has no source spans and costs about 6–7×** ($2.45 against $0.35 and $0.42). Docling kept 100% of text and tables but 0% of list nesting. Reporting lines are the shared weak spot | Keep **Docling + langextract**; Semantica's extractor isn't needed. Take reporting lines from HR systems, not documents |
| **Deduplication** (`runs/2026-10-09-semantica-dedup/`): its `DuplicateDetector` on I2's 41,617 labelled pairs | **18,402 false merges** at defaults (17,564 on the replication). Same-type lookalike ids, so its type check can't help. No safe threshold: at 0.9, 0 false merges but 4 of 108 true duplicates found | **Never** an identity authority. At most a candidate generator behind the OWM's guard, judge and routing (0 wrong merges, 0.79% routed) |
| **Bi-temporal queries** (`runs/2026-10-09-semantica-bitemporal/`): the register's governing documents as facts with validity and registration dates | **8/8** agree with an independent calculation, including "as known on T, in force on V", once entities carry transaction time. Untimed entities default to wall-clock *now*, which silently empties past queries (2/8) | A good reference design for G-38. If reused, make transaction time mandatory |

**Revised recommendation:**
- **Reuse candidates:** connectors, PROV-O provenance, and the bi-temporal model (with
  transaction time enforced).
- **Not its extractor:** no spans, more cost, no gain.
- **Never its deduplication or decision layer.**
