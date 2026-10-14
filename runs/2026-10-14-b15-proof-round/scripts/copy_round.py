"""Copy a finished live round from `.owm-rounds/` into this run folder (spec §8).

    python3 runs/2026-10-14-b15-proof-round/scripts/copy_round.py <round_id> <sub> <sha>

`<sub>` is `rounds` (the counted round) or `shakedown` (the declared trial).

Writes `<sub>/<round_id>.json` (runs embedded) and `<sub>/<round_id>/` (each run's transcript and
call log). In the copy, `source` names the committed file, `pre_registration` is the notes'
commit, and each run's `transcript` and `tool_calls` point at the copied files, relative to this
folder. The live round is not changed. Refuses a round that is still running.

`REDACT` (env, comma-separated) lists strings to replace with `[operator identity]` in every
copied file: Claude Code shows the agent the operator's account identity, and the repo is public.
The strings themselves are never written to this repo.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
LAB = HERE.parents[1]
LIVE = LAB / ".owm-rounds" / "rounds"
REDACT = [x for x in os.environ.get("REDACT", "").split(",") if x]


def scrub(text: str) -> str:
    for x in REDACT:
        text = text.replace(x, "[operator identity]")
    return text


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
                (dest / name).write_text(scrub((src / name).read_text(errors="replace")))
                run[key] = f"{sub}/{round_id}/{name}"
    out = HERE / sub / f"{round_id}.json"
    out.write_text(scrub(json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False)) + "\n")
    print("wrote", out.relative_to(LAB), "and", dest.relative_to(LAB))


if __name__ == "__main__":
    main()
