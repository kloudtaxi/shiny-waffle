"""Every refusal message in the committed register-attack results is unchanged: replay each sealed
case through `registrar.apply` and compare each step with `results.json` (decisions_moved needs the
kernel and is left out)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from ._registrar import ATTACKS, registrar

CASES = ATTACKS / "sealed/cases"
RESULTS = {r["case"]: r for r in json.loads((ATTACKS / "results.json").read_text())}
PATHS = sorted(CASES.glob("*.yaml"))


def replay(path: Path) -> list[dict[str, Any]]:
    case = yaml.safe_load(path.read_text())
    acting = {str(x) for x in case.get("acting_as") or []}
    staff = registrar.Staff.load()
    state = registrar.State.bootstrap(case.get("corpus", "base"))
    steps: list[dict[str, Any]] = []
    for i, ch in enumerate(case.get("changes") or []):
        text = (CASES / ch["text"]).read_text() if ch.get("text") else None
        step: dict[str, Any] = {"change": i + 1, "action": ch.get("action")}
        try:
            state = registrar.apply(state, ch, text, acting, staff=staff)
            step["result"] = "admitted"
        except registrar.RefusedError as e:
            step |= {"result": "refused", "rule": e.rule, "why": str(e)}
        except Exception as e:  # noqa: BLE001 - a malformed case is refused, and counted
            step |= {"result": "refused", "rule": "malformed",
                     "why": f"{type(e).__name__}: {e}"[:200]}  # fmt: skip
        steps.append(step)
    return steps


def test_all_cases_present() -> None:
    assert len(PATHS) == 24 and {p.stem for p in PATHS} == set(RESULTS)


@pytest.mark.parametrize("path", PATHS, ids=lambda p: p.stem)
def test_steps_match_committed_results(path: Path) -> None:
    assert replay(path) == RESULTS[path.stem]["steps"]
