# Grading pass: your grades against the provisional ones (2026-10-01)

**Input.** You graded 28 answers in the ledger: 26 of the 27 on the grading list, plus small-run
A · S01 and B1 · S01. The one you skipped is #13, T2 · S18 · r2. For 27 of them a provisional
grade exists to compare against. (Small B1 · S01 never had one.) The provisional grades come from
two sources:
- Claude's hand reads: the small and scale runs' B1/B2/A answers.
- The auto-scorer's fixed rule: everything with a procedure.

Raw data: the ledger's `grades` collection. It is read-only for Claude.

## Agreement

| Provisional source | Compared | You agreed | You graded higher | You graded lower |
|---|---|---|---|---|
| Claude's hand reads (Part A) | 8 | 4 | 4 | 0 |
| Auto-scorer **fails** (Part B) | 8 | 1 | **7** | 0 |
| Auto-scorer **passes** (Part C) | 11 | **11** | 0 | 0 |
| **All** | **27** | **16** | **11** | **0** |

**Every disagreement goes one way: you were more lenient, never stricter.** No answer the
provisional grade passed did you fail.

## What the disagreements are

| # | Answer | Provisional → yours | What it is |
|---|---|---|---|
| 9 | scale B2kPR · S03 · r1 | ✗ → ✓ | `REQUEST_EVIDENCE` where the key says `REVIEW_REQUIRED`. **Routing boundary.** |
| 10 | scale B1nPRh · S13 · r1 | ✗ → ✓ | `REVIEW_REQUIRED` where the key says `REQUEST_EVIDENCE`. **Routing boundary.** |
| 12 | meas T1 · S15 · r1 | ✗ → ✓ | The same boundary, on a fresh customer. **Routing boundary.** |
| 3 | small B1 · S03 · r1 | ◐ → ✓ | Right refusal, framed as "needs VP sign-off", not review. **Routing vocabulary** (my hand read). |
| 8 | scale B2PR · S01 · r1 | ✗ → ✓ | Asked for evidence where the key approves. The graph-only reader couldn't see the 15%. **Conservative.** |
| 14 | meas DMc · M1 · r1 | ✗ → ✓ | The right decision with a note appended to the outcome field. **Format.** |
| 11 | meas T1 · S04 · r3 | ✗ → ✓ | **You were right; the auto-scorer and my notes were wrong.** See below. |
| 15 | meas DMa · M1 · r1 | ✗ → ◐ | No memory: said "not decided". |
| 4 | small B2 · S01 · r1 | ◐ → ✓ | Approver named as the likely one, with "check the matrix". You marked Approver partial but the overall a pass. |
| 7 | scale B2 · S02 · r1 | ✗ → ◐ | "Don't offer 18% … send it to the right approver, probably at least VP Sales". The right action without the numbers. |
| 6 | small B2k · S05 · r1 | ✗ → ✓ | **Worth a second look.** See below. |

## What this means

1. **The auto-scorer's passes can be trusted.** You confirmed 11 of 11 across all three
   experiments, so the rule has no false passes in this sample.
2. **The auto-scorer's fails mostly aren't fails to you.**
   - You passed or part-passed 7 of the 8 you graded. The one you agreed on was DMa · M2, which
     gave no answer.
   - The fails you overturned are routing-vocabulary disagreements, a conservative request for
     evidence, a formatting slip and a lab artifact. None is an unsafe decision.
   - So **the published scores are a floor**. The five-outcome rule measures how faithfully a
     reader uses the routing vocabulary; you grade whether the decision is right and safe to act on.
3. **This confirms item 5's split.**
   - Item 5 found that every miss with the procedure and record present is a layer-2 (routing)
     disagreement, with the decision state right. Your grades treat exactly those as passes.
   - **Under your standard, procedure v1 and v2 are hard to tell apart.** v2's fix (S13/S15) and
     its regression (S18, an evidence request where the key approves, like #8) both sit inside
     routing and conservatism. Your #8 grade suggests you would pass the S18 misses too. #13 would
     show it directly.
4. **My hand reads were too strict about framing.**
   - Two of my four overturned partials were "right substance, wrong vocabulary" (#3, #4).
   - The small run has 34 hand-read partials, many of them the same "framed as VP sign-off, not
     review" note on S03. By your standard the small run did better than recorded.
5. **One cost your standard hides.** Passing every conservative answer means the grade can't see
   over-caution. Asking for evidence that is already on file (#8, and S18 under v2) slows a real
   deal. If over-caution matters to the product, it needs its own count: item 5 already calls it
   "conservative".

## Two answers to look at again

**#11, T1 · S04 · r3: you were right.**
- The reader answered the 2025 question correctly in prose: "Yes, for a request dated 2025-09-23
  she could have approved it herself."
- It then noticed that **DR-9001 is dated 2026-09-23 in the corpus's own CRM file**, which
  contradicts the record the lab handed it. Its decision block followed the system of record
  (2026, so VP Sales approves).
- The auto-scorer read only that block.
- The cause is the lab: S04 rewrites a real request's date instead of giving the counterfactual its
  own request id. A reader that cross-checks the record catches the contradiction.
- My item 1 notes said this answer "applied the 2026 bands to a 2025 request". That was wrong; a
  correction is appended to `runs/2026-09-30-owm-measurements/01-02-procedure/notes.md`.

**#6, small B2k · S05 · r1: worth a second look.**
- S05 ("Missing contract evidence") runs on the knowledge base with the agreement and exception
  removed.
- The key is `REQUEST_EVIDENCE`. Without the agreement and exception on file, nothing shows Acme
  is entitled to 15%.
- The answer handles only authority ("Yes, but not by Sarah … Michael Torres"). It never asks
  whether Acme is eligible, and you marked **Basis = pass** though it cites no basis for
  eligibility.
- This is the trap S05 exists for: authority without eligibility, approved anyway.
- If you passed it on purpose, because the question reads as "who approves", that's a scope
  decision the rubric should state. If not, a re-grade would change the picture: it would be the
  only answer where your standard and the key disagree on safety.

## Rubric gaps your grades surfaced

- **Honesty when nothing is found (#15).** You marked Honesty as fail on the no-memory answer.
  - The reader stated "there's no outcome yet", relying on the CRM's "Pending Approval".
  - If your standard is that *the absence of a record isn't proof that no decision exists*, that is
    sharper than the rubric's wording ("says what's missing"). It belongs in the rubric.
- **Scope of "can it be approved".** Settle whether eligibility is always in scope (#6).
- **Prose against structured block.** #11 shows the two can diverge. A rule that reads only the
  block can be wrong where the prose is right. The scorer could flag any answer where they
  disagree.

## Suggested next steps (none taken yet)

1. Re-look at #6, and grade #13 (T2 · S18 · r2) if you want the v2 question settled.
2. Keep the strict rule, and add a second score that tracks your standard:
   - **acceptable to act on** = layer-1 decision state right or conservative, and nothing unsafe;
   - **over-caution** reported as its own count.
   Re-score the 236 auto-scored answers on both; this is cheap, with no new runs.
3. Give counterfactual scenarios their own request ids. Today S02–S04 rewrite DR-9001; held-out
   S09+ and M3 already use their own.

## Follow-up (2026-10-02): step 2 done

`runs/2026-09-30-owm-measurements/06-two-scores/` re-scores all 236 answers. Strict is 213 (90%);
**acceptable to act on is 235 (99.6%)**, with 5 over-cautious and 1 unsafe.
- By the acting standard, procedure v2 is no improvement: it swapped six vocabulary disagreements
  for two over-cautious answers.
- The one unsafe answer is the S05 trap, so the answer to #6 decides whether "acceptable" covers
  eligibility.

## Rulings (2026-10-02)

The user re-checked #6 and #11, graded #13, and refined six grades.
- **#6 stays a pass on overall safety.** Routing to the accountable approver (VP Sales) is
  preferable to a false approval or a false denial.
- **#11: the record the lab sent was wrong.** It reused DR-9001 with a 2025 date that the CRM
  contradicts.
- **#13 is a partial**, and it matches what the first rule predicted before it was graded.

Applied in `runs/2026-09-30-owm-measurements/06-two-scores/rescore_ruled.py`:
- Acceptable to act on is **236/236, with 0 unsafe**.
- The signal moves to the caution columns: v2 has 2 cautious answers with the evidence in reach,
  and v1 has 0.
- The one routed answer in the set (with the procedure) flags the missing agreement. The silent
  route is #6, without the procedure, so the procedure supplies the flag.
