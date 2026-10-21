"""The lab's own state: the commit and whether its code tree is clean."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from preflight.record import Value

_SOURCE = "git rev-parse HEAD · git status"


@dataclass(frozen=True)
class LabObservation:
    commit: str
    dirty_paths: list[str]


def run_git(repo: Path, args: list[str]) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return done.stdout


def _dirty(porcelain: str) -> list[str]:
    paths: list[str] = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        code, path = line[:2], line[3:].split(" -> ")[-1].strip('"')
        if code == "??":
            if path.startswith("lab/") and "__pycache__" not in path:
                paths.append(path)
        elif path.startswith(("lab/", "src/")):
            paths.append(path)
    return paths


def observe_lab(repo: Path, git: Callable[[list[str]], str] | None = None) -> LabObservation:
    """Read HEAD and the dirty code paths (tracked changes, plus untracked files under lab/)."""
    run = git if git is not None else (lambda args: run_git(repo, args))
    commit = run(["rev-parse", "HEAD"]).strip()
    status = run(["status", "--porcelain=v1", "--", "lab", "src"])
    return LabObservation(commit=commit, dirty_paths=_dirty(status))


def lab_values(obs: LabObservation) -> list[Value]:
    return [
        Value(
            field="lab.commit",
            label="Lab commit",
            group="lab",
            value=obs.commit,
            source=_SOURCE,
            state="read",
            compare="record",
        ),
        Value(
            field="lab.clean",
            label="Lab code tree clean",
            group="lab",
            value=not obs.dirty_paths,
            source=_SOURCE,
            state="read",
            compare="true",
        ),
    ]
