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
