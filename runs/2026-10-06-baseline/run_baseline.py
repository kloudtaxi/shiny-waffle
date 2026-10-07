"""The reader re-baseline (`plan.md`): the plain reader, the adopted procedures (G-35), and each
scenario's own request in its system of record (G-36's overlay).

    uv run python runs/2026-10-06-baseline/run_baseline.py [--reps 3] [--workers 6] [--score]

Experiment 4's 18 discount scenarios and credit S26–S35, as in set F's `pf` arm: the fixed system
prompt plus the canonical procedure, then the question (the record "as recorded in Northstar
CRM/ERP", or "as submitted" for S35) and every document of the overlaid corpus. The cost guard
stops the run if the first `--workers` calls average more than $0.45.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
OUT = HERE / "answers"
GUARD_USD = 0.45
VARIANTS = LAB / "dataset/evidence-variants"
CORPORA = {"base": LAB / "dataset/evidence",
           "missing-contract-evidence": VARIANTS / "missing-contract-evidence",
           "missing-guarantee-evidence": VARIANTS / "missing-guarantee-evidence"}  # fmt: skip
SUBMITTED = {"S35"}  # records "as submitted": the export stays as it is


def load(name: str, path: Path) -> ModuleType:
    s = importlib.util.spec_from_file_location(name, path)
    assert s and s.loader
    mod = importlib.util.module_from_spec(s)
    sys.modules[name] = mod
    s.loader.exec_module(mod)
    return mod


exp4r = load("exp4_reader", LAB / "runs/2026-10-03-adversarial/run_reader.py")
exp5r = load("exp5_reader", LAB / "runs/2026-10-03-exp5-credit/run_reader.py")
creader = load("set_c_reader", LAB / "runs/2026-10-03-exp5-credit/run_set_c_reader.py")
rh4 = load("exp4_run_hybrid", LAB / "runs/2026-10-03-adversarial/run_hybrid.py")
heldout = rh4.load("heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py")
v3 = rh4.load("hybrid", LAB / "runs/2026-10-03-adversarial/hybrid_v3.py")
x5 = load("x5_hybrid", LAB / "runs/2026-10-03-exp5-credit/run_hybrid.py")
ov = load("reader_overlay", LAB / "lab/reader_inputs/overlay.py")
from northstar.model import load_truth  # noqa: E402

SCENARIOS = list(v3.SCENARIOS) + list(x5.SCENARIOS)


def kind(sid: str) -> str:
    return "credit" if sid in x5.SCENARIOS else "discount"


def prompt(truth: Any, sid: str, tmp: Path) -> str:
    s = next(x for x in truth.scenarios if x.id == sid)
    src = CORPORA[str(s.corpus)]
    if kind(sid) == "credit":
        root = src if sid in SUBMITTED else ov.overlay(src, tmp / sid, x5.record(truth, sid),
                                                       "credit")  # fmt: skip
        return str(creader.prompt(truth, sid, root))
    rec = rh4.record(heldout, sid)
    root = ov.overlay(src, tmp / sid, rec, "discount")
    q = f"{s.question} The request, as recorded in Northstar CRM: {json.dumps(rec)}"
    return f"{q}\n\n{exp5r.evidence(root)}"


def system(sid: str) -> str:
    proc = exp5r.PROCEDURE if kind(sid) == "credit" else exp4r.PROCEDURE
    return f"{exp4r.SYSTEM_PROMPT}\n\n{proc.read_text()}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--score", action="store_true", help="score what exists; ask nothing")
    a = ap.parse_args()
    truth = load_truth(LAB / "truth")
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ns-baseline-") as tmp:
        jobs = []
        for sid in SCENARIOS:
            text, sys_prompt = prompt(truth, sid, Path(tmp)), system(sid)
            jobs += [(OUT / f"{sid}-r{r}.jsonl", text, sys_prompt) for r in range(1, a.reps + 1)]
    jobs = [j for j in jobs if not j[0].exists() and not a.score]

    def go(job: tuple[Path, str, str]) -> float:
        path, text, sys_prompt = job
        path.write_text(exp4r.ask(text, sys_prompt))
        usd = float(exp4r.result(path).get("total_cost_usd") or 0)
        print(f"{path.name}: ${usd:.3f}", flush=True)
        return usd

    with cf.ThreadPoolExecutor(a.workers) as pool:
        first = list(pool.map(go, jobs[: a.workers]))
        avg = sum(first) / len(first) if first else 0.0
        if avg > GUARD_USD:
            sys.exit(f"cost guard: the first {len(first)} calls averaged ${avg:.2f}; stopped")
        list(pool.map(go, jobs[a.workers :]))

    key = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    exp_disc = exp4r.scorer.expected()
    rows, cost = [], 0.0
    for path in sorted(OUT.glob("*.jsonl")):
        sid, rep = path.stem.split("-")
        res = exp4r.result(path)
        cost += float(res.get("total_cost_usd") or 0)
        text = str(res.get("result") or "")
        if kind(sid) == "discount":
            got = exp4r.scorer.decision(text)
            safety = str(exp4r.classify(got, exp_disc[sid]))
        else:
            got = exp5r.scorer.decision(text)
            _, s = exp5r.grade(got, key[sid])
            safety = str(creader.unsafe_type(got, s, key[sid]["decision"]["outcome"]))
        conds = [c for c in ((got or {}).get("conditions") or []) if isinstance(c, dict)]
        rows.append({"scenario": sid, "rep": rep, "answer": str(path.relative_to(LAB)),
                     "outcome": (got or {}).get("outcome"), "safety": safety,
                     "blocking": sum(bool(c.get("blocking")) for c in conds),
                     "conditions": conds})  # fmt: skip
    (HERE / "results.json").write_text(json.dumps(rows, indent=1) + "\n")
    c = Counter(r["safety"].split(":")[0] for r in rows)
    print(
        f"{len(rows)} answers, cost ${cost:.2f}; safety {dict(c)}; "
        f"with a blocking condition {sum(r['blocking'] > 0 for r in rows)}"
    )


if __name__ == "__main__":
    main()
