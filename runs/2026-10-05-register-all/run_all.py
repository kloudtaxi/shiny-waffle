"""G-30: one register for credit, discount and SLA (`plan.md`).

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-05-register-all/run_all.py [--replay]

Engines:
- discount (`specs/discount.yaml`, frozen), plus **discount+R** (route) and **discount+Ru** (the
  default, proceed on the approved version). Each adds one declaration: the `registered_kinds`
  mapping onto the register's kinds;
- sla (`specs/sla.yaml`, frozen), plus **sla+R** and **sla+Ru**, likewise.

Every register-backed engine gets its company's register (`lab/owm_register/<corpus>.yaml`).

The run:
- **K3:** clean decisions with and without the register, every decision field. Discount uses
  experiment 4's 18 scenarios (base and missing-contract corpora); SLA uses S36–S45;
- **K5:** the same with every registered document re-saved (CRLF line endings, trailing spaces);
- **attacks:** experiment 4's sets A and B through the three discount engines, classed and with
  side effects reported as in experiment 4.

Jev calls are recorded in this folder's `engine-calls.jsonl`, seeded from experiment 6's.
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
CALLS = HERE / "engine-calls.jsonl"


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ce = load("check_equivalence", LAB / "runs/2026-10-04-specs-as-data/check_equivalence.py")
flow, Evidence, plain = ce.flow, ce.Evidence, ce.plain
from engine import Recorder, Replay, TypeSafe  # noqa: E402
from kernel import Register  # noqa: E402

from northstar.model import load_truth  # noqa: E402

CORPORA = ("base", "missing-contract-evidence", "missing-guarantee-evidence")
REG = {c: Register.load(LAB / "lab/owm_register" / f"{c}.yaml") for c in CORPORA}
DISCOUNT = {"policy": "pricing_policy", "agreement": "agreement", "amendment": "amendment",
            "exception": "exception"}  # fmt: skip
SLA = {"schedule": "sla_schedule", "guide": "severity_guide", "procedure": "escalation_procedure",
       "calendar": "holiday_calendar", "terms": "support_terms"}  # fmt: skip
SLA_FIELDS = ("outcome", "gated_outcome", "uncertain", "scope", "severity", "breach",
              "credit_usd", "obligations", "account_owner")  # fmt: skip
DISC_FIELDS = ("outcome", "gated_outcome", "commercial_eligibility", "authority")


def specs(file: str, mapping: dict[str, str]) -> dict[str, tuple[dict[str, Any], bool]]:
    name = file.split(".")[0]
    out = {}
    for tag, patch, reg in (("", {}, False),
                            ("+R", {"registered_kinds": mapping, "on_mismatch": "route"}, True),
                            ("+Ru", {"registered_kinds": mapping}, True)):  # fmt: skip
        s = flow.load(ce.SPECS / file)
        s["documents"].update(patch)
        out[name + tag] = (s, reg)
    return out


def resave(root: Path) -> None:
    """K5: every document re-saved as an editor might (CRLF, trailing spaces); same words."""
    for corpus in root.iterdir():
        for p in (corpus / "documents").glob("*.md"):
            p.write_bytes(("  \r\n".join(p.read_text().split("\n")) + "\r\n").encode())


def safe_run(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """K5 feeds engines malformed text, so an engine may fail; that is recorded as an outcome."""
    try:
        return dict(flow.run(*args, **kwargs))
    except Exception as e:  # noqa: BLE001
        return {
            "outcome": "ERROR",
            "gated_outcome": "ERROR",
            "error": f"{type(e).__name__}: {e}"[:200],
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    if not CALLS.exists():
        shutil.copy(LAB / "runs/2026-10-03-exp6-sla/engine-calls.jsonl", CALLS)
    eng = Replay(CALLS, "jev-1.13.0") if a.replay else Recorder(TypeSafe("jev-1.13.0"), CALLS)
    truth = load_truth(LAB / "truth")
    scen = {s.id: s for s in truth.scenarios}
    exp4 = ce.RUNS / "2026-10-03-adversarial"
    rh = ce.load("exp4_run_hybrid", exp4 / "run_hybrid.py")
    v3 = rh.load("hybrid", exp4 / "hybrid_v3.py")
    heldout = rh.load(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    exp = v3.scorer.expected()
    disc = specs("discount.yaml", DISCOUNT)
    sla = specs("sla.yaml", SLA)
    report: list[str] = ["# One register for all three decision types (G-30)", ""]
    ok = True

    def run_discount(attack: dict[str, Any] | None, src: Path | None, saved: bool = False
                     ) -> dict[str, dict[str, dict[str, Any]]]:  # fmt: skip
        with tempfile.TemporaryDirectory(prefix="ns-g30-") as tmp:
            roots = rh.build(attack, src, Path(tmp))
            if saved:
                resave(Path(tmp))
            return {name: {sid: safe_run(spec, eng, Evidence(roots[scen[sid].corpus]),
                                         {"sid": sid, "record": rh.record(heldout, sid),
                                          "as_of": scen[sid].as_of},
                                         register=REG[scen[sid].corpus] if reg else None)
                           for sid in v3.SCENARIOS}
                    for name, (spec, reg) in disc.items()}  # fmt: skip

    def run_sla(saved: bool = False) -> dict[str, dict[str, dict[str, Any]]]:
        with tempfile.TemporaryDirectory(prefix="ns-g30-sla-") as tmp:
            root = Path(tmp) / "base"
            shutil.copytree(LAB / "dataset/evidence", root)
            if saved:
                resave(Path(tmp))
            return {name: {sid: plain(safe_run(spec, eng, Evidence(root),
                                               {"sid": sid, "ticket_id": scen[sid].ticket,
                                                "decided_at": scen[sid].decided_at},
                                               register=REG["base"] if reg else None))
                           for sid in [f"S{n}" for n in range(36, 46)]}
                    for name, (spec, reg) in sla.items()}  # fmt: skip

    # K3 and K5
    for label, runner, fields in (
        ("discount", run_discount, DISC_FIELDS),
        ("sla", run_sla, SLA_FIELDS),
    ):
        clean = runner(None, None) if label == "discount" else runner()
        saved = runner(None, None, saved=True) if label == "discount" else runner(saved=True)
        base = clean[label]
        report += [f"## {label}: clean (K3) and re-saved (K5)", "",
                   "| Engine | Clean: matches the frozen spec | Re-saved: decisions changed |",
                   "|---|---|---|"]  # fmt: skip

        def differs(x: dict[str, Any], y: dict[str, Any]) -> bool:
            return any(plain(x).get(k) != plain(y).get(k) for k in fields)  # noqa: B023

        for name in clean:
            diff = [sid for sid in base if differs(clean[name][sid], base[sid])]
            moved = [sid for sid in base if differs(saved[name][sid], clean[name][sid])]
            report.append(f"| {name} | {len(base) - len(diff)}/{len(base)} {diff or ''} | "
                          f"{len(moved)}/{len(base)} {moved or ''} |")  # fmt: skip
            ok &= not diff
            if name.endswith("+Ru"):
                ok &= not moved
        report.append("")

    # experiment 4's attack sets A and B on discount
    for set_name in ("A", "B"):
        attacks = yaml.safe_load((rh.SETS[set_name] / "manifest.yaml").read_text())
        clean = run_discount(None, None)
        rows = []
        for at in attacks:
            got = run_discount(at, rh.SETS[set_name])
            for name, ds in got.items():
                for sid, d in ds.items():
                    moved = rh.key(d) != rh.key(clean[name][sid])
                    if sid != at["target"] and not moved:
                        continue
                    rows.append({"attack": at["id"], "engine": name, "scenario": sid,
                                 "target": sid == at["target"], "class": rh.classify(d, exp[sid]),
                                 "outcome": d["gated_outcome"],
                                 "flags": d.get("flags", [])})  # fmt: skip
        (HERE / f"set-{set_name.lower()}-results.json").write_text(
            json.dumps(rows, indent=1, default=str) + "\n"
        )
        report += [f"## Experiment 4's set {set_name} on discount", "",
                   "| Attack | Target | discount | discount+R | discount+Ru |",
                   "|---|---|---|---|---|"]  # fmt: skip
        for at in attacks:
            cells = [next(r["class"] for r in rows if r["attack"] == at["id"] and r["engine"] == n
                          and r["target"]) for n in disc]  # fmt: skip
            report.append(f"| {at['id']} | {at['target']} | " + " | ".join(cells) + " |")
        report += ["", "| Engine | Targets unsafe | routed | Collateral unsafe | "
                   "Collateral routed |", "|---|---|---|---|---|"]  # fmt: skip
        for n in disc:
            mine = [r for r in rows if r["engine"] == n]
            t = Counter(r["class"] for r in mine if r["target"])
            c = Counter(r["class"] for r in mine if not r["target"])
            report.append(
                f"| {n} | {t['unsafe']} | {t['routed']} | {c['unsafe']} | {c['routed']} |"
            )
            if n != "discount":
                ok &= t["unsafe"] == 0 and c["unsafe"] == 0
        report.append("")
    report.append(f"**All pre-registered checks: {'pass' if ok else 'FAIL'}**")
    (HERE / "results.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
