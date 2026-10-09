"""Semantica 0.7.0's bi-temporal queries on the OWM register (G-38: "as known at" time).

    <scratchpad>/kfenv/bin/python runs/2026-10-09-semantica-bitemporal/check.py

Each registered governing document becomes one relationship (company -> document) with its
validity window (valid_from / valid_until) and its registration date as transaction time
(recorded_at). Questions:
- valid time only: what governs on date V (the kernel's `entry_in_force` question);
- transaction time only: what had the organization registered by date T;
- both: what did the organization, as known on T, hold to be in force on V. Semantica takes one
  time per call, so this is composed: filter by transaction time T, then by valid time V.

The expected answer for every question is computed here independently of Semantica, from the
register's own fields. No model calls.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from semantica.kg.temporal_query import TemporalGraphQuery

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
REG = LAB / "lab/owm_register/base.yaml"


def d(x: Any) -> date:
    return date.fromisoformat(str(x)[:10])


def graph(entries: list[dict[str, Any]], entity_times: bool) -> dict[str, Any]:
    """`entity_times`: give every entity its own transaction time (the company from 2000, each
    document from its registration). Without it, Semantica treats an entity with no
    `recorded_at` as recorded now (wall-clock time), which hides it from earlier queries."""
    ents = [{"id": "northstar", "name": "Northstar"}] + [
        {"id": e["doc_id"], "name": e["doc_id"], "type": e["kind"]} for e in entries
    ]
    if entity_times:
        ents[0]["recorded_at"] = "2000-01-01"
        for x, e in zip(ents[1:], entries, strict=True):
            x["recorded_at"] = str(e["registered_on"])
    rels = [{"source": "northstar", "target": e["doc_id"], "type": f"governed_by_{e['kind']}",
             "valid_from": str(e["effective_from"]),
             "valid_until": str(e["effective_to"]) if e.get("effective_to") else None,
             "recorded_at": str(e["registered_on"])} for e in entries]  # fmt: skip
    return {"entities": ents, "relationships": rels}


def ids(result: dict[str, Any]) -> set[str]:
    return {r["target"] for r in result.get("relationships", [])}


def main() -> None:
    entries = yaml.safe_load(REG.read_text())["entries"]
    report = {}
    for label, et in (("entities_untimed", False), ("entities_timed", True)):
        print(f"== {label}")
        report[label] = run(entries, graph(entries, et))
    (HERE / "results.json").write_text(json.dumps(report, indent=1) + "\n")


def run(entries: list[dict[str, Any]], g: dict[str, Any]) -> list[dict[str, Any]]:
    q = TemporalGraphQuery()

    def valid(e: dict[str, Any], v: date) -> bool:
        end = d(e["effective_to"]) if e.get("effective_to") else date.max
        return d(e["effective_from"]) <= v <= end

    def known(e: dict[str, Any], t: date) -> bool:
        return d(e["registered_on"]) <= t

    cases = [("valid", "2026-09-23", None), ("valid", "2027-02-01", None),
             ("transaction", None, "2025-12-01"), ("transaction", None, "2026-09-20"),
             ("both", "2026-02-01", "2025-12-01"), ("both", "2026-02-01", "2026-01-15"),
             ("both", "2027-03-01", "2026-09-01"), ("both", "2027-03-01", "2026-09-20")]  # fmt: skip
    out, ok = [], 0
    for axis, v, t in cases:
        if axis == "valid":
            got = ids(q.query_at_time(g, "", v, time_axis="valid"))
            want = {e["doc_id"] for e in entries if valid(e, d(v))}
        elif axis == "transaction":
            got = ids(q.query_at_time(g, "", t, time_axis="transaction"))
            want = {e["doc_id"] for e in entries if known(e, d(t))}
        else:
            known_g = q.reconstruct_at_time(g, q._parse_time(t), time_axis="transaction")
            got = ids(q.query_at_time(known_g, "", v, time_axis="valid"))
            want = {e["doc_id"] for e in entries if known(e, d(t)) and valid(e, d(v))}
        same = got == want
        ok += same
        out.append({"axis": axis, "valid_at": v, "known_at": t, "agrees": same,
                    "semantica": sorted(got), "expected": sorted(want),
                    "only_semantica": sorted(got - want), "only_expected": sorted(want - got)})  # fmt: skip
        print(
            f"{axis:<11} V={v} T={t}: {'agrees' if same else 'DIFFERS'} "
            f"({len(got)} vs {len(want)}) {sorted(got ^ want)}"
        )
    print(f"{ok}/{len(cases)} agree")
    return out


if __name__ == "__main__":
    main()
