"""M1 (`plan.md`): what would change if lineage were on by default for every graded kind?

    uv run python runs/2026-10-05-instrument-guards/m1_default_on.py [--counts-only]

1. Runs specs as data's equivalence check (`check_equivalence.py`, on replay) with each spec's
   `documents.lineage_kinds` set to its `graded` kinds: discount clean plus sets A and B, credit
   S26–S35, SLA S36–S45. "identical" means default-on lineage changes nothing there; for a
   difference, the first differing row is printed.
2. Lists every clean discount decision (J1's 18 scenarios) that default-on changes.

`--counts-only` skips step 1. Measured, not predicted.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[2]
HELDOUT = LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
_spec = importlib.util.spec_from_file_location(
    "check_equivalence", LAB / "runs/2026-10-04-specs-as-data/check_equivalence.py"
)
assert _spec and _spec.loader
ce = importlib.util.module_from_spec(_spec)
sys.modules["check_equivalence"] = ce
_spec.loader.exec_module(ce)
from engine import Replay  # noqa: E402

from northstar.model import load_truth  # noqa: E402

_load = ce.flow.load


def default_on(path: Path) -> dict[str, Any]:
    s: dict[str, Any] = _load(path)
    s["documents"]["lineage_kinds"] = list(s["documents"].get("graded", []))
    return s


def discount_clean() -> None:
    eng = Replay(ce.RUNS / "2026-10-03-exp6-sla/engine-calls.jsonl", "jev-1.13.0")
    truth = load_truth(LAB / "truth")
    exp4 = ce.RUNS / "2026-10-03-adversarial"
    rh = ce.load("exp4_run_hybrid", exp4 / "run_hybrid.py")
    v3 = rh.load("hybrid", exp4 / "hybrid_v3.py")
    heldout = rh.load("heldout", HELDOUT)
    exp, scen = v3.scorer.expected(), {s.id: s for s in truth.scenarios}
    off, on = _load(ce.SPECS / "discount.yaml"), default_on(ce.SPECS / "discount.yaml")
    changed = 0
    with tempfile.TemporaryDirectory(prefix="ns-m1-") as tmp:
        roots = rh.build(None, rh.SETS["A"], Path(tmp))
        for sid in v3.SCENARIOS:
            inputs = {"sid": sid, "record": rh.record(heldout, sid), "as_of": scen[sid].as_of}
            ev = ce.Evidence(roots[scen[sid].corpus])
            a, b = ce.flow.run(off, eng, ev, inputs), ce.flow.run(on, eng, ev, inputs)
            ca, cb = rh.classify(a, exp[sid]), rh.classify(b, exp[sid])
            if (a["gated_outcome"], ca) != (b["gated_outcome"], cb):
                changed += 1
                print(f"  {sid}: {a['gated_outcome']} ({ca}) -> {b['gated_outcome']} ({cb}); "
                      f"{b['flags'][-1]}")  # fmt: skip
    print(f"discount clean: {changed}/{len(v3.SCENARIOS)} decisions change with default-on")


def main() -> None:
    counts_only = "--counts-only" in sys.argv
    if not counts_only:
        ce.flow.load = default_on
        sys.argv = sys.argv[:1]
        try:
            ce.main()  # exits non-zero when anything differs
        except SystemExit:
            pass
        ce.flow.load = _load
    discount_clean()


if __name__ == "__main__":
    main()
