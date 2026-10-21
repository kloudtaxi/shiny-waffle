"""Fixtures for the pre-flight tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo() -> Path:
    """The repo root."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    """A fresh run folder with a notes.md."""
    run = tmp_path / "runs" / "2026-10-21-test"
    run.mkdir(parents=True)
    (run / "notes.md").write_text("# Notes\n")
    return run
