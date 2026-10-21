"""A local foundation: nothing to read."""

from __future__ import annotations

from datetime import UTC, datetime

from preflight.foundations import FoundationSnapshot


class LocalFoundation:
    """The lab's own code under test; there is no server to inspect."""

    kind = "local"

    def snapshot(self, since: datetime) -> FoundationSnapshot:
        return FoundationSnapshot(
            at=datetime.now(UTC),
            counts={},
            settings={},
            binary_sha256=None,
            jobs_active=None,
            jobs_failed_since=None,
            documents_unfinished=None,
            log_errors=None,
        )
