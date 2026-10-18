"""The exam's tables: Part 1 and Part 2 side by side, per arm (pre-registration §§3–4).

    uv run python lab/exam/summarize.py runs/<exam>

Reads what the scorers wrote (`part1/<arm>/<corpus>.score.json` and `.judge.json`,
`part2/scores.json`, each answer's `.calls.jsonl`) and prints Markdown. It decides nothing:
- **C2's three runs** are given as each run's count and their range. The pre-registered noise rule
  is applied as written: a difference smaller than the spread of the three C2 runs is no difference.
- **The gold-evidence ceilings** (experiments 5 and 6, every document in the message) are printed
  beside credit and SLA: credit 27/30, SLA 16/20 strict and 20/20 core.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

ARMS = ("b20", "b20-ids-off", "today")
CORPORA = ("base", "missing-contract-evidence", "missing-guarantee-evidence")
SHORT = {
    "base": "base",
    "missing-contract-evidence": "no contract",
    "missing-guarantee-evidence": "no guarantee",
}
TEXT = {"search", "list_documents", "read_passages"}


def part1(run: Path) -> str:
    out = [
        "| Arm | Base | Facts | Evidence | Exact (verified) | U-31 (P3a) | False merges (P3b) "
        "| SLA data held (P5, of 76) | Day only |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for arm in ARMS:
        for c in CORPORA:
            s = json.loads((run / "part1" / arm / f"{c}.score.json").read_text())
            p1, p3a, p3b, p5 = s["p1"], s["p3a"], s["p3b"], s["p5"]
            exact = p1["by_alignment"].get("exact", 0)
            out.append(
                f"| {arm} | {SHORT[c]} | {p1['facts']:,} | {p1['evidence']:,} "
                f"| {exact:,} ({p1['exact_share']:.0%}; {p1['exact_verified']:,}) "
                f"| {p3a['grade']} | {len(p3b['false_merges'])} | {p5['held']} "
                f"| {p5['date_only']} |"
            )
    out += [
        "",
        "| Arm | Base | P2 stated / partly / not (26) | P2 dated, x-holds (4) "
        "| P4 stated / partly / not (4) | P4, x-holds | U-31 facts F01–F03 |",
        "|---|---|---|---|---|---|---|",
    ]
    for arm in ARMS:
        for c in CORPORA:
            j = json.loads((run / "part1" / arm / f"{c}.judge.json").read_text())
            t = Counter((r["part"], r["reading"], r["verdict"]) for r in j["readings"])

            def three(part: str, reading: str, t: Counter[tuple[str, str, str]] = t) -> str:
                return " / ".join(
                    str(t[(part, reading, v)]) for v in ("stated", "partly", "not_stated")
                )

            u31 = ", ".join(
                r["verdict"] for r in j["readings"] if r["u31"] and r["reading"] == "stated"
            )
            out.append(
                f"| {arm} | {SHORT[c]} | {three('p2', 'stated')} | {three('p2', 'x-holds')} "
                f"| {three('p4', 'stated')} | {three('p4', 'x-holds')} | {u31} |"
            )
    return "\n".join(out)


def _n(rows: list[dict[str, Any]], lo: int, hi: int, grade: str) -> int:
    return sum(
        lo <= int(r["scenario"][1:3]) <= hi and r["grade"] == grade
        for r in rows
        if r["grade"] != "hand"
    )


def part2(run: Path) -> str:
    rows = json.loads((run / "part2" / "scores.json").read_text())
    by: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by[(r["arm"], r["variant"], r["rep"])].append(r)
    measures: dict[str, Callable[[list[dict[str, Any]]], float]] = {
        "Discount pass (of 22)": lambda rs: _n(rs, 1, 25, "pass"),
        "Credit pass (of 10)": lambda rs: _n(rs, 26, 35, "pass"),
        "SLA strict (of 10)": lambda rs: _n(rs, 36, 45, "strict"),
        "SLA core or strict (of 10)": lambda rs: _n(rs, 36, 45, "strict") + _n(rs, 36, 45, "core"),
        "Unsafe (of 42)": lambda rs: sum(r["safety"] == "unsafe" for r in rs),
        "Out of turns": lambda rs: sum(r["stop"] == "error_max_turns" for r in rs),
        "Cost ($)": lambda rs: round(sum(r["cost_usd"] for r in rs), 2),
    }
    out = [
        "| Measure | " + " | ".join(f"{a} C1" for a in ARMS) + " | "
        + " | ".join(f"{a} C2 (r1, r2, r3)" for a in ARMS) + " |",
        "|---|" + "---|" * (2 * len(ARMS)),
    ]  # fmt: skip
    for name, f in measures.items():
        c1 = [str(f(by[(a, "C1", "r1")])) for a in ARMS]
        c2 = []
        for a in ARMS:
            vals = [f(by[(a, "C2", r)]) for r in ("r1", "r2", "r3")]
            c2.append(", ".join(str(v) for v in vals))
        out.append(f"| {name} | " + " | ".join(c1) + " | " + " | ".join(c2) + " |")
    n = {k: len(v) for k, v in by.items()}
    out += ["", f"Answers per run: {sorted(n.items())}"]
    return "\n".join(out)


def tools(run: Path) -> str:
    out = [
        "| Arm | Variant | Calls per answer | Text-tool share | Errors (non-200) | Top tools |",
        "|---|---|---|---|---|---|",
    ]
    for arm in ARMS:
        for variant in ("C1", "C2"):
            calls: list[dict[str, Any]] = []
            answers = 0
            for p in (run / "part2" / arm / variant).rglob("S*.calls.jsonl"):
                if ".infra-error-" in p.name:
                    continue
                answers += 1
                calls += [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
            used = Counter(c["tool"] for c in calls)
            text = sum(v for k, v in used.items() if k in TEXT)
            errs = sum(1 for c in calls if c.get("status") not in (200, None))
            top = ", ".join(f"{k} {v}" for k, v in used.most_common(4))
            out.append(
                f"| {arm} | {variant} | {len(calls) / max(answers, 1):.1f} "
                f"| {text / max(len(calls), 1):.0%} | {errs} | {top} |"
            )
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(prog="exam-summarize")
    ap.add_argument("run", type=Path)
    a = ap.parse_args()
    print("## Part 1\n\n" + part1(a.run) + "\n\n## Part 2\n\n" + part2(a.run))
    print("\n## Tool use\n\n" + tools(a.run))


if __name__ == "__main__":
    main()
