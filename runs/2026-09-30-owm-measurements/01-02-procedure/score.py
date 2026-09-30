"""Score items 1 + 2 (T1: v1 via tool, T2: v2 via tool) with the fixed rule, and compare.

    python3 runs/2026-09-30-owm-measurements/01-02-procedure/score.py

The rule is `../../2026-09-28-utopia-aad5b06/procedure/score.py`'s (imported, unchanged). For each
answer it also records whether the reader called the stand-in's `get_procedure` (the uptake the
pre-registration asked for), plus turns and cost. The comparison baseline is the same reader (B1n,
uncurated graph) with the v1 procedure **in the system prompt**:
`b1/scores-uncurated-nochanges.json`
(S01–S05) and `heldout/scores-b1n-uncurated.json` (S09–S14).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(LAB / "runs/2026-09-28-utopia-aad5b06/procedure"))
import score as scorer  # noqa: E402

SCALE = LAB / "runs/2026-09-28-utopia-aad5b06-scale-large"
SCENARIOS = ["S01", "S02", "S03", "S04", "S05"] + [f"S{n:02d}" for n in range(9, 21)]
BASELINE = [
    SCALE / "b1/scores-uncurated-nochanges.json",
    SCALE / "heldout/scores-b1n-uncurated.json",
]


def tool_calls(jsonl: Path) -> list[str]:
    names = []
    for line in jsonl.read_text().splitlines():
        if not line.startswith("{"):
            continue
        msg = json.loads(line).get("message")
        if isinstance(msg, dict) and isinstance(msg.get("content"), list):
            names += [
                b["name"]
                for b in msg["content"]
                if isinstance(b, dict) and b.get("type") == "tool_use"
            ]
    return names


def run_meta(md: Path) -> tuple[int, float]:
    t = md.read_text()
    turns = re.search(r"Turns: (\d+)", t)
    cost = re.search(r"cost: ([\d.]+)", t)
    return (int(turns.group(1)) if turns else 0, float(cost.group(1)) if cost else 0.0)


def score_arm(arm: str) -> dict[str, Any]:
    exp = scorer.expected()
    report: dict[str, Any] = {}
    for n in (1, 2, 3):
        run = HERE / arm / f"r{n}" / "B1n"
        rows = {}
        for sid in SCENARIOS:
            jsonl = run / f"{sid}.jsonl"
            if not jsonl.exists():
                rows[sid] = {"grade": "missing"}
                continue
            got = scorer.decision(scorer.result_text(jsonl))
            calls = tool_calls(jsonl)
            turns, cost = run_meta(run / f"{sid}.md")
            rows[sid] = {
                "expected": exp[sid],
                "got": got,
                **scorer.score(sid, got, exp[sid]),
                "called_get_procedure": any(c.endswith("__get_procedure") for c in calls),
                "turns": turns,
                "cost_usd": cost,
            }
        report[str(run.relative_to(LAB))] = rows
    (HERE / f"scores-{arm}.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False) + "\n"
    )
    return report


def marks(rows_by_run: list[dict[str, Any]], sid: str) -> str:
    out = ""
    for rows in rows_by_run:
        g = rows.get(sid, {}).get("grade")
        out += {"pass": "✓", "partial": "~", "fail": "✗"}.get(g or "", "·")
    return out


def main() -> None:
    arms = {arm: score_arm(arm) for arm in ("T1", "T2")}
    base: dict[str, list[dict[str, Any]]] = {}
    for f in BASELINE:
        for run, rows in json.loads(f.read_text()).items():
            base.setdefault(run.split("/")[-2], []).append(rows)
    base_runs = [
        {k: v for part in base.get(r, []) for k, v in part.items()} for r in ("r1", "r2", "r3")
    ]
    lines = [
        "| Scenario | expected | v1 in prompt (baseline) | T1: v1 via tool | T2: v2 via tool |",
        "|---|---|---|---|---|",
    ]
    exp = scorer.expected()
    tot = {"base": 0, "T1": 0, "T2": 0}
    for sid in SCENARIOS:
        b = marks(base_runs, sid) if sid <= "S14" else "—"
        t1 = marks(list(arms["T1"].values()), sid)
        t2 = marks(list(arms["T2"].values()), sid)
        tot["base"] += b.count("✓")
        tot["T1"] += t1.count("✓")
        tot["T2"] += t2.count("✓")
        lines.append(f"| {sid} | {exp[sid]['outcome']} | {b} | {t1} | {t2} |")
    lines.append(
        f"| **passes** | | **{tot['base']}/33** | **{tot['T1']}/51** | **{tot['T2']}/51** |"
    )
    for arm, rep in arms.items():
        rows = [r for run in rep.values() for r in run.values() if "turns" in r]
        called = sum(r["called_get_procedure"] for r in rows)
        cost = sum(r["cost_usd"] for r in rows)
        turns = [r["turns"] for r in rows]
        lines.append(
            f"\n{arm}: get_procedure called in {called}/{len(rows)} answers · "
            f"turns {min(turns)}–{max(turns)} · cost ${cost:.2f}"
        )
    print("\n".join(lines))
    (HERE / "table.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
