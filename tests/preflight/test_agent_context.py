"""The probe and the agent-context check."""

from __future__ import annotations

import functools
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from preflight.checks.agent_context import check_agent_context, reader_values
from preflight.config import AgentContextConfig
from preflight.observe.probe import (
    ProbeObservation,
    claude_cli_version,
    run_probe,
    run_subprocess,
)
from tests.preflight.fakes import MARKERS as M
from tests.preflight.fakes import stream

FAKE = Path(__file__).parent / "fixtures" / "fake_probe.py"

INIT: dict[str, Any] = {
    "cwd": "/tmp/northstar-exam-blind-x",
    "tools": ["mcp__foundation__find_entities"],
    "mcp_servers": [{"name": "foundation", "status": "connected"}],
    "model": "claude-opus-5-5",
    "claude_code_version": "2.1.299",
    "apiKeySource": "none",
    "skills": ["a"],
    "plugins": [{"name": "p", "path": "/Users/ada/p"}],
    "agents": [],
    "slash_commands": [],
}
META: dict[str, Any] = {
    "runner": "exam-reader",
    "model": "claude-opus-5-5",
    "flags": "f",
    "expected_tools": ["mcp__foundation__find_entities"],
    "expected_servers": ["foundation"],
    "system_prompt_sha256": "s",
    "problems": [],
}


def obs(
    init: dict[str, Any] | None = INIT,
    answer: str = "I don't know.",
    meta: dict[str, Any] = META,
    extra: list[dict[str, Any]] | None = None,
) -> ProbeObservation:
    return ProbeObservation(
        raw_stream=stream(init=init, answer=answer, cost=0.1, extra=extra),
        meta=meta,
        cost_usd=0.1,
        saved=None,
        error=None,
    )


def test_a_clean_probe_passes(repo: Path) -> None:
    r = check_agent_context(obs(), repo, M)
    assert r.status == "pass"
    assert r.summary == "cwd outside repo · tools as expected · MCP connected · no operator named"


@pytest.mark.parametrize(
    "change, words",
    [
        ({"cwd": str(Path(__file__).parent)}, "cwd"),
        ({"tools": []}, "tools"),
        ({"mcp_servers": [{"name": "foundation", "status": "failed"}]}, "foundation"),
    ],
)
def test_init_problems_fail(repo: Path, change: dict[str, Any], words: str) -> None:
    r = check_agent_context(obs(init={**INIT, **change}), repo, M)
    assert r.status == "fail" and any(words in p for p in r.problems)


def test_auto_memory_with_content_fails(repo: Path, tmp_path: Path) -> None:
    (tmp_path / "MEMORY.md").write_text("x")
    r = check_agent_context(obs(init={**INIT, "memory_paths": {"auto": str(tmp_path)}}), repo, M)
    assert r.status == "fail" and any("auto memory" in p for p in r.problems)


def test_an_empty_or_missing_auto_memory_dir_passes(repo: Path, tmp_path: Path) -> None:
    for auto in (str(tmp_path), str(tmp_path / "absent")):
        o = obs(init={**INIT, "memory_paths": {"auto": auto}})
        assert check_agent_context(o, repo, M).status == "pass"


def test_an_answer_naming_the_repo_fails_and_stores_only_the_kind(repo: Path) -> None:
    r = check_agent_context(obs(answer="I see shiny-waffle's CLAUDE.md"), repo, M)
    assert r.status == "fail" and any("names the repo" in p for p in r.problems)
    assert "shiny-waffle" not in r.model_dump_json()


def test_home_in_init_is_not_an_answer_problem(repo: Path) -> None:
    assert check_agent_context(obs(), repo, M).status == "pass"  # plugin path holds /Users/ada


def test_the_real_date_is_recorded_not_failed(repo: Path) -> None:
    o = obs(answer="Today is 2026-10-20.")
    assert check_agent_context(o, repo, M).status == "pass"
    knows = next(x for x in reader_values(o, "2.1.299", M) if x.field == "reader.knows_real_date")
    assert knows.value is True and knows.compare == "equal"


def test_denials_runner_problems_and_truncated_streams_fail(repo: Path) -> None:
    denied = obs(extra=[{"subtype": "permission_denied"}])
    assert check_agent_context(denied, repo, M).status == "fail"
    r = check_agent_context(obs(meta={**META, "problems": ["x"]}), repo, M)
    assert r.status == "fail" and "runner: x" in r.problems
    r = check_agent_context(obs(init=None), repo, M)
    assert r.status == "fail" and "probe stream has no init event" in r.problems


def test_a_probe_error_fails(repo: Path) -> None:
    o = ProbeObservation("", {}, None, None, "the probe wrote no stream (exit 2)")
    r = check_agent_context(o, repo, M)
    assert r.status == "fail" and r.problems == ["the probe wrote no stream (exit 2)"]


def test_null_expected_tools_defers_to_the_runner(repo: Path) -> None:
    o = obs(init={**INIT, "tools": ["mcp__sor__q"]}, meta={**META, "expected_tools": None})
    assert check_agent_context(o, repo, M).status == "pass"


def test_reader_values_hash_names_not_paths() -> None:
    vals = {x.field: x for x in reader_values(obs(), "2.1.299", M)}
    assert vals["reader.claude_cli_version"].value == "2.1.299"
    assert vals["reader.claude_cli_version"].label == "claude --version"
    assert vals["reader.claude_code_version"].value == "2.1.299"
    assert vals["reader.tools"].value == ["mcp__foundation__find_entities"]
    assert all(
        v.compare == "equal" and v.group == "reader" and v.state == "read" for v in vals.values()
    )
    assert "/Users/ada" not in json.dumps([x.model_dump(mode="json") for x in vals.values()])
    assert str(vals["reader.plugins"].value).startswith("1 · ")
    assert str(vals["reader.agents"].value).startswith("0 · ")


def test_run_probe_saves_a_redacted_stream(tmp_path: Path, run_dir: Path, repo: Path) -> None:
    cfg = AgentContextConfig(
        probe=[sys.executable, str(FAKE), "--say", "ada.ops@example.test"], est_usd=0.25, cap_usd=5
    )
    o = run_probe(cfg, run_dir, repo, M, datetime(2026, 10, 21, 9, 14, 2, tzinfo=UTC))
    assert o.error is None and o.saved == run_dir / "preflight" / "2026-10-21T09-14-02Z.probe.jsonl"
    assert o.saved is not None
    assert "ada.ops" not in o.saved.read_text() and "<marker:operator>" in o.saved.read_text()
    assert "ada.ops" in o.raw_stream
    assert o.meta["runner"] == "exam-reader" and o.cost_usd == 0.0


def test_run_probe_never_overwrites_a_saved_stream(run_dir: Path, repo: Path) -> None:
    cfg = AgentContextConfig(probe=[sys.executable, str(FAKE)], est_usd=0.25, cap_usd=5)
    at = datetime(2026, 10, 21, 9, 14, 2, tzinfo=UTC)
    first = run_probe(cfg, run_dir, repo, M, at)
    second = run_probe(cfg, run_dir, repo, M, at)
    assert first.saved != second.saved and second.saved is not None
    assert second.saved.name == "2026-10-21T09-14-03Z.probe.jsonl"


def test_run_probe_without_a_stream_is_an_error(run_dir: Path, repo: Path) -> None:
    cfg = AgentContextConfig(probe=["ignored"], est_usd=0.25, cap_usd=5)
    at = datetime(2026, 10, 21, 9, 14, 2, tzinfo=UTC)
    o = run_probe(cfg, run_dir, repo, M, at, runner=lambda cmd, env, cwd: 3)
    assert o.error == "the probe wrote no stream (exit 3)" and o.saved is None


def test_claude_cli_version_parses_the_first_token() -> None:
    assert claude_cli_version(lambda: "2.1.299 (Claude Code)\n") == "2.1.299"


def _cfg(*cmd: str) -> AgentContextConfig:
    return AgentContextConfig(probe=list(cmd), est_usd=0.25, cap_usd=5)


AT = datetime(2026, 10, 21, 9, 14, 2, tzinfo=UTC)
GOOD_JSONL = stream(init=INIT, answer="ok", cost=0.0)


@pytest.mark.parametrize("meta_text", [None, "{not json", "[]"])
def test_an_unusable_probe_json_is_an_error(
    run_dir: Path, repo: Path, meta_text: str | None
) -> None:
    def runner(cmd: list[str], env: dict[str, str], cwd: Path) -> int:
        out = Path(env["PREFLIGHT_PROBE_OUT"])
        (out / "probe.jsonl").write_text(GOOD_JSONL)
        if meta_text is not None:
            (out / "probe.json").write_text(meta_text)
        return 0

    o = run_probe(_cfg("x"), run_dir, repo, M, AT, runner=runner)
    assert o.error == "the runner wrote no usable probe.json"
    r = check_agent_context(o, repo, M)
    assert r.status == "fail" and r.problems == ["the runner wrote no usable probe.json"]


def test_a_missing_cwd_result_or_an_error_result_fails(repo: Path) -> None:
    no_cwd = {k: v for k, v in INIT.items() if k != "cwd"}
    assert "probe init event has no cwd" in check_agent_context(obs(init=no_cwd), repo, M).problems
    assert (
        "probe init event has no cwd"
        in check_agent_context(obs(init={**INIT, "cwd": ""}), repo, M).problems
    )
    no_result = ProbeObservation(
        stream(init=INIT).rsplit("\n", 2)[0] + "\n", META, None, None, None
    )
    assert "probe stream has no result event" in check_agent_context(no_result, repo, M).problems
    errored = ProbeObservation(
        stream(init=INIT).replace('"is_error": false', '"is_error": true'), META, None, None, None
    )
    assert "the probe ended on an error" in check_agent_context(errored, repo, M).problems


def test_a_nonempty_permission_denials_list_fails(repo: Path) -> None:
    raw = stream(init=INIT).replace(
        '"is_error": false', '"is_error": false, "permission_denials": [{}]'
    )
    o = ProbeObservation(raw, META, None, None, None)
    assert "a permission was denied" in check_agent_context(o, repo, M).problems


def test_a_missing_command_is_an_error(run_dir: Path, repo: Path) -> None:
    o = run_probe(_cfg("/nonexistent/zzz-probe", "secret-arg"), run_dir, repo, M, AT)
    assert o.error == "probe command not found: /nonexistent/zzz-probe"
    assert o.saved is None


def test_a_timeout_is_an_error_even_with_a_partial_stream(run_dir: Path, repo: Path) -> None:
    runner = functools.partial(run_subprocess, timeout=1)
    o = run_probe(_cfg(sys.executable, str(FAKE), "--sleep", "30"), run_dir, repo, M, AT, runner)
    assert o.error == "probe timed out after 1 s"


def test_a_timeout_after_a_partial_stream_stays_an_error(run_dir: Path, repo: Path) -> None:
    import subprocess

    def runner(cmd: list[str], env: dict[str, str], cwd: Path) -> int:
        out = Path(env["PREFLIGHT_PROBE_OUT"])
        (out / "probe.jsonl").write_text(GOOD_JSONL)
        (out / "probe.json").write_text(json.dumps(META))
        raise subprocess.TimeoutExpired(cmd, 900)

    o = run_probe(_cfg("x"), run_dir, repo, M, AT, runner=runner)
    assert o.error == "probe timed out after 900 s" and o.saved is not None


def test_meta_strings_are_redacted_in_values() -> None:
    meta = {**META, "flags": "--add-dir /Users/ada/x", "expected_tools": ["t-/Users/ada"]}
    vals = {x.field: x for x in reader_values(obs(meta=meta), "2.1.299", M)}
    assert vals["reader.flags"].value == "--add-dir <marker:home>/x"
    assert "/Users/ada" not in json.dumps([x.model_dump(mode="json") for x in vals.values()])


def test_a_non_dict_server_item_does_not_crash(repo: Path) -> None:
    o = obs(init={**INIT, "mcp_servers": ["foundation"]})
    assert "MCP server foundation not connected" in check_agent_context(o, repo, M).problems


def test_an_unreadable_auto_memory_dir_is_a_problem(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(self: Path) -> Any:
        raise PermissionError

    monkeypatch.setattr(Path, "iterdir", boom)
    o = obs(init={**INIT, "memory_paths": {"auto": str(tmp_path)}})
    assert "auto memory directory can't be read" in check_agent_context(o, repo, M).problems


def test_an_unreadable_cli_version_is_unread() -> None:
    def fail() -> str:
        raise FileNotFoundError

    assert claude_cli_version(fail) is None
    v = next(x for x in reader_values(obs(), None, M) if x.field == "reader.claude_cli_version")
    assert v.state == "unread" and v.value is None


def test_the_probe_temp_dir_is_outside_the_repo_and_removed(run_dir: Path, repo: Path) -> None:
    seen: list[Path] = []

    def runner(cmd: list[str], env: dict[str, str], cwd: Path) -> int:
        seen.append(Path(env["PREFLIGHT_PROBE_OUT"]))
        assert "PREFLIGHT_PROBE_OUT" not in os.environ
        return 0

    run_probe(_cfg("x"), run_dir, repo, M, AT, runner=runner)
    assert not seen[0].resolve().is_relative_to(repo.resolve()) and not seen[0].exists()
