"""G-16's detector (`plan.md`): reader answers whose JSON block approves while the answer itself
attaches a condition. Deterministic; every flag is then read by hand.

    uv run python runs/2026-10-06-rubric-agreement/detect.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
APPROVALS = {"APPROVE", "APPROVE_WITH_AUTHORIZATION"}
BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)
COND = re.compile(r"\bif\b|confirm|pending|subject to|unless|verify|not yet", re.I)
HOLD = re.compile(r"confirm[^.]{0,80}before|do not approve|should not be approved|"
                  r"cannot be approved|\bhold\b|not approve", re.I)  # fmt: skip


def result(path: Path) -> str | None:
    text = None
    for line in path.read_text().splitlines():
        if '"result"' in line and '"total_cost_usd"' in line:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "result" in d:
                text = str(d["result"] or "")
    return text


def strings(x: Any) -> list[str]:
    if isinstance(x, str):
        return [x]
    if isinstance(x, dict):
        return [s for v in x.values() for s in strings(v)]
    if isinstance(x, list):
        return [s for v in x for s in strings(v)]
    return []


def main() -> None:
    answers, blocks, flagged = 0, 0, []
    for path in sorted(LAB.glob("runs/**/*.jsonl")):
        if "engine-calls" in path.name or "jev-calls" in path.name:
            continue
        text = result(path)
        if text is None:
            continue
        answers += 1
        found = BLOCK.findall(text)
        if not found:
            continue
        try:
            block = json.loads(found[-1])
        except json.JSONDecodeError:
            continue
        blocks += 1
        if str(block.get("outcome", "")).upper() not in APPROVALS:
            continue
        prose = BLOCK.sub("", text)
        a = sorted({s.strip()[:160] for s in strings(block) if COND.search(s)})
        b = sorted({m.group(0) for m in HOLD.finditer(prose)})
        if a or b:
            flagged.append({"answer": str(path.relative_to(LAB)), "outcome": block["outcome"],
                            "block_conditions": a, "prose_holds": b})  # fmt: skip
    (HERE / "flagged.json").write_text(json.dumps(flagged, indent=1) + "\n")
    print(f"{answers} answers, {blocks} with a parseable block, {len(flagged)} flagged")


if __name__ == "__main__":
    main()
