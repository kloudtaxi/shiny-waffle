"""Governed decisions (G-13, `runs/2026-10-06-procedures-governed/plan.md`).

A decision runs the procedure version **in force on its date**, from the **approved text** in the
procedure register's store (`lab/owm_register/procedures.yaml`), never the file on disk. The record
is stamped with the version that made it. A file on disk that differs from its registered version
raises an incident; the approved version is what runs. With no version in force, nothing runs.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import flow
import yaml
from kernel import Evidence, Register, fingerprint

LAB = Path(__file__).resolve().parents[2]
REGISTER = LAB / "lab/owm_register/procedures.yaml"
STORE = LAB / "lab/owm_register/procedure-store"
SPECS = LAB / "lab/owm_kernel/specs"


class NoProcedureError(Exception):
    """No registered procedure version is in force for this decision type on this date."""


def procedures(path: Path = REGISTER) -> list[dict[str, Any]]:
    return list(yaml.safe_load(path.read_text())["entries"])


def day(at: date | datetime | str) -> date:
    if isinstance(at, datetime):
        return at.date()
    if isinstance(at, date):
        return at
    return date.fromisoformat(str(at)[:10])


def in_force(entries: list[dict[str, Any]], decision_type: str,
             at: date | datetime | str) -> dict[str, Any] | None:  # fmt: skip
    on = day(at)
    live = [e for e in entries if e["decision_type"] == decision_type
            and day(e["effective_from"]) <= on
            and (e["effective_to"] is None or on <= day(e["effective_to"]))]  # fmt: skip
    return max(live, key=lambda e: e["version"]) if live else None


def decide(
    decision_type: str, eng: Any, ev: Evidence, inputs: dict[str, Any], at: date | datetime | str,
    register: Register | None, entries: list[dict[str, Any]] | None = None,
    store: Path = STORE, specs: Path = SPECS,
) -> dict[str, Any]:  # fmt: skip
    entries = procedures() if entries is None else entries
    entry = in_force(entries, decision_type, at)
    if entry is None:
        raise NoProcedureError(f"no {decision_type} procedure is in force on {day(at)}")
    approved = (store / f"{entry['sha256']}.yaml").read_text()
    spec = flow.loads(approved, entry["file"])
    if entry.get("deployment"):
        spec["documents"].update(entry["deployment"])
    on_disk = specs / entry["file"]
    differs = not on_disk.exists() or fingerprint(on_disk.read_text()) != entry["sha256"]
    record = flow.run(spec, eng, ev, inputs, register)
    if differs:
        record.setdefault("flags", []).append(
            f"incident: the procedure file {entry['file']} differs from {entry['proc_id']} "
            f"v{entry['version']}; the approved version was used (raised to "
            f"{entry['approved_by']})"
        )
    record["procedure"] = {"id": entry["proc_id"], "version": entry["version"],
                           "sha256": entry["sha256"]}  # fmt: skip
    return record
