"""Shared test helpers for the pre-flight tests."""

from __future__ import annotations

from pathlib import Path


def write_config(run: Path, text: str) -> None:
    """Write a run's preflight.yaml."""
    (run / "preflight.yaml").write_text(text)
