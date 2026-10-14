"""The /lab/rounds API and the `python -m rounds` seam, against a fake runner (no services)."""

from __future__ import annotations

import json
import shutil
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
    as_json = {"Content-Type": "application/json"}
    assert client.post("/lab/rounds", content=b"not json", headers=as_json).status_code == 400


def test_post_refuses_anything_but_json(store: Store) -> None:
    """A web page can POST text/plain cross-origin to 127.0.0.1 without a preflight; it must
    not be able to start a paid round."""
    runner = FakeRunner(store)
    client = TestClient(create_app(runner, store))
    body = json.dumps(BODY).encode()
    for ctype in ("text/plain", "application/x-www-form-urlencoded", "multipart/form-data", None):
        headers = {} if ctype is None else {"Content-Type": ctype}
        resp = client.post("/lab/rounds", content=body, headers=headers)
        assert (resp.status_code, resp.json()) == (415, {"error": "unsupported_media_type"}), ctype
    assert runner.n == 0
    runner.release.set()
    ok = {"Content-Type": "Application/JSON; charset=utf-8"}
    assert client.post("/lab/rounds", content=body, headers=ok).status_code == 202


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


@pytest.mark.parametrize("cap", ["0", "-5", "nan", "inf", "-inf", "thirty", ""])
def test_cap_must_be_finite_and_positive(tmp_path: Path, cap: str) -> None:
    from rounds.__main__ import build_app_from_env

    env = {"ROUNDS_SCRIPTED": "1", "ROUNDS_STATE_DIR": str(tmp_path), "ROUNDS_CAP_USD": cap}
    with pytest.raises(SystemExit) as exc:
        build_app_from_env(env)
    assert "ROUNDS_CAP_USD" in str(exc.value) and "\n" not in str(exc.value)


def _token_file(
    tmp_path: Path, text: str = "claude-token-value-789\n", mode: int = 0o600
) -> dict[str, str]:
    path = tmp_path / "rounds-agent.token"
    path.write_text(text)
    path.chmod(mode)
    return {"ROUNDS_CLAUDE_TOKEN_FILE": str(path)}


@pytest.mark.parametrize("problem", ["missing", "empty", "readable by others"])
def test_live_mode_needs_a_private_claude_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, problem: str
) -> None:
    """Live runs sign the agent in with a long-lived token in a fresh config dir, so the agent never
    sees the operator's account email. Without a private token file, the runner won't start."""
    from rounds.__main__ import build_app_from_env

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/local/bin/{name}")
    token = {"missing": {"ROUNDS_CLAUDE_TOKEN_FILE": str(tmp_path / "none")},
             "empty": _token_file(tmp_path, text="\n"),
             "readable by others": _token_file(tmp_path, mode=0o644)}[problem]  # fmt: skip
    live = {"ROUNDS_KB": "kb-1", "ROUNDS_STATE_DIR": str(tmp_path / "s"), **token}
    with pytest.raises(SystemExit) as exc:
        build_app_from_env(live)
    assert "token" in str(exc.value) and "\n" not in str(exc.value)
    build_app_from_env({**live, "ROUNDS_SCRIPTED": "1"})  # scripted needs no token


def test_live_mode_needs_claude_on_the_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from rounds.__main__ import build_app_from_env

    looked: list[str] = []

    def which(name: str) -> str | None:
        looked.append(name)
        return None

    monkeypatch.setattr(shutil, "which", which)
    live = {"ROUNDS_KB": "kb-1", "ROUNDS_STATE_DIR": str(tmp_path), **_token_file(tmp_path)}
    with pytest.raises(SystemExit) as exc:
        build_app_from_env(live)
    assert looked == ["claude"]
    assert "claude" in str(exc.value) and "\n" not in str(exc.value)
    build_app_from_env({**live, "ROUNDS_SCRIPTED": "1"})  # scripted needs no claude
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/local/bin/{name}")
    build_app_from_env(live)


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
    rounds = client.get("/lab/rounds").json()["rounds"]
    assert all(r["source"].startswith("runs/") for r in rounds)  # only the committed copies


def test_scripted_mode_records_the_scripted_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ROUNDS_SCRIPTED=1` must label its runs "scripted", never the live model."""
    import rounds.__main__ as main_mod
    from rounds.runner import Runner

    seen: list[Any] = []

    def spy(config: Any, **kw: Any) -> Any:
        seen.append(config)
        return Runner(config, **kw)

    monkeypatch.setattr(main_mod, "Runner", spy)
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/local/bin/{name}")
    main_mod.build_app_from_env({"ROUNDS_SCRIPTED": "1", "ROUNDS_STATE_DIR": str(tmp_path)})
    live = {"ROUNDS_KB": "kb-1", "ROUNDS_STATE_DIR": str(tmp_path / "l"), **_token_file(tmp_path)}
    main_mod.build_app_from_env(live)
    assert [(c.model, c.scripted) for c in seen] == [("scripted", True), ("claude-opus-5-5", False)]


FINISH = {
    "scenario": "S22",
    "service_url": "http://127.0.0.1:8003",
    "started_by": {"kind": "admin", "name": "mehul"},
}
RETRY = {"started_by": {"kind": "admin", "name": "sarah"}}


class FakeFinishes:
    """Writes to the store like `Finishes` and holds each turn until released."""

    def __init__(self, store: Store) -> None:
        self.store = store
        self.release = threading.Event()
        self.started = threading.Event()
        self.n = 0
        self.urls: list[str] = []
        self.turns: list[tuple[str, str]] = []

    def new_finish(
        self, scenario: Scenario, service_url: str, started_by: dict[str, Any]
    ) -> dict[str, Any]:
        self.n += 1
        self.urls.append(service_url)
        f: dict[str, Any] = {
            "finish_id": f"2026-10-14-F{self.n}",
            "scenario": scenario.id,
            "service_url": service_url,
            "status": "queued",
            "started_by": started_by,
            "turns": [],
        }
        self.store.save_finish(f)
        return f

    def start_retry(self, finish_id: str, started_by: dict[str, Any]) -> dict[str, Any]:
        from rounds.finish import NotWaiting

        f = self.store.get_finish(finish_id)
        if f is None:
            raise KeyError(finish_id)
        if f["status"] != "waiting":
            raise NotWaiting(finish_id)
        f["status"] = "queued"
        self.store.save_finish(f)
        return f

    def run_turn(self, finish_id: str, turn: str) -> dict[str, Any]:
        self.turns.append((finish_id, turn))
        self.started.set()
        self.release.wait(5)
        return {}


def _finish_client(store: Store) -> tuple[TestClient, FakeRunner, FakeFinishes]:
    runner, finishes = FakeRunner(store), FakeFinishes(store)
    return TestClient(create_app(runner, store, finishes, 8001)), runner, finishes


def test_finish_routes_share_the_rounds_lock(store: Store) -> None:
    client, runner, finishes = _finish_client(store)
    first = client.post("/lab/finishes", json=FINISH)
    assert (first.status_code, first.json()) == (202, {"finish_id": "2026-10-14-F1"})
    assert finishes.started.wait(5)
    for resp in (client.post("/lab/rounds", json=BODY), client.post("/lab/finishes", json=FINISH)):
        assert (resp.status_code, resp.json()) == (409, {"error": "busy"})
    finishes.release.set()
    for _ in range(100):  # the thread frees the lock after its turn returns
        resp = client.post("/lab/rounds", json=BODY)
        if resp.status_code != 409:
            break
        threading.Event().wait(0.05)
    assert resp.status_code == 202
    assert runner.started.wait(5)
    busy = client.post("/lab/finishes", json=FINISH)
    assert (busy.status_code, busy.json()) == (409, {"error": "busy"})
    runner.release.set()


def test_finish_post_validation(store: Store) -> None:
    client, _runner, finishes = _finish_client(store)
    finishes.release.set()
    plain = client.post(
        "/lab/finishes", content=json.dumps(FINISH).encode(), headers={"Content-Type": "text/plain"}
    )
    assert (plain.status_code, plain.json()) == (415, {"error": "unsupported_media_type"})
    unknown = client.post("/lab/finishes", json={**FINISH, "scenario": "S99"})
    assert (unknown.status_code, unknown.json()["detail"]) == (400, "unknown scenario")
    bad = [
        {**FINISH, "service_url": "http://10.0.0.5:8003"},
        {**FINISH, "service_url": "http://127.0.0.1:8001"},
        {**FINISH, "extra": 1},
    ]
    for body in bad:
        resp = client.post("/lab/finishes", json=body)
        assert resp.status_code == 400, body
        assert resp.json()["error"] == "bad_request"
        assert resp.json()["detail"]
    assert finishes.n == 0
    ok = client.post("/lab/finishes", json={**FINISH, "service_url": "http://localhost:8003/"})
    assert ok.status_code == 202
    assert finishes.urls == ["http://localhost:8003"]


def test_retry_route(store: Store) -> None:
    client, _runner, finishes = _finish_client(store)
    finishes.release.set()
    missing = client.post("/lab/finishes/nope/retry", json=RETRY)
    assert (missing.status_code, missing.json()) == (404, {"error": "not_found"})
    store.save_finish({"finish_id": "F-done", "status": "done", "turns": []})
    done = client.post("/lab/finishes/F-done/retry", json=RETRY)
    assert (done.status_code, done.json()) == (409, {"error": "not_waiting"})
    store.save_finish({"finish_id": "F-wait", "status": "waiting", "turns": []})
    assert client.post("/lab/finishes/F-wait/retry", json={}).status_code == 400
    plain = client.post(
        "/lab/finishes/F-wait/retry", content=b"{}", headers={"Content-Type": "text/plain"}
    )
    assert plain.status_code == 415
    ok = client.post("/lab/finishes/F-wait/retry", json=RETRY)
    assert (ok.status_code, ok.json()) == (202, {"finish_id": "F-wait"})
    assert finishes.started.wait(5)
    assert finishes.turns == [("F-wait", "retry")]


def test_refused_retries_free_the_lock(store: Store) -> None:
    client, _runner, finishes = _finish_client(store)
    finishes.release.set()
    store.save_finish({"finish_id": "F-done", "status": "done", "turns": []})
    assert client.post("/lab/finishes/F-done/retry", json=RETRY).status_code == 409
    assert client.post("/lab/finishes/nope/retry", json=RETRY).status_code == 404
    assert client.post("/lab/finishes", json=FINISH).status_code == 202


def test_get_finishes(store: Store) -> None:
    client, _runner, finishes = _finish_client(store)
    finishes.release.set()
    fid = client.post("/lab/finishes", json=FINISH).json()["finish_id"]
    listed = client.get("/lab/finishes")
    assert listed.status_code == 200
    assert [f["finish_id"] for f in listed.json()["finishes"]] == [fid]
    got = client.get(f"/lab/finishes/{fid}")
    assert (got.status_code, got.json()["finish_id"]) == (200, fid)
    missing = client.get("/lab/finishes/nope")
    assert (missing.status_code, missing.json()) == (404, {"error": "not_found"})
    assert client.get("/lab/rounds").json() == {"rounds": []}


def test_no_finish_routes_without_finishes(store: Store) -> None:
    client = TestClient(create_app(FakeRunner(store), store))
    assert client.get("/lab/finishes").status_code == 404


def test_scripted_app_has_finish_routes(tmp_path: Path) -> None:
    from rounds.__main__ import build_app_from_env

    app = build_app_from_env({"ROUNDS_SCRIPTED": "1", "ROUNDS_STATE_DIR": str(tmp_path)})
    resp = TestClient(app).get("/lab/finishes")
    assert (resp.status_code, resp.json()) == (200, {"finishes": []})
