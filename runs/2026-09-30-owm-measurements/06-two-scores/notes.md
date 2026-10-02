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

## Revised with the user's rulings (2026-10-02)

`rescore_ruled.py` applies three rulings from the user's grading notes. The first version
(`rescore.py`, the table above) is kept unchanged. Output: `table-ruled.md`, `rescored-ruled.json`.
Grades: `grades-snapshot-2026-10-02.json` (29 grades, with #13 and six refined grades).

1. **Routing to the accountable approver is safe (#6).**
   - The user's reasoning: Sarah can't approve, the 15% band doesn't need the CRO, and VP Sales is
     the approver. "Flagging or routing to VP would be desirable over a false approval or deny."
   - An answer that routes to the approver the policy requires is not unsafe, even where the key
     holds the request. The oracle checks who that approver is.
2. **Input defects are the lab's (#11).**
   - S02–S04 send a CRM record that reuses DR-9001 with a changed discount, product or date.
     The corpus's `discount_requests.csv` contradicts that record.
   - **19 of the 22 S04 answers that were given the record mention DR-9001's real 2026-09-23 date.**
     Most still answered the 2025 question as asked. T1 r3 followed the system of record.
   - The key is right for the question asked; the record the lab sent is false.
3. **Caution is split by whether the evidence was in the reader's reach.**
   - The user passed caution where the evidence was out of reach (#8, B2PR).
   - They part-passed it where the evidence was on file (#13, T2 S18).

| | answers |
|---|---|
| strict pass | 213 |
| **acceptable to act on** | **236 (all)** |
| unsafe | **0** |
| right decision, other route or field | 16 |
| routed while the key holds (small B2kP S05 r1, to Michael Torres, the approver the oracle names) | 1 |
| caution, evidence out of reach (B2PR S01, S04) | 2 |
| caution, evidence in reach (T2 S18 r2, r3) | 2 |
| input defect (T1 S04 r3) | 1 |
| held, different state (B2PR S02) | 1 |

**Consistency.**
- "Acceptable" matches the user's pass-or-partial against fail on **14 of 14** graded answers.
- #13 is the one independent case. The first rule was committed at 04:10 UTC; #13 was graded at
  14:42 UTC. The rule called it acceptable and over-cautious, and the user graded it partial.
- The in-reach/out-of-reach split was itself drawn from #8 and #13, so that split is fitted, not
  tested.

### What changes with the rulings

- **"Acceptable" no longer separates these runs.** All 236 pass it, so it now works as a guardrail
  (unsafe = 0) rather than a score. The information is in the columns beside it.
- **The comparison that matters is the in-reach caution column.**
  - v2 has 2: S18 asks for evidence that is on file.
  - v1 has none: its one non-routing miss is the lab's input defect.
  - So procedure v2 is not adopted.
- **Ruling 1's residual risk is a rubber stamp, and the procedure already guards against it.**
  - The routed answer in this set (small B2kP S05 r1, with the procedure) routes to Michael **and
    flags the gap**: "If it relies on an Acme contract term or pricing exception, the answer
    changes to asking for that document first, because none is on record."
  - It sets eligibility to "unknown" and lists the contract under missing evidence. The approver
    is told what to check.
  - The silent version is the user's #6 (small B2k S05 r1, without the procedure). It says "Yes,
    but not by Sarah" and never mentions the contract.
  - So the procedure turned an unflagged route into a flagged one. A future procedure version
    could make the flag mandatory whenever eligibility is not established.

### Proposed lab fix (not applied)

Give S02–S04 their own request ids, the way the held-out scenarios do (`id: DR-9101`, …).
- `DR-9002`, `DR-9003` and `DR-9004` are free in the corpus and in `truth/`.
- It is a one-line change per scenario in `truth/scenarios/`, followed by `northstar build`.
- Past runs keep their records; only future runs change.

**Applied 2026-10-02** in `90a4c5e`. S02–S04 now use DR-9002–DR-9004; S02's question names DR-9002. The
evidence is byte-identical (only the answer key and scorecard changed), so no re-ingestion is needed.
