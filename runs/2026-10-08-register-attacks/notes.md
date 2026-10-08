# Attacks on the register (2026-10-08)

> **Status: waiting for the user's attack set** (the user's call, 2026-10-08; it first read
> "parked", which the user corrected). The controls are built, frozen and regression-clean. The
> blind subagent asked to write the sealed attack set wrote nothing: a safety classifier stopped
> one of its responses, and it didn't retry. The lab won't reword the request to get around that.
> **The user writes the attack set**, as for sets C–F, from `sealed/BRIEF.md`.

## What exists

- **`plan.md`** (pre-registration, fedc303): the threat model, rules RR-1 to RR-14, the clock
  (2026-09-01), the order, measures M1–M4, and predictions P1–P5.
- **`lab/owm_register/registrar.py`**: the document registrar, frozen at 167575d.
  - It governs every change after the bootstrap import: register and revoke.
  - Its controls are authentication, employees only, the owning function, approval by the head or
    an Executive (never the submitter), terms and window bound to the text (including "text ⊆
    terms" for authority lines), scope (customer ids resolved against the systems of record), no
    backdating, no silent overlap, valid supersession, revocation, stale base (races), and
    relation types.
- **The kernel:**
  - `in_window` honours `revoked_on`;
  - `Register.as_of` and `governed.decide` make a revoked document stop counting on every decision
    path. This was a post-freeze fix found by a smoke test before any case existed; it's disclosed
    in `freeze.md` (11d1cf8).
- **The served register** shows a revocation.
- **`check_registrar.py`**: the lab's self-check, 20/20. It covers 3 legitimate changes with their
  in-force effects and 15 single-rule violations, each refused by its rule. Written by the lab, it
  proves only that the rules work as written.
- **P5 regression**, before and after the fix: every committed harness output is byte-identical:
  - `check_withhold.py` (all six sets and set F);
  - `check_equivalence.py`;
  - `run_governed.py`;
  - both `--check`s;
  - pytest, ruff and mypy.
- **`run_attacks.py`**: the runner. `run` is blind (it applies cases, then decides every affected
  scenario through the changed register at the outcome level); `score` runs after unsealing.
  Smoke-tested on two throwaway cases outside `sealed/`.
- **`sealed/FORMAT.md`**: the case format.

## What the build already showed (without attacks)

1. **The bootstrap register enforced nothing.** `registered_by` and `approved_by` were recorded
   but never checked. G-01's decisions now exist as code.
2. **Revocation needs to reach every decision path,** not just procedures that read registered
   terms. A revoked pricing exception kept applying to discount decisions until
   `governed.decide` read the register as of the decision's date.
3. **The lab's HR export has no Legal, Deal Desk, RevOps or People staff.** The ownership map
   assigns those kinds to the functions that use them. A real deployment needs real owners.

## To resume

1. The user writes about 24 cases (at least 8 of them legitimate changes) into `sealed/cases/`,
   following `sealed/FORMAT.md`, plus a sealed `sealed/descriptions.md` with one row per case:
   ID, legit or attack, class, intent, the rule expected to stop it, and the harm if admitted.
   The threat classes and rules are in `plan.md`.
2. Run `run_attacks.py run` (labels unread), and commit.
3. Then `run_attacks.py score`, and write up the notes.

**Cost so far:** none. The smoke test used only recorded Jev answers.
