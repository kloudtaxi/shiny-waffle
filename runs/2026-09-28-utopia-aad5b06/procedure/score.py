"""Score the decision-procedure runs against the lab's answer key, field by field.

    python3 runs/2026-09-28-utopia-aad5b06/procedure/score.py runs/.../procedure/arm-b/r1/B2 ...

For the discount decisions (S01-S05), the reader ends its answer with a decision JSON
(owm/procedures/discount-approval.md). That is compared with `dataset/answer-key/
expected-results.yaml`, the oracle's decision objects. The rule was fixed before the results
were seen:

- pass: outcome, commercial-eligibility status and requestor-authorized all match, and the
  approver matches whenever the expected outcome is an approval (APPROVE,
  APPROVE_WITH_AUTHORIZATION)
- partial: the outcome matches, but one of those fields does not
- fail: the outcome does not match, or there is no decision JSON

S06-S08 are not decisions and are graded by reading. Output is MLflow-shaped: per answer, one
`Feedback`-like assessment per field.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

LAB = Path(__file__).resolve().parents[3]
DECISIONS = ("S01", "S02", "S03", "S04", "S05")
APPROVALS = {"APPROVE", "APPROVE_WITH_AUTHORIZATION"}


def expected() -> dict[str, dict[str, Any]]:
    rows = yaml.safe_load((LAB / "dataset/answer-key/expected-results.yaml").read_text())
    roles = {
        r["id"]: r["title"]
        for r in yaml.safe_load((LAB / "truth/organization.yaml").read_text())["roles"]
    }
    out = {}
    for r in rows:
        if r.get("type") != "discount_approval":
            continue
        out[r["scenario"]] = {
            "outcome": r["decision"]["outcome"],
            "eligibility": r["commercial_eligibility"]["status"],
            "authorized": r["authority"]["requestor"]["authorized"],
            "required_role": roles.get(r["authority"]["required"]["role"]),
            "approver": r["authority"]["approver"]["name"],
        }
    return out


def result_text(path: Path) -> str:
    for line in path.read_text().splitlines():
        e = json.loads(line)
        if e.get("type") == "result":
            return str(e.get("result") or "")
    return ""


def decision(text: str) -> dict[str, Any] | None:
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.S)
    for block in reversed(blocks):
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "outcome" in obj:
            return obj
    return None


def norm(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip().lower()


def score(sid: str, got: dict[str, Any] | None, exp: dict[str, Any]) -> dict[str, Any]:
    if got is None:
        return {"grade": "fail", "fields": {}, "note": "no decision JSON"}
    auth = got.get("authority") or {}
    elig = got.get("commercial_eligibility") or {}
    fields = {
        "outcome": norm(got.get("outcome")) == norm(exp["outcome"]),
        "eligibility": norm(elig.get("status")) == norm(exp["eligibility"]),
        "authorized": auth.get("requestor_authorized") is exp["authorized"],
        "approver": norm(exp["approver"]) in norm(auth.get("approver")),
        "required_role": norm(exp["required_role"]) in norm(auth.get("required_role")),
    }
    must = ["outcome", "eligibility", "authorized"]
    if exp["outcome"] in APPROVALS:
        must.append("approver")
    if not fields["outcome"]:
        grade = "fail"
    elif all(fields[k] for k in must):
        grade = "pass"
    else:
        grade = "partial"
    misses = [k for k in must if not fields[k]]
    note = f"outcome {got.get('outcome')}" + (
        f"; mismatched: {', '.join(misses)}" if misses else ""
    )
    return {"grade": grade, "fields": fields, "note": note}


def main(dirs: list[str]) -> None:
    exp = expected()
    report: dict[str, Any] = {}
    for d in dirs:
        run = Path(d)
        rows = {}
        for sid in DECISIONS:
            got = decision(result_text(run / f"{sid}.jsonl"))
            rows[sid] = {"expected": exp[sid], "got": got, **score(sid, got, exp[sid])}
        report[str(run)] = rows
        line = " ".join(f"{sid}:{r['grade'][0].upper()}" for sid, r in rows.items())
        print(f"{run}: {line}")
        for sid, r in rows.items():
            if r["grade"] != "pass":
                print(f"    {sid} {r['grade']}: {r['note']}")
    out = Path(__file__).resolve().parent / "scores.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {out.relative_to(LAB)}")


if __name__ == "__main__":
    main(sys.argv[1:])
