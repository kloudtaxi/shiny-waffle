"""The 24 register attack cases (runs/2026-10-08-register-attacks) through the two-step queue
(B-06 Task 20). Each step must be admitted or refused as in the one-shot registrar's committed
`results.json`. The named rule may differ only where a case breaks more than one rule, because
submit runs the content rules before approval runs RR-4. Every such difference is listed in
`fixtures/attack_rule_differences.json` and explained in the slice 2 addendum of
docs/owm-service-slice1-2026-10-11.md. Registrar-only: no kernel decision, so no Jev."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from owm_service.changes import ChangeBody
from owm_service.config import load_settings
from owm_service.errors import Refused
from owm_service.models import Actor
from owm_service.org import Org
from owm_service.register_queue import RegisterQueue
from owm_service.sessions import Sessions

ATTACKS = Path(__file__).resolve().parents[2] / "runs/2026-10-08-register-attacks"
CASES = ATTACKS / "sealed/cases"
FIXTURE = Path(__file__).parent / "fixtures/attack_rule_differences.json"
CLOCK = "2026-09-01T09:00:00-05:00"  # the registrar's fixed clock
DROP = frozenset({"submit_by", "approve_by", "file", "proposed_by", "text"})
RESULTS = {r["case"]: r for r in json.loads((ATTACKS / "results.json").read_text())}
IDS = sorted(p.stem for p in CASES.glob("*.yaml"))


def _is_employee(x: str) -> bool:
    return x.startswith("EMP-")


def _session(sessions: Sessions, acting: list[str], who: str | None) -> tuple[Actor, str | None]:
    """The session for `who` (submit_by or approve_by), and the submitted_by the body then
    carries: none when `who` acts (a person's own session, or an agent's), else the first
    employee in `acting_as` (an agent when it holds none) with `submitted_by = who`, for RR-1 to
    refuse."""
    if who is not None and who in acting:
        if _is_employee(who):
            return sessions.open_person(who)[1], None
        return sessions.open_agent(who, "EMP-101")[1], None
    employees = [a for a in acting if _is_employee(a)]
    actor = (
        sessions.open_person(employees[0])[1]
        if employees
        else sessions.open_agent("AGT-DEALDESK", "EMP-101")[1]
    )
    return actor, who


def run_case(case_id: str, root: Path) -> list[dict[str, Any]]:
    case = yaml.safe_load((CASES / f"{case_id}.yaml").read_text())
    acting = [str(x) for x in case.get("acting_as") or []]
    org = Org(
        load_settings({"OWM_STATE_DIR": str(root / case_id), "OWM_CLOCK": CLOCK}),
        corpus=case.get("corpus", "base"),
    )
    queue, sessions = RegisterQueue(org), Sessions(org)
    steps: list[dict[str, Any]] = []
    for i, ch in enumerate(case.get("changes") or []):
        step: dict[str, Any] = {"change": i + 1, "action": ch.get("action")}
        steps.append(step)
        try:
            text = (CASES / ch["text"]).read_text() if ch.get("text") else None
            submitter, submitted_by = _session(sessions, acting, ch.get("submit_by"))
            fields = {k: v for k, v in ch.items() if k not in DROP}
            extra = {"submitted_by": submitted_by} if submitted_by else {}
            body = ChangeBody.model_validate(fields | {"text": text, "submit": True} | extra)
        except (KeyError, ValidationError, TypeError, ValueError) as e:
            step |= {"result": "refused", "rule": "malformed",
                     "why": f"{type(e).__name__}: {e}"[:200]}  # fmt: skip
            continue
        try:
            change = queue.submit_new(submitter, body)
        except Refused as e:
            step |= {"result": "refused", "rule": e.refusals[0].rule}
            continue
        if ch.get("approve_by") is None:  # never approved: it can't reach approval
            step |= {"result": "refused", "rule": "RR-4"}
            continue
        approver, _ = _session(sessions, acting, ch["approve_by"])
        try:
            done = queue.approve(approver, change.change_id)
        except Refused as e:
            step |= {"result": "refused", "rule": e.refusals[0].rule}
            continue
        step["result"] = "admitted" if done.state == "approved" else "refused"
        if step["result"] == "refused":
            step["rule"] = "RR-4"
    return steps


def committed(case_id: str) -> list[dict[str, Any]]:
    return list(RESULTS[case_id]["steps"])


def differences() -> dict[str, list[list[str | None]]]:
    out: dict[str, list[list[str | None]]] = {}
    with tempfile.TemporaryDirectory(prefix="ns-attackq-") as tmp:
        for c in IDS:
            diffs = [
                [w.get("rule"), g.get("rule")]
                for g, w in zip(run_case(c, Path(tmp)), committed(c), strict=True)
                if g.get("rule") != w.get("rule")
            ]
            if diffs:
                out[c] = diffs
    return out


def test_all_cases_present() -> None:
    assert len(IDS) == 24 and set(IDS) == set(RESULTS)


@pytest.mark.parametrize("case", IDS)
def test_same_admitted_or_refused(case: str, tmp_path: Path) -> None:
    got, want = run_case(case, tmp_path), committed(case)
    assert [s["result"] for s in got] == [s["result"] for s in want]


def test_rule_differences_are_listed() -> None:
    assert differences() == json.loads(FIXTURE.read_text())


if __name__ == "__main__":
    if "--write-fixture" not in sys.argv:
        sys.exit("usage: PYTHONPATH=lab python <this file> --write-fixture")
    FIXTURE.parent.mkdir(exist_ok=True)
    FIXTURE.write_text(json.dumps(differences(), indent=2, sort_keys=True) + "\n")
    print(FIXTURE.read_text())
