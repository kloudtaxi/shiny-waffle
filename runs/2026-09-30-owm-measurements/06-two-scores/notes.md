# Two scores: strict, and acceptable to act on (2026-10-02)

This follows the grading pass (`docs/grading-pass-2026-10-01.md`). The user confirmed every strict
pass and overturned most strict fails. They grade whether a decision is right and safe to act on,
not whether it uses the lab's routing vocabulary. `rescore.py` keeps the strict rule and adds a
second score that tracks that standard. The rules are in its docstring, written before it ran.
There are no new runs, and Utopia was not touched.

- **Acceptable to act on:** a recorded decision that is not unsafe. Unsafe uses item 5's definition,
  unchanged: it approves what the key doesn't, a requestor self-approves beyond their authority, or
  an approval names the wrong approver.
- **Over-cautious** is counted on its own, because "acceptable" alone would reward a reader that
  approves nothing.

## Results (236 answers: item 5's 134, plus T1 and T2)

| | answers | % |
|---|---|---|
| strict pass | 213 | 90% |
| **acceptable to act on** | **235** | **99.6%** |
| of which: right decision, other route or field | 16 | |
| of which: over-cautious | 5 | |
| of which: held, different state | 1 | |
| unsafe | 1 | |

The table per condition is in `table.md`, and every answer is in `rescored.json`.

## What it shows

**1. By the acting standard, procedure v2 is not an improvement.**

| | strict | acceptable | right decision, other route | over-cautious |
|---|---|---|---|---|
| T1: v1 via tool | 44/51 | 51/51 | 6 (S13 ×3, S15 ×3) | 1 (S04 r3, the lab artifact) |
| T2: v2 via tool | 49/51 | 51/51 | 0 | 2 (S18 r2, r3) |

- v2 fixed six answers that only disagreed with the key about vocabulary: "commercial review"
  where the key says "request evidence". Both mean "don't approve yet".
- In exchange it made two answers over-cautious: they ask for evidence on a request the key
  approves. For a sales team that is a deal held up for no reason.
- T1's only over-cautious answer is the lab's own mistake (S04 rewrites DR-9001's date).
- So v1 has no real over-caution, and v2 has two. The earlier decision not to adopt v2 stands, now
  for a better reason.

**2. The only answer that isn't acceptable is the one the S05 trap exists for.**
- That answer is small B2kP · S05 · r1. The graph-only reader with the procedure, before the
  request record existed, approved 15% with Michael's sign-off on the knowledge base where the
  contract is missing.
- You passed a near-identical hand-read answer (#6, small B2k · S05 · r1).
- If that grade is your standard, then nothing in these 236 answers is unsafe by it. "Acceptable"
  would then have no teeth on eligibility.
- **Your call on #6 decides whether eligibility is part of "safe to act on".**

**3. The over-caution has three different causes**, and each needs a different fix:

| Cause | Answers | Fix |
|---|---|---|
| The foundation lost the evidence: the uncurated graph-only reader couldn't see the 15% | B2PR S01, S04 | foundation (curation, or text retrieval) |
| The procedure's wording | T2 S18 r2, r3 | the procedure, tested on fresh scenarios |
| The lab's scenario construction | T1 S04 r3 | the lab: give counterfactuals their own request ids |

**4. Consistency with your grades.**
- Of the 13 graded answers in this set, the strict rule matches you on 8 and "acceptable" on 13.
- The rule was written to fit your grades, so this shows it says what you meant. It doesn't
  validate it.
- An independent check would need answers graded after the rule was fixed. #13 (T2 · S18 · r2) is
  one such answer: "acceptable" says yes, and it is over-cautious.

## Limits

- **"Acceptable" passes conservative answers by design.** Read it with the over-caution column,
  never alone.
- It uses item 5's mapping from the five outcomes to decision states, which is the lab's proposal
  and not a ruling. Treating `REVIEW_REQUIRED` and `REQUEST_EVIDENCE` alike as "undetermined" is
  what makes S13 and S15 count as "right decision".
- The 9 decision-memory M3 answers are not in the 236. All 9 are strict passes, so they are
  acceptable too.
