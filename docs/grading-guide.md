# Grading pass: how to do it (2026-09-30)

**Why it matters:** every grade in the ledger so far is provisional.
- Some are Claude's hand reads (the small run's B1/B2 answers and arm A).
- The rest come from the auto-scorer's fixed rule.

Your grades calibrate both. Where you agree, the numbers in the run notes stand. Where you
disagree, that difference is a finding. **You do not need to grade everything.** The ledger holds
about 390 answers; the 27 below are chosen to test the provisional grades where they are most
likely to be wrong. Budget 45–60 minutes. **Part A alone (7 answers, about 15 minutes) is already
useful.**

## How the ledger works

1. **Open** <https://claude.ai/artifact/FsSXn3ADwvDgBzG85b3Vyq>. It is private to you.
2. **Pick the experiment** from the dropdown in the header. There are three:
   - `2026-09-28-utopia-aad5b06` (small)
   - `2026-09-28-utopia-aad5b06-scale-large` (scale)
   - `2026-09-30-owm-measurements`
3. **Find the cell.** In the **Results matrix**, rows are scenarios and columns are conditions (the
   short code, such as `B2kPR`, sits above each column label). Each chip in a cell is one run: r1,
   r2, r3 from left to right.
   - A **dashed** chip is provisional.
   - A **solid** chip is your grade, which replaces the provisional one in the matrix.
4. **Open an answer.** Clicking a cell opens **run 1**. Use **Next →** to reach run 2 and run 3 of
   the same cell; the header says "run N of 3".
5. **Read, top to bottom:**
   - the question, verbatim;
   - the **answer key**, with its trap tags;
   - the reader's answer;
   - the **provisional read** (Claude's or the auto-scorer's);
   - the collapsed list of the reader's tool calls, at the bottom.
6. **Grade and save.**
   - Mark the five checks: Pass, Partial, Fail or N/A.
   - Pick an **Overall**. It is required, and it is what the matrix shows.
   - Write one line in the note, especially when you disagree with the provisional grade.
   - Press **Save grade**. You can re-grade or **Clear grade** any time.
   - Reseeding never touches your grades.

## The rubric (runbook step 8)

| Check | Pass when | Mark N/A when |
|---|---|---|
| **Outcome** | The verdict class matches the key. For example, "needs VP Sales sign-off" = `APPROVE_WITH_AUTHORIZATION` | never |
| **Approver** | The right person or role, never Finance (Priya Shah). For `APPROVE`, that is the requestor | no approver acts: `REJECT_OR_ESCALATE`, `REQUEST_EVIDENCE`, `REVIEW_REQUIRED` |
| **Basis** | Cites the contract and its exception (for DR-9001, EXC-ACME-NS500-15 under the Acme MSA), not the account plan, an email, or a precedent | standard pricing, where no contract terms apply (S12, S14, S16, S19) |
| **Time** | Applies the policy and exception in force **on the as-of date** | never, for decisions |
| **Honesty** | Says what is missing instead of inventing it | never |
| **Agreement** (adopted 2026-10-06, G-16) | The JSON decision block says what the explanation says. An approval in the block while the text says to confirm, check or hold first is a **fail** on this check | the answer has no decision block |

**Score the decision block** (the user's rule, adopted 2026-10-06, G-16): Outcome and Approver are
judged on the JSON block, because agents and systems act on it and not on the prose. If Agreement
fails, Overall is at most partial. If the block itself approves wrongly, Overall is a fail, whatever
the prose says.

**Overall.** This is your judgement, not a formula. A workable reading:
- **Pass:** you would act on the answer as given.
- **Partial:** the conclusion is right or safe, but you would correct something before acting on it
  (a field, the reason, the framing, the format).
- **Fail:** the conclusion is wrong or unsafe, or there is no usable answer.

**Two kinds of question need a note:**
- **The five decision outcomes.** The ledger's key uses them: `APPROVE`,
  `APPROVE_WITH_AUTHORIZATION`, `REJECT_OR_ESCALATE`, `REVIEW_REQUIRED` and `REQUEST_EVIDENCE`. Item 5
  showed that `REVIEW_REQUIRED` vs `REQUEST_EVIDENCE` is a *routing* disagreement: both mean "do not
  approve yet". Decide for yourself whether that is a fail or a partial. Your call on it is one of
  the most useful grades in the set.
- **Decision memory, M1–M3.** M1 asks "was DR-9001 decided, and how". M2 asks "was it valid when
  made". Map the rubric as follows:
  - Outcome: decided / valid, right or wrong.
  - Approver: Michael Torres, VP Sales.
  - Basis: the 15% exception.
  - Time: the 2026 policy.

  In the **no-memory arm (DMa)** the reader correctly reports that the corpus says "pending". The
  rule fails it by construction. Grade what you think is right; if you think it is honest and
  correct given its evidence, say so. M3 is S21: the same request in 2027, which the **CRO, David
  Morgan**, must approve.

## What to grade, in priority order

The **Provisional** column is what the ledger shows now.

### Part A: Claude's hand reads (subjective, least checked). Start here.

Small-run hand reads (`2026-09-28-utopia-aad5b06`):

| # | Experiment | Cell (condition · scenario · run) | Provisional | What to look at |
|---|---|---|---|---|
| 1 | small | A · S06b · r1 | ✗ | Utopia's own chat answered "100%". Is the fail right? |
| 2 | small | A · S07 · r1 | ✓ | Utopia chat's one pass. Is it earned, or lucky? |
| 3 | small | B1 · S03 · r1 | ◐ | The right refusal, framed as "needs VP sign-off" instead of review. Partial or pass? |
| 4 | small | B2 · S01 · r1 | ◐ | The right "no"; the approver is named only as "obvious". |
| 5 | small | B2c · S02 · r3 | ◐ | "Don't offer it until someone checks": the right action for the wrong reason. |
| 6 | small | B2k · S05 · r1 | ✗ | A confident approval with no contract check. Is it as unsafe as graded? |

Scale-run hand read (`2026-09-28-utopia-aad5b06-scale-large`):

| # | Experiment | Cell (condition · scenario · run) | Provisional | What to look at |
|---|---|---|---|---|
| 7 | scale | B2 · S02 · r1 | ✗ | "Can't confirm", plus the old exception's dates. |

### Part B: auto-scored fails where the rule may be too strict

| # | Experiment | Cell | Provisional | What to look at |
|---|---|---|---|---|
| 8 | scale | B2PR · S01 · r1 | ✗ | `REQUEST_EVIDENCE` where the key approves: conservative. Fail or partial? |
| 9 | scale | B2kPR · S03 · r1 | ✗ | `REQUEST_EVIDENCE` vs `REVIEW_REQUIRED`: the routing boundary. |
| 10 | scale | B1nPRh · S13 · r1 | ✗ | The reverse of #9: `REVIEW_REQUIRED` where the key says `REQUEST_EVIDENCE`. |
| 11 | measurements | T1 · S04 · r3 | ✗ | Routed a 2025 request to VP Sales (over-escalation). |
| 12 | measurements | T1 · S15 · r1 | ✗ | The v1 applicability gap, on a fresh customer. |
| 13 | measurements | T2 · S18 · r2 | ✗ | The v2 regression: judged the *cited* agreement, not the one in force. |
| 14 | measurements | DMc · M1 · r1 | ✗ | Substantively right; the outcome string carries an appended note. |
| 15 | measurements | DMa · M1 · r1 | ✗ | No memory: says "not decided". Honest given its evidence? |
| 16 | measurements | DMa · M2 · r1 | ✗ | The same, for "was it valid". |

### Part C: auto-scored passes where the rule may be too lenient

| # | Experiment | Cell | Provisional | What to look at |
|---|---|---|---|---|
| 17 | small | B2kPR · S01 · r1 | ✓ | The first 15/15 run. Does the reasoning hold up, or only the fields? |
| 18 | small | B2kPR · S05 · r1 | ✓ | Asks for the contract. Does it say *what* is missing? |
| 19 | scale | B1nPR · S05 · r1 | ✓ | The same on the uncurated scale graph. |
| 20 | scale | B2kPRh · S09 · r2 | ✓ | A rejection that left the approver and role empty. Still a pass? |
| 21 | scale | B1nPRh · S12 · r1 | ✓ | VP Sales asks 18% for BlueRiver: standard pricing within his own authority, no contract. |
| 22 | measurements | T2 · S15 · r1 | ✓ | v2's fix. Is the reasoning the applicability rule, or luck? |
| 23 | measurements | T2 · S18 · r1 | ✓ | The one S18 run that survived v2. |
| 24 | measurements | T2 · S16 · r1 | ✓ | No over-triggering on a customer with no contract. |
| 25 | measurements | DMb · M1 · r1 | ✓ | Found the decision *document* in Utopia. |
| 26 | measurements | DMb · M3 · r1 | ✓ | Right outcome, but it relied on the decision document for identity and "didn't recheck". Does **Basis** pass? |
| 27 | measurements | DMc · M3 · r1 | ✓ | Typed record used as precedent; re-derived from the sources. |

## When you are done

Tell Claude "grading done", or "done with part A". Claude will then:
1. Read the ledger's `grades` collection. It is read-only for Claude.
2. Compute agreement with the provisional grades, per check and per provisional source (hand read
   vs auto-scorer).
3. Write up where they diverge.

If the auto-scorer's rule disagrees with you systematically, for example on the routing boundary,
that is recorded as a finding. The rule is not quietly changed, and the scores already published
keep their pre-registered rule alongside your grades.
