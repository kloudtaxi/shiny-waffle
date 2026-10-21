"""The run config: what loads, and what is refused with the problem named."""

from __future__ import annotations

from pathlib import Path

import pytest

from preflight.config import ConfigError, load_config
from tests.preflight.fakes import write_config

GOOD = """
checks: [inputs, fingerprint, settled, agent_context]
inputs:
  id_patterns: ['\\bCRM-\\d{4}\\b']
  supplied_keys: [request_id]
  evidence: {base: [dataset/evidence]}
foundation: {kind: local}
agent_context: {probe: [python, x.py], est_usd: 0.25, cap_usd: 5}
"""


def test_a_good_config_loads(run_dir: Path, repo: Path) -> None:
    write_config(run_dir, GOOD)
    cfg = load_config(run_dir, repo)
    assert cfg.checks == ["inputs", "fingerprint", "settled", "agent_context"]
    assert cfg.settled.window_seconds == 60 and cfg.baseline == "latest"


@pytest.mark.parametrize(
    "bad, words",
    [
        (GOOD + "extra: 1\n", "extra"),  # unknown key
        (GOOD.replace("dataset/evidence", "dataset/answer-key"), "deny"),  # never-load path
        (GOOD.replace("dataset/evidence", "truth"), "deny-listed"),
        (GOOD.replace("dataset/evidence", "site"), "deny-listed"),
        (GOOD.replace("dataset/evidence", "owm"), "deny-listed"),
        (GOOD.replace("dataset/evidence", "dataset/evaluation"), "deny-listed"),
        (GOOD.replace("dataset/evidence", "dataset"), "contains a deny-listed"),
        (GOOD.replace("[dataset/evidence]", "['.']"), "contains a deny-listed"),
        (GOOD.replace("dataset/evidence", "dataset/evidence/MANIFEST.yaml"), "MANIFEST"),
        (GOOD.replace("dataset/evidence", "../elsewhere"), "outside"),
        (GOOD.replace("\\bCRM-\\d{4}\\b", "(unclosed"), "pattern"),
        ("checks: [inputs]\n", "inputs"),  # listed check, no section
        ("checks: [settled]\n", "foundation"),
        ("checks: [settled]\nfoundation: {kind: utopia}\n", "kbs"),  # utopia needs kbs, ...
        ("checks: [settled]\nfoundation: {kind: b20}\n", "arm"),
    ],
)
def test_bad_configs_are_refused_with_the_problem_named(
    run_dir: Path, repo: Path, bad: str, words: str
) -> None:
    write_config(run_dir, bad)
    with pytest.raises(ConfigError, match=words):
        load_config(run_dir, repo)


def test_a_missing_config_is_a_config_error(run_dir: Path, repo: Path) -> None:
    with pytest.raises(ConfigError, match="preflight.yaml"):
        load_config(run_dir, repo)


def test_columns_default_and_merge_a_partial_override(run_dir: Path, repo: Path) -> None:  # F-2
    write_config(run_dir, GOOD)
    cfg = load_config(run_dir, repo).inputs
    assert cfg is not None and cfg.columns == {
        "id": "id",
        "corpus": "corpus",
        "question": "question",
    }
    write_config(
        run_dir, GOOD.replace("  supplied_keys:", "  columns: {corpus: kb}\n  supplied_keys:")
    )
    cfg = load_config(run_dir, repo).inputs
    assert cfg is not None and cfg.columns == {"id": "id", "corpus": "kb", "question": "question"}


def test_an_unknown_column_key_is_refused(run_dir: Path, repo: Path) -> None:  # F-2
    write_config(run_dir, GOOD.replace("  supplied_keys:", "  columns: {kb: kb}\n  supplied_keys:"))
    with pytest.raises(ConfigError, match="columns"):
        load_config(run_dir, repo)
