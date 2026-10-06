"""G-16, A3: the 41 human-graded answers under the rule (`plan.md`). Reads exported Ledger docs;
writes nothing to the Ledger.

    uv run python runs/2026-10-06-rubric-agreement/graded.py GRADES_DIR ANSWERS_DIR
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
s = importlib.util.spec_from_file_location("detect", HERE / "detect.py")
assert s and s.loader
detect = importlib.util.module_from_spec(s)
s.loader.exec_module(detect)


def main() -> None:
    gdir, adir = Path(sys.argv[1]), Path(sys.argv[2])
    rows = []
    for g in sorted(gdir.glob("*.json")):
        grade = json.loads(g.read_text())
        grade = grade.get("data", grade)
        a = json.loads((adir / g.name).read_text())
        a = a.get("data", a)
        text = str((a.get("outputs") or {}).get("answer") or "")
        found = detect.BLOCK.findall(text)
        block = None
        if found:
            try:
                block = json.loads(found[-1])
            except json.JSONDecodeError:
                block = None
        outcome = str((block or {}).get("outcome", "")).upper() or None
        prose = detect.BLOCK.sub("", text)
        flag_a = sorted({x[:90] for x in detect.strings(block or {}) if detect.COND.search(x)})
        flag_b = sorted({m.group(0) for m in detect.HOLD.finditer(prose)})
        flagged = outcome in detect.APPROVALS and bool(flag_a or flag_b)
        rows.append({"answer": grade["answer_id"], "user_overall": grade.get("overall"),
                     "user_outcome": (grade.get("checks") or {}).get("outcome"),
                     "block_outcome": outcome,
                     "expected": (a.get("expectations") or {}).get("expected"),
                     "flagged": flagged, "block_conditions": flag_a, "prose_holds": flag_b,
                     "note": grade.get("note", "")})  # fmt: skip
    (HERE / "graded-41.json").write_text(json.dumps(rows, indent=1) + "\n")
    for r in rows:
        mark = "FLAG" if r["flagged"] else "    "
        print(f"{mark} {r['answer'][-40:]:40} user {r['user_overall']:8} block {r['block_outcome']} "
              f"exp {r['expected']}")


if __name__ == "__main__":
    main()
