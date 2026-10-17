"""Part 1: the foundation, read only through the contract (pre-registration §3).

    uv run python lab/exam/part1.py snapshot --run runs/<exam> --arm <arm> --corpus base \\
        --out <file>
    uv run python lab/exam/part1.py score <snapshot file>

`snapshot` reads one base once, through the contract: K0, every document (K2), its text (K7, as
bytes) and passages (K8), the facts with evidence in it (K13 by `doc_id`), and the entities the
identity checks name (K15, K16) with their `x-holds` intervals where served. `score` computes P1,
P3 and P5 from the snapshot, so a base can be scored again without reading it again. P2 and P4 are
`judge.py`'s.

- **P1, alignment:** every piece of evidence, by alignment. An `exact` one is verified: the text's
  bytes at its span must be its quote, whitespace aside (B-20's `probes/spans.py` rule).
- **P3a, U-31 (a feature check, labelled):** CRM-2048, C-1001 and ACME-MFG-2025 among one entity's
  identifiers.
- **P3b:** no entity carries two of the lab's customers' names or identifiers. The names are the
  truth's, compared whole (after case and spacing), never by a shared word.
- **P5, SLA's operational data:** for the ten tickets S36–S45 name, each ticket's opened and
  restored times and its events' times, and the holiday calendar's dates: is the value a fact of the
  base, read from that row? `exact` is the same instant with the zone the source wrote; `instant`
  the same instant in another zone; `wall` the clock time with its zone dropped; `date` only the
  day. Only `exact` and `instant` count as held.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(LAB / "lab"), str(LAB / "src")]

from contract_reader.client import Contract, adapter, bearer  # noqa: E402
from contract_reader.tools import _seg  # noqa: E402

U31 = ("CRM-2048", "C-1001", "ACME-MFG-2025")
U31_SYSTEMS = {"CRM-2048": ("CRM", "Northstar CRM"), "C-1001": ("ERP", "Northstar ERP")}
SLA_DOCS = ("service_tickets.csv", "ticket_events.csv", "holiday_calendar.md")


# ------------------------------------------------------------------ names


def norm(s: object) -> str:
    """A name as compared: NFKC, case-folded, without periods or commas, single-spaced."""
    t = unicodedata.normalize("NFKC", str(s or "")).casefold()
    t = re.sub(r"[.,]", "", t)
    t = re.sub(r"\s+", " ", t).strip(" \t\"';:()[]")
    return re.sub(r"^(the|a|an) ", "", t)


def id_norm(s: object) -> str:
    return re.sub(r"[^0-9a-z]", "", str(s or "").casefold())


def customers() -> dict[str, dict[str, set[str]]]:
    """The lab's customers: their whole names and their ids, from the truth. A one-word alias that
    starts another customer's name (Acme) is left out: it names no one customer."""
    from northstar.model import load_truth

    truth = load_truth(LAB / "truth")
    out: dict[str, dict[str, set[str]]] = {}
    for c in truth.customers:
        names = {c.canonical_name, c.erp_name, *c.aliases}
        ids = {v for v in c.source_ids.values() if v}
        if c.duns:
            ids.add(c.duns)
        out[c.id] = {
            "names": {norm(n) for n in names if n not in ids},
            "ids": {id_norm(i) for i in ids},
        }
    for cid, entry in out.items():
        others = [n for oid, o in out.items() if oid != cid for n in o["names"]]
        entry["names"] = {
            n for n in entry["names"] if " " in n or not any(o.startswith(n) for o in others)
        }
    return out


# ------------------------------------------------------------------ snapshot


def connect(run: Path, arm: str) -> tuple[Contract, dict[str, Any]]:
    cfg: dict[str, Any] = json.loads((run / "arms.json").read_text())["arms"][arm]
    if cfg["mode"] == "bearer":
        return bearer(cfg["url"], (LAB / cfg["token_file"]).resolve()), cfg
    return adapter(cfg["url"], cfg["person"]), cfg


def snapshot(c: Contract, kb: str) -> dict[str, Any]:
    about = c.request("GET", "/about").body
    docs = c.pages(f"/kbs/{kb}/documents", {"limit": 100})
    out: dict[str, Any] = {"kb": kb, "about": about, "documents": [], "entities": {}}
    for d in docs:
        v = d["current_version"]
        status, text = c.raw("GET", f"/documents/{d['doc_id']}/versions/{v}/text")
        passages = c.pages(f"/documents/{d['doc_id']}/versions/{v}/passages")
        facts = c.pages(f"/kbs/{kb}/facts", {"doc_id": d["doc_id"], "limit": 500})
        out["documents"].append(
            {
                "doc_id": d["doc_id"],
                "version": v,
                "filename": d["filename"],
                "text": text.decode("utf-8", errors="replace") if status == 200 else None,
                "passages": [
                    {"passage_id": p["passage_id"], "text": p["text"], "span": p.get("span")}
                    for p in passages
                ],
                "facts": facts,
            }
        )
    wanted: set[str] = set()
    for cust in customers().values():
        for name in cust["names"]:
            a = c.request("GET", f"/kbs/{kb}/entities", {"q": name, "limit": 20})
            if a.status == 200 and isinstance(a.body, dict):
                wanted |= {e["entity_id"] for e in a.body.get("items") or []}
    lookups = []
    for ident, systems in U31_SYSTEMS.items():
        for system in systems:
            a = c.request("GET", f"/kbs/{kb}/identifiers/{_seg(system)}/{_seg(ident)}")
            lookups.append({"system": system, "id": ident, "status": a.status, "body": a.body})
            if a.status == 200 and isinstance(a.body, dict):
                wanted.add(a.body["entity_id"])
    out["identifier_lookups"] = lookups
    # P2 and P4's anchors (p2_items.yaml): each name's entities, in the foundation's own order.
    out["anchors"] = {}
    for name in anchors():
        a = c.request("GET", f"/kbs/{kb}/entities", {"q": name, "limit": 10})
        found = (
            [e["entity_id"] for e in (a.body or {}).get("items") or []] if a.status == 200 else []
        )
        out["anchors"][name] = found
        wanted |= set(found)
    out["x_holds"] = {}
    for eid in sorted(wanted):
        a = c.request("GET", f"/entities/{_seg(eid)}")
        if a.status == 200:
            out["entities"][eid] = a.body
        h = c.request("GET", f"/kbs/{kb}/x-holds", {"entity": eid})
        out["x_holds"][eid] = (
            h.body.get("items") if h.status == 200 and isinstance(h.body, dict) else None
        )
    return out


def items() -> dict[str, list[dict[str, Any]]]:
    import yaml

    data: dict[str, list[dict[str, Any]]] = yaml.safe_load(
        (LAB / "lab/exam/p2_items.yaml").read_text()
    )
    return data


def anchors() -> list[str]:
    names: list[str] = []
    for group in items().values():
        for it in group:
            names += [n for n in it["anchors"] if n not in names]
    return names


# ------------------------------------------------------------------ P1


def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def p1(snap: dict[str, Any]) -> dict[str, Any]:
    by: dict[str, int] = {"exact": 0, "partial": 0, "fuzzy": 0, "none": 0}
    verified = mismatched = 0
    facts: set[str] = set()
    for d in snap["documents"]:
        text = (d["text"] or "").encode("utf-8")
        for f in d["facts"]:
            facts.add(f["fact_id"])
            for e in f.get("evidence") or []:
                if e.get("doc_id") != d["doc_id"]:
                    continue  # counted under its own document
                align = e.get("alignment", "none")
                by[align] = by.get(align, 0) + 1
                if align == "exact":
                    span = e.get("span") or {}
                    got = text[span.get("start", 0) : span.get("end", 0)].decode("utf-8", "replace")
                    if span and _ws(got) == _ws(e.get("quote", "")):
                        verified += 1
                    else:
                        mismatched += 1
    total = sum(by.values())
    return {
        "facts": len(facts),
        "evidence": total,
        "by_alignment": by,
        "exact_share": round(by["exact"] / total, 4) if total else None,
        "exact_verified": verified,
        "exact_span_mismatch": mismatched,
    }


# ------------------------------------------------------------------ P3


def _entity_ids(e: dict[str, Any]) -> set[str]:
    return {id_norm(i.get("id")) for i in e.get("identifiers") or []}


def _entity_names(e: dict[str, Any]) -> set[str]:
    names = {norm(e.get("name"))} | {norm(n.get("name")) for n in e.get("names") or []}
    return {n for n in names if n}


def p3(snap: dict[str, Any]) -> dict[str, Any]:
    ents = list(snap["entities"].values())
    want = {id_norm(i) for i in U31}
    served = any(lk["status"] not in (501,) for lk in snap["identifier_lookups"])
    best = max((len(want & _entity_ids(e)) for e in ents), default=0)
    p3a = {
        "label": "feature check: built knowing the corpus (D3)",
        "served": served,
        "ids_on_one_entity": best,
        "grade": "not served" if not served else "pass" if best == 3 else f"{best} of 3",
        "lookups": [
            {k: lk[k] for k in ("system", "id", "status")} for lk in snap["identifier_lookups"]
        ],
    }
    cust = customers()
    merges = []
    for e in ents:
        names, ids = _entity_names(e), _entity_ids(e)
        hit = sorted(cid for cid, c in cust.items() if names & c["names"] or ids & c["ids"])
        if len(hit) > 1:
            merges.append({"entity": e.get("name"), "customers": hit})
    acme_pair = any({"CUST-1001", "CUST-1044"} <= set(m["customers"]) for m in merges)
    return {
        "p3a": p3a,
        "p3b": {
            "grade": "pass" if not merges else "fail",
            "acme_industrial_kept_apart": not acme_pair,
            "false_merges": merges,
            "entities_checked": len(ents),
        },
    }


# ------------------------------------------------------------------ P5


def _instant(s: str) -> tuple[datetime | None, str | None, date | None]:
    """A written value as (instant, its zone as written, its day)."""
    s = str(s).strip()
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}(?::\d{2})?)(Z|[+-]\d{2}:?\d{2})?$", s)
    if m:
        zone = m.group(3)
        z = "+00:00" if zone == "Z" else (zone[:3] + ":" + zone[-2:] if zone else None)
        try:
            dt = datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}{z or ''}")
        except ValueError:
            return None, None, None
        return dt, z, dt.date()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return None, None, date.fromisoformat(s)
    return None, None, None


def classify(written: str, want: str) -> str:
    """How a value served compares with the source's: exact, instant, date or no."""
    got_i, got_z, got_d = _instant(written)
    want_i, want_z, want_d = _instant(want)
    if want_i is None:  # a date in the source
        return "exact" if got_d == want_d and got_d is not None else "no"
    if got_i is not None and got_i.tzinfo and want_i.tzinfo and got_i == want_i:
        return "exact" if got_z == want_z else "instant"
    if got_i is not None and got_i.tzinfo is None and got_i.replace(tzinfo=want_i.tzinfo) == want_i:
        return "wall"  # the wall time kept, the zone dropped: the instant can't be recovered
    return "date" if got_d is not None and got_d == want_d else "no"


def _values(f: dict[str, Any]) -> list[str]:
    vals = []
    for v in [f.get("object") or {}, *[q.get("value") or {} for q in f.get("qualifiers") or []]]:
        if v.get("kind") == "value":
            vals.append(str(v.get("value")))
    return vals


RANK = {"exact": 4, "instant": 3, "wall": 2, "date": 1, "no": 0}


def sla_items() -> list[dict[str, str]]:
    """The 76 items: (document, the row's key words, the value written)."""
    import yaml

    tickets = sorted(
        {
            t
            for p in sorted((LAB / "truth/scenarios").glob("*.yaml"))
            if 36 <= int(p.name[:2]) <= 45
            for t in re.findall(r"SR-\d+", p.read_text())
        }
    )
    ev = LAB / "dataset/evidence/structured"
    items = []
    for row in csv.DictReader(io.StringIO((ev / "service_tickets.csv").read_text())):
        if row["ticket_id"] in tickets:
            for col in ("opened_at", "restored_at"):
                if row[col]:
                    items.append(
                        {
                            "doc": "service_tickets.csv",
                            "key": row["ticket_id"],
                            "value": row[col],
                            "what": col,
                        }
                    )
    for row in csv.DictReader(io.StringIO((ev / "ticket_events.csv").read_text())):
        if row["ticket_id"] in tickets:
            items.append(
                {
                    "doc": "ticket_events.csv",
                    "key": row["ticket_id"],
                    "value": row["at"],
                    "what": row["event"],
                }
            )
    cal = (LAB / "dataset/evidence/documents/holiday_calendar.md").read_text()
    for d, _day, name in re.findall(r"^\| (\d{4}-\d{2}-\d{2}) \| (\w+) \| ([^|]+?) \|", cal, re.M):
        items.append({"doc": "holiday_calendar.md", "key": "", "value": d, "what": name})
    del yaml
    return items


def p5(snap: dict[str, Any]) -> dict[str, Any]:
    docs = {d["filename"].rsplit("/", 1)[-1]: d for d in snap["documents"]}
    results = []
    for it in sla_items():
        d = docs.get(it["doc"])
        best = "no"
        if d is not None:
            ptext = {p["passage_id"]: p["text"] for p in d["passages"]}
            for f in d["facts"]:
                rows = [
                    ptext.get(e.get("passage_id") or "", "")
                    for e in f.get("evidence") or []
                    if e.get("doc_id") == d["doc_id"]
                ]
                if it["key"] and not any(it["key"] in r and it["value"] in r for r in rows):
                    continue  # not read from this ticket's row
                for v in _values(f):
                    c = classify(v, it["value"])
                    if RANK[c] > RANK[best]:
                        best = c
        results.append({**it, "match": best})
    held = sum(r["match"] in ("exact", "instant") for r in results)
    return {
        "items": len(results),
        "held": held,
        "exact": sum(r["match"] == "exact" for r in results),
        "instant": sum(r["match"] == "instant" for r in results),
        "wall_time_no_zone": sum(r["match"] == "wall" for r in results),
        "date_only": sum(r["match"] == "date" for r in results),
        "missing": sum(r["match"] == "no" for r in results),
        "rows": results,
    }


def score(snap: dict[str, Any]) -> dict[str, Any]:
    return {"kb": snap["kb"], "p1": p1(snap), **p3(snap), "p5": p5(snap)}


def main() -> None:
    ap = argparse.ArgumentParser(prog="exam-part1")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("snapshot")
    sp.add_argument("--run", type=Path, required=True)
    sp.add_argument("--arm", required=True)
    sp.add_argument("--corpus", default="base")
    sp.add_argument("--out", type=Path, required=True)
    sc = sub.add_parser("score")
    sc.add_argument("snapshot", type=Path)
    a = ap.parse_args()
    if a.cmd == "snapshot":
        c, cfg = connect(a.run.resolve(), a.arm)
        snap = snapshot(c, cfg["kbs"][a.corpus])
        a.out.write_text(json.dumps(snap, ensure_ascii=False) + "\n")
        print(f"{len(snap['documents'])} documents, {len(snap['entities'])} entities -> {a.out}")
    else:
        result = score(json.loads(a.snapshot.read_text()))
        out = a.snapshot.with_suffix(".score.json")
        out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
        brief = {
            "p1": result["p1"],
            "p3a": {k: v for k, v in result["p3a"].items() if k != "lookups"},
            "p3b": {k: v for k, v in result["p3b"].items() if k != "false_merges"},
            "p5": {k: v for k, v in result["p5"].items() if k != "rows"},
        }
        print(json.dumps(brief, indent=1, ensure_ascii=False))
        print(f"-> {out}")


if __name__ == "__main__":
    main()
