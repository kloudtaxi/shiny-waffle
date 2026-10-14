"""Copy a finished live round from `.owm-rounds/` into this run folder (spec §8).

    python3 runs/2026-10-14-b15-proof-round/scripts/copy_round.py <round_id> <rounds|shakedown> <sha>

Writes `<sub>/<round_id>.json` (runs embedded) and `<sub>/<round_id>/` (each run's transcript and
call log). In the copy, `source` names the committed file, `pre_registration` is the notes'
commit, and each run's `transcript` and `tool_calls` point at the copied files, relative to this
folder. The live round is not changed. Refuses a round that is still running.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
LAB = HERE.parents[1]
LIVE = LAB / ".owm-rounds" / "rounds"


def main() -> None:
    round_id, sub, sha = sys.argv[1], sys.argv[2], sys.argv[3]
    assert sub in ("rounds", "shakedown"), sub
    src = LIVE / round_id
    r = json.loads((src / "round.json").read_text())
    if r["status"] in ("queued", "running"):
        sys.exit(f"{round_id} is still {r['status']}")
    dest = HERE / sub / round_id
    dest.mkdir(parents=True, exist_ok=True)
    folder = HERE.relative_to(LAB)
    source = f"{folder}/{sub}/{round_id}.json"
    r["source"], r["pre_registration"] = source, sha
    for run in r["runs"]:
        run["source"], run["pre_registration"] = source, sha
        for key in ("transcript", "tool_calls"):
            if run.get(key):
                name = Path(run[key]).name
                shutil.copyfile(src / name, dest / name)
                run[key] = f"{sub}/{round_id}/{name}"
    out = HERE / sub / f"{round_id}.json"
    out.write_text(json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print("wrote", out.relative_to(LAB), "and", dest.relative_to(LAB))


if __name__ == "__main__":
    main()
