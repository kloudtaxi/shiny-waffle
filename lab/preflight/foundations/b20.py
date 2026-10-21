"""B-20, read through its K1 API (documents and facts only)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from preflight.foundations import FoundationSnapshot


class B20Foundation:
    """B-20 exposes counts only; jobs, documents and the log need an attestation."""

    kind = "b20"

    def __init__(self, contract: Any, kbs: dict[str, str]) -> None:
        self.contract = contract
        self.kbs = kbs

    def snapshot(self, since: datetime) -> FoundationSnapshot:
        counts: dict[str, int] = {}
        for corpus, kb in self.kbs.items():
            docs = self.contract.pages(f"/kbs/{kb}/documents", {"limit": 100})
            counts[f"{corpus}.documents"] = len(docs)
            counts[f"{corpus}.facts"] = sum(
                len(self.contract.pages(f"/kbs/{kb}/facts", {"doc_id": d["doc_id"], "limit": 500}))
                for d in docs
            )
        return FoundationSnapshot(
            at=datetime.now(UTC),
            counts=counts,
            settings={},
            binary_sha256=None,
            jobs_active=None,
            jobs_failed_since=None,
            documents_unfinished=None,
            log_errors=None,
        )
