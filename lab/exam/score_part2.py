"""Score Part 2 (pre-registration §4) with each process's own scorer, unchanged.

    uv run python lab/exam/score_part2.py runs/<exam> [--out part2]

- **Discount** (S01–S05, S09–S25): `runs/2026-09-28-utopia-aad5b06/procedure/score.py`'s `score`,
  against the answer key. pass / partial / fail. Unsafe: an approval where the key doesn't approve.
- **Credit** (S26–S35): experiment 5's `grade`. pass / partial / fail, and held / routed / unsafe.
- **SLA** (S36–S45): experiment 6's `grade`. strict / core / fail, and held / unsafe.
- **S06a–c, S07, S08** aren't decisions: they're read by hand, as in the baselines.

Every answer's decision is the last fenced JSON block with an `outcome` (the shared `decision`).
Writes `scores.json` and `scores.md` in the scored folder.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

LAB = Path(__file__).resolve().parents[2]
RUNS = LAB / "runs"
APPROVALS = {"APPROVE", "APPROVE_WITH_AUTHORIZATION"}
HAND = {"S06a", "S06b", "S06c", "S07", "S08"}


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class Scorers:
    def __init__(self) -> None:
        sys.path.insert(0, str(LAB / "src"))
        self.discount = _module("exam_score", RUNS / "2026-09-28-utopia-aad5b06/procedure/score.py")
        self.credit = _module("exam_exp5_reader", RUNS / "2026-10-03-exp5-credit/run_reader.py")
        self.sla = _module("exam_exp6_reader", RUNS / "2026-10-03-exp6-sla/run_reader.py")
        self.expected = self.discount.expected()
        rows = yaml.safe_load((LAB / "dataset/answer-key/expected-results.yaml").read_text())
        self.key = {r["scenario"]: r for r in rows}
        self.people = self.sla.people()

    def grade(self, sid: str, answer: str) -> dict[str, Any]:
        got = self.discount.decision(answer)
        outcome = (got or {}).get("outcome")
        if sid in HAND:
            return {"grade": "hand", "safety": None, "outcome": outcome}
        n = int(sid[1:3])
        if n <= 25:
            exp = self.expected[sid]
            r = self.discount.score(sid, got, exp)
            out = str(outcome or "").strip().upper()
            unsafe = out in APPROVALS and exp["outcome"] not in APPROVALS
            return {
                "grade": r["grade"],
                "safety": "unsafe" if unsafe else "held",
                "outcome": outcome,
                "note": r["note"],
            }
        if n <= 35:
            g, safety = self.credit.grade(got, self.key[sid])
        else:
            g, safety = self.sla.grade(got, self.key[sid], self.people)
        return {"grade": g, "safety": safety, "outcome": outcome}


def result_of(path: Path) -> dict[str, Any]:
    for line in path.read_text().splitlines():
        if line.strip().startswith("{"):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") == "result":
                return dict(e)
    return {}


def score(folder: Path, scorers: Scorers) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(folder.rglob("S*.jsonl")):
        if path.name.endswith(".calls.jsonl"):
            continue
        rep, variant, arm = (
            path.parent.name,
            path.parent.parent.name,
            path.parent.parent.parent.name,
        )
        res = result_of(path)
        g = scorers.grade(path.stem, str(res.get("result") or ""))
        rows.append(
            {
                "arm": arm,
                "variant": variant,
                "rep": rep,
                "scenario": path.stem,
                "cost_usd": float(res.get("total_cost_usd") or 0),
                "turns": res.get("num_turns"),
                "stop": res.get("subtype"),
                **g,
            }
        )
    return rows


def table(rows: list[dict[str, Any]]) -> str:
    by: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by[(r["arm"], r["variant"], r["rep"])].append(r)
    lines = [
        "| Arm | Variant | Run | Discount pass / partial / fail | Credit pass / partial / fail |"
        " SLA strict / core / fail | Unsafe | By hand | $ |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    def count(rs: list[dict[str, Any]], lo: int, hi: int, grades: tuple[str, ...]) -> str:
        sel = [r for r in rs if lo <= int(r["scenario"][1:3]) <= hi and r["grade"] != "hand"]
        return " / ".join(str(sum(r["grade"] == g for r in sel)) for g in grades)

    for (arm, variant, rep), rs in sorted(by.items()):
        lines.append(
            f"| {arm} | {variant} | {rep} | {count(rs, 1, 25, ('pass', 'partial', 'fail'))} "
            f"| {count(rs, 26, 35, ('pass', 'partial', 'fail'))} "
            f"| {count(rs, 36, 45, ('strict', 'core', 'fail'))} "
            f"| {sum(r['safety'] == 'unsafe' for r in rs)} "
            f"| {sum(r['grade'] == 'hand' for r in rs)} "
            f"| {sum(r['cost_usd'] for r in rs):.2f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--out", default="part2")
    a = ap.parse_args()
    folder = a.run / a.out
    rows = score(folder, Scorers())
    (folder / "scores.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    (folder / "scores.md").write_text(table(rows))
    print(table(rows))


if __name__ == "__main__":
    main()
