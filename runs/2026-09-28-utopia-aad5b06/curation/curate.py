"""Curation arm: fix the facts extraction got wrong or missed, then rerun B2.

    python3 runs/2026-09-28-utopia-aad5b06/curation/curate.py plan
    python3 runs/2026-09-28-utopia-aad5b06/curation/curate.py setup --apply
    python3 runs/2026-09-28-utopia-aad5b06/curation/curate.py pilot --apply
    python3 runs/2026-09-28-utopia-aad5b06/curation/curate.py apply --apply
    python3 runs/2026-09-28-utopia-aad5b06/curation/curate.py resolve --apply   # after processing
    python3 runs/2026-09-28-utopia-aad5b06/curation/curate.py verify

What is curated, and only from what each KB's own corpus states:

1. Reporting lines (organization_chart.md). Every `reports to` edge in both KBs is inverted
   (manager -> report). All 13 are rejected, which is a record-time retraction with no API undo.
   The correct edges are pushed for people whose names resolve to one entity. Background staff
   with duplicate entities are left without an edge: a statement naming an ambiguous entity
   makes Utopia mint a new one and queue adjudication.
2. Approval bands (pricing_policy_2025.md, pricing_policy_2026.md), as facts on the unique
   policy entities, valid for the policy's calendar year.
3. Exception values (acme_pricing_exception*.md), base KB only; the missing-contract corpus
   has no such documents, and curation must not add what the evidence lacks.

Everything goes through a Statements source: structured statements in Utopia's open contract,
parsed with no model, attached by name to existing entities. Pushes are logged to
`curation_log.jsonl`. To withdraw them, push `deleted: true` for each external_id (Utopia
marks the documents "Not in source") and delete the documents in the Library.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(LAB / "lab" / "utopia"))
import utopia  # noqa: E402

HERE = Path(__file__).resolve().parent
DB = os.environ.get("UTOPIA_DB_CONTAINER", "utopia-db-1")
KBS = {
    "base": "01a0e787-41f4-71b2-83fb-22aefb8dd650",
    "missing-contract": "01a0e787-457c-7f50-a8f1-e33beb27dfb3",
}
SOURCE_NAME = "Northstar curation (2026-09-28)"


def person(name: str) -> list[Any]:
    return [name, "person", True]


def st(subject: str, phrase: str, obj: str | None, value: str | None,
       when: str | None = None, ended: str | None = None) -> list[Any]:  # fmt: skip
    """One statement in the open contract: [quote, subject, phrase, object, value,
    qualifiers, when, ended]. The quote is null: the item is its own evidence."""
    return [None, subject, phrase, obj, value, None, when, ended]


REPORTING = {
    "external_id": "northstar-curation-reporting-lines",
    "doc_time": "2026-09-01T00:00:00Z",  # organization_chart.md: "Reporting lines as of 2026-09-01"
    "e": [
        person(n)
        for n in (
            "Sarah Chen",
            "Kelly Floyd",
            "Anthony Day",
            "Zachary Brown",
            "Michael Torres",
            "David Morgan",
            "Priya Shah",
            "Elena Novak",
        )
    ],
    "s": [
        st("Sarah Chen", "reports to", "Michael Torres", None),
        st("Kelly Floyd", "reports to", "Michael Torres", None),
        st("Anthony Day", "reports to", "Michael Torres", None),
        st("Zachary Brown", "reports to", "Michael Torres", None),
        st("Michael Torres", "reports to", "David Morgan", None),
        st("Priya Shah", "reports to", "Elena Novak", None),
    ],
    "n": [],
}
BANDS_2025 = {
    "external_id": "northstar-curation-authority-bands-2025",
    "doc_time": "2024-12-10T00:00:00Z",  # pricing_policy_2025.md created
    "e": [["Northstar Pricing Policy 2025", "policy", True]],
    "s": [
        st(
            "Northstar Pricing Policy 2025",
            "lets Enterprise Account Executives approve discounts up to and including",
            None,
            "15%",
            "2025-01-01",
            "2025-12-31",
        ),
        st(
            "Northstar Pricing Policy 2025",
            "requires VP Sales approval for discounts greater than",
            None,
            "15%",
            "2025-01-01",
            "2025-12-31",
        ),
    ],  # fmt: skip
    "n": [],
}
BANDS_2026 = {
    "external_id": "northstar-curation-authority-bands-2026",
    "doc_time": "2025-12-08T00:00:00Z",  # pricing_policy_2026.md created
    "e": [["Northstar Pricing Policy 2026", "policy", True]],
    "s": [
        st(
            "Northstar Pricing Policy 2026",
            "lets Enterprise Account Executives approve discounts up to and including",
            None,
            "10%",
            "2026-01-01",
            "2026-12-31",
        ),
        st(
            "Northstar Pricing Policy 2026",
            "requires VP Sales approval for discounts",
            None,
            "greater than 10% and up to and including 20%",
            "2026-01-01",
            "2026-12-31",
        ),
        st(
            "Northstar Pricing Policy 2026",
            "requires Chief Revenue Officer approval for discounts greater than",
            None,
            "20%",
            "2026-01-01",
            "2026-12-31",
        ),
    ],  # fmt: skip
    "n": [],
}
EXCEPTIONS = {
    "external_id": "northstar-curation-exception-values",
    "doc_time": "2025-03-20T00:00:00Z",  # acme_pricing_exception.md created
    "e": [
        ["Acme Mfg. Holdings", "company", True],
        ["Acme NS-500 Strategic Account Exception", "pricing exception", True],
        ["EXC-ACME-NS500-10", "pricing exception", True],
    ],
    "s": [
        st(
            "Acme NS-500 Strategic Account Exception",
            "sets the maximum eligible NS-500 Industrial Controller discount at",
            None,
            "15% of list price",
            "2025-04-01",
            "2028-03-31",
        ),
        st(
            "EXC-ACME-NS500-10",
            "sets the maximum eligible NS-500 Industrial Controller discount at",
            None,
            "10% of list price",
            "2023-04-01",
            "2025-03-31",
        ),
        st(
            "Acme Mfg. Holdings",
            "may receive NS-500 Industrial Controller discounts of up to",
            None,
            "15% of list price",
            "2025-04-01",
            "2028-03-31",
        ),
        st(
            "Acme Mfg. Holdings",
            "may receive NS-500 Industrial Controller discounts of up to",
            None,
            "10% of list price",
            "2023-04-01",
            "2025-03-31",
        ),
    ],  # fmt: skip
    "n": [],
}
PUSHES = {
    "base": [REPORTING, BANDS_2025, BANDS_2026, EXCEPTIONS],
    "missing-contract": [REPORTING, BANDS_2025, BANDS_2026],
}
PILOT = {
    "external_id": REPORTING["external_id"],  # the full push updates this doc in place
    "doc_time": "2026-09-01T00:00:00Z",
    "e": [person("Sarah Chen"), person("Michael Torres")],
    "s": [st("Sarah Chen", "reports to", "Michael Torres", None)],
    "n": [],
}


def sql(query: str) -> list[list[str]]:
    cmd = ["docker", "exec", DB, "psql", "-U", "utopia", "-d", "utopia", "-At", "-F", "\t"]
    out = subprocess.run([*cmd, "-c", query], capture_output=True, text=True, check=True).stdout
    return [line.split("\t") for line in out.splitlines() if line.strip()]


def log(rec: dict[str, Any]) -> None:
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **rec}
    with (HERE / "curation_log.jsonl").open("a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def source_id(kb: str) -> str | None:
    sources = utopia.jcall("GET", f"/kbs/{kb}/sources")["sources"]
    ids = [s["id"] for s in sources if s["name"] == SOURCE_NAME and s["kind"] == "statements"]
    return ids[0] if ids else None


def push(kb: str, payload: dict[str, Any]) -> Any:
    sid = source_id(kb)
    if not sid:
        raise SystemExit("no Statements source; run `setup --apply` first")
    push_key = utopia.jcall("GET", f"/kbs/{kb}/sources/{sid}/token")["ingest_token"]
    req = urllib.request.Request(
        f"{utopia.API}/sources/{sid}/statements",
        json.dumps(payload).encode(),
        {"Authorization": f"Bearer {push_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"push {payload['external_id']} -> {e.code} {e.read().decode()}") from e
    log({"op": "push", "kb": kb, "external_id": payload["external_id"], "result": resp})
    return resp


def inverted_edges(kb: str) -> list[list[str]]:
    return sql(
        "select f.id, s.canonical_name, o.canonical_name from facts f "
        "join entities s on s.id = f.subject_id join entities o on o.id = f.object_id "
        f"where f.kb_id = '{kb}' and f.invalidated_at is null and f.layer = 'open' "
        "and f.phrase ilike 'reports to' and s.canonical_name in ('Michael Torres', "
        "'David Morgan', 'Elena Novak')"
    )


def cmd_plan() -> None:
    for name, kb in KBS.items():
        print(f"== {name}")
        for fid, s, o in inverted_edges(kb):
            print(f"   reject  {s} —reports to→ {o}  ({fid})")
        for p in PUSHES[name]:
            print(f"   push    {p['external_id']}: {len(p['s'])} statements")


def cmd_setup(apply: bool) -> None:
    for name, kb in KBS.items():
        if source_id(kb):
            print(f"{name}: source exists")
            continue
        print(f"{name}: create Statements source {SOURCE_NAME!r}")
        if apply:
            body = {"kind": "statements", "name": SOURCE_NAME}
            resp = utopia.jcall("POST", f"/kbs/{kb}/sources", body)
            log({"op": "create-source", "kb": kb, "source": resp["source"]["id"]})


def cmd_pilot(apply: bool) -> None:
    print("pilot: push 1 statement to base (Sarah Chen reports to Michael Torres)")
    if apply:
        print(push(KBS["base"], PILOT))


def cmd_apply(apply: bool) -> None:
    for name, kb in KBS.items():
        for fid, s, o in inverted_edges(kb):
            print(f"{name}: reject {s} —reports to→ {o}")
            if apply:
                utopia.call("POST", f"/kbs/{kb}/facts/{fid}/reject")
                log({"op": "reject", "kb": kb, "fact": fid, "subject": s, "object": o})
        for p in PUSHES[name]:
            print(f"{name}: push {p['external_id']} ({len(p['s'])} statements)")
            if apply:
                print("   ", push(kb, p))


def curation_start() -> str:
    """When the curation began (the first create-source in the log), as UTC for SQL."""
    for line in (HERE / "curation_log.jsonl").read_text().splitlines():
        rec = json.loads(line)
        if rec["op"] == "create-source":
            return time.strftime(
                "%Y-%m-%d %H:%M:%S+00",
                time.gmtime(time.mktime(time.strptime(rec["at"], "%Y-%m-%dT%H:%M:%S%z"))),
            )
    raise SystemExit("no create-source in curation_log.jsonl")


def cmd_resolve(apply: bool) -> None:
    """Confirm identity for every entity the curation pushes created: a statement can only
    name a thing (the contract has no slot for an entity id), so Utopia mints a new entity and
    queues the pair for a human. Each new entity must match exactly one pre-existing entity by
    display name or `known as` name; otherwise it is reported, not guessed."""
    t0 = curation_start()
    for name, kb in KBS.items():
        new = sql(
            f"select id, canonical_name from entities where kb_id = '{kb}' "
            f"and merged_into is null and created_at >= '{t0}' order by canonical_name"
        )
        for nid, nname in new:
            cands = sql(
                "select distinct e.id, e.canonical_name from entities e "
                "left join facts f on f.subject_id = e.id and f.invalidated_at is null "
                "and f.layer = 'typed' "
                f"where e.kb_id = '{kb}' and e.merged_into is null and e.created_at < '{t0}' "
                f"and (lower(e.canonical_name) = lower($${nname}$$) "
                f"or lower(f.object_value->>'value') = lower($${nname}$$))"
            )
            if len(cands) != 1:
                print(f"{name}: {nname!r} has {len(cands)} candidates; left for review")
                log({"op": "resolve-skip", "kb": kb, "entity": nid, "name": nname, "n": len(cands)})
                continue
            tid, tname = cands[0]
            review = sql(
                f"select id from resolution_reviews where kb_id = '{kb}' and status = 'pending' "
                f"and ((left_id = '{nid}' and right_id = '{tid}') "
                f"or (left_id = '{tid}' and right_id = '{nid}'))"
            )
            why = (
                "Curation statement (Statements source, 2026-09-28) names this existing "
                f"entity ({tname}); the push has no slot for an entity id."
            )
            how = f"review {review[0][0]}" if review else "manual merge"
            print(f"{name}: {nname} (new) -> {tname} via {how}")
            if not apply:
                continue
            if review:
                utopia.jcall("POST", f"/kbs/{kb}/review/{review[0][0]}",
                             {"action": "merge", "rationale": why})  # fmt: skip
            else:
                utopia.jcall("POST", f"/kbs/{kb}/entities/merge",
                             {"source": nid, "target": tid, "rationale": why})  # fmt: skip
            log({"op": "resolve", "kb": kb, "new": nid, "target": tid, "name": nname, "via": how})


def cmd_verify() -> None:
    for name, kb in KBS.items():
        facts, ents = sql(
            f"select (select count(*) from facts where kb_id='{kb}' and invalidated_at is null), "
            f"(select count(*) from entities where kb_id='{kb}' and merged_into is null)"
        )[0]
        print(f"== {name}: live facts {facts}, live entities {ents}")
        rows = sql(
            "select s.canonical_name, coalesce(f.phrase, rt.label), "
            "coalesce(o.canonical_name, f.object_value->>'value'), "
            "coalesce(f.valid_from::date::text, ''), coalesce(f.valid_to::date::text, '') "
            "from facts f join entities s on s.id = f.subject_id "
            "left join entities o on o.id = f.object_id "
            "left join relation_types rt on rt.id = f.predicate_id "
            f"where f.kb_id = '{kb}' and f.invalidated_at is null and f.layer = 'open' and ("
            "f.phrase ilike 'reports to' or s.canonical_name like 'Northstar Pricing Policy%' "
            "or f.phrase ilike '%maximum eligible%' or f.phrase ilike '%discounts of up to%') "
            "order by 1, 2, 4"
        )
        for r in rows:
            span = f"  [{r[3]}..{r[4]}]" if r[3] or r[4] else ""
            print(f"   {r[0]} —{r[1]}→ {r[2]}{span}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("cmd", choices=["plan", "setup", "pilot", "apply", "resolve", "verify"])
    p.add_argument("--apply", action="store_true", help="write to Utopia (default: print)")
    a = p.parse_args()
    if a.cmd == "plan":
        cmd_plan()
    elif a.cmd == "setup":
        cmd_setup(a.apply)
    elif a.cmd == "pilot":
        cmd_pilot(a.apply)
    elif a.cmd == "apply":
        cmd_apply(a.apply)
    elif a.cmd == "resolve":
        cmd_resolve(a.apply)
    else:
        cmd_verify()


if __name__ == "__main__":
    main()
