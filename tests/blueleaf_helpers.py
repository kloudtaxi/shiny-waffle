"""Shared helpers for the BlueLeaf MCP server's tests (plan, task 2).

Each one stands in for a piece the build hasn't reached yet and raises `NotImplementedError`
naming the task that fills it in, so a test that needs it fails for that reason and no other.
"""

from __future__ import annotations

from pathlib import Path


def open_session(home: Path, arm: str, scenarios: list[str]) -> Path:
    """Prepare `home` (a `BLUELEAF_HOME`) with a clean sandbox and an open subject session on
    `scenarios` for `arm`, and return the path of its `subject.json`."""
    raise NotImplementedError("task 19 builds open_subject_session")


def scripted_session(home: Path, runs: Path) -> None:
    """Drive both servers through a whole session (plan, task 23): sandboxes, edits, a register
    change, a procedure, decisions, a subject session and its answers, and `promote` to `runs`."""
    raise NotImplementedError("task 23 builds the scripted session")
