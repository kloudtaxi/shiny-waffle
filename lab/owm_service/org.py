"""One organisation: settings, event log, clock, systems of record, people, the Jev replay engine,
the overlay evidence, the register and the procedures (spec §2).

The register is the registrar's bootstrap plus the stored result of every approved change
(`change.approved`, written by the register queue), replayed in log order without running any
rule. Approved texts live in the org's content store, `register-store/<sha256>.md`.

The procedures are the procedure register's bootstrap plus every approved procedure version
(`procedure.approved`, also written by the register queue; ruling R50 keeps it apart from the
document register). Their approved texts live in `procedure-store/<sha256>.yaml`, the bootstrap's
copied there from the lab's store, and that is what decisions run. Every read checks each stored
text's fingerprint against its registered sha256 first: a text that differs stops the procedure
register (`CannotDecide`, so a decision fails closed with a 503) and is never mirrored or run.
`procedure-specs/<file>` then mirrors each verified text under its version's file name, never
outside that directory, because the kernel checks a version's file against its registered sha256
(`incident: the procedure file … differs`) and would otherwise flag every version registered
here."""

from __future__ import annotations

import copy
import os
import sqlite3
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from . import _lab
from .clock import Clock
from .config import Settings
from .errors import CannotDecide
from .events import EventLog
from .people import People
from .sor import SystemsOfRecord


def _write(path: Path, text: str) -> None:
    """`text` at `path`, whole or not at all (a temp file, then a rename), as UTF-8 with its line
    endings untouched."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, part = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(part, path)
    except BaseException:
        Path(part).unlink(missing_ok=True)
        raise


def _read(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as f:
        return f.read()


class Org:
    def __init__(
        self, settings: Settings, *, org_id: str = "northstar", corpus: str | None = None,
        procedure_filter: Callable[[dict[str, Any]], bool] | None = None,
    ) -> None:  # fmt: skip
        """`procedure_filter` is for tests only: it keeps the bootstrap's procedure versions it
        returns true for (approved versions are never filtered)."""
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
        self.procedure_store = self.dir / "procedure-store"
        self.procedure_specs = self.dir / "procedure-specs"
        self._procedure_filter = procedure_filter
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
            _write(path, text)
        return sha

    def register_text(self, sha: str) -> str:
        """An approved text from the content store."""
        return _read(self.register_store / f"{sha}.md")

    def kernel_register(self) -> Any:
        state = self.register_state()
        if self._kernel_register is None or self._kernel_register[0] != state.version:
            self._kernel_register = (
                state.version,
                _lab.kernel_register(state, self.dir / "store"),
            )
        return self._kernel_register[1]

    # -- procedures ---------------------------------------------------------------------------
    def procedures(self, tx: sqlite3.Connection | None = None) -> tuple[list[dict[str, Any]], Path]:
        """The procedure register now and the store its texts run from: the bootstrap's versions
        (through `procedure_filter`), then each approved version (`procedure.approved`), in log
        order. Every version's text is in the store, matches its sha256, and is mirrored in
        `procedure_specs` before this returns; a text that doesn't match, or a file that would
        land outside `procedure_specs`, raises `CannotDecide`. Copies; `tx` reads the log inside
        a caller's write transaction."""
        boot, lab_store = _lab.procedures_bootstrap()
        keep = self._procedure_filter
        boot = [e for e in boot if keep is None or keep(e)]
        for e in boot:
            if not self._procedure_path(e["sha256"]).exists():
                self.put_procedure_text(_read(lab_store / f"{e['sha256']}.yaml"))
        approved = self.log.read(self.org_id, kinds=("procedure.approved",), tx=tx)
        entries = [*boot, *(copy.deepcopy(ev.payload["entry"]) for ev in approved)]
        specs = self.procedure_specs.resolve()
        for e in entries:
            name = f"{e['proc_id']} v{e['version']}"
            text = self.procedure_text(e["sha256"])
            if _lab.fingerprint(text) != e["sha256"]:
                raise CannotDecide(f"the procedure store's text for {name} doesn't match its "
                                   f"registered sha256 {e['sha256']}; it doesn't run")  # fmt: skip
            mirror = (specs / str(e["file"])).resolve()
            if mirror.parent != specs:
                raise CannotDecide(f"the file {e['file']!r} of {name} would be mirrored outside "
                                   "the procedure specs; it doesn't run")  # fmt: skip
            if not mirror.exists() or _read(mirror) != text:
                _write(mirror, text)
        return entries, self.procedure_store

    def _procedure_path(self, sha: str) -> Path:
        return self.procedure_store / f"{sha}.yaml"

    def put_procedure_text(self, text: str) -> str:
        """Keep an approved procedure text in the procedure store, by its fingerprint; that
        sha256."""
        sha = _lab.fingerprint(text)
        path = self._procedure_path(sha)
        if not path.exists():
            _write(path, text)
        return sha

    def procedure_text(self, sha: str) -> str:
        """An approved procedure text from the procedure store."""
        return _read(self._procedure_path(sha))

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
