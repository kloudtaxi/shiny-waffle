# Instrument guards and set D (2026-10-05)

**STATUS: GUARDS BUILT AND CHECKED. Set D is with the user** (`set-d-brief.md`).
- Pre-registered in `plan.md` (`5b145ed`), before any guard code.
- Set C was re-run as a check only, since it shaped these guards.

## What was built

**The guards:** three generic, opt-in guards in the kernel, declared in a spec's `documents`
section. They are 80 lines in `kernel.py` (`lineages`, `lineage_routes`) and 5 in `flow.py`.

| Guard | Declared by | Rule |
|---|---|---|
| **L1** | `lineage_kinds` | A document naming another document of its kind (by the kind's id prefixes) is a dependent: an amendment, an extension. It counts only if its parent is on file and qualifies. Experiment 4's G5b, no longer tied to "Agreement:" |
| **L2** | `lineage_kinds` | Relying on any member of a lineage that has a dependent routes to a person |
| **L3** | `single_kinds` | Relying on two separate lineages of the kind routes (a conflict between instruments) |

**The specs:**

| Spec | Change from v1 |
|---|---|
| `specs/credit_v2.yaml` | The two declarations, plus judging every covering guarantee and relying on all that apply, instead of the first by filename |
| `specs/credit_agent_v2.yaml` | **Only the two declaration lines** (and a comment). The agent's logic is untouched |

**The format reference:** `SPEC_FORMAT.md` now documents every `documents` key. That includes the
G1/G5 keys that existed but were never written down, which is why neither credit spec declared
them. See the correction in `runs/2026-10-03-exp5-credit/set-c-notes.md`.

| File | sha256 (first 12) |
|---|---|
| `kernel.py` | `b2c4d011afb5` |
| `flow.py` | `fce102ac7dae` |
| `credit_v2.yaml` | `20e42df05fbe` |
| `credit_agent_v2.yaml` | `f4c1a5defc56` |

## Checks

| # | Check | Result |
|---|---|---|
| K1 | The existing specs decide exactly as before | ✓ **identical** on four checks: YAML (discount 69 rows, credit 10, SLA 10); Python discount and credit (experiment 6's `check_behaviour.py`, 69 + 10); Python SLA (experiment 6's harness replay, outputs unchanged). Experiment 5's own Python replays fail with "not recorded", but they fail identically without this change: experiment 6's four new staff changed the role question, as `check_behaviour.py` documents |
| K2 | v2 on clean S26–S35 | ✓ both v2 specs match v1 on every decision field, **10/10 strict**, with no new judgment calls |
| K3 | v2 on set C (a check, not evidence) | ✓ **every prediction held**, including the collateral routing counts. Table below |
| K4 | v2 under the handed-in filenames | ✓ **identical** to K3: v2 doesn't depend on file order. Under those names v1 python and v1 yaml are unsafe on C2 |
| M1 | Lineage on by default for every graded kind of the existing specs (measured) | Credit and SLA unchanged. **Discount: 9 of 18 clean decisions would route.** The current pricing exception says "Supersedes EXC-ACME-NS500-10", and lineage read from text can't tell *supersedes* from *amends* |

**K3: set C, v1 against v2** (`set-c-results.md`):

| Engine | Targets unsafe | Targets routed | Collateral unsafe | Collateral routed (key not a route) |
|---|---|---|---|---|
| v1 yaml | 2 (C1, C3) | 0 | 2 (S34, S33) | 0 |
| **v2 yaml** | **1** (C1) | 1 (C2) | **1** (S34) | 3 |
| v1 agent | 3 (C1, C2, C3) | 0 | 2 | 0 |
| **v2 agent** | **1** (C1) | 1 (C2) | **1** (S34) | 11 |

What v2 did with each attack:
- **C2:** routed on S29. On S33 the amendment is dropped (L1) and evidence is requested.
- **C3:** routes S32 to REQUEST_EVIDENCE, which is the correct answer.
- **C1** still lands on every engine: an in-place edit needs a document register.
- **C4–C7** are held throughout.

## What it shows so far

1. **Guards can be added by declaration.** The agent's spec got them from two lines of YAML, with
   no change to its logic, and on set C its unsafe targets fell from 3 to 1. The guards live in
   the document model, not in a decision type.
2. **The cost of a guard depends on how a spec uses `rely`.** v2 agent routes 11 decisions that
   should have been decided; v2 yaml routes 3. The agent's spec relies on every covering guarantee
   in every Acme decision, even where the decision never needs it (a $400k request within the
   $750k maximum). So **relying only on what the decision depends on** becomes a
   spec-quality property: a reviewable one, and one to check before admitting a spec.
3. **Lineage read from text can't be a safe default** (M1). "Names another id of its kind" covers
   both amending and superseding, so on by default it would route half the discount decisions.
   Two ways to resolve it:
   - **The safe one** (used here): any mention routes, and a person sorts it out.
   - **A supersession-aware rule:** it would let a forged "superseding" guarantee through.

   Either way, the real fix is the same as for C1: **relations between instruments (amends,
   supersedes, extends) as explicit, registered metadata**, not inferred from body text.
4. **What is left to a register:** in-place edits (C1). Plus, predicted for set D, forged
   standalone instruments that are the only one a decision relies on.

## Next

- **Set D:** the user writes it from `set-d-brief.md`. It runs against v1 and v2 with
  `run_set.py --set D`, against predictions D1–D6 in `plan.md`.

## Cost

| | Cost |
|---|---|
| Jev | No new calls (every judgment replayed from set C's recording) |
| Claude | Build only; no subagents, no reader |

## Files

| File | What it holds |
|---|---|
| `plan.md` | The pre-registration (guards, checks, predictions for set D) |
| `run_set.py` | The harness (`--set C or D`, `--check`, `--literal`, `--replay`) |
| `m1_default_on.py` | M1 |
| `set-c-results.{md,json}`, `set-c-literal-results.{md,json}` | K3, K4 |
| `set-d-brief.md` | What the user writes set D to |
| `engine-calls.jsonl` | The Jev recording, seeded from set C's |
