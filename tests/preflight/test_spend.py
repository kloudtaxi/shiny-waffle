"""One spend cap per run folder, held across processes and threads."""

from __future__ import annotations

import json
import multiprocessing as mp
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from preflight.spend import CapReached, Guard, live_reservations, recorded_usd, run_folder_of
from tests.preflight import spend_worker
from tests.preflight.fakes import stream


def test_recorded_usd_counts_answers_attempts_and_judges(tmp_path: Path) -> None:
    run = tmp_path / "runs" / "r"
    (run / "a").mkdir(parents=True)
    (run / "a" / "S01.jsonl").write_text(stream(cost=1.25))
    (run / "a" / "S02.infra-error-1.jsonl").write_text(stream(cost=0.5))
    (run / "a" / "S01.calls.jsonl").write_text(stream(cost=9.0))  # never counted
    (run / "a" / "S03.jsonl").write_text(stream(cost=0.25) + "not json\n")
    (run / "preflight").mkdir()
    (run / "preflight" / "2026-10-21T09-14-02Z.probe.jsonl").write_text(stream(cost=0.1))
    judge = {"readings": [{"runs": [{"cost_usd": 0.02}, {"cost_usd": 0.03}]}]}
    (run / "a" / "base.judge.json").write_text(json.dumps(judge))
    (run / "a" / "base.judge.infra-1.json").write_text(json.dumps(judge))  # superseded (P3)
    (run / "a" / "other.judge.infra-2.json").write_text(json.dumps(judge))  # newest, no .judge.json
    (run / "a" / "other.judge.infra-1.json").write_text(json.dumps({"readings": []}))
    assert recorded_usd(run) == pytest.approx(1.25 + 0.5 + 0.25 + 0.1 + 0.05 + 0.05)


def test_five_processes_and_room_for_three(tmp_path: Path) -> None:
    run = tmp_path / "runs" / "r"
    run.mkdir(parents=True)
    (run / "S00.jsonl").write_text(stream(cost=40.0))
    ctx = mp.get_context("spawn")
    gate, done, results = ctx.Barrier(5), ctx.Barrier(6), ctx.Queue()
    procs = [
        ctx.Process(
            target=spend_worker.reserve_and_hold,
            args=(str(run), 45.0, 1.58, gate, done, results),
        )
        for _ in range(5)
    ]
    for p in procs:
        p.start()
    done.wait(timeout=60)
    got = sorted(results.get(timeout=10) for _ in range(5))
    assert got == [False, False, True, True, True]  # 40 + 3 x 1.58 = 44.74; a fourth: 46.32
    for p in procs:
        p.join(timeout=30)
    assert live_reservations(run) == []


def test_a_dead_process_reservation_is_ignored_and_removed(tmp_path: Path) -> None:
    run = tmp_path / "runs" / "r"
    run.mkdir(parents=True)
    dead = subprocess.run(
        [sys.executable, "-c", "import os; print(os.getpid())"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    stale = run / ".spend" / "inflight" / f"{dead}-x.json"
    stale.parent.mkdir(parents=True)
    stale.write_text(
        json.dumps(
            {
                "pid": int(dead),
                "label": "l",
                "item": "i",
                "est_usd": 99.0,
                "cap_usd": 100.0,
                "started": "2026-10-21T00:00:00Z",
                "settled_usd": None,
            }
        )
    )
    assert live_reservations(run) == [] and not stale.exists()
    with Guard(run, 5.0, 1.0, "t").reserve("S01"):
        pass


def test_refusal_names_every_term_and_settle_counts(tmp_path: Path) -> None:
    run = tmp_path / "runs" / "r"
    run.mkdir(parents=True)
    (run / "S00.jsonl").write_text(stream(cost=43.40))
    g = Guard(run, 45.0, 1.58, "t")
    with g.reserve("S01") as r:
        r.settle(0.10)
        assert live_reservations(run)[0].settled_usd == 0.10
        with pytest.raises(
            CapReached,
            match=r"\$43\.40 recorded \+ \$0\.10 running \+ \$1\.58 next > \$45\.00 cap",
        ):
            Guard(run, 45.0, 1.58, "t").reserve("S02")
    assert live_reservations(run) == []


def test_threads_share_one_cap(tmp_path: Path) -> None:
    run = tmp_path / "runs" / "r"
    run.mkdir(parents=True)
    g, tried, granted = Guard(run, 10.0, 1.0, "t"), threading.Barrier(16), []

    def one() -> None:
        try:
            with g.reserve("x"):
                granted.append(1)
                tried.wait(10)  # hold until every thread has tried
        except CapReached:
            tried.wait(10)

    ts = [threading.Thread(target=one) for _ in range(15)]
    for t in ts:
        t.start()
    tried.wait(10)
    for t in ts:
        t.join()
    assert len(granted) == 10


def test_release_is_idempotent(tmp_path: Path) -> None:
    run = tmp_path / "runs" / "r"
    run.mkdir(parents=True)
    r = Guard(run, 5.0, 1.0, "t").reserve("x")
    r.release()
    r.release()
    assert live_reservations(run) == []


def test_run_folder_of(tmp_path: Path) -> None:
    assert run_folder_of(tmp_path / "runs" / "r" / "part1" / "x.json") == tmp_path / "runs" / "r"
    with pytest.raises(ValueError):
        run_folder_of(tmp_path / "x.json")
