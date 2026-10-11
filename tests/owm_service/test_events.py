"""The event log: append, read, counters, the spent key and the rebuild (spec §5)."""

from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

from owm_service.events import ClearanceRow, EventLog, ExecutionRow

T = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)


def _append(log: EventLog, tx: sqlite3.Connection, kind: str = "x.y", **payload: object) -> int:
    return log.append(
        tx, at=T, org="northstar", stream="s1", kind=kind, actor={"id": "a"}, payload=dict(payload)
    ).seq


def _exec(subject: str, action: str, clearance: str) -> ExecutionRow:
    return ExecutionRow(
        org="northstar",
        subject=subject,
        action=action,
        decision_id="DEC-0001",
        version=1,
        clearance_id=clearance,
        redeemed_at=T.isoformat(),
    )


def _clr(cid: str) -> ClearanceRow:
    return ClearanceRow(
        id=cid,
        org="northstar",
        decision_id="DEC-0001",
        decision_version=1,
        action="apply_discount",
        subject="DR-9001",
        bound={"params": {"pct": 12}, "actor": "p1"},
        expires_at="2026-09-23T09:05:00+00:00",
    )


def test_append_and_read_round_trip(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    with log.transaction() as tx:
        ev = log.append(
            tx, at=T, org="northstar", stream="s1", kind="a.b", actor=None, payload={"k": [1, "x"]}
        )
        _append(log, tx, "c.d")
    got = log.read("northstar")
    assert [e.kind for e in got] == ["a.b", "c.d"]
    assert got[0] == ev
    assert got[0].payload == {"k": [1, "x"]}
    assert got[0].actor is None and got[0].at == T
    assert [e.kind for e in log.read("northstar", kinds={"c.d"})] == ["c.d"]
    assert log.read("northstar", stream="other") == []
    assert log.read("other-org") == []
    assert log.last_seq("northstar", "s1") == got[1].seq
    assert log.last_seq("northstar", "none") == 0


def test_rollback_on_error(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    with pytest.raises(RuntimeError), log.transaction() as tx:
        _append(log, tx)
        raise RuntimeError("boom")
    assert log.read("northstar") == []


def test_non_json_payload_is_rejected_early(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    with pytest.raises(TypeError), log.transaction() as tx:
        log.append(tx, at=T, org="o", stream="s", kind="k", actor=None, payload={"d": T})
    with pytest.raises(TypeError), log.transaction() as tx:
        log.append(tx, at=T, org="o", stream="s", kind="k", actor={"a": {1, 2}}, payload={})


def test_events_cannot_be_edited(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    with log.transaction() as tx:
        _append(log, tx)
    with pytest.raises(sqlite3.DatabaseError), log.transaction() as tx:
        tx.execute("UPDATE events SET kind = 'z'")
    with pytest.raises(sqlite3.DatabaseError), log.transaction() as tx:
        tx.execute("DELETE FROM events")


def test_counters_are_per_org_and_prefix(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    with log.transaction() as tx:
        assert [log.next_id(tx, "northstar", "DEC", 4) for _ in range(2)] == [
            "DEC-0001",
            "DEC-0002",
        ]
        assert log.next_id(tx, "northstar", "CLR", 5) == "CLR-00001"
        assert log.next_id(tx, "other", "DEC", 4) == "DEC-0001"
    with log.transaction() as tx:
        assert log.next_id(tx, "northstar", "DEC", 4) == "DEC-0003"


def test_execution_unique_on_subject_and_action(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    with log.transaction() as tx:
        assert log.insert_execution(tx, _exec("DR-9001", "apply_discount", "CLR-00001")) is True
        assert log.insert_execution(tx, _exec("DR-9001", "apply_discount", "CLR-00002")) is False
        assert log.insert_execution(tx, _exec("DR-9001", "other_action", "CLR-00003")) is True
    assert len(log.executions()) == 2


def test_mark_used_once(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    with log.transaction() as tx:
        log.put_clearance(tx, _clr("CLR-00001"))
        assert (log.mark_used(tx, "CLR-00001", T), log.mark_used(tx, "CLR-00001", T)) == (
            True,
            False,
        )
        assert log.mark_used(tx, "CLR-99999", T) is False
    row = log.get_clearance("CLR-00001")
    assert row is not None and row.used_at == T.isoformat() and row.bound["actor"] == "p1"


def test_rebuild_projections_equals_live(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    c1, c2 = _clr("CLR-00001"), _clr("CLR-00002")
    ex = _exec("DR-9001", "apply_discount", "CLR-00001")
    with log.transaction() as tx:
        for c in (c1, c2):
            log.put_clearance(tx, c)
            log.append(
                tx,
                at=T,
                org="northstar",
                stream="DR-9001",
                kind="clearance.attempted",
                actor=None,
                payload={"issued": True, "clearance": c.__dict__},
            )
        log.append(
            tx,
            at=T,
            org="northstar",
            stream="DR-9001",
            kind="clearance.attempted",
            actor=None,
            payload={"issued": False, "refusals": []},
        )
        assert log.insert_execution(tx, ex)
        assert log.mark_used(tx, "CLR-00001", T)
        log.append(
            tx,
            at=T,
            org="northstar",
            stream="DR-9001",
            kind="clearance.redeemed",
            actor=None,
            payload=ex.__dict__,
        )
        log.append(
            tx,
            at=T,
            org="northstar",
            stream="DR-9001",
            kind="execution.reported",
            actor=None,
            payload={"ok": False},
        )
    live = (log.clearances(), log.executions())
    log.rebuild_projections()
    assert (log.clearances(), log.executions()) == live
    assert len(live[0]) == 2 and len(live[1]) == 1


def test_concurrent_appends_both_succeed(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    seqs: list[int] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(4)

    def work() -> None:
        try:
            barrier.wait()
            for _ in range(10):
                with log.transaction() as tx:
                    seqs.append(_append(log, tx))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=work) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert len(set(seqs)) == 40 == len(log.read("northstar"))


def test_non_unique_integrity_error_is_raised(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    bad = ExecutionRow("northstar", "DR-1", "a", "DEC-0001", 1, None, T.isoformat())  # type: ignore[arg-type]
    with pytest.raises(sqlite3.IntegrityError), log.transaction() as tx:
        log.insert_execution(tx, bad)


def test_naive_at_is_rejected(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "e.db")
    with pytest.raises(ValueError), log.transaction() as tx:
        log.append(
            tx, at=datetime(2026, 9, 23), org="o", stream="s", kind="k", actor=None, payload={}
        )


def _redeemed(log: EventLog, tx: sqlite3.Connection, ex: ExecutionRow) -> None:
    log.append(
        tx,
        at=T,
        org="northstar",
        stream="s",
        kind="clearance.redeemed",
        actor=None,
        payload=ex.__dict__,
    )


def test_rebuild_raises_on_a_corrupt_log(tmp_path: Path) -> None:
    # a redemption of a clearance that was never issued: mark_used changes no row
    log = EventLog(tmp_path / "e.db")
    with log.transaction() as tx:
        _redeemed(log, tx, _exec("DR-1", "a", "CLR-00001"))
    with pytest.raises(RuntimeError, match="corrupt"):
        log.rebuild_projections()
    # the same subject/action redeemed twice: a duplicate
    log2 = EventLog(tmp_path / "f.db")
    with log2.transaction() as tx:
        for c in ("CLR-00001", "CLR-00002"):
            log2.put_clearance(tx, _clr(c))
            log2.append(
                tx,
                at=T,
                org="northstar",
                stream="s",
                kind="clearance.attempted",
                actor=None,
                payload={"issued": True, "clearance": _clr(c).__dict__},
            )
            _redeemed(log2, tx, _exec("DR-1", "a", c))
    with pytest.raises(RuntimeError, match="twice"):
        log2.rebuild_projections()
