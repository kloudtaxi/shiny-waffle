"""One organisation: settings, event log, clock, systems of record, people, the Jev replay engine,
the overlay evidence, the register and the procedures (spec §2).

The register is the registrar's bootstrap plus the stored result of every approved change
(`change.approved`, written by the register queue), replayed in log order without running any
rule. Approved texts live in the org's content store, `register-store/<sha256>.md`."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Literal

from . import _lab
from .clock import Clock
from .config import Settings
from .events import EventLog
from .people import People
from .sor import SystemsOfRecord


class Org:
    def __init__(
        self, settings: Settings, *, org_id: str = "northstar", corpus: str | None = None
    ) -> None:
        self.settings, self.org_id = settings, org_id
        self.corpus = corpus or settings.corpus
        self.dir = settings.state_dir / org_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.log = EventLog(self.dir / "events.sqlite")
        self.clock = Clock(self.log, org_id, settings.clock)
        self.clock.now()  # start it now: a first read inside a write transaction would deadlock
        root = _lab.corpus_root(self.corpus)
        self.sor = SystemsOfRecord(self.log, org_id, root)
        self.people = People(_lab.staff(root))
        self.engine = _lab.ReplayEngine(
            _lab.replay_files(_lab.LAB_ROOT),
            self.dir / "jev-calls.jsonl",
            live=settings.jev == "live",
            cap=settings.jev_cap,
        )
        self.evidence = _lab.make_evidence(root, self._overlay)
        self.register_store = self.dir / "register-store"
        self._state: tuple[int, Any] | None = None  # (the last approval's seq, the state)
        self._kernel_register: tuple[int, Any] | None = None

    def _overlay(self, name: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        """The kernel's view of a table: the systems of record's (base rows, inserts, edits)."""
        return self.sor.table(name)

    def register_state(self, tx: sqlite3.Connection | None = None) -> Any:
        """The registrar's state now: the bootstrap, then each approved change's stored result
        (`_lab.register_replay`). Rules never run again here. Cached until the next approval;
        `tx` reads the log inside a caller's write transaction."""
        approved = self.log.read(self.org_id, kinds=("change.approved",), tx=tx)
        key = approved[-1].seq if approved else 0
        cached = self._state
        if cached is None or cached[0] != key:
            results = [e.payload["result"] for e in approved]
            cached = (key, _lab.register_replay(self.corpus, results, self.register_text))
            self._state = cached
        return cached[1]

    def put_register_text(self, text: str) -> str:
        """Keep an approved text in the content store, by its fingerprint; that sha256."""
        sha = _lab.fingerprint(text)
        path = self.register_store / f"{sha}.md"
        if not path.exists():
            self.register_store.mkdir(parents=True, exist_ok=True)
            fd, part = tempfile.mkstemp(dir=self.register_store, prefix=f".{sha}.", suffix=".part")
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                    f.write(text)
                os.replace(part, path)
            except BaseException:
                Path(part).unlink(missing_ok=True)
                raise
        return sha

    def register_text(self, sha: str) -> str:
        """An approved text from the content store."""
        with (self.register_store / f"{sha}.md").open(encoding="utf-8", newline="") as f:
            return f.read()

    def kernel_register(self) -> Any:
        state = self.register_state()
        if self._kernel_register is None or self._kernel_register[0] != state.version:
            self._kernel_register = (
                state.version,
                _lab.kernel_register(state, self.dir / "store"),
            )
        return self._kernel_register[1]

    def procedures(self) -> tuple[list[dict[str, Any]], Path]:
        return _lab.procedures_bootstrap()

    def on_mismatch(self) -> Literal["use_registered", "route"]:
        """The register's setting (`settings.changed`, latest wins); `use_registered` until set."""
        found = self.log.read(self.org_id, stream="register:settings", kinds=("settings.changed",))
        if found and found[-1].payload["on_mismatch"] == "route":
            return "route"
        return "use_registered"

    def policy_terms(self, doc_id: str) -> dict[str, Any] | None:
        for e in self.register_state().entries:
            if e["doc_id"] == doc_id:
                terms: dict[str, Any] | None = e.get("terms")
                return terms
        return None
