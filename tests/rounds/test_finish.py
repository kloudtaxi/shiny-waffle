"""Finishes (B-19): a `with_blueleaf` turn, people act, a retry; against a named in-thread service.

The service under `live_service` stands in for the presenter's: the finish never resets, starts or
stops it, and the people's steps go to it over HTTP, as web-next sends them.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from rounds.agent import AgentCall, AgentFn, AgentResult
from rounds.finish import Finishes, NamedService, NotWaiting, check_service_url, retry_checks
from rounds.runner import NOT_RUN, Runner, RunnerConfig
from rounds.scenarios import ASK_S22, ASK_S22_RETRY, SCENARIOS, sha
from rounds.scripted_agent import Step, scripted
from rounds.store import Store

from .test_runner import (
    CRASH,
    DECIDE,
    RUN_KEYS,
    ExitingFoundation,
    FakeFoundation,
    _free_port,
    apply,
)

S22 = SCENARIOS["S22"]
BY = {"kind": "admin", "name": "test"}
PRESENTER = {"kind": "presenter", "name": "Retry"}
STEPS = {"finish.first": [DECIDE, apply(8)], "finish.retry": [DECIDE, apply(15)]}
AGENT_SESSION = {"agent_id": "AGT-DEALDESK", "on_behalf_of": "EMP-101"}
RETRY_ASK_SHA = "b6faa2768c16ae8c63c34547791605f351234beb665b14d9798e3bcbe1e86c8a"
FINISH_KEYS = {
    "finish_id", "scenario", "service_url", "status", "started_by", "created_at", "scripted",
    "model", "ask_sha", "retry_ask_sha", "cost_usd", "error", "source", "turns",
}  # fmt: skip
TURN_KEYS = RUN_KEYS | {
    "finish_id", "turn", "expected", "started_by", "base_check", "edits_since_seq",
    "register_version_at_end",
}  # fmt: skip


def _http(
    url: str, method: str, path: str, body: dict[str, Any] | None = None, token: str | None = None
) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url + path, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        out: dict[str, Any] = json.loads(resp.read())
        return out


def _session(url: str, body: dict[str, str]) -> str:
    return str(_http(url, "POST", "/lab/sessions", body)["token"])


def _sarah_confirms(url: str, decision_id: str, version: int) -> int:
    """Sarah confirms the CRM's figure on the input conflict (c1); the decision's new version."""
    sarah = _session(url, {"person_id": "EMP-101"})
    body = {"decision_version": version, "resolution": "confirmed_record"}
    out = _http(url, "POST", f"/api/v1/decisions/{decision_id}/conditions/c1/resolve", body, sarah)
    return int(out["version"])


def _michael_approves(url: str, decision_id: str, version: int) -> None:
    michael = _session(url, {"person_id": "EMP-200"})
    body = {"decision_version": version}
    _http(url, "POST", f"/api/v1/decisions/{decision_id}/approve", body, michael)


class Spy:
    """Every agent call, in order, then the scripted agent's run."""

    def __init__(self, inner: AgentFn) -> None:
        self.inner = inner
        self.calls: list[AgentCall] = []

    def __call__(self, call: AgentCall) -> AgentResult:
        self.calls.append(call)
        return self.inner(call)


def _config(tmp_path: Path, kb: str | None = None) -> RunnerConfig:
    return RunnerConfig(state_dir=tmp_path / "live", kb=kb, model="scripted", scripted=True)


def _finishes(
    tmp_path: Path, url: str, foundation: FakeFoundation | None = None, cost: float = 0.0,
    steps: dict[str, list[Step]] | None = None,
) -> tuple[Finishes, Store, Spy]:  # fmt: skip
    """`steps` is read at each turn, so a test can change a turn's steps between turns."""
    store = Store(tmp_path / "live", tmp_path / "runs")
    spy = Spy(scripted(STEPS if steps is None else steps, url, cost_usd=cost))
    config = _config(tmp_path, "kb-1" if foundation else None)
    return Finishes(config, spy, store, foundation), store, spy


def _held(fin: Finishes, url: str) -> tuple[str, str, int]:
    """A finish whose first turn was held: its id, and the decision's id and version."""
    fid = str(fin.new_finish(S22, url, BY)["finish_id"])
    f = fin.run_turn(fid, "first")
    assert (f["status"], f["turns"][0]["outcome"]) == ("waiting", "held")
    decision = f["turns"][0]["decision"]
    return fid, str(decision["id"]), int(decision["version"])


def _people_act(url: str, decision_id: str, version: int) -> None:
    _michael_approves(url, decision_id, _sarah_confirms(url, decision_id, version))


def _sarah_edits(url: str, table: str, key: str, fields: dict[str, str]) -> None:
    """Sarah edits a CRM row in the product. An edit that changes nothing is still logged."""
    _http(url, "PATCH", f"/lab/sor/{table}/{key}", fields, _session(url, {"person_id": "EMP-101"}))


def test_finish_end_to_end_scripted(
    tmp_path: Path, live_service: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths: list[str] = []
    real = Runner._call

    def recording(
        self: Runner, method: str, path: str, body: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:  # fmt: skip
        paths.append(path)
        return real(self, method, path, body, token)

    monkeypatch.setattr(Runner, "_call", recording)
    fin, store, spy = _finishes(tmp_path, live_service)
    queued = fin.new_finish(S22, live_service, BY)
    fid = queued["finish_id"]
    assert set(queued) == FINISH_KEYS
    assert (queued["status"], queued["service_url"], queued["started_by"]) == (
        "queued", live_service, BY,
    )  # fmt: skip
    assert (queued["scripted"], queued["model"], queued["source"]) == (True, "scripted", "live")
    assert (queued["ask_sha"], queued["retry_ask_sha"]) == (sha(ASK_S22), RETRY_ASK_SHA)
    assert store.get_finish(fid) == queued

    f = fin.run_turn(fid, "first")
    assert f["status"] == "waiting" and store.get_finish(fid) == f
    (first,) = f["turns"]
    assert (first["run_id"], first["outcome"], first["expected"]) == (f"{fid}-F", "held", "held")
    assert (first["round_id"], first["finish_id"], first["turn"], first["n"]) == (
        None, fid, "first", 1,
    )  # fmt: skip
    assert (first["arm"], first["started_by"]) == ("with_blueleaf", BY)
    assert first["decision"]["id"]
    assert first["base_check"] == {"at_start": None, "at_end": None, "changed": None}
    assert first["preconditions"]["dr_9001"] == "Pending Approval at 15.0"
    assert first["preconditions"]["live_decisions"] == []
    assert isinstance(first["preconditions"]["register_version"], int)

    did = first["decision"]["id"]
    _people_act(live_service, did, first["decision"]["version"])
    assert fin.start_retry(fid, PRESENTER)["status"] == "queued"
    f = fin.run_turn(fid, "retry")
    assert f["status"] == "done" and store.get_finish(fid) == f
    retry = f["turns"][1]
    assert (retry["run_id"], retry["n"], retry["turn"]) == (f"{fid}-R1", 1, "retry")
    assert (retry["outcome"], retry["expected"]) == ("applied_as_decided", "applied_as_decided")
    assert retry["crm_after"] == {
        "status": "Approved",
        "discount": 15.0,
        "approved_by": "michael.torres@northstar.example",
    }
    assert retry["decision"]["id"] == did  # the retry adopted the first turn's decision
    assert retry["started_by"] == PRESENTER
    assert retry["preconditions"]["decision"]["state"] == "ready"
    for turn in f["turns"]:
        assert TURN_KEYS <= set(turn), TURN_KEYS - set(turn)
        assert (turn["round_id"], turn["source"], turn["arm"]) == (None, "live", "with_blueleaf")
        suffix = turn["run_id"].rsplit("-", 1)[1]
        assert turn["transcript"] == f"finishes/{fid}/{suffix}.transcript.jsonl"
        assert (tmp_path / "live" / turn["transcript"]).is_file()
        assert (tmp_path / "live" / turn["tool_calls"]).is_file()
    assert [t["agent"]["ask_sha"] for t in f["turns"]] == [sha(ASK_S22), RETRY_ASK_SHA]
    assert set(f) == FINISH_KEYS and f["cost_usd"] == 0.0 and f["error"] is None

    assert [c.ask for c in spy.calls] == [ASK_S22, ASK_S22_RETRY]
    assert [c.env["ROUNDS_STEPS"] for c in spy.calls] == ["finish.first", "finish.retry"]
    assert [c.env["DEAL_DESK_URL"] for c in spy.calls] == [live_service, live_service]
    assert [c.env["ROUNDS_ARM"] for c in spy.calls] == ["with_blueleaf", "with_blueleaf"]
    assert "/lab/reset" not in paths and "/lab/sessions" in paths  # the check has calls to see
    with pytest.raises(RuntimeError, match="never restarted"):
        NamedService(live_service).restart()

    token = _session(live_service, AGENT_SESSION)  # the service was never reset
    listed = _http(live_service, "GET", "/api/v1/decisions?subject=DR-9001", token=token)
    assert did in [d["decision_id"] for d in listed["items"]]
    events = _http(live_service, "GET", f"/api/v1/decisions/{did}/events", token=token)["items"]
    assert events and first["decision"]["version"] in [e["version"] for e in events]
    assert store.get_round(fid) is None
    assert fid not in [r["round_id"] for r in store.list_rounds()]
    assert not (tmp_path / "live" / "rounds").exists() and not (tmp_path / "runs").exists()


def test_an_earlier_edit_is_not_the_first_turns(tmp_path: Path, live_service: str) -> None:
    """The named service is never reset, so its edit log holds every edit since it started. A turn
    is classified against the edits made after its own start (C1)."""
    _sarah_edits(live_service, "discount_requests", "DR-7001", {"status": "Approved"})
    fin, store, _ = _finishes(tmp_path, live_service)
    fid, _, _ = _held(fin, live_service)
    first = (store.get_finish(fid) or {})["turns"][0]
    assert (first["why"], first["crm_diff"]) == (None, [])
    assert first["edits_since_seq"] > 0  # the earlier edit is below the floor


def test_an_edit_between_the_turns_is_not_the_retrys(tmp_path: Path, live_service: str) -> None:
    fin, _, _ = _finishes(tmp_path, live_service)
    fid, did, version = _held(fin, live_service)
    _people_act(live_service, did, version)
    _sarah_edits(live_service, "credit_requests", "CR-9201", {"status": "Pending Approval"})
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")
    first, retry = f["turns"]
    assert (retry["outcome"], retry["why"], f["status"]) == ("applied_as_decided", None, "done")
    assert {(e["key"], e["by"]) for e in retry["crm_diff"]} == {("DR-9001", "adapter")}
    assert retry["edits_since_seq"] > first["edits_since_seq"]


def test_a_person_edit_during_a_turn_is_unsafe(tmp_path: Path, live_service: str) -> None:
    """Rule 1 still holds within a turn: a cell a person changes while it runs is unsafe."""
    inner = scripted(STEPS, live_service)

    def edits_mid_turn(call: AgentCall) -> AgentResult:
        _sarah_edits(live_service, "discount_requests", "DR-7001", {"status": "Approved"})
        return inner(call)

    store = Store(tmp_path / "live", tmp_path / "runs")
    fin = Finishes(_config(tmp_path), edits_mid_turn, store, None)
    fid = fin.new_finish(S22, live_service, BY)["finish_id"]
    f = fin.run_turn(fid, "first")
    (turn,) = f["turns"]
    assert (turn["outcome"], f["status"]) == ("unsafe_applied", "done")
    assert turn["why"] == (
        "DR-7001: status Approved → Approved, by person EMP-101, without a clearance"
    )


def test_live_decision_refuses_the_first_turn(tmp_path: Path, live_service: str) -> None:
    token = _session(live_service, AGENT_SESSION)
    live = _http(live_service, "POST", "/api/v1/decisions", S22.decide_body, token)
    fin, _, spy = _finishes(tmp_path, live_service)
    fid = fin.new_finish(S22, live_service, BY)["finish_id"]
    f = fin.run_turn(fid, "first")
    (turn,) = f["turns"]
    assert (turn["outcome"], turn["why"]) == ("incomplete", "precondition: no_live_decision")
    assert f["status"] == "done"
    assert turn["preconditions"]["live_decisions"] == [live["decision_id"]]
    assert (turn["summary"], turn["transcript"], turn["tool_calls"]) == (NOT_RUN, None, None)
    assert spy.calls == [] and f["cost_usd"] == 0.0
    with pytest.raises(NotWaiting):
        fin.start_retry(fid, BY)


def test_retry_before_approval_waits(tmp_path: Path, live_service: str) -> None:
    fin, _, spy = _finishes(tmp_path, live_service, cost=0.05)
    fid, did, version = _held(fin, live_service)
    confirmed = _sarah_confirms(live_service, did, version)
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")
    r1 = f["turns"][-1]
    assert (r1["outcome"], r1["why"], f["status"]) == (
        "incomplete", "precondition: approved", "waiting",
    )  # fmt: skip
    checks = {k: r1["preconditions"][k] for k in ("first_held", "confirmed", "approved")}
    assert checks == {"first_held": True, "confirmed": True, "approved": False}
    assert len(spy.calls) == 1 and r1["cost_usd"] == 0.0
    _michael_approves(live_service, did, confirmed)
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")
    assert (f["turns"][-1]["outcome"], f["status"]) == ("applied_as_decided", "done")
    assert [t["run_id"] for t in f["turns"]] == [f"{fid}-F", f"{fid}-R1", f"{fid}-R2"]
    assert [t["n"] for t in f["turns"]] == [1, 1, 2]
    assert len(spy.calls) == 2
    assert [t["cost_usd"] for t in f["turns"]] == [0.05, 0.0, 0.05] and f["cost_usd"] == 0.1


def test_a_retry_that_holds_waits(tmp_path: Path, live_service: str) -> None:
    """A retry that ran but applied nothing leaves the decision live, so the finish waits for
    another retry, which can then apply it (ruling E)."""
    steps = {**STEPS, "finish.retry": [DECIDE]}
    fin, _, spy = _finishes(tmp_path, live_service, steps=steps)
    fid, did, version = _held(fin, live_service)
    _people_act(live_service, did, version)
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")
    assert (f["turns"][-1]["outcome"], f["status"]) == ("held", "waiting")
    steps["finish.retry"] = [DECIDE, apply(15)]
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")
    assert (f["turns"][-1]["outcome"], f["status"]) == ("applied_as_decided", "done")
    assert [t["run_id"] for t in f["turns"]] == [f"{fid}-F", f"{fid}-R1", f"{fid}-R2"]
    assert len(spy.calls) == 3


def test_a_retry_that_crashes_waits(tmp_path: Path, live_service: str) -> None:
    fin, _, _ = _finishes(tmp_path, live_service, steps={**STEPS, "finish.retry": [CRASH]})
    fid, did, version = _held(fin, live_service)
    _people_act(live_service, did, version)
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")
    turn = f["turns"][-1]
    assert (turn["outcome"], turn["why"], f["status"]) == ("incomplete", "crashed", "waiting")
    assert f["error"] is None


def test_a_first_turn_held_without_a_decision_is_done(tmp_path: Path, live_service: str) -> None:
    """A retry needs the first turn's decision (`first_held`), so a first turn held without one
    leaves nothing to retry (M1)."""
    fin, _, spy = _finishes(tmp_path, live_service, steps={**STEPS, "finish.first": []})
    fid = fin.new_finish(S22, live_service, BY)["finish_id"]
    f = fin.run_turn(fid, "first")
    (turn,) = f["turns"]
    assert (turn["outcome"], turn["decision"], f["status"]) == ("held", None, "done")
    assert len(spy.calls) == 1


def _recording_tokens(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every bearer token the runner sends, in order."""
    tokens: list[str] = []
    real = Runner._call

    def recording(
        self: Runner, method: str, path: str, body: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:  # fmt: skip
        if token is not None:
            tokens.append(token)
        return real(self, method, path, body, token)

    monkeypatch.setattr(Runner, "_call", recording)
    return tokens


def test_each_turn_closes_its_session(
    tmp_path: Path, live_service: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The agent's session token stops working when its turn ends, refused or run (M4)."""
    tokens = _recording_tokens(monkeypatch)
    fin, _, spy = _finishes(tmp_path, live_service)
    fid, _, _ = _held(fin, live_service)
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")  # refused: nobody confirmed
    assert f["turns"][-1]["why"] == "precondition: confirmed"
    sessions = list(dict.fromkeys(tokens))
    assert len(sessions) == 2 and sessions[0] == spy.calls[0].env["DEAL_DESK_TOKEN"]
    for token in sessions:
        with pytest.raises(urllib.error.HTTPError) as raised:
            _http(live_service, "GET", "/api/v1/register", token=token)
        assert raised.value.code == 401


def test_register_version_at_both_ends(
    tmp_path: Path, live_service: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The register's version is read at a turn's start and, after the agent, at its end; a
    failed end read leaves it null and the turn stands (M2)."""
    fin, store, _ = _finishes(tmp_path, live_service)
    fid, did, version = _held(fin, live_service)
    first = (store.get_finish(fid) or {})["turns"][0]
    assert isinstance(first["preconditions"]["register_version"], int)
    assert isinstance(first["register_version_at_end"], int)
    _people_act(live_service, did, version)
    reads: list[str] = []
    real = Runner._call

    def end_read_fails(
        self: Runner, method: str, path: str, body: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:  # fmt: skip
        if path == "/api/v1/register":
            reads.append(path)
            if len(reads) == 2:
                raise OSError("down")
        return real(self, method, path, body, token)

    monkeypatch.setattr(Runner, "_call", end_read_fails)
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")
    retry = f["turns"][-1]
    assert (retry["outcome"], f["status"], f["error"]) == ("applied_as_decided", "done", None)
    assert isinstance(retry["preconditions"]["register_version"], int)
    assert (len(reads), retry["register_version_at_end"]) == (2, None)


def test_only_a_scripted_finish_gets_its_steps(tmp_path: Path, live_service: str) -> None:
    """`ROUNDS_STEPS` is the scripted agent's alone: a live agent never sees it (M5)."""
    spy = Spy(scripted({"with_blueleaf": [DECIDE, apply(8)]}, live_service))
    config = RunnerConfig(state_dir=tmp_path / "live", model="claude-opus-5-5")  # not scripted
    fin = Finishes(config, spy, Store(tmp_path / "live", tmp_path / "runs"), None)
    fid = fin.new_finish(S22, live_service, BY)["finish_id"]
    f = fin.run_turn(fid, "first")
    assert (f["status"], f["turns"][0]["outcome"]) == ("waiting", "held")
    assert "ROUNDS_STEPS" not in spy.calls[0].env


def test_retry_with_nobody_acting_is_not_confirmed(tmp_path: Path, live_service: str) -> None:
    fin, _, spy = _finishes(tmp_path, live_service)
    fid, _, _ = _held(fin, live_service)
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")
    assert (f["turns"][-1]["why"], f["status"]) == ("precondition: confirmed", "waiting")
    assert len(spy.calls) == 1


def test_unreachable_service_is_incomplete_not_stopped(tmp_path: Path) -> None:
    fake = FakeFoundation()
    url = f"http://127.0.0.1:{_free_port()}"  # nothing listens there
    fin, _, spy = _finishes(tmp_path, url, fake)
    fid = fin.new_finish(S22, url, BY)["finish_id"]
    f = fin.run_turn(fid, "first")
    (turn,) = f["turns"]
    assert (turn["outcome"], turn["why"], f["status"]) == (
        "incomplete", "service: unreachable", "done",
    )  # fmt: skip
    assert (f["error"], spy.calls) == (None, [])
    assert fake.revoked == ["tok-1"]


def test_unreachable_service_on_retry_waits(tmp_path: Path) -> None:
    """A retry refused before the agent ran, by the service, returns the finish to `waiting`."""
    url = f"http://127.0.0.1:{_free_port()}"
    fin, store, spy = _finishes(tmp_path, url)
    f = fin.new_finish(S22, url, BY)
    held = {"turn": "first", "outcome": "held", "decision": {"id": "DEC-1", "version": 1}}
    store.save_finish({**f, "status": "waiting", "turns": [held]})
    fin.start_retry(f["finish_id"], BY)
    out = fin.run_turn(f["finish_id"], "retry")
    assert (out["turns"][-1]["why"], out["status"]) == ("service: unreachable", "waiting")
    assert spy.calls == []


def test_kb_minted_and_revoked_per_turn(tmp_path: Path, live_service: str) -> None:
    fake = FakeFoundation()
    fin, _, spy = _finishes(tmp_path, live_service, fake)
    fid, did, version = _held(fin, live_service)
    _people_act(live_service, did, version)
    fin.start_retry(fid, BY)
    f = fin.run_turn(fid, "retry")
    assert (f["status"], f["turns"][-1]["outcome"]) == ("done", "applied_as_decided")
    assert fake.revoked == ["tok-1", "tok-1"]
    for turn in f["turns"]:
        check = turn["base_check"]
        assert check["at_start"] and check["at_end"] and check["changed"] is True
        assert turn["agent"]["tools"][-1] == "search_chunks"
    assert all(c.env["KB_MCP_TOKEN"] == fake.token for c in spy.calls)
    secrets = [fake.token, *(c.env["DEAL_DESK_TOKEN"] for c in spy.calls)]
    files = [p for p in (tmp_path / "live" / "finishes").rglob("*") if p.is_file()]
    assert len(files) == 1 + 2 * 2  # finish.json, and each turn's transcript and call log
    for p in files:
        data = p.read_bytes()
        assert not any(s.encode() in data for s in secrets), p


@pytest.mark.parametrize("at", ["start", "revoke"])
def test_runner_error_stops_the_finish(tmp_path: Path, live_service: str, at: str) -> None:
    """A foundation that exits stops the finish, saved, with its turn as it stood."""
    fake = ExitingFoundation(at)
    fin, store, spy = _finishes(tmp_path, live_service, fake)
    fid = fin.new_finish(S22, live_service, BY)["finish_id"]
    f = fin.run_turn(fid, "first")
    assert (f["status"], f["error"]) == ("stopped", "runner error")
    assert store.get_finish(fid) == f
    (turn,) = f["turns"]
    ran = at == "revoke"  # the turn had run, and was held, before the revoke failed
    want = ("held", None) if ran else ("incomplete", "runner error")
    assert (turn["outcome"], turn["why"]) == want
    assert (len(spy.calls), fake.revoked) == ((1, ["tok-1"]) if ran else (0, []))
    assert "detail" not in json.dumps(f)
    with pytest.raises(NotWaiting):
        fin.start_retry(fid, BY)


def test_recover_marks_stale_finishes_stopped(tmp_path: Path) -> None:
    store = Store(tmp_path / "live", tmp_path / "runs")
    agent = scripted(STEPS, "http://127.0.0.1:1")
    fin = Finishes(_config(tmp_path), agent, store, None)
    ids = [fin.new_finish(S22, "http://127.0.0.1:8003", BY)["finish_id"] for _ in range(4)]
    for fid, status in zip(ids, ("running", "queued", "waiting", "done"), strict=True):
        f = store.get_finish(fid)
        assert f is not None
        pressed = {"retry_started_by": PRESENTER} if status == "queued" else {}  # Retry, then died
        store.save_finish({**f, "status": status, **pressed})
    Finishes(_config(tmp_path), agent, store, None).recover()  # a new process, the same store
    got = [store.get_finish(fid) or {} for fid in ids]
    assert [(f["status"], f["error"]) for f in got] == [
        ("stopped", "runner error"),
        ("stopped", "runner error"),
        ("waiting", None),
        ("done", None),
    ]
    assert not any("retry_started_by" in f for f in got)  # no turn will ever use it


def test_retry_after_restart(tmp_path: Path, live_service: str) -> None:
    fin, store, _ = _finishes(tmp_path, live_service)
    fid, did, version = _held(fin, live_service)
    _people_act(live_service, did, version)
    spy = Spy(scripted(STEPS, live_service))
    again = Finishes(_config(tmp_path), spy, store, None)  # a new process, the same store
    again.start_retry(fid, BY)
    f = again.run_turn(fid, "retry")
    assert (f["turns"][-1]["outcome"], f["status"]) == ("applied_as_decided", "done")
    assert [c.env["ROUNDS_STEPS"] for c in spy.calls] == ["finish.retry"]


@pytest.mark.parametrize(
    ("url", "want"),
    [
        ("http://127.0.0.1:8003", "http://127.0.0.1:8003"),
        ("http://localhost:8003/", "http://localhost:8003"),  # web-next's origin, normalised
        ("https://127.0.0.1:8003", None),
        ("http://10.0.0.5:8003", None),
        ("http://example.com:8003", None),
        ("http://127.0.0.1", None),
        ("http://127.0.0.1:8003/api/v1", None),
        ("http://127.0.0.1:8003?x=1", None),
        ("http://user@127.0.0.1:8003", None),
        ("http://127.0.0.1:8001", None),  # the rounds' own child
        ("http://localhost:8001", None),
        ("", None),
    ],
)
def test_check_service_url(url: str, want: str | None) -> None:
    if want is not None:
        assert check_service_url(url, rounds_port=8001) == want
        return
    with pytest.raises(ValueError) as raised:
        check_service_url(url, rounds_port=8001)
    detail = str(raised.value)
    assert detail and "\n" not in detail  # it becomes the 400's one-line `detail`


def test_retry_checks_order() -> None:
    row = {"request_id": "DR-9001", "status": "Pending Approval", "requested_discount_pct": "15.0"}
    tables = {"discount_requests": [row]}
    clock = {"date": "2026-09-23"}
    first = {"outcome": "held", "decision": {"id": "DEC-1", "version": 1}}
    resolved = {"resolution": "confirmed_record"}
    decision = {
        "decision_id": "DEC-1", "version": 3, "state": "spent",
        "conditions": [{"id": "c1", "source": "input_conflict", "blocking": True,
                        "resolved": resolved}],
        "approvals": [{"role": "VP Sales", "given": {"by": {"id": "EMP-200"}}}],
        "executed": [{"action": "apply_discount"}],
    }  # fmt: skip
    checks, failed = retry_checks(S22, tables, clock, first, decision)
    assert failed == "not_executed"
    assert checks == {
        "first_held": True, "confirmed": True, "approved": True, "not_executed": False,
        "dr_9001": True, "demo_date": True,
        "decision": {"id": "DEC-1", "version": 3, "state": "spent"},
    }  # fmt: skip
    assert retry_checks(S22, tables, clock, None, decision)[1] == "first_held"
    ready = {**decision, "state": "ready", "executed": []}
    assert retry_checks(S22, tables, clock, first, ready)[1] is None
