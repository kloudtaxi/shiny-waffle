"""Finishes (B-19): S22 finished once in the product, by the `with_blueleaf` agent (spec §1-§8).

A finish's first turn runs Sarah's ask and is expected to be held. People then act in the product
(Sarah confirms the CRM's figure, Michael approves), and a retry turn runs Sarah's frozen follow-up,
expected to be applied as decided. Each turn goes through a `Runner` over the named service, so the
agent call, the classifier and the run record are the rounds' own (spec §4, §6).

- The named service is never reset: no turn sends `/lab/reset`, and `NamedService.restart` raises.
- A finish is never a round: it lives under `finishes/`, with no tally and no cap, and its turns
  carry `round_id: null`.
- The runner never repairs the service: its preconditions are reads only, and the first that fails
  refuses the turn before the agent runs (re-seeding is the presenter's job, spec §5).

A turn's `why` has the rounds' vocabulary plus "service: unreachable", for a named service that
didn't answer at all. A finish is `queued`, then `running`, then `waiting` (after a held first turn,
or a retry refused before its agent ran), `done` (after any other turn) or `stopped` ("runner
error", when the runner itself fails).
"""

from __future__ import annotations

import contextlib
import urllib.parse
from datetime import datetime
from typing import Any, Literal

from rounds.agent import AgentFn
from rounds.runner import (
    FoundationLike,
    Runner,
    RunnerConfig,
    Tables,
    _charged,
    _Ctx,
    _from_log,
    _Kb,
    _now,
    _print,
    _read_log,
    _row,
    _ServiceError,
)
from rounds.scenarios import ARMS, SCENARIOS, Scenario, sha
from rounds.store import Store

Turn = Literal["first", "retry"]
ARM = next(a for a in ARMS if a.id == "with_blueleaf")  # a finish runs this arm only
EXPECTED: dict[str, str] = {"first": "held", "retry": "applied_as_decided"}
LOOPBACK = ("127.0.0.1", "localhost")
ENDED = frozenset({"withdrawn", "declined", "spent"})  # a decision in any other state is live


class NamedService:
    """The presenter's service: the runner knows where it is, and nothing about running it."""

    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def url(self) -> str:
        return self._url

    def restart(self) -> None:
        raise RuntimeError("a named service is never restarted")


class NotWaiting(Exception):  # noqa: N818 (the name the plan fixes)
    """A retry of a finish that isn't `waiting` (the routes answer 409 `not_waiting`)."""


def check_service_url(url: str, rounds_port: int) -> str:
    """The named service's origin, `http://<host>:<port>`, or a ValueError with a one-line detail.

    Loopback only, since the agent's session token goes there (ruling F1). Never the rounds' own
    child: every round resets it."""
    try:
        u = urllib.parse.urlsplit(url)
        port = u.port
    except ValueError:
        raise ValueError("service_url is not a URL") from None
    if u.scheme != "http":
        raise ValueError("service_url must be http://")
    if u.username is not None or u.password is not None:
        raise ValueError("service_url must carry no credentials")
    if u.hostname not in LOOPBACK:
        raise ValueError("service_url must be on 127.0.0.1 or localhost")
    if not port:
        raise ValueError("service_url must name its port")
    if u.path not in ("", "/") or u.query or u.fragment:
        raise ValueError("service_url must have no path, query or fragment")
    if port == rounds_port:
        raise ValueError("service_url is the rounds' own service")
    return f"http://{u.hostname}:{port}"


def _row_check(sc: Scenario, tables: Tables) -> tuple[str, str, bool]:
    """The CRM row's check, named and read as `Runner._preconditions` does: `dr_9001`, what the
    row reads, and whether that is the scenario's starting row."""
    row = _row(tables, sc) or {}
    seen = f"{row.get('status')} at {row.get('requested_discount_pct')}" if row else "missing"
    name = sc.request_id.lower().replace("-", "_")
    return name, seen, seen == f"{sc.expect_status} at {sc.expect_pct}"


def first_checks(
    sc: Scenario, tables: Tables, clock: dict[str, Any], decisions: list[dict[str, Any]]
) -> tuple[dict[str, Any], str | None]:
    """The first turn's preconditions as recorded, and the first that fails (spec §5)."""
    name, seen, row_ok = _row_check(sc, tables)
    live = [d.get("decision_id") for d in decisions if d.get("state") not in ENDED]
    checks = ((name, row_ok), ("demo_date", clock.get("date") == sc.demo_date),
              ("no_live_decision", not live))  # fmt: skip
    recorded = {name: seen, "demo_date": clock.get("date"), "live_decisions": live}
    return recorded, next((check for check, ok in checks if not ok), None)


def retry_checks(
    sc: Scenario, tables: Tables, clock: dict[str, Any], first: dict[str, Any] | None,
    decision: dict[str, Any] | None,
) -> tuple[dict[str, Any], str | None]:  # fmt: skip
    """A retry's preconditions, each as a boolean, and the first that fails (spec §5).

    The service leaves unset fields out of a decision, so each one is read with a default."""
    d = decision or {}
    conditions, approvals = d.get("conditions") or [], d.get("approvals") or []
    turn1 = first or {}
    held = turn1.get("outcome") == "held" and bool((turn1.get("decision") or {}).get("id"))
    conflicts = [c.get("resolved") or {} for c in conditions if c.get("source") == "input_conflict"]
    confirmed = (
        decision is not None
        and all(c.get("resolved") for c in conditions if c.get("blocking"))
        and any(r.get("resolution") == "confirmed_record" for r in conflicts)
    )
    name, _, row_ok = _row_check(sc, tables)
    checks = (
        ("first_held", held), ("confirmed", confirmed),
        ("approved", decision is not None and all(a.get("given") for a in approvals)),
        ("not_executed", d.get("state") == "ready" and not d.get("executed")),
        (name, row_ok), ("demo_date", clock.get("date") == sc.demo_date),
    )  # fmt: skip
    about = {"id": d.get("decision_id"), "version": d.get("version"), "state": d.get("state")}
    return {**dict(checks), "decision": about}, next((c for c, ok in checks if not ok), None)


def _ask(sc: Scenario, turn: Turn) -> str:
    """What a turn sends: Sarah's ask, or on a retry her follow-up (ruling A: else her ask)."""
    return sc.ask if turn == "first" else (sc.retry_ask or sc.ask)


def _status(rec: dict[str, Any]) -> str:
    """Where a finish goes after a turn that ended without a runner error (spec §6)."""
    if rec["turn"] == "first":
        return "waiting" if rec["outcome"] == "held" else "done"
    return "waiting" if rec["tool_calls"] is None else "done"  # refused before its agent ran


class Finishes:
    """A finish's turns, each run by a `Runner` over the named service (spec §4)."""

    def __init__(
        self, config: RunnerConfig, agent: AgentFn, store: Store, foundation: FoundationLike | None
    ) -> None:
        self.config = config
        self.agent = agent
        self.store = store
        self.foundation = foundation

    def new_finish(
        self, scenario: Scenario, service_url: str, started_by: dict[str, Any]
    ) -> dict[str, Any]:
        """A `queued` finish, saved. `service_url` has been through `check_service_url`."""
        f: dict[str, Any] = {
            "finish_id": self.store.new_finish_id(datetime.now().astimezone().date().isoformat()),
            "scenario": scenario.id, "service_url": service_url, "status": "queued",
            "started_by": dict(started_by), "created_at": _now(),
            "scripted": self.config.scripted, "model": self.config.model,
            "ask_sha": sha(scenario.ask), "retry_ask_sha": sha(_ask(scenario, "retry")),
            "cost_usd": 0.0, "error": None, "source": "live", "turns": [],
        }  # fmt: skip
        self.store.save_finish(f)
        return f

    def start_retry(self, finish_id: str, started_by: dict[str, Any]) -> dict[str, Any]:
        """Queue a retry of a `waiting` finish. Who asked for it is kept for the coming turn, so a
        reader knows who pressed Retry (ruling P1)."""
        f = self.store.get_finish(finish_id)
        if f is None:
            raise KeyError(finish_id)
        if f.get("status") != "waiting":
            raise NotWaiting(finish_id)
        f.update(status="queued", retry_started_by=dict(started_by))
        self.store.save_finish(f)
        return f

    def run_turn(self, finish_id: str, turn: Turn) -> dict[str, Any]:
        """Run one turn. It always ends saved, `waiting`, `done` or `stopped`, with its `kb` token
        revoked; a SystemExit (the foundation client's way to fail) stops it too."""
        f = self.store.get_finish(finish_id)
        if f is None:
            raise KeyError(finish_id)
        pressed = f.pop("retry_started_by", None) if turn == "retry" else None
        started_by = pressed or f["started_by"]
        f["status"] = "running"
        service = NamedService(f["service_url"])
        eng = Runner(self.config, self.agent, self.store, service, self.foundation)
        ctx = _Ctx(SCENARIOS[f["scenario"]], None)
        check: dict[str, Any] = {"at_start": None, "at_end": None, "changed": None}
        minted: list[str] = []  # the `kb` token's id, once there is one to revoke
        rec: dict[str, Any] | None = None
        ended = False
        try:
            self.store.save_finish(f)
            found, kb_id = self.foundation, self.config.kb
            if found is not None and kb_id is not None:
                check["at_start"] = _print(found.fingerprint(kb_id))
                token, token_id = found.mint(kb_id)
                minted.append(token_id)
                ctx.kb = _Kb(found.mcp_url(kb_id), token, found.kb_tools(token, kb_id))
            rec = self._record(eng, f, ctx, turn, started_by, check)
            self._turn(eng, f, ctx, rec, turn)
            ended = True
        except (Exception, SystemExit):  # noqa: BLE001 - the turn stops; the finish is still saved
            pass
        finally:
            if rec is None:  # it failed before the turn had a record
                rec = self._record(eng, f, ctx, turn, started_by, check)
            self._close(eng, f, rec, minted, ended)
        return f

    def recover(self) -> None:
        """A finish left `queued` or `running` by a runner that died is `stopped`, so nothing
        shows as running for ever after a restart."""
        for summary in self.store.list_finishes():
            f = self.store.get_finish(str(summary.get("finish_id")))
            if f is not None and f.get("status") in ("queued", "running"):
                f.update(status="stopped", error="runner error")
                self.store.save_finish(f)

    def _record(
        self, eng: Runner, f: dict[str, Any], ctx: _Ctx, turn: Turn, started_by: dict[str, Any],
        check: dict[str, Any],
    ) -> dict[str, Any]:  # fmt: skip
        """A B-15 run record that never started (ruling B), made this finish's turn."""
        fid = f["finish_id"]
        n = 1 if turn == "first" else 1 + sum(t.get("turn") == "retry" for t in f["turns"])
        rec = eng._record({"round_id": fid, "scenario": ctx.scenario.id}, ctx, ARM, n)
        rec.update(run_id=f"{fid}-F" if turn == "first" else f"{fid}-R{n}", round_id=None, n=n,
                   finish_id=fid, turn=turn, expected=EXPECTED[turn],
                   started_by=dict(started_by), base_check=check)  # fmt: skip
        rec["agent"]["ask_sha"] = sha(_ask(ctx.scenario, turn))  # ruling C: the ask it was sent
        return rec

    def _turn(
        self, eng: Runner, f: dict[str, Any], ctx: _Ctx, rec: dict[str, Any], turn: Turn
    ) -> None:
        """The session, the reads and the preconditions; then the agent, unless one fails."""
        sc = ctx.scenario
        try:
            body = {"agent_id": sc.agent_id, "on_behalf_of": sc.on_behalf_of}
            session = eng._call("POST", "/lab/sessions", body)
            tables, _ = eng._snapshot()
            clock = eng._call("GET", "/lab/clock")
            rec["demo_time"] = clock.get("now")
            auth = str(session["token"])
            register = eng._call("GET", "/api/v1/register", token=auth)
            if turn == "first":
                query = urllib.parse.urlencode({"subject": sc.request_id})
                items = eng._call("GET", f"/api/v1/decisions?{query}", token=auth)["items"]
                checks, failed = first_checks(sc, tables, clock, items)
            else:
                first = next((t for t in f["turns"] if t.get("turn") == "first"), None)
                did = ((first or {}).get("decision") or {}).get("id")
                path = f"/api/v1/decisions/{urllib.parse.quote(str(did), safe='')}"
                decision = eng._call("GET", path, token=auth) if did else None
                checks, failed = retry_checks(sc, tables, clock, first, decision)
        except _ServiceError as e:
            rec["why"] = f"service: {e.status}"
            return
        except OSError:  # no HTTP status at all: the connection was refused, or timed out
            rec["why"] = "service: unreachable"
            return
        rec["preconditions"] = {**checks, "register_version": register.get("version")}
        if failed:
            rec["why"] = f"precondition: {failed}"
            return
        paths = self.store.finish_paths(f["finish_id"], rec["run_id"])
        eng._agent_turn(ctx, rec, ARM, session, tables, paths, ask=_ask(sc, turn),
                        steps=f"finish.{turn}")  # fmt: skip

    def _close(
        self, eng: Runner, f: dict[str, Any], rec: dict[str, Any], minted: list[str], ended: bool
    ) -> None:
        """The end fingerprint, the revoke, then the turn, its cost and the status; saved."""
        if not ended and rec["outcome"] == "incomplete" and rec["why"] is None:
            path = rec["tool_calls"]  # rule 1: a write in the call log is unsafe even so
            _from_log(rec, _read_log(self.store.live_dir / path) if path else [], None)
        with contextlib.suppress(Exception, SystemExit):
            eng._end_print(rec)  # best effort, so `base_check.changed` still answers
        if minted and self.foundation is not None:
            try:
                self.foundation.revoke(minted[0])
            except (Exception, SystemExit):  # noqa: BLE001
                ended = False
        rec["ended_at"] = _now()
        f["turns"].append(rec)
        f["cost_usd"] = round(f["cost_usd"] + _charged(rec), 6)
        if ended:
            f["status"] = _status(rec)
        else:
            f.update(status="stopped", error="runner error")
        with contextlib.suppress(OSError):
            self.store.save_finish(f)
