"""Score Utopia governance's identity decisions on the luna scale KBs, with I2's code unchanged.

    uv run python "runs/2026-10-13-utopia-aad5b06+c4da9cc-luna-scale-large/scripts/identity.py"

Labels every agent decision on an identity review with `j4/build_pairs.py` (`label_all`, the lab
resolver over the scale corpus committed with the gpt-4o scale run) and maps Utopia's decision as
J4's `gpt_call` does. Read-only SQL. Writes `identity.json` next to this folder's notes.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(LAB / "runs/2026-10-02-jev-probe/j4"))
import build_pairs as bp  # noqa: E402

CORPUS = LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/dataset"
KBS = {"base": "01a136fa-8e1d-77c0-b01d-bfc6423990b4",
       "missing-contract": "01a136fa-a00d-7421-b90b-4ad99714585b"}  # fmt: skip


def utopia_call(r: dict) -> str:
    """J4's `gpt_call`, verbatim in effect: unsure or not applied is a route."""
    if r["action"] == "unsure" or r["status"] != "applied":
        return "route"
    return r["action"]


def main() -> None:
    resolve = bp.Resolver(CORPUS)
    out: dict[str, dict] = {}
    for name, kb in KBS.items():
        total = len(bp.decisions(kb) or [])
        pairs = bp.label_all(kb, resolve)
        c: Counter[str] = Counter()
        kinds: Counter[str] = Counter()
        false_merges = []
        for p in pairs:
            d = utopia_call(p)
            c[d] += 1
            if d == "merge" and p["label"] == "different":
                c["false_merge"] += 1
                kinds[f"{p['left_obj'][0]}~{p['right_obj'][0]}"] += 1
                false_merges.append({"a": p["left_name"], "b": p["right_name"],
                                     "reason": p.get("reason"), "confidence": p.get("confidence")})
            c["missed_merge"] += d == "keep" and p["label"] == "same"
            c["right"] += d != "route" and (d == "merge") == (p["label"] == "same")
            c["truly_same"] += p["label"] == "same"
        out[name] = {"decisions": total, "labelled": len(pairs), **dict(c),
                     "false_merge_kinds": dict(kinds), "false_merges": false_merges}
        print(name, {k: v for k, v in out[name].items() if k != "false_merges"})
    (HERE.parent / "identity.json").write_text(json.dumps(out, indent=2, default=str) + "\n")


if __name__ == "__main__":
    main()
