"""Specs as data, phase 1: the YAML specs must decide exactly as the Python specs did.

    uv run python runs/2026-10-04-specs-as-data/check_equivalence.py [credit] [discount] [sla]

- **discount:** experiment 4's harness rows (clean, then sets A and B), byte for byte against
  `hybrid-{a,b}-v3.json`.
- **credit:** S26–S35 decision fields against experiment 5's `hybrid-decisions.json`.
- **sla:** S36–S45 decision fields against experiment 6's `hybrid-decisions.json`.

It replays experiment 6's Jev recording, so no new calls are made. An identical question gets an
identical answer.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
RUNS = LAB / "runs"
sys.path[:0] = [str(LAB / "lab/owm_kernel"), str(LAB / "lab/decision_engine")]
import flow  # noqa: E402
from engine import Replay  # noqa: E402
from kernel import Evidence  # noqa: E402

from northstar.model import load_truth  # noqa: E402

SPECS = LAB / "lab/owm_kernel/specs"


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def plain(x: Any) -> Any:
    return json.loads(json.dumps(x, default=str))


def credit(eng: Any, truth: Any) -> bool:
    spec = flow.load(SPECS / "credit.yaml")
    exp5 = load("exp5_run_hybrid", RUNS / "2026-10-03-exp5-credit/run_hybrid.py")
    ref = json.loads((RUNS / "2026-10-03-exp5-credit/hybrid-decisions.json").read_text())
    fields = ("outcome", "gated_outcome", "uncertain", "eligibility", "authority", "approvers",
              "flags")  # fmt: skip
    bad = []
    for sid in exp5.SCENARIOS:
        s = next(x for x in truth.scenarios if x.id == sid)
        d = flow.run(spec, eng, Evidence(exp5.CORPUS[s.corpus]),
                     {"sid": sid, "record": exp5.record(truth, sid), "as_of": s.as_of})  # fmt: skip
        if plain({k: d[k] for k in fields}) != {k: ref[sid][k] for k in fields}:
            bad.append(sid)
            print(sid, json.dumps(plain({k: d[k] for k in fields}))[:600])
            print("  ref", json.dumps({k: ref[sid][k] for k in fields})[:600])
    print(f"credit, S26–S35: {'identical' if not bad else 'DIFFERENT: ' + ', '.join(bad)}")
    return not bad


def discount(eng: Any, truth: Any) -> bool:
    spec = flow.load(SPECS / "discount.yaml")
    exp4 = RUNS / "2026-10-03-adversarial"
    rh = load("exp4_run_hybrid", exp4 / "run_hybrid.py")
    v3 = rh.load("hybrid", exp4 / "hybrid_v3.py")
    heldout = rh.load(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    exp = v3.scorer.expected()
    scen = {s.id: s for s in truth.scenarios}
    ok = True
    for name in ("A", "B"):
        attacks = yaml.safe_load((rh.SETS[name] / "manifest.yaml").read_text())

        def run(attack: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
            with tempfile.TemporaryDirectory(prefix="ns-data-") as tmp:
                roots = rh.build(attack, rh.SETS[name], Path(tmp))  # noqa: B023
                return {sid: flow.run(spec, eng, Evidence(roots[scen[sid].corpus]),
                                      {"sid": sid, "record": rh.record(heldout, sid),
                                       "as_of": scen[sid].as_of})
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
        mine = json.dumps(rows, indent=1, default=str) + "\n"
        same = mine == (exp4 / f"hybrid-{name.lower()}-v3.json").read_text()
        if not same:
            ref = json.loads((exp4 / f"hybrid-{name.lower()}-v3.json").read_text())
            for a, b in zip(json.loads(mine), ref, strict=False):
                if a != b:
                    print("  mine", a)
                    print("  ref ", b)
                    break
        ok &= same
        print(f"discount, set {name}: {len(rows)} rows, {'identical' if same else 'DIFFERENT'}")
    return ok


def sla(eng: Any, truth: Any) -> bool:
    spec = flow.load(SPECS / "sla.yaml")
    ref = json.loads((RUNS / "2026-10-03-exp6-sla/hybrid-decisions.json").read_text())
    fields = ("outcome", "gated_outcome", "uncertain", "scope", "severity", "breach",
              "credit_usd", "obligations", "account_owner", "flags")  # fmt: skip
    bad = []
    for sid in [f"S{n}" for n in range(36, 46)]:
        s = next(x for x in truth.scenarios if x.id == sid)
        d = flow.run(spec, eng, Evidence(LAB / "dataset/evidence"),
                     {"sid": sid, "ticket_id": s.ticket, "decided_at": s.decided_at})  # fmt: skip
        got, want = plain({k: d[k] for k in fields}), {k: ref[sid][k] for k in fields}
        if got != want:
            bad.append(sid)
            for k in fields:
                if got[k] != want[k]:
                    print(f"  {sid} {k}: data {got[k]!r}")
                    print(f"  {sid} {k}: code {want[k]!r}")
    print(f"sla, S36–S45: {'identical' if not bad else 'DIFFERENT: ' + ', '.join(bad)}")
    return not bad


def main() -> None:
    which = sys.argv[1:] or ["credit", "discount", "sla"]
    eng = Replay(RUNS / "2026-10-03-exp6-sla/engine-calls.jsonl", "jev-1.13.0")
    truth = load_truth(LAB / "truth")
    ok = True
    for name in which:
        ok &= globals()[name](eng, truth)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
