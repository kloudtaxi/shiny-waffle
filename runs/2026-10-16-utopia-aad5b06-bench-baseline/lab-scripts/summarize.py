"""Summarise the B-20 baseline runs in out/ as markdown tables (stdout) and a JSON digest.

Usage: python3 -I summarize.py OUT_DIR DIGEST_JSON
Prices at gpt-6-luna's list price ($0.10 / M input, $0.50 / M output); cached input is not
discounted here (a ceiling, not the bill).
"""
import json, os, re, sys

OUT, DIGEST = sys.argv[1], sys.argv[2]
P_IN, P_OUT = 0.10 / 1e6, 0.50 / 1e6


def load(name):
    p = os.path.join(OUT, name)
    return json.load(open(p)) if os.path.exists(p) and os.path.getsize(p) else None


def usage(run):
    u = load(f"{run}.usage.json") or {}
    calls = sum(v["calls"] for v in u.values())
    p = sum(v["prompt"] for v in u.values())
    c = sum(v["completion"] for v in u.values())
    cached = sum(v.get("cached", 0) for v in u.values())
    t = lambda k: open(os.path.join(OUT, f"{run}.{k}")).read().strip()
    start, end = t("start"), t("end")
    from datetime import datetime
    secs = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    return {"calls": calls, "prompt": p, "completion": c, "cached": cached,
            "usd": round(p * P_IN + c * P_OUT, 4), "minutes": round(secs / 60, 1),
            "start": start, "end": end}


digest = {"temporal": {}, "identity": {}, "recall": {}, "contracts": {}, "usage": {}}
rows_usage = []

# ---- temporal
TEMPORAL = [("A", "temporal-armA-r1"), ("A", "temporal-A-r2"),
            ("B", "temporal-B-r1b"), ("B", "temporal-B-r2b"),
            ("bench setup", "temporal-bench-r1"), ("bench setup", "temporal-bench-r2")]
print("## Temporal (37: 23 world axis, 14 record axis)\n")
print("| Arm | Run | All | World | Record | Absent | Failed questions | Base |")
print("|---|---|---|---|---|---|---|---|")
for arm, run in TEMPORAL:
    d = load(f"{run}.json")
    if not d:
        print(f"| {arm} | {run} | not run | | | | | |"); continue
    L = d["ledger"]
    failed = [q["id"] for q in d["questions"] if q["outcome"] != "pass"]
    digest["temporal"][run] = {"arm": arm, "kb": d["kb"], "all": L["all"], "world": L["world"],
                               "record": L["record"], "absent": d["absent"], "failed": failed}
    print(f"| {arm} | {run} | {L['all']['pass']}/{L['all']['asked']} | {L['world']['pass']}/{L['world']['asked']} "
          f"| {L['record']['pass']}/{L['record']['asked']} | {len(d['absent'])} | {', '.join(failed)} | `{d['kb']}` |")
    rows_usage.append(("temporal", arm, run))

# ---- identity
IDENTITY = [("bench setup", "identity-bench-r1"), ("bench setup", "identity-bench-r2"),
            ("C (governance on)", "identity-C-r1"), ("C (governance on)", "identity-C-r2")]
print("\n## Identity (21 anchors, 8 entities; pairwise P/R/F1)\n")
print("| Arm | Run | Order | P | R | F1 | False merges | False splits | Anchors missing | Pending reviews | Base |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for arm, run in IDENTITY:
    d = load(f"{run}.json")
    if not d:
        continue
    digest["identity"][run] = {"arm": arm, "order_disagreement": d["order_disagreement"]}
    for order in ("forward", "reverse"):
        o = d[order]
        pend = sum(p.get("n", 0) for p in o["pending_reviews"])
        digest["identity"][run][order] = {k: o[k] for k in ("kb", "precision", "recall", "f1", "missing", "pairs")}
        digest["identity"][run][order].update(false_merges=len(o["false_merges"]), false_splits=len(o["false_splits"]),
                                              pending=pend)
        print(f"| {arm} | {run} | {order} | {o['precision']} | {o['recall']} | {o['f1']} | {len(o['false_merges'])} "
              f"| {len(o['false_splits'])} | {len(o['missing'])} | {pend} | `{o['kb']}` |")
    od = d["order_disagreement"]
    print(f"| | | order disagreement | {od['differ']}/{od['compared']} pairs | | | | | | | |")
    rows_usage.append(("identity", arm, run))

# ---- recall
print("\n## Recall (52 items)\n")
print("| Arm | Run | Extracted (bench scorer) | Contract view (no qualifiers / time mentions) | Edges | Values | Predicate | Base |")
print("|---|---|---|---|---|---|---|---|")
only_q = {}
for run in ("recall-A-r1", "recall-A-r2"):
    p = os.path.join(OUT, f"{run}.json")
    if not os.path.exists(p):
        continue
    txt = open(p).read()
    kb = json.loads(txt.splitlines()[0])["kb"]
    tot = re.search(r"总分 (\d+)/(\d+)", txt).groups()
    edges = re.search(r"(\d+)/(\d+)\s+关系边", txt).groups()
    vals = re.search(r"(\d+)/(\d+)\s+字面值", txt).groups()
    pred = re.search(r"(\d+)/(\d+)\s+谓词区分度", txt).groups()
    cv = open(os.path.join(OUT, f"{run}.contract-view.txt")).read()
    cvt = re.search(r"总分 (\d+)/(\d+)", cv).groups()
    miss = lambda s: {l.strip() for l in s.splitlines() if l.startswith("  [")}
    only = sorted(miss(cv) - miss(txt))
    only_q[run] = only
    digest["recall"][run] = {"arm": "A", "kb": kb, "extracted": f"{tot[0]}/{tot[1]}", "contract_view": f"{cvt[0]}/{cvt[1]}",
                             "missed": sorted(miss(txt)), "only_via_qualifiers_or_time": only}
    print(f"| A | {run} | {tot[0]}/{tot[1]} | {cvt[0]}/{cvt[1]} | {edges[0]}/{edges[1]} | {vals[0]}/{vals[1]} | {pred[0]}/{pred[1]} | `{kb}` |")
    rows_usage.append(("recall", "A", run))

# ---- contracts
print("\n## Contracts (18 questions, bench scorer)\n")
print("| Arm | Run | Right | Partial | Lease entities with landlord/tenant | Base |")
print("|---|---|---|---|---|---|")
for run in ("contracts-bench-r1", "contracts-bench-r2"):
    p = os.path.join(OUT, f"{run}.json")
    if not os.path.exists(p):
        continue
    txt = open(p).read()
    r = re.search(r"right (\d+)/(\d+), partial (\d+)", txt).groups()
    car = re.search(r"landlord or tenant: (\d+)", txt).group(1)
    label = run.rsplit("-", 1)[1]
    kb = json.load(open(os.path.join(OUT, "..", "work", "bench", "corpora", "contracts", f"lease-kb-bench-{label}.json")))["kb"]
    digest["contracts"][run] = {"arm": "bench setup", "kb": kb, "right": int(r[0]), "of": int(r[1]), "partial": int(r[2]),
                                "carriers": int(car)}
    print(f"| bench setup | {run} | {r[0]}/{r[1]} | {r[2]} | {car} | `{kb}` |")
    rows_usage.append(("contracts", "bench setup", run))

# ---- usage
print("\n## Tokens and list-price dollars (gpt-6-luna, from the server log)\n")
print("| Set | Arm | Run | Calls | Prompt | Completion | Cached | $ at list | Minutes |")
print("|---|---|---|---|---|---|---|---|---|")
tot = {"calls": 0, "prompt": 0, "completion": 0, "cached": 0, "usd": 0.0}
for s, arm, run in rows_usage:
    u = usage(run)
    digest["usage"][run] = u
    for k in tot:
        tot[k] += u[k]
    print(f"| {s} | {arm} | {run} | {u['calls']} | {u['prompt']:,} | {u['completion']:,} | {u['cached']:,} | {u['usd']:.4f} | {u['minutes']} |")
print(f"| **all** | | | {tot['calls']} | {tot['prompt']:,} | {tot['completion']:,} | {tot['cached']:,} | **{tot['usd']:.2f}** | |")
digest["usage_total"] = tot
json.dump(digest, open(DIGEST, "w"), indent=1, ensure_ascii=False)
