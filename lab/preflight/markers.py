"""Runtime markers: values an agent should not know, found and redacted but never stored.

A marker is a value (operator identity, home path, repo name, today's date) that a probed
agent must not be able to name. Only the kinds are ever recorded; the values live in memory
for the length of one check.

A value matches only as a whole: not preceded or followed by a letter, a digit, a hyphen or an
underscore (F-8). So a git name "claude" doesn't mark "claude-opus-5-5", while `/Users/ada/x`
still holds the home `/Users/ada`, since `/` is a boundary.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

MarkerKind = Literal["operator", "home", "repo", "date"]

MIN_LENGTH = 4
_BEFORE = r"(?<![A-Za-z0-9_-])"
_AFTER = r"(?![A-Za-z0-9_-])"


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


def collect_markers(
    repo: Path, days: date | Sequence[date], home: str, git: Callable[[list[str]], str]
) -> Markers:
    """Build the markers from injected sources; `days` are every date that counts as today."""
    name = git(["config", "--get", "user.name"])
    email = git(["config", "--get", "user.email"])
    today = [days] if isinstance(days, date) else list(days)
    return Markers(
        {
            "operator": _clean([name, email, email.split("@", 1)[0]]),
            "home": _clean([home, Path(home).name]),
            "repo": _clean([repo.name]),
            "date": _clean([form for day in today for form in _dates(day)]),
        }
    )


def default_markers(repo: Path, days: Sequence[date]) -> Markers:
    """Markers from the real home directory and the repo's git config."""

    def git(args: list[str]) -> str:
        done = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
        )
        return done.stdout.strip()

    return collect_markers(repo, days, str(Path.home()), git)


def _whole(value: str) -> re.Pattern[str]:
    return re.compile(_BEFORE + re.escape(value) + _AFTER, re.IGNORECASE)


def found_kinds(text: str, markers: Markers) -> set[str]:
    """The kinds with at least one value in `text` as a whole, ignoring case."""
    return {kind for kind, vs in markers.values.items() if any(_whole(v).search(text) for v in vs)}


def redact(text: str, markers: Markers, kinds: Collection[str] | None = None) -> str:
    """Replace every marker value (of `kinds`, default all) with `<marker:kind>`.

    Longest first, ignoring case, whole values only.
    """
    pairs = sorted(
        (
            (v, kind)
            for kind, vs in markers.values.items()
            if kinds is None or kind in kinds
            for v in vs
        ),
        key=lambda p: len(p[0]),
        reverse=True,
    )
    for value, kind in pairs:
        text = _whole(value).sub(f"<marker:{kind}>", text)
    return text
