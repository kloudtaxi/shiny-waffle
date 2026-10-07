"""One-time seed: `tracker/builds/<build>.yaml` into the ledger's `build` collection.

    python3 tracker/seed_build.py tracker/builds/blueleaf-mcp.yaml OUT_DIR

Writes one JSON file per document (`OUT_DIR/<id>.json`): the build's decisions (`D-n`) and tasks
(`B-nn`). Claude then writes them into the artifact's database with one `ArtifactData` batch.
After that the ledger is the source of truth: statuses, choices, evidence and updates are made on
the page, or by Claude with `ArtifactData` `update` pinned to the version it read, appending to
`log`. **Never re-run this over a live ledger:** it would overwrite the user's choices and the
builders' evidence.

A decision document holds `kind: decision`, `build`, `order`, `id`, `title`, `question`,
`options` ([{key, label, text}]), `recommended`, `recommendation`, `blocks` (task ids),
`plan_ref`, `choice` (null until the user decides) and `log`.

A task document holds `kind: task`, `build`, `order`, `id`, `phase`, `phase_title`, `title`,
`plan_ref`, `owner`, `files`, `test_first`, `prove`, `spec_tests`, `depends_on`, `decisions`,
`status` (todo, doing, review, done or blocked), `status_note`, `evidence` ({commit, ci}) and
`log`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

CREATED = "2026-10-07T00:00:00Z"


def main() -> None:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    data = yaml.safe_load(src.read_text())
    log = ["git", "log", "-1", "--format=%h", "--", str(src)]
    sha = subprocess.run(log, capture_output=True, text=True).stdout.strip() or "uncommitted"
    note = f"Created from `{src.as_posix()}` ({sha}), for the plan `{data['plan']}`."
    docs: list[dict[str, Any]] = []
    for n, d in enumerate(data["decisions"], 1):
        docs.append({"kind": "decision", "build": data["build"], "order": n, "id": d["id"],
                     "title": d["title"], "question": d["question"], "options": d["options"],
                     "recommended": d["recommended"], "recommendation": d["recommendation"],
                     "blocks": d.get("blocks", []), "plan_ref": d.get("plan_ref", ""),
                     "choice": None, "updated_at": CREATED,
                     "log": [{"at": CREATED, "by": "Claude", "text": note}]})  # fmt: skip
    for n, t in enumerate(data["tasks"], 1):
        docs.append({"kind": "task", "build": data["build"], "order": 100 + n, "id": t["id"],
                     "phase": t["phase"], "phase_title": data["phases"][t["phase"]],
                     "title": t["title"], "plan_ref": t.get("plan_ref", ""),
                     "owner": t.get("owner", "builder"), "files": t.get("files", []),
                     "test_first": t.get("test_first", ""), "prove": t.get("prove", ""),
                     "spec_tests": t.get("spec_tests", []), "depends_on": t.get("depends_on", []),
                     "decisions": t.get("decisions", []), "status": "todo", "status_note": "",
                     "evidence": {"commit": None, "ci": None}, "updated_at": CREATED,
                     "log": [{"at": CREATED, "by": "Claude", "text": note}]})  # fmt: skip
    ids = [d["id"] for d in docs]
    known = set(ids)
    for d in docs:  # every reference must name a document in this build
        refs = d.get("blocks", []) + d.get("depends_on", []) + d.get("decisions", [])
        missing = [r for r in refs if r not in known]
        if missing:
            sys.exit(f"{d['id']}: unknown references {missing}")
    if len(ids) != len(known):
        sys.exit("duplicate ids")
    out.mkdir(parents=True, exist_ok=True)
    for d in docs:
        (out / f"{d['id']}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(docs)} documents -> {out}")


if __name__ == "__main__":
    main()
