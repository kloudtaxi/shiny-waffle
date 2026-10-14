"""The /lab/rounds API and the `python -m rounds` seam, against a fake runner (no services)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from rounds.api import create_app
from rounds.scenarios import Scenario
from rounds.store import Store

BODY = {"scenario": "S22", "runs_per_arm": 1, "started_by": {"kind": "admin", "name": "mehul"}}


class FakeRunner:
    def __init__(self, store: Store, crash: bool = False) -> None:
        self.store = store
        self.crash = crash
        self.release = threading.Event()
        self.started = threading.Event()
        self.n = 0

    def new_round(
        self, scenario: Scenario, runs_per_arm: int, started_by: dict[str, Any]
    ) -> dict[str, Any]:
        self.n += 1
        r: dict[str, Any] = {
            "round_id": f"2026-10-13-{self.n}",
            "scenario": scenario.id,
            "runs_per_arm": runs_per_arm,
            "started_by": started_by,
            "status": "queued",
            "runs": [],
        }
        self.store.save_round(r)
        return r

    def run_round(self, round_id: str) -> dict[str, Any]:
        self.started.set()
        if self.crash:
            raise RuntimeError("boom")
        self.release.wait(5)
        return {}


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "live", tmp_path / "runs")


def test_post_returns_202_then_409_while_running(store: Store) -> None:
    runner = FakeRunner(store)
    client = TestClient(create_app(runner, store))
    first = client.post("/lab/rounds", json=BODY)
    assert first.status_code == 202
    assert first.json() == {"round_id": "2026-10-13-1"}
    assert runner.started.wait(5)
    busy = client.post("/lab/rounds", json=BODY)
    assert (busy.status_code, busy.json()) == (409, {"error": "busy"})
    runner.release.set()


def test_post_validates_scenario_and_runs_per_arm(store: Store) -> None:
    client = TestClient(create_app(FakeRunner(store), store))
    bad = [
        {**BODY, "scenario": "S99"},
        {**BODY, "runs_per_arm": 0},
        {**BODY, "runs_per_arm": 6},
        {**BODY, "extra": 1},
        {**BODY, "started_by": {"kind": "root", "name": "x"}},
        {"scenario": "S22"},
    ]
    for body in bad:
        resp = client.post("/lab/rounds", json=body)
        assert resp.status_code == 400, body
        assert resp.json()["error"] == "bad_request"
        assert resp.json()["detail"]
    assert client.post("/lab/rounds", content=b"not json").status_code == 400


def test_get_lists_and_gets(store: Store) -> None:
    runner = FakeRunner(store)
    client = TestClient(create_app(runner, store))
    runner.release.set()
    rid = client.post("/lab/rounds", json=BODY).json()["round_id"]
    listed = client.get("/lab/rounds")
    assert listed.status_code == 200
    assert [r["round_id"] for r in listed.json()["rounds"]] == [rid]
    got = client.get(f"/lab/rounds/{rid}")
    assert got.status_code == 200
    assert got.json()["round_id"] == rid


def test_get_unknown_is_404(store: Store) -> None:
    client = TestClient(create_app(FakeRunner(store), store))
    resp = client.get("/lab/rounds/nope")
    assert (resp.status_code, resp.json()) == (404, {"error": "not_found"})


def test_crashed_round_frees_runner(store: Store) -> None:
    runner = FakeRunner(store, crash=True)
    client = TestClient(create_app(runner, store))
    assert client.post("/lab/rounds", json=BODY).status_code == 202
    assert runner.started.wait(5)
    for _ in range(100):
        resp = client.post("/lab/rounds", json=BODY)
        if resp.status_code != 409:
            break
        threading.Event().wait(0.05)
    assert resp.status_code == 202


def test_no_other_routes(store: Store) -> None:
    client = TestClient(create_app(FakeRunner(store), store))
    assert client.delete("/lab/rounds/x").status_code == 405
    assert client.get("/").status_code == 404


def test_build_app_requires_kb_unless_scripted(tmp_path: Path) -> None:
    from rounds.__main__ import build_app_from_env

    with pytest.raises(SystemExit) as exc:
        build_app_from_env({"ROUNDS_STATE_DIR": str(tmp_path)})
    assert "ROUNDS_KB" in str(exc.value)


def test_scripted_mode_builds_without_minting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from rounds import foundation
    from rounds.__main__ import build_app_from_env

    def boom(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("minted")

    monkeypatch.setattr(foundation, "mint", boom)
    app = build_app_from_env({"ROUNDS_SCRIPTED": "1", "ROUNDS_STATE_DIR": str(tmp_path)})
    client = TestClient(app)
    assert client.get("/lab/rounds").json() == {"rounds": []}
