"""G-13's checks, P1–P5 (`plan.md`). Free: Jev replay only.

uv run python runs/2026-10-06-procedures-governed/run_governed.py
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]


def load(name: str, path: Path) -> ModuleType:
    s = importlib.util.spec_from_file_location(name, path)
    assert s and s.loader
    mod = importlib.util.module_from_spec(s)
    sys.modules[name] = mod
    s.loader.exec_module(mod)
    return mod


admit = load("admit", LAB / "lab/spec_admission/admit.py")  # puts the kernel on sys.path
bp = load("build_procedures", LAB / "lab/owm_register/build_procedures.py")
import flow  # noqa: E402
import governed  # noqa: E402

SPECS = LAB / "lab/owm_kernel/specs"
TYPES = {"discount": "discount.yaml", "credit": "credit_v3.yaml", "sla": "sla.yaml"}
TAMPER = (
    '  - { when: \'eligibility["status"] in ("ineligible", "exceeded")\', '
    "outcome: REJECT_OR_ESCALATE }\n"
)


def strip(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if k != "procedure"}


def main() -> None:
    gate = admit.Gate(admit.Layered(HERE / "jev-calls.jsonl", live=False, cap=0))
    entries = governed.procedures()
    reg = admit.ra.REG
    out: dict[str, Any] = {}

    # P1: the build is stable, and the registrar refuses the four bad requests
    staff = bp.employees()
    first = {v["file"]: v for v in bp.VERSIONS}
    bad = {
        "credit_agent.yaml (not admitted)": (
            first["credit_v3.yaml"] | {"file": "credit_agent.yaml"},
            None, HERE / "admission/credit_agent.json"),
        "sla_agent_v1.yaml (not admitted)": (
            first["sla_agent.yaml"], (LAB / "runs/2026-10-06-spec-admission/sla_agent_v1.yaml"
                                      ).read_text(), HERE / "admission/sla_agent_v1.json"),
        "approver = registrar": (first["sla.yaml"] | {"who": (bp.SUPPORT[0], bp.SUPPORT[0])},
                                 None, None),
        "an agent approves": (first["sla_agent.yaml"]
                              | {"who": (bp.SUPPORT[0], "the SLA author (an agent)")}, None, None),
    }  # fmt: skip
    refusals = {}
    for label, (v, text, rp) in bad.items():
        try:
            bp.register(v, staff, text, rp)
            refusals[label] = "ACCEPTED (wrong)"
        except bp.RefusedError as e:
            refusals[label] = f"refused: {e}"
    stable = bp.build()[0] == bp.OUT.read_text()
    out["P1"] = {"versions": len(entries), "stable": stable, "refusals": refusals,
                 "holds": stable and len(entries) == 4
                 and all(r.startswith("refused") for r in refusals.values())}  # fmt: skip

    # P2: governed decisions equal the deployed specs' decisions, and every record is stamped
    with tempfile.TemporaryDirectory(prefix="ns-g13-") as tmp:
        roots = gate.clean_roots(Path(tmp) / "clean")
        p2: dict[str, Any] = {}
        clean_gov: dict[str, dict[str, Any]] = {}
        for kind, file in TYPES.items():
            spec, _ = gate.deployed(SPECS / file, kind)
            same, stamped, n = 0, 0, 0
            for sid in gate.scenarios(kind):
                c = gate.corpus(kind, sid)
                at = gate.inputs(kind, sid).get("as_of") or gate.scen[sid].as_of
                g = governed.decide(kind, gate.eng, admit.Evidence(roots[c]),
                                    gate.inputs(kind, sid), at, reg[c], entries)  # fmt: skip
                d = gate.decide(spec, kind, sid, roots[c], reg[c])
                g_plain = admit.ra.plain(g)
                clean_gov[sid] = g_plain
                n += 1
                same += strip(g_plain) == d
                stamped += g_plain.get("procedure", {}).get("id") == f"PROC-{kind.upper()}"
            p2[kind] = {"scenarios": n, "equal": same, "stamped": stamped}
        out["P2"] = p2 | {"holds": all(v["equal"] == v["scenarios"] == v["stamped"]
                                       for v in p2.values())}  # fmt: skip

        # P3: SLA versions by date
        versions = {sid: clean_gov[sid]["procedure"]["version"] for sid in gate.scenarios("sla")}
        later = admit.ra.plain(governed.decide(
            "sla", gate.eng, admit.Evidence(roots["base"]), gate.inputs("sla", "S36"),
            "2026-10-07", reg["base"], entries))  # fmt: skip
        agent_spec, _ = gate.deployed(SPECS / "sla_agent.yaml", "sla")
        agent = gate.decide(agent_spec, "sla", "S36", roots["base"], reg["base"])
        out["P3"] = {"clean_versions": versions, "at_2026_10_07": later["procedure"],
                     "equals_sla_agent": strip(later) == agent,
                     "holds": set(versions.values()) == {1} and later["procedure"]["version"] == 2
                     and strip(later) == agent}  # fmt: skip

        # P4: the credit procedure edited in place on disk
        specs = Path(tmp) / "specs"
        shutil.copytree(SPECS, specs)
        text = (specs / "credit_v3.yaml").read_text()
        assert TAMPER in text, "the tamper target moved"
        (specs / "credit_v3.yaml").write_text(text.replace(TAMPER, ""))
        unchanged, flagged, moved_ungoverned = 0, 0, []
        tampered = flow.load(specs / "credit_v3.yaml")
        for sid in gate.scenarios("credit"):
            c = gate.corpus("credit", sid)
            g = admit.ra.plain(governed.decide(
                "credit", gate.eng, admit.Evidence(roots[c]), gate.inputs("credit", sid),
                gate.scen[sid].as_of, reg[c], entries, specs=specs))  # fmt: skip
            flags = g.get("flags") or []
            flagged += any(str(f).startswith("incident: the procedure file") for f in flags)
            g2 = dict(g, flags=[f for f in flags if not str(f).startswith("incident:")])
            unchanged += g2 == clean_gov[sid]
            raw = gate.decide(tampered, "credit", sid, roots[c], reg[c])
            if gate.kkey("credit", raw) != gate.kkey("credit", strip(clean_gov[sid])):
                moved_ungoverned.append(f"{sid}: {raw.get('gated_outcome')}")
        n = len(gate.scenarios("credit"))
        out["P4"] = {"scenarios": n, "unchanged": unchanged, "flagged": flagged,
                     "ungoverned_tampered_moved": moved_ungoverned,
                     "holds": unchanged == flagged == n and bool(moved_ungoverned)}  # fmt: skip

        # P5: no procedure in force
        try:
            ev, inp = admit.Evidence(roots["base"]), gate.inputs("discount", "S01")
            governed.decide("discount", gate.eng, ev, inp, "2024-06-01", reg["base"], entries)
            out["P5"] = {"result": "RAN (wrong)", "holds": False}
        except governed.NoProcedureError as e:
            out["P5"] = {"result": f"refused: {e}", "holds": True}

    (HERE / "results.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    for k, v in out.items():
        print(k, "HOLDS" if v["holds"] else "MISSED", {x: y for x, y in v.items() if x != "holds"})


if __name__ == "__main__":
    main()
