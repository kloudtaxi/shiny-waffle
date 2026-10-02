"""J4, step 1: label Utopia's duplicate pairs with lab truth and rebuild what the adjudicator saw.

    uv run python runs/2026-10-02-jev-probe/j4/build_pairs.py

Design in `../plan-2.md`. Read-only SQL against Utopia's database (`docker exec … psql`); nothing
is written there. Output: `pairs.jsonl`, one sampled pair per line, with gpt-4o's decision, the
truth label and each side's view (name, type, also-known-as, top four facts as of the decision
time). Also `population.json`, the label coverage of the whole queue.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
KB = "01a0ea56-61e7-79e3-99d1-e82b5d6af79a"  # scale base KB
SEED = 20261002
N_KEEPS = 1000
CSVS = ["crm_accounts", "customers", "employees", "erp_orders", "discount_requests", "products"]


def sql(query: str) -> Any:
    """Run one query that returns a single JSON value; return it parsed."""
    out = subprocess.run(
        ["docker", "exec", "-i", "utopia-db-1", "psql", "-U", "utopia", "-d", "utopia", "-At",
         "-v", "ON_ERROR_STOP=1"],
        input=query, capture_output=True, text=True, check=True,
    ).stdout.strip()  # fmt: skip
    return json.loads(out) if out else None


def norm(s: str) -> str:
    return " ".join(s.lower().split())


def corpus() -> Path:
    out = Path(tempfile.mkdtemp(prefix="ns-large-"))
    subprocess.run(["uv", "run", "northstar", "build", "--scale", "large", "--out", str(out)],
                   cwd=LAB, check=True, capture_output=True)  # fmt: skip
    stored = dict(
        sql(f"""select json_agg(json_build_array(filename, sha256)) from documents
                where kb_id='{KB}' and deleted_at is null
                and filename in ({",".join(f"'{c}.csv'" for c in CSVS)})""")
    )
    for c in CSVS:
        local = hashlib.sha256((out / "evidence/structured" / f"{c}.csv").read_bytes()).hexdigest()
        assert stored[f"{c}.csv"] == local, f"{c}.csv differs from what Utopia ingested"
    return out


class Resolver:
    """Maps an entity name to a lab object (kind, key), or None when unknown or ambiguous."""

    def __init__(self, root: Path) -> None:
        def rows(name: str) -> list[dict[str, str]]:
            with (root / "evidence/structured" / f"{name}.csv").open() as f:
                return list(csv.DictReader(f))

        self.ids: dict[str, tuple[str, str]] = {}
        names: dict[str, set[tuple[str, str]]] = {}

        def name(n: str, obj: tuple[str, str]) -> None:
            if n:
                names.setdefault(norm(n), set()).add(obj)

        for a in rows("crm_accounts"):
            obj = ("customer", a["duns_number"])
            self.ids[a["account_id"].lower()] = obj
            name(a["account_name"], obj)
        for c in rows("customers"):
            obj = ("customer", c["duns_number"])
            self.ids[c["erp_customer_id"].lower()] = obj
            name(c["customer_name"], obj)
        for e in rows("employees"):
            obj = ("employee", e["employee_id"])
            self.ids[e["employee_id"].lower()] = obj
            self.ids[e["email"].lower()] = obj
            name(e["full_name"], obj)
            name(e["preferred_name"], obj)
        for p in rows("products"):
            obj = ("product", p["product_id"])
            for k in (p["product_id"], p["sku"]):
                self.ids[k.lower()] = obj
            name(p["product_name"], obj)
        self.names = names

    def __call__(self, raw: str) -> tuple[tuple[str, str] | None, bool]:
        """(object, composite): composite marks an "SO-n C-m" name."""
        s = norm(raw)
        if m := re.fullmatch(r"(so-\d+)\s+c-\d+", s):
            return ("order", m[1].upper()), True
        if re.fullmatch(r"so-\d+", s):
            return ("order", s.upper()), False
        if re.fullmatch(r"dr-\d+", s):
            return ("request", s.upper()), False
        if re.fullmatch(r"\d+", s):
            return ("literal", s), False
        if s in self.ids:
            return self.ids[s], False
        objs = self.names.get(s, set())
        return (next(iter(objs)) if len(objs) == 1 else None), False


def decisions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = sql(f"""
        select json_agg(json_build_object(
            'review_id', r.id, 'decision_id', d.id, 'action', d.action, 'status', d.status,
            'confidence', d.confidence, 'reason', d.reason, 'calls', d.calls,
            -- just before the decision, or before its merge when that was recorded first
            -- (merges are written ~30 ms before their decision row)
            't', least(d.created_at, coalesce(mg.created_at, d.created_at)) - interval '1 millisecond',
            'left_id', l.id, 'right_id', rr.id,
            'left_name', l.canonical_name, 'right_name', rr.canonical_name,
            'left_type', coalesce(tl.label, 'untyped'),
            'right_type', coalesce(tr.label, 'untyped')))
        from resolution_reviews r
        join agent_decisions d on d.target_id = r.id and d.target_kind = 'review'
        left join entity_merges mg on mg.id = d.merge_id
        join entities l on l.id = r.left_id join entities rr on rr.id = r.right_id
        left join entity_types tl on tl.id = l.type_id
        left join entity_types tr on tr.id = rr.type_id
        where r.kb_id = '{KB}'""")  # fmt: skip
    return rows


def views(items: list[tuple[str, str]]) -> dict[str, Any]:
    """Each (entity_id, time) → also-known-as and top four facts as they stood at that time,
    chosen the way `entity_fact_lines` chooses them. Later merges that moved facts are undone."""
    values = ",".join(f"('{e}'::uuid, '{t}'::timestamptz)" for e, t in items)
    q = f"""
    with want(e, t) as (values {values}),
    attributed as (
      -- facts on the entity now, unless a merge after t moved them in
      select w.e, w.t, f.id, case when f.subject_id = w.e then 'out' else 'in' end as dir
        from want w join facts f on f.kb_id = '{KB}' and (f.subject_id = w.e or f.object_id = w.e)
       where not exists (select 1 from entity_merges m
                          where m.kb_id = '{KB}' and m.target_id = w.e and m.created_at > w.t
                            and (f.id = any(m.moved_subject_facts)
                                 or f.id = any(m.moved_object_facts)))
      union
      -- facts a merge after t moved away from the entity
      select w.e, w.t, x.fid, x.dir from want w join entity_merges m
          on m.kb_id = '{KB}' and m.source_id = w.e and m.created_at > w.t
        cross join lateral (select unnest(m.moved_subject_facts) as fid, 'out' as dir
                            union all select unnest(m.moved_object_facts), 'in') x
    ),
    live as (
      select a.e, a.t, a.dir, f.*, coalesce(r.label, f.phrase, fact_surface_predicate(f.id)) as pl,
             r.key as rkey, r.builtin as rbuiltin
        from attributed a join facts f on f.id = a.id
        left join relation_types r on r.id = f.predicate_id
       where f.recorded_at <= a.t and (f.invalidated_at is null or f.invalidated_at > a.t)
    ),
    lines as (
      select l.e, l.t, row_number() over (partition by l.e, l.t
                 order by l.confidence desc, l.recorded_at desc) as rn,
             case when l.dir = 'out' then l.pl || ' → ' else l.pl || ' ← ' end
             || coalesce(o.canonical_name, '?')
             || case when l.valid_from is not null and l.valid_to is not null
                       then ' (' || to_char(l.valid_from, 'YYYY-MM') || ' → '
                            || to_char(l.valid_to, 'YYYY-MM') || ')'
                     when l.valid_from is not null
                       then ' (' || to_char(l.valid_from, 'YYYY-MM') || ' → now)'
                     else '' end as line
        from live l
        left join entities o
          on o.id = case when l.dir = 'out' then l.object_id else l.subject_id end
       where l.pl is not null and not (coalesce(l.rbuiltin, false) and l.rkey = 'known_as')
    ),
    aka as (
      select l.e, l.t, array_agg(distinct l.object_value->>'value') as names
        from live l join entities en on en.id = l.e
       where l.dir = 'out' and l.rbuiltin and l.rkey = 'known_as'
         and lower(l.object_value->>'value') <> lower(en.canonical_name)
       group by l.e, l.t
    )
    select json_object_agg(w.e || '|' || (to_json(w.t) #>> '{{}}'), json_build_object(
             'aka', coalesce((select a.names from aka a where a.e = w.e and a.t = w.t), '{{}}'),
             'facts', coalesce((select json_agg(x.line order by x.rn) from lines x
                                 where x.e = w.e and x.t = w.t and x.rn <= 4), '[]')))
      from want w"""
    out: dict[str, Any] = sql(q)
    return out


def main() -> None:
    resolve = Resolver(corpus())
    rows = decisions()
    labelled, kinds = [], Counter()
    for r in rows:
        (lo, lc), (ro, rc) = resolve(r["left_name"]), resolve(r["right_name"])
        if lo is None or ro is None:
            kinds["unlabelled"] += 1
            continue
        r |= {"label": "same" if lo == ro else "different", "left_obj": lo, "right_obj": ro,
              "composite": lc or rc}  # fmt: skip
        kinds[f"{lo[0]}~{ro[0]}"] += 1
        labelled.append(r)
    keeps = [r for r in labelled if r["action"] == "keep" and r["status"] == "applied"]
    rest = [r for r in labelled if not (r["action"] == "keep" and r["status"] == "applied")]
    sample = rest + random.Random(SEED).sample(keeps, min(N_KEEPS, len(keeps)))
    items = sorted({(r[f"{s}_id"], r["t"]) for r in sample for s in ("left", "right")})
    seen: dict[str, Any] = {}
    for i in range(0, len(items), 400):
        seen |= views(items[i : i + 400])
    with (HERE / "pairs.jsonl").open("w") as f:
        for r in sample:
            for s in ("left", "right"):
                v = seen[f"{r[f'{s}_id']}|{r['t']}"]
                r[s] = {"name": r[f"{s}_name"], "type": r[f"{s}_type"],
                        "also_known_as": v["aka"], "facts": v["facts"]}  # fmt: skip
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    pop = {"pairs_with_decision": len(rows), "labelled": len(labelled),
           "by_kind": dict(kinds.most_common()), "sample": len(sample),
           "sample_by_decision": dict(Counter(f"{r['action']}/{r['status']}" for r in sample)),
           "sample_by_label": dict(Counter(r["label"] for r in sample))}  # fmt: skip
    (HERE / "population.json").write_text(json.dumps(pop, indent=1) + "\n")
    print(json.dumps(pop, indent=1))


if __name__ == "__main__":
    main()
