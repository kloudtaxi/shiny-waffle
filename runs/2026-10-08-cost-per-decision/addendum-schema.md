# Addendum: a cheaper agent held to a fixed record format (pre-registration, 2026-10-08)

**The question.** In G-23, Haiku 4.5 on the OWM slice was unsafe 12 times in 84 by the
pre-registered rule. Rescored, that's 3 wrong decisions and **9 records** that were incomplete or
misformatted: an empty approver, or a name with ids appended. If the record's format is
**enforced**, is a cheaper agent's record reliable enough for systems to act on? The user's go:
"Run both", 2026-10-08.

## Design

**Arm H-slice-schema** is H-slice unchanged in every respect but one:
- Haiku 4.5 on the OWM-served slice;
- the same procedure in the system prompt, and the same questions;
- 28 scenarios × 3.

The change: each call carries `claude -p --json-schema`, the product's record format, validated
by the API. The answer is the validated record alone. Schema (`run_schema.py`):
- **The outcome is one of the five.** The eligibility status is one of the procedure's values.
- **Discount:**
  - `authority.approver` is **required, and must be an employee's full name from the HR export**
    (an enum of the 19 names);
  - `requestor_authorized` is a boolean.

  Every discount key names an approver, so requiring one forces nothing false.
- **Credit:** each `authority.approvers[]` entry has `name` from the same enum, `kind` either
  approval or concurrence, and a role. The list may be empty. The API rejects top-level
  conditionals, so "an approval must list an approver" can't be enforced for credit.
- **`conditions`:** items carry `what`, `who` and `blocking`.

**Scoring:** the record is wrapped in a fenced block and scored by G-23's own `score_arm` (strict,
as pre-registered) and by `rescore.py`'s rules (exploratory, as in G-23). No explanation text
exists, so prose agreement isn't measured.

## Predictions (fixed before any answer)

| # | Prediction | Why |
|---|---|---|
| S1 | **Records incomplete or misformatted (the rescore rules): ≤ 1 of 84** (H-slice: 9) | The enum and the required approver remove both defect types |
| S2 | **Strict unsafe ≤ 4 of 84** (H-slice: 12) | What's left is the wrong decisions |
| S3 | **Wrong decisions (rescored) ≤ 3** (H-slice: 3) | The format doesn't change the judgment |
| S4 | **Cost ≤ $0.04 per decision** (H-slice: $0.048) | No long prose explanation |

## Cost and guard

84 calls, about $4. Stop if the first 6 average over $0.08.
