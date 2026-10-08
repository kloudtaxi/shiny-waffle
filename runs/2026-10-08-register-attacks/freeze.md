# Freeze (plan step 3)

The registrar (`lab/owm_register/registrar.py`), the kernel's `revoked_on` (`in_window`) and the
served register's revocation line are frozen at this commit. They are not changed again before the
attack set's results are committed.

**Self-check:** `check_registrar.py`, 20/20 as expected. That's 3 legitimate changes admitted
(with their in-force effects) and 15 single-rule violations each refused by its rule. These cases
were written by the lab, so they only prove that each rule works as written.

**P5 regression, before any attack exists:**
- `build_register.py --check`: up to date. `build_procedures.py --check`: up to date.
- G-32's `check_withhold.py`, which replays all six attack sets plus set F: all predictions hold,
  and its committed outputs are byte-identical.
- `check_equivalence.py`: credit S26–S35, discount sets A and B, and SLA S36–S45 are identical.
- G-13's `run_governed.py`: P1–P5 hold, and `results.json` is byte-identical.
- pytest: 40 passed. ruff check and format: clean. mypy (strict): clean.

## Post-freeze fix (before the attack set existed or was opened)

**What the smoke test showed.** `run_attacks.py` was smoke-tested on two throwaway cases (in the
scratchpad, not `sealed/`): a legitimate revocation of EXC-ACME-NS500-15 from 2026-09-15, and an
agent revoking it. The legitimate revocation was admitted but **moved no decision**:
- `revoked_on` was honoured only where a procedure reads registered terms through
  `entry_in_force` / `in_window` (credit, SLA).
- The discount procedure reads documents through the register screen, which ignored revocation.
- So the published rule RR-12 ("a revoked entry isn't in force from its revocation date") didn't
  hold on the discount path.

**The fix.**
- `Register.as_of(date)` drops entries revoked on or before the date.
- `governed.decide` reads the register as of the decision's date, so a revoked document stops
  counting for screening as well as for terms.
- The registrar is unchanged.
- After the fix, the smoke revocation moves S01, S02, S20 and S21 to REVIEW_REQUIRED (the 15%
  exception set aside), and the agent's revocation is refused (RR-2).

**P5 re-run after the fix:** everything above holds again. `check_withhold.py`'s predictions all
hold, with byte-identical outputs. `check_equivalence.py`: identical. `run_governed.py`: P1–P5
hold, with byte-identical results. Self-check: 20/20. Both `--check`s: up to date. pytest: 40.
ruff and mypy: clean.

This was found and fixed before any attack case was read. It's disclosed here because it changed
engine-visible behaviour after the freeze commit.
