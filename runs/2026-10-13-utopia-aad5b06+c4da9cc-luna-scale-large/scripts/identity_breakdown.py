"""Break `identity.py`'s missed merges and routed pairs down by entity kind. Added after the run.

    uv run python "runs/2026-10-13-utopia-aad5b06+c4da9cc-luna-scale-large/scripts/identity_breakdown.py"

Same labelling and mapping as `identity.py` (it imports them). Writes `identity-breakdown.json`
next to this folder's notes.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import identity as idm

bp = idm.bp
HERE = Path(__file__).resolve().parent


def main() -> None:
    resolve = bp.Resolver(idm.CORPUS)
    out: dict[str, dict] = {}
    for name, kb in idm.KBS.items():
        missed: Counter[str] = Counter()
        routed: Counter[str] = Counter()
        missed_pairs = []
        for p in bp.label_all(kb, resolve):
            d = idm.utopia_call(p)
            kind = f"{p['left_obj'][0]}~{p['right_obj'][0]}"
            if d == "keep" and p["label"] == "same":
                missed[kind] += 1
                missed_pairs.append({"a": p["left_name"], "b": p["right_name"],
                                     "reason": p.get("reason"), "confidence": p.get("confidence")})
            if d == "route":
                routed[f"{kind} {p['label']}"] += 1
        out[name] = {"missed_by_kind": dict(missed), "routed_by_kind_and_label": dict(routed),
                     "missed_merges": missed_pairs}
        print(name, {k: v for k, v in out[name].items() if k != "missed_merges"})
    (HERE.parent / "identity-breakdown.json").write_text(json.dumps(out, indent=2, default=str) + "\n")


if __name__ == "__main__":
    main()
