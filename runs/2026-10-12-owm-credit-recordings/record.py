"""Record Jev's answers for the credit requests the OWM service can't replay (see notes.md).

Usage (from the repo root; the key file is read by the engine, never by this script):

    TYPESAFE_API_KEY_FILE=<key file> PYTHONPATH=lab \\
        uv run --group owm-service python runs/2026-10-12-owm-credit-recordings/record.py \\
        record <fresh state dir>
    PYTHONPATH=lab uv run --group owm-service python \\
        runs/2026-10-12-owm-credit-recordings/record.py check <another fresh state dir>

`record` asks CR-7001..CR-7010 once each, live, under a 150-call cap, and stops at the first error.
`check` runs in replay mode on a fresh state and asks all eleven credit requests as two people.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from owm_service.config import load_settings
from owm_service.decisions import Decisions
from owm_service.errors import CannotDecide
from owm_service.models import DecisionRequest
from owm_service.org import Org
from owm_service.sessions import Sessions

TO_RECORD = [f"CR-70{n:02d}" for n in range(1, 11)]
ALL_CREDIT = ["CR-9201", *TO_RECORD]
CAP = 150


def org_at(state: Path, *, live: bool) -> Org:
    env = {"OWM_STATE_DIR": str(state), "OWM_JEV": "live" if live else "replay"}
    if live:
        env["OWM_JEV_CAP"] = str(CAP)
    return Org(load_settings(env))


def ask(org: Org, emp: str, rid: str) -> str:
    actor = Sessions(org).open_person(emp)[1]
    req = DecisionRequest.model_validate(
        {"decision_type": "credit", "subject": {"request_id": rid}}
    )
    rec = Decisions(org).ask(actor, req)
    return f"{rec.decision_id} {rec.outcome} {rec.state}"


def calls_in(org: Org) -> list[dict[str, object]]:
    """The live exchanges this state recorded: the engine's own file (`<state>/<org>/...`)."""
    path: Path = org.engine.calls
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def record(state: Path) -> int:
    org = org_at(state, live=True)
    for rid in TO_RECORD:
        before = len(calls_in(org))
        try:
            got = ask(org, "EMP-101", rid)
        except CannotDecide as e:
            print(f"{rid}: STOP, cannot decide: {str(e)[:200]}")
            return 1
        print(f"{rid}: {got} (live calls {len(calls_in(org)) - before})")
    calls = calls_in(org)
    tokens_in = sum(int(c["response"]["usage"]["input_tokens"]) for c in calls)  # type: ignore[index]
    tokens_out = sum(int(c["response"]["usage"]["output_tokens"]) for c in calls)  # type: ignore[index]
    print(f"live calls: {len(calls)} of {CAP}; tokens in {tokens_in}, out {tokens_out}")
    return 0


def check(state: Path) -> int:
    bad = 0
    for emp in ("EMP-101", "EMP-401"):
        org = org_at(state / emp, live=False)
        for rid in ALL_CREDIT:
            try:
                got = ask(org, emp, rid)
            except CannotDecide as e:
                got, bad = f"503 {str(e)[:120]}", bad + 1
            print(f"{emp} {rid}: {got}")
    print("all decide" if bad == 0 else f"{bad} gave 503")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    mode, where = sys.argv[1], Path(sys.argv[2])
    sys.exit(record(where) if mode == "record" else check(where))
