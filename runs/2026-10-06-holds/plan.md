# G-35: putting holds in the decision record (pre-registration, 2026-10-06)

The user chose G-35 from the board on 2026-10-06. G-16's application found 59 of 757 reader answers
that approve in the JSON block while the explanation says to confirm or hold first. The decision
record has no field for "approve once X is confirmed". This file is committed before any run.

**The question:** if the record gets a `conditions` field, and the procedure says that systems act
on the record alone, do holds move from the prose into the block, without changing outcomes and
without adding holds where none is needed?

## The treatment

These are copies of the two procedures (`procedures/discount-approval.md`,
`procedures/credit-limit.md`). The canonical ones in `owm/procedures/` are unchanged. Each copy
adds `"conditions": []` to the JSON template, plus this rule, identical in both:

> **Conditions.** If anything must be confirmed, corrected or done before this decision may be
> acted on, put it in `conditions`, each as `{"what": ..., "who": ..., "blocking": true}`. Systems
> act on the decision record alone: they will not act while a blocking condition is open, and they
> never read the explanation, so a condition stated only in the explanation will be ignored. Use
> `"blocking": false` for something worth noting that doesn't stop the decision. If nothing must
> happen first, leave `conditions` empty.

## The run

- **Reader:** `claude -p` (Opus 5.5), no tools. The system prompt is the fixed one plus the
  procedure (the original for control, the copy for treatment). The user message is the question
  and the request, then every document of the scenario's corpus. This is set F's `pf` arm.
- **Questions:**
  - S22–S25: J3's own text (`runs/2026-10-02-jev-probe/j3/questions.tsv`): "the request, as
    submitted";
  - discount: experiment 4's builder;
  - credit: set C's reader prompt.

| Group | Scenarios | Why |
|---|---|---|
| **Hold-prone** | S04 (the question's 2025 date against the CRM's 2026), S22 (8% submitted against 15% in the CRM), S27, S31, S35 (credit: "confirm before recording") | the clusters of G-16's 59 |
| **Controls** (no conflict) | S25 (J3's control), S01, S26 | to catch holds added where none is needed |

8 scenarios × 2 arms × 3 runs = **48 calls, about $15**. The cost guard stops the run above $0.45 a
call.

## Measures

- **Hold in prose:** the prose asks to wait, confirm or correct before acting, while the block is
  an approval with **no blocking condition** that captures it. That is G-16's failure. It is judged
  by one reading subagent with G-16's definition, extended to the `conditions` field. The arm
  shows through the field, so the read can't be blind.
- **Blocking conditions:** counted from the JSON.
- **Outcome safety:** the committed graders (experiment 4's `classify`; experiment 5's `grade` and
  set C's `unsafe_type`).

## Predictions

| # | Prediction |
|---|---|
| H1 | **Control reproduces the pattern:** at least 5 of the 15 hold-prone answers hold in prose |
| H2 | **Treatment moves the hold into the block:** at most 1 of 15 hold-prone answers holds in prose |
| H3 | **No outcome change:** treatment's unsafe count is at most control's. Per scenario, the block outcomes differ by at most 1 answer of 3 between the arms |
| H4 | **No over-holding:** on the 9 control answers, treatment adds a blocking condition to at most 2 |

**If H2–H4 hold, the user decides on adoption:** the `conditions` field in `owm/procedures/` and in
the OWM decision record contract, with executors honouring blocking conditions.

## Addendum (2026-10-06, after the results, before any new run): the refined rule, as a check

The user chose "refine and re-check". Round one's results (`notes.md`, `b6f71d3`) shaped these two
sentences, so this is a **check**, not fresh evidence. They are added to the treatment rule
(`procedures-v2/`). Only the treatment arm re-runs (`treatment-v2`): 24 calls, about $7.50.

> **Don't list the approval the outcome itself requires.** For APPROVE_WITH_AUTHORIZATION, the
> approver named in `authority` must approve. `conditions` is for anything else.
>
> **Decide on the system of record.** If a submitted figure or date differs from the system of
> record, decide on the system of record's value and record the difference as a condition. A
> condition never replaces deciding.

| # | Prediction |
|---|---|
| V1 | Holds still reach the block: 0 of 15 hold-prone answers hold only in prose |
| V2 | Restated approvals fall from 11 of 24 to **at most 2 of 24** |
| V3 | No conditional approval on a submitted value that the system of record contradicts. S22 is decided on the CRM's 15% in all 3 runs |
| V4 | Controls: a blocking condition on **at most 1 of 9** |

The reads use the same definitions as round one (one reading subagent).
