"""The register (G-01): v1, v2, v2+R, v3 and v3u credit engines on sets C and D (`plan.md`).

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-05-register/run_set.py --check            # K3, K4 (clean, re-save)
    uv run python runs/2026-10-05-register/run_set.py --set C|D|E [--replay]

Engines:
- v1 python / yaml / agent and v2 yaml / agent: frozen, as in the instrument-guards run;
- **v2+R** yaml / agent: the frozen v2 specs plus one declaration, `registered_kinds: [policy,
  guarantee]` (R1), added here;
- **v3**: `specs/credit_v3.yaml`, terms from the register (R2), `on_mismatch: route` (R3);
- **v3u**: v3 with `on_mismatch: use_registered`, set here.

Register-backed engines get their company's register (`lab/owm_register/<corpus>.yaml`), built
from the clean corpora. Attacks change documents only; the register is out of reach.

Attacks are applied, and decisions scored, exactly as in `runs/2026-10-05-instrument-guards/
run_set.py`, which this reuses. With `--set`, the harness also checks that v1 and v2 reproduce
that run's committed rows (R-e). Jev calls are recorded in this folder's `engine-calls.jsonl`,
seeded from that run's.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
GUARDS = LAB / "runs/2026-10-05-instrument-guards"
KERNEL = LAB / "lab/owm_kernel"
CALLS = HERE / "engine-calls.jsonl"
SCORED = ("outcome", "gated_outcome", "approvers")


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


guards = load("guards_run_set", GUARDS / "run_set.py")  # puts the kernel on sys.path
setc, x5 = guards.setc, guards.x5
guards.SETS["E"] = (HERE / "set-e", HERE / "set-e.sha256")  # the user's set E (set-e-plan.md)
import credit  # noqa: E402
import flow  # noqa: E402
from engine import Recorder, Replay, TypeSafe  # noqa: E402
from kernel import Evidence, Register  # noqa: E402

from northstar.model import load_truth  # noqa: E402

REGISTERS = {c: Register.load(LAB / "lab/owm_register" / f"{c}.yaml") for c in setc.CORPORA}
Engine = Callable[[Evidence, str, Any, dict[str, str], str], dict[str, Any]]


def engines(eng: Any) -> dict[str, Engine]:
    def by_spec(file: str, patch: dict[str, Any] | None = None, reg: bool = False) -> Engine:
        spec = flow.load(KERNEL / "specs" / file)
        spec["documents"].update(patch or {})
        return lambda ev, corpus, as_of, rec, sid: flow.run(
            spec, eng, ev, {"sid": sid, "record": rec, "as_of": as_of},
            register=REGISTERS[corpus] if reg else None,
        )  # fmt: skip

    r1 = {"registered_kinds": ["policy", "guarantee"]}
    return {
        "v1 python": lambda ev, corpus, as_of, rec, sid: credit.decide(eng, ev, as_of, rec, sid),
        "v1 yaml": by_spec("credit.yaml"),
        "v1 agent": by_spec("credit_agent.yaml"),
        "v2 yaml": by_spec("credit_v2.yaml"),
        "v2 agent": by_spec("credit_agent_v2.yaml"),
        "v2+R yaml": by_spec("credit_v2.yaml", r1, reg=True),
        "v2+R agent": by_spec("credit_agent_v2.yaml", r1, reg=True),
        "v3": by_spec("credit_v3.yaml", reg=True),
        "v3u": by_spec("credit_v3.yaml", {"on_mismatch": "use_registered"}, reg=True),
    }


def scored(d: dict[str, Any]) -> tuple[Any, ...]:
    e, a = d.get("eligibility") or {}, d.get("authority") or {}
    return (d["outcome"], d["gated_outcome"], tuple(setc.approvers(d)), e.get("status"),
            e.get("maximum_limit"), a.get("requestor_authorized"))  # fmt: skip


def resave(root: Path) -> None:
    """K4: re-save the registered documents as an editor might (CRLF, trailing spaces)."""
    for name in ("credit_policy_2026.md", "credit_policy_2025.md", "acme_parent_guarantee.md"):
        p = root / "base/documents" / name
        p.write_bytes(("  \r\n".join(p.read_text().split("\n")) + "\r\n").encode())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=sorted(guards.SETS))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    if not (a.set or a.check):
        ap.error("give --set or --check")
    if not CALLS.exists():
        shutil.copy(GUARDS / "engine-calls.jsonl", CALLS)
    eng = Replay(CALLS, guards.MODEL) if a.replay else Recorder(TypeSafe(guards.MODEL), CALLS)
    truth = load_truth(LAB / "truth")
    exp = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    run_by = engines(eng)
    scen = {s.id: s for s in truth.scenarios if s.id in x5.SCENARIOS}

    def run(attack: dict[str, Any] | None, src: Path | None, saved: bool = False
            ) -> dict[str, dict[str, dict[str, Any]]]:  # fmt: skip
        with tempfile.TemporaryDirectory(prefix="ns-register-") as tmp:
            corp = guards.build(attack, src, Path(tmp), False)
            if saved:
                resave(Path(tmp))
            return {name: {sid: setc.plain(fn(Evidence(corp[s.corpus]), s.corpus, s.as_of,
                                               x5.record(truth, sid), sid))
                           for sid, s in scen.items()}
                    for name, fn in run_by.items()}  # fmt: skip

    clean = run(None, None)
    for name in run_by:
        if name.startswith(("v2+R", "v3")):
            ref = "v1 agent" if name.endswith("agent") else "v1 yaml"  # the spec it derives from
            bad = [sid for sid, d in clean[name].items() if scored(d) != scored(clean[ref][sid])]
            n = sum(guards.strict(d, exp[sid]) for sid, d in clean[name].items())
            print(f"clean: {name} matches {ref} on {10 - len(bad)}/10 {bad or ''}; strict {n}/10")
            if bad or n != 10:
                sys.exit("K3 failed")
    if a.check:
        saved = run(None, None, saved=True)
        mismatch = ("registered version", "not registered", " is mismatch", " is missing")
        for name in run_by:
            flagged = [sid for sid, d in saved[name].items()
                       if any(m in f for f in d.get("flags") or [] for m in mismatch)]  # fmt: skip
            changed = [
                sid for sid, d in saved[name].items() if scored(d) != scored(clean[name][sid])
            ]
            print(f"re-saved: {name:10} register mismatch flags: {flagged or 'none'}; "
                  f"decisions changed: {changed or 'none'}")  # fmt: skip
            if flagged:  # K4: a re-save must still match its registered version
                sys.exit("K4 failed")
        print("check: K3 and K4 pass")
        return

    src, sums = guards.SETS[a.set]
    guards.check_seal(src, sums)
    attacks = yaml.safe_load((src / "manifest.yaml").read_text())
    rows = []
    for at in attacks:
        got = run(at, src)
        for name, ds in got.items():
            for sid, d in ds.items():
                moved = setc.key(d) != setc.key(clean[name][sid])
                if sid != at["target"] and not moved:
                    continue
                rows.append({"attack": at["id"], "engine": name, "scenario": sid,
                             "target": sid == at["target"], "class": setc.classify(d, exp[sid]),
                             "moved": moved, "outcome": d["outcome"],
                             "gated_outcome": d["gated_outcome"], "approvers": d.get("approvers"),
                             "eligibility": d.get("eligibility"), "authority": d.get("authority"),
                             "registered": d.get("registered"),
                             "flags": d.get("flags")})  # fmt: skip
    # R-e: v1 and v2 reproduce the instrument-guards run's committed rows (sets C and D)
    old_path = GUARDS / f"set-{a.set.lower()}-results.json"
    if old_path.exists():
        old = json.loads(old_path.read_text())["rows"]
        pick = lambda rs: {(r["attack"], r["engine"], r["scenario"], r["class"], r["gated_outcome"])  # noqa: E731
                           for r in rs if r["engine"].startswith(("v1", "v2 "))}  # fmt: skip
        if pick(rows) != pick(old):
            sys.exit(f"R-e failed: v1/v2 differ from the committed set {a.set} rows")
        print(f"R-e: v1 and v2 reproduce the committed set {a.set} rows")
    tag = f"set-{a.set.lower()}"
    (HERE / f"{tag}-results.json").write_text(
        json.dumps({"rows": rows}, indent=1, default=str) + "\n"
    )
    lines = [f"# Set {a.set}: v1, v2 and register-backed credit engines", "",
             "| Attack | Target | Engine | Target result | Gated outcome | Collateral (moved) |",
             "|---|---|---|---|---|---|"]  # fmt: skip
    for at in attacks:
        for name in run_by:
            mine = [r for r in rows if r["attack"] == at["id"] and r["engine"] == name]
            t = next(r for r in mine if r["target"])
            coll = [
                f"{r['scenario']} {r['gated_outcome']} ({r['class']})"
                for r in mine
                if not r["target"]
            ]
            lines.append(f"| {at['id']} | {at['target']} | {name} | **{t['class']}** | "
                         f"{t['gated_outcome']} | {'; '.join(coll) or 'none'} |")  # fmt: skip
    tally = Counter((r["engine"], r["class"].split(":")[0]) for r in rows if r["target"])
    cu = Counter(r["engine"] for r in rows if not r["target"] and r["class"].startswith("unsafe"))
    cr = Counter(r["engine"] for r in rows if not r["target"] and r["class"] == "routed")
    lines += ["", "| Engine | Targets held | routed | unsafe | Collateral unsafe | "
              "Collateral routed |", "|---|---|---|---|---|---|"]  # fmt: skip
    for name in run_by:
        lines.append(f"| {name} | {tally[(name, 'held')]} | {tally[(name, 'routed')]} | "
                     f"{tally[(name, 'unsafe')]} | {cu[name]} | {cr[name]} |")  # fmt: skip
    (HERE / f"{tag}-results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
