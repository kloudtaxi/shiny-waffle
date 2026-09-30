# Item 5: the decision vocabulary, split (2026-09-30)

`rescore.py` re-scores every auto-scored decision answer the lab has (134 answers, 10 conditions,
small and scale, visible and held-out) on two layers. There are no new runs. The rules were written in
`../plan.md` first, but the answers were already known, so this is **not blind**. Output:
`rescored.json` (per answer) and `table.md`.

## The three layers

| Layer | Question it answers | Values | Produced by |
|---|---|---|---|
| **1. Decision state** | What does the organization conclude about this request? | `APPROVABLE` · `APPROVABLE_WITH_AUTHORIZATION` · `NOT_APPROVABLE` · `UNDETERMINED` | the decision (agent or engine) |
| **2. Governance routing** | What happens next, and to whom? | `ACT` (the requestor approves) · `ROUTE_TO_APPROVER(role, person)` · `ESCALATE_FOR_TERMS` · `COMMERCIAL_REVIEW` · `REQUEST_EVIDENCE` | governance, from layer 1 plus policy |
| **3. Review action** | What does the human do with the routed item? | approve · reject · request changes · defer · revert | a person (HITL) |

**The lab's five outcomes are layer 2 values**, one to one (`APPROVE`→ACT … `REQUEST_EVIDENCE`→REQUEST_EVIDENCE).
PRD-1's `APPROVE / REJECT / ESCALATE` sit mostly in layer 1. Its gate outcomes `ACT / ROUTE / ESCALATE /
REQUEST_EVIDENCE / REJECT / HUMAN_REVIEW` are layer 2, and its review-queue actions are layer 3. Mixing
them is how one word (`ESCALATE`) ends up in all three.

## Results

| Condition | n | pass (5-outcome rule) | layer 1 | layer 2 | unsafe | conservative | no record |
|---|---|---|---|---|---|---|---|
| B2kP (small) | 15 | 14 | 14 | 14 | 1 | 0 | 0 |
| B2kPR (small) | 15 | 15 | 15 | 15 | 0 | 0 | 0 |
| B2PR (scale) | 5 | 0 | 2 | 1 | 0 | 2 | 0 |
| B2kPR (scale) | 15 | 13 | 15 | 13 | 0 | 0 | 0 |
| B2kPRa (scale, S03) | 3 | 3 | 3 | 3 | 0 | 0 | 0 |
| B1kPR (scale) | 15 | 15 | 15 | 15 | 0 | 0 | 0 |
| B1PR (scale) | 15 | 15 | 15 | 15 | 0 | 0 | 0 |
| B1nPR (scale) | 15 | 15 | 15 | 15 | 0 | 0 | 0 |
| B1nPRh (held-out) | 18 | 15 | 18 | 15 | 0 | 0 | 0 |
| B2kPRh (held-out) | 18 | 15 | 18 | 15 | 0 | 0 | 0 |
| **all** | **134** | **120** | **130** | **121** | **1** | **2** | **0** |

"Unsafe" means one of:
- layer 1 says approvable where the key doesn't;
- a requestor self-approves beyond their authority;
- an approval names the wrong approver.

"Conservative" means the key says approvable and the answer doesn't.

## What it shows

1. **Once the procedure and the request record are present, every miss is a routing disagreement
   between `COMMERCIAL_REVIEW` and `REQUEST_EVIDENCE`.** Those are S03 at scale (×2) and S13 (×6).
   All eight have layer 1 right (`UNDETERMINED`: do not approve). The five-outcome score counts
   them as failures; the decision-state score counts them as correct.
2. **One unsafe answer in 134**: small-run S05 r1, the confident approval under the procedure
   alone, before the request record existed. With the procedure *and* the record, there are **0
   unsafe answers in 119**.
3. **The uncurated graph-only reader (B2PR) is the only source of conservative misses**: it returned
   `REQUEST_EVIDENCE` where the key approves (S01, S04). A third answer (S02) is "not approvable" in
   the key and "undetermined" in the answer: safe, but neither conservative nor right.
4. **The boundary that matters is inside layer 2,** so a vocabulary amendment should define routing
   separately from decision state, and state the **customer-applicability rule** that separates
   `COMMERCIAL_REVIEW` from `REQUEST_EVIDENCE`. Item 2 tests that rule.

## What this does not establish

- Layer 3 is unscored: no decision answer produces a review action.
- The mapping from five outcomes to layers is the lab's proposal, not a ruling. The counts depend
  on it, especially treating `REVIEW_REQUIRED` and `REQUEST_EVIDENCE` alike as `UNDETERMINED` in
  layer 1.
