"""J2: are Jev's probabilities calibrated against the lab's truth labels?

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-02-jev-probe/j2/calibrate.py
    uv run python runs/2026-10-02-jev-probe/j2/calibrate.py --replay   # from the recording only

Sets. The grid is fixed in `../plan.md`; J2b was added before any J2 call (see the plan's addendum).
All of them use J1's own question definitions and state builders (`../j1/hybrid.py`).

- **grid** (base corpus):
  - party: each CRM account × each agreement or exception document;
  - product: each product × each such document;
  - basis: each distinct justification in `discount_requests.csv`.

  Labels come from `truth/`: the document's customer and products, and the request's basis.
- **J2b** (the scale corpus, built here at seed 20260923):
  - each CRM account paired with its true ERP customer and the two ERP customers with the most
    similar names (difflib);
  - **J2b-addr** gives Jev the name and address; **J2b-name** gives the names only;
  - labels: the CRM↔ERP pairing the generator made. DUNS numbers are withheld, because they would
    turn identity into a join.

Positive-class probability:
- party: P(`same_legal_entity`);
- product: the Noul;
- basis: P(`contract_terms`).

Outputs: `judgments.jsonl` and `calibration.md`.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "j1"))
import hybrid as h  # noqa: E402

CALLS = HERE.parent / "j1" / "engine-calls.jsonl"  # one recording for J1 and J2
POSITIVE = {"party": "same_legal_entity", "basis": "contract_terms"}


def ask(eng: Any, job: dict[str, Any]) -> dict[str, Any]:
    reply = eng.ask(job["state"], {job["name"]: job["q"]})["answers"][job["name"]]
    if job["q"]["type"] == "noul":
        p, conf = float(reply["noul"]), None
    else:
        p = float(reply["probabilities"].get(POSITIVE[job["name"]], 0.0))
        conf = float(reply["confidence"])
    return {"set": job["set"], "type": job["name"], "pair": job["pair"], "label": job["label"],
            "p": p, "confidence": conf}  # fmt: skip


def grid_jobs(truth: Any) -> list[dict[str, Any]]:
    docs = [d for d in h.load_docs("base") if h.is_agreement(d) or h.is_exception(d)]
    owner = {a: c.customer for c in truth.contracts for a in [c.id, *c.aliases]}
    owner |= {x.id: x.customer for x in truth.exceptions}
    covers = {a: set(c.covers) for c in truth.contracts for a in [c.id, *c.aliases]}
    covers |= {x.id: {x.product} for x in truth.exceptions}
    by_crm = {c.source_ids.get("crm"): c.id for c in truth.customers}
    jobs = []
    for acct in h.table("base", "crm_accounts"):
        cust = {k: acct[k] for k in ("account_name", "billing_street", "billing_city",
                                     "billing_state")}  # fmt: skip
        for d in docs:
            jobs.append({"set": "grid", "name": "party", "q": h.Q_PARTY,
                         "pair": f"{acct['account_id']}~{d.doc_id}",
                         "label": by_crm.get(acct["account_id"]) == owner[d.doc_id],
                         "state": {"request_customer": cust,
                                   "document": h.party_text(d)}})  # fmt: skip
    for prod in h.table("base", "products"):
        name = f"{prod['product_name']} ({prod['sku']})"
        for d in docs:
            jobs.append({"set": "grid", "name": "covers_product", "q": h.Q_PRODUCT,
                         "pair": f"{prod['product_id']}~{d.doc_id}",
                         "label": prod["product_id"] in covers[d.doc_id],
                         "state": {"product": name, "document": h.product_text(d)}})  # fmt: skip
    for just in sorted({r["justification"] for r in h.table("base", "discount_requests")}):
        jobs.append({"set": "grid", "name": "basis", "q": h.Q_BASIS, "pair": just,
                     "label": just.lower().startswith("contract pricing"),
                     "state": {"request": {"justification": just}}})  # fmt: skip
    return jobs


def j2b_jobs() -> list[dict[str, Any]]:
    out = Path(tempfile.mkdtemp(prefix="ns-large-"))
    subprocess.run(["uv", "run", "northstar", "build", "--scale", "large", "--out", str(out)],
                   cwd=LAB, check=True, capture_output=True)  # fmt: skip
    with (out / "evidence/structured/crm_accounts.csv").open() as f:
        crm = list(csv.DictReader(f))
    with (out / "evidence/structured/customers.csv").open() as f:
        erp = list(csv.DictReader(f))
    by_duns = {e["duns_number"]: e for e in erp}  # the generator's pairing, kept from Jev
    names = [e["customer_name"] for e in erp]
    jobs = []
    for a in crm:
        true = by_duns.get(a["duns_number"])
        if true is None:
            continue
        decoys = [n for n in difflib.get_close_matches(a["account_name"], names, n=4, cutoff=0)
                  if n != true["customer_name"]][:2]  # fmt: skip
        pairs = [(true, True)] + [(next(e for e in erp if e["customer_name"] == n), False)
                                  for n in decoys]  # fmt: skip
        for e, label in pairs:
            for variant in ("addr", "name"):
                cust: dict[str, str] = {"account_name": a["account_name"]}
                doc = f"ERP customer: {e['customer_name']}"
                if variant == "addr":
                    cust |= {k: a[k] for k in ("billing_street", "billing_city", "billing_state")}
                    doc += f", {e['bill_to_street']}, {e['bill_to_city']}, {e['bill_to_state']}"
                jobs.append({"set": f"J2b-{variant}", "name": "party", "q": h.Q_PARTY,
                             "pair": f"{a['account_id']}~{e['erp_customer_id']}", "label": label,
                             "state": {"request_customer": cust, "document": doc}})  # fmt: skip
    return jobs


def report(rows: list[dict[str, Any]]) -> str:
    lines = []
    for key in sorted({(r["set"], r["type"]) for r in rows}):
        rs = [r for r in rows if (r["set"], r["type"]) == key]
        n = len(rs)
        pos = sum(r["label"] for r in rs)
        acc = sum((r["p"] >= 0.5) == r["label"] for r in rs) / n
        brier = sum((r["p"] - r["label"]) ** 2 for r in rs) / n
        bins: list[list[dict[str, Any]]] = [[] for _ in range(10)]
        for r in rs:
            bins[min(int(r["p"] * 10), 9)].append(r)
        ece = sum(len(b) / n * abs(sum(r["p"] for r in b) / len(b)
                                   - sum(r["label"] for r in b) / len(b))
                  for b in bins if b)  # fmt: skip
        if rs[0]["confidence"] is not None:
            kept = [r for r in rs if r["confidence"] >= h.CHOICE_FLOOR]
        else:
            kept = [r for r in rs if not (h.NOUL_BAND[0] <= r["p"] <= h.NOUL_BAND[1])]
        kacc = sum((r["p"] >= 0.5) == r["label"] for r in kept) / len(kept) if kept else 0.0
        lines += [f"### {key[0]} · {key[1]}  (n = {n}, positives = {pos})", "",
                  f"accuracy {acc:.3f} · Brier {brier:.3f} · **ECE {ece:.3f}** · past the gate: "
                  f"{len(kept)}/{n} ({len(kept) / n:.0%}), accuracy there {kacc:.3f}", "",
                  "| p bin | n | mean p | observed |", "|---|---|---|---|"]  # fmt: skip
        for i, b in enumerate(bins):
            if b:
                mp = sum(r["p"] for r in b) / len(b)
                ob = sum(r["label"] for r in b) / len(b)
                lines.append(
                    f"| {i / 10:.1f}–{(i + 1) / 10:.1f} | {len(b)} | {mp:.2f} | {ob:.2f} |"
                )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    eng = h.Replay(CALLS, h.MODEL) if a.replay else h.Recorder(h.TypeSafe(h.MODEL), CALLS)
    jobs = grid_jobs(h.load_truth(LAB / "truth")) + j2b_jobs()
    with ThreadPoolExecutor(a.workers) as pool:
        rows = list(pool.map(lambda j: ask(eng, j), jobs))
    (HERE / "judgments.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    md = "# J2 calibration (jev-1.13.0)\n\nGenerated by `calibrate.py`.\n\n" + report(rows)
    (HERE / "calibration.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
