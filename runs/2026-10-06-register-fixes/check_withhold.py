"""The G-32 addendum's check: a forced route withholds its findings (`plan.md`, addendum).

    uv run python runs/2026-10-06-register-fixes/check_withhold.py

Every set is re-run by replay through its committed harness, unedited. Outputs are redirected to
`withhold/`. One scoring rule is added by wrapping each family's classifier: a decision carrying a
`withheld:` flag counts as **routed**. Then:
- **P-32c:** route-mode engines have 0 unsafe on every set, side effects included;
- **P-32d:** every forced route carries a `withheld:` flag and states no finding;
- **P-32e:** default-mode and frozen engines reproduce their committed rows; credit K3 and K4 pass.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
OUT = HERE / "withhold"
ROUTE = {"v2+R yaml", "v2+R agent", "v3", "discount+R", "sla+R",
         "credit v2+R yaml", "credit v2+R agent", "credit v3"}  # fmt: skip
FORCED = "set aside (on_mismatch: route)"


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


setf = load("run_set_f", LAB / "runs/2026-10-05-register-all/run_set_f.py")
ra, rs = setf.ra, setf.rs  # run_all.py (discount sets A, B; K3, K5) and the credit harness


def withheld(d: dict[str, Any]) -> bool:
    return any(str(f).startswith("withheld:") for f in d.get("flags") or [])


def routed_if_withheld(fn: Any) -> Any:
    def classify(d: dict[str, Any], exp: dict[str, Any]) -> str:
        return "routed" if withheld(d) else str(fn(d, exp))

    return classify


setf.sla_class = routed_if_withheld(setf.sla_class)
rs.setc.classify = routed_if_withheld(rs.setc.classify)
_load = ra.ce.load


def load_patched(name: str, path: Path) -> Any:  # experiment 4's harness is reloaded per call
    mod = _load(name, path)
    if name == "exp4_run_hybrid":
        mod.classify = routed_if_withheld(mod.classify)
    return mod


ra.ce.load = load_patched


def rows(path: Path) -> list[dict[str, Any]]:
    d = json.loads(path.read_text())
    return list(d["rows"] if isinstance(d, dict) else d)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for mod in (setf, ra, rs):
        mod.HERE = OUT
    log: list[str] = []
    for mod, argv in ((rs, ["--check", "--replay"]), (rs, ["--set", "C", "--replay"]),
                      (rs, ["--set", "D", "--replay"]), (rs, ["--set", "E", "--replay"]),
                      (ra, ["--replay"]), (setf, ["--replay"])):  # fmt: skip
        sys.argv = [mod.__name__, *argv]
        try:
            mod.main()
            log.append(f"{mod.__name__} {' '.join(argv)}: ran")
        except SystemExit as e:
            log.append(f"{mod.__name__} {' '.join(argv)}: EXIT {e.code}")

    key = {r["scenario"]: (r.get("decision") or {}).get("outcome") for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    reg, rall = LAB / "runs/2026-10-05-register", LAB / "runs/2026-10-05-register-all"
    sets = {  # name: (now, committed before G-32, the G-32 run)
        "credit C": ("set-c-results.json", reg / "set-c-results-proceed-default.json",
                     HERE / "credit-set-c.json"),
        "credit D": ("set-d-results.json", reg / "set-d-results-proceed-default.json",
                     HERE / "credit-set-d.json"),
        "credit E": ("set-e-results.json", reg / "set-e-results-proceed-default.json",
                     HERE / "credit-set-e.json"),
        "discount A": ("set-a-results.json", rall / "set-a-results.json",
                       HERE / "discount-sla-set-a-results.json"),
        "discount B": ("set-b-results.json", rall / "set-b-results.json",
                       HERE / "discount-sla-set-b-results.json"),
        "set F": ("set-f-results.json", rall / "set-f-results.json", HERE / "set-f.json"),
    }  # fmt: skip
    lines = ["# G-32 addendum: a forced route withholds its findings (check)", "",
             *(f"- {x}" for x in log), "",
             "| Set | Route-mode unsafe | Routed | Forced routes | Withheld | "
             "Re-scored by the rule | Default/frozen reproduce | Other route rows unchanged |",
             "|---|---|---|---|---|---|---|---|"]  # fmt: skip
    ok = all(x.endswith("ran") for x in log)
    for name, (now_f, old_f, g32_f) in sets.items():
        now, old, g32 = rows(OUT / now_f), rows(old_f), rows(g32_f)
        mine = [r for r in now if r["engine"] in ROUTE]
        unsafe = [r for r in mine if str(r["class"]).startswith("unsafe")]
        forced = [r for r in mine if any(FORCED in str(f) for f in r.get("flags") or [])]
        held_back = [r for r in forced if withheld(r)]
        rescored = [
            r
            for r in held_back
            if (r.get("gated_outcome") or r.get("outcome")) == key[r["scenario"]]
        ]

        def pick(rs_: list[dict[str, Any]], route: bool) -> set[tuple[Any, ...]]:
            return {(r["attack"], r["engine"], r["scenario"], r["class"],
                     r.get("gated_outcome") or r.get("outcome"))
                    for r in rs_ if (r["engine"] in ROUTE) == route}  # fmt: skip

        same = pick(now, False) == pick(old, False)
        plain_now = {(r["attack"], r["engine"], r["scenario"], r["class"]) for r in mine
                     if not withheld(r)}  # fmt: skip
        plain_g32 = {(r["attack"], r["engine"], r["scenario"], r["class"]) for r in g32
                     if r["engine"] in ROUTE and not any(FORCED in str(f)
                                                        for f in r.get("flags") or [])}  # fmt: skip
        unchanged = plain_now == plain_g32
        ok &= not unsafe and len(held_back) == len(forced) and same and unchanged
        bad = [(r["attack"], r["engine"], r["scenario"]) for r in unsafe]
        lines.append(f"| {name} | {len(unsafe)} {bad or ''} | "
                     f"{sum(r['class'] == 'routed' for r in mine)} | {len(forced)} | "
                     f"{len(held_back)} | {len(rescored)} "
                     f"{sorted({(r['engine'], r['scenario']) for r in rescored}) or ''} | "
                     f"{same} | {unchanged} |")  # fmt: skip

    # P-32d in full, on the records themselves: F9 on S45 (sla+R), and one forced route per family
    probe: list[str] = []
    attacks = {a["id"]: a for a in yaml.safe_load((setf.SET / "manifest.yaml").read_text())}
    eng = setf.Replay(setf.CALLS, "jev-1.13.0")
    truth = setf.load_truth(LAB / "truth")
    s45 = next(x for x in truth.scenarios if x.id == "S45")
    sla = ra.specs("sla.yaml", ra.SLA)
    with tempfile.TemporaryDirectory() as tmp:
        roots = setf.build(attacks["F9"], Path(tmp))
        spec, _ = sla["sla+R"]
        d = dict(ra.plain(ra.flow.run(spec, eng, ra.Evidence(roots["base"]),
                                      {"sid": "S45", "ticket_id": s45.ticket,
                                       "decided_at": s45.decided_at}, ra.REG["base"])))  # fmt: skip
        found = {k: d[k] for k in ("outcome", "gated_outcome", "scope", "severity", "breach",
                                   "credit_usd", "obligations", "account_owner")}  # fmt: skip
        empty = all(found[k] in (None, {}, []) for k in found if k != "gated_outcome")
        ok &= empty and withheld(d)
        probe += [
            f"- F9 → S45, sla+R: {found}",
            f"  - flags: {d['flags']}",
            f"  - **states no finding: {empty}**",
        ]
    for name in ("credit C", "credit D"):
        for r in rows(OUT / sets[name][0]):
            if r["engine"] == "v3" and any(FORCED in str(f) for f in r.get("flags") or []):
                f = {k: r.get(k) for k in ("outcome", "eligibility", "authority", "approvers",
                                          "registered")}  # fmt: skip
                empty = all(v in (None, {}, []) for v in f.values())
                ok &= empty
                probe.append(
                    f"- {name} {r['attack']} → {r['scenario']}, v3: {f}; "
                    f"**states no finding: {empty}**"
                )
                break
    lines += [
        "",
        "## P-32d: the records",
        "",
        *probe,
        "",
        f"**All addendum predictions: {'hold' if ok else 'DO NOT HOLD'}**",
    ]
    (HERE / "withhold-check.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
