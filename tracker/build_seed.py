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
        "As ingested (runs 2–3: correction reverted to replay it)",
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
    (
        "B2k",
        6,
        "After fact curation",
        "Opus · graph only",
        "Opus 5.5, blind, headless claude -p",
        "9 MCP tools; search_chunks and get_document hidden",
        "Corrected + curated facts (bands, exception values, reporting lines)",
        "curation/arm-b/r1/B2",
        "B2 after curating the facts extraction got wrong or missed, via a Statements source.",
    ),
    (
        "B2kP",
        7,
        "After fact curation",
        "Opus · graph only + procedure",
        "Opus 5.5, blind, headless claude -p; system prompt + owm/procedures/discount-approval.md",
        "9 MCP tools; search_chunks and get_document hidden",
        "Corrected + curated facts (bands, exception values, reporting lines)",
        "procedure/arm-b/r1/B2",
        "B2k plus the OWM decision procedure (from the corpus SOP and doc 03 §11); "
        "S01-S05 auto-scored against the answer key.",
    ),
    (
        "B2kPR",
        8,
        "After fact curation",
        "Opus · graph only + procedure + request record",
        "Opus 5.5, blind, headless claude -p; system prompt + owm/procedures/discount-approval.md",
        "9 MCP tools; search_chunks and get_document hidden",
        "Corrected + curated facts (bands, exception values, reporting lines)",
        "request/arm-b/r1/B2",
        "B2kP plus the request as recorded in the CRM (the DR-9001 row, varied per scenario), "
        "as the OWM would receive it. Decision scenarios S01-S05 only; auto-scored.",
    ),
    (
        "B2PR",
        9,
        "As ingested",
        "Opus · graph only + procedure + request record",
        "Opus 5.5, blind, headless claude -p; system prompt + owm/procedures/discount-approval.md",
        "9 MCP tools; search_chunks and get_document hidden",
        "As ingested (no identity correction, no curation)",
        "request-uncurated/arm-b/r1/B2",
        "The OWM layer (procedure + request record) on the uncurated graph: is curation still "
        "needed when the OWM supplies the decision logic and inputs?",
    ),
    (
        "B2kPRa",
        10,
        "After fact curation",
        "Opus · graph only + procedure + request record",
        "Opus 5.5, blind, headless claude -p; system prompt + owm/procedures/discount-approval.md",
        "9 MCP tools; search_chunks and get_document hidden",
        "Curated facts + the agreement's term (one fact)",
        "agreement/arm-b/r1/B2",
        "B2kPR with one more curated fact, the agreement's term, to test what split S03. "
        "S03 only; auto-scored.",
    ),
    (
        "B1kPR",
        11,
        "After fact curation",
        "Opus · all tools + procedure + request record",
        "Opus 5.5, blind, headless claude -p; system prompt + owm/procedures/discount-approval.md",
        "All 11 MCP tools",
        "Curated facts (bands, exception values, reporting lines, the agreement's term)",
        "b1/curated/r1/B1",
        "The OWM layer with text retrieval, on the curated graph. Decision scenarios S01-S05 "
        "only; auto-scored.",
    ),
    (
        "B1PR",
        12,
        "As ingested",
        "Opus · all tools + procedure + request record",
        "Opus 5.5, blind, headless claude -p; system prompt + owm/procedures/discount-approval.md",
        "All 11 MCP tools",
        "Curation withdrawn (its values still visible as rejected events in `changes`)",
        "b1/uncurated/r1/B1",
        "The OWM layer with text retrieval, on the uncurated graph: is curation needed when the "
        "reader can read the source documents? Decision scenarios S01-S05 only; auto-scored.",
    ),
    (
        "B1nPR",
        13,
        "As ingested",
        "Opus · all tools but changes + procedure + request record",
        "Opus 5.5, blind, headless claude -p; system prompt + owm/procedures/discount-approval.md",
        "10 MCP tools; changes hidden",
        "Curation withdrawn; no route to the withdrawn values",
        "b1/uncurated/r1/B1n",
        "B1PR's control: `changes` hidden so the withdrawn curation values can't leak. Decision "
        "scenarios S01-S05 only; auto-scored.",
    ),
]

# Provisional first-read grades (Claude), from comparison.md and correction/comparison.md.
# Repeat runs of a condition: folder pattern relative to the run, with {n} = 2, 3, ...
REPEAT_DIRS = {
    "B2": "repeats/pre-r{n}/B2",  # graph reverted to pre-correction for these runs
    "B1c": "repeats/r{n}/B1",
    "B2c": "repeats/r{n}/B2",
    "B2k": "curation/arm-b/r{n}/B2",
    "B2kP": "procedure/arm-b/r{n}/B2",
    "B2kPR": "request/arm-b/r{n}/B2",
}
# Conditions whose reader got a different question text than the run's questions.tsv.
QUESTION_FILES = {"B2kPR": "request/questions.tsv"}


def annotations(run_name: str) -> dict:
    """Claude's provisional grades, the findings and the experiment status for one run.

    They live in tracker/annotations/<run>.json: data, edited per run, not code. Human grades
    are never here; they live only in the ledger's `grades` collection."""
    return json.loads((LAB / "tracker" / "annotations" / f"{run_name}.json").read_text())


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
    ann = annotations(exp)
    first_run = {c: {sid: tuple(v) for sid, v in d.items()} for c, d in ann["provisional"].items()}
    repeats = {
        (r["condition"], r["scenario"], r["repeat"]): (r["grade"], r["note"])
        for r in ann["provisional_repeats"]
    }

    def read_questions(path: Path) -> dict[str, tuple[str, str]]:
        out = {}
        for row in path.read_text().splitlines()[1:]:
            sid, kb, q = row.split("\t")
            out[sid] = (kb, q)
        return out

    questions = read_questions(run / "questions.tsv")
    # A run's annotations may pick its own conditions (and their folders, repeat patterns,
    # question files, labels). Otherwise every condition in CONDITIONS applies.
    selected: dict[str, dict] | None = ann.get("conditions")
    namespaced = bool(ann.get("namespace_conditions"))

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
        if selected is not None and cid not in selected:
            continue
        ov = (selected or {}).get(cid, {})
        folder, group, graph = (
            ov.get("folder", folder),
            ov.get("group", group),
            ov.get("graph", graph),
        )
        desc, order = ov.get("description", desc), ov.get("order", order)
        pattern = ov.get("repeats", REPEAT_DIRS.get(cid))
        qfile = ov.get("questions", QUESTION_FILES.get(cid))
        cond_questions = read_questions(run / qfile) if qfile and (run / qfile).exists() else {}
        tot_cost, tot_turns, n = 0.0, 0, 0
        folders = [(1, folder)]
        if pattern:
            rep = 2
            while (run / pattern.format(n=rep)).is_dir():
                folders.append((rep, pattern.format(n=rep)))
                rep += 1
        for rep, fdir in folders:
            for sid in scenarios:
                if cid == "A":
                    src = run / fdir / f"{sid}.md"
                    if not src.exists():
                        continue
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
                    default = tuple(ann["default_first_run"])
                    grade, note = first_run.get(cid, {}).get(sid, default)
                else:
                    grade, note = repeats.get((cid, sid, rep), (None, "Not read yet."))
                kb, q = cond_questions.get(sid, questions[sid])
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
        if n == 0:
            continue  # nothing ran under this condition in this run
        conditions[f"{exp}~{cid}" if namespaced else cid] = {
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

    meta = ann["experiment"]

    def expand(v: object) -> object:
        return v.replace("{run}", rel) if isinstance(v, str) else v

    experiments = {
        exp: {
            "id": exp,
            **{k: expand(v) for k, v in meta.items() if k != "docs"},
            "docs": [expand(d) for d in meta.get("docs", [])],
        }
    }
    findings = {
        f"{exp}~{f['id']}": {
            "experiment": exp,
            "order": i,
            "category": f["category"],
            "title": f["title"],
            "body": f["body"],
            "status": "observed",
            "source": "Claude",
            "evidence": [f"{rel}/{e}" for e in f["evidence"]],
        }
        for i, f in enumerate(ann["findings"], 1)
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
