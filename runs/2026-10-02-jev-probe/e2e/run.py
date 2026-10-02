"""E2E: the agent retrieves, the hybrid engine decides. Run on the 102 T1/T2 reader transcripts.

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-02-jev-probe/e2e/run.py [--replay]

The design is in `../plan-2.md`. Each transcript's evidence set is rebuilt from its tool calls:
- **read**: documents opened with `get_document`;
- **seen**: read, plus documents whose chunks came back from `search_chunks` or `search_docs`.

Utopia document ids are mapped to filenames through the `documents` table of the KB the run used
(read-only). The hybrid engine (`../j1/hybrid.py`) then decides with its candidate documents
limited to that set. It uses J1's recording, so recurring judgments are not asked again.

Outputs: `results.jsonl` (one row per transcript and set) and `results.md`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "j1"))
sys.path.insert(0, str(HERE.parent.parent / "2026-09-30-owm-measurements/05-vocabulary"))
import hybrid as h  # noqa: E402
import rescore as item5  # noqa: E402

T = LAB / "runs/2026-09-30-owm-measurements/01-02-procedure"
KBS = {
    "base": "01a0ea56-61e7-79e3-99d1-e82b5d6af79a",
    "missing-contract-evidence": "01a0ea56-65d0-73d2-940d-6f1f9da0d800",
}
NEEDED = {  # truth keys in the oracle's evidence list → the document that carries them
    "MSA-ACME-2025": "acme_master_supply_agreement.md",
    "EXC-ACME-NS500-15": "acme_pricing_exception.md",
    "EXC-ACME-NS500-10": "acme_pricing_exception_2023.md",
    "SA-ACME-2023": "acme_pricing_exception_2023.md",
}
SEARCH = {"search_chunks", "search_docs"}


def filenames(kb: str) -> dict[str, str]:
    out = subprocess.run(
        ["docker", "exec", "-i", "utopia-db-1", "psql", "-U", "utopia", "-d", "utopia", "-At"],
        input=f"select json_object_agg(id, filename) from documents where kb_id = '{kb}'",
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    m: dict[str, str] = json.loads(out)
    return m


def evidence(jsonl: Path, names: dict[str, str]) -> tuple[set[str], set[str]]:
    uses: dict[str, tuple[str, dict[str, Any]]] = {}
    read: set[str] = set()
    seen: set[str] = set()
    for line in jsonl.read_text().splitlines():
        if not line.startswith("{"):
            continue
        msg = json.loads(line).get("message")
        if not isinstance(msg, dict) or not isinstance(msg.get("content"), list):
            continue
        for b in msg["content"]:
            if b.get("type") == "tool_use":
                tool = b["name"].split("__")[-1]
                uses[b["id"]] = (tool, b.get("input") or {})
                if tool == "get_document" and b["input"].get("document_id") in names:
                    read.add(names[b["input"]["document_id"]])
            elif (
                b.get("type") == "tool_result"
                and uses.get(b.get("tool_use_id"), ("",))[0] in SEARCH
            ):
                c = b.get("content")
                text = c if isinstance(c, str) else " ".join(
                    x.get("text", "") for x in c or [] if isinstance(x, dict))  # fmt: skip
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                for hit in payload.get("chunks", []) + payload.get("documents", []):
                    fn = hit.get("filename") or names.get(hit.get("document_id", ""))
                    if fn:
                        seen.add(fn)
    return read, read | seen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--authority", choices=["truth", "evidence"], default="truth")
    a = ap.parse_args()
    tag = "" if a.authority == "truth" else "-a1"
    eng = h.Replay(h.CALLS, h.MODEL) if a.replay else h.Recorder(h.TypeSafe(h.MODEL), h.CALLS)
    truth = h.load_truth(LAB / "truth")
    exp = h.scorer.expected()
    import yaml

    key_evidence = {
        r["scenario"]: r["evidence"]
        for r in yaml.safe_load((LAB / "dataset/answer-key/expected-results.yaml").read_text())
        if r.get("type") == "discount_approval"
    }
    names = {c: filenames(kb) for c, kb in KBS.items()}
    spec_scores = {arm: json.loads((T / f"scores-{arm}.json").read_text()) for arm in ("T1", "T2")}
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    assert spec and spec.loader
    heldout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(heldout)

    rows = []
    for arm in ("T1", "T2"):
        for run_key, scen in spec_scores[arm].items():
            rep = run_key.split("/")[-2]
            for sid, reader in scen.items():
                corpus = next(s for s in truth.scenarios if s.id == sid).corpus
                read, seen = evidence(LAB / run_key / f"{sid}.jsonl", names[corpus])
                needed = {NEEDED[k] for k in key_evidence[sid] if k in NEEDED}
                for which, docs in (("read", read), ("seen", seen)):
                    d = h.decide(eng, truth, sid, heldout.record(sid), allowed=docs,
                                 authority=a.authority)  # fmt: skip
                    g = h.scorer.score(sid, d, exp[sid])
                    c = item5.classify({"expected": exp[sid], "got": d, "fields": g["fields"]})
                    rows.append({"arm": arm, "run": rep, "scenario": sid, "set": which,
                                 "sufficient": needed <= docs, "missing": sorted(needed - docs),
                                 "hybrid": g["grade"], "hybrid_outcome": d["outcome"],
                                 "gated_outcome": d["gated_outcome"], "safety": c["safety"],
                                 "reader": reader["grade"], "expected": exp[sid]["outcome"],
                                 "policy": d["authority"]["policy"]})  # fmt: skip
    (HERE / f"results{tag}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))

    lines = ["# E2E: the agent retrieves, the hybrid engine decides (T1 + T2 transcripts)", ""]
    for which in ("seen", "read"):
        rs = [r for r in rows if r["set"] == which]
        n = len(rs)
        suff = sum(r["sufficient"] for r in rs)
        hp = sum(r["hybrid"] == "pass" for r in rs)
        rp = sum(r["reader"] == "pass" for r in rs)
        unsafe = sum(r["safety"] == "unsafe" for r in rs)
        insuff = [r for r in rs if not r["sufficient"]]
        found = (f"{sum(r['policy'] is not None for r in rs)}/{n}" if a.authority == "evidence"
                 else "taken from truth")  # fmt: skip
        lines += [f"## Evidence set: {which}", "",
                  f"- retrieval sufficient: **{suff}/{n}**",
                  f"- hybrid strict pass: **{hp}/{n}**, against the readers' own **{rp}/{n}**",
                  f"- unsafe: **{unsafe}**",
                  f"- governing policy found in the set: {found}",
                  f"- when retrieval was insufficient ({len(insuff)}): hybrid outcomes "
                  f"{dict(Counter(r['hybrid_outcome'] for r in insuff))}", ""]  # fmt: skip
        both = Counter((r["reader"], r["hybrid"]) for r in rs)
        lines += ["| reader \\ hybrid | pass | partial | fail |", "|---|---|---|---|"]
        for rg in ("pass", "partial", "fail"):
            cells = " | ".join(str(both[(rg, hg)]) for hg in ("pass", "partial", "fail"))
            lines.append(f"| **{rg}** | {cells} |")
        lines.append("")
        misses = Counter((r["arm"], r["scenario"], r["hybrid_outcome"], tuple(r["missing"]))
                         for r in rs if r["hybrid"] != "pass")  # fmt: skip
        if misses:
            lines += ["Hybrid misses (arm, scenario, outcome, missing documents) × count:", ""]
            lines += [f"- {k} × {v}" for k, v in sorted(misses.items())] + [""]
    (HERE / f"results{tag}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
