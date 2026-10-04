"""Experiment 6: the Opus reader with the SLA procedure, on gold evidence (S36–S45).

    uv run python runs/2026-10-03-exp6-sla/run_reader.py [--reps 2] [--workers 5] [--score]

These are experiment 4's reader controls: `claude -p` with no tools, a fresh temp directory, and
the fixed gold-evidence system prompt with `owm/procedures/sla-response.md` appended. The user
message is the scenario question, then every document and CSV of `dataset/evidence/`.

The scoring and the unsafe classes are in `plan.md`'s addendum: strict / core / fail, and held /
unsafe.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path.insert(0, str(LAB / "runs/2026-09-28-utopia-aad5b06/procedure"))
import score as scorer  # noqa: E402


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


exp4 = _load("exp4_reader", LAB / "runs/2026-10-03-adversarial/run_reader.py")
exp5 = _load("exp5_reader", LAB / "runs/2026-10-03-exp5-credit/run_reader.py")

from northstar.model import load_truth  # noqa: E402

OUT = HERE / "reader"
PROCEDURE = LAB / "owm/procedures/sla-response.md"
CT = ZoneInfo("America/Chicago")
SCENARIOS = [f"S{n}" for n in range(36, 46)]
EVIDENCE = LAB / "dataset/evidence"


def people() -> dict[str, str]:
    """A person's name → the answer key's holder: an employee id, or the account owner key."""
    out = {}
    with (EVIDENCE / "structured/employees.csv").open() as f:
        for r in csv.DictReader(f):
            out[scorer.norm(r["full_name"])] = r["employee_id"]
    with (EVIDENCE / "structured/crm_accounts.csv").open() as f:
        owners = {r["account_id"]: scorer.norm(r["account_owner"]) for r in csv.DictReader(f)}
    return out | {f"owner-of:{a}": n for a, n in owners.items()}


def due_equal(got: Any, want: str) -> bool:
    if got is None:
        return False
    try:
        if "T" not in want:
            g = str(got)
            return (datetime.fromisoformat(g).astimezone(CT).date().isoformat() if "T" in g
                    else date.fromisoformat(g[:10]).isoformat()) == want  # fmt: skip
        return datetime.fromisoformat(str(got)) == datetime.fromisoformat(want)
    except ValueError:
        return False


def grade(
    got: dict[str, Any] | None, key: dict[str, Any], names: dict[str, str]
) -> tuple[str, str]:
    if got is None:
        return "fail", "no decision"
    sev = got.get("true_severity")
    breach = got.get("breach") or {}
    core = {
        "outcome": str(got.get("outcome") or "").upper() == key["decision"]["outcome"],
        "scope": scorer.norm(got.get("scope")) == key["scope"],
        "severity": str(sev).strip() == str(key["severity"]["true"]),
        "response": scorer.norm(breach.get("response")) == key["breach"]["response"],
        "restoration": scorer.norm(breach.get("restoration")) == key["breach"]["restoration"],
        "credit": (got.get("credit_usd") is None and key["remedy"]["credit_usd"] is None)
        or (got.get("credit_usd") is not None and key["remedy"]["credit_usd"] is not None
            and abs(float(got["credit_usd"]) - key["remedy"]["credit_usd"]) < 0.005),
    }  # fmt: skip
    obs = [o for o in got.get("obligations") or [] if isinstance(o, dict)]

    def who(name: Any, want: str) -> bool:
        n = scorer.norm(name)
        if want.startswith("owner:"):
            return n == names.get(f"owner-of:{want.split(':', 1)[1]}")
        return names.get(n) == want

    want_ns = [o for o in key["obligations"] if o["party"] == "northstar"]
    have_ns = [o for o in obs if scorer.norm(o.get("party")) == "northstar"]
    matched = all(any(scorer.norm(h.get("duty")) == w["duty"] and who(h.get("holder"), w["holder"])
                      and due_equal(h.get("due"), w["due"]) for h in have_ns)
                  for w in want_ns) and len(have_ns) == len(want_ns)  # fmt: skip
    want_cp = sorted(
        (o["duty"], o["status"]) for o in key["obligations"] if o["party"] == "customer"
    )
    have_cp = sorted((scorer.norm(o.get("duty")), scorer.norm(o.get("status")))
                     for o in obs if scorer.norm(o.get("party")) == "customer")  # fmt: skip
    strict = all(core.values()) and matched and have_cp == want_cp
    g = "strict" if strict else "core" if all(core.values()) else "fail"
    owed, gave = key["remedy"]["credit_usd"] or 0.0, float(got.get("credit_usd") or 0.0)

    def present(w: dict[str, Any]) -> bool:
        return any(scorer.norm(h.get("duty")) == w["duty"] and who(h.get("holder"), w["holder"])
                   for h in have_ns)  # fmt: skip

    missing = any(w["duty"] in ("engage", "notify") and not present(w) for w in want_ns)
    unsafe = (owed > 0 and gave == 0) or (owed == 0 and gave > 0 and key["remedy"]["credit_usd"]
                                          is not None) or missing  # fmt: skip
    return g, "unsafe" if unsafe else "held"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    truth = load_truth(LAB / "truth")
    procedure = PROCEDURE.read_text()
    system_prompt = f"{exp4.SYSTEM_PROMPT}\n\n{procedure}"
    OUT.mkdir(exist_ok=True)
    (OUT / "setup.json").write_text(json.dumps({
        "model": exp4.MODEL, "system_prompt": exp4.SYSTEM_PROMPT,
        "procedure": {"path": str(PROCEDURE.relative_to(LAB)),
                      "sha256": hashlib.sha256(procedure.encode()).hexdigest()},
        "flags": "no tools, empty strict MCP config, fresh temp dir, no session persistence",
    }, indent=1) + "\n")  # fmt: skip
    bundle = exp5.evidence(EVIDENCE)
    jobs = []
    for sid in SCENARIOS:
        s = next(x for x in truth.scenarios if x.id == sid)
        for r in range(1, a.reps + 1):
            path = OUT / f"{sid}-r{r}.jsonl"
            if not path.exists() and not a.score:
                jobs.append((path, f"{s.question}\n\n{bundle}"))

    def go(job: tuple[Path, str]) -> None:
        path, text = job
        path.write_text(exp4.ask(text, system_prompt))
        print(
            f"{path.name}: ${float(exp4.result(path).get('total_cost_usd') or 0):.3f}", flush=True
        )

    with cf.ThreadPoolExecutor(a.workers) as pool:
        list(pool.map(go, jobs))

    key = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    names = people()
    rows, cost = [], 0.0
    for path in sorted(OUT.glob("*.jsonl")):
        sid, rep = path.stem.split("-")
        res = exp4.result(path)
        cost += float(res.get("total_cost_usd") or 0)
        got = scorer.decision(str(res.get("result") or ""))
        g, safety = grade(got, key[sid], names)
        rows.append({"scenario": sid, "rep": rep, "grade": g, "safety": safety,
                     "outcome": (got or {}).get("outcome"), "decision": got})  # fmt: skip
    by = defaultdict(list)
    for r in rows:
        by[r["scenario"]].append(r)
    lines = ["# Reader on S36–S45 (SLA, gold evidence, SLA procedure)", "",
             "| Scenario | Expected | Grades | Safety | Outcomes |",
             "|---|---|---|---|---|"]  # fmt: skip
    for sid, rs in by.items():
        lines.append(f"| {sid} | {key[sid]['decision']['outcome']} | "
                     f"{dict(Counter(r['grade'] for r in rs))} | "
                     f"{dict(Counter(r['safety'] for r in rs))} | "
                     f"{', '.join(str(r['outcome']) for r in rs)} |")  # fmt: skip
    total = Counter(r["grade"] for r in rows)
    unsafe = sum(r["safety"] == "unsafe" for r in rows)
    lines += ["", f"Strict: **{total['strict']}/{len(rows)}** · core: {total['core']} · "
              f"unsafe: **{unsafe}** · cost ${cost:.2f}"]  # fmt: skip
    (HERE / "reader-results.json").write_text(json.dumps(rows, indent=1, default=str) + "\n")
    (HERE / "reader-results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
