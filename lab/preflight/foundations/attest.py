"""Attestations: a hand-written note from whoever can read what this machine cannot."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from preflight.config import Attest

_COMMIT = re.compile(r"^[\s>*_-]*commit[\s*_]*:[\s*_`]*([0-9a-f]{7,40})[\s*_`]*$", re.M | re.I)


@dataclass(frozen=True)
class Attestation:
    path: str
    sha256: str
    mtime: str
    covers: frozenset[str]
    commit: str | None
    fresh: bool
    max_age_hours: float


def read_attestation(cfg: Attest, run: Path, now: datetime) -> Attestation | None:
    """The attestation note, or None when it is missing."""
    f = run / cfg.file
    if not f.is_file():
        return None
    data = f.read_bytes()
    mtime = datetime.fromtimestamp(os.stat(f).st_mtime, UTC)
    age_hours = (now.astimezone(UTC) - mtime).total_seconds() / 3600
    m = _COMMIT.search(data.decode("utf-8", errors="replace"))
    return Attestation(
        path=cfg.file,
        sha256=hashlib.sha256(data).hexdigest(),
        mtime=mtime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        covers=frozenset(cfg.covers),
        commit=m.group(1).lower() if m else None,
        fresh=age_hours <= cfg.max_age_hours,
        max_age_hours=cfg.max_age_hours,
    )
