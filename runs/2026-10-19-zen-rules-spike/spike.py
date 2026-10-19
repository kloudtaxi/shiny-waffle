"""THROWAWAY (G-52 spike). Run everything, $0, no edits outside this folder:

    uv run --with zen-engine==2.1.3 python runs/2026-10-19-zen-rules-spike/spike.py all

Subcommands: build · checks · gate --arm base|zen · compare · all. See plan.md.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
TABLES, OUT = HERE / "tables", HERE / "outputs"
SPEC = LAB / "lab/owm_kernel/specs/credit_v3.yaml"
REGISTERS = sorted((LAB / "lab/owm_register").glob("*.yaml"))
PROTECTED = ["lab/owm_kernel/*.py", "lab/owm_kernel/specs/*.yaml", "lab/owm_register/*.yaml",
             "lab/owm_register/*.py", "lab/spec_admission/*.py"]  # fmt: skip
ZEN_VERSION = "2.1.3"

sys.path[:0] = [str(HERE), str(LAB / "lab/owm_kernel"), str(LAB / "lab/decision_engine")]
import tables as T  # noqa: E402


def protected_hashes() -> dict[str, str]:
    files = sorted({p for g in PROTECTED for p in LAB.glob(g)})
    return {str(p.relative_to(LAB)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def register_entries(path: Path) -> list[dict[str, Any]]:
    d = yaml.safe_load(path.read_text())
    return list(d.get("entries", [])) if isinstance(d, dict) else []


def key(e: dict[str, Any]) -> str:
    return f"{e['doc_id']}.v{e['version']}"


# -- build ---------------------------------------------------------------------------------------
def build() -> dict[str, Any]:
    TABLES.mkdir(exist_ok=True)
    built, sizes = {}, {}
    for e in register_entries(LAB / "lab/owm_register/base.yaml"):
        if e["kind"] in T.BUILDERS:
            jdm = T.BUILDERS[e["kind"]](e)
            text = json.dumps(jdm, indent=1, ensure_ascii=False) + "\n"
            (TABLES / f"{key(e)}.json").write_text(text)
            built[key(e)] = e["terms"]
            terms_yaml = yaml.safe_dump(e["terms"], sort_keys=False, allow_unicode=True)
            sizes[key(e)] = {"kind": e["kind"], "terms_yaml_lines": terms_yaml.count("\n"),
                             "terms_yaml_bytes": len(terms_yaml.encode()),
                             "jdm_pretty_bytes": len(text.encode()),
                             "jdm_compact_bytes": len(json.dumps(jdm, separators=(",", ":"))),
                             "rules": sum(len(n["content"].get("rules", [])) for n in jdm["nodes"]
                                          if n["type"] == "decisionTableNode")}  # fmt: skip
    same = {}
    for reg in REGISTERS:
        for e in register_entries(reg):
            if "kind" in e and key(e) in built:
                same[f"{reg.name}:{key(e)}"] = e["terms"] == built[key(e)]
    return {"tables": sorted(built), "sizes": sizes, "variant_terms_identical": same}


# -- the ZEN adapter (the RulesPort's one implementation) ---------------------------------------
class ZenRules:
    """RulesPort: evaluate(entry, context) -> (result, trace). One JDM file per register entry."""

    def __init__(self) -> None:
        import zen

        self.engine, self.cache, self.traces = zen.ZenEngine(), {}, []
        self.override: dict[str, dict[str, Any]] = {}  # P4 plants a modified table here

    def evaluate(self, entry: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        k = key(entry)
        if k in self.override:
            dec = self.engine.create_decision(json.dumps(self.override[k]))
        else:
            if k not in self.cache:
                self.cache[k] = self.engine.create_decision((TABLES / f"{k}.json").read_text())
            dec = self.cache[k]
        t0 = time.perf_counter()
        r = dec.evaluate(context, {"trace": True})
        us = (time.perf_counter() - t0) * 1e6
        rows = {}
        for node in (r.get("trace") or {}).values():
            td = node.get("traceData")
            if isinstance(td, dict) and "rule" in td:
                rows[node.get("name")] = td["rule"].get("_id")
            elif isinstance(td, list):
                rows[node.get("name")] = [x.get("rule", {}).get("_id") for x in td]
        self.traces.append({"table": f"{k}.json", "doc_id": entry["doc_id"],
                            "version": entry["version"], "context": context, "rows": rows,
                            "us": round(us, 1)})  # fmt: skip
        return r["result"]


def zen_terms_functions(kernel: Any, rules: ZenRules) -> tuple[Any, Any]:
    """Drop-in versions of kernel.authority_from_terms / concurrences_from_terms: the business
    rules come from the table; resolving people stays with the kernel."""

    def policy(out: dict[str, Any]) -> tuple[bool, Any]:
        pol = out.get("policy") or {}
        sod, passes = bool(pol.get("separation_of_duties")), pol.get("passes_to")
        if sod and passes not in T.HANDOFFS:
            raise ValueError(f"the table's hand-off {passes!r} isn't one the kernel can resolve")
        return sod, passes

    def authority(entry, staff, amount, requested_by):  # type: ignore[no-untyped-def]
        me = next(e for e in staff if e["email"].lower() == requested_by.lower())
        out = rules.evaluate(entry, {"amount": amount, "title": me["title"], "tier": None})
        need = (out.get("band") or {}).get("required_title")
        lim = out["limit"]
        sod, _ = policy(out)
        within = True if lim["unlimited"] else amount <= float(lim["limit"])
        approver = kernel.resolve_approver(staff, me, need, sod)
        return {"policy": entry["doc_id"],
                "requestor_limit": None if lim["unlimited"] else float(lim["limit"]),
                "requestor_authorized": within and not sod, "required_role": need,
                "approver": approver["full_name"] if approver else None}  # fmt: skip

    def concurrences(entry, staff, amount, tier, requested_by):  # type: ignore[no-untyped-def]
        me = next(e for e in staff if e["email"].lower() == requested_by.lower())
        out = rules.evaluate(entry, {"amount": amount, "title": me["title"], "tier": tier})
        sod, _ = policy(out)
        found = [kernel.resolve_approver(staff, me, row["title"], sod)
                 for row in (out.get("concurrence") or [])]  # fmt: skip
        return [w for w in found if w is not None]

    return authority, concurrences


# -- P2, P3, P4: checks over the tables ------------------------------------------------------------
def grid_amounts(bands: list[dict[str, Any]], extra: list[float]) -> list[float]:
    edges = {float(b[k]) for b in bands for k in ("min_exclusive", "max_inclusive")
             if b[k] is not None}  # fmt: skip
    pts = {0.0, -1.0, *extra}
    for x in edges:
        pts |= {x, x - 0.01, x + 0.01, round(x * 0.5, 4)}
    top = max(edges) if edges else 1.0
    pts |= {top * 10}
    return sorted(pts)


def checks() -> dict[str, Any]:
    import kernel

    rules = ZenRules()
    base = {key(e): e for e in register_entries(LAB / "lab/owm_register/base.yaml")
            if e.get("kind") in T.BUILDERS}  # fmt: skip
    diffs, exceptions, points = [], [], 0

    def compare(where: str, got: Any, want: Any, exception: bool = False) -> None:
        nonlocal points
        points += 1
        if got != want:
            (exceptions if exception else diffs).append({"at": where, "zen": got, "kernel": want})

    for k, e in base.items():
        t = e["terms"]
        if e["kind"] in ("credit_policy", "pricing_policy"):
            field = "amount" if e["kind"] == "credit_policy" else "discount"
            kb = [(b["title"], float(b["min_exclusive"] or 0.0),
                   None if b["max_inclusive"] is None else float(b["max_inclusive"]))
                  for b in t["bands"]]  # fmt: skip
            titles = [*dict.fromkeys(b["title"] for b in t["bands"]), "Nobody In Particular"]
            tiers = sorted({x for c in t.get("concurrence", []) for x in (c.get("tiers") or [])})
            tiers = [*tiers, "Standard", "Unknown Tier", None]
            for amt in grid_amounts(t["bands"], [float(c["min_exclusive"])
                                                  for c in t.get("concurrence", [])]):
                for title in titles:
                    for tier in (tiers if e["kind"] == "credit_policy" else [None]):
                        ctx = {field: amt, "title": title, "tier": tier}
                        out = rules.evaluate(e, ctx)
                        at = f"{k} {ctx}"
                        compare(at + " band", (out.get("band") or {}).get("required_title"),
                                next((x for x, lo, hi in kb if kernel.in_band(amt, lo, hi)), None))
                        lim = out["limit"]
                        kl = kernel.limit_for(kb, title)
                        # The table states an unlimited band as unlimited; the kernel returns 1.0.
                        # For discounts that is 100%, the same rule. For credit (dollars) it's the
                        # pre-declared exception: compared under the kernel's convention, counted.
                        zl = 1.0 if lim["unlimited"] else float(lim["limit"])
                        compare(at + " limit", zl, kl)
                        if lim["unlimited"] and e["kind"] == "credit_policy" and kl == 1.0:
                            exceptions.append({"at": at + " limit", "zen": "unlimited",
                                               "kernel": kl})
                        if e["kind"] == "credit_policy":
                            want = [c["title"] for c in t.get("concurrence", [])
                                    if amt > float(c["min_exclusive"])
                                    and (not c["tiers"] or tier in c["tiers"])]  # fmt: skip
                            compare(at + " concurrence",
                                    [r["title"] for r in out.get("concurrence") or []], want)
                        else:
                            above = t.get("approval_evidence_required_above")
                            compare(at + " evidence", (out.get("evidence") or {}).get("required"),
                                    above is not None and amt > float(above))
        else:  # sla_schedule: a direct lookup over the YAML lists
            plans = sorted({x["plan"] for x in t["targets"] if x["plan"]} | {"Gold", "Unknown"})
            for sev in (0, 1, 2, 3, 4, 5):
                for plan in [*plans, None]:
                    out = rules.evaluate(e, {"severity": sev, "plan": plan, "target": None,
                                             "band": None})  # fmt: skip
                    hit = next((x for x in t["targets"] if x["severity"] == sev
                                and (x["plan"] is None or x["plan"] == plan)), None)  # fmt: skip
                    want = None if hit is None else (hit["response_minutes"],
                                                     hit["restoration_minutes"], hit["clock"])
                    got = out.get("target")
                    got = None if not got else (got.get("response_minutes"),
                                                got.get("restoration_minutes"), got.get("clock"))
                    compare(f"{k} target sev={sev} plan={plan}", got, want)
                for tg in ("response", "restoration", "resolution"):
                    for band in (None, 1, 2, 3):
                        out = rules.evaluate(e, {"severity": sev, "plan": None, "target": tg,
                                                 "band": band})  # fmt: skip
                        hit = next((c for c in t["credits"] if c["severity"] == sev
                                    and c["target"] == tg
                                    and (c["band"] is None or c["band"] == band)), None)  # fmt: skip
                        compare(f"{k} credit sev={sev} target={tg} band={band}",
                                (out.get("credit") or {}).get("pct"),
                                None if hit is None else hit["pct"])
            out = rules.evaluate(e, {"severity": 1, "plan": None, "target": None, "band": None})
            compare(f"{k} other terms", out.get("terms"),
                    {x: t[x] for x in ("cap_pct", "claim_days", "notice_business_days")})

    # P3: registration checks, real and planted
    real = {p.name: json.loads(p.read_text()) for p in sorted(TABLES.glob("*.json"))}
    p3 = {"validate_real": {n: T.validate(j) for n, j in real.items()},
          "coverage_real": {n: T.coverage(j) for n, j in real.items() if
                            any(x["id"] == "bands" for x in j["nodes"])}}  # fmt: skip
    credit = copy.deepcopy(real["CREDIT-POLICY-2026.v1.json"])
    planted_fn = copy.deepcopy(credit)
    planted_fn["nodes"].append({"id": "fn", "type": "functionNode", "name": "Fetch",
                                "position": {"x": 0, "y": 0},
                                "content": {"source": "export const handler = async () => "
                                            "(await http.get('https://example.com')).data"}})  # fmt: skip
    p3["validate_planted_function"] = T.validate(planted_fn)
    gap, overlap = copy.deepcopy(credit), copy.deepcopy(credit)
    gnode = next(n for n in gap["nodes"] if n["id"] == "bands")
    gnode["content"]["rules"][1]["i0"] = "(150000..500000]"
    onode = next(n for n in overlap["nodes"] if n["id"] == "bands")
    onode["content"]["rules"][1]["i0"] = "(90000..500000]"
    p3["coverage_planted_gap"], p3["coverage_planted_overlap"] = T.coverage(gap), T.coverage(overlap)

    # P4: the hand-off lives in the table
    staff = list(csv.DictReader((LAB / "dataset/evidence/structured/employees.csv").open()))
    reqs = list(csv.DictReader((LAB / "dataset/evidence/structured/credit_requests.csv").open()))
    # The first pass used the first credit request's requestor, who holds no band, so separation
    # of duties couldn't change anything (notes.md). An AR Specialist holds the first band.
    first_requestor = reqs[0]["requested_by"]
    ar = next(e for e in staff if e["title"] == "Accounts Receivable Specialist")
    requested_by = ar["email"]
    authority, _ = zen_terms_functions(kernel, rules)
    entry = base["CREDIT-POLICY-2026.v1"]
    p4: dict[str, Any] = {"requestor": requested_by, "requestor_title": ar["title"],
                          "first_pass_requestor": first_requestor}
    p4["as_registered"] = authority(entry, staff, 1000.0, requested_by)
    p4["kernel_as_registered"] = kernel.authority_from_terms(entry, staff, 1000.0, requested_by)
    no_sod = copy.deepcopy(credit)
    pnode = next(n for n in no_sod["nodes"] if n["id"] == "policy")
    pnode["content"]["expressions"][0]["value"] = "false"
    rules.override = {key(entry): no_sod}
    p4["table_sod_off"] = authority(entry, staff, 1000.0, requested_by)
    bad = copy.deepcopy(credit)
    bnode = next(n for n in bad["nodes"] if n["id"] == "policy")
    bnode["content"]["expressions"][1]["value"] = '"the CFO"'
    rules.override = {key(entry): bad}
    try:
        authority(entry, staff, 1000.0, requested_by)
        p4["unsupported_handoff"] = "accepted (FAIL)"
    except ValueError as err:
        p4["unsupported_handoff"] = f"refused: {err}"
    rules.override = {}
    p4["yaml_terms_unchanged"] = entry["terms"]["separation_of_duties"] is True

    us = [t["us"] for t in rules.traces]
    return {"P2": {"points": points, "differences": diffs, "expected_exceptions": len(exceptions),
                   "exception_sample": exceptions[:3]},
            "P3": p3, "P4": p4,
            "latency_us": {"calls": len(us), "median": sorted(us)[len(us) // 2],
                           "max": max(us)}}  # fmt: skip


# -- P1: the admission gate, baseline and ZEN-backed -----------------------------------------------
def gate(arm: str) -> None:
    spec = importlib.util.spec_from_file_location("admit", LAB / "lab/spec_admission/admit.py")
    assert spec and spec.loader
    admit = importlib.util.module_from_spec(spec)
    sys.modules["admit"] = admit
    spec.loader.exec_module(admit)
    rules = None
    if arm == "zen":
        import kernel

        rules = ZenRules()
        flow = sys.modules["flow"]
        flow.authority_from_terms, flow.concurrences_from_terms = zen_terms_functions(kernel, rules)
    g = admit.Gate(admit.Layered(LAB / "runs/2026-10-06-spec-admission/jev-calls.jsonl",
                                 live=False, cap=0), "outcome")  # fmt: skip
    report = g.run(SPEC, "credit")
    OUT.mkdir(exist_ok=True)
    (OUT / f"gate-{arm}.json").write_text(json.dumps(
        {"arm": arm, "live_jev": g.eng.live_calls, "report": report}, indent=1, default=str) + "\n")
    if rules is not None:
        (OUT / "traces.jsonl").write_text("".join(json.dumps(t) + "\n" for t in rules.traces))
    print(f"gate {arm}: A {report['A']['held']}/{report['A']['of']} · B "
          f"{len(report['B']['unsafe_or_error'])} unsafe/error in {report['B']['attacks']} · C "
          f"{len(report['C']['idle'])} idle · live {g.eng.live_calls}"
          + (f" · {len(rules.traces)} ZEN calls" if rules else ""))


def compare() -> dict[str, Any]:
    a = json.loads((OUT / "gate-base.json").read_text())
    b = json.loads((OUT / "gate-zen.json").read_text())
    same = a["report"] == b["report"]
    diff = []
    if not same:
        def walk(x: Any, y: Any, path: str) -> None:
            if isinstance(x, dict) and isinstance(y, dict):
                for k in sorted(set(x) | set(y)):
                    walk(x.get(k), y.get(k), f"{path}.{k}")
            elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
                for i, (p, q) in enumerate(zip(x, y, strict=True)):
                    walk(p, q, f"{path}[{i}]")
            elif x != y:
                diff.append({"at": path, "base": x, "zen": y})
        walk(a["report"], b["report"], "report")
    traces = [json.loads(x) for x in (OUT / "traces.jsonl").read_text().splitlines()]
    return {"identical": same, "live_jev": [a["live_jev"], b["live_jev"]],
            "differences": diff[:20], "zen_calls": len(traces),
            "trace_sample": traces[:2]}  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "checks", "gate", "compare", "all"])
    ap.add_argument("--arm", choices=["base", "zen"])
    a = ap.parse_args()
    if a.cmd == "gate":
        gate(a.arm)
        return
    if a.cmd == "build":
        print(json.dumps(build(), indent=1))
        return
    if a.cmd == "checks":
        print(json.dumps(checks(), indent=1, default=str))
        return
    if a.cmd == "compare":
        print(json.dumps(compare(), indent=1, default=str))
        return
    before = protected_hashes()
    import zen  # noqa: F401  (fail early if the engine isn't there)
    import importlib.metadata as md

    res: dict[str, Any] = {"zen_engine": md.version("zen-engine"), "build": build()}
    for arm in ("base", "zen"):
        subprocess.run([sys.executable, __file__, "gate", "--arm", arm], check=True)
    res["P1"] = compare()
    res.update(checks())
    after = protected_hashes()
    res["guards"] = {"protected_files": len(before), "unchanged": before == after,
                     "zen_expected": md.version("zen-engine") == ZEN_VERSION}  # fmt: skip
    OUT.mkdir(exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    p3 = res["P3"]
    print(json.dumps({
        "P1_identical": res["P1"]["identical"], "P1_live": res["P1"]["live_jev"],
        "P2_points": res["P2"]["points"], "P2_differences": len(res["P2"]["differences"]),
        "P2_expected_exceptions": res["P2"]["expected_exceptions"],
        "P3_real_clean": not any(p3["validate_real"].values()) and not any(
            p3["coverage_real"].values()),
        "P3_planted": [bool(p3["validate_planted_function"]), bool(p3["coverage_planted_gap"]),
                       bool(p3["coverage_planted_overlap"])],
        "P4": res["P4"], "latency_us": res["latency_us"], "guards": res["guards"],
    }, indent=1, default=str))


if __name__ == "__main__":
    main()
