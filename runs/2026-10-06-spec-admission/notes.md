# Admitting a procedure (G-07 + G-06), and an AI-written SLA procedure through it (G-12)

> **Status:** done, including addendum 2 (the user's decisions, pre-registered in `e8ca7e1`):
> - **Gate C now scores on the outcome.** Both AI-written credit specs are now refused (6 idle of
>   16, against the reference's 2 of 12).
> - **The revision loop worked.** With only the gate's report, the SLA author revised once, and
>   the revision is **admitted**: 10/10 clean, safe under attack, 0 idle.
>
> Below is the first round, then addendum 2. Pre-registered in `plan.md` (`2cff2c6`); the first
> addendum (`b9fe2ac`) moved gate C to the deployed form before any run.
> - **The AI-written SLA procedure** held all 10 clean scenarios at its first attempt, with no fix
>   round, and was safe on every SLA attack. It was **not admitted**: gate C found 2 idle reliances
>   on the holiday calendar, against the reference's 0.
> - **Calibration:** the gate admits all three references. It also admits both AI-written credit
>   specs, because the pre-registered reliance key is too broad to see their over-reliance. An
>   exploratory outcome-level key does see it.
> - **Spend:** 10 new Jev calls (under a cent); no reader or Utopia spend.

## What was built

- `lab/spec_admission/admit.py`: the admission gate. Each run is in the spec's deployed form,
  with the company's register, in the default mode.
  - **A, clean:** every clean scenario of its type is held.
  - **B, under attack:** no unsafe target, side effect or error on any sealed attack set of its
    type. That is 19 discount attacks (A, B, F1–F3), 24 credit (C, D, E, F4–F6) and 4 SLA
    (F7–F10).
  - **C, reliance:** no more idle reliances than the type's reference. An idle reliance is a
    relied-on document whose removal, from the corpus and the register alike, leaves the scored
    decision unchanged.

  A verdict is refused if any ablation couldn't be judged by Jev.
- `flow.run(..., trace=)`: an optional trace that receives the relied-on documents. No record
  changes.
- `SPEC_FORMAT.md`: "rely only on documents that feed this decision's outcome" (G-06), and the
  admission gate (G-07).

## Calibration: existing specs (P1–P4)

| Spec | A, clean | B, under attack | C, idle / relied (reference) | Verdict |
|---|---|---|---|---|
| `discount.yaml` (reference) | 18/18 | 0 unsafe in 19 (0 routed) | 9 / 34 | admitted |
| `credit_v2.yaml` (reference) | 10/10 | 0 in 24 (0 routed) | 0 / 12 | admitted |
| `sla.yaml` (reference) | 10/10 | 0 in 4 (0 routed) | 0 / 39 | admitted |
| `credit_v3.yaml` | 10/10 | 0 in 24 | 0 / 0 (it uses register entries, not `rely`) | admitted |
| `credit_agent_v2.yaml` | 10/10 | 0 in 24 | 0 / 16 (0) | admitted |
| `credit_agent.yaml` | 10/10 | 0 in 24 | 0 / 16 (0) | admitted |

Jev: no live calls; every judgment was replayed.

| # | Prediction | Result |
|---|---|---|
| P1 | The references pass A and B | **Holds** |
| P2 | `credit_agent_v2` passes A and B, **fails C** | **A and B hold; C is missed.** 0 idle |
| P3 | `credit_agent` passes A and B, **fails C** | **A and B hold; C is missed.** 0 idle |
| P4 | Without the register, `credit_agent` has more unsafe targets on set C than `credit_v2` | **Holds, by the committed record** (3 against 1, `runs/2026-10-05-instrument-guards/`), not re-run |

**Why gate C missed the agent specs' over-reliance.** The scored decision key for credit
(`setc.key`) includes the eligibility maximum. A guarantee still raises that maximum even when the
outcome doesn't need it, so removing it changes the key, and the reliance never counts as idle. The
pre-registered measure is too broad to see G-06's pattern.

**Exploratory, not pre-registered** (`explore_outcome_idle.py`): the same ablation, scored on the
outcome and the approvers only.

| Spec | Outcome-idle / relied |
|---|---|
| `credit_v2.yaml` | 2 / 12 |
| `credit_agent.yaml` | 6 / 16 |
| `credit_agent_v2.yaml` | 6 / 16 |

That is G-06's pattern: the agent specs rely on 4 more documents that don't decide the outcome.
Adopting an outcome-level gate C would need its own decision and a fresh test. It is proposed
below, not applied.

**And in the deployed form, over-reliance cost nothing:** both agent specs routed 0 correct
decisions across 24 attacks. G-06's cost (set D: 22 routed for the v2 agent) came from the guards
without the register. With the register in default mode, those decisions read approved versions,
and nothing waits.

## G-12: an AI-written SLA procedure

**The author** was a subagent on the same information diet as the 2026-10-04 credit author. It had
`SPEC_FORMAT.md`, the SLA procedure, `dataset/evidence/` and the input and record contract.
- It listed the files it read, and all of them are in the allowed set.
- Its spec, `lab/owm_kernel/specs/sla_agent.yaml` (553 lines), was committed as delivered
  (`46a2d32`), before scoring.
- The runner accepted it and ran all 10 clean cases without an error, so **no fix round was
  needed**.
- It declares `registered_kinds` itself, mapping every kind to the register.

| Gate | Result |
|---|---|
| A, clean | **10/10 held** (outcome, credit, every Northstar obligation, both breach findings) |
| B, under attack | 0 unsafe or errors on the 4 SLA attacks (F7–F10), 0 routed |
| C, reliance | **2 idle of 39 relied** (S38 and S40: the holiday calendar), against the reference's 0 of 39 |
| **Verdict** | **Not admitted** (fails C) |

**Why C failed:** the spec relies on the holiday calendar whenever a holiday falls anywhere in the
dates its business-day calculations span (`hol_hit`). In S38 and S40, a holiday falls in the span
but changes no computed time. Removing the calendar leaves the decision unchanged, so the reliance
is idle. It's G-06's pattern in a mild form: a condition that is broader than "this document
changed the result". It costs nothing in the default mode, where 0 decisions were routed.

| # | Prediction | Result |
|---|---|---|
| P5 | Loads after at most one fix round, and holds **at least 7 of 10** clean scenarios | **Holds, and is beaten:** no fix round, and 10/10 |
| P6 | **Not admitted** at its first attempt, failing gate A or C | **Holds:** it fails C |

As pre-registered, the spec was not fixed after scoring. The failed admission is the finding.

## What it shows

1. **An agent can author a correct procedure for a type the primitives weren't shaped around**
   (G-12). Clocks, business hours, holidays, pauses and obligations came out 10/10 at the first
   attempt. That is stronger than the credit author (10/10 after the format was shaped around
   credit).
2. **The gate works as a gate.** It admitted the references and refused a correct-but-sloppy spec.
   But its reliance measure, as pre-registered, is too coarse for credit: a document that feeds an
   intermediate field (the eligibility maximum) never counts as idle.
3. **With the register in default mode, over-reliance has no observed cost:** 0 correct decisions
   were routed across 24 credit and 4 SLA attacks for every spec. G-06's cost came from guards
   acting without the register. Gate C is now a hygiene check more than a safety check.

## Addendum 2: the user's decisions (pre-registered in `e8ca7e1`)

**1. Gate C scores on the outcome** (`--reliance-key outcome`, now the default; `full` reproduces
the first round). The seven specs were re-run (`calibration-outcome/`):

| Spec | C, idle / relied | Verdict |
|---|---|---|
| `discount.yaml` (reference) | 9 / 34 | admitted |
| `credit_v2.yaml` (reference) | **2 / 12** | admitted |
| `sla.yaml` (reference) | 0 / 39 | admitted |
| `credit_v3.yaml` | 0 / 0 | admitted |
| `credit_agent_v2.yaml` | **6 / 16** | **not admitted** |
| `credit_agent.yaml` | **6 / 16** | **not admitted** |
| `sla_agent_v1.yaml` (first version, `46a2d32`) | 2 / 39 | not admitted |

A and B are unchanged for every spec.
- **Q1 holds:** the exploration reproduces, and both agent credit specs are now refused.
- **Q2 holds:** discount stays at 9 (at least 9, as expected), and SLA is unchanged.

**2. The revision loop.** The author (the same subagent, with its context) got only the gate's report:
- A passed, B passed, C failed;
- the holiday calendar was relied on idly in 2 of 10 clean cases.

It opened no files. It replaced "a holiday falls in the date span" with a counterfactual: measure
the clocks again on a calendar with no holidays, and rely on the calendar only if the response or
restoration result differs. The revision was committed as delivered (`8514430`) before gating.

| Gate | Revision 1 |
|---|---|
| A, clean | 10/10 held |
| B, under attack | 0 unsafe or errors in 4 attacks, 0 routed |
| C, reliance | **0 idle of 37 relied** |
| **Verdict** | **Admitted** |

- **R1 holds:** admitted after one revision.
- **R2 holds:** no regression.
- **Jev:** no new calls.

**Exploratory, not pre-registered: the mirror of gate C** (`explore_unrelied.py`). Each governing
document the decision did *not* rely on is removed, and the decision is checked for a change.

| Spec | Unwatched dependence |
|---|---|
| `sla_agent_v1.yaml` | none |
| `sla_agent.yaml` (revision 1) | none |
| `sla.yaml` (reference) | **S37: the holiday calendar changes the decision, but isn't relied on** |

Gate C catches over-reliance only. A spec that relies on *too little* passes it, and the guards
then never watch that document. The reference SLA spec has one such case. The risk is low in the
default mode, where registered documents are read as their approved versions anyway. A mirror test
for the gate is a candidate (G-34).

## What the whole run shows

1. **An agent can author a correct procedure for a type the primitives weren't shaped around**
   (G-12): 10/10 at the first attempt.
2. **The gate plus a feedback loop is a workable admission process.** The gate refused a correct
   but sloppy spec. The author fixed it from the gate's report alone, in one round, without
   regressions. That is the product flow: agents propose, the gate admits, people approve.
3. **The measure matters.** The pre-registered reliance key was too coarse for credit. The
   outcome-level key refuses both agent credit specs, which matches G-06's evidence.
4. **With the register in default mode, reliance has no observed safety cost** (0 routed, 0 unsafe
   everywhere). Gate C is about keeping the guards meaningful, not about any attack seen here.

## Open for the user (answered 2026-10-06; see addendum 2)

- **Gate C's measure:** keep the pre-registered key, or adopt the outcome-level key (the outcome
  and approvers; for SLA, the outcome, credit and obligations, as now). The exploratory
  measurement is in `explore-outcome-idle.json`.
- **The SLA spec:** leave it not admitted, or test a revision loop in which the author sees the
  gate's report. That would be a new, pre-registered test.

## Files

| File | What |
|---|---|
| `plan.md` | Pre-registration and addendum |
| `calibration/*.json` | The gate's reports on the six existing specs |
| `explore_outcome_idle.py`, `explore-outcome-idle.json` | Exploratory outcome-level reliance |
| `errors_only.py` | The fix-round runner (errors only; not needed) |
| `sla_agent.json` | The gate's report on the agent's SLA spec |
| `jev-calls.jsonl` | 10 new Jev calls, made by the errors-only run |
| `calibration-outcome/*.json` | Addendum 2: the seven specs on the outcome-level key |
| `sla_agent_v1.yaml` | The first version, snapshotted from `46a2d32`, so it could be gated while the author revised |
| `sla_agent_r1.json` | The gate's report on revision 1 |
| `explore_unrelied.py` | Exploratory: the mirror test |

The gate's own counter said "live Jev 10" on the G-12 run. Those 10 came from the errors-only run's
recording, which the gate didn't load. The counter now loads it (fixed after the run), and the G-12
run made no network calls.
