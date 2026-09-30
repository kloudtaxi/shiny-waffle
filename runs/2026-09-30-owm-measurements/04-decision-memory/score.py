"""Score item 4 (decision memory): arms a (no memory), b (decision as a document), c (typed record).

    python3 runs/2026-09-30-owm-measurements/04-decision-memory/score.py

Rules, fixed in `prereg.md` before any run:
- M1 pass: decided = true, outcome APPROVE_WITH_AUTHORIZATION, approved_by names Michael Torres,
  policy names 2026, eligibility basis names the 15% NS-500 exception. partial: decided and outcome
  right, another field wrong. fail: anything else.
- M2 pass: decision_found = true, valid_when_made = true, approved_by names Michael Torres,
  approver_role_then is VP Sales, policy_then names 2026. partial: valid_when_made right, another
  field wrong. fail: anything else.
- M3: the lab's fixed decision rule against S21 (APPROVE_WITH_AUTHORIZATION, eligible, not
  authorized, approver David Morgan, CRO). Reusing the 2026 approver is a fail.
Also recorded per answer: turns, cost, and reads of source documents (search_chunks / get_document).
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

ARMS = {"a": "no memory", "b": "decision as a document in Utopia", "c": "typed decision record"}


def last_json(text: str) -> dict[str, Any] | None:
    blocks = re.findall(r"```json\n(.*?)```", text, re.S)
    for b in reversed(blocks):
        try:
            d = json.loads(b)
        except json.JSONDecodeError:
            continue
        if isinstance(d, dict):
            return d
    return None


def has(v: Any, *needles: str) -> bool:
    s = str(v or "").lower()
    return all(n in s for n in needles)


def grade_m1(d: dict[str, Any] | None) -> str:
    if not d or d.get("decided") is not True or d.get("outcome") != "APPROVE_WITH_AUTHORIZATION":
        return "fail"
    ok = (
        has(d.get("approved_by"), "michael")
        and has(d.get("policy"), "2026")
        and (has(d.get("eligibility_basis"), "15") or has(d.get("eligibility_basis"), "ns500-15"))
    )
    return "pass" if ok else "partial"


def grade_m2(d: dict[str, Any] | None) -> str:
    if not d or d.get("valid_when_made") is not True:
        return "fail"
    ok = (
        d.get("decision_found") is True
        and has(d.get("approved_by"), "michael")
        and has(d.get("approver_role_then"), "vp")
        and has(d.get("policy_then"), "2026")
    )
    return "pass" if ok else "partial"


def meta(run: Path, qid: str) -> dict[str, Any]:
    md = (run / f"{qid}.md").read_text()
    turns = re.search(r"Turns: (\d+)", md)
    cost = re.search(r"cost: ([\d.]+)", md)
    reads = 0
    decision_tools = 0
    for line in (run / f"{qid}.jsonl").read_text().splitlines():
        if not line.startswith("{"):
            continue
        msg = json.loads(line).get("message")
        if isinstance(msg, dict) and isinstance(msg.get("content"), list):
            for b in msg["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    name = b["name"].split("__")[-1]
                    reads += name in {"search_chunks", "get_document"}
                    decision_tools += name in {"find_decisions", "get_decision"}
    return {
        "turns": int(turns.group(1)) if turns else 0,
        "cost_usd": float(cost.group(1)) if cost else 0.0,
        "source_reads": reads,
        "decision_tool_calls": decision_tools,
    }


def main() -> None:
    exp = scorer.expected()
    report: dict[str, Any] = {}
    lines = [
        "| Arm | M1 decided? | M2 valid when made? | M3 same request in 2027 | "
        "turns M1/M2 (mean) | source reads M1/M2 (mean) | cost |",
        "|---|---|---|---|---|---|---|",
    ]
    for arm, label in ARMS.items():
        marks = {"M1": "", "M2": "", "M3": ""}
        turns12: list[int] = []
        reads12: list[int] = []
        cost = 0.0
        for n in (1, 2, 3):
            run = HERE / arm / f"r{n}" / "B1n"
            for qid in ("M1", "M2", "M3"):
                if not (run / f"{qid}.jsonl").exists():
                    marks[qid] += "·"
                    continue
                text = scorer.result_text(run / f"{qid}.jsonl")
                m = meta(run, qid)
                cost += m["cost_usd"]
                if qid == "M3":
                    got = scorer.decision(text)
                    g = scorer.score("S21", got, exp["S21"])["grade"]
                    parsed: Any = got
                else:
                    parsed = last_json(text)
                    g = grade_m1(parsed) if qid == "M1" else grade_m2(parsed)
                    turns12.append(m["turns"])
                    reads12.append(m["source_reads"])
                marks[qid] += {"pass": "✓", "partial": "~", "fail": "✗"}[g]
                report[f"{arm}/r{n}/{qid}"] = {"grade": g, "answer": parsed, **m}
        mean = lambda xs: sum(xs) / len(xs) if xs else 0.0  # noqa: E731
        lines.append(
            f"| ({arm}) {label} | {marks['M1']} | {marks['M2']} | {marks['M3']} | "
            f"{mean(turns12):.1f} | {mean(reads12):.1f} | ${cost:.2f} |"
        )
    (HERE / "scores.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    (HERE / "table.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
