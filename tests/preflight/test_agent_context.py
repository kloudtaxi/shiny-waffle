"""The probe and the agent-context check."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from preflight.checks.agent_context import check_agent_context, reader_values
from preflight.config import AgentContextConfig
from preflight.observe.probe import ProbeObservation, claude_cli_version, run_probe
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
