"""Shared test helpers for the pre-flight tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from preflight.markers import collect_markers


def write_config(run: Path, text: str) -> None:
    """Write a run's preflight.yaml."""
    (run / "preflight.yaml").write_text(text)


def fake_git(args: list[str]) -> str:
    """Stand in for `git config --get <key>`."""
    return {"user.name": "ada-ops", "user.email": "ada.ops@example.test"}[args[-1]]


MARKERS = collect_markers(Path("/w/shiny-waffle"), date(2026, 10, 20), "/Users/ada", fake_git)
