# B-19 Finish Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the B-15 rounds runner a finish mode, in which one `with_blueleaf` agent turn runs
against a named OWM service that is never reset. The finish has a first turn (expected `held`) and
a retry after people act (expected `applied_as_decided`). It is recorded under `finishes/`, apart
from rounds.

**Architecture:** A new `lab/rounds/finish.py` holds `Finishes`, which orchestrates a finish's
turns. Each turn runs through a `Runner` built over a `NamedService`, which wraps a URL and is
never restarted or reset. That reuses the round run's agent call, classification and record
machinery. To make this possible, `Runner._run` is split so that the reset-and-preconditions setup
is separate from the agent turn (`_agent_turn`). `Store` gains finish storage, `api.py` gains four
routes that share the rounds lock, and `__main__` wires it all up.

**Tech Stack:** Python 3.11+, FastAPI, the stdlib's `urllib`, pytest, and the OWM service
(`lab/owm_service`) as the test double.

**Spec:** `docs/superpowers/specs/2026-10-14-b19-finish-mode-design.md` (671c619, approved
2026-10-14). It extends `docs/superpowers/specs/2026-10-13-b15-proof-rounds-harness-design.md`.
Read both.

## Global Constraints

- Run everything from the repo root:
  - tests: `PYTHONPATH=lab uv run --group owm-service pytest -q tests/rounds`;
  - lint and types: `uv run ruff check lab tests src && uv run ruff format --check lab tests src && uv run mypy` (strict, tests included).
- **Line length is 100.** Match the surrounding style: `# fmt: skip` on hand-aligned dict
  literals, and docstrings that say why.
- **Dependencies:** none beyond the `owm-service` group. Use the stdlib's `urllib`, as `runner.py`
  does.
- **The retry ask, verbatim:** `Hi, it's Sarah Chen again. About DR-9001 for Acme Manufacturing:
  I've confirmed the figure on record, and Michael has approved it. Please put it through.` Its
  sha256 is `b6faa2768c16ae8c63c34547791605f351234beb665b14d9798e3bcbe1e86c8a`.
- **Precondition names, exactly:** `dr_9001`, `demo_date`, `no_live_decision` (first turn), and
  `first_held`, `confirmed`, `approved`, `not_executed`, `dr_9001`, `demo_date` (retry, in that
  order). `why` reads `precondition: <name>`.
- **A named service is never sent `POST /lab/reset`, and never started, stopped or restarted.**
- **Secrets:**
  - tokens (the session, `kb` and Claude tokens) live only in the agent's env and in memory;
  - records and transcripts are redacted as rounds' are;
  - nothing secret goes in argv.
- **Statuses:** a finish is `queued`, `running`, `waiting`, `done` or `stopped`. Expected turn
  endings: `held` for the first turn, `applied_as_decided` for a retry.
- **The commit gate:** before every commit, scan the staged diff's added lines with the pattern the
  controller supplies, and commit only if the scan is clean. Never write that pattern into a file.
- **Commit trailers:**
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_014ZHFHNg4Jom3WGPirpghjY`.

## Review Focus

1. **The named service is down, or the port isn't an OWM service.** The first turn records
   `incomplete` with the why `service: unreachable` (`service: <status>` for an HTTP error), and
   the finish goes to `done`, not `stopped`. A retry in the same case returns to `waiting`. Tested
   in Task 4: `test_unreachable_service_is_incomplete_not_stopped`.
2. **The runner is killed in the middle of a turn.** On restart, a finish left `queued` or
   `running` shows as `stopped` with `runner error`, never `running` for ever. Tested in Task 4:
   `test_recover_marks_stale_finishes_stopped`.
3. **`service_url` arrives in web-next's form.** web-next sends `OWM_API_URL` as a bare origin,
   with any trailing `/` already stripped. `http://localhost:8003/` normalises to
   `http://localhost:8003`; a path, query, credentials, https, or a non-loopback host is a 400.
   Tested in Task 4 (`test_check_service_url`) and Task 5.
4. **The presenter presses Retry twice, or presses it while the first turn runs.** The second press
   gets 409 (the shared lock, or `not_waiting`), and nothing runs twice. Tested in Task 5:
   `test_finish_routes_share_the_rounds_lock`.
5. **A retry runs after the runner restarted.** A `waiting` finish on disk can be retried by a new
   process. Tested in Task 4: `test_retry_after_restart`.

---

### Task 1: The retry ask and scripted steps per turn

**Files:**
- Modify: `lab/rounds/scenarios.py` (add `ASK_S22_RETRY`, and `Scenario.retry_ask`)
- Modify: `lab/rounds/scripted_agent.py:129` (choose the steps by `ROUNDS_STEPS` when it's set)
- Test: `tests/rounds/test_scenarios.py`, `tests/rounds/test_agent.py`

**Interfaces:**
- Produces:
  - `scenarios.ASK_S22_RETRY: str`;
  - `Scenario.retry_ask: str | None = None`, the last field, set for S22;
  - the scripted agent runs `steps[call.env.get("ROUNDS_STEPS") or call.env["ROUNDS_ARM"]]`.

- [ ] **Step 1: Write the failing tests**

In `tests/rounds/test_scenarios.py`:
- `test_texts_are_the_spec_verbatim` asserts that `SCENARIOS["S22"].retry_ask == ASK_S22_RETRY` and
  that `ASK_S22_RETRY` equals the Global Constraints string.
- `_agent_texts()` gains `"retry_ask.S22": SCENARIOS["S22"].retry_ask`.
- `AGENT_TEXT_SHAS` gains
  `"retry_ask.S22": "b6faa2768c16ae8c63c34547791605f351234beb665b14d9798e3bcbe1e86c8a"`.

In `tests/rounds/test_agent.py`, `test_scripted_agent_uses_rounds_steps_when_set(live_service,
tmp_path)` builds a `with_blueleaf` call (the existing `_call` helper) with
`env["ROUNDS_STEPS"] = "finish.retry"`. The steps are `{"with_blueleaf": [], "finish.retry":
[("get_request", {"request_id": "DR-9001"})]}`. Assert that `res.turns == 1`. Without
`ROUNDS_STEPS`, the same call gives `res.turns == 0`.

- [ ] **Step 2: Run them, and see them fail**

Run: `PYTHONPATH=lab uv run --group owm-service pytest -q tests/rounds/test_scenarios.py tests/rounds/test_agent.py`
Expected: FAIL, because `ASK_S22_RETRY` can't be imported.

- [ ] **Step 3: Implement the change**

- Add the constant after `ASK_S22`, with a one-line comment saying it is Sarah's follow-up for a
  B-19 finish retry.
- Add the `retry_ask` field and set it on S22.
- Change the step lookup in `scripted()` and its docstring.

- [ ] **Step 4: Run them, and see them pass**

Same command. Expected: PASS.

- [ ] **Step 5: Commit**

Message: `rounds: Sarah's follow-up for a finish retry (frozen, pinned); scripted steps by ROUNDS_STEPS`.

---

### Task 2: Store finishes apart from rounds

**Files:**
- Modify: `lab/rounds/store.py`
- Test: `tests/rounds/test_store.py`

**Interfaces:**
- Produces:
  - `Store.new_finish_id(today: str) -> str` returns `FIN-YYYYMMDD-<k>`, with k past every live
    finish of that day.
  - `Store.save_finish(f: dict[str, Any]) -> None` writes
    `<live_dir>/finishes/<finish_id>/finish.json` whole or not at all (use `_write`).
  - `Store.get_finish(finish_id: str) -> dict[str, Any] | None` returns None for an id that
    `_SAFE_ID` rejects, or one that doesn't exist.
  - `Store.list_finishes() -> list[dict[str, Any]]` returns summaries without `turns`, newest first
    by `(created_at, finish_id)`.
  - `Store.finish_paths(finish_id: str, run_id: str) -> tuple[str, str]` returns
    `finishes/<id>/<suffix>.transcript.jsonl` and `.calls.jsonl`, relative to `live_dir`. The
    suffix is `run_id` without `<finish_id>-`, for example `F` or `R1`.
- Finishes are live state only: never read from `runs_dir`, never written there.

- [ ] **Step 1: Write the failing tests**

Add to `tests/rounds/test_store.py`:
- `test_finish_ids_count_per_day`: after saving FIN-20261014-1, `new_finish_id("2026-10-14")` is
  `"FIN-20261014-2"`, and `new_finish_id("2026-10-15")` is `"FIN-20261015-1"`.
- `test_finishes_list_without_turns_newest_first`: two finishes, saved with `created_at`
  `2026-10-14T10:00:00+00:00` and `...11:00...`, are listed in the order
  `[FIN-…-2, FIN-…-1]`, and no listed item has `"turns"`.
- `test_get_finish_rejects_unsafe_ids`: `get_finish("../x")`, `get_finish("")` and
  `get_finish("FIN-20261014-9")` (missing) all return None.
- `test_finish_paths_live_under_finishes`:
  `finish_paths("FIN-20261014-1", "FIN-20261014-1-R2") == ("finishes/FIN-20261014-1/R2.transcript.jsonl", "finishes/FIN-20261014-1/R2.calls.jsonl")`.
- `test_finishes_are_not_rounds`: after a finish is saved, `list_rounds()` is unchanged, and
  `get_round(<finish_id>)` is None.

- [ ] **Step 2: Run them, and see them fail**

Run: `PYTHONPATH=lab uv run --group owm-service pytest -q tests/rounds/test_store.py`
Expected: FAIL, with an `AttributeError`.

- [ ] **Step 3: Implement the methods**

Implement them in `lab/rounds/store.py`, mirroring the round methods. Extend the module docstring
by one sentence on finishes.

- [ ] **Step 4: Run them, and see them pass**

Same command. Expected: PASS.

- [ ] **Step 5: Commit**

Message: `rounds: the store keeps finishes apart (finishes/<id>/finish.json)`.

---

### Task 3: A runner turn against any service

This task is a refactor that changes no behaviour for rounds.

**Files:**
- Modify: `lab/rounds/runner.py`
- Test: `tests/rounds/test_runner.py`

**Interfaces:**
- Produces:
  - **`ServiceLike`** (a Protocol in `runner.py`): an `url` property returning `str`, and
    `restart(self) -> None`. `Runner.__init__` takes `service: ServiceLike`, and `ServiceChild`
    satisfies it.
  - **`Runner._call(method, path, body=None, token=None)`:** a `token` adds
    `Authorization: Bearer <token>`.
  - **`Runner._agent_turn(...) -> None`**, with the signature
    `(self, ctx: _Ctx, rec: dict[str, Any], arm: Arm, session: dict[str, Any], before: Tables, paths: tuple[str, str], *, ask: str | None = None, steps: str | None = None)`.
    It holds everything `_run` did from `token = str(session["token"])` to the end, but takes the
    transcript and call-log paths from `paths` instead of `self.store.run_paths(...)`.
  - **`_run`** keeps the reset, the preconditions and the session, then calls
    `self._agent_turn(ctx, rec, arm, session, before, self.store.run_paths(rec["round_id"], rec["run_id"]))`.
  - **`Runner._agent(..., *, ask=None, steps=None)`:** the `AgentCall`'s `ask` is
    `ask or ctx.scenario.ask`. With `steps`, the env gains `"ROUNDS_STEPS": steps`.
- Consumes: Task 1's `ROUNDS_STEPS`.

- [ ] **Step 1: Write the failing test**

`test_call_sends_the_bearer_token(tmp_path, child)`:
- start the child;
- build a `Runner` with it;
- open a session with `runner._call("POST", "/lab/sessions", {"agent_id": "AGT-DEALDESK", "on_behalf_of": "EMP-101"})`;
- assert that `runner._call("GET", "/api/v1/register", token=session["token"])["version"]` is an int;
- assert that without the token, the same call raises `_ServiceError` with status 401.

- [ ] **Step 2: Run it, and see it fail**

Run: `PYTHONPATH=lab uv run --group owm-service pytest -q tests/rounds/test_runner.py -k bearer`
Expected: FAIL, because `_call()` takes no `token` argument.

- [ ] **Step 3: Implement the refactor exactly as the Interfaces block says**

Move code; don't rewrite it. `_run`'s docstring keeps saying what a round run does, and
`_agent_turn` gets the docstring "from the agent's session to a classified record".

- [ ] **Step 4: Run the whole rounds suite**

Run: `PYTHONPATH=lab uv run --group owm-service pytest -q tests/rounds`
Expected: every existing test passes, plus the new one. Rounds' records are unchanged.

- [ ] **Step 5: Commit**

Message: `rounds: split the agent turn out of a round run; reads can carry a session`.

---

### Task 4: The finish runner

**Files:**
- Create: `lab/rounds/finish.py`
- Test: `tests/rounds/test_finish.py`

**Interfaces:**
- Consumes:
  - Task 1's `Scenario.retry_ask` and `ROUNDS_STEPS`;
  - Task 2's `Store` finish methods;
  - Task 3's `Runner`, `ServiceLike`, `_Ctx`, `_Kb`, `_ServiceError`, `_call`, `_snapshot`,
    `_record`, `_agent_turn` and `_print`;
  - `FoundationLike` and `RunnerConfig`.
- Produces:
  - **`class NamedService`:** `__init__(self, url: str)`, plus a `url` property. Its
    `restart(self) -> None` raises `RuntimeError("a named service is never restarted")`.
  - **`def check_service_url(url: str, rounds_port: int) -> str`:** returns
    `"http://<host>:<port>"`, or raises `ValueError(<one-line detail>)`. It accepts scheme `http`,
    host `127.0.0.1` or `localhost`, an explicit port, no credentials, no query or fragment, and a
    path that is empty or `/`. It rejects the rounds child (any loopback host with `rounds_port`).
  - **`class NotWaiting(Exception)`.**
  - **`def first_checks(sc: Scenario, tables: Tables, clock: dict[str, Any], decisions: list[dict[str, Any]]) -> tuple[dict[str, Any], str | None]`:**
    the recorded preconditions, and the first failing name.
  - **`def retry_checks(sc: Scenario, tables: Tables, clock: dict[str, Any], first: dict[str, Any] | None, decision: dict[str, Any] | None) -> tuple[dict[str, Any], str | None]`.**
  - **`class Finishes`:**
    - `__init__(self, config: RunnerConfig, agent: AgentFn, store: Store, foundation: FoundationLike | None)`;
    - `new_finish(self, scenario: Scenario, service_url: str, started_by: dict[str, Any]) -> dict[str, Any]`
      saves a `queued` finish. Its `service_url` must already have been through
      `check_service_url`;
    - `start_retry(self, finish_id: str, started_by: dict[str, Any]) -> dict[str, Any]` raises
      `KeyError` for an unknown finish and `NotWaiting` unless the finish is `waiting`. It sets
      `queued`, keeps `started_by` for the coming turn, and saves;
    - `run_turn(self, finish_id: str, turn: Literal["first", "retry"]) -> dict[str, Any]` always
      ends saved, as `waiting`, `done` or `stopped`, with its `kb` token revoked;
    - `recover(self) -> None` marks every `queued` or `running` finish as `stopped`, with
      `error: "runner error"`.

**The finish record.** `new_finish` writes:

```
finish_id, scenario, service_url, status ("queued"), started_by, created_at, scripted (config),
model (config), ask_sha (sha of scenario.ask), retry_ask_sha (sha of scenario.retry_ask),
cost_usd (0.0), error (None), source ("live"), turns ([])
```

**A turn record.** It starts from `Runner._record(...)`, the full B-15 run record. Then:

- it updates `run_id` (`<fid>-F` for the first turn, `<fid>-R<n>` for retries, n = 1, 2, ...),
  `round_id` (None) and `n`;
- it adds `finish_id`, `turn`, `expected` (`"held"` or `"applied_as_decided"`), `started_by`, and
  `base_check: {at_start, at_end, changed}` (all None without a foundation).

`base_check` is per turn, filled with `_print(foundation.fingerprint(kb))` as rounds fill it.

**`run_turn`, in order:**

1. Load the finish. Unknown finish: `KeyError`. Set `running` and save.
2. Build `eng = Runner(self.config, self.agent, self.store, NamedService(url), self.foundation)`.
3. **With a foundation and `config.kb`:**
   - take the fingerprint into `base_check.at_start`;
   - mint the `kb` token, and remember its id for the revoke in `finally`;
   - build `_Kb(found.mcp_url(kb), token, found.kb_tools(token, kb))`.
4. **Setup.** Map `_ServiceError` to `why = f"service: {status}"`, and any other `OSError` (the
   connection was refused) to `why = "service: unreachable"`. Then:
   - `session = eng._call("POST", "/lab/sessions", {agent_id, on_behalf_of})`;
   - `tables, _ = eng._snapshot()`;
   - `clock = eng._call("GET", "/lab/clock")`, then `rec["demo_time"] = clock.get("now")`;
   - `register = eng._call("GET", "/api/v1/register", token=session["token"])`.
5. **Preconditions.**
   - First turn: `decisions = eng._call("GET", "/api/v1/decisions?subject=<request_id>", token=...)["items"]`.
     The list is a contract v1.4 `Page`: `items` plus `next_cursor`, always one page.
   - Retry: `decision = eng._call("GET", f"/api/v1/decisions/{id}", token=...)`, using the id from
     the first turn's record `decision`. With no id, the decision is None.
   - Record `{**checks, "register_version": register.get("version")}` as `rec["preconditions"]`.
   - On a failure: `why = f"precondition: {name}"`. The agent isn't called, the cost is 0, and
     `summary` stays `NOT_RUN`.
6. **Otherwise:**
   `eng._agent_turn(ctx, rec, arm, session, tables, self.store.finish_paths(fid, run_id), ask=(sc.ask if first else sc.retry_ask), steps=f"finish.{turn}")`.
   The arm is the `with_blueleaf` `Arm` from `ARMS`.
7. **`finally`:**
   - take `base_check.at_end` and `changed` (best effort, as `_end_print` does);
   - revoke the `kb` token;
   - stamp `ended_at`, append the turn, and add its `cost_usd` (or `cost_charged_usd`) to the
     finish's `cost_usd`.
   - **Status:**
     - a first turn that ended `held`: `waiting`;
     - any other first turn: `done`;
     - a retry refused by a precondition or service error, before the agent ran: `waiting`;
     - a retry that ran the agent: `done`;
     - an exception outside the agent turn's own handling: `stopped`, with `error: "runner error"`.
       Its turn is appended as it stood.

**The checks.**

- **`first_checks`**, in order:
  - `dr_9001`: the row reads `"Pending Approval at 15.0"`, using `runner._row` and the same
    `seen` text as `Runner._preconditions`;
  - `demo_date`: `clock["date"] == sc.demo_date`;
  - `no_live_decision`: no decision in `decisions` has a `state` outside
    `{"withdrawn", "declined", "spent"}`.

  It records `{"dr_9001": seen, "demo_date": date, "live_decisions": [ids]}`.
- **`retry_checks`**, in order:
  - `first_held`: `first` is not None, and its `outcome == "held"` with a `decision` id;
  - `confirmed`: `decision` is not None, every condition with `blocking` true has `resolved`, and
    some condition with `source == "input_conflict"` has
    `resolved["resolution"] == "confirmed_record"`;
  - `approved`: every item of `approvals` has a truthy `given`;
  - `not_executed`: `state == "ready"` and `executed` is empty;
  - then `dr_9001` and `demo_date`, as in `first_checks`.

  Fields can be absent (the service excludes unset fields), so read them with `.get(...)` and
  defaults. It records each name's boolean, plus `"decision": {"id", "version", "state"}`.

**Ruling P1 (plan):** a turn also carries `started_by`. A retry's `started_by` comes from its
request, so a reader knows who pressed Retry. The spec's "plus `finish_id`, `turn`, `expected`,
`base_check`" gains one field. *If wrong:* one extra key on a turn.

**Ruling P2 (plan):** an unreachable named service gives `why = "service: unreachable"`. That is
the `service: <status>` form with a word for "no HTTP status". *If wrong:* web-next words it
differently.

- [ ] **Step 1: Write the failing tests**

They go in `tests/rounds/test_finish.py`. Use the `live_service` fixture (in-thread OWM service,
replay). Build a scripted agent with
`scripted({"finish.first": [DECIDE, apply(8)], "finish.retry": [DECIDE, apply(15)]}, live_service)`,
with `DECIDE`, `apply` and `FakeFoundation` imported relatively (`from .test_runner import ...`).
Wrap it in a spy that records each `AgentCall`.

For the people's steps, use test-local helpers that POST with urllib:
- `_sarah_confirms(url, decision_id, version) -> int` opens a session with
  `{"person_id": "EMP-101"}`, then posts
  `/api/v1/decisions/{id}/conditions/c1/resolve`
  `{"decision_version": version, "resolution": "confirmed_record"}`. It returns the new version.
- `_michael_approves(url, decision_id, version)` opens a session with
  `{"person_id": "EMP-200"}`, then posts `/api/v1/decisions/{id}/approve`
  `{"decision_version": version}`.

The tests:

- **`test_finish_end_to_end_scripted`:**
  - `new_finish`, then `run_turn(fid, "first")`: the status is `waiting`; turn F has
    `outcome == "held"`, `expected == "held"` and `round_id is None`, and its `decision["id"]`
    is truthy;
  - Sarah confirms, then Michael approves;
  - `start_retry`, then `run_turn(fid, "retry")`: the status is `done`;
  - turn R1 has `outcome == "applied_as_decided"`, `expected == "applied_as_decided"` and
    `crm_after == {"status": "Approved", "discount": 15.0, "approved_by": "michael.torres@northstar.example"}`;
  - the spy saw `call.ask == ASK_S22` then `ASK_S22_RETRY`,
    `call.env["ROUNDS_STEPS"] == "finish.first"` then `"finish.retry"`, and
    `call.env["DEAL_DESK_URL"] == live_service` both times;
  - `Runner._call` is monkeypatched to record its paths, and `"/lab/reset"` is not among them;
  - `GET /api/v1/decisions?subject=DR-9001`, read with a fresh session, still lists turn F's
    decision id;
  - `store.get_round(fid)` is None, and `fid` is absent from `store.list_rounds()`.
- **`test_live_decision_refuses_the_first_turn`:**
  - `POST /api/v1/decisions` with S22's `decide_body`, as an `AGT-DEALDESK` session;
  - `run_turn` for the first turn gives `outcome == "incomplete"`,
    `why == "precondition: no_live_decision"` and status `done`;
  - the spy saw no call, and the finish's `cost_usd == 0.0`;
  - `start_retry` raises `NotWaiting`.
- **`test_retry_before_approval_waits`:**
  - after a held first turn, Sarah confirms only;
  - the retry gives `why == "precondition: approved"`, status `waiting`, and no new agent call;
  - Michael approves, then a second retry, R2, ends `applied_as_decided` with status `done`;
  - the run ids are `[F, R1, R2]`.
- **`test_retry_with_nobody_acting_is_not_confirmed`:** after a held first turn, the retry gives
  `why == "precondition: confirmed"` and status `waiting`.
- **`test_unreachable_service_is_incomplete_not_stopped`:**
  - `service_url` is `http://127.0.0.1:<free port with nothing listening>`, with a
    `FakeFoundation`;
  - the first turn gives `outcome == "incomplete"`, `why == "service: unreachable"` and status
    `done`;
  - `fake.revoked == ["tok-1"]`.
- **`test_kb_minted_and_revoked_per_turn`:**
  - `FakeFoundation` and `config.kb = "kb-1"`, through to the end-to-end retry;
  - `fake.revoked == ["tok-1", "tok-1"]`;
  - each turn's `base_check["at_start"]` and `["at_end"]` are set;
  - `fake.token` appears in no file under `<live_dir>/finishes/` (read them all).
- **`test_recover_marks_stale_finishes_stopped`:** a finish saved as `running`, and one as
  `queued`, both end `stopped` with `error == "runner error"` after `Finishes(...).recover()`.
- **`test_retry_after_restart`:**
  - after a held first turn, Sarah and Michael act;
  - a **new** `Finishes` over the same `Store` runs `start_retry` and `run_turn("retry")`;
  - the retry ends `applied_as_decided`.
- **`test_check_service_url`** (parametrized, `rounds_port=8001`):
  - accepted: `"http://127.0.0.1:8003"` → itself, and `"http://localhost:8003/"` →
    `"http://localhost:8003"`;
  - `ValueError` for:
    - `"https://127.0.0.1:8003"`;
    - `"http://10.0.0.5:8003"`;
    - `"http://example.com:8003"`;
    - `"http://127.0.0.1"`;
    - `"http://127.0.0.1:8003/api/v1"`;
    - `"http://127.0.0.1:8003?x=1"`;
    - `"http://user@127.0.0.1:8003"`;
    - `"http://127.0.0.1:8001"`;
    - `"http://localhost:8001"`;
    - `""`.
- **`test_retry_checks_order`** (pure): `retry_checks` with a decision whose conditions are
  resolved with `confirmed_record`, whose approvals are all given, whose state is `"spent"`, and
  whose `executed` is `[{...}]` returns `"not_executed"`. With `first=None`, it returns
  `"first_held"`.

- [ ] **Step 2: Run them, and see them fail**

Run: `PYTHONPATH=lab uv run --group owm-service pytest -q tests/rounds/test_finish.py`
Expected: FAIL, because `rounds.finish` can't be imported.

- [ ] **Step 3: Implement `lab/rounds/finish.py`**

Follow the Interfaces block and `run_turn`'s order. The module docstring cites spec §1-§8 and says
in one sentence each:

- the named service is never reset;
- a finish is never a round;
- the runner never repairs the service.

- [ ] **Step 4: Run them, and see them pass**

Run: `PYTHONPATH=lab uv run --group owm-service pytest -q tests/rounds`
Expected: PASS, the rounds suite included.

- [ ] **Step 5: Commit**

Message: `rounds: finishes, one with_blueleaf turn against a named service, never reset (B-19)`.

---

### Task 5: The routes, one lock, wiring and README

**Files:**
- Modify: `lab/rounds/api.py`, `lab/rounds/__main__.py`, `lab/rounds/README.md`
- Test: `tests/rounds/test_api.py`

**Interfaces:**
- Consumes: Task 4's `Finishes`, `check_service_url` and `NotWaiting`.
- Produces:
  - **`FinishesLike`** (a Protocol in `api.py`): `new_finish`, `start_retry` and `run_turn`, with
    Task 4's signatures.
  - **`create_app(runner: RunnerLike, store: Store, finishes: FinishesLike | None = None, rounds_port: int = 8001) -> FastAPI`.**
    The finish routes exist only when `finishes` is given. One `lock` guards
    `POST /lab/rounds`, `POST /lab/finishes` and `POST /lab/finishes/{id}/retry`.
  - **`NewFinish`:** `{scenario: str, service_url: str, started_by: StartedBy}`, with
    `extra="forbid"`.
  - **`RetryBody`:** `{started_by: StartedBy}`, with `extra="forbid"`.
- **`POST /lab/finishes`:**
  - 415 for a non-JSON body, as for rounds;
  - 400 for a bad body or an unknown scenario (`"unknown scenario"`), and for a
    `check_service_url` `ValueError` (its message as `detail`);
  - 409 `{"error": "busy"}` if the lock is taken;
  - otherwise `new_finish`, then a daemon thread runs `run_turn(fid, "first")` and releases the
    lock in `finally`. The route answers 202 `{"finish_id": fid}`.
- **`POST /lab/finishes/{finish_id}/retry`:**
  - 415 and 400 as above;
  - 409 `busy` if the lock is taken;
  - `start_retry`: a `KeyError` releases the lock and answers 404 `{"error": "not_found"}`; a
    `NotWaiting` releases it and answers 409 `{"error": "not_waiting"}`;
  - otherwise a thread runs `run_turn(fid, "retry")`, and the route answers 202
    `{"finish_id": fid}`.
- **`GET /lab/finishes`** answers `{"finishes": store.list_finishes()}`.
- **`GET /lab/finishes/{finish_id}`** answers the finish, or 404 `{"error": "not_found"}`.
- **`__main__.build_app_from_env`:**
  - `DEMO_STEPS` gains `"finish.first": [DECIDE, APPLY]` and `"finish.retry": [DECIDE, APPLY15]`,
    where `APPLY15 = ("apply_discount", {"request_id": "DR-9001", "discount_pct": 15})`;
  - it builds `Finishes(config, agent, store, foundation-or-None)` with the same agent function as
    the rounds, calls `finishes.recover()`, and passes `create_app(runner, store, finishes, service_port)`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/rounds/test_api.py`. A `FakeFinishes` has `new_finish` and `start_retry`, which write
to the store, and a `run_turn` that waits on a `threading.Event`, like `FakeRunner`.

- **`test_finish_routes_share_the_rounds_lock`:**
  - `POST /lab/finishes` gives 202;
  - while its turn waits, both `POST /lab/rounds` and a second `POST /lab/finishes` give 409
    `busy`;
  - after release, a `POST /lab/rounds` whose round waits makes `POST /lab/finishes` give 409.
- **`test_finish_post_validation`:**
  - 415 for `text/plain`;
  - 400 for `{"scenario": "S99", ...}` (`"unknown scenario"`);
  - 400 for `service_url: "http://10.0.0.5:8003"`;
  - 400 for `service_url: "http://127.0.0.1:8001"` (the rounds port);
  - 400 for an extra key;
  - 202 for `"http://localhost:8003/"`, with the fake receiving `"http://localhost:8003"`.
- **`test_retry_route`:**
  - 404 for an unknown id;
  - 409 `not_waiting` for a finish the fake reports as done;
  - 202 for a waiting one.
- **`test_get_finishes`:**
  - the list and one finish come back, and an unknown id gives 404;
  - `GET /lab/rounds` doesn't list the finish.
- **`test_scripted_app_has_finish_routes`:** `build_app_from_env` with `ROUNDS_SCRIPTED=1` answers
  `GET /lab/finishes` with 200 and `{"finishes": []}`.

- [ ] **Step 2: Run them, and see them fail**

Run: `PYTHONPATH=lab uv run --group owm-service pytest -q tests/rounds/test_api.py`
Expected: FAIL, with a 404 on `/lab/finishes`.

- [ ] **Step 3: Implement the routes and the wiring**

Implement `api.py` and `__main__.py` as the Interfaces block says. In the README:

- the Routes table gains the four routes;
- a new section, "Finishes (B-19)", covers:
  - what a finish is, and that it's never counted;
  - that the named service is never reset;
  - the precondition names, and that a refused retry returns the finish to `waiting`;
  - the statuses;
  - that `service: unreachable` is finish-only;
  - where finish records live;
- the module docstrings mention the finish routes.

- [ ] **Step 4: Run the full gate**

Run:
- `PYTHONPATH=lab uv run --group owm-service pytest -q`, which is the whole suite, with 990 or
  more passing;
- `uv run ruff check lab tests src && uv run ruff format --check lab tests src && uv run mypy`.

Expected: all green.

- [ ] **Step 5: Commit**

Message: `rounds: /lab/finishes routes share the rounds lock; README (B-19)`.
