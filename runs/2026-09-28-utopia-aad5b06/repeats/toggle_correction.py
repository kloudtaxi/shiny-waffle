"""Temporarily undo the 2026-09-28 identity correction, then put it back.

    python3 runs/2026-09-28-utopia-aad5b06/repeats/toggle_correction.py state
    python3 runs/2026-09-28-utopia-aad5b06/repeats/toggle_correction.py revert --apply
    python3 runs/2026-09-28-utopia-aad5b06/repeats/toggle_correction.py reapply --apply

This exists for the pre-correction B2 repeats. The correction's 17 merges (all human, made
17:25:39-41 UTC) are reverted newest-first through Utopia's own revert route, which moves the
facts back and restores the source entity under its original id. Afterwards they are
re-applied oldest-first, as manual merges of the same source -> target ids. A human merge's
revert does not reopen reviews or wake the governance agent (governance::after_revert only
settles agent decisions).

Every write is logged to `toggle_log.jsonl`. Without `--apply` it only prints what it would
do. `state` prints the numbers to compare against the snapshots.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(LAB / "lab" / "utopia"))
import utopia  # noqa: E402

HERE = Path(__file__).resolve().parent
KBS = {
    "base": "01a0e787-41f4-71b2-83fb-22aefb8dd650",
    "missing-contract": "01a0e787-457c-7f50-a8f1-e33beb27dfb3",
}
WINDOW = ("2026-09-28 17:25:39", "2026-09-28 17:25:42")  # the correction's merges, UTC
DB = os.environ.get("UTOPIA_DB_CONTAINER", "utopia-db-1")


def sql(query: str) -> list[list[str]]:
    cmd = ["docker", "exec", DB, "psql", "-U", "utopia", "-d", "utopia", "-At", "-F", "\t"]
    out = subprocess.run([*cmd, "-c", query], capture_output=True, text=True, check=True).stdout
    return [line.split("\t") for line in out.splitlines() if line.strip()]


def correction_merges(kb: str) -> list[dict[str, str]]:
    rows = sql(
        "select m.id, m.source_id, m.target_id, s.canonical_name, t.canonical_name, "
        "m.created_at, coalesce(m.reverted_at::text, '') from entity_merges m "
        "join entities s on s.id = m.source_id join entities t on t.id = m.target_id "
        f"where m.kb_id = '{kb}' and m.merged_by is not null "
        f"and m.created_at >= '{WINDOW[0]}' and m.created_at < '{WINDOW[1]}' "
        "order by m.created_at"
    )
    keys = ("id", "source", "target", "source_name", "target_name", "created", "reverted")
    return [dict(zip(keys, r, strict=True)) for r in rows]


def state() -> None:
    for name, kb in KBS.items():
        facts, merges, ents = sql(
            f"select (select count(*) from facts where kb_id='{kb}' and invalidated_at is null), "
            f"(select count(*) from entity_merges where kb_id='{kb}' and reverted_at is null), "
            f"(select count(*) from entities where kb_id='{kb}' and merged_into is null)"
        )[0]
        cm = correction_merges(kb)
        live = sum(1 for m in cm if not m["reverted"])
        print(f"{name:17} live facts {facts} · live merges {merges} · live entities {ents} · "
              f"correction merges live {live}/{len(cm)}")  # fmt: skip


def log(rec: dict[str, object]) -> None:
    with (HERE / "toggle_log.jsonl").open("a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def revert(apply: bool) -> None:
    for name, kb in KBS.items():
        for m in reversed(correction_merges(kb)):  # newest first: undo in stack order
            if m["reverted"]:
                continue
            print(f"revert {name}: {m['source_name']} -> {m['target_name']} ({m['id']})")
            if apply:
                utopia.call("POST", f"/kbs/{kb}/merges/{m['id']}/revert")
                log({"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "op": "revert", "kb": kb, **m})


def reapply(apply: bool) -> None:
    for name, kb in KBS.items():
        for m in correction_merges(kb):  # oldest first: the original order
            if not m["reverted"]:
                continue
            print(f"re-merge {name}: {m['source_name']} -> {m['target_name']}")
            if apply:
                body = {
                    "source": m["source"],
                    "target": m["target"],
                    "rationale": "Re-applied after the pre-correction B2 repeats "
                    f"(originally merge {m['id']} at {m['created']}).",
                }
                resp = utopia.jcall("POST", f"/kbs/{kb}/entities/merge", body)
                log({"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "op": "reapply", "kb": kb,
                     "result": resp, **m})  # fmt: skip


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("cmd", choices=["state", "revert", "reapply"])
    p.add_argument("--apply", action="store_true", help="write to Utopia (default: print)")
    a = p.parse_args()
    if a.cmd == "state":
        state()
    elif a.cmd == "revert":
        revert(a.apply)
    else:
        reapply(a.apply)


if __name__ == "__main__":
    main()
