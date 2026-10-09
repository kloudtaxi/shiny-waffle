# sovera-owm: its time model and provenance against Semantica, and rebuild or refactor? (2026-10-09)

**What was read.** `kloudtaxi/sovera-owm` `main` @ `1f403d2` (2026-09-22; a fresh clone; read-only)
and the local checkout's CodeGraph index (the same code; one docs PR apart). The gate was run on
the clone: `uv sync`, pytest, ruff, mypy. Semantica facts come from
`docs/semantica-evaluation-2026-10-09.md` and its three test runs. The lab facts come from this
repo. Nothing was written to sovera-owm, and its `CLAUDE.md` seat instructions were read as
information, not acted on. In sovera-owm, change happens through amendments, so every
recommendation below is an amendment candidate, not a decision.

## The short version

- **Time: sovera-owm is ahead of Semantica.**
  - OWM stamps system time itself; producers can't set or backdate it. Semantica takes
    `recorded_at` from the caller and defaults it to *now*.
  - One call answers the two-coordinate question, `query_state(entity, as_of_system,
    as_of_valid)`. Semantica needs two calls composed.
  - Valid-time precision is per endpoint and never defaulted (including "ended, date unknown").
  - Invalidation cites a change record.
  - **Its gaps:** relations read back as single-valued (#94, still open); retraction isn't wired
    to the surface; there are no effective-dated *governing objects* (policies, procedures,
    authority).
- **Provenance: sovera-owm is stronger at intake, weaker after promotion.**
  - At intake the frozen proposal port requires evidence: a source and spans with offsets.
    Lineage covers the extractor, run, adapter and model, and confidence its score and method.
    That's stricter than Semantica.
  - **On promotion, the spans are dropped.** A fact keeps only source, extractor and lineage; the
    spans stay in the proposal store. That store is reachable only through a one-way id (uuid5),
    and the audit log has no read port.
  - The audit log is append-only **by API**, not tamper-evident. Semantica hash-chains its entries
    and exports W3C PROV-O; sovera-owm does neither.
- **Rebuild or refactor: refactor, by extension.**
  - The parts that matter for BlueLeaf's foundation are sound, tested and aligned with what the lab
    proved. That's the bitemporal store, the proposal port (*producers assert, OWM judges*), the
    governance loop, the identity overlay, authorization-as-absence, and the MCP gateway behind
    ports. The gate is fully green: **3,958 tests pass**, and ruff and strict mypy are clean on
    369 files.
  - What's missing is **the decision layer the lab built**: the register, procedures as data with
    admission, governed decisions with conditions, identity judging and routing, and the
    decision-scoped slice. It's *additive*: new kinds through the port (v1.x), new domain types,
    new services behind ports.
  - **Rewrite inside the refactor:**
    - remove `owm.synthesize` (an LLM in the serving path, against canon);
    - retire the context-bundle envelope;
    - fix #94;
    - add author ≠ approver, and "agents never approve governing kinds", to promotion;
    - hash-chain the episode log;
    - keep evidence spans on facts.
  - **A rebuild** would throw away about 26,600 lines, 3,958 tests and 50 ADRs of mostly correct
    infrastructure, to rewrite the parts that already work.

## 1. Time model

| | **sovera-owm** (owm-core, `Observation`) | **Semantica** 0.7.0 (`BiTemporalFact`) | **The lab** (kernel and register) |
|---|---|---|---|
| Valid time | `valid_from` / `valid_to` with a **per-endpoint `TemporalPrecision`**, never defaulted (`None` = not asserted; "ended, date unknown" supported) | `valid_from` / `valid_until` (datetime or an OPEN bound) | Document windows (`effective_from` / `effective_to`) plus `revoked_on` |
| System (transaction) time | `created_at`, **stamped by OWM at intake**; producers send only valid time | `recorded_at` / `superseded_at`, **supplied by the caller**; a missing value becomes *now* (wall clock) | `registered_on` / `approved_on`, stamped by the registrar's clock; not queried |
| A two-coordinate query | **One call:** `query_state(entity, as_of_system, as_of_valid)`, in the fake and the Neo4j adapter alike (contract-tested) | One time per call. "As known on T, in force on V" needs a two-step composition (8/8 correct once entities carry `recorded_at`) | Valid time only (`entry_in_force`, `Register.as_of`); "as known at" is open (G-38) |
| Change and retraction | `invalidate_observation(…, invalidated_at, change_record_ref)` on the port; **not wired** to any service or MCP tool | `superseded_at` | `revoked_on` on register entries (honoured on every decision path since 2026-10-08) |
| Multi-valued facts | **One winner per (entity, attribute)** in `query_state`, so every relation reads back as single-valued (**#94, open**) | Relationships are multi-valued | Not an issue (documents and terms) |
| Governing objects in time | None: no effective-dated policy, procedure, authority or role types | None | Registered instruments with windows, supersession, revocation; procedures in force by date |

**Read:** sovera-owm has the stronger temporal *substrate*. Its system time can't be backdated,
its precision is honest, and it answers one-call bitemporal queries. Semantica adds nothing it
lacks. What sovera-owm lacks is temporal *governance objects*. That's the lab's register (windows,
supersession, revocation, registration time) and procedures in force by date. It should be built
on sovera-owm's two clocks, not beside them.

## 2. Provenance

| | **sovera-owm** | **Semantica** 0.7.0 | **The lab** |
|---|---|---|---|
| At intake (write) | **Mandatory** `Evidence {source_ref, spans[{snippet, start, end, locator}]}`; `Lineage {extractor_id, run_id, adapter, model_ref}`; `Confidence {score, method}`, through the frozen proposal port | `ProvenanceEntry {source_document, source_location, source_quote, start/end index, PROV entity/activity/agent, confidence, credibility}`. Its LLM triples carried **no spans** in the bake-off | Not a write path (generated corpus); the register records `registered_by` and `approved_by` |
| On the stored fact | `Provenance {source, extractor, lineage}`. **Spans dropped.** The proposal (with spans) stays in the review store (Postgres jsonb), linked one way by `observation_id = uuid5(proposal_id, attribute)` | Per-entry provenance, optionally with a character range | Decision records stamp the procedure `{id, version, sha256}`, the register versions read, and incident flags |
| Decision provenance | `ReviewDecision {decided_by (from the authenticated principal), decided_by_kind (human or agent, from the credential class), decided_at}` plus a `PromotionReceipt` | A `Decision` log (outcome, reasoning, confidence, maker) with causal links | Typed decision record with conditions; procedure and register versions; Jev judgments recorded by hash |
| Integrity | Episode log append-only **by API** (insert-only; `ON CONFLICT DO NOTHING`; no update or delete method). **No hash chain.** Not readable through a port | **SHA-256 per entry, chained to the previous one** (deletion detectable) | Content-addressed store (sha256) for approved texts and procedures; a fingerprint check at decision time |
| Standards | Custom | **W3C PROV-O export** | Custom |
| Separation of duties | **Not enforced:** proposals carry no submitter, and promotion refuses nothing, so an agent token can approve, including its own proposal | None | Enforced (the registrar: employees only, author ≠ approver, agents never approve) |

**Read:** sovera-owm's intake is the best of the three. It's the only one that *requires* evidence
spans and lineage at the door. But it loses the spans at the moment they matter, when a fact is
cited, and its audit trail is trustworthy only as far as the database is.

**Three borrowings close the gap:**
1. **Keep spans on facts,** or expose them through `get_history`.
2. **Hash-chain the episode log,** Semantica's pattern.
3. **Map to PROV-O** for export (G-42).

## 3. sovera-owm today (facts)

| | |
|---|---|
| Code | 5 packages, about 26,600 lines: `owm-core` 8,270 (stdlib only), adapters 6,324, gateway 5,349, seed 4,012, bootstrap 2,646 |
| Gate (run 2026-10-09 on the clone) | **pytest: 3,958 passed** (148 deselected: live and integration). ruff clean. **mypy strict: clean, 369 files** |
| Process | Spec-kit constitution, **50 ADRs**, 30+ numbered specs, seats (CC-OWM proposes, MM rules), change by amendment |
| Agent surface | 14 MCP tools over stdio, including `submit_proposal`, `review_decision`, `get_state_at_time`, `get_history`, `assemble_context`, `ground` and `synthesize` |
| Open work at pause | #94 (relations read back single-valued); PR #95 (ontology slice, "wired to nothing"); `invalidate_observation` unwired; `definition_candidate` and `ontology_refinement` parked; OAuth scopes not enforced; no OTel tracing |

## 4. Fit with what shiny-waffle proved

| Lab-proven primitive or finding | In sovera-owm | Where it lands in a refactor |
|---|---|---|
| Bitemporal facts, identity that keeps every source id | **Present** (Observation; `RESOLVES_TO`; candidate keys) | Keep |
| "Producers assert, OWM judges"; agents propose, never approve | **Half:** the port exists; promotion doesn't refuse agents or self-approval | Extend promotion: author ≠ approver; agents never approve governing kinds (the lab's RR-2 to RR-4) |
| Register of governing documents (approved versions, fingerprints, approved-text store, terms bound to text, registrar controls, revocation) | **Absent** | New kind(s) through the port (`instrument_registration`, `instrument_revocation`; additive v1.x). A register domain type and service on the two clocks. Port the registrar's rules |
| Procedures as data, admission gate, governed decisions stamped with the version | **Absent** | New bounded context, `owm-decisions`: the procedure type, an admission service, and a decision runner behind a `JudgmentProvider` port (Jev adapter). Procedures registered through the same governance loop |
| Decision record with conditions (blocking holds) | **Absent** | A domain type in `owm-decisions`; readable through MCP (`get_decision`) |
| Identity: guard, calibrated judge, routing (0 wrong merges; 0.79% to people) | **Partial:** fuzzy candidates are never auto-applied; the resolver in every profile is the fake | Add the type-guard and judge ports; the routing policy as data (G-18's R2) |
| Authority and roles as types (bands, effective dates, approvers from HR) | **Absent** (no roles, reporting lines, policies) | Domain types sourced from systems of record (HR), not documents. The bake-off showed reporting lines don't survive PDFs |
| Agents get the decision's slice, not everything | `assemble_context` and `ground` (bounded, authz-as-absence, no LLM): **close in spirit** | Add `get_decision_slice` / `get_register(decision_type)`: served register plus named documents plus system-of-record rows (G-23: a third of the cost, the same safety) |
| No LLM in the serving path | **Conflict:** `owm.synthesize` is still registered (slated for removal) | **Remove** |
| Agents call; they don't receive assemblies | **Conflict:** `ContextBundle` envelope remnants | Retire |
| Multi-valued relations (an agreement covers three products) | **Bug** #94 | Fix before the register, since instruments have many-valued terms |

## 5. Rebuild or refactor: the evaluation

| Criterion | Refactor (extend sovera-owm) | Rebuild (a new core from the lab) |
|---|---|---|
| **Keeps what works** | Bitemporal store, frozen port, governance loop, identity overlay, authz, MCP gateway, adapters (Neo4j, Postgres, fakes), bootstrap, 3,958 tests | Re-implements all of it. The lab has none of it at product grade |
| **Fit with the lab's primitives** | Additive: new kinds (v1.x), new domain types, one new bounded context | A clean slate shaped around decisions |
| **Quality bar** | Already enforced (stdlib domain, contract tests, strict mypy, ADRs) | The lab's code is experimental, not under mypy; it would be rewritten anyway |
| **Time to a demonstrable governed decision** | Weeks: the decision context plus the register on the existing store and gateway | Months to reach parity with the substrate |
| **Risk** | Process weight (amendments, seats) slows change; the fixes above must land first | Discards working, aligned infrastructure; a second rebuild of identity, authz and audit |
| **Canon alignment** | Canon already says "most of the overhaul is adding primitives, not reversing direction" (reconciliation, 2026-09-29) | Contradicts the frozen write contract unless re-ruled |

**Recommendation: refactor by extension.** The work, in order:
1. **Fix and retire.** Fix #94. Remove `synthesize` and the envelope. Enforce author ≠ approver and
   "agents never approve" in promotion. Wire `invalidate_observation`. Hash-chain the episode log.
   Keep evidence spans on facts.
2. **The register on the two clocks.** Registration and revocation kinds through the port. The
   registrar's rules (RR-1 to RR-14, already written and self-tested in the lab) become promotion
   policy. "As known at" queries over registration time (G-38) come almost free from
   `as_of_system`.
3. **`owm-decisions`.** Procedures as data, the admission gate, the decision runner (Jev behind a
   port), and the decision record with conditions. Then the MCP tools: `get_procedure`,
   `get_register`, `get_decision_slice`, `decide`, `get_decision`.
4. **Identity routing** (the G-18 design) and **authority from HR** as types.

**Commercial fit.**
- The technical demo doesn't have to wait. The agreed path (2026-10-07) is a lab-built OWM API for
  web-next's endpoints #16–#20, a separate service.
- Make that service's contract the future `owm-decisions` port's contract. The demo then exercises
  the same interface the refactor fills in, and the lab service is retired when sovera-owm serves
  it.
- That keeps "marketing leads engineering" honest: what's shown is what the product will run.

## 6. For the user to decide

1. **Refactor by extension, or rebuild?** The recommendation is refactor.
2. **Who carries the port?**
   - (a) The sovera-owm fleet, through amendments and specs (governed, slower).
   - (b) A focused build from this lab's code, against sovera-owm's quality bar, landing as PRs
     (faster, needs MM's rulings first).
3. **Should the demo API's contract be the `owm-decisions` contract** from day one? Recommended.
