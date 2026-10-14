"""The `/lab/rounds` HTTP API that web-next's `/present` page calls, server-side only (spec §7).

Three routes, no auth and no CORS: the runner binds to loopback and web-next is its only caller.
A POST validates its body (400, never FastAPI's 422), refuses while a round runs (409), and
otherwise starts the round on a daemon thread (202). A non-blocking `threading.Lock` is held for
the round's life and released in the thread's `finally`, so a round that raises can't leave the
API answering 409 for ever.
"""

from __future__ import annotations

import threading
from typing import Any, Literal, Protocol

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from rounds.scenarios import SCENARIOS, Scenario
from rounds.store import Store


class RunnerLike(Protocol):
    def new_round(
        self, scenario: Scenario, runs_per_arm: int, started_by: dict[str, Any]
    ) -> dict[str, Any]: ...
    def run_round(self, round_id: str) -> dict[str, Any]: ...


class StartedBy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["admin", "key"]
    name: str


class NewRound(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: str
    runs_per_arm: int = Field(ge=1, le=5)
    started_by: StartedBy


def _bad(detail: str) -> JSONResponse:
    return JSONResponse({"error": "bad_request", "detail": detail}, status_code=400)


def create_app(runner: RunnerLike, store: Store) -> FastAPI:
    app = FastAPI(title="Northstar proof rounds")
    lock = threading.Lock()

    @app.post("/lab/rounds", status_code=202)
    async def post_round(request: Request) -> JSONResponse:
        try:
            body = NewRound.model_validate_json(await request.body())
        except ValidationError as exc:
            first = exc.errors()[0]
            where = ".".join(str(p) for p in first["loc"]) or "body"
            return _bad(f"{where}: {first['msg']}"[:200])
        scenario = SCENARIOS.get(body.scenario)
        if scenario is None:
            return _bad("unknown scenario")
        if not lock.acquire(blocking=False):
            return JSONResponse({"error": "busy"}, status_code=409)
        try:
            rnd = runner.new_round(scenario, body.runs_per_arm, body.started_by.model_dump())
            round_id = str(rnd["round_id"])

            def work() -> None:
                try:
                    runner.run_round(round_id)
                except Exception:  # noqa: BLE001 - the runner records its own failures
                    pass
                finally:
                    lock.release()

            threading.Thread(target=work, daemon=True).start()
        except BaseException:
            lock.release()
            raise
        return JSONResponse({"round_id": round_id}, status_code=202)

    @app.get("/lab/rounds")
    def list_rounds() -> dict[str, Any]:
        return {"rounds": store.list_rounds()}

    @app.get("/lab/rounds/{round_id}", response_model=None)
    def get_round(round_id: str) -> Any:
        found = store.get_round(round_id)
        if found is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return found

    return app
