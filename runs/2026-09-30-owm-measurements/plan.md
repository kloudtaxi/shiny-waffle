# Lab measurements for the OWM overhaul: plan and pre-registration (2026-09-30)

**Why:** `docs/owm-overhaul-reconciliation-2026-09-29.md` §3 lists five measurements the lab can
make before the constitution and PRD rulings (which the user holds). This folder runs them.
**Nothing here decides anything**; each result is evidence for an amendment candidate.

**System under test:** Utopia `dev` @ `aad5b06`, scale KBs (`../2026-09-28-utopia-aad5b06-scale-large/kbs.jsonl`),
plus the small KBs for item 3. **Reader:** blind Opus 5.5 over MCP (`lab/utopia/blind_reader.py`),
fixed system prompt, per-run read tokens revoked. **Scoring:** the fixed rule in
`../2026-09-28-utopia-aad5b06/procedure/score.py` (pass: outcome, eligibility and authorization
match, plus the approver for an approval).

**Cost estimate:** about 130 reader answers (~$40 of Claude). Utopia gpt-4o is used only in item
4 (two small documents ingested) and by curation re-pushes (cents).

## Order

1. **Item 5**, vocabulary split: re-scoring only, no runs. **Item 3**, constraint check:
   deterministic, no model calls.
2. Build `lab/owm_standin/`, a small stdio MCP server standing in for the OWM contract of PRD-3
   §11 (`get_procedure`, `find_decisions`, `get_decision`), and let `blind_reader.py` attach it.
3. **Items 1 + 2**, one pre-registered batch. Commit it (scenarios, procedure v2, questions)
   **before** any reader sees it.
4. **Item 4**, decision memory. Pre-registered in its own commit before its runs, because it needs
   a truth change: a 2027 policy.

## Items 1 + 2: pre-registration

**Configuration:** B1n (all Utopia tools except `changes`) on the **uncurated** scale graph, with
curation withdrawn by `../2026-09-28-utopia-aad5b06-scale-large/b1/toggle_curation.py` and restored
afterwards. This is the configuration that scored 45/45 on S01–S05 and 15/18 on held-out S09–S14,
with the procedure in the system prompt.

**What changes:** the procedure is no longer in the system prompt. The system prompt is the fixed
28-09 prompt, verbatim. The procedure is served by the stand-in's `get_procedure` tool, and the
reader must discover and call it. The question and the request record are unchanged.

| Arm | Procedure | Served as | Scenarios | n |
|---|---|---|---|---|
| **T1** | v1, `owm/procedures/discount-approval.md` (sha256 `6e72951c…`, unchanged) | tool | S01–S05, S09–S14, **S15–S20** | 3 |
| **T2** | **v2**, `owm/procedures/discount-approval-v2.md` | tool | same | 3 |

**Procedure v2** changes only three things:
- Step 4 names the customer.
- A principle scoping special terms to the customer (legal entity), product and dates they name.
- The `REVIEW_REQUIRED` / `REQUEST_EVIDENCE` boundary states the customer case. `REVIEW_REQUIRED`
  means an active contract with *this* customer exists but no exception covers the product or date.
  `REQUEST_EVIDENCE` means no active contract with this customer can be established, including when
  the cited terms are another customer's.

This is the canonical process (doc 03 §11, as the oracle implements it), written into the outcome
table where v1 left it implicit.

**Fresh held-out scenarios S15–S20:** written after v2, so they are **held-out, not blind**. They
are proven by the oracle and change no evidence:

| | Request | Tests | Expected |
|---|---|---|---|
| S15 | BlueRiver (no contract), 12% NS-500, contract pricing citing the **Acme** agreement, requested by Michael | the v2 rule with a customer whose name is **not** similar | `REQUEST_EVIDENCE`: eligibility unknown; Michael authorized |
| S16 | Acme Industrial Supply, 8% NS-Edge, **standard** pricing, by Sarah | v2 must **not** over-trigger for a no-contract customer on standard pricing | `APPROVE`: approver Sarah |
| S17 | Acme Manufacturing, 12% NS-Edge, contract pricing (the agreement covers NS-Edge, no exception does) | the `REVIEW_REQUIRED` boundary is kept | `REVIEW_REQUIRED`: not authorized; VP Sales, Michael |
| S18 | Acme Manufacturing, 8% NS-500, contract pricing, **2025-03-31** | S09's complement: within the old 10% exception | `APPROVE`: approver Sarah |
| S19 | Acme Manufacturing, 8% NS-Edge, standard, **missing-contract KB** | v2 must not over-trigger where the contract documents are absent | `APPROVE`: approver Sarah |
| S20 | Acme Manufacturing, 18% NS-500, contract pricing, requested by **Michael** | authority ≠ eligibility with a VP requestor | `REJECT_OR_ESCALATE`: exceeded; Michael authorized |

**Predictions, stated before any run:**
1. **T1 vs the prompt-injected results** on S01–S14: the tool form loses nothing on the scenarios the
   reader decides (S01–S05, S09–S12, S14 remain 3/3), *if* the reader calls `get_procedure`. The
   call rate is recorded. A run that never calls it counts as a fail if it produces no decision
   record.
2. **T2 fixes S13** (0/3 → 3/3) and **S15** (whatever T1 does). T2 does **not** regress S16, S17, S18
   or S19.
3. Any T2 regression on S01–S14 is reported as the cost of v2, not discarded.

## Item 3: rules, stated before running

A deterministic checker over the foundation's own `reports to` facts. It **flags, never fixes**, and
writes nothing to Utopia. The constraints come from PRD-3 §5.5 and §9:
- `reports_to` is acyclic.
- Each person has at most one active manager.
- A manager's role rank is at least the subordinate's.

Ranks are a declared constraint table: Enterprise AE 1, Finance Manager 1, VP Sales 2, Director
of Finance 2, CRO 3. Roles are read from the foundation's title facts through a declared title
table. Run it on:
- the small base KB **as ingested**, reconstructed at a record time before any correction or curation;
- the small base KB now (after correction and curation);
- the scale base KB uncurated and curated.

It is scored against the org chart's true lines. Expected: the small as-ingested graph is flagged
(every line inverted); the others are clean. The scale uncurated graph reports **missing**
managers, not conflicts.

## Item 5: rules, stated before re-scoring (not blind: the results are already known)

Every auto-scored decision answer so far is re-scored on two layers:
- **Layer 1, decision state:** `APPROVABLE` (APPROVE), `APPROVABLE_WITH_AUTHORIZATION`,
  `NOT_APPROVABLE` (REJECT_OR_ESCALATE), `UNDETERMINED` (REVIEW_REQUIRED, REQUEST_EVIDENCE).
- **Layer 2, governance routing:** ACT, ROUTE_TO_APPROVER(role, approver), ESCALATE_FOR_TERMS,
  COMMERCIAL_REVIEW, REQUEST_EVIDENCE.

**Layer 3** (review action: approve, reject, defer, and so on) is what a human does with a routed
item. No decision answer produces it, so it is defined but not scored.

Also counted:
- **unsafe:** layer 1 says approvable when the key doesn't, or an approval routes to the wrong
  approver;
- **conservative:** the key says approvable and the answer doesn't.
