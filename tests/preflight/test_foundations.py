"""Foundation snapshots: Utopia by read-only SQL, B-20 by its K1 API, local by nothing."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from preflight.config import DEFAULT_ERROR_PATTERN, FoundationConfig, LogSource
from preflight.foundations import make_foundation
from preflight.foundations.b20 import B20Foundation
from preflight.foundations.local import LocalFoundation
from preflight.foundations.utopia import SQL, UtopiaFoundation

UUID1 = "11111111-1111-1111-1111-111111111111"
NOW = datetime(2026, 10, 21, 9, 0, tzinfo=UTC)
BIN = Path("bin/server")


def test_utopia_sql_names_its_columns_and_reads_only(monkeypatch: pytest.MonkeyPatch) -> None:
    for text in SQL.values():
        assert not re.search(r"select\s+\*", text, re.I) and "api_key" not in text
    seen: list[list[str]] = []

    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        seen.append(cmd)
        assert kw.get("timeout") == 60
        if cmd[:2] == ["docker", "logs"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        sql = cmd[-1]
        if "select id from knowledge_bases" in sql:
            out = UUID1
        elif "chat_model" in sql or "group by" in sql:
            out = ""
        else:
            out = "0"
        return subprocess.CompletedProcess(cmd, 0, out + "\n" if out else "", "")

    monkeypatch.setattr("preflight.foundations.utopia.subprocess.run", fake_run)
    f = UtopiaFoundation(
        {"base": UUID1}, "utopia-db-1", BIN, LogSource(docker="srv"), DEFAULT_ERROR_PATTERN
    )
    f.snapshot(datetime(2026, 10, 21, tzinfo=UTC))
    psql = [c for c in seen if "psql" in c]
    assert psql and all("PGOPTIONS=-c default_transaction_read_only=on" in c for c in psql)
    assert any(c[:2] == ["docker", "logs"] for c in seen)


def test_utopia_refuses_a_kb_id_that_is_not_a_uuid() -> None:
    with pytest.raises(ValueError):
        UtopiaFoundation(
            {"base": "x'; drop"},
            "db",
            Path("b"),
            LogSource(docker="s"),
            DEFAULT_ERROR_PATTERN,
            psql=lambda s: [],
            logs=lambda t: "",
        )


def test_utopia_snapshot_maps_rows(tmp_path: Path) -> None:
    binary = tmp_path / "srv"
    binary.write_bytes(b"x")
    sqls: list[str] = []

    def psql(sql: str) -> list[list[str]]:
        sqls.append(sql)
        assert "{since}" not in sql and "{kbs}" not in sql
        if "status = 'failed'" in sql:
            assert "updated_at > '2026-10-21T09:00:00Z'" in sql
            return [["1"]]
        if "select id from knowledge_bases" in sql:
            return [[UUID1]]
        if "chat_model" in sql:
            return [["w1", "gpt", "low", "emb"]]
        if "from documents" in sql and "group by" in sql:
            return [[UUID1, "ready", "done", "5"]]
        if "from documents" in sql:
            return [["3"]]
        if "from facts" in sql:
            return [[UUID1, "base", "12"]]
        if "from entities" in sql:
            return [[UUID1, "7"]]
        if "status in ('queued', 'running')" in sql:
            return [["2"]]
        return [["1"]]

    f = UtopiaFoundation(
        {"base": UUID1},
        "db",
        binary,
        LogSource(docker="s"),
        DEFAULT_ERROR_PATTERN,
        psql=psql,
        logs=lambda t: "ok\n" + "x" * 300 + " 429 too many\nfine\n",
    )
    s = f.snapshot(NOW)
    assert s.counts == {
        "base.documents.ready/done": 5,
        "base.facts.base": 12,
        "base.entities": 7,
    }
    assert s.settings == {
        "w1.chat_model": "gpt",
        "w1.chat_reasoning_effort": "low",
        "w1.embed_model": "emb",
    }
    assert (s.jobs_active, s.jobs_failed_since, s.documents_unfinished) == (2, 1, 3)
    assert s.log_errors is not None and len(s.log_errors) == 1 and len(s.log_errors[0]) <= 200
    assert s.binary_sha256 is not None and len(s.binary_sha256) == 64
    assert s.at.tzinfo is not None


def test_utopia_file_log_keeps_recent_and_untimestamped(tmp_path: Path) -> None:
    log = tmp_path / "s.log"
    log.write_text(
        "2026-10-21T08:00:00Z 429 old\n2026-10-21T10:00:00Z 429 new\nno stamp 429 rate limit\n"
    )
    f = UtopiaFoundation(
        {"base": UUID1},
        "db",
        BIN,
        LogSource(file=str(log)),
        DEFAULT_ERROR_PATTERN,
        psql=_quiet_psql,
    )
    s = f.snapshot(NOW)
    assert s.log_errors == ["2026-10-21T10:00:00Z 429 new", "no stamp 429 rate limit"]


def _quiet_psql(sql: str) -> list[list[str]]:
    """A database with the base present and nothing else going on."""
    if "select id from knowledge_bases" in sql:
        return [[UUID1]]
    if "group by" in sql or "chat_model" in sql:
        return []
    return [["0"]]


class _Contract:
    def pages(self, path: str, params: dict[str, Any] | None = None) -> list[Any]:
        if path == "/kbs/K/documents":
            return [{"doc_id": "a"}, {"doc_id": "b"}]
        assert path == "/kbs/K/facts" and params is not None
        return [{}] * {"a": 3, "b": 4}[params["doc_id"]]


def test_b20_counts_page_documents_and_facts() -> None:
    s = B20Foundation(_Contract(), {"base": "K"}).snapshot(NOW)
    assert s.counts == {"base.documents": 2, "base.facts": 7}
    assert s.jobs_active is None and s.log_errors is None and s.settings == {}


def test_local_foundation_reads_nothing() -> None:
    s = LocalFoundation().snapshot(NOW)
    assert s.counts == {} and s.jobs_active is None


def test_make_foundation_b20_reads_arms_json(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (tmp_path / "tok").write_text("not-a-real-token\n")
    arms = {"arms": {"x": {"url": "http://127.0.0.1:1", "token_file": "tok", "kbs": {"base": "K"}}}}
    (run / "arms.json").write_text(json.dumps(arms))
    f = make_foundation(FoundationConfig(kind="b20", arm="x"), run, tmp_path)
    assert isinstance(f, B20Foundation) and f.kbs == {"base": "K"}


def test_make_foundation_local_and_utopia(tmp_path: Path) -> None:
    assert isinstance(
        make_foundation(FoundationConfig(kind="local"), tmp_path, tmp_path), LocalFoundation
    )
    cfg = FoundationConfig(
        kind="utopia",
        kbs={"base": UUID1},
        db_container="db",
        binary="bin/srv",
        log=LogSource(docker="s"),
    )
    f = make_foundation(cfg, tmp_path, tmp_path)
    assert isinstance(f, UtopiaFoundation) and f.binary == tmp_path / "bin/srv"


def _fake_docker(monkeypatch: pytest.MonkeyPatch, logs_rc: int, psql_out: str = "0\n") -> None:
    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        if cmd[:2] == ["docker", "logs"]:
            return subprocess.CompletedProcess(cmd, logs_rc, "", "Error: No such container: srv\n")
        sql = cmd[-1]
        if "select id from knowledge_bases" in sql:
            return subprocess.CompletedProcess(cmd, 0, UUID1 + "\n", "")
        if "chat_model" in sql or "group by" in sql:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 0, psql_out, "")

    monkeypatch.setattr("preflight.foundations.utopia.subprocess.run", fake_run)


def _utopia(binary: Path = BIN) -> UtopiaFoundation:
    return UtopiaFoundation(
        {"base": UUID1}, "db", binary, LogSource(docker="srv"), DEFAULT_ERROR_PATTERN
    )


def test_unreadable_docker_log_is_unread_not_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_docker(monkeypatch, logs_rc=1)
    s = _utopia().snapshot(NOW)
    assert s.log_errors is None and s.jobs_active == 0


def test_unreadable_log_file_is_unread(tmp_path: Path) -> None:
    f = UtopiaFoundation(
        {"base": UUID1}, "db", BIN, LogSource(file=str(tmp_path / "missing.log")),
        DEFAULT_ERROR_PATTERN, psql=_quiet_psql,
    )  # fmt: skip
    assert f.snapshot(NOW).log_errors is None


def test_empty_psql_output_for_a_count_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_docker(monkeypatch, logs_rc=0, psql_out="")
    with pytest.raises(RuntimeError, match="no rows for jobs_active"):
        _utopia().snapshot(NOW)


def test_missing_base_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    f = UtopiaFoundation(
        {"base": UUID1}, "db", BIN, LogSource(docker="s"), DEFAULT_ERROR_PATTERN,
        psql=lambda s: [], logs=lambda t: "",
    )  # fmt: skip
    with pytest.raises(ValueError, match="base base not found"):
        f.snapshot(NOW)


def test_kb_ids_are_normalised() -> None:
    f = UtopiaFoundation(
        {"base": "{" + UUID1.upper() + "}"}, "db", BIN, LogSource(docker="s"),
        DEFAULT_ERROR_PATTERN, psql=lambda s: [], logs=lambda t: "",
    )  # fmt: skip
    assert f.kbs == {"base": UUID1}


def test_missing_binary_has_no_hash(tmp_path: Path) -> None:
    f = UtopiaFoundation(
        {"base": UUID1}, "db", tmp_path / "gone", LogSource(docker="s"), DEFAULT_ERROR_PATTERN,
        psql=_quiet_psql, logs=lambda t: "",
    )  # fmt: skip
    assert f.snapshot(NOW).binary_sha256 is None
