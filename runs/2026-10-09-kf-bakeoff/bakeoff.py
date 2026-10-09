"""Knowledge-foundation bake-off: langextract vs Semantica vs a no-framework baseline, same model.

Run with the isolated environment (Semantica 0.7.0, langextract 1.7.1), never the lab's:

    KF=<scratchpad>/kfenv/bin/python
    $KF runs/2026-10-09-kf-bakeoff/bakeoff.py gold          # gold facts, no model calls
    $KF runs/2026-10-09-kf-bakeoff/bakeoff.py run           # all three pipelines (cached)
    $KF runs/2026-10-09-kf-bakeoff/bakeoff.py score

Documents: every `dataset/evidence/documents/*.md` of the base corpus, **front matter stripped**
(a parsed PDF has no YAML header). Gold facts come from the OWM register's structured terms
(`lab/owm_register/base.yaml`, truth-derived and checked against each text) and the HR export,
kept only where the fact is stated in the stripped body. The pipelines never see gold. Design and
predictions in `plan.md`.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path.insert(0, str(HERE))
import claude_cli  # noqa: E402

DOCS = LAB / "dataset/evidence/documents"
REGISTER = LAB / "lab/owm_register/base.yaml"
EMPLOYEES = LAB / "dataset/evidence/structured/employees.csv"
OUT = HERE / "out"

PREDICATES = {
    "approval_limit": "subject: a job title (role); object: the discount percentage or credit "
    "amount bounding what that role may approve (its upper bound, or for the "
    "top role the amount it starts above)",
    "effective_from": "subject: the document; object: the date it takes effect",
    "effective_to": "subject: the document; object: the date it ends or expires",
    "reports_to": "subject: a person; object: the person they report to",
    "has_title": "subject: a person; object: their job title",
    "maximum_discount": "subject: the customer and product the pricing exception covers; "
    "object: the maximum discount percentage it allows",
    "guarantee_amount": "subject: the guaranteed customer; object: the guaranteed amount",
    "credit_cap": "subject: an account tier; object: the maximum credit limit for that tier",
}
INSTRUCTION = (
    "Extract every fact of the following kinds that the document states explicitly. "
    "Do not infer facts the document does not state.\n"
    + "\n".join(f"- {k}: {v}" for k, v in PREDICATES.items())
)


# -- documents and gold -------------------------------------------------------------------------
def body(path: Path) -> str:
    t = path.read_text()
    return t.split("---", 2)[2].lstrip("\n") if t.startswith("---") else t


def docs() -> dict[str, str]:
    return {p.name: body(p) for p in sorted(DOCS.glob("*.md"))}


def num(x: Any) -> list[float]:
    s = str(x).replace(",", "")
    return [float(m) for m in re.findall(r"\d+(?:\.\d+)?", s)]


def norm(s: Any) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", str(s).lower())
    words = [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in s.split()]
    return " ".join(words)


def gold() -> dict[str, list[dict[str, Any]]]:
    reg = yaml.safe_load(REGISTER.read_text())["entries"]
    texts = docs()
    g: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add(doc: str, pred: str, subj: str, obj: Any, surface: str) -> None:
        if surface in texts.get(doc, ""):  # stated in the body as written
            g[doc].append({"predicate": pred, "subject": subj, "object": obj, "surface": surface})

    def pct(x: float) -> str:
        return f"{x * 100:g}%"

    def usd(x: float) -> str:
        return f"${x:,.0f}"

    for e in reg:
        f, t = e["file"], e["terms"]
        for k in ("effective_from", "effective_to"):
            # the holiday calendar's start date appears only as a holiday, not as an effective date
            if e.get(k) and e["kind"] != "holiday_calendar":
                add(f, k, e["doc_id"], str(e[k]), str(e[k]))
        if e["kind"] in ("pricing_policy", "credit_policy"):
            fmt = pct if e["kind"] == "pricing_policy" else usd
            for b in t["bands"]:
                bound = b["max_inclusive"] if b["max_inclusive"] is not None else b["min_exclusive"]
                add(f, "approval_limit", b["title"], bound * (100 if fmt is pct else 1), fmt(bound))
        if e["kind"] == "credit_policy":
            for tier, v in t["caps"].items():
                add(f, "credit_cap", tier, v, usd(v))
        if e["kind"] == "exception":
            add(
                f,
                "maximum_discount",
                f"{t['customer']['name']} {t['product']}",
                t["maximum_discount"] * 100,
                pct(t["maximum_discount"]),
            )
        if e["kind"] == "guarantee":
            add(f, "guarantee_amount", t["customer"]["name"], t["amount"], usd(t["amount"]))
    # the matrix restates the 2026 pricing bands
    p26 = next(e for e in reg if e["doc_id"] == "PRICING-POLICY-2026")
    for b in p26["terms"]["bands"]:
        bound = b["max_inclusive"] if b["max_inclusive"] is not None else b["min_exclusive"]
        add(
            "approval_authority_matrix.md",
            "approval_limit",
            b["title"],
            bound * 100,
            f"{bound * 100:g}%",
        )
    with EMPLOYEES.open() as fh:
        staff = {r["employee_id"]: r for r in csv.DictReader(fh)}
    for chart in ("organization_chart.md", "support_org_chart.md"):
        text = texts.get(chart, "")
        for r in staff.values():
            if r["full_name"] in text:
                add(chart, "has_title", r["full_name"], r["title"], r["title"])
                m = staff.get(r["manager_id"])
                if m and m["full_name"] in text:
                    add(chart, "reports_to", r["full_name"], m["full_name"], m["full_name"])
    return dict(g)


# -- pipelines ----------------------------------------------------------------------------------
def run_langextract(name: str, text: str) -> list[dict[str, Any]]:
    import adapters
    import langextract as lx

    ex = [
        lx.data.ExampleData(
            text="Zephyr Policy\n\nThis policy is effective from 2001-02-03 through 2001-12-31.\n\n"
            "- Shift Leads may approve refunds up to and including $50.\n"
            "- Refunds greater than $50 require Store Manager approval.\n"
            "- Jo Park (Shift Lead) reports to Ana Ruiz.",
            extractions=[
                lx.data.Extraction(
                    "effective_from",
                    "2001-02-03",
                    attributes={"subject": "Zephyr Policy", "object": "2001-02-03"},
                ),
                lx.data.Extraction(
                    "effective_to",
                    "2001-12-31",
                    attributes={"subject": "Zephyr Policy", "object": "2001-12-31"},
                ),
                lx.data.Extraction(
                    "approval_limit",
                    "Shift Leads may approve refunds up to and including $50",
                    attributes={"subject": "Shift Lead", "object": "$50"},
                ),
                lx.data.Extraction(
                    "approval_limit",
                    "greater than $50 require Store Manager",
                    attributes={"subject": "Store Manager", "object": "$50"},
                ),
                lx.data.Extraction(
                    "has_title",
                    "Jo Park (Shift Lead)",
                    attributes={"subject": "Jo Park", "object": "Shift Lead"},
                ),
                lx.data.Extraction(
                    "reports_to",
                    "Jo Park (Shift Lead) reports to Ana Ruiz",
                    attributes={"subject": "Jo Park", "object": "Ana Ruiz"},
                ),
            ],
        )
    ]
    res = lx.extract(
        text,
        prompt_description=INSTRUCTION,
        examples=ex,
        model=adapters.ClaudeLX(tag=f"lx:{name}"),
        fence_output=True,
        use_schema_constraints=False,
        show_progress=False,
        prompt_validation_level=lx.prompt_validation.PromptValidationLevel.OFF,
    )
    out = []
    for e in res.extractions or []:
        a = e.attributes or {}
        ci = e.char_interval
        out.append(
            {
                "predicate": e.extraction_class,
                "subject": a.get("subject"),
                "object": a.get("object"),
                "quote": e.extraction_text,
                "span": [ci.start_pos, ci.end_pos] if ci and ci.start_pos is not None else None,
            }
        )
    return out


def run_semantica(name: str, text: str) -> list[dict[str, Any]]:
    import adapters  # noqa: F401 — registers the provider
    from semantica.semantic_extract.triplet_extractor import TripletExtractor

    types = [f"{k} ({v})" for k, v in PREDICATES.items()]
    tx = TripletExtractor(
        method="llm", provider="claude_cli", triplet_types=types, include_provenance=True
    )
    out = []
    for t in tx.extract_triplets(text) if hasattr(tx, "extract_triplets") else tx.extract(text):
        pred = str(t.predicate).split(" (")[0].strip()
        out.append(
            {
                "predicate": pred,
                "subject": t.subject,
                "object": t.object,
                "quote": None,
                "span": None,
                "meta": {
                    k: v
                    for k, v in (t.metadata or {}).items()
                    if k in ("source_sentence", "start_char", "end_char")
                },
            }
        )
    return out


def run_baseline(name: str, text: str) -> list[dict[str, Any]]:
    prompt = (
        f'{INSTRUCTION}\n\nReturn a JSON array. Each item: {{"predicate": one of '
        f'{list(PREDICATES)}, "subject": ..., "object": ..., "quote": the exact '
        f"text span from the document that states it}}. Return only the JSON array.\n\n"
        f"<document>\n{text}\n</document>"
    )
    raw = claude_cli.complete(prompt, tag=f"base:{name}")
    m = re.search(r"\[.*\]", raw, re.S)
    try:
        items = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        items = []
    out = []
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        q = str(it.get("quote") or "")
        i = text.find(q) if q else -1
        out.append(
            {
                "predicate": it.get("predicate"),
                "subject": it.get("subject"),
                "object": it.get("object"),
                "quote": q,
                "span": [i, i + len(q)] if i >= 0 else None,
            }
        )
    return out


PIPELINES = {"langextract": run_langextract, "semantica": run_semantica, "baseline": run_baseline}


def run(names: list[str], workers: int = 4) -> None:
    OUT.mkdir(exist_ok=True)
    texts = docs()
    for p in names:
        fn = PIPELINES[p]

        def one(item: tuple[str, str], fn: Any = fn, p: str = p) -> tuple[str, Any]:
            n, t = item
            try:
                return n, fn(n, t)
            except Exception as e:  # noqa: BLE001 — recorded, scored as no extractions
                return n, {"error": f"{type(e).__name__}: {e}"[:300]}

        with ThreadPoolExecutor(workers) as pool:
            results = dict(pool.map(one, texts.items()))
        (OUT / f"{p}.json").write_text(json.dumps(results, indent=1, default=str) + "\n")
        errs = [n for n, r in results.items() if isinstance(r, dict)]
        print(
            f"{p}: {sum(len(r) for r in results.values() if isinstance(r, list))} facts, "
            f"{len(errs)} errors {errs[:3]}, ${claude_cli.spend(p[:3]):.2f}"
        )


# -- scoring ------------------------------------------------------------------------------------
def iso_dates(x: Any) -> set[str]:
    s = str(x)
    out = set(re.findall(r"\d{4}-\d{2}-\d{2}", s))
    for m in re.finditer(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", s):
        try:
            out.add(
                date(
                    int(m[3]),
                    "January February March April May June July August "
                    "September October November December".split().index(m[1])
                    + 1,
                    int(m[2]),
                ).isoformat()
            )
        except ValueError:
            pass
    return out


def matches(gf: dict[str, Any], x: dict[str, Any]) -> bool:
    p = gf["predicate"]
    if str(x.get("predicate")) != p:
        return False
    if p in ("effective_from", "effective_to"):
        return gf["object"] in iso_dates(x.get("object"))
    if p in ("approval_limit", "credit_cap"):
        return norm(gf["subject"]) in norm(x.get("subject")) and float(gf["object"]) in num(
            x.get("object")
        )
    if p in ("maximum_discount", "guarantee_amount"):
        return float(gf["object"]) in num(x.get("object"))
    if p == "reports_to":
        return norm(gf["subject"]) in norm(x.get("subject")) and norm(gf["object"]) in norm(
            x.get("object")
        )
    if p == "has_title":
        return norm(gf["subject"]) in norm(x.get("subject")) and norm(gf["object"]) == norm(
            x.get("object")
        )
    return False


def grounded(x: dict[str, Any], text: str) -> dict[str, bool]:
    """native: the tool's own span contains the object's value; locatable: the object's surface
    (or its number/date) appears verbatim in the document."""
    obj = str(x.get("object") or "")
    keys = (
        [obj] + sorted(iso_dates(obj)) + [f"{n:,.0f}" if n >= 1000 else f"{n:g}" for n in num(obj)]
    )
    keys = [k for k in keys if k]
    span = x.get("span")
    native = bool(span) and any(
        k in text[span[0] : span[1]] or norm(k) in norm(text[span[0] : span[1]]) for k in keys
    )
    locatable = any(k in text for k in keys) or (bool(obj) and norm(obj) in norm(text))
    return {"native": native, "locatable": locatable}


def score() -> None:
    g, texts = gold(), docs()
    report: dict[str, Any] = {"gold": {d: len(v) for d, v in g.items()}}
    for p in PIPELINES:
        path = OUT / f"{p}.json"
        if not path.exists():
            continue
        res = json.loads(path.read_text())
        tp, fp, miss = Counter(), Counter(), []
        nat = loc = n_in = 0
        derived = []
        for doc, facts in res.items():
            facts = facts if isinstance(facts, list) else []
            want = list(g.get(doc, []))
            used = [False] * len(want)
            for x in facts:
                if x.get("predicate") not in PREDICATES:
                    continue
                if doc in g:
                    n_in += 1
                    gr = grounded(x, texts[doc])
                    nat += gr["native"]
                    loc += gr["locatable"]
                hit = next((i for i, gf in enumerate(want) if not used[i] and matches(gf, x)), None)
                if hit is None:
                    fp[x["predicate"]] += doc in g
                else:
                    used[hit] = True
                    tp[x["predicate"]] += 1
                if (
                    x.get("predicate") == "approval_limit"
                    and re.search(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", str(x.get("subject")))
                    and not any(
                        w in norm(x.get("subject"))
                        for w in (
                            "account",
                            "officer",
                            "vp",
                            "director",
                            "manager",
                            "specialist",
                            "executive",
                            "sale",
                            "finance",
                            "revenue",
                        )
                    )
                ):
                    derived.append(f"{doc}: {x.get('subject')} -> {x.get('object')}")
            miss += [
                f"{doc}: {gf['predicate']} {gf['subject']} = {gf['surface']}"
                for i, gf in enumerate(want)
                if not used[i]
            ]
        n_gold = sum(len(v) for v in g.values())
        n_tp = sum(tp.values())
        report[p] = {
            "recall": round(n_tp / n_gold, 3),
            "precision_on_gold_docs": round(n_tp / max(n_tp + sum(fp.values()), 1), 3),
            "tp": dict(tp),
            "fp": dict(fp),
            "native_span_ok": round(nat / max(n_in, 1), 3),
            "locatable": round(loc / max(n_in, 1), 3),
            "facts_on_gold_docs": n_in,
            "person_level_authority_claims": derived,
            "missed": miss,
            "usd": round(
                claude_cli.spend({"langextract": "lx", "semantica": "sem", "baseline": "base"}[p]),
                2,
            ),
        }
        print(p, {k: v for k, v in report[p].items() if k not in ("missed",)})
    (HERE / "results.json").write_text(json.dumps(report, indent=1) + "\n")


def main() -> None:
    step = sys.argv[1]
    if step == "gold":
        g = gold()
        c = Counter(f["predicate"] for v in g.values() for f in v)
        print(f"{sum(len(v) for v in g.values())} gold facts in {len(g)} documents:", dict(c))
        (HERE / "gold.json").write_text(json.dumps(g, indent=1) + "\n")
    elif step == "run":
        run(sys.argv[2:] or list(PIPELINES))
    else:
        score()


if __name__ == "__main__":
    main()
