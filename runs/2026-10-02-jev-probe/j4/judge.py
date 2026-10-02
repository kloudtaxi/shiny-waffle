"""J4, step 2: Jev judges the sampled duplicate pairs; compare it with gpt-4o against lab truth.

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-02-jev-probe/j4/judge.py [--replay]

The design is in `../plan-2.md`. Jev sees the same records the governance adjudicator saw (name,
type, also-known-as, top four facts as of the decision time), but not Utopia's identity rulebook.
The question is neutral.

Decisions:
- **Jev:** `same` with confidence ≥ 0.5 means merge; `different` with confidence ≥ 0.5 means keep;
  anything else is routed to a human.
- **gpt-4o:** an applied merge or keep is acted on; a proposal, or "unsure", is routed.

Outputs: `judged.jsonl`, `results.md`.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(LAB / "lab/decision_engine"))
from engine import Recorder, Replay, TypeSafe, request_hash  # noqa: E402

MODEL = "jev-1.13.0"
CALLS = HERE / "engine-calls.jsonl"
Q_SAME = {
    "type": "choice",
    "instructions": "Do `record_a` and `record_b` refer to the same real-world thing?",
    "criteria": {
        "same": "Yes: the same real-world thing",
        "different": "No: two different things",
        "unsure": "Cannot tell from these records",
    },
}
SYSTEM_CHARS = 6700  # Utopia's adjudication system prompt, IDENTITY_RULES included (~5,213)
BATCH = 12  # governance.rs BATCH_SIZE
GPT4O_IN, GPT4O_OUT = 2.50, 10.00  # $ per million tokens: assumed list price, stated as such
JEV_IN = 0.042


def side(s: dict[str, Any]) -> dict[str, Any]:
    return {"name": s["name"], "type": s["type"], "also_known_as": s["also_known_as"],
            "facts": s["facts"]}  # fmt: skip


def utopia_render(s: dict[str, Any]) -> str:
    facts = "\n".join(f"  - {f}" for f in s["facts"]) or "  (no recorded facts)"
    return f'"{s["name"]}" ({s["type"]})\n{facts}'


def gpt_call(r: dict[str, Any]) -> str:
    if r["action"] == "unsure" or r["status"] != "applied":
        return "route"
    return r["action"]


def jev_call(ans: dict[str, Any]) -> str:
    if ans["confidence"] < 0.5 or ans["choice"] == "unsure":
        return "route"
    return "merge" if ans["choice"] == "same" else "keep"


def tally(rows: list[dict[str, Any]], who: str) -> dict[str, int]:
    c = Counter()
    for r in rows:
        call = r[who]
        c["n"] += 1
        c[call] += 1
        c["false_merge"] += call == "merge" and r["label"] == "different"
        c["missed_merge"] += call == "keep" and r["label"] == "same"
        c["right"] += (call == "merge") == (r["label"] == "same") and call != "route"
    return dict(c)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    eng = Replay(CALLS, MODEL) if a.replay else Recorder(TypeSafe(MODEL), CALLS)
    rows = [json.loads(line) for line in (HERE / "pairs.jsonl").read_text().splitlines()]

    def judge(r: dict[str, Any]) -> dict[str, Any]:
        state = {"record_a": side(r["left"]), "record_b": side(r["right"])}
        ans = eng.ask(state, {"same": Q_SAME})["answers"]["same"]
        return {"review_id": r["review_id"], "label": r["label"], "composite": r["composite"],
                "kinds": f"{r['left_obj'][0]}~{r['right_obj'][0]}",
                "stratum": "gpt4o_keep_sample" if gpt_call(r) == "keep" else f"gpt4o_{gpt_call(r)}",
                "gpt4o": gpt_call(r), "gpt4o_reason": r["reason"],
                "jev": jev_call(ans), "jev_choice": ans["choice"],
                "jev_conf": ans["confidence"], "p_same": ans["probabilities"].get("same", 0.0),
                "a": r["left_name"], "b": r["right_name"],
                "prompt_chars": len(utopia_render(r["left"]))
                                + len(utopia_render(r["right"]))}  # fmt: skip

    with ThreadPoolExecutor(8) as pool:
        out = list(pool.map(judge, rows))
    (HERE / "judged.jsonl").write_text(
        "".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out)
    )

    lines = ["# J4: Jev against gpt-4o on Utopia's duplicate queue (sample)", ""]
    for title, sel in [
        ("All sampled pairs", lambda o: True),
        ("Excluding composite 'SO-n C-m' names", lambda o: not o["composite"]),
        ("Stratum: pairs gpt-4o merged", lambda o: o["stratum"] == "gpt4o_merge"),
        ("Stratum: pairs gpt-4o routed (unsure or proposed)",
         lambda o: o["stratum"] == "gpt4o_route"),
        ("Stratum: random 1,000 of gpt-4o's applied keeps",
         lambda o: o["stratum"] == "gpt4o_keep_sample"),
    ]:  # fmt: skip
        rs = [o for o in out if sel(o)]
        g, j = tally(rs, "gpt4o"), tally(rs, "jev")
        same = sum(o["label"] == "same" for o in rs)
        lines += [f"## {title} (n = {len(rs)}, truly same = {same})", "",
                  "| | merge | keep | routed | false merges | missed merges | right when acting |",
                  "|---|---|---|---|---|---|---|"]  # fmt: skip
        for name, t in (("gpt-4o", g), ("Jev", j)):
            acted = t.get("merge", 0) + t.get("keep", 0)
            lines.append(f"| {name} | {t.get('merge', 0)} | {t.get('keep', 0)} | "
                         f"{t.get('route', 0)} | {t['false_merge']} | {t['missed_merge']} | "
                         f"{t['right']}/{acted} |")  # fmt: skip
        lines.append("")

    # Jev calibration on P(same)
    bins: list[list[dict[str, Any]]] = [[] for _ in range(10)]
    for o in out:
        bins[min(int(o["p_same"] * 10), 9)].append(o)
    ece = sum(len(b) / len(out) * abs(sum(o["p_same"] for o in b) / len(b)
                                     - sum(o["label"] == "same" for o in b) / len(b))
              for b in bins if b)  # fmt: skip
    lines += [f"**Jev ECE on P(same): {ece:.3f}** (n = {len(out)})", ""]

    # Cost
    calls = {json.loads(line)["hash"]: json.loads(line) for line in CALLS.read_text().splitlines()}
    used = [request_hash(MODEL, {"record_a": side(r["left"]), "record_b": side(r["right"])},
                         {"same": Q_SAME}) for r in rows]  # fmt: skip
    jev_tokens = sum(calls[x]["response"]["usage"]["input_tokens"] for x in used)  # this run only
    gpt_in = sum((o["prompt_chars"] + 60 + SYSTEM_CHARS / BATCH) / 4 for o in out)
    gpt_out = 40 * len(out)
    gpt_cost = gpt_in * GPT4O_IN / 1e6 + gpt_out * GPT4O_OUT / 1e6
    jev_cost = jev_tokens * JEV_IN / 1e6
    lines += [
        f"**Cost on these {len(out)} pairs:** Jev ${jev_cost:.4f} measured "
        f"({jev_tokens:,} input tokens). gpt-4o about ${gpt_cost:.2f} estimated "
        f"({gpt_in:,.0f} input and {gpt_out:,} output tokens at ${GPT4O_IN}/${GPT4O_OUT} per "
        f"million, system prompt shared across batches of {BATCH}). Ratio "
        f"{jev_cost / gpt_cost:.2%}.",
    ]
    (HERE / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
