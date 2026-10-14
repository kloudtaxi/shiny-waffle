"""Read-only lab routes for the CRM tables and the clock, and the OWM_PORT setting (B-15 Task 1).

These run only with the `owm-service` dependency group; in the default group FastAPI isn't
installed and the module skips."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

import owm_service.__main__
from owm_service.app import create_app
from owm_service.config import Settings, load_settings

Headers = dict[str, str]


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return load_settings({"OWM_STATE_DIR": str(tmp_path / "state")})


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def sign_in(client: TestClient, **body: str) -> Headers:
    r = client.post("/lab/sessions", json=body)
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def sarah_tok(client: TestClient) -> Headers:
    return sign_in(client, person_id="EMP-101")


def test_get_sor_table_returns_rows_and_edits(client: TestClient, sarah_tok: Headers) -> None:
    r = client.get("/lab/sor/discount_requests")
    assert r.status_code == 200
    dr = next(x for x in r.json()["rows"] if x["request_id"] == "DR-9001")
    assert (dr["status"], dr["requested_discount_pct"]) == ("Pending Approval", "15.0")
    assert r.json()["edits"] == []
    client.patch(
        "/lab/sor/discount_requests/DR-9001", json={"status": "Approved"}, headers=sarah_tok
    )
    e = client.get("/lab/sor/discount_requests").json()["edits"]
    assert [(x["key"], x["field"], x["was"], x["now"]) for x in e] == [
        ("DR-9001", "status", "Pending Approval", "Approved")
    ]
    assert e[0]["kind"] == "sor.edited"
    assert e[0]["row"] is None
    assert e[0]["actor"]["person"]["id"] == "EMP-101"  # the actor as logged


def test_get_sor_insert_is_an_edit_entry(client: TestClient, sarah_tok: Headers) -> None:
    rows = client.get("/lab/sor/discount_requests").json()["rows"]
    row = {**rows[0], "request_id": "DR-9999"}
    r = client.post("/lab/sor/discount_requests", json=row, headers=sarah_tok)
    assert r.status_code == 201, r.text
    e = client.get("/lab/sor/discount_requests").json()["edits"]
    assert len(e) == 1
    assert (e[0]["kind"], e[0]["key"]) == ("sor.inserted", "DR-9999")
    assert (e[0]["field"], e[0]["was"], e[0]["now"]) == (None, None, None)
    assert e[0]["row"]["request_id"] == "DR-9999"


def test_get_sor_unknown_table_is_404(client: TestClient) -> None:
    assert client.get("/lab/sor/employees").status_code == 404


def test_get_sor_unkeyed_writable_table(client: TestClient, sarah_tok: Headers) -> None:
    r = client.get("/lab/sor/service_credits")
    assert r.status_code == 200
    assert r.json()["edits"] == []
    row = {**r.json()["rows"][0], "credit_id": "SCR-NEW"}
    assert client.post("/lab/sor/service_credits", json=row, headers=sarah_tok).status_code == 201
    e = client.get("/lab/sor/service_credits").json()["edits"]
    assert [(x["kind"], x["key"]) for x in e] == [("sor.inserted", None)]
    assert e[0]["row"] == row


def test_get_clock_is_demo_date(client: TestClient) -> None:
    body = client.get("/lab/clock").json()
    assert body["date"] == "2026-09-23"
    assert body["now"].startswith("2026-09-23")


def test_owm_port_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: dict[str, object] = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **kw: seen.update(kw))
    monkeypatch.setenv("OWM_PORT", "8123")
    monkeypatch.setenv("OWM_STATE_DIR", str(tmp_path))
    owm_service.__main__.main()
    assert seen["port"] == 8123


def test_owm_port_defaults_to_8000(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: dict[str, object] = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **kw: seen.update(kw))
    monkeypatch.delenv("OWM_PORT", raising=False)
    monkeypatch.setenv("OWM_STATE_DIR", str(tmp_path))
    owm_service.__main__.main()
    assert seen["port"] == 8000
