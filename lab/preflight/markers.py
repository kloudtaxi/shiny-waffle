"""Runtime markers: values an agent should not know, found and redacted but never stored.

A marker is a value (operator identity, home path, repo name, today's date) that a probed
agent must not be able to name. Only the kinds are ever recorded; the values live in memory
for the length of one check.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

MarkerKind = Literal["operator", "home", "repo", "date"]

MIN_LENGTH = 4


@dataclass(frozen=True)
class Markers:
    """Marker values by kind. Never serialise this."""

    values: dict[str, tuple[str, ...]]


def _clean(candidates: list[str]) -> tuple[str, ...]:
    """Drop empty and short values, and duplicates, keeping order."""
    seen: dict[str, None] = {}
    for c in candidates:
        c = c.strip()
        if len(c) >= MIN_LENGTH:
            seen.setdefault(c, None)
    return tuple(seen)


def _dates(today: date) -> list[str]:
    day = str(today.day)  # no zero padding, without relying on the %-d extension
    return [
        today.isoformat(),
        f"{today.strftime('%B')} {day}, {today.year}",
        f"{day} {today.strftime('%B')} {today.year}",
        f"{today.strftime('%b')} {day}, {today.year}",
    ]


def collect_markers(repo: Path, today: date, home: str, git: Callable[[list[str]], str]) -> Markers:
    """Build the markers from injected sources."""
    name = git(["config", "--get", "user.name"])
    email = git(["config", "--get", "user.email"])
    return Markers(
        {
            "operator": _clean([name, email, email.split("@", 1)[0]]),
            "home": _clean([home, Path(home).name]),
            "repo": _clean([repo.name]),
            "date": _clean(_dates(today)),
        }
    )


def default_markers(repo: Path, today: date) -> Markers:
    """Markers from the real home directory and the repo's git config."""

    def git(args: list[str]) -> str:
        done = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
        )
        return done.stdout.strip()

    return collect_markers(repo, today, str(Path.home()), git)


def found_kinds(text: str, markers: Markers) -> set[str]:
    """The kinds with at least one value in `text`, ignoring case."""
    low = text.lower()
    return {kind for kind, vs in markers.values.items() if any(v.lower() in low for v in vs)}


def redact(text: str, markers: Markers) -> str:
    """Replace every marker value with `<marker:kind>`, longest first, ignoring case."""
    pairs = sorted(
        ((v, kind) for kind, vs in markers.values.items() for v in vs),
        key=lambda p: len(p[0]),
        reverse=True,
    )
    for value, kind in pairs:
        text = re.sub(re.escape(value), f"<marker:{kind}>", text, flags=re.IGNORECASE)
    return text
