"""Set F: the user's attacks across discount, credit and SLA, on every engine (`set-f-plan.md`).

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-05-register-all/run_set_f.py [--replay]

Each attack is added to, or swapped into, every corpus (base, missing-contract, missing-guarantee).
Every engine then decides every scenario of its type:

| Family | Engines | Scenarios |
|---|---|---|
| Discount | discount, discount+R, discount+Ru (`run_all.py`) | experiment 4's 18 |
| Credit | the register harness's eleven (`runs/2026-10-05-register/run_set.py`) | S26–S35 |
| SLA | sla, sla+R, sla+Ru (`run_all.py`) | S36–S45 |

**Scoring:**
- **discount:** experiment 4's classifier;
- **credit:** set C's classifier;
- **SLA:** held when the gated outcome, the credit and every Northstar obligation match the key
  (experiment 6's comparison); routed when CANNOT_DECIDE where the key differs; otherwise unsafe;
- an engine that fails outright is recorded as **error**.

Every scenario that moves from its clean decision is reported as a side effect, whatever its type.
"""

from __future__ import annotations

import argparse
import hashlib
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
SET, SUMS = HERE / "set-f", HERE / "set-f.sha256"
CALLS = HERE / "set-f-engine-calls.jsonl"
VARIANTS = "dataset/evidence-variants"
CORPORA = {"base": "dataset/evidence",
           "missing-contract-evidence": f"{VARIANTS}/missing-contract-evidence",
           "missing-guarantee-evidence": f"{VARIANTS}/missing-guarantee-evidence"}  # fmt: skip


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ra = load("register_all", HERE / "run_all.py")  # specs(), REG, safe_run, flow, Evidence, plain
rs = load("register_run_set", LAB / "runs/2026-10-05-register/run_set.py")  # credit engines
x6 = load("exp6_run_hybrid", LAB / "runs/2026-10-03-exp6-sla/run_hybrid.py")  # SLA compare()
from engine import Recorder, Replay, TypeSafe  # noqa: E402

from northstar.model import load_truth  # noqa: E402

SLA_IDS = [f"S{n}" for n in range(36, 46)]


def check_seal() -> None:
    for line in SUMS.read_text().splitlines():
        digest, rel = line.split(maxsplit=1)
        if hashlib.sha256((SET / rel).read_bytes()).hexdigest() != digest:
            sys.exit(f"set F changed since it was sealed: {rel}")


def build(attack: dict[str, Any] | None, root: Path) -> dict[str, Path]:
    out = {}
    for name, rel in CORPORA.items():
        dst = root / name
        shutil.copytree(LAB / rel, dst)
        out[name] = dst
        if attack:
            target = dst / "documents" / attack["file"]
            if attack["mode"] == "replace" and not target.exists():
                if name == "base":
                    sys.exit(f"{attack['id']}: nothing to replace at {target.name}")
                continue
            shutil.copy(SET / "files" / attack["file"], target)
    return out


def sla_class(d: dict[str, Any], key: dict[str, Any]) -> str:
    out = d.get("gated_outcome")
    if out == "ERROR":
        return "error"
    if out == key["decision"]["outcome"]:
        c = x6.compare(d, key)
        ok = c["credit"] and c["northstar_obligations"] and c["response"] and c["restoration"]
        return "held" if ok else "unsafe: wrong credit or obligations"
    return "routed" if out == "CANNOT_DECIDE" else "unsafe: wrong finding"


def sla_key(d: dict[str, Any]) -> tuple[Any, ...]:
    obl = sorted(json.dumps(o, sort_keys=True, default=str) for o in d.get("obligations") or [])
    return (d.get("gated_outcome"), d.get("credit_usd"), tuple(obl))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    check_seal()
    if not CALLS.exists():  # seed with both recordings, so clean judgments replay
        seen: set[str] = set()
        with CALLS.open("w") as f:
            for seed in (
                HERE / "engine-calls.jsonl",
                LAB / "runs/2026-10-05-register/engine-calls.jsonl",
            ):
                for line in seed.read_text().splitlines():
                    if (h := json.loads(line)["hash"]) not in seen:
                        seen.add(h)
                        f.write(line + "\n")
    eng = Replay(CALLS, "jev-1.13.0") if a.replay else Recorder(TypeSafe("jev-1.13.0"), CALLS)
    truth = load_truth(LAB / "truth")
    scen = {s.id: s for s in truth.scenarios}
    key = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    exp4 = ra.ce.RUNS / "2026-10-03-adversarial"
    rh = ra.ce.load("exp4_run_hybrid", exp4 / "run_hybrid.py")
    v3 = rh.load("hybrid", exp4 / "hybrid_v3.py")
    heldout = rh.load(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    exp_disc = v3.scorer.expected()
    disc, sla = ra.specs("discount.yaml", ra.DISCOUNT), ra.specs("sla.yaml", ra.SLA)
    credit = rs.engines(eng)

    def guarded(fn: Any, *args: Any) -> dict[str, Any]:
        try:
            return dict(ra.plain(fn(*args)))
        except Exception as e:  # noqa: BLE001
            return {
                "outcome": "ERROR",
                "gated_outcome": "ERROR",
                "error": f"{type(e).__name__}: {e}"[:200],
            }

    def run(attack: dict[str, Any] | None) -> dict[str, dict[str, dict[str, Any]]]:
        with tempfile.TemporaryDirectory(prefix="ns-set-f-") as tmp:
            roots = build(attack, Path(tmp))
            out: dict[str, dict[str, dict[str, Any]]] = {}
            for name, (spec, reg) in disc.items():
                ev = lambda sid: ra.Evidence(roots[scen[sid].corpus])  # noqa: E731
                out[name] = {sid: guarded(ra.flow.run, spec, eng, ev(sid),
                                          {"sid": sid, "record": rh.record(heldout, sid),
                                           "as_of": scen[sid].as_of},
                                          ra.REG[scen[sid].corpus] if reg else None)
                             for sid in v3.SCENARIOS}  # fmt: skip
            for name, fn in credit.items():
                out["credit " + name] = {
                    sid: guarded(fn, ra.Evidence(roots[scen[sid].corpus]), scen[sid].corpus,
                                 scen[sid].as_of, rs.x5.record(truth, sid), sid)
                    for sid in rs.x5.SCENARIOS}  # fmt: skip
            for name, (spec, reg) in sla.items():
                out[name] = {sid: guarded(ra.flow.run, spec, eng, ra.Evidence(roots["base"]),
                                          {"sid": sid, "ticket_id": scen[sid].ticket,
                                           "decided_at": scen[sid].decided_at},
                                          ra.REG["base"] if reg else None)
                             for sid in SLA_IDS}  # fmt: skip
            return out

    def classify(engine: str, sid: str, d: dict[str, Any]) -> str:
        if d.get("gated_outcome") == "ERROR":
            return "error"
        if engine.startswith("discount"):
            return str(rh.classify(d, exp_disc[sid]))
        if engine.startswith("credit"):
            return str(rs.setc.classify(d, key[sid]))
        return sla_class(d, key[sid])

    def kkey(engine: str, d: dict[str, Any]) -> Any:
        if d.get("gated_outcome") == "ERROR":
            return ("ERROR",)
        if engine.startswith("discount"):
            return rh.key(d)
        if engine.startswith("credit"):
            return rs.setc.key(d)
        return sla_key(d)

    clean = run(None)
    bad = [(n, sid, classify(n, sid, d)) for n, ds in clean.items() for sid, d in ds.items()
           if classify(n, sid, d) != "held" and not n.startswith("credit v1")]  # fmt: skip
    print("clean, not held (outside credit v1):", bad or "none")
    attacks = yaml.safe_load((SET / "manifest.yaml").read_text())
    rows = []
    for at in attacks:
        got = run(at)
        for name, ds in got.items():
            for sid, d in ds.items():
                moved = kkey(name, d) != kkey(name, clean[name][sid])
                if sid != at["target"] and not moved:
                    continue
                rows.append({"attack": at["id"], "engine": name, "scenario": sid,
                             "target": sid == at["target"], "class": classify(name, sid, d),
                             "gated_outcome": d.get("gated_outcome"), "error": d.get("error"),
                             "flags": d.get("flags")})  # fmt: skip
    (HERE / "set-f-results.json").write_text(json.dumps(rows, indent=1, default=str) + "\n")
    lines = ["# Set F: every engine", "",
             "| Attack | Target | Engine | Target result | "
             "Side effects (unsafe / routed / error) |",
             "|---|---|---|---|---|"]  # fmt: skip
    for at in attacks:
        for name in clean:
            t = next((r for r in rows if r["attack"] == at["id"] and r["engine"] == name
                      and r["target"]), None)  # fmt: skip
            if t is None:
                continue
            side = Counter(r["class"].split(":")[0] for r in rows if r["attack"] == at["id"]
                           and r["engine"] == name and not r["target"])  # fmt: skip
            lines.append(f"| {at['id']} | {at['target']} | {name} | **{t['class']}** | "
                         f"{side['unsafe']} / {side['routed']} / {side['error']} |")  # fmt: skip
    lines += ["", "| Engine | Targets held | routed | unsafe | error | Side effects unsafe | "
              "routed | error |", "|---|---|---|---|---|---|---|---|"]  # fmt: skip
    for name in clean:
        t = Counter(r["class"].split(":")[0] for r in rows if r["engine"] == name and r["target"])
        c = Counter(
            r["class"].split(":")[0] for r in rows if r["engine"] == name and not r["target"]
        )
        if sum(t.values()):
            lines.append(f"| {name} | {t['held']} | {t['routed']} | {t['unsafe']} | {t['error']} | "
                         f"{c['unsafe']} | {c['routed']} | {c['error']} |")  # fmt: skip
    (HERE / "set-f-results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
