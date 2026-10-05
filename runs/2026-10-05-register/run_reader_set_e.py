"""Set E: the Opus reader with and without the OWM register (`set-e-plan.md`, reader arms).

    uv run python runs/2026-10-05-register/run_reader_set_e.py [--workers 6] [--score]

Arms, each on the 7 set-E targets, 3 runs each:
- **re**: the plain reader;
- **rre**: the reader plus the register extract.

It is the same reader, prompt and register extract as `run_reader.py` (rc0/rr0/rr), which this
reuses. Attacked corpora are built as for the engines. Graded with experiment 5's reader
`grade()`. The cost guard: if the first `--workers` calls average more than $0.45, the run stops.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from types import ModuleType

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
OUT = HERE / "reader"
SET, SUMS = HERE / "set-e", HERE / "set-e.sha256"


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


base = load("register_reader", HERE / "run_reader.py")
reader, creader, guards = base.reader, base.creader, base.guards

from northstar.model import load_truth  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--score", action="store_true", help="score what exists; ask nothing")
    ap.add_argument(
        "--coverage-check",
        action="store_true",
        help="arm rre2 (extract v2): E3 x3, clean S33 and S28 (set-e-plan addendum)",
    )
    a = ap.parse_args()
    if a.coverage_check:
        return coverage_check(a.workers)
    guards.check_seal(SET, SUMS)
    truth = load_truth(LAB / "truth")
    scen = {s.id: s for s in truth.scenarios}
    exp = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    system_prompt = f"{reader.exp4.SYSTEM_PROMPT}\n\n{reader.PROCEDURE.read_text()}"
    for arm in ("re", "rre"):
        (OUT / arm).mkdir(parents=True, exist_ok=True)
    attacks = yaml.safe_load((SET / "manifest.yaml").read_text())

    with tempfile.TemporaryDirectory(prefix="ns-set-e-reader-") as tmp:
        jobs = []
        for at in attacks:
            corp = guards.build(at, SET, Path(tmp) / at["id"], False)
            sid, c = at["target"], scen[at["target"]].corpus
            for arm, reg in (("re", False), ("rre", True)):
                text = base.prompt(truth, sid, corp[c], c, reg)
                jobs += [(OUT / arm / f"{at['id']}-{sid}-r{r}.jsonl", text) for r in (1, 2, 3)]
        jobs = [j for j in jobs if not j[0].exists() and not a.score]

        def go(job: tuple[Path, str]) -> float:
            path, text = job
            path.write_text(reader.exp4.ask(text, system_prompt))
            usd = float(reader.exp4.result(path).get("total_cost_usd") or 0)
            print(f"{path.parent.name}/{path.name}: ${usd:.3f}", flush=True)
            return usd

        with cf.ThreadPoolExecutor(a.workers) as pool:
            first = list(pool.map(go, jobs[: a.workers]))
            avg = sum(first) / len(first) if first else 0.0
            if avg > base.GUARD_USD:
                sys.exit(f"cost guard: the first {len(first)} calls averaged ${avg:.2f}; stopped")
            list(pool.map(go, jobs[a.workers :]))

    rows, cost = [], defaultdict(float)
    for arm in ("re", "rre"):
        for path in sorted((OUT / arm).glob("E*.jsonl")):
            aid, sid, rep = path.stem.split("-")
            res = reader.exp4.result(path)
            cost[arm] += float(res.get("total_cost_usd") or 0)
            got = reader.scorer.decision(str(res.get("result") or ""))
            g, safety = reader.grade(got, exp[sid])
            rows.append({"arm": arm, "attack": aid, "scenario": sid, "rep": rep, "grade": g,
                         "safety": creader.unsafe_type(got, safety,
                                                       exp[sid]["decision"]["outcome"]),
                         "outcome": (got or {}).get("outcome")})  # fmt: skip
    by = defaultdict(list)
    for r in rows:
        by[(r["arm"], r["attack"], r["scenario"])].append(r)
    lines = ["# Set E: the reader with and without the OWM register", "",
             "| Arm | Attack | Target | Expected | Safety | Outcomes |",
             "|---|---|---|---|---|---|"]  # fmt: skip
    for (arm, aid, sid), rs in by.items():
        lines.append(f"| {arm} | {aid} | {sid} | {exp[sid]['decision']['outcome']} | "
                     f"{dict(Counter(r['safety'] for r in rs))} | "
                     f"{', '.join(str(r['outcome']) for r in rs)} |")  # fmt: skip
    lines.append("")
    for arm in ("re", "rre"):
        mine = [r for r in rows if r["arm"] == arm]
        unsafe = [r for r in mine if r["safety"].startswith("unsafe")]
        hit = len({r["attack"] for r in unsafe})
        lines.append(f"- **{arm}**: unsafe {len(unsafe)}/{len(mine)} runs, on {hit}/7 targets; "
                     f"cost ${cost[arm]:.2f}")  # fmt: skip
    (HERE / "reader-set-e-results.json").write_text(json.dumps(rows, indent=1) + "\n")
    (HERE / "reader-set-e-results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def coverage_check(workers: int) -> None:
    """The set-E addendum's check (not evidence): extract v2 states the register's coverage."""
    guards.check_seal(SET, SUMS)
    truth = load_truth(LAB / "truth")
    scen = {s.id: s for s in truth.scenarios}
    exp = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    system_prompt = f"{reader.exp4.SYSTEM_PROMPT}\n\n{reader.PROCEDURE.read_text()}"
    (OUT / "rre2").mkdir(parents=True, exist_ok=True)
    e3 = next(at for at in yaml.safe_load((SET / "manifest.yaml").read_text()) if at["id"] == "E3")
    with tempfile.TemporaryDirectory(prefix="ns-rre2-") as tmp:
        att = guards.build(e3, SET, Path(tmp) / "E3", False)
        clean = guards.build(None, None, Path(tmp) / "clean", False)
        jobs = [(OUT / "rre2" / f"E3-S33-r{r}.jsonl", att, "S33") for r in (1, 2, 3)]
        jobs += [(OUT / "rre2" / f"clean-{sid}-r1.jsonl", clean, sid) for sid in ("S33", "S28")]
        jobs = [(p, base.prompt(truth, sid, corp[scen[sid].corpus], scen[sid].corpus, True,
                                coverage=True))
                for p, corp, sid in jobs if not p.exists()]  # fmt: skip
        with cf.ThreadPoolExecutor(workers) as pool:
            list(pool.map(lambda j: j[0].write_text(reader.exp4.ask(j[1], system_prompt)), jobs))
    for path in sorted((OUT / "rre2").glob("*.jsonl")):
        aid, sid, _ = path.stem.split("-")
        res = reader.exp4.result(path)
        got = reader.scorer.decision(str(res.get("result") or ""))
        g, safety = reader.grade(got, exp[sid])
        print(f"rre2 {path.stem}: {(got or {}).get('outcome')} "
              f"({creader.unsafe_type(got, safety, exp[sid]['decision']['outcome'])}, {g}) "
              f"${float(res.get('total_cost_usd') or 0):.3f}")  # fmt: skip


if __name__ == "__main__":
    main()
