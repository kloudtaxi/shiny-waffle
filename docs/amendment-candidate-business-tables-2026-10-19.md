# Amendment candidate: business tables in registered terms, behind a rules port

**2026-10-19. A candidate for the BlueLeaf canon (owm-edd), not an applied amendment.**
- **Source:** G-52, recorded as a decided direction with the build deferred.
- **Evidence:** the ZEN spike, `runs/2026-10-19-zen-rules-spike/` (dfe4b61), and the user's own
  read-through.
- **Analysis:** `docs/rules-engine-zen-evaluation-2026-10-19.md`.

| | |
|---|---|
| **Canon axes** | Component architecture (the register's term schema, a new port) and the substrate register (ZEN, as an adapter) |
| **Rules it** | MM |
| **Status** | Direction decided on the user's delegation (2026-10-19: "I'm not prescribing, if it's a distraction then drop it"). **The build is deferred** until the register moves into the product, or an approver-facing view is built, whichever comes first |

## The problem

A governing document's business tables live as bespoke structured terms plus prose rules that
nothing executes. Examples are approval bands, concurrence, credit caps, discount ceilings and SLA
credit schedules.
- **G-33:** separation of duties was registered as a bare `true`, which lost "passes to the
  requestor's manager".
- **G-11:** approvers can't read the YAML the OWM evaluates.

## The proposal

1. **The register stores business tables in a small schema the OWM owns:** inputs, outputs, and
   rows of interval, list or exact cells, under a first or collect hit policy, plus constants.
   Approvals and versions attach to that schema, never to an engine's file format.
2. **A `RulesPort` evaluates them,** returning the outcome plus the matched rows. The decision
   record cites the table, its version and the rows.
3. **ZEN (gorules/zen, MIT) is the first adapter.**
   - The schema compiles to ZEN's JSON format.
   - ZEN's open-source editor is the review and editing view. Edits come back into the schema, and
     anything outside it is refused at registration: no function nodes and no custom nodes.
   - The commercial BRMS isn't used. The register stays the only governance.
4. **A reference evaluator checks the adapter.** The OWM's own small evaluator runs a differential
   boundary grid on every registered table and on every ZEN upgrade.
5. **Replace triggers, decided now:**
   - an upgrade changes any grid result;
   - a needed feature ZEN lacks (a Unique hit policy for overlap detection, DMN export for an
     auditor);
   - the editor fails approvers;
   - a licence or vendor change.

   On any of these, the adapter is swapped (the reference evaluator, or a DMN engine), and no
   approved table needs re-approval.
6. **Procedures stay the OWM's,** and ZEN never runs them: evidence rules, provenance and validity
   guards, Jev judgments, people resolution, business clocks, routing and the record. Definitions
   and bindings ("calculated against list price", "tier from the CRM") belong to the semantic
   layer (G-51), not to tables.

## Evidence

- **Spike (dfe4b61), all five checks at $0:**
  - the admission gate on `credit_v3` was identical with the credit tables evaluated by ZEN
    through a port;
  - 1,445 boundary points across seven tables, with 0 differences;
  - registration checks refuse a function node and flag a gap and an overlap;
  - the separation-of-duties hand-off lives in the table;
  - row-level trace;
  - a median of 0.26 ms per call.
- **The user's read-through** (2026-10-19): opened and edited all seven tables in GoRules' editor.
  Other user-facing features weren't tried.
- **A finding the tables exposed:** the lab kernel's `limit_for` gives 1.0 for an unlimited dollar
  band (the discount convention). Separation of duties masks it today. The table states
  "unlimited" explicitly.

## What it doesn't settle

- When the build happens: deferred, as above.
- Whether SLA and pricing engine paths move onto tables. Today the SLA specs read schedule prose,
  and no engine reads the pricing terms.
- Any business-rule authoring by agents beyond the existing propose-and-approve path.
