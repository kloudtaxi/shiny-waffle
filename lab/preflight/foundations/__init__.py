"""Foundations: the knowledge system under test, read for the settled and fingerprint checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from preflight.config import FoundationConfig


@dataclass(frozen=True)
class FoundationSnapshot:
    """One read of a foundation. `None` signals cannot be read from this machine."""

    at: datetime  # aware, UTC
    counts: dict[str, int]
    settings: dict[str, str]
    binary_sha256: str | None
    jobs_active: int | None
    jobs_failed_since: int | None
    documents_unfinished: int | None
    log_errors: list[str] | None  # matching lines, each cut to 200 chars


class Foundation(Protocol):
    """Anything that can be read into a snapshot."""

    kind: str

    def snapshot(self, since: datetime) -> FoundationSnapshot: ...


def make_foundation(cfg: FoundationConfig, run: Path, repo: Path) -> Foundation:
    """Build the foundation a run's config names."""
    from preflight.config import LogSource
    from preflight.foundations.b20 import B20Foundation
    from preflight.foundations.local import LocalFoundation
    from preflight.foundations.utopia import UtopiaFoundation

    if cfg.kind == "local":
        return LocalFoundation()
    if cfg.kind == "b20":
        from contract_reader.client import bearer

        assert cfg.arm is not None
        arm = json.loads((run / "arms.json").read_text())["arms"][cfg.arm]
        contract = bearer(arm["url"], repo / arm["token_file"])
        return B20Foundation(contract, dict(arm["kbs"]))
    assert cfg.kbs and cfg.db_container and cfg.binary and cfg.log
    log = cfg.log
    if log.file is not None:
        log = LogSource(file=str(repo / log.file))
    return UtopiaFoundation(cfg.kbs, cfg.db_container, repo / cfg.binary, log, cfg.error_pattern)
