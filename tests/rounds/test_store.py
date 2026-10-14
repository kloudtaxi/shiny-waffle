from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rounds.store import Store

FOLDER = "2026-10-14-b15-proof-round"


def _round(round_id: str, created: str = "2026-10-14T10:00:00+00:00", **kw: Any) -> dict[str, Any]:
    r: dict[str, Any] = {
        "round_id": round_id,
        "scenario": "S22",
        "status": "done",
        "created_at": created,
        "tally": {"alone_realistic": {"finished": 1}},
        "runs": [{"run_id": f"{round_id}-R1", "outcome": "held"}],
        "source": "live",
        "pre_registration": None,
    }
    r.update(kw)
    return r


def _tree(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(p.relative_to(root)): (p.read_bytes() if p.is_file() else b"", p.stat().st_mtime_ns)
        for p in sorted(root.rglob("*"))
    }


def test_committed_copy_wins_and_is_read_only(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    rounds = runs_dir / FOLDER / "rounds"
    rounds.mkdir(parents=True)
    committed = _round(
        "RND-20261014-1",
        runs=[{"run_id": "RND-20261014-1-R1", "outcome": "unsafe_applied"}],
        pre_registration="abc1234",
    )
    (rounds / "RND-20261014-1.json").write_text(json.dumps(committed))
    (rounds / "RND-20261014-1").mkdir()
    (rounds / "RND-20261014-1" / "R1.calls.jsonl").write_text("")
    before = _tree(runs_dir)

    store = Store(tmp_path / "live", runs_dir)
    store.save_round(_round("RND-20261014-1", status="running"))
    store.save_round(_round("RND-20261014-2", created="2026-10-14T11:00:00+00:00"))

    source = f"runs/{FOLDER}/rounds/RND-20261014-1.json"
    got = store.get_round("RND-20261014-1")
    assert got is not None
    assert got["source"] == source
    assert got["pre_registration"] == "abc1234"
    assert got["runs"] == committed["runs"]
    assert got["status"] == "done"
    listed = {r["round_id"]: r for r in store.list_rounds()}
    assert set(listed) == {"RND-20261014-1", "RND-20261014-2"}
    assert listed["RND-20261014-1"]["source"] == source
    assert listed["RND-20261014-2"]["source"] == "live"
    assert [r["round_id"] for r in store.list_rounds()] == ["RND-20261014-2", "RND-20261014-1"]
    # a new id counts past live rounds and committed copies alike, so none is ever shadowed
    assert store.new_round_id("2026-10-14") == "RND-20261014-3"
    assert _tree(runs_dir) == before


def test_list_excludes_runs(tmp_path: Path) -> None:
    store = Store(tmp_path / "live", tmp_path / "runs")
    store.save_round(_round("RND-20261014-1"))
    (summary,) = store.list_rounds()
    assert "runs" not in summary
    assert summary["tally"] == {"alone_realistic": {"finished": 1}}
    full = store.get_round("RND-20261014-1")
    assert full is not None and full["runs"] == [{"run_id": "RND-20261014-1-R1", "outcome": "held"}]


def test_ids_paths_and_run_records(tmp_path: Path) -> None:
    store = Store(tmp_path / "live", tmp_path / "runs")
    assert store.new_round_id("2026-10-13") == "RND-20261013-1"
    store.save_round(_round("RND-20261013-1"))
    store.save_round(_round("RND-20261012-7"))
    assert store.new_round_id("2026-10-13") == "RND-20261013-2"
    assert store.run_paths("RND-20261013-1", "RND-20261013-1-B2") == (
        "rounds/RND-20261013-1/B2.transcript.jsonl",
        "rounds/RND-20261013-1/B2.calls.jsonl",
    )
    record = tmp_path / "live" / "rounds" / "RND-20261013-1" / "R1.json"
    assert json.loads(record.read_text()) == {"run_id": "RND-20261013-1-R1", "outcome": "held"}
    assert store.get_round("RND-20261013-9") is None
    assert store.get_round("../RND-20261013-1") is None
    assert store.get_round("*") is None
