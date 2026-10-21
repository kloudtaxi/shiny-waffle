"""Utopia, read through read-only SQL and its server log."""

from __future__ import annotations

import hashlib
import re
import subprocess
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from preflight.config import LogSource
from preflight.foundations import FoundationSnapshot

SQL: dict[str, str] = {
    "bases": "select id from knowledge_bases where id in ({kbs})",
    "settings": (
        "select workspace_id, chat_model, chat_reasoning_effort, embed_model from llm_settings "
        "where workspace_id in (select workspace_id from knowledge_bases where id in ({kbs}))"
    ),
    "documents": (
        "select kb_id, status, graph_status, count(*) from documents "
        "where kb_id in ({kbs}) and deleted_at is null group by kb_id, status, graph_status"
    ),
    "unfinished": (
        "select count(*) from documents where kb_id in ({kbs}) and deleted_at is null "
        "and not (status = 'ready' and graph_status = 'done')"
    ),
    "facts": (
        "select kb_id, layer, count(*) from facts "
        "where kb_id in ({kbs}) and invalidated_at is null group by kb_id, layer"
    ),
    "entities": "select kb_id, count(*) from entities where kb_id in ({kbs}) group by kb_id",
    "jobs_active": "select count(*) from jobs where status in ('queued', 'running')",
    "jobs_failed": ("select count(*) from jobs where status = 'failed' and updated_at > '{since}'"),
}

_STAMP = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d))")


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class UtopiaFoundation:
    """Counts, settings and signals from Utopia's database and log."""

    kind = "utopia"

    def __init__(
        self,
        kbs: dict[str, str],
        container: str,
        binary: Path,
        log: LogSource,
        error_pattern: str,
        psql: Callable[[str], list[list[str]]] | None = None,
        logs: Callable[[datetime], str] | None = None,
    ) -> None:
        # raises ValueError for a non-UUID: ids are interpolated into SQL
        self.kbs = {corpus: str(uuid.UUID(kb)) for corpus, kb in kbs.items()}
        self.container = container
        self.binary = binary
        self.log = log
        self.error_pattern = re.compile(error_pattern)
        self._psql = psql or self._docker_psql
        self._logs = logs or self._default_logs

    def _docker_psql(self, sql: str) -> list[list[str]]:
        cmd = [
            "docker", "exec", "-e", "PGOPTIONS=-c default_transaction_read_only=on",
            self.container, "psql", "-U", "utopia", "-d", "utopia", "-At", "-F", "\t", "-c", sql,
        ]  # fmt: skip
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            first = (r.stderr.splitlines() or [""])[0][:200]
            raise RuntimeError(f"psql failed: {first}")
        return [line.split("\t") for line in r.stdout.splitlines() if line]

    def _default_logs(self, since: datetime) -> str:
        """The log text since `since`; raises when the log cannot be read."""
        if self.log.docker is not None:
            cmd = ["docker", "logs", "--since", _iso(since), self.log.docker]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                first = (r.stderr.splitlines() or [""])[0][:200]
                raise RuntimeError(f"docker logs failed: {first}")
            return r.stdout + r.stderr
        assert self.log.file is not None
        out: list[str] = []
        for line in Path(self.log.file).read_text(errors="replace").splitlines():
            m = _STAMP.match(line)
            if m is None:
                out.append(line)
                continue
            try:
                t = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
            except ValueError:
                out.append(line)
                continue
            if t.tzinfo is None:
                t = t.replace(tzinfo=UTC)
            if t >= since:
                out.append(line)
        return "\n".join(out)

    def _q(self, name: str, since: datetime) -> list[list[str]]:
        kbs = ", ".join(f"'{k}'" for k in self.kbs.values())
        return self._psql(SQL[name].format(kbs=kbs, since=_iso(since)))

    def _count(self, name: str, since: datetime) -> int:
        rows = self._q(name, since)
        if not rows or not rows[0]:
            raise RuntimeError(f"psql returned no rows for {name}")
        return int(rows[0][0])

    def _read_log(self, since: datetime) -> list[str] | None:
        """Matching log lines, or None when the log cannot be read."""
        try:
            text = self._logs(since)
        except (RuntimeError, OSError, subprocess.SubprocessError):
            return None
        return [line[:200] for line in text.splitlines() if self.error_pattern.search(line)]

    def snapshot(self, since: datetime) -> FoundationSnapshot:
        since = since.astimezone(UTC)
        names = {kb: corpus for corpus, kb in self.kbs.items()}
        found = {row[0] for row in self._q("bases", since)}
        for corpus, kb in self.kbs.items():
            if kb not in found:
                raise ValueError(f"base {corpus} not found")
        counts: dict[str, int] = {}
        for kb, status, graph, n in self._q("documents", since):
            counts[f"{names[kb]}.documents.{status}/{graph}"] = int(n)
        for kb, layer, n in self._q("facts", since):
            counts[f"{names[kb]}.facts.{layer}"] = int(n)
        for kb, n in self._q("entities", since):
            counts[f"{names[kb]}.entities"] = int(n)
        settings: dict[str, str] = {}
        for ws, chat, effort, embed in self._q("settings", since):
            settings[f"{ws}.chat_model"] = chat
            settings[f"{ws}.chat_reasoning_effort"] = effort
            settings[f"{ws}.embed_model"] = embed
        errors = self._read_log(since)
        digest: str | None = None
        if self.binary.is_file():
            with self.binary.open("rb") as fh:
                digest = hashlib.file_digest(fh, "sha256").hexdigest()
        return FoundationSnapshot(
            at=datetime.now(UTC),
            counts=counts,
            settings=settings,
            binary_sha256=digest,
            jobs_active=self._count("jobs_active", since),
            jobs_failed_since=self._count("jobs_failed", since),
            documents_unfinished=self._count("unfinished", since),
            log_errors=errors,
        )
