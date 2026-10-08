"""G-37: title priors (`plan.md`). Variant T moves the 10-20% discount band from "VP Sales" to a
new "Commercial Policy Lead" (Dana Okafor, reporting to the CRO); Michael Torres keeps the VP Sales
title with no discount authority.

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-08-title-priors/run_titles.py check     # the transform, no spend
    uv run python runs/2026-10-08-title-priors/run_titles.py engine
    uv run python runs/2026-10-08-title-priors/run_titles.py ask [--arms r-full r-slice]
    uv run python runs/2026-10-08-title-priors/run_titles.py score

The variant is rebuilt deterministically in a temporary directory by every step; `truth/` and
`dataset/` are untouched.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import copy
import csv
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
OUT = HERE / "answers"
CALLS = HERE / "jev-calls.jsonl"
OLD_T, NEW_T = "VP Sales", "Commercial Policy Lead"
NEW_NAME = "Dana Okafor"
NEW_EMP = {"employee_id": "EMP-310", "full_name": NEW_NAME, "preferred_name": "",
           "title": NEW_T, "department": "Revenue Operations", "manager_id": "EMP-300",
           "email": "dana.okafor@northstar.example", "location": "Chicago, IL"}  # fmt: skip
# every occurrence of "VP Sales" in these files is the discount band (checked by `check`)
POLICY_FILES = {"pricing_policy_2025.md": 1, "pricing_policy_2026.md": 1,
                "pricing_policy_2027.md": 1, "approval_authority_matrix.md": 1}  # fmt: skip
ORG_ANCHOR = "- **David Morgan** — Chief Revenue Officer\n"
ORG_LINE = f"  - **{NEW_NAME}** — {NEW_T} (Revenue Operations)\n"
MICHAEL_REQUESTS = {"S12", "S15", "S20"}
CORPORA = ("base", "missing-contract-evidence")
GUARD = {"r-full": 0.45, "r-slice": 0.20}


def load(name: str, path: Path) -> ModuleType:
    s = importlib.util.spec_from_file_location(name, path)
    assert s and s.loader
    mod = importlib.util.module_from_spec(s)
    sys.modules[name] = mod
    s.loader.exec_module(mod)
    return mod


rc = load("run_cost", LAB / "runs/2026-10-08-cost-per-decision/run_cost.py")
bl = rc.bl
sys.path[:0] = [str(LAB / "lab/owm_kernel"), str(LAB / "lab/owm_register")]
from kernel import Register, fingerprint  # noqa: E402

REG_DIR = LAB / "lab/owm_register"


# -- the variant ----------------------------------------------------------------------------------
def build_corpus(src: Path, dst: Path) -> Path:
    shutil.copytree(src, dst)
    docs = dst / "documents"
    for name, n in POLICY_FILES.items():
        p = docs / name
        if not p.exists():
            continue
        text = p.read_text()
        assert text.count(OLD_T) == n, f"{name}: {text.count(OLD_T)} occurrences of {OLD_T!r}"
        p.write_text(text.replace(OLD_T, NEW_T))
    org = docs / "organization_chart.md"
    text = org.read_text()
    assert text.count(ORG_ANCHOR) == 1
    org.write_text(text.replace(ORG_ANCHOR, ORG_ANCHOR + ORG_LINE))
    emp = dst / "structured/employees.csv"
    with emp.open() as f:
        r = csv.DictReader(f)
        fields, rows = list(r.fieldnames or []), list(r)
    rows.append(dict(NEW_EMP))
    with emp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return dst


def build_register(corpus: str, out: Path) -> Path:
    """The variant register: pricing policies' titles, fingerprints and approved texts follow
    the transformed documents."""
    entries = copy.deepcopy(yaml.safe_load((REG_DIR / f"{corpus}.yaml").read_text())["entries"])
    (out / "store").mkdir(parents=True, exist_ok=True)
    for e in entries:
        text = (REG_DIR / "store" / f"{e['sha256']}.md").read_text()
        if e["kind"] == "pricing_policy":
            assert text.count(OLD_T) == 1, e["doc_id"]
            text = text.replace(OLD_T, NEW_T)
            e["sha256"] = fingerprint(text)
            for b in e["terms"]["bands"]:
                if b["title"] == OLD_T:
                    b["title"] = NEW_T
        (out / "store" / f"{e['sha256']}.md").write_text(text)
    (out / f"{corpus}.yaml").write_text(yaml.safe_dump({"entries": entries}, sort_keys=False))
    return out


def build(tmp: Path) -> tuple[dict[str, Path], Path]:
    roots = {c: build_corpus(bl.CORPORA[c], tmp / "corpus" / c) for c in CORPORA}
    for c in CORPORA:
        build_register(c, tmp / "register")
    return roots, tmp / "register"


def expected() -> dict[str, dict[str, Any]]:
    """The variant's expectations, mechanically from the base key (`plan.md`)."""
    out = {}
    for sid, e in bl.exp4r.scorer.expected().items():
        e = dict(e)
        if e["required_role"] == OLD_T:
            e["required_role"], e["approver"] = NEW_T, NEW_NAME
        if sid in MICHAEL_REQUESTS:
            e["authorized"] = False
            if e["outcome"] == "APPROVE":
                e["outcome"] = "APPROVE_WITH_AUTHORIZATION"
        out[sid] = e
    return out


def check() -> None:
    with tempfile.TemporaryDirectory(prefix="ns-g37-") as tmp:
        roots, reg = build(Path(tmp))
        for c, r in roots.items():
            emp = (r / "structured/employees.csv").read_text()
            assert NEW_NAME in emp and emp.count("VP Sales") == 1
            print(c, "ok:", sum((r / "documents" / f).exists() for f in POLICY_FILES), "files")
        for c in CORPORA:
            e = yaml.safe_load((reg / f"{c}.yaml").read_text())["entries"]
            titles = [
                b["title"] for x in e if x["kind"] == "pricing_policy" for b in x["terms"]["bands"]
            ]
            assert OLD_T not in titles and NEW_T in titles
            print(c, "register ok:", sorted(set(titles)))
    exp = expected()
    changed = {s: exp[s] for s in exp if exp[s] != bl.exp4r.scorer.expected()[s]}
    print(f"{len(changed)} expectations changed:", ", ".join(sorted(changed)))


# -- arms -----------------------------------------------------------------------------------------
def engine() -> None:
    admit = load("admit", LAB / "lab/spec_admission/admit.py")
    import governed

    gate = admit.Gate(admit.Layered(CALLS, live=True, cap=500))
    exp, rows = expected(), []
    with tempfile.TemporaryDirectory(prefix="ns-g37-") as tmp:
        roots, reg = build(Path(tmp))
        regs = {c: Register.load(reg / f"{c}.yaml") for c in CORPORA}
        for sid in gate.scenarios("discount"):
            c = gate.corpus("discount", sid)
            inp = gate.inputs("discount", sid)
            try:
                d = admit.ra.plain(governed.decide("discount", gate.eng, admit.Evidence(roots[c]),
                                                   inp, inp["as_of"], regs[c]))  # fmt: skip
            except Exception as e:  # noqa: BLE001
                d = {"gated_outcome": "ERROR", "error": str(e)[:200]}
            cls = str(admit.rh.classify(d, exp[sid]))
            a = d.get("authority") or {}
            rows.append({"scenario": sid, "class": cls, "outcome": d.get("gated_outcome"),
                         "approver": a.get("approver"), "authorized": a.get("requestor_authorized"),
                         "expected": exp[sid]})  # fmt: skip
            print(
                sid, cls, d.get("gated_outcome"), a.get("approver"), a.get("requestor_authorized")
            )
    c = Counter(r["class"] for r in rows)
    summary = {"classes": dict(c), "live_jev_calls": gate.eng.live_calls, "rows": rows}
    (HERE / "engine.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(dict(c), "live Jev calls:", gate.eng.live_calls)


def prompts(arm: str, tmp: Path) -> list[tuple[str, str, str]]:
    from northstar.model import load_truth

    truth = load_truth(LAB / "truth")
    roots, reg = build(tmp)
    out = []
    orig = rc.sl.serve.served
    rc.sl.serve.served = lambda corpus, decision: orig(corpus, decision, root=reg)
    try:
        for sid in bl.v3.SCENARIOS:
            s = next(x for x in truth.scenarios if x.id == sid)
            rec = bl.rh4.record(bl.heldout, sid)
            root = bl.ov.overlay(roots[str(s.corpus)], tmp / "ov" / sid, rec, "discount")
            q = f"{s.question} The request, as recorded in Northstar CRM: {json.dumps(rec)}"
            ctx = (rc.sl.served_slice("discount", str(s.corpus), root, rec)
                   if arm == "r-slice" else bl.exp5r.evidence(root))  # fmt: skip
            out.append((sid, f"{q}\n\n{ctx}", bl.system(sid)))
    finally:
        rc.sl.serve.served = orig
    return out


def ask(arms: list[str], reps: int, workers: int) -> None:
    for arm in arms:
        (OUT / arm).mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="ns-g37-") as tmp:
            ps = prompts(arm, Path(tmp))
        todo = [(OUT / arm / f"{sid}-r{r}.jsonl", text, sysp) for sid, text, sysp in ps
                for r in range(1, reps + 1)]  # fmt: skip
        todo = [j for j in todo if not j[0].exists()]

        def go(job: tuple[Path, str, str], arm: str = arm) -> float:
            path, text, sysp = job
            path.write_text(rc.ask(rc.MODELS["o"], text, sysp))
            usd = float(bl.exp4r.result(path).get("total_cost_usd") or 0)
            print(f"{arm} {path.name}: ${usd:.3f}", flush=True)
            return usd

        with cf.ThreadPoolExecutor(workers) as pool:
            first = list(pool.map(go, todo[:workers]))
            avg = sum(first) / len(first) if first else 0.0
            if avg > GUARD[arm]:
                sys.exit(f"cost guard ({arm}): first {len(first)} averaged ${avg:.3f}")
            list(pool.map(go, todo[workers:]))


def score() -> None:
    exp = expected()
    res: dict[str, Any] = {}
    for arm in ("r-full", "r-slice"):
        rows, cost = [], 0.0
        for p in sorted((OUT / arm).glob("S*-r*.jsonl")):
            sid, rep = p.stem.split("-")
            r = bl.exp4r.result(p)
            cost += float(r.get("total_cost_usd") or 0)
            got = bl.exp4r.scorer.decision(str(r.get("result") or ""))
            cls = str(bl.exp4r.classify(got, exp[sid]))
            appr = str(((got or {}).get("authority") or {}).get("approver") or "")
            rows.append({"scenario": sid, "rep": rep, "class": cls,
                         "outcome": (got or {}).get("outcome"), "approver": appr,
                         "names_michael_for_dana": exp[sid]["approver"] == NEW_NAME
                         and "michael" in appr.lower()})  # fmt: skip
        c = Counter(x["class"].split(":")[0] for x in rows)
        unsafe = [f"{x['scenario']} {x['rep']}" for x in rows if x["class"].startswith("unsafe")]
        res[arm] = {"n": len(rows), "classes": dict(c), "unsafe": unsafe,
                    "unsafe_on_michael_requests": sum(u.split()[0] in MICHAEL_REQUESTS
                                                      for u in unsafe),
                    "names_michael_for_dana": sum(x["names_michael_for_dana"] for x in rows),
                    "usd": round(cost, 2), "rows": rows}  # fmt: skip
        print(arm, {k: v for k, v in res[arm].items() if k != "rows"})
    (HERE / "results.json").write_text(json.dumps(res, indent=1) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["check", "engine", "ask", "score"])
    ap.add_argument("--arms", nargs="+", default=list(GUARD))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.step == "check":
        check()
    elif a.step == "engine":
        engine()
    elif a.step == "ask":
        ask(a.arms, a.reps, a.workers)
    else:
        score()


if __name__ == "__main__":
    main()
