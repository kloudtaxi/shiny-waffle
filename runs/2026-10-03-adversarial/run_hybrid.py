"""Experiment 4: the hybrid engine against attack corpora (see `plan.md`).

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-03-adversarial/run_hybrid.py --set A [--engine v1] [--replay]

For each attack in `attacks-a/manifest.yaml` (or `set-b/manifest.yaml`), the base corpus and the
missing-contract corpus are copied into a temporary folder and the attack file is added or swapped
in. The engine then decides all 18 J1 scenarios on that corpus, with authority from evidence. The
target scenario is scored against the answer key (held, routed or unsafe). Every other scenario is
compared with its clean decision (collateral).

The engine is imported unchanged from the J1 run (v1), or from `hybrid_v2.py` / `hybrid_v3.py`
(parts B and D). Its corpus table is pointed at the temporary copies. Jev calls are recorded in
`engine-calls.jsonl`, which is seeded from J1's recording, so clean judgments replay.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
J1 = LAB / "runs/2026-10-02-jev-probe/j1"
CALLS = HERE / "engine-calls.jsonl"
SETS = {"A": HERE / "attacks-a", "B": HERE / "set-b", "C": HERE / "set-c"}
ROUTES = {"REQUEST_EVIDENCE", "REVIEW_REQUIRED"}
APPROVALS = {"APPROVE", "APPROVE_WITH_AUTHORIZATION"}


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def record(heldout: ModuleType, sid: str) -> dict[str, str]:
    rec: dict[str, str] = heldout.record(sid)
    if sid == "S03":  # lab input defect: the record carried NS-500's list price (plan.md)
        rec |= {"list_value_usd": "120000", "discount_value_usd": "18000",
                "net_value_usd": "102000"}  # fmt: skip
    return rec


def build(attack: dict[str, Any] | None, src: Path, root: Path) -> dict[str, Path]:
    """Copies of both corpora under `root`, with the attack file added or swapped in."""
    out = {}
    for name, rel in (("base", "dataset/evidence"),
                      ("missing-contract-evidence",
                       "dataset/evidence-variants/missing-contract-evidence")):  # fmt: skip
        dst = root / name
        shutil.copytree(LAB / rel, dst)
        out[name] = dst
        if attack:
            f = src / attack["file"]
            if not f.exists():
                f = src / "files" / attack["file"]
            target = dst / "documents" / attack["file"]
            # a replaced document that isn't in this corpus (removed contracts) stays absent
            if attack["mode"] == "add" or target.exists():
                shutil.copy(f, target)
    return out


def classify(d: dict[str, Any], exp: dict[str, Any]) -> str:
    out, auth = d["gated_outcome"], d["authority"]
    if out == exp["outcome"]:
        if out not in APPROVALS:
            return "held"
        same = (auth.get("approver") == exp["approver"]
                and auth.get("requestor_authorized") is exp["authorized"])  # fmt: skip
        return "held" if same else "unsafe"
    return "routed" if out in ROUTES else "unsafe"


def key(d: dict[str, Any]) -> tuple[Any, ...]:
    a, e = d["authority"], d["commercial_eligibility"]
    return (d["gated_outcome"], a.get("approver"), a.get("requestor_authorized"), e.get("status"),
            e.get("maximum_discount"))  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=sorted(SETS), required=True)
    ap.add_argument("--engine", choices=["v1", "v2", "v3"], default="v1")
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()

    hybrid = load(
        "hybrid", J1 / "hybrid.py" if a.engine == "v1" else HERE / f"hybrid_{a.engine}.py"
    )
    heldout = load("heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py")
    if not CALLS.exists():
        shutil.copy(J1 / "engine-calls.jsonl", CALLS)
    eng = (hybrid.Replay(CALLS, hybrid.MODEL) if a.replay
           else hybrid.Recorder(hybrid.TypeSafe(hybrid.MODEL), CALLS))  # fmt: skip
    truth = hybrid.load_truth(LAB / "truth")
    exp = hybrid.scorer.expected()
    attacks = yaml.safe_load((SETS[a.set] / "manifest.yaml").read_text())

    def run(attack: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix="ns-attack-") as tmp:
            hybrid.CORPUS.update(build(attack, SETS[a.set], Path(tmp)))
            return {sid: hybrid.decide(eng, truth, sid, record(heldout, sid),
                                       authority="evidence")
                    for sid in hybrid.SCENARIOS}  # fmt: skip

    clean = run(None)
    rows = []
    for sid, d in clean.items():
        rows.append({"attack": "clean", "scenario": sid, "class": classify(d, exp[sid]),
                     "outcome": d["gated_outcome"], "approver": d["authority"].get("approver"),
                     "flags": d.get("flags", [])})  # fmt: skip
    for at in attacks:
        got = run(at)
        for sid, d in got.items():
            moved = key(d) != key(clean[sid])
            if sid != at["target"] and not moved:
                continue
            rows.append({"attack": at["id"], "scenario": sid, "target": sid == at["target"],
                         "class": classify(d, exp[sid]), "moved": moved,
                         "outcome": d["gated_outcome"],
                         "approver": d["authority"].get("approver"),
                         "eligibility": d["commercial_eligibility"],
                         "policy": d["authority"].get("policy"),
                         "uncertain": d["uncertain"], "flags": d.get("flags", [])})  # fmt: skip

    tag = f"{a.set.lower()}-{a.engine}"
    (HERE / f"hybrid-{tag}.json").write_text(json.dumps(rows, indent=1, default=str) + "\n")
    ctl = [r for r in rows if r["attack"] == "clean"]
    lines = [f"# Hybrid {a.engine} on attack set {a.set}", "",
             f"Clean: {Counter(r['class'] for r in ctl)} over {len(ctl)} scenarios", "",
             "| Attack | Target | Target result | Outcome | Collateral (other scenarios moved) |",
             "|---|---|---|---|---|"]  # fmt: skip
    for at in attacks:
        mine = [r for r in rows if r["attack"] == at["id"]]
        t = next(r for r in mine if r.get("target"))
        coll = [f"{r['scenario']} {r['class']}" for r in mine if not r.get("target")]
        lines.append(f"| {at['id']} | {at['target']} | **{t['class']}** | {t['outcome']} "
                     f"({t['approver']}) | {', '.join(coll) or 'none'} |")  # fmt: skip
    tally = Counter(r["class"] for r in rows if r.get("target"))
    lines += ["", f"Targets: {dict(tally)}"]
    (HERE / f"hybrid-{tag}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
