"""BlueLeaf lab MCP server, task B-03: the state root and atomic writes (plan §1, "State root")."""

from __future__ import annotations

from pathlib import Path

import pytest
from service import paths


def test_home_follows_blueleaf_home_and_is_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BLUELEAF_HOME", str(tmp_path / "state"))
    assert paths.home() == tmp_path / "state"
    assert (tmp_path / "state").is_dir()


def test_runs_root_follows_blueleaf_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLUELEAF_RUNS", str(tmp_path / "runs"))
    assert paths.runs_root() == tmp_path / "runs"
    monkeypatch.delenv("BLUELEAF_RUNS")
    assert paths.runs_root() == paths.LAB / "runs"


def test_atomic_write_replaces_whole_and_leaves_no_temp(tmp_path: Path) -> None:
    target = tmp_path / "a/b/state.json"
    paths.atomic_write(target, "first")
    paths.atomic_write(target, "second")
    assert target.read_text() == "second"
    assert sorted(p.name for p in target.parent.iterdir()) == ["state.json"]
