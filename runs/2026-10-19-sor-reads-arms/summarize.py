"""Aggregate the three-arm test's measures (plan.md): scores from each folder's scores.json (the
exam's scorer), plus tool use, gate refusals, SQL errors and cost from the answer streams.

    uv run python runs/2026-10-19-sor-reads-arms/summarize.py
"""

from __future__ import annotations

import importlib.util
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(LAB / "lab"), str(LAB / "lab/utopia")]
_s = importlib.util.spec_from_file_location("er", LAB / "lab/exam/reader.py")
assert _s and _s.loader
er = importlib.util.module_from_spec(_s)
_s.loader.exec_module(er)

FOLDERS = [("G", "clean-G", "b20"), ("GD", "clean-GD", "b20"), ("GS", "clean-GS", "b20"),
           ("GD attacked", "attack-GD", "b20-attacked"), ("GS attacked", "attack-GS", "b20-attacked"),
           ("GS-sync attacked", "attack-GS-sync", "b20-attacked")]  # fmt: skip


def tool_calls(stream: str) -> list[str]:
    names = []
    for e in er.events(stream):
        msg = e.get("message")
        if isinstance(msg, dict):
            names += [b["name"].split("__")[-1] for b in msg.get("content") or []
                      if isinstance(b, dict) and b.get("type") == "tool_use"]  # fmt: skip
    return names


def main() -> None:
    out: dict[str, list[dict[str, object]]] = {}
    for label, folder, arm in FOLDERS:
        scores = json.loads((HERE / folder / "scores.json").read_text())
        for rep in sorted({r["rep"] for r in scores}):
            rows = [r for r in scores if r["rep"] == rep]
            d = HERE / folder / arm / "C2" / rep
            calls, sor, refused, sqlerr, cost, outs = [], 0, 0, 0, 0.0, 0
            for p in sorted(d.glob("S*.jsonl")):
                if p.name.endswith(".calls.jsonl") or ".infra-error-" in p.name:
                    continue
                text = p.read_text()
                res = er.result_of(text)
                cost += float(res.get("total_cost_usd") or 0)
                outs += res.get("subtype") == "error_max_turns"
                names = tool_calls(text)
                calls.append(len(names))
                graph = {t["name"] for t in er.TOOLS}
                sor += any(n not in graph for n in names)
                log = p.with_name(p.stem + ".sor.calls.jsonl")
                if log.exists():
                    for ln in log.read_text().splitlines():
                        rec = json.loads(ln)
                        if rec.get("tool") == "run_sql":
                            refused += bool(rec.get("refused"))
                            sqlerr += bool(rec.get("is_error")) and not rec.get("refused")
            g = [r["grade"] for r in rows]
            out.setdefault(label, []).append({
                "rep": rep, "answers": len(rows), "strict": g.count("strict"),
                "core": g.count("core"), "fail": g.count("fail"),
                "core_or_strict": g.count("strict") + g.count("core"),
                "unsafe": sum(r["safety"] == "unsafe" for r in rows), "out_of_turns": outs,
                "cost_usd": round(cost, 2), "cost_per_answer": round(cost / max(1, len(rows)), 2),
                "tool_calls_median": st.median(calls) if calls else None,
                "answers_using_sor_tools": sor, "gate_refusals": refused, "sql_errors": sqlerr,
            })  # fmt: skip
    (HERE / "summary.json").write_text(json.dumps(out, indent=1) + "\n")
    hdr = ("| Arm | Run | strict | core | fail | unsafe | out of turns | $ / answer | median tool "
           "calls | answers using sor tools | gate refusals | SQL errors |")
    lines = [hdr, "|" + "---|" * 12]
    for label, runs in out.items():
        for r in runs:
            lines.append(f"| {label} | {r['rep']} | {r['strict']} | {r['core']} | {r['fail']} | "
                         f"{r['unsafe']} | {r['out_of_turns']} | {r['cost_per_answer']} | "
                         f"{r['tool_calls_median']} | {r['answers_using_sor_tools']} | "
                         f"{r['gate_refusals']} | {r['sql_errors']} |")  # fmt: skip
    for label in ("G", "GD", "GS"):
        runs = out[label]
        mean = lambda k: round(st.mean(float(r[k]) for r in runs), 2)  # noqa: E731
        lines.append(f"| **{label} mean** | {len(runs)} runs | {mean('strict')} | {mean('core')} | "
                     f"{mean('fail')} | {mean('unsafe')} | | {mean('cost_per_answer')} | | | | |")  # fmt: skip
    total = er.cost_so_far(HERE)
    lines += ["", f"Folder spend: ${total:.2f} of the $200 stop."]
    (HERE / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
