# OWM overhaul: what must be resolved, as amendment candidates (2026-09-29)

**Inputs:** the PRD batch (`raw-material/owm-prd-batch-2026-09-29/`, raw material, not canon), BlueLeaf
canon (`owm-edd/00-CANON.md` and the documents it names, as digested in
`blueleaf-owm-digest-2026-09-29.md`), and this lab's evidence (`runs/`).

**The rule this map follows:** in sovera-owm, agents adhere to the constitution and the build process,
and **anything can change through amendments**. So nothing below is a decision. Each row is either a
**ruling** someone must make on a canon axis, or a question the **lab can measure** before the ruling.
Where a draft contradicts canon, the draft is not wrong; the amendment that would make it canon is
what's missing.

## 1. Where all three PRDs already agree (the stable core)

- **OWM is a persistent, governed model of how the organization works**, grounded in evidence, and
  consumed by agents.
- **Evidence ≠ provenance ≠ interpretation ≠ decision.** This matches the evidence-vs-provenance
  distinction canon adopted on 09-17.
- **Extraction proposes; governance promotes.** Nothing machine-generated becomes organizational truth
  silently. This is canon's proposal port.
- **Two clocks.** What was true, and when the organization learned it; historical decisions stay
  historically valid.
- **Identity keeps every source id.** Canonicalization must never destroy source identifiers.
- **First-class organizational primitives** beyond entities and facts: policy, authority, exceptions,
  procedures, decisions.
- **No proprietary agent runtime; the domain layer stays vendor-neutral.**

All seven are either canon already or consistent with it. **Most of the overhaul is adding
primitives, not reversing direction.**

## 2. What must be resolved

"Axis" names who decides under `00-CANON.md`: **P** = Product (CPM, with MM's veto), **D** = Direction,
**Dep** = Deployment, **W** = Write contract, **V** = Vocabulary (all MM). "Lab" says whether this lab can
measure something first.

| # | Question | PRD-1 (09-23) | PRD-2 (09-27) | PRD-3 (09-29) | Canon today | Lab evidence | Axis / Lab |
|---|---|---|---|---|---|---|---|
| 1 | **What is the product?** | "Sovera OWM" | "Sovera platform powered by OWM" | "Sovera OWM", with an MVP and product surface | **BlueLeaf is the product**; OWM alone is never a product; OWM is internal | — | **P** |
| 2 | **Agent runtime** | not named | **Agno** | Agno "or other"; runtime-agnostic | **LangGraph is the orchestration layer** (09-15) | — | **D** |
| 3 | **Where judgment lives** | Decision engine is an OWM capability (rules, LLM, TypeSafe, human, composite) | Decision intelligence is a sibling of OWM | OWM holds procedures, vocabulary and decision memory; the agent runtime executes | **No LLM in the OWM serving path** | Judgment at the edge worked: an agent applying the procedure got 45/45 visible and 15/18 held-out. Authority and eligibility are deterministic lookups | **D** · Lab: yes |
| 4 | **Context: assembled or called?** | Context bundle (§15) | Context assembled and injected into the runtime (§10, §12) | Tool-style API: `get_policy()`, `get_procedure()`, `record_decision()` (§11) | **Agents call; they don't receive assemblies** (the envelope is a road not taken, twice) | B1's calls worked. The lab's procedure-in-prompt **is** the envelope pattern (its own weakness) | **D** · Lab: yes |
| 5 | **Procedures** | Process as a primitive | Process as a primitive | "Executable descriptions of organizational reasoning", fetched via `GET /owm/procedures/…`, executed by the runtime | Absent from code and canon | The procedure and its outcome vocabulary were necessary. S13 found a gap in prose. **The lab's oracle is an executable procedure over typed state**, tested by held-out scenarios | **D/W** · Lab: yes |
| 6 | **Constraints and conflict detection** | Semantic validation | — | First-class; conflicts preserved, never silently fixed (`reports_to` acyclic, rank) | Absent in OWM. Utopia checks axioms only on typed relations, and the lab's KBs typed nothing | Small run: every reporting line inverted. Scale run: none extracted | **D** · Lab: yes (deterministic) |
| 7 | **Decision vocabulary** | Outcomes `APPROVE / APPROVE_WITH_AUTHORIZATION / REJECT / ESCALATE`, plus gate outcomes `ACT / ROUTE / ESCALATE / REQUEST_EVIDENCE / REJECT / HUMAN_REVIEW`, plus review actions | Gate outcomes | The lab's five decision states | None | **Three layers are conflated**: organizational decision state, governance routing, review-queue action. S13 shows the `REVIEW_REQUIRED` / `REQUEST_EVIDENCE` boundary is underspecified (customer applicability) | **V** · Lab: yes |
| 8 | **Decision records: who writes them, and are they governed?** | Every consequential decision creates a record | Decision records; agents must not silently rewrite truth | Decision memory, persisted and queryable | The proposal port has no `decision` kind (a new kind is additive v1.x). **The code lets an agent approve its own proposal** (*inferred*), against "the approver is never the author" | Decision JSON was produced per run; persistence untested | **W** · Lab: yes |
| 9 | **Tenancy** | Organizations, workspaces, multi-tenant | Multi-tenancy | Tenant isolation | **Single-tenant, internal** | — | **Dep** |
| 10 | **Human surfaces** | A 20-item console; business-user personas | Experiences on the runtime | Explore, understand, decide, explain, remember | **Agents-first**; humans only in DevOps and the control plane; UI is a later IQ application; REST is an adapter | — | **P/D** |
| 11 | **Where the knowledge foundation ends** | Evidence layer below OWM | — | The foundation owns retrieval, extraction, **identity and provenance**; OWM consumes. Utopia could be a substrate | OWM owns **governance, provenance and identity (rule + decision)**; DocIQ is the OG-RAG loop; Utopia is **reference design, not a dependency** | Utopia's merges dropped source ids (issue 3). The foundation's extraction dropped decision-critical facts at scale | **P/D** · Lab: partly |
| 12 | **Evidence storage** | Addressable evidence (§33) | Evidence distinct from derived state | Traceable evidence | Canon agrees, but **OWM stores no spans on facts** | Graph-only readers can't reach sentence-only values; text retrieval can | **W** (additive) · Lab: yes |
| 13 | **Semantic resolution / mapping** | A defining capability (§14) | FR-5 | Domain model | A "gap of record" (09-17) | Not tested: the Northstar corpus has little conflict between concepts | **D** · Lab: needs new scenarios |
| 14 | **Names** | — | — | — | Glossary v4 plus the 09-21 `IX`/`ix` taxonomy | Doc 04 uses AssistIQ, AgentIQ and ContextIQ: retired or new names | **V** |
| 15 | **Document chain** | v1.0 | "v2.0, supersedes" | **also "v2.0, supersedes"** | Amendments are numbered and applied in order | — | process |
| 16 | **TypeSafe** | A decision-engine implementation | Named | — | Not in canon | — | **P** (what is it?) |
| 17 | **Governed action and external writes** | Action registry and gates (Slice F) | Capability governance: risk level, approval | Out of the initial scope | OWM is not transactional. Where action authorization lives (GatewayIX? IX?) is unstated | — | **D** |
| 18 | **Evaluation** | Success metrics | Agent evaluation dimensions | **Six dimensions**: identity, state, policy, authority, procedure, decision persistence | Eval is load-bearing (agents-first); the Northwind gold set covers aggregates | **The lab's scorer already covers 5 of 6**: outcome, eligibility, authorized, required role, approver | Lab: yes |
| 19 | **The primary experiment** | — | — | §21: A decides and persists; B reuses; the policy changes; "historically valid vs same decision today" | Not planned | Needs a fair baseline (the decision written back to the foundation) and a 2027 policy (new truth and evidence: a small ingestion) | Lab: yes |

## 3. What the lab can settle before the rulings

In order of cost, all Claude-reader-only unless marked:

1. **Procedure as a governed object (rows 4, 5).** Serve the frozen procedure through a tool the reader
   calls, instead of the system prompt, and re-run S01–S14. This tests whether the agents-first form
   loses anything.
2. **Procedure v2 with an applicability rule (rows 5, 7).** Fix the S13 class, then test on *fresh*
   held-out scenarios (pre-registered; the review's "held-out, not blind" point applies).
3. **Constraint check (row 6).** A deterministic pass for `reports_to` acyclicity and role rank over the
   foundation's facts. Measures whether inverted or missing edges are flagged rather than fixed. No
   model calls.
4. **Decision memory with a fair baseline (rows 8, 19).** PRD-3 §21's three phases, with arm (b) = the
   decision written back to Utopia as a document, and a 2027 policy added to `truth/`. The ingestion is
   small, on the small KBs.
5. **Vocabulary split (row 7).** Re-score the existing answers against a three-layer vocabulary: decision
   state, governance routing, review action. No new runs.

## 4. Amendment candidates the process will need

Rows 1, 2, 9, 10, 14, 15 and 16 are rulings, not experiments. Rows 3–8, 11, 12 and 17 each become an
amendment once decided. Several touch the **constitution itself**, which is also amendable:

- **Principle IV** ("writes go through propose plus human review") must say whether a *decision record*
  is a proposal (HITL-gated), an attributed append-only record, or both.
- **Principle VI** ("no hard dependency on DocIQ") predates DocIQ becoming a privileged first-party
  component (09-15).
- **Principle VII's** human-judgment gates will need a rule for **agent deciders**: `DeciderKind.AGENT`
  exists, but author ≠ approver is not enforced.

*This map is the lab's reading. None of it has been proposed to, or ruled by, MM or CPM.*
