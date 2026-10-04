"""Experiment 6: discount and credit must behave exactly as before (verdict test (b), `plan.md`).

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-03-exp6-sla/check_behaviour.py [--replay]

- **Discount:** experiment 4's harness rows (clean, then sets A and B, on all 18 scenarios),
  compared byte for byte with `hybrid-{a,b}-v3.json`.
- **Credit:** the decision fields of S26–S35 (outcome, gated outcome, uncertain, eligibility,
  authority, approvers, flags), compared with experiment 5's `hybrid-decisions.json`.

The judgments' raw probabilities are not compared: the HR file now lists four more titles, so the
role-mapping question has more options, and its probabilities shift even when its answer doesn't.
Jev calls are recorded in this folder's `engine-calls.jsonl`, seeded from experiment 5's.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
EXP4, EXP5 = LAB / "runs/2026-10-03-adversarial", LAB / "runs/2026-10-03-exp5-credit"
CALLS = HERE / "engine-calls.jsonl"
sys.path[:0] = [str(EXP4), str(LAB / "lab/owm_kernel"), str(LAB / "lab/decision_engine")]
import credit  # noqa: E402
import discount  # noqa: E402
import run_hybrid as rh  # noqa: E402
from engine import Recorder, Replay, TypeSafe  # noqa: E402
from kernel import Evidence  # noqa: E402

from northstar.model import load_truth  # noqa: E402

FIELDS = ("outcome", "gated_outcome", "uncertain", "eligibility", "authority", "approvers", "flags")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    if not CALLS.exists():
        shutil.copy(EXP5 / "engine-calls.jsonl", CALLS)
    eng = Replay(CALLS, "jev-1.13.0") if a.replay else Recorder(TypeSafe("jev-1.13.0"), CALLS)
    truth = load_truth(LAB / "truth")
    scen = {s.id: s for s in truth.scenarios}
    v3 = rh.load("hybrid", EXP4 / "hybrid_v3.py")
    heldout = rh.load(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    exp = v3.scorer.expected()
    ok = True
    for name in ("A", "B"):
        attacks = yaml.safe_load((rh.SETS[name] / "manifest.yaml").read_text())

        def run(attack: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
            with tempfile.TemporaryDirectory(prefix="ns-behaviour-") as tmp:
                roots = rh.build(attack, rh.SETS[name], Path(tmp))  # noqa: B023
                return {sid: discount.decide(eng, Evidence(roots[scen[sid].corpus]),
                                             scen[sid].as_of, rh.record(heldout, sid), sid)
                        for sid in v3.SCENARIOS}  # fmt: skip

        clean = run(None)
        rows = [{"attack": "clean", "scenario": sid, "class": rh.classify(d, exp[sid]),
                 "outcome": d["gated_outcome"], "approver": d["authority"].get("approver"),
                 "flags": d.get("flags", [])} for sid, d in clean.items()]  # fmt: skip
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
        same = (
            json.dumps(rows, indent=1, default=str) + "\n"
            == (EXP4 / f"hybrid-{name.lower()}-v3.json").read_text()
        )
        ok &= same
        print(f"discount, set {name}: {len(rows)} rows, {'identical' if same else 'DIFFERENT'}")

    credit_run = rh.load("exp5_run_hybrid", EXP5 / "run_hybrid.py")  # its request records

    ref = json.loads((EXP5 / "hybrid-decisions.json").read_text())
    diffs = []
    for sid in credit_run.SCENARIOS:
        s = scen[sid]
        d = credit.decide(eng, Evidence(credit_run.CORPUS[s.corpus]), s.as_of,
                          credit_run.record(truth, sid), sid)  # fmt: skip
        got = json.loads(json.dumps({k: d[k] for k in FIELDS}, default=str))
        want = {k: ref[sid][k] for k in FIELDS}
        if got != want:
            diffs.append(sid)
    ok &= not diffs
    print(f"credit, S26–S35: {'identical' if not diffs else 'DIFFERENT: ' + ', '.join(diffs)}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
