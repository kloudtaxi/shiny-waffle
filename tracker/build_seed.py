"""Build the lab tracker's database seed from a run folder.

    python3 tracker/build_seed.py runs/2026-09-28-utopia-aad5b06

Writes tracker/seed/<collection>.json, each a {doc_id: body} map for the tracker artifact's
`db`. Answers are shaped like an `mlflow.genai.evaluate` row (inputs / outputs / expectations)
so the set can move to MLflow later without reshaping. Human grades live in a separate
`grades` collection that this script never writes, so reseeding cannot overwrite them.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
OUT = LAB / "tracker" / "seed"

SCENARIOS = [
    # id, order, title, as_of, corpus, expected outcome, expected detail, traps
    (
        "S01",
        1,
        "Standard 15% request",
        "2026-09-23",
        "base",
        "APPROVE_WITH_AUTHORIZATION",
        "Eligible under EXC-ACME-NS500-15, but Sarah (Enterprise AE, ≤10% in 2026) lacks "
        "authority; "
        "15% sits in the VP Sales band, so Michael Torres must approve.",
        [
            "eligibility ≠ authority",
            "temporal precedent (DR-8104)",
            "wrong department (Priya Shah)",
        ],
    ),
    (
        "S02",
        2,
        "18% request",
        "2026-09-23",
        "base",
        "REJECT_OR_ESCALATE",
        "18% exceeds Acme's contractual 15% cap; VP authority alone does not create eligibility.",
        ["exception as a constraint"],
    ),
    (
        "S03",
        3,
        "NS-Cloud request",
        "2026-09-23",
        "base",
        "REVIEW_REQUIRED",
        "The 15% exception covers the NS-500 only and must not transfer to NS-Cloud.",
        ["product scope"],
    ),
    (
        "S04",
        4,
        "Historical 15% request",
        "2025-09-23",
        "base",
        "APPROVE",
        "Under the 2025 policy an Enterprise AE could approve up to 15%.",
        ["temporal state"],
    ),
    (
        "S05",
        5,
        "Missing contract evidence",
        "2026-09-23",
        "missing-contract-evidence",
        "REQUEST_EVIDENCE",
        "Without the MSA and exception, 15% eligibility cannot be established; hearsay "
        '("I believe 15%") is not a basis.',
        ["hearsay"],
    ),
    (
        "S06a",
        6,
        "Exception on 2026-09-23",
        "2026-09-23",
        "base",
        "15% · EXC-ACME-NS500-15",
        "The current exception applies; the 2023 one is kept, not overwritten.",
        ["superseded fact", "stale status"],
    ),
    (
        "S06b",
        7,
        "Exception on 2024-10-01",
        "2024-10-01",
        "base",
        "10% · EXC-ACME-NS500-10",
        "The 2023 exception was in force; the 15% one had not started.",
        ["superseded fact"],
    ),
    (
        "S06c",
        8,
        "Exception on 2022-10-01",
        "2022-10-01",
        "base",
        "None",
        "No exception was in force; both later facts must remain on record.",
        ["temporal state"],
    ),
    (
        "S07",
        9,
        "Why is Acme eligible?",
        None,
        "base",
        "EXC-ACME-NS500-15 under MSA-ACME-2025",
        "Cite the MSA and the pricing exception; the account plan and the email are hearsay.",
        ["hearsay"],
    ),
    (
        "S08",
        10,
        "Which customer is it?",
        None,
        "base",
        "CRM-2048 = C-1001 = ACME-MFG-2025; Acme Industrial is different",
        "All three ids are Acme Manufacturing (Acme Mfg. Holdings); Acme Industrial Supply Co. "
        "(CRM-2091 / C-1044) is a separate customer.",
        ["identity drift", "similar name"],
    ),
]

CONDITIONS = [
    # id, order, group, label, reader, tools, graph, folder, description
    (
        "A",
        1,
        "As ingested",
        "Utopia chat",
        "Utopia in-app agent (gpt-4o-mini, unverified)",
        "Utopia's own chat loop, all tools",
        "As ingested",
        "answers",
        "Utopia's reference chat agent. Measures the product's built-in app, not the foundation.",
    ),
    (
        "B1",
        2,
        "As ingested",
        "Opus · all tools",
        "Opus 5.5, blind, headless claude -p",
        "All 11 MCP tools",
        "As ingested",
        "arm-b/B1",
        "Foundation as retrieval plus a strong reader.",
    ),
    (
        "B2",
        3,
        "As ingested",
        "Opus · graph only",
        "Opus 5.5, blind, headless claude -p",
        "9 MCP tools; search_chunks and get_document hidden",
        "As ingested",
        "arm-b/B2",
        "What the foundation modelled. Graph tools still return provenance quotes via `changes`.",
    ),
    (
        "B1c",
        4,
        "After identity correction",
        "Opus · all tools",
        "Opus 5.5, blind, headless claude -p",
        "All 11 MCP tools",
        "After 18 identity corrections (17:25 UTC)",
        "correction/arm-b/B1",
        "B1 rerun after the Review-queue and merge corrections.",
    ),
    (
        "B2c",
        5,
        "After identity correction",
        "Opus · graph only",
        "Opus 5.5, blind, headless claude -p",
        "9 MCP tools; search_chunks and get_document hidden",
        "After 18 identity corrections (17:25 UTC)",
        "correction/arm-b/B2",
        "B2 rerun after the corrections. Its drop is reader-strategy variance, not the correction.",
    ),
]

# Provisional first-read grades (Claude), from comparison.md and correction/comparison.md.
P, H, F = "pass", "partial", "fail"
PROVISIONAL = {
    "A": {
        "S01": (F, "Cannot determine; no approver named."),
        "S02": (F, "Cannot determine; queried record time 2023-10-01, before ingestion."),
        "S03": (F, "Cannot determine."),
        "S04": (F, "Cannot determine; no facts at 2025-09-23."),
        "S05": (F, "Cannot determine; does not name the missing contract."),
        "S06a": (F, "No facts."),
        "S06b": (F, 'Answered "100%": value invented, period right.'),
        "S06c": (P, "No facts — right, but only because nothing is dated then."),
        "S07": (P, "Correct basis, cites the exception document (the one text search)."),
        "S08": (H, "Acme Industrial different ✓; CRM-2048 and ACME-MFG-2025 not found."),
    },
    "B1": {
        "S03": (
            H,
            'Doesn\'t transfer the exception ✓, but frames it as "needs VP sign-off" '
            "rather than review.",
        )
    },
    "B2": {
        "S01": (H, 'Right "no" and reasoning; VP band absent, approver only "obvious".'),
        "S03": (H, "No NS-Cloud exception ✓; authority unresolved."),
        "S05": (H, "Declines to decide ✓, but asks for the authority limits, not the contract."),
        "S08": (H, "Acme Industrial different ✓; ids not in the graph."),
    },
    "B1c": {"S03": (H, 'Same framing as B1: "needs VP sign-off".')},
    "B2c": {
        "S01": (F, '"Can\'t confirm"; never found the percentage quotes.'),
        "S02": (F, 'No verdict; "percentage wasn\'t captured".'),
        "S03": (H, "No NS-Cloud exception ✓; authority unknown."),
        "S04": (F, '"Can\'t confirm"; leans toward "unlikely".'),
        "S05": (H, "Declines ✓; asks for the limits, not the contract."),
        "S08": (H, 'Ids "not recorded anywhere, not even as an alias" — the merge erased C-1001.'),
    },
}
DEFAULT_PASS_NOTE = "Matches the expected outcome and reasoning."

# Repeat runs of a condition: folder pattern relative to the run, with {n} = 2, 3, ...
REPEAT_DIRS = {"B1c": "repeats/r{n}/B1", "B2c": "repeats/r{n}/B2"}
# First-read grades for repeats: {(condition, scenario, repeat): (grade, note)}. A repeat
# with no entry is left ungraded — unlike run 1, it never defaults to "pass".
PROVISIONAL_REPEATS: dict[tuple[str, str, int], tuple[str, str]] = {
    ("B2c", "S01", 2): (
        F,
        '"Can\'t confirm", leans "probably not"; no approver. No per-entity `changes`, no '
        "percentages.",
    ),
    ("B2c", "S01", 3): (
        F,
        '"Can\'t confirm" she can approve; eligibility vs authority noted, no verdict.',
    ),
    ("B2c", "S02", 2): (F, 'No verdict: "percentages were never captured".'),
    ("B2c", "S02", 3): (
        H,
        '"Don\'t offer it until someone checks" — right action, wrong reason (cap unknown, not '
        "exceeded).",
    ),
    ("B2c", "S03", 2): (
        H,
        '"No, over her 10% limit" (found the quotes via `changes`); framed as escalation, not '
        "review.",
    ),
    ("B2c", "S03", 3): (
        H,
        "No: above her 10% limit and the exception covers a different product; framed as "
        "escalation.",
    ),
    ("B2c", "S04", 2): (
        F,
        '"Most of what is recorded points to no" — wrong direction; 2025 limit never found.',
    ),
    ("B2c", "S04", 3): (F, '"Points toward no" — wrong direction; limits not found.'),
    ("B2c", "S05", 2): (H, "Declines ✓; asks for the limits, not the contract."),
    ("B2c", "S05", 3): (
        H,
        "Declines ✓ after 12 `changes` calls on the wrong entities; asks for thresholds, not the "
        "contract.",
    ),
    ("B2c", "S06a", 2): (P, DEFAULT_PASS_NOTE),
    ("B2c", "S06a", 3): (P, DEFAULT_PASS_NOTE),
    ("B2c", "S06b", 2): (P, DEFAULT_PASS_NOTE),
    ("B2c", "S06b", 3): (P, DEFAULT_PASS_NOTE),
    ("B2c", "S06c", 2): (P, DEFAULT_PASS_NOTE),
    ("B2c", "S06c", 3): (P, DEFAULT_PASS_NOTE),
    ("B2c", "S07", 2): (P, DEFAULT_PASS_NOTE),
    ("B2c", "S07", 3): (P, DEFAULT_PASS_NOTE),
    ("B2c", "S08", 2): (
        H,
        "Acme Industrial different ✓; none of the three ids found (searched fragments too).",
    ),
    ("B2c", "S08", 3): (H, "Acme Industrial different ✓; ids not found."),
}

FINDINGS = [
    (
        "f01",
        "agent",
        "The reader is the largest variable",
        "On the same graph Utopia's chat got 2 of 10 right and Opus with all tools got 9. Arm A "
        "measured Utopia's reference chat loop, not the foundation; Utopia's own ADR 0046 says the "
        "app surface is MCP.",
        ["comparison.md"],
    ),
    (
        "f02",
        "owm",
        "A strong reader did the OWM's work at question time",
        "B1 composed role + reporting line + policy band into the approver, kept eligibility apart "
        "from authority, chose policy and exception by date, refused hearsay and matched ids on "
        "DUNS. The OWM's case must rest on what that lacks: persistence, consistency and audit, "
        "scale, cost.",
        ["comparison.md"],
    ),
    (
        "f03",
        "foundation",
        "Every reporting line is inverted",
        "Utopia's MCP serves `Michael Torres —reports to→ Sarah Chen` and `David Morgan —reports "
        "to→ Michael Torres`, citing organization_chart.md: the indented list was read upside "
        "down.",
        ["notes.md"],
    ),
    (
        "f04",
        "owm",
        "The reader silently repairs foundation errors",
        'B2 read the inverted edges and wrote "Sarah reports to Michael" from title priors. Right '
        "answer, wrong data, nothing in the answer shows it. Candidate OWM capability: structural "
        "constraints on organizational relations that flag the error.",
        ["comparison.md"],
    ),
    (
        "f05",
        "foundation",
        "Authority and eligibility values never reached the graph",
        "No VP Sales band (>10% ≤20%), no percentages as values, undated roles. The current 15% "
        "exception is undated while the stale 10% one is dated, so dated reads find the past and "
        "miss the present.",
        ["notes.md", "comparison.md"],
    ),
    (
        "f06",
        "foundation",
        "Every CSV lost rows to truncated extraction",
        "All six CSVs hit `truncated_reply`; rows after the cut produced no facts. Structured "
        "evidence is the least completely extracted part of the corpus.",
        ["notes.md"],
    ),
    (
        "f07",
        "foundation",
        "Graph tools carry quotes, but only through `changes`",
        "`entity_facts` returns document ids, not quotes. B2 reached the percentages only by "
        "calling `changes` per entity since ingestion day, an audit feed used as a quote "
        "retriever.",
        ["correction/comparison.md"],
    ),
    (
        "f08",
        "review",
        "Identity is decided on names, and the stakes are routed backwards",
        "The adjudicator never used shared DUNS, SKU or email. It auto-applied the identity calls "
        "that change answers at 90–95% and sent SKU trivia to humans.",
        ["notes.md"],
    ),
    (
        "f09",
        "agent",
        "Utopia's chat confuses record time with world time",
        "It passed question dates as `as_of` (record time), before anything was ingested, so every "
        'lookup was empty. It also invented "100%" for S06b.',
        ["notes.md"],
    ),
    (
        "f10",
        "review",
        "Identity review bought nothing measurable",
        "B1 was unchanged after 18 corrections. B2's binding gaps are missing facts, which no "
        "identity decision can supply and the Review queue never surfaces.",
        ["correction/comparison.md"],
    ),
    (
        "f11",
        "foundation",
        "A human merge erased the identifier it connected",
        "Merging C-1001 and CRM-2048 into Acme dropped them as findable names: the ID entities had "
        "a canonical name but no name fact. Appears to diverge from Utopia ADR 0041 decision 1.",
        ["notes.md"],
    ),
    (
        "f12",
        "method",
        "The graph-only drop after correction is stable, not variance",
        "Three B2 runs on the corrected graph grade 4/3/3, 4/3/3 and 4/4/2; the single "
        'pre-correction run (6/4/0) is the outlier. The earlier "reader-strategy variance" '
        "reading was wrong: on S01, S02 and S04 the pre-correction reader made 8-9 per-entity "
        "`changes` calls each and reached the percentage quotes; after correction it made 0 in "
        "9 of 9 runs.",
        ["repeats/notes.md", "correction/comparison.md"],
    ),
    (
        "f13",
        "foundation",
        "Cleaner identity cut the dig that found the evidence (hypothesis)",
        "Before correction the reader kept meeting thin, duplicated entities (one fact each) and "
        "fell back to the `changes` feed, where the quotes carrying the percentages live. After "
        "correction, consolidated entities returned richer-looking facts, so it stopped and "
        'answered "can\'t confirm". If this holds, graph-only answers depend on an undocumented '
        "path, and the fix is quotes on `entity_facts`, not better identity. Test: "
        "pre-correction repeats.",
        ["repeats/notes.md"],
    ),
]


def md_section(text: str, head: str) -> str:
    m = re.search(rf"^## {re.escape(head)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def arm_a_answer(path: Path) -> dict:
    text = path.read_text()
    steps = []
    for line in md_section(text, "Tool steps").splitlines():
        m = re.match(r"- `(.*)`$", line.strip())
        if not m:
            continue
        try:
            s = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        args = {k: s[k] for k in ("label", "valid_at", "as_of", "since", "until") if k in s}
        steps.append(
            {
                "tool": s.get("kind", "?"),
                "args": args,
                "result": s.get("detail", ""),
                "status": s.get("status"),
            }
        )
    return {
        "answer": md_section(text, "Answer"),
        "tool_calls": steps,
        "turns": len(steps),
        "cost_usd": None,
        "duration_ms": None,
        "text_tools_used": sorted(
            {"search_chunks" for s in steps if s["tool"] == "search"}
            | {"get_document" for s in steps if s["tool"] == "document"}
        ),
    }


def arm_b_answer(path: Path) -> dict:
    calls: list[dict] = []
    by_id: dict[str, dict] = {}
    result: dict = {}
    for line in path.read_text().splitlines():
        if not line.startswith("{"):
            continue
        e = json.loads(line)
        if e.get("type") == "result":
            result = e
        msg = e.get("message")
        if not isinstance(msg, dict):
            continue
        for b in msg.get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                c = {
                    "tool": b["name"].split("__")[-1],
                    "args": b.get("input") or {},
                    "result": None,
                    "status": "ok",
                }
                by_id[b.get("id")] = c
                calls.append(c)
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in by_id:
                content = b.get("content")
                text = (
                    "".join(x.get("text", "") for x in content if isinstance(x, dict))
                    if isinstance(content, list)
                    else str(content or "")
                )
                c = by_id[b["tool_use_id"]]
                c["result"] = f"{len(text):,} chars"
                if b.get("is_error"):
                    c["status"] = "error"
    used = {c["tool"] for c in calls}
    return {
        "answer": (result.get("result") or "").strip(),
        "tool_calls": calls,
        "turns": result.get("num_turns"),
        "cost_usd": result.get("total_cost_usd"),
        "duration_ms": result.get("duration_ms"),
        "text_tools_used": sorted(used & {"search_chunks", "get_document"}),
    }


def main(run_dir: str) -> None:
    run = (LAB / run_dir).resolve()
    exp = run.name
    rel = str(run.relative_to(LAB))
    questions = {}
    for row in (run / "questions.tsv").read_text().splitlines()[1:]:
        sid, kb, q = row.split("\t")
        questions[sid] = (kb, q)

    scenarios = {}
    for sid, order, title, as_of, corpus, outcome, detail, traps in SCENARIOS:
        scenarios[sid] = {
            "id": sid,
            "order": order,
            "title": title,
            "as_of": as_of,
            "corpus": corpus,
            "question": questions[sid][1],
            "expected": outcome,
            "expected_detail": detail,
            "traps": traps,
        }

    conditions, answers = {}, {}
    for cid, order, group, label, reader, tools, graph, folder, desc in CONDITIONS:
        tot_cost, tot_turns, n = 0.0, 0, 0
        folders = [(1, folder)]
        if cid in REPEAT_DIRS:
            rep = 2
            while (run / REPEAT_DIRS[cid].format(n=rep)).is_dir():
                folders.append((rep, REPEAT_DIRS[cid].format(n=rep)))
                rep += 1
        for rep, fdir in folders:
            for sid in scenarios:
                if cid == "A":
                    src = run / fdir / f"{sid}.md"
                    out = arm_a_answer(src)
                else:
                    src = run / fdir / f"{sid}.jsonl"
                    if not src.exists():
                        continue
                    out = arm_b_answer(src)
                n += 1
                tot_turns += out["turns"] or 0
                tot_cost += out["cost_usd"] or 0.0
                if rep == 1:
                    grade, note = PROVISIONAL.get(cid, {}).get(sid, (P, DEFAULT_PASS_NOTE))
                else:
                    grade, note = PROVISIONAL_REPEATS.get((cid, sid, rep), (None, "Not read yet."))
                kb, q = questions[sid]
                doc_id = f"{exp}~{cid}~{sid}~r{rep}"
                answers[doc_id] = {
                    "experiment": exp,
                    "condition": cid,
                    "scenario": sid,
                    "repeat": rep,
                    "inputs": {"question": q, "kb": kb, "as_of": scenarios[sid]["as_of"]},
                    "outputs": out,
                    "expectations": {
                        "expected": scenarios[sid]["expected"],
                        "expected_detail": scenarios[sid]["expected_detail"],
                    },
                    "provisional": {"grade": grade, "note": note, "by": "Claude (first read)"},
                    "source": str(src.relative_to(LAB)),
                }
        conditions[cid] = {
            "id": cid,
            "experiment": exp,
            "order": order,
            "group": group,
            "label": label,
            "reader": reader,
            "tools": tools,
            "graph": graph,
            "description": desc,
            "answers": n,
            "turns": tot_turns,
            "cost_usd": round(tot_cost, 2) if cid != "A" else None,
        }

    experiments = {
        exp: {
            "id": exp,
            "title": "Northstar × Utopia · boundary run",
            "date": "2026-09-28",
            "status": "active",
            "status_note": "Resumed: B2c repeats (n=3) are stable at 4-3-3 / 4-3-3 / 4-4-2; the "
            "pre-correction B2 run is the outlier.",
            "next": [
                "Decide: pre-correction B2 repeats (revert merges, rerun, re-apply)",
                "Steps 7–8: fact checklist and rubric scoring",
                "Curation arm: fix VP band, percentages, reporting direction",
                "Scale arm: northstar build --scale large",
            ],
            "utopia": "dev @ aad5b06",
            "lab_commit": "976d119",
            "seed": 20260923,
            "notes": f"{rel}/notes.md",
            "docs": [
                f"{rel}/comparison.md",
                f"{rel}/correction/comparison.md",
                "docs/experiment-runbook.md",
                "docs/tracking-mlflow-review.md",
            ],
        }
    }
    findings = {
        f"{exp}~{fid}": {
            "experiment": exp,
            "order": i,
            "category": cat,
            "title": title,
            "body": body,
            "status": "observed",
            "source": "Claude",
            "evidence": [f"{rel}/{e}" for e in ev],
        }
        for i, (fid, cat, title, body, ev) in enumerate(FINDINGS, 1)
    }

    OUT.mkdir(parents=True, exist_ok=True)
    for name, docs in (
        ("experiments", experiments),
        ("conditions", conditions),
        ("scenarios", scenarios),
        ("answers", answers),
        ("findings", findings),
    ):
        (OUT / f"{name}.json").write_text(json.dumps(docs, ensure_ascii=False, indent=1) + "\n")
        size = max(len(json.dumps(d, ensure_ascii=False)) for d in docs.values())
        print(f"{name}: {len(docs)} docs, largest {size:,} bytes")


if __name__ == "__main__":
    main(sys.argv[1])
