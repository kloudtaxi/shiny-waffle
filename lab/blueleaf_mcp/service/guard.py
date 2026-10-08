"""The secret guard: nothing leaves the server carrying the TypeSafe key (spec §5; plan, task 3).

The key's text is read once, when this module is imported (server start-up), from the file named
by `TYPESAFE_API_KEY_FILE` and from `TYPESAFE_API_KEY`, whichever are set. It is never logged,
returned or stored anywhere else. Both servers pass every tool result, every error message and
every log line through `scrub` or `check_log_line` before it leaves the process; a match is
refused, never redacted, so the caller sees that something was withheld.
"""

from __future__ import annotations

import os
from pathlib import Path

from service.errors import RefusedError


def _load() -> tuple[str, ...]:
    found: list[str] = []
    path = os.environ.get("TYPESAFE_API_KEY_FILE")
    if path and Path(path).expanduser().is_file():
        found.append(Path(path).expanduser().read_text().strip())
    found.append((os.environ.get("TYPESAFE_API_KEY") or "").strip())
    return tuple(k for k in dict.fromkeys(found) if k)  # an empty key would match everything


_KEYS = _load()


def _carries_key(text: str) -> bool:
    return any(k in text for k in _KEYS)


def scrub(text: str) -> str:
    """`text`, unchanged, unless it contains the key."""
    if _carries_key(text):
        raise RefusedError("output withheld: it contained the TypeSafe key")
    return text


def check_log_line(line: str) -> str:
    """`line`, unchanged, unless it contains the key."""
    if _carries_key(line):
        raise RefusedError("log line withheld: it contained the TypeSafe key")
    return line
