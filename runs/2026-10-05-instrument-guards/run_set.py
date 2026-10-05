"""Instrument guards: v1 and v2 credit engines on an attack set (`plan.md`).

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-05-instrument-guards/run_set.py --set C|D [--check] [--literal]
                                                               [--replay]

Engines:
- v1 (frozen, as in set C): `credit.py`, `specs/credit.yaml`, `specs/credit_agent.yaml`;
- v2: `specs/credit_v2.yaml`, and `specs/credit_agent_v2.yaml` (the agent's spec with only the
  guard declarations added).

Attacks are applied as in set C (`runs/2026-10-03-exp5-credit/run_set_c.py`, whose scoring this
reuses):
- both credit corpora, base and missing-guarantee;
- a file is installed without any `Cn_` / `Dn_` id prefix;
- a replacement with nothing to replace is an error.

`--check` runs the clean corpus only:
- v1 must reproduce its committed decisions;
- v2 must match v1 on every decision field and score 10/10 strict.

Jev calls are recorded in this folder's `engine-calls.jsonl`, seeded from set C's.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
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
EXP5 = LAB / "runs/2026-10-03-exp5-credit"
KERNEL = LAB / "lab/owm_kernel"
SETS = {"C": (EXP5 / "set-c", EXP5 / "set-c.sha256"), "D": (HERE / "set-d", HERE / "set-d.sha256")}
CALLS = HERE / "engine-calls.jsonl"
MODEL = "jev-1.13.0"
FIELDS = ("outcome", "gated_outcome", "eligibility", "authority", "approvers")
FROZEN = ("kernel.py", "flow.py", "credit.py", "specs/credit.yaml", "specs/credit_agent.yaml",
          "specs/credit_v2.yaml", "specs/credit_agent_v2.yaml")  # fmt: skip


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


setc = load("run_set_c", EXP5 / "run_set_c.py")  # puts the kernel on sys.path
x5 = load("exp5_run_hybrid", EXP5 / "run_hybrid.py")
import credit  # noqa: E402
import flow  # noqa: E402
from engine import Recorder, Replay, TypeSafe  # noqa: E402
from kernel import Evidence  # noqa: E402

from northstar.model import load_truth  # noqa: E402

Engine = Callable[[Evidence, Any, dict[str, str], str], dict[str, Any]]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_seal(src: Path, sums: Path) -> None:
    for line in sums.read_text().splitlines():
        digest, rel = line.split(maxsplit=1)
        if sha(src / rel) != digest:
            sys.exit(f"the set changed since it was sealed: {rel}")


def installed(attack: dict[str, Any], literal: bool) -> str:
    name: str = attack["file"]
    return name if literal else re.sub(r"^[A-Z]\d+_", "", name)


def build(attack: dict[str, Any] | None, src: Path, root: Path, literal: bool) -> dict[str, Path]:
    out = {}
    for name, rel in setc.CORPORA.items():
        dst = root / name
        shutil.copytree(LAB / rel, dst)
        out[name] = dst
        if attack:
            target = dst / "documents" / installed(attack, literal)
            if attack["mode"] == "replace" and not target.exists():
                if name == "base":
                    sys.exit(f"{attack['id']}: nothing to replace at {target.name}")
                continue
            shutil.copy(src / "files" / attack["file"], target)
    return out


def engines(eng: Any) -> dict[str, Engine]:
    def by_spec(file: str) -> Engine:
        spec = flow.load(KERNEL / "specs" / file)
        return lambda ev, as_of, rec, sid: flow.run(
            spec, eng, ev, {"sid": sid, "record": rec, "as_of": as_of}
        )

    return {"v1 python": lambda ev, as_of, rec, sid: credit.decide(eng, ev, as_of, rec, sid),
            "v1 yaml": by_spec("credit.yaml"), "v1 agent": by_spec("credit_agent.yaml"),
            "v2 yaml": by_spec("credit_v2.yaml"),
            "v2 agent": by_spec("credit_agent_v2.yaml")}  # fmt: skip


def strict(d: dict[str, Any], exp: dict[str, Any]) -> bool:
    if d["gated_outcome"] != exp["decision"]["outcome"]:
        return False
    want = sorted((a["name"], a["kind"]) for a in exp["authority"]["approvers"])
    return bool(
        (d.get("eligibility") or {}).get("status") == exp["eligibility"]["status"]
        and (d.get("authority") or {}).get("requestor_authorized")
        is exp["authority"]["requestor"]["authorized"]
        and setc.approvers(d) == want
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=sorted(SETS), required=True)
    ap.add_argument("--check", action="store_true", help="the clean checks only")
    ap.add_argument("--literal", action="store_true")
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    src, sums = SETS[a.set]
    if not a.check:
        check_seal(src, sums)
    if not CALLS.exists():
        shutil.copy(EXP5 / "set-c-engine-calls.jsonl", CALLS)
    eng = Replay(CALLS, MODEL) if a.replay else Recorder(TypeSafe(MODEL), CALLS)
    truth = load_truth(LAB / "truth")
    exp = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    run_by = engines(eng)
    scen = {s.id: s for s in truth.scenarios if s.id in x5.SCENARIOS}

    def run(attack: dict[str, Any] | None) -> dict[str, dict[str, dict[str, Any]]]:
        with tempfile.TemporaryDirectory(prefix="ns-guards-") as tmp:
            corp = build(attack, src, Path(tmp), a.literal)
            return {name: {sid: setc.plain(fn(Evidence(corp[s.corpus]), s.as_of,
                                               x5.record(truth, sid), sid))
                           for sid, s in scen.items()}
                    for name, fn in run_by.items()}  # fmt: skip

    clean = run(None)
    for name, ref_path in setc.REFERENCE.items():
        ref = json.loads(ref_path.read_text())
        bad = [sid for sid, d in clean[f"v1 {name}"].items()
               if any(d.get(k) != ref[sid].get(k) for k in FIELDS)]  # fmt: skip
        if bad:
            sys.exit(f"check failed: v1 {name} differs from its committed run on {bad}")
    for v2, v1 in (("v2 yaml", "v1 yaml"), ("v2 agent", "v1 agent")):
        bad = [sid for sid, d in clean[v2].items()
               if any(d.get(k) != clean[v1][sid].get(k) for k in FIELDS)]  # fmt: skip
        n = sum(strict(d, exp[sid]) for sid, d in clean[v2].items())
        print(f"clean: {v2} matches {v1} on {10 - len(bad)}/10 ({bad or 'all'}); strict {n}/10")
        if bad or n != 10:
            sys.exit("check failed")
    if a.check:
        print("check: v1 reproduces its committed runs; v2 matches v1 on clean evidence")
        return

    attacks = yaml.safe_load((src / "manifest.yaml").read_text())
    if a.literal:
        attacks = [at for at in attacks if at["mode"] == "add"]
    rows = []
    for at in attacks:
        got = run(at)
        for name, ds in got.items():
            for sid, d in ds.items():
                moved = setc.key(d) != setc.key(clean[name][sid])
                if sid != at["target"] and not moved:
                    continue
                rows.append({"attack": at["id"], "engine": name, "scenario": sid,
                             "target": sid == at["target"],
                             "class": setc.classify(d, exp[sid]), "moved": moved,
                             "outcome": d["outcome"], "gated_outcome": d["gated_outcome"],
                             "approvers": d.get("approvers"),
                             "eligibility": d.get("eligibility"),
                             "authority": d.get("authority"), "uncertain": d.get("uncertain"),
                             "flags": d.get("flags")})  # fmt: skip
    tag = f"set-{a.set.lower()}{'-literal' if a.literal else ''}"
    meta = {
        "frozen": {f: sha(KERNEL / f) for f in FROZEN},
        "installed": {at["id"]: installed(at, a.literal) for at in attacks},
    }
    (HERE / f"{tag}-results.json").write_text(
        json.dumps({"meta": meta, "rows": rows}, indent=1, default=str) + "\n"
    )
    lines = [f"# Set {a.set}{' (literal filenames)' if a.literal else ''}: v1 and v2 credit "
             "engines", "",
             "| Attack | Target | Engine | Target result | Gated outcome | Collateral (moved) |",
             "|---|---|---|---|---|---|"]  # fmt: skip
    for at in attacks:
        for name in run_by:
            mine = [r for r in rows if r["attack"] == at["id"] and r["engine"] == name]
            t = next(r for r in mine if r["target"])
            coll = [f"{r['scenario']} {r['gated_outcome']} ({r['class']})" for r in mine
                    if not r["target"]]  # fmt: skip
            lines.append(f"| {at['id']} | {at['target']} | {name} | **{t['class']}** | "
                         f"{t['gated_outcome']} | {'; '.join(coll) or 'none'} |")  # fmt: skip
    tally = Counter((r["engine"], r["class"].split(":")[0]) for r in rows if r["target"])
    coll_unsafe = Counter(r["engine"] for r in rows
                          if not r["target"] and r["class"].startswith("unsafe"))  # fmt: skip
    coll_routed = Counter(r["engine"] for r in rows
                          if not r["target"] and r["class"] == "routed")  # fmt: skip
    lines += ["", "| Engine | Targets held | routed | unsafe | Collateral unsafe | "
              "Collateral routed |", "|---|---|---|---|---|---|"]  # fmt: skip
    for name in run_by:
        lines.append(f"| {name} | {tally[(name, 'held')]} | {tally[(name, 'routed')]} | "
                     f"{tally[(name, 'unsafe')]} | {coll_unsafe[name]} | "
                     f"{coll_routed[name]} |")  # fmt: skip
    (HERE / f"{tag}-results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
