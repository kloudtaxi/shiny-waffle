"""Withdraw the scale curation from both scale KBs, and push it again afterwards.

    python3 runs/2026-09-28-utopia-aad5b06-scale-large/b1/toggle_curation.py state
    python3 runs/2026-09-28-utopia-aad5b06-scale-large/b1/toggle_curation.py withdraw --apply
    python3 runs/2026-09-28-utopia-aad5b06-scale-large/b1/toggle_curation.py reapply --apply

The B1 arm needs the scale graph without curation. At scale, curation only added facts through
the Statements source: no edge was rejected (the org chart yielded no `reports to`), so the
whole of it can be withdrawn. Withdrawal is Utopia's designed path. A tombstone push
(`deleted: true`) per curation document marks it "not in source". Then the source's
missing-cleanup deletes those documents, which retracts every fact whose only evidence they
were (record time keeps the history) and drops them from search. `reapply` pushes the same
statements again through `../curation/curate.py` and `../agreement/agreement.py`. Every push
is logged in `../curation/curation_log.jsonl`. Everything prints unless `--apply`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "curation"))
sys.path.insert(0, str(HERE.parent / "agreement"))
import agreement  # noqa: E402
import curate  # noqa: E402

utopia = curate.utopia


def external_ids(name: str) -> list[str]:
    ids = [curate.reporting(curate.KBS[name])["external_id"]]
    ids += [p["external_id"] for p in curate.PUSHES[name]]
    if name == "base":
        ids.append(agreement.PUSH["external_id"])
    return ids


def docs(kb: str) -> list[list[str]]:
    """Curation documents in this KB: filename, status, deleted?, live facts citing them."""
    return curate.sql(
        "select d.filename, d.status, (d.deleted_at is not null)::text, "
        "(select count(distinct fe.fact_id) from fact_evidence fe "
        " join facts f on f.id = fe.fact_id "
        " where fe.document_id = d.id and f.invalidated_at is null) "
        f"from documents d where d.kb_id = '{kb}' and d.filename like 'northstar-curation-%' "
        "order by d.filename, d.created_at"
    )


def live_counts(kb: str) -> str:
    facts, ents = curate.sql(
        f"select (select count(*) from facts where kb_id = '{kb}' and invalidated_at is null), "
        f"(select count(*) from entities where kb_id = '{kb}' and merged_into is null)"
    )[0]
    return f"live facts {facts}, live entities {ents}"


def cmd_state() -> None:
    for name, kb in curate.KBS.items():
        print(f"== {name}: {live_counts(kb)}")
        for fn, status, deleted, n in docs(kb):
            print(f"   {fn}  status={status} deleted={deleted} live_facts={n}")


def cmd_withdraw(apply: bool) -> None:
    for name, kb in curate.KBS.items():
        for xid in external_ids(name):
            print(f"{name}: tombstone {xid}")
            if apply:
                print("   ", curate.push(kb, {"external_id": xid, "deleted": True}))
        sid = curate.source_id(kb)
        print(f"{name}: clean up missing documents of source {sid}")
        if apply and sid:
            resp = utopia.jcall("POST", f"/kbs/{kb}/sources/{sid}/missing/cleanup")
            curate.log({"op": "cleanup-missing", "kb": kb, "source": sid, "result": resp})
            print("   ", resp)


def cmd_reapply(apply: bool) -> None:
    curate.cmd_apply(apply)
    agreement.cmd_push(apply)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("cmd", choices=["state", "withdraw", "reapply"])
    p.add_argument("--apply", action="store_true", help="write to Utopia (default: print)")
    a = p.parse_args()
    if a.cmd == "state":
        cmd_state()
    elif a.cmd == "withdraw":
        cmd_withdraw(a.apply)
    else:
        cmd_reapply(a.apply)


if __name__ == "__main__":
    main()
