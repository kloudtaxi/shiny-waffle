"""Where the server keeps its state, and how it writes it (plan §1, "State root"; task 3).

State lives under `.blueleaf/` at the repo root (gitignored), or wherever `BLUELEAF_HOME` points;
tests always point it at a temporary folder. `promote` writes run folders under `BLUELEAF_RUNS`,
which defaults to the repo's `runs/`. Every write is atomic, so a crash never leaves half a file
(spec §11, B12).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

LAB = Path(__file__).resolve().parents[3]


def home() -> Path:
    """The state root, created on first use."""
    root = Path(os.environ.get("BLUELEAF_HOME") or LAB / ".blueleaf")
    root.mkdir(parents=True, exist_ok=True)
    return root


def runs_root() -> Path:
    """Where `promote` writes run folders."""
    return Path(os.environ.get("BLUELEAF_RUNS") or LAB / "runs")


def atomic_write(path: Path, text: str) -> None:
    """Write `text` to `path` through a temporary file in the same folder, then `os.replace` it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
