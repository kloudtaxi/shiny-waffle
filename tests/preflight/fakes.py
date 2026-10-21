"""Shared test helpers for the pre-flight tests."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from preflight.markers import collect_markers


def write_config(run: Path, text: str) -> None:
    """Write a run's preflight.yaml."""
    (run / "preflight.yaml").write_text(text)


def fake_git(args: list[str]) -> str:
    """Stand in for `git config --get <key>`."""
    return {"user.name": "ada-ops", "user.email": "ada.ops@example.test"}[args[-1]]


MARKERS = collect_markers(Path("/w/shiny-waffle"), date(2026, 10, 20), "/Users/ada", fake_git)


def stream(
    *,
    init: dict[str, Any] | None = None,
    answer: str = "",
    cost: float | None = 0.0,
    extra: list[dict[str, Any]] | None = None,
) -> str:
    """A stream-json transcript: an optional init event, extra events, then the result."""
    events: list[dict[str, Any]] = []
    if init is not None:
        events.append({"type": "system", "subtype": "init", **init})
    events.extend(extra or [])
    result: dict[str, Any] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": answer,
    }
    if cost is not None:
        result["total_cost_usd"] = cost
    events.append(result)
    return "".join(json.dumps(e) + "\n" for e in events)
