"""Live rounds and committed copies of the B-15 proof rounds (spec §8).

A live round lives in `<live_dir>/rounds/<round_id>/`: `round.json` (the round, runs embedded),
each run's record (`R1.json`, ...), and each run's transcript and call log. Committed copies are
`<runs_dir>/<folder>/rounds/<round_id>.json`, copied in by hand after a pre-registered round. The
store only reads them: it never writes under `runs_dir`, and a committed copy wins when an id is in
both places. A finish (one agent turn plus a retry) is live state only, in
`<live_dir>/finishes/<finish_id>/finish.json`, apart from rounds and never under `runs_dir`.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*")


def _suffix(round_id: str, run_id: str) -> str:
    """`R1` from `RND-20261014-1-R1`."""
    return run_id.removeprefix(f"{round_id}-")


def _read(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write(path: Path, data: dict[str, Any]) -> None:
    """Write whole or not at all, so a reader in another thread never sees half a file."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


class Store:
    def __init__(self, live_dir: Path, runs_dir: Path) -> None:
        if live_dir.resolve().is_relative_to(runs_dir.resolve()):
            raise ValueError("the live directory must not be under the committed runs")
        self.live_dir = live_dir
        self.runs_dir = runs_dir

    def new_round_id(self, today: str) -> str:
        """`RND-YYYYMMDD-<k>`, k past every round of that day, live or committed."""
        prefix = f"RND-{today.replace('-', '')}-"
        taken = [i.removeprefix(prefix) for i in (*self._live(), *self._committed())]
        ks = [int(k) for k in taken if k.isdigit()]
        return f"{prefix}{max(ks, default=0) + 1}"

    def save_round(self, r: dict[str, Any]) -> None:
        folder = self.live_dir / "rounds" / r["round_id"]
        folder.mkdir(parents=True, exist_ok=True)
        for run in r.get("runs", []):
            _write(folder / f"{_suffix(r['round_id'], run['run_id'])}.json", run)
        _write(folder / "round.json", r)

    def run_paths(self, round_id: str, run_id: str) -> tuple[str, str]:
        """The transcript and call-log paths, relative to the live directory."""
        base = f"rounds/{round_id}/{_suffix(round_id, run_id)}"
        return f"{base}.transcript.jsonl", f"{base}.calls.jsonl"

    def live_round(self, round_id: str) -> dict[str, Any] | None:
        if not _SAFE_ID.fullmatch(round_id):
            return None
        return _read(self.live_dir / "rounds" / round_id / "round.json")

    def get_round(self, round_id: str) -> dict[str, Any] | None:
        if not _SAFE_ID.fullmatch(round_id):
            return None
        return self._committed(round_id).get(round_id) or self.live_round(round_id)

    def list_rounds(self) -> list[dict[str, Any]]:
        """Summaries (no `runs`), newest first."""
        merged = {**self._live(), **self._committed()}
        out = [{k: v for k, v in r.items() if k != "runs"} for r in merged.values()]
        return sorted(out, key=lambda r: (str(r.get("created_at")), str(r.get("round_id"))),
                      reverse=True)  # fmt: skip

    def new_finish_id(self, today: str) -> str:
        """`FIN-YYYYMMDD-<k>`, k past every live finish of that day."""
        prefix = f"FIN-{today.replace('-', '')}-"
        taken = [p.name.removeprefix(prefix) for p in self._finish_dirs()]
        ks = [int(k) for k in taken if k.isdigit()]
        return f"{prefix}{max(ks, default=0) + 1}"

    def save_finish(self, f: dict[str, Any]) -> None:
        folder = self.live_dir / "finishes" / f["finish_id"]
        folder.mkdir(parents=True, exist_ok=True)
        _write(folder / "finish.json", f)

    def finish_paths(self, finish_id: str, run_id: str) -> tuple[str, str]:
        """The transcript and call-log paths, relative to the live directory."""
        base = f"finishes/{finish_id}/{_suffix(finish_id, run_id)}"
        return f"{base}.transcript.jsonl", f"{base}.calls.jsonl"

    def get_finish(self, finish_id: str) -> dict[str, Any] | None:
        if not _SAFE_ID.fullmatch(finish_id):
            return None
        return _read(self.live_dir / "finishes" / finish_id / "finish.json")

    def list_finishes(self) -> list[dict[str, Any]]:
        """Summaries (no `turns`), newest first."""
        out: list[dict[str, Any]] = []
        for path in self._finish_dirs():
            f = _read(path / "finish.json")
            if f is not None:
                out.append({k: v for k, v in f.items() if k != "turns"})
        return sorted(out, key=lambda f: (str(f.get("created_at")), str(f.get("finish_id"))),
                      reverse=True)  # fmt: skip

    def _finish_dirs(self) -> list[Path]:
        return sorted((self.live_dir / "finishes").glob("*/"))

    def _live(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for path in sorted((self.live_dir / "rounds").glob("*/round.json")):
            r = _read(path)
            if r is not None:
                out[path.parent.name] = r
        return out

    def _committed(self, round_id: str = "*") -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for path in sorted(self.runs_dir.glob(f"*/rounds/{round_id}.json")):
            r = _read(path)
            if r is not None:
                r["source"] = f"runs/{path.parent.parent.name}/rounds/{path.name}"
                out[path.stem] = r
        return out
