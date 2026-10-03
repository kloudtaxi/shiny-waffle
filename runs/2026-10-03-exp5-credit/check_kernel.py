"""Experiment 5, step 1: the kernel + discount spec must reproduce hybrid v3 byte for byte.

    uv run python runs/2026-10-03-exp5-credit/check_kernel.py

Runs experiment 4's harness logic (clean, then each attack in sets A and B, on all 18 scenarios)
with `lab/owm_kernel/discount.py` instead of `hybrid_v3.py`, from the experiment-4 recording only,
and compares the rows with `hybrid-{a,b}-v3.json`.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
EXP4 = LAB / "runs/2026-10-03-adversarial"
sys.path[:0] = [str(EXP4), str(LAB / "lab/owm_kernel")]
import discount  # noqa: E402
import run_hybrid as rh  # noqa: E402
from kernel import Evidence  # noqa: E402

from northstar.model import load_truth  # noqa: E402


def main() -> None:
    v3 = rh.load("hybrid", EXP4 / "hybrid_v3.py")  # for the engine classes and the scenario list
    heldout = rh.load(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    eng = v3.Replay(EXP4 / "engine-calls.jsonl", v3.MODEL)
    truth = load_truth(LAB / "truth")
    exp = v3.scorer.expected()
    scen = {s.id: s for s in truth.scenarios}
    ok = True
    for name in ("A", "B"):
        attacks = yaml.safe_load((rh.SETS[name] / "manifest.yaml").read_text())

        def run(attack: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
            with tempfile.TemporaryDirectory(prefix="ns-kernel-") as tmp:
                roots = rh.build(attack, rh.SETS[name], Path(tmp))  # noqa: B023
                return {sid: discount.decide(eng, Evidence(roots[scen[sid].corpus]),
                                             scen[sid].as_of, rh.record(heldout, sid), sid)
                        for sid in v3.SCENARIOS}  # fmt: skip

        clean = run(None)
        rows = []
        for sid, d in clean.items():
            rows.append({"attack": "clean", "scenario": sid, "class": rh.classify(d, exp[sid]),
                         "outcome": d["gated_outcome"],
                         "approver": d["authority"].get("approver"),
                         "flags": d.get("flags", [])})  # fmt: skip
        for at in attacks:
            for sid, d in run(at).items():
                moved = rh.key(d) != rh.key(clean[sid])
                if sid != at["target"] and not moved:
                    continue
                rows.append({"attack": at["id"], "scenario": sid, "target": sid == at["target"],
                             "class": rh.classify(d, exp[sid]), "moved": moved,
                             "outcome": d["gated_outcome"],
                             "approver": d["authority"].get("approver"),
                             "eligibility": d["commercial_eligibility"],
                             "policy": d["authority"].get("policy"),
                             "uncertain": d["uncertain"], "flags": d.get("flags", [])})  # fmt: skip
        mine = json.dumps(rows, indent=1, default=str) + "\n"
        ref = (EXP4 / f"hybrid-{name.lower()}-v3.json").read_text()
        same = mine == ref
        ok &= same
        print(f"set {name}: {len(rows)} rows, {'identical to v3' if same else 'DIFFERENT from v3'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
