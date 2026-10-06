"""The OWM's register of approved procedures (G-13, `runs/2026-10-06-procedures-governed/plan.md`).

    uv run python lab/owm_register/build_procedures.py [--check]

A procedure (a spec, `lab/owm_kernel/specs/*.yaml`) is used only in a registered version. Each
version is admitted by the gate (`lab/spec_admission/admit.py`) on its exact text, registered by
its owning function and approved by a second person. Its approved text goes to a content-addressed
store, `procedure-store/<sha256>.yaml`, and is what runs (`lab/owm_kernel/governed.py`).

The registrar refuses a version when:
- no admission report exists for that exact text (by the kernel's normalised sha256), or the
  report's verdict isn't admitted;
- the approver is the registrar;
- either of them isn't an employee in the HR export. An agent may propose a registration but never
  approve one (G-01, decided 2026-10-05).

`--check` rebuilds in memory and fails if `procedures.yaml` or the store would change.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(LAB / "lab/owm_kernel")]
from kernel import fingerprint  # noqa: E402

SPECS = LAB / "lab/owm_kernel/specs"
STORE = HERE / "procedure-store"
OUT = HERE / "procedures.yaml"
ADMISSION = LAB / "runs/2026-10-06-procedures-governed/admission"
EMPLOYEES = LAB / "dataset/evidence/structured/employees.csv"

SALES = ("Michael Torres (EMP-200, VP Sales)", "David Morgan (EMP-300, Chief Revenue Officer)")
FINANCE = ("Priya Shah (EMP-401, Finance Manager)", "Elena Novak (EMP-402, Director of Finance)")
SUPPORT = ("Hannah Lindqvist (EMP-601, Support Escalation Manager)",
           "Marcus Adeyemi (EMP-602, Director of Customer Support)")  # fmt: skip
DISCOUNT_KINDS = {"policy": "pricing_policy", "agreement": "agreement", "amendment": "amendment",
                  "exception": "exception"}  # fmt: skip
SLA_KINDS = {"schedule": "sla_schedule", "guide": "severity_guide",
             "procedure": "escalation_procedure", "calendar": "holiday_calendar",
             "terms": "support_terms"}  # fmt: skip

# The versions to register. `deployment` is what the gate admitted the spec with: the register
# mapping applied to a spec that declares none (None: the spec's own declaration).
VERSIONS: list[dict[str, Any]] = [
    {"proc_id": "PROC-DISCOUNT", "decision_type": "discount", "version": 1,
     "file": "discount.yaml", "effective_from": "2025-01-01", "effective_to": None,
     "author": "transcribed by the lab from the discount procedure (specs as data, 2026-10-04)",
     "admission": "discount.json", "deployment": {"registered_kinds": DISCOUNT_KINDS},
     "who": SALES, "on": "2026-10-06"},
    {"proc_id": "PROC-CREDIT", "decision_type": "credit", "version": 1,
     "file": "credit_v3.yaml", "effective_from": "2025-01-01", "effective_to": None,
     "author": "written by the lab: the credit procedure on the register's terms (2026-10-05)",
     "admission": "credit_v3.json", "deployment": None, "who": FINANCE, "on": "2026-10-06"},
    {"proc_id": "PROC-SLA", "decision_type": "sla", "version": 1,
     "file": "sla.yaml", "effective_from": "2025-01-01", "effective_to": "2026-10-05",
     "author": "transcribed by the lab from rules a blind subagent wrote (2026-10-03, 2026-10-04)",
     "admission": "sla.json", "deployment": {"registered_kinds": SLA_KINDS},
     "who": SUPPORT, "on": "2026-10-06"},
    {"proc_id": "PROC-SLA", "decision_type": "sla", "version": 2,
     "file": "sla_agent.yaml", "effective_from": "2026-10-06", "effective_to": None,
     "author": "proposed by an agent (the SLA author subagent); revision 1 after the admission "
               "gate's report (runs/2026-10-06-spec-admission/)",
     "admission": "sla_agent.json", "deployment": None, "supersedes": "PROC-SLA v1",
     "who": SUPPORT, "on": "2026-10-06"},
]  # fmt: skip


class RefusedError(Exception):
    pass


def employees() -> set[str]:
    with EMPLOYEES.open() as f:
        return {r["employee_id"] for r in csv.DictReader(f)}


def person(who: str, staff: set[str]) -> str:
    m = re.search(r"\((EMP-\d+),", who)
    if not m or m.group(1) not in staff:
        raise RefusedError(f"{who!r} is not an employee; an agent may propose a registration but "
                      "never approve one")  # fmt: skip
    return m.group(1)


def register(v: dict[str, Any], staff: set[str], spec_text: str | None = None,
             report_path: Path | None = None) -> tuple[dict[str, Any], str]:  # fmt: skip
    """One version, checked; returns its entry and its approved text."""
    text = spec_text if spec_text is not None else (SPECS / v["file"]).read_text()
    sha = fingerprint(text)
    rp = report_path or ADMISSION / v["admission"]
    if not rp.exists():
        raise RefusedError(f"{v['file']}: no admission report")
    report = json.loads(rp.read_text())
    if report["report"].get("sha256") != sha:
        raise RefusedError(f"{v['file']}: the admission report is not for this exact text")
    if not report["verdict"]["admitted"]:
        failed = [g for g in "ABC" if not report["verdict"][g]]
        raise RefusedError(f"{v['file']}: not admitted (failed gate {', '.join(failed)})")
    registrar, approver = v["who"]
    if person(registrar, staff) == person(approver, staff):
        raise RefusedError(f"{v['file']}: the approver is the registrar")
    entry = {
        "proc_id": v["proc_id"], "decision_type": v["decision_type"], "version": v["version"],
        "file": v["file"], "sha256": sha,
        "effective_from": v["effective_from"], "effective_to": v["effective_to"],
        "relations": ([{"type": "supersedes", "target": v["supersedes"]}]
                      if v.get("supersedes") else []),
        "deployment": v["deployment"], "author": v["author"],
        "admission": {"report": str(rp.relative_to(LAB)), "verdict": "admitted",
                      "gates": {g: report["verdict"][g] for g in "ABC"}},
        "registered_by": registrar, "approved_by": approver,
        "registered_on": v["on"], "approved_on": v["on"],
    }  # fmt: skip
    return entry, text


HEADER = ("# The OWM's register of approved procedures (G-13). GENERATED by\n"
          "# lab/owm_register/build_procedures.py, do not edit.\n")  # fmt: skip


def build() -> tuple[str, dict[str, str]]:
    staff = employees()
    entries, store = [], {}
    for v in VERSIONS:
        entry, text = register(v, staff)
        entries.append(entry)
        store[f"{entry['sha256']}.yaml"] = text
    body = yaml.safe_dump({"register": "procedures", "entries": entries}, sort_keys=False,
                          allow_unicode=True, width=100)  # fmt: skip
    return HEADER + body, store


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text, store = build()
    if a.check:
        stale = [n for n, t in store.items() if not (STORE / n).exists()
                 or (STORE / n).read_text() != t]  # fmt: skip
        if not OUT.exists() or OUT.read_text() != text or stale:
            sys.exit("procedures register: out of date")
        print("procedures register: up to date")
        return
    STORE.mkdir(exist_ok=True)
    for n, t in store.items():
        (STORE / n).write_text(t)
    OUT.write_text(text)
    print(f"procedures register: {len(store)} versions written")


if __name__ == "__main__":
    main()
