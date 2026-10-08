"""Attacks on the register: apply the sealed cases to the frozen registrar, then decide through
(`plan.md`, steps 5 and 6).

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-08-register-attacks/run_attacks.py run     # blind: no labels read
    uv run python runs/2026-10-08-register-attacks/run_attacks.py score   # after results commit

`run` applies each case's changes in order to a fresh copy of its corpus's register at the clock,
recording each change as admitted or refused (with the rule). If anything was admitted, it decides
every discount, credit and SLA scenario on that corpus through the governed procedures, with the
changed register and with the bootstrap register, and records every scenario whose decision moves
(at the outcome level, gate C's key, and at the harnesses' full key). Jev: every recorded answer,
then live calls up to a cap. `run` never opens `sealed/descriptions.md`.

`score` reads the unsealed labels and computes M1–M4.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
CASES = HERE / "sealed/cases"
LABELS = HERE / "sealed/descriptions.md"
CALLS = HERE / "jev-calls.jsonl"
JEV_CAP = 2000  # about $0.04 at I2's rate
KINDS = ("discount", "credit", "sla")


def load(name: str, path: Path) -> ModuleType:
    s = importlib.util.spec_from_file_location(name, path)
    assert s and s.loader
    mod = importlib.util.module_from_spec(s)
    sys.modules[name] = mod
    s.loader.exec_module(mod)
    return mod


def run(cases: Path = CASES, out_dir: Path = HERE) -> None:
    admit = load("admit", LAB / "lab/spec_admission/admit.py")  # puts the kernel on sys.path
    sys.path.insert(0, str(LAB / "lab/owm_register"))
    import governed
    import registrar

    gate = admit.Gate(admit.Layered(CALLS, live=True, cap=JEV_CAP))
    entries = governed.procedures()
    staff = registrar.Staff.load()
    out: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="ns-regatk-") as tmp:
        roots = gate.clean_roots(Path(tmp) / "clean")
        base_cache: dict[tuple[str, str], Any] = {}

        def decide(kind: str, sid: str, reg: Any) -> dict[str, Any]:
            c = gate.corpus(kind, sid)
            inp = gate.inputs(kind, sid)
            at = inp.get("as_of") or gate.scen[sid].as_of or inp.get("decided_at")
            try:
                g = governed.decide(kind, gate.eng, admit.Evidence(roots[c]), inp, at, reg,
                                    entries)  # fmt: skip
                return dict(admit.ra.plain(g))
            except Exception as e:  # noqa: BLE001
                return {"gated_outcome": "ERROR", "error": f"{type(e).__name__}: {e}"[:200]}

        for path in sorted(cases.glob("*.yaml")):
            case = yaml.safe_load(path.read_text())
            corpus = case.get("corpus", "base")
            acting = {str(x) for x in case.get("acting_as") or []}
            state = registrar.State.bootstrap(corpus)
            base_state = state
            steps = []
            for i, ch in enumerate(case.get("changes") or []):
                text = (cases / ch["text"]).read_text() if ch.get("text") else None
                try:
                    state = registrar.apply(state, ch, text, acting, staff=staff)
                    steps.append({"change": i + 1, "action": ch.get("action"),
                                  "result": "admitted"})  # fmt: skip
                except registrar.RefusedError as e:
                    steps.append({"change": i + 1, "action": ch.get("action"),
                                  "result": "refused", "rule": e.rule, "why": str(e)})  # fmt: skip
                except Exception as e:  # noqa: BLE001 — a malformed case is refused, and counted
                    steps.append({"change": i + 1, "action": ch.get("action"),
                                  "result": "refused", "rule": "malformed",
                                  "why": f"{type(e).__name__}: {e}"[:200]})  # fmt: skip
            moved: list[dict[str, Any]] = []
            if any(s["result"] == "admitted" for s in steps):
                reg_new, reg_base = state.register(), base_state.register()
                for kind in KINDS:
                    for sid in gate.scenarios(kind):
                        if gate.corpus(kind, sid) != corpus:
                            continue
                        if (kind, sid) not in base_cache:
                            base_cache[(kind, sid)] = decide(kind, sid, reg_base)
                        b, n = base_cache[(kind, sid)], decide(kind, sid, reg_new)
                        if gate.ckey(kind, b) != gate.ckey(kind, n) or (
                            gate.kkey(kind, b) != gate.kkey(kind, n)
                        ):
                            moved.append({"scenario": sid, "kind": kind,
                                          "outcome_level": gate.ckey(kind, b) != gate.ckey(kind, n),
                                          "before": str(gate.ckey(kind, b)),
                                          "after": str(gate.ckey(kind, n)),
                                          "before_full": str(gate.kkey(kind, b)),
                                          "after_full": str(gate.kkey(kind, n)),
                                          "flags_after": (n.get("flags") or [])[:6]})  # fmt: skip
            out.append({"case": case.get("case", path.stem), "corpus": corpus, "steps": steps,
                        "decisions_moved": moved})  # fmt: skip
            print(f"{path.stem}: " + ", ".join(
                f"{s['action']} {s['result']}" + (f" ({s['rule']})" if s.get("rule") else "")
                for s in steps) + (f"; {len(moved)} decisions moved" if moved else ""))  # fmt: skip
    (out_dir / "results.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    lines = ["# Attacks on the register: results (blind; labels not yet read)", "",
             "| Case | Corpus | Changes | Decisions moved |", "|---|---|---|---|"]  # fmt: skip
    for r in out:
        ch = "; ".join(f"{s['action']}: **{s['result']}**" + (f" {s['rule']}" if s.get("rule")
                       else "") for s in r["steps"])  # fmt: skip
        mv = ", ".join(f"{m['scenario']}{'*' if m['outcome_level'] else ''}"
                       for m in r["decisions_moved"]) or "none"  # fmt: skip
        lines.append(f"| {r['case']} | {r['corpus']} | {ch} | {mv} |")
    lines += ["", "`*` = moved at the outcome level (gate C's key); otherwise the full key only.",
              f"Live Jev calls: {gate.eng.live_calls}."]  # fmt: skip
    (out_dir / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def score() -> None:
    res = json.loads((HERE / "results.json").read_text())
    labels: dict[str, str] = {}
    for line in LABELS.read_text().splitlines():
        m = re.match(r"\|\s*\**(C\d+)\**\s*\|\s*\**(legit|attack)", line, re.I)
        if m:
            labels[m.group(1)] = m.group(2).lower()
    rows, m1, m2, harm = [], [], [], []
    for r in res:
        lab = labels.get(r["case"], "?")
        admitted = [s for s in r["steps"] if s["result"] == "admitted"]
        refused = [s for s in r["steps"] if s["result"] == "refused"]
        moved = [m for m in r["decisions_moved"] if m["outcome_level"]]
        if lab == "attack" and admitted:
            m1.append(r["case"])
            if moved:
                harm.append(r["case"])
        if lab == "legit" and refused:
            m2.append(r["case"])
        rows.append(f"| {r['case']} | {lab} | {len(admitted)} admitted, {len(refused)} refused "
                    + "(" + ", ".join(s.get("rule", "") for s in refused) + ") | "
                    + (", ".join(m["scenario"] for m in moved) or "none") + " |")  # fmt: skip
    n_att = sum(v == "attack" for v in labels.values())
    n_leg = sum(v == "legit" for v in labels.values())
    text = ["# Scored (labels unsealed)", "",
            f"- Cases: {len(res)}; labels found: {len(labels)} ({n_leg} legit, {n_att} attack)",
            f"- **M1 attacks with any change admitted:** {len(m1)} {m1}",
            f"- **M2 legitimate cases with any change refused:** {len(m2)} {m2}",
            f"- **M3 admitted attacks that moved a decision (outcome level):** {len(harm)} {harm}",
            "", "| Case | Label | Changes | Decisions moved (outcome level) |",
            "|---|---|---|---|", *rows]  # fmt: skip
    (HERE / "scored.md").write_text("\n".join(text) + "\n")
    print("\n".join(text))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["run", "score"])
    ap.add_argument("--cases", type=Path, default=CASES, help="smoke tests only")
    ap.add_argument("--out", type=Path, default=HERE, help="smoke tests only")
    a = ap.parse_args()
    if a.step == "run":
        run(a.cases, a.out)
    else:
        score()


if __name__ == "__main__":
    main()
