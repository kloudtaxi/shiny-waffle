"""M1 (`plan.md`): what would change if lineage were on by default for every graded kind?

    uv run python runs/2026-10-05-instrument-guards/m1_default_on.py

Runs specs as data's equivalence check (`check_equivalence.py`, on replay) with each spec's
`documents.lineage_kinds` set to its `graded` kinds. That covers discount clean plus sets A and B,
credit S26–S35, and SLA S36–S45. A difference is printed per decision; "identical" means default-on
lineage changes nothing there. Measured, not predicted.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "check_equivalence", LAB / "runs/2026-10-04-specs-as-data/check_equivalence.py"
)
assert spec and spec.loader
ce = importlib.util.module_from_spec(spec)
sys.modules["check_equivalence"] = ce
spec.loader.exec_module(ce)
_load = ce.flow.load


def default_on(path: Path) -> dict[str, Any]:
    s = _load(path)
    s["documents"]["lineage_kinds"] = list(s["documents"].get("graded", []))
    print(f"{path.name}: lineage_kinds = {s['documents']['lineage_kinds']}")
    return s


ce.flow.load = default_on
counts_only = "--counts-only" in sys.argv
sys.argv = sys.argv[:1] + (["--counts-only"] if counts_only else [])
ce.main() if "--counts-only" not in sys.argv else None


def discount_clean() -> None:
    """The discount clean decisions (J1's 18 scenarios), lineage off against default-on."""
    import tempfile

    from engine import Replay  # type: ignore[import-not-found]

    from northstar.model import load_truth

    eng = Replay(ce.RUNS / "2026-10-03-exp6-sla/engine-calls.jsonl", "jev-1.13.0")
    truth = load_truth(LAB / "truth")
    exp4 = ce.RUNS / "2026-10-03-adversarial"
    rh = ce.load("exp4_run_hybrid", exp4 / "run_hybrid.py")
    v3 = rh.load("hybrid", exp4 / "hybrid_v3.py")
    heldout = rh.load("heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py")
    exp, scen = v3.scorer.expected(), {s.id: s for s in truth.scenarios}
    off, on = _load(ce.SPECS / "discount.yaml"), default_on(ce.SPECS / "discount.yaml")
    with tempfile.TemporaryDirectory(prefix="ns-m1-") as tmp:
        roots = rh.build(None, rh.SETS["A"], Path(tmp))
        for sid in v3.SCENARIOS:
            args = (eng, ce.Evidence(roots[scen[sid].corpus]),
                    {"sid": sid, "record": rh.record(heldout, sid), "as_of": scen[sid].as_of})
            a, b = ce.flow.run(off, *args), ce.flow.run(on, *args)
            if (a["gated_outcome"], rh.classify(a, exp[sid])) != (b["gated_outcome"], rh.classify(b, exp[sid])):
                print(f"  {sid}: {a['gated_outcome']} ({rh.classify(a, exp[sid])}) -> "
                      f"{b['gated_outcome']} ({rh.classify(b, exp[sid])}); {b['flags'][-1]}")


print("discount clean, default-on against off:")
discount_clean()
