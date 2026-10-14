"""The `/lab/rounds` and `/lab/finishes` HTTP API that web-next's `/present` page calls,
server-side only (spec §7; finishes are B-19 spec §3).

Three round routes, and four finish routes when a `Finishes` is given; no auth and no CORS: the
runner binds to loopback and web-next is its only caller.
A POST must be `application/json` (else 415): a web page in the operator's browser can send a
text/plain POST to 127.0.0.1 without a CORS preflight, and must not start a paid round. It
validates its body (400, never FastAPI's 422), refuses while a round runs (409), and
otherwise starts the round on a daemon thread (202). A non-blocking `threading.Lock` is held for
the round's life and released in the thread's `finally`, so a round that raises can't leave the
API answering 409 for ever. A finish's turns take the same lock: a round and a finish never run
together, since both spend on the agent.
"""

from __future__ import annotations

import threading
from typing import Any, Literal, Protocol

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from rounds.finish import NotWaiting, check_service_url
from rounds.scenarios import SCENARIOS, Scenario
from rounds.store import Store


class RunnerLike(Protocol):
    def new_round(
        self, scenario: Scenario, runs_per_arm: int, started_by: dict[str, Any]
    ) -> dict[str, Any]: ...
    def run_round(self, round_id: str) -> dict[str, Any]: ...


class FinishesLike(Protocol):
    def new_finish(
        self, scenario: Scenario, service_url: str, started_by: dict[str, Any]
    ) -> dict[str, Any]: ...
    def start_retry(self, finish_id: str, started_by: dict[str, Any]) -> dict[str, Any]: ...
    def run_turn(self, finish_id: str, turn: Literal["first", "retry"]) -> dict[str, Any]: ...


class StartedBy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["admin", "key"]
    name: str


class NewRound(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: str
    runs_per_arm: int = Field(ge=1, le=5)
    started_by: StartedBy


class NewFinish(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: str
    service_url: str
    started_by: StartedBy


class RetryBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    started_by: StartedBy


def _bad(detail: str) -> JSONResponse:
    return JSONResponse({"error": "bad_request", "detail": detail}, status_code=400)


def _is_json(request: Request) -> bool:
    media = request.headers.get("content-type", "").split(";")[0].strip().lower()
    return media == "application/json"


def _invalid(exc: ValidationError) -> JSONResponse:
    first = exc.errors()[0]
    where = ".".join(str(p) for p in first["loc"]) or "body"
    return _bad(f"{where}: {first['msg']}"[:200])


def create_app(
    runner: RunnerLike,
    store: Store,
    finishes: FinishesLike | None = None,
    rounds_port: int = 8001,
) -> FastAPI:
    app = FastAPI(title="Northstar proof rounds")
    lock = threading.Lock()

    @app.post("/lab/rounds", status_code=202)
    async def post_round(request: Request) -> JSONResponse:
        if not _is_json(request):
            return JSONResponse({"error": "unsupported_media_type"}, status_code=415)
        try:
            body = NewRound.model_validate_json(await request.body())
        except ValidationError as exc:
            return _invalid(exc)
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
                except (Exception, SystemExit):  # noqa: BLE001 - the runner records its failures
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

    if finishes is None:
        return app
    fin = finishes

    def start_turn(finish_id: str, turn: Literal["first", "retry"]) -> None:
        """Run a turn on a daemon thread that frees the held lock however the turn ends."""

        def work() -> None:
            try:
                fin.run_turn(finish_id, turn)
            except (Exception, SystemExit):  # noqa: BLE001 - the finish records its failures
                pass
            finally:
                lock.release()

        threading.Thread(target=work, daemon=True).start()

    @app.post("/lab/finishes", status_code=202)
    async def post_finish(request: Request) -> JSONResponse:
        if not _is_json(request):
            return JSONResponse({"error": "unsupported_media_type"}, status_code=415)
        try:
            body = NewFinish.model_validate_json(await request.body())
        except ValidationError as exc:
            return _invalid(exc)
        scenario = SCENARIOS.get(body.scenario)
        if scenario is None:
            return _bad("unknown scenario")
        try:
            url = check_service_url(body.service_url, rounds_port)
        except ValueError as exc:
            return _bad(str(exc))
        if not lock.acquire(blocking=False):
            return JSONResponse({"error": "busy"}, status_code=409)
        try:
            made = fin.new_finish(scenario, url, body.started_by.model_dump())
            finish_id = str(made["finish_id"])
            start_turn(finish_id, "first")
        except BaseException:
            lock.release()
            raise
        return JSONResponse({"finish_id": finish_id}, status_code=202)

    @app.post("/lab/finishes/{finish_id}/retry", status_code=202)
    async def post_retry(finish_id: str, request: Request) -> JSONResponse:
        if not _is_json(request):
            return JSONResponse({"error": "unsupported_media_type"}, status_code=415)
        try:
            body = RetryBody.model_validate_json(await request.body())
        except ValidationError as exc:
            return _invalid(exc)
        if not lock.acquire(blocking=False):
            return JSONResponse({"error": "busy"}, status_code=409)
        try:
            fin.start_retry(finish_id, body.started_by.model_dump())
            start_turn(finish_id, "retry")
        except KeyError:
            lock.release()
            return JSONResponse({"error": "not_found"}, status_code=404)
        except NotWaiting:
            lock.release()
            return JSONResponse({"error": "not_waiting"}, status_code=409)
        except BaseException:
            lock.release()
            raise
        return JSONResponse({"finish_id": finish_id}, status_code=202)

    @app.get("/lab/finishes")
    def list_finishes() -> dict[str, Any]:
        return {"finishes": store.list_finishes()}

    @app.get("/lab/finishes/{finish_id}", response_model=None)
    def get_finish(finish_id: str) -> Any:
        found = store.get_finish(finish_id)
        if found is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return found

    return app
