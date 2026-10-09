"""Semantica 0.7.0's DuplicateDetector on I2's labelled identity pairs (`plan.md`).

    <scratchpad>/kfenv/bin/python runs/2026-10-09-semantica-dedup/dedup.py

No model calls. Each pair is decided by the library at its defaults
(`detect_duplicates([a, b])`); the sweep re-applies its rule (similarity >= t and confidence >= 0.6)
to the similarity and confidence the library computes, checked equal to the library at t = 0.7.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from semantica.deduplication.duplicate_detector import DuplicateDetector

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
I2 = LAB / "runs/2026-10-02-jev-probe/i2/local"
KBS = {"base": "pairs-base.jsonl", "missing-contract": "pairs-missing-contract.jsonl"}
KINDS = [(r"so-\d+", "order"), (r"dr-\d+", "request"), (r"crm-\d+", "customer"),
         (r"c-\d+", "customer"), (r"emp-\d+", "employee"), (r"prod-\d+", "product")]  # fmt: skip
SWEEP = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]


def id_kind(name: str) -> str | None:
    s = name.strip().lower()
    return next((k for pat, k in KINDS if re.match(pat, s)), None)


def entity(side: dict[str, Any], eid: str, typed: bool) -> dict[str, Any]:
    props: dict[str, str] = {}
    for f in side.get("facts") or []:
        m = re.match(r"\s*(.+?)\s*[→←]\s*(.+?)\s*(?:\(.*\))?\s*$", str(f))
        if m:
            props[m.group(1)] = m.group(2)
    t = side.get("type")
    kind = id_kind(side["name"]) if typed else (None if t in (None, "", "untyped") else t)
    e = {"id": eid, "name": side["name"], "aliases": side.get("also_known_as") or [],
         "properties": props}  # fmt: skip
    if kind:
        e["type"] = kind
    return e


def main() -> None:
    det = DuplicateDetector(similarity_threshold=0.7, confidence_threshold=0.6)
    report: dict[str, Any] = {}
    for kb, fname in KBS.items():
        pairs = [json.loads(x) for x in (I2 / fname).read_text().splitlines()]
        for arm, typed in (("D0", False), ("D1", True)):
            c: Counter[str] = Counter()
            scored = []
            for i, p in enumerate(pairs):
                a = entity(p["left"], f"a{i}", typed)
                b = entity(p["right"], f"b{i}", typed)
                lib = bool(det.detect_duplicates([a, b]))
                sim = det.similarity_calculator.calculate_similarity(a, b)
                s = float(getattr(sim, "score", sim))
                conf = det._create_duplicate_candidate(a, b, s).confidence
                mine = s >= 0.7 and conf >= 0.6
                c["rule_mismatch"] += lib != mine
                c["merge"] += lib
                c["false_merge"] += lib and p["label"] == "different"
                c["missed"] += (not lib) and p["label"] == "same"
                scored.append((s, conf, p["label"]))
            sweep = {}
            for t in SWEEP:
                fm = sum(s >= t and conf >= 0.6 and lab == "different" for s, conf, lab in scored)
                mm = sum(not (s >= t and conf >= 0.6) and lab == "same" for s, conf, lab in scored)
                sweep[str(t)] = {"false_merges": fm, "missed": mm}
            report[f"{kb}/{arm}"] = {"pairs": len(pairs), "same": sum(p["label"] == "same"
                                                                       for p in pairs),
                                     **dict(c), "sweep": sweep}  # fmt: skip
            print(kb, arm, dict(c))
            print("   sweep", sweep)
    (HERE / "results.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
