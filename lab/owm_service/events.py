"""The append-only event log and its projection tables (spec §5).

One SQLite table, `events`, records every state change. Two projection tables, `clearances` and
`executions`, are written in the same transaction as their event and can be rebuilt from the log.
The log knows nothing about what a decision or a clearance means: it stores and projects rows.

Every `actor` and `payload` is JSON-serialisable (dict, list, str, int, float, bool, None);
anything else raises `TypeError` before a row is written. `at` (demo time) and `wall` (real time)
are stored as ISO 8601 strings with an offset.

Payload shapes the projections are rebuilt from (Task 13 writes these events):

* `clearance.attempted` with `{"issued": true, "clearance": {...}}` where `clearance` carries the
  `ClearanceRow` fields: `id`, `org`, `decision_id`, `decision_version`, `action`, `subject`,
  `bound` (a JSON object: the bound params and the actor), `expires_at` (ISO string). `used_at`
  is absent or null. A refused or dry-run attempt (`"issued": false`) projects nothing.
* `clearance.redeemed` with the `ExecutionRow` fields: `org`, `subject`, `action`, `decision_id`,
  `version`, `clearance_id`, `redeemed_at` (ISO string). It projects an `executions` row and sets
  the clearance's `used_at` to `redeemed_at`.
* `execution.reported` touches neither projection: a failed report stays spent.

Concurrency: a new connection per transaction (WAL, `BEGIN IMMEDIATE`, busy timeout of 30 s).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Collection, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    wall TEXT NOT NULL,
    org TEXT NOT NULL,
    stream TEXT NOT NULL,
    kind TEXT NOT NULL,
    actor TEXT,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_org_stream ON events (org, stream, seq);
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
CREATE TABLE IF NOT EXISTS counters (
    org TEXT NOT NULL, prefix TEXT NOT NULL, n INTEGER NOT NULL,
    PRIMARY KEY (org, prefix)
);
CREATE TABLE IF NOT EXISTS clearances (
    id TEXT PRIMARY KEY,
    org TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    decision_version INTEGER NOT NULL,
    action TEXT NOT NULL,
    subject TEXT NOT NULL,
    bound TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT
);
CREATE TABLE IF NOT EXISTS executions (
    org TEXT NOT NULL,
    subject TEXT NOT NULL,
    action TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    clearance_id TEXT NOT NULL,
    redeemed_at TEXT NOT NULL,
    UNIQUE (org, subject, action)
);
"""


@dataclass(frozen=True)
class Event:
    seq: int
    at: datetime
    wall: datetime
    org: str
    stream: str
    kind: str
    actor: dict[str, Any] | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class ClearanceRow:
    id: str
    org: str
    decision_id: str
    decision_version: int
    action: str
    subject: str
    bound: dict[str, Any]
    expires_at: str
    used_at: str | None = None


@dataclass(frozen=True)
class ExecutionRow:
    org: str
    subject: str
    action: str
    decision_id: str
    version: int
    clearance_id: str
    redeemed_at: str


def _dumps(value: Any, what: str) -> str:
    try:
        return json.dumps(value, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{what} is not JSON-serialisable: {exc}") from exc


def _event(r: sqlite3.Row) -> Event:
    return Event(
        seq=r["seq"],
        at=datetime.fromisoformat(r["at"]),
        wall=datetime.fromisoformat(r["wall"]),
        org=r["org"],
        stream=r["stream"],
        kind=r["kind"],
        actor=None if r["actor"] is None else json.loads(r["actor"]),
        payload=json.loads(r["payload"]),
    )


def _clearance(r: sqlite3.Row) -> ClearanceRow:
    return ClearanceRow(
        id=r["id"],
        org=r["org"],
        decision_id=r["decision_id"],
        decision_version=r["decision_version"],
        action=r["action"],
        subject=r["subject"],
        bound=json.loads(r["bound"]),
        expires_at=r["expires_at"],
        used_at=r["used_at"],
    )


def _execution(r: sqlite3.Row) -> ExecutionRow:
    return ExecutionRow(
        org=r["org"],
        subject=r["subject"],
        action=r["action"],
        decision_id=r["decision_id"],
        version=r["version"],
        clearance_id=r["clearance_id"],
        redeemed_at=r["redeemed_at"],
    )


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_SCHEMA)
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            conn.execute("COMMIT")
        finally:
            conn.close()

    @contextmanager
    def _reader(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    def append(
        self,
        tx: sqlite3.Connection,
        *,
        at: datetime,
        org: str,
        stream: str,
        kind: str,
        actor: dict[str, Any] | None,
        payload: dict[str, Any],
        wall: datetime | None = None,
    ) -> Event:
        actor_json = None if actor is None else _dumps(actor, "actor")
        payload_json = _dumps(payload, "payload")
        wall = wall or datetime.now().astimezone()
        cur = tx.execute(
            "INSERT INTO events (at, wall, org, stream, kind, actor, payload) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (at.isoformat(), wall.isoformat(), org, stream, kind, actor_json, payload_json),
        )
        assert cur.lastrowid is not None
        return Event(cur.lastrowid, at, wall, org, stream, kind, actor, payload)

    def read(
        self,
        org: str,
        *,
        stream: str | None = None,
        kinds: Collection[str] | None = None,
        tx: sqlite3.Connection | None = None,
    ) -> list[Event]:
        sql = "SELECT * FROM events WHERE org = ?"
        args: list[Any] = [org]
        if stream is not None:
            sql += " AND stream = ?"
            args.append(stream)
        if kinds is not None:
            sql += f" AND kind IN ({','.join('?' * len(kinds))})"
            args.extend(kinds)
        sql += " ORDER BY seq"
        if tx is not None:
            return [_event(r) for r in tx.execute(sql, args)]
        with self._reader() as conn:
            return [_event(r) for r in conn.execute(sql, args)]

    def last_seq(self, org: str, stream: str, *, tx: sqlite3.Connection | None = None) -> int:
        sql = "SELECT COALESCE(MAX(seq), 0) FROM events WHERE org = ? AND stream = ?"
        if tx is not None:
            return int(tx.execute(sql, (org, stream)).fetchone()[0])
        with self._reader() as conn:
            return int(conn.execute(sql, (org, stream)).fetchone()[0])

    def next_id(self, tx: sqlite3.Connection, org: str, prefix: str, width: int) -> str:
        tx.execute(
            "INSERT INTO counters (org, prefix, n) VALUES (?, ?, 1) "
            "ON CONFLICT (org, prefix) DO UPDATE SET n = n + 1",
            (org, prefix),
        )
        n = tx.execute(
            "SELECT n FROM counters WHERE org = ? AND prefix = ?", (org, prefix)
        ).fetchone()[0]
        return f"{prefix}-{n:0{width}d}"

    # --- projections -------------------------------------------------------------------------

    def put_clearance(self, tx: sqlite3.Connection, row: ClearanceRow) -> None:
        tx.execute(
            "INSERT INTO clearances (id, org, decision_id, decision_version, action, subject, "
            "bound, expires_at, used_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                row.id,
                row.org,
                row.decision_id,
                row.decision_version,
                row.action,
                row.subject,
                _dumps(row.bound, "bound"),
                row.expires_at,
                row.used_at,
            ),
        )

    def mark_used(self, tx: sqlite3.Connection, clearance_id: str, at: datetime) -> bool:
        cur = tx.execute(
            "UPDATE clearances SET used_at = ? WHERE id = ? AND used_at IS NULL",
            (at.isoformat(), clearance_id),
        )
        return cur.rowcount == 1

    def insert_execution(self, tx: sqlite3.Connection, row: ExecutionRow) -> bool:
        try:
            tx.execute(
                "INSERT INTO executions (org, subject, action, decision_id, version, "
                "clearance_id, redeemed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    row.org,
                    row.subject,
                    row.action,
                    row.decision_id,
                    row.version,
                    row.clearance_id,
                    row.redeemed_at,
                ),
            )
        except sqlite3.IntegrityError:
            return False
        return True

    def get_clearance(
        self, clearance_id: str, *, tx: sqlite3.Connection | None = None
    ) -> ClearanceRow | None:
        sql = "SELECT * FROM clearances WHERE id = ?"
        if tx is not None:
            r = tx.execute(sql, (clearance_id,)).fetchone()
        else:
            with self._reader() as conn:
                r = conn.execute(sql, (clearance_id,)).fetchone()
        return None if r is None else _clearance(r)

    def clearances(self) -> list[ClearanceRow]:
        with self._reader() as conn:
            return [_clearance(r) for r in conn.execute("SELECT * FROM clearances ORDER BY id")]

    def executions(self) -> list[ExecutionRow]:
        with self._reader() as conn:
            return [
                _execution(r)
                for r in conn.execute("SELECT * FROM executions ORDER BY org, subject, action")
            ]

    def rebuild_projections(self) -> None:
        """Drop and refill `clearances` and `executions` from the events (shapes: see top)."""
        with self.transaction() as tx:
            tx.execute("DELETE FROM clearances")
            tx.execute("DELETE FROM executions")
            rows = tx.execute(
                "SELECT * FROM events WHERE kind IN ('clearance.attempted', 'clearance.redeemed') "
                "ORDER BY seq"
            ).fetchall()
            for r in rows:
                ev = _event(r)
                if ev.kind == "clearance.attempted":
                    if ev.payload.get("issued") is True:
                        self.put_clearance(tx, ClearanceRow(**ev.payload["clearance"]))
                else:
                    ex = ExecutionRow(**ev.payload)
                    self.insert_execution(tx, ex)
                    self.mark_used(tx, ex.clearance_id, datetime.fromisoformat(ex.redeemed_at))
