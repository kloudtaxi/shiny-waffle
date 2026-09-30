"""Item 3: a deterministic constraint check over the foundation's own `reports to` facts.

    python3 runs/2026-09-30-owm-measurements/03-constraints/check.py

It flags and never fixes. It reads Utopia's database read-only, reconstructs the graph at a record
time (a fact is live at T if recorded by T and not invalidated by T), applies the organizational
constraints of PRD-3 §5.5 / §9, and emits conflict records that keep the evidence (fact id, source
document, quote) with status REQUIRES_REVIEW. No model calls; nothing is written to Utopia.

Constraints (declared here; in BlueLeaf they would be governed OWM content):
  C1 acyclic         the reports_to graph has no cycle
  C2 one_manager     a person has at most one live manager
  C3 rank            rank(manager) >= rank(subordinate), ranks from ROLE_RANK via the person's
                     title fact ("<person> is <title>")
Coverage (reported, not a conflict): a ranked person below the top rank with no live manager.

Each snapshot is scored against the true lines in the corpus's organization_chart.md.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
DB = "utopia-db-1"
SMALL_BASE = "01a0e787-41f4-71b2-83fb-22aefb8dd650"
SCALE_BASE = "01a0ea56-61e7-79e3-99d1-e82b5d6af79a"
SMALL_CHART = LAB / "dataset/evidence/documents/organization_chart.md"
SCALE_CHART = (
    LAB
    / "runs/2026-09-28-utopia-aad5b06-scale-large/dataset/evidence/documents/organization_chart.md"
)
SNAPSHOTS = [  # (label, kb, record time or None for now, org chart)
    ("small base, as ingested", SMALL_BASE, "2026-09-28 20:00:00+00",
     SMALL_CHART),
    ("small base, now (corrected + curated)", SMALL_BASE, None,
     SMALL_CHART),
    ("scale base, as ingested (before curation)", SCALE_BASE, "2026-09-29 13:40:00+00",
     SCALE_CHART),
    ("scale base, now (curated)", SCALE_BASE, None,
     SCALE_CHART),
]  # fmt: skip
# The declared rank table. Titles seen in the foundation, lower-cased.
ROLE_RANK = {
    "enterprise account executive": 1,
    "sales engineer": 1,
    "sales operations analyst": 1,
    "customer success manager": 1,
    "accounts receivable specialist": 1,
    "finance manager": 1,
    "vp sales": 2,
    "director of finance": 2,
    "chief revenue officer": 3,
}
TOP_RANK = 3


def sql(query: str) -> list[list[str]]:
    cmd = ["docker", "exec", DB, "psql", "-U", "utopia", "-d", "utopia", "-At", "-F", "\t"]
    out = subprocess.run([*cmd, "-c", query], capture_output=True, text=True, check=True).stdout
    return [line.split("\t") for line in out.splitlines() if line.strip()]


def live(alias: str, at: str | None) -> str:
    if at is None:
        return f"{alias}.invalidated_at is null"
    return (
        f"{alias}.recorded_at <= '{at}' and "
        f"({alias}.invalidated_at is null or {alias}.invalidated_at > '{at}')"
    )


def load(kb: str, at: str | None) -> tuple[list[dict[str, str]], dict[str, str]]:
    edges = [
        {"fact_id": r[0], "subject": r[1], "manager": r[2], "doc": r[3], "quote": r[4]}
        for r in sql(
            "select f.id, s.canonical_name, o.canonical_name, "
            "coalesce((select d.filename from fact_evidence fe join documents d "
            "  on d.id = fe.document_id where fe.fact_id = f.id limit 1), ''), "
            "coalesce((select left(replace(fe.quote, E'\\n', ' '), 140) from fact_evidence fe "
            "  where fe.fact_id = f.id limit 1), '') "
            "from facts f join entities s on s.id = f.subject_id "
            "join entities o on o.id = f.object_id "
            f"where f.kb_id = '{kb}' and f.layer = 'open' and f.phrase ilike 'reports to' "
            f"and {live('f', at)} order by 2, 3"
        )
    ]
    titles: dict[str, str] = {}
    for name, title in sql(
        "select s.canonical_name, lower(coalesce(o.canonical_name, f.object_value->>'value')) "
        "from facts f join entities s on s.id = f.subject_id "
        "left join entities o on o.id = f.object_id "
        f"where f.kb_id = '{kb}' and f.layer = 'open' and f.phrase = 'is' and {live('f', at)}"
    ):
        if title in ROLE_RANK:
            titles.setdefault(name, title)
    return edges, titles


def true_pairs(org_chart: Path) -> set[tuple[str, str]]:
    stack: list[tuple[int, str]] = []
    pairs = set()
    for line in org_chart.read_text().splitlines():
        m = re.match(r"^(\s*)- \*\*(.+?)\*\*", line)
        if not m:
            continue
        depth, name = len(m.group(1)), m.group(2)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if stack:
            pairs.add((name, stack[-1][1]))
        stack.append((depth, name))
    return pairs


def check(edges: list[dict[str, str]], titles: dict[str, str]) -> dict[str, Any]:
    conflicts: list[dict[str, Any]] = []
    managers: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        managers[e["subject"]].add(e["manager"])
    # C1: cycles (DFS over person -> manager)
    seen_cycles: set[frozenset[str]] = set()
    for start in list(managers):
        path: list[str] = []
        node = start
        while node in managers and node not in path:
            path.append(node)
            node = sorted(managers[node])[0]
        if node in path:
            cyc = path[path.index(node) :]
            key = frozenset(cyc)
            if key not in seen_cycles:
                seen_cycles.add(key)
                conflicts.append({"constraint": "C1 acyclic", "people": cyc,
                                  "status": "REQUIRES_REVIEW"})  # fmt: skip
    # C2: at most one live manager
    for person, ms in managers.items():
        if len(ms) > 1:
            conflicts.append({"constraint": "C2 one_manager", "people": [person, *sorted(ms)],
                              "status": "REQUIRES_REVIEW"})  # fmt: skip
    # C3: rank(manager) >= rank(subordinate)
    for e in edges:
        ts, tm = titles.get(e["subject"]), titles.get(e["manager"])
        if ts and tm and ROLE_RANK[tm] < ROLE_RANK[ts]:
            conflicts.append({
                "constraint": "C3 rank",
                "fact_id": e["fact_id"],
                "claim": f"{e['subject']} ({ts}) reports to {e['manager']} ({tm})",
                "evidence": {"document": e["doc"], "quote": e["quote"]},
                "status": "REQUIRES_REVIEW",
            })  # fmt: skip
    missing = sorted(p for p, t in titles.items() if ROLE_RANK[t] < TOP_RANK and p not in managers)
    return {"conflicts": conflicts, "no_manager": missing}


def main() -> None:
    report: list[dict[str, Any]] = []
    rows = ["| Snapshot | reports_to edges | correct | inverted | other | conflicts (C1/C2/C3) | "
            "defective edges flagged | correct edges flagged | "
            "people with a title but no manager |",
            "|---|---|---|---|---|---|---|---|---|"]  # fmt: skip
    for label, kb, at, chart in SNAPSHOTS:
        edges, titles = load(kb, at)
        truth = true_pairs(chart)
        result = check(edges, titles)
        flagged = {c["fact_id"] for c in result["conflicts"] if "fact_id" in c}
        cyc_people = {p for c in result["conflicts"] if c["constraint"] != "C3 rank"
                      for p in c["people"]}  # fmt: skip
        kinds = {"correct": 0, "inverted": 0, "other": 0}
        defective = defective_flagged = correct_flagged = 0
        for e in edges:
            pair = (e["subject"], e["manager"])
            kind = ("correct" if pair in truth else
                    "inverted" if (e["manager"], e["subject"]) in truth else "other")  # fmt: skip
            kinds[kind] += 1
            hit = e["fact_id"] in flagged or e["subject"] in cyc_people
            if kind == "correct":
                correct_flagged += hit
            else:
                defective += 1
                defective_flagged += hit
            e["truth"] = kind
            e["flagged"] = hit
        by_c = {k: sum(c["constraint"].startswith(k) for c in result["conflicts"])
                for k in ("C1", "C2", "C3")}  # fmt: skip
        rows.append(
            f"| {label} | {len(edges)} | {kinds['correct']} | {kinds['inverted']} | "
            f"{kinds['other']} | {by_c['C1']}/{by_c['C2']}/{by_c['C3']} | "
            f"{defective_flagged}/{defective} | {correct_flagged}/{kinds['correct']} | "
            f"{len(result['no_manager'])} of {len(titles)} titled |"
        )
        report.append({"snapshot": label, "kb": kb, "record_time": at, "titled_people": titles,
                       "edges": edges, **result})  # fmt: skip
    (HERE / "results.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    (HERE / "table.md").write_text("\n".join(rows) + "\n")
    print("\n".join(rows))
    first = next(r for r in report if r["conflicts"])
    print("\nexample conflict record:", json.dumps(first["conflicts"][0], ensure_ascii=False))


if __name__ == "__main__":
    main()
