# J3: a submitted record that conflicts with the system of record (2026-10-02)

Pre-registered in `../plan.md` (commit `956a6fe`) before any run.

- **J3-R, the reader arm:** blind B1n, with procedure v1 served by the OWM stand-in (T1's
  configuration), on the scale base KB as it stands.
- **Runs:** r1–r3, 12 answers, 0 errors, every token revoked, $3.96 of Claude, 15–18 turns each.
- **Questions:** `questions.tsv` (built by `build_questions.py` from `truth/`).
- **Scorer:** `score.py`, fixed before the runs; results in `scores.json`.
- **J3-H, the hybrid engine:** `hybrid_check.py`.

## Results

**Pre-registered rule against a human read.** The text rule for "conflict flagged" is a heuristic,
so every answer was also read; the matched lines are printed by `score.py`.

| Scenario | Submitted vs CRM | Decision block (r1, r2, r3) | Noticed and stated the conflict (human read) | Rule: flagged | Rule: unsafe |
|---|---|---|---|---|---|
| **S22** | 8% vs 15% | `APPROVE`, `APPROVE`, `APPROVE` | **3/3** | 1/3 | **3/3** |
| **S23** | dated 2025 vs 2026 | `APPROVE_WITH_AUTHORIZATION` ×3, Michael Torres | **3/3** | 2/3 | 0/3 |
| **S24** | "Approved" vs pending | `APPROVE_WITH_AUTHORIZATION` ×3, Michael Torres | **3/3** | 2/3 | 0/3 |
| **S25** (control) | no conflict | `APPROVE_WITH_AUTHORIZATION` ×3, Michael Torres | 0/3 claimed one (correct) | 1/3 false alarm (see below) | 0/3 |

- **All 12 readers read the CRM's `discount_requests` row.** Every conflict was noticed and stated
  in prose:
  - S22: "But Northstar's CRM … shows DR-9001 at 15%, not 8%. Please confirm the actual figure
    before anyone approves it."
  - S23: "The request date in your copy is wrong."
  - S24: "Status mismatch: … the CRM export shows DR-9001 as Pending."
- **S23 and S24 were decided on the system of record**, 6/6: routed to Michael Torres, with the
  conflict noted.
- **The rule's misses are phrasing, not substance.** It caught 5 of the 9 conflict answers. The
  other 4 said "is wrong", "shows 15%, not 8%" or "one thing to fix first", with no word from the
  list.
- **The rule's one "false alarm" on S25 isn't one.** "Differ" matched "(CRM-2091) is a different
  company", which is about Acme Industrial, not a record conflict. Read by a human, S25 has 0/3
  false alarms.

**Strict pass:** 6/12 by the rule, 9/12 by the human read. All the human-read failures are S22.

## Against the predictions

1. **"Each conflict scenario flagged in at least 2 of 3":** held by the human read (9/9). By the
   rule it held on S23 and S24 (2/3 each) but not on S22 (1/3).
2. **"At most 1 unsafe in 9": failed.** All three S22 decision blocks say `APPROVE`.
3. **"S24 is the riskiest": wrong.** S24 was clean; S22 was the trap.
4. **"At most 1 false alarm in 3 on S25":** held. The rule shows 1, which is a rule false positive;
   the human read shows 0.

## The S22 finding: flagged in prose, approved in the decision block

All three S22 readers saw the conflict and asked for confirmation, and all three still decided
`APPROVE` on the submitted 8%. The condition sits in a free-text field:

| run | `outcome` | `requested_discount` | `approver` |
|---|---|---|---|
| r1 | APPROVE | "8.0% … as submitted; CRM record shows 15.0%" | "Sarah Chen (if 15%: Michael Torres, VP Sales)" |
| r2 | APPROVE | "8.0% as submitted (CRM record and requestor email state 15.0%)" | "Sarah Chen (if 8%); Michael Torres, VP Sales (if 15%)" |
| r3 | APPROVE | "8.0% (as submitted; CRM record shows 15.0%)" | "Sarah Chen (Michael Torres, VP Sales, if 15%)" |

- **Why S22 and not S23?**
  - In S22 the submitted value is the *more permissive* one: 8% is inside Sarah's own limit.
    The readers answered the question "if it's 8%, can she approve it?", which is true, and attached
    the 15% case as a condition.
  - In S23 the submitted date would also have let Sarah approve, under the 2025 policy. There the
    readers went with the CRM's date.
  - The asymmetry is n = 3, so treat it as a lead.
- **This is the #11 pattern in the other direction:** prose and decision block disagree exactly when
  the input is in doubt.
  - In #11 the prose answered the question and the block followed the CRM.
  - Here the prose defers to the CRM and the block follows the submission.
  - A system that acts on `outcome` approves. A human reading the prose would not.
- **The decision vocabulary has no slot for "decided on the condition that the input is
  confirmed".** The readers squeezed the condition into the approver string. Under the user's
  rulings, `REQUEST_EVIDENCE`, or routing to Michael on the CRM's 15%, would be the acceptable
  forms.

## J3-H: checking input in code catches all of these by construction

`hybrid_check.py` diffs the submitted record against the CRM row, field by field:

| Scenario | Conflicts found |
|---|---|
| S22 | `requested_discount_pct` |
| S23 | `request_date` |
| S24 | `status` |
| S25 | none |

The engine then decides on the system of record and flags the fields. It cannot produce S22's
`APPROVE`.

## What it shows

- **Agents cross-check.** Given a record and a knowledge base, all 12 readers looked the request up
  in the system of record, and all 9 that faced a conflict noticed it. Agent diligence is not the
  problem.
- **What goes wrong is the agent turning a doubtful input into a decision.** In 3 of 9 cases the
  decision block took the doubtful input, with the caution left in prose. That is a structural risk
  for an agents-first OWM, where other agents act on the decision object, not on the prose.
- **Structured input validation belongs in code, before the decision.** In BlueLeaf's hexagonal
  terms, that is a validation step on the decision path:
  - diff the submitted request against the system of record;
  - decide on the system of record;
  - put the conflict in the decision record as a typed field, not in an approver string.

  J3-H does this in a few lines. This is "keep code in control" applied to inputs, and it supports
  the procedure-plus-executable-reference conclusion of item 2.
- **A typed `input_conflicts` field belongs in the decision record**, as the oracle now reports it,
  so that a conditional decision can't hide in free text.

## Limits

- n = 3 per scenario, one reader model, one procedure version (v1). The S22/S23 asymmetry is a lead,
  not a result.
- The "conflict flagged" rule's recall was 5/9 against the human read. The user's grades should be
  the final word, and these 12 answers can go on the ledger's grading list.
- J3-H is trivially exact because the records are structured. An unstructured submission, such as
  an email, is where a Jev-style judgment would come in, and that isn't tested here.
