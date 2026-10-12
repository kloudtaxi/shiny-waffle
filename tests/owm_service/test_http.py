"""HTTP for slice 1 (B-06 Task 14; spec §11 and §6.8): the contract's routes under /api/v1, the
lab-only routes under /lab, and the status codes. Replay only.

These run only with the `owm-service` dependency group (`uv run --group owm-service pytest`); in
the default group FastAPI isn't installed and the module skips."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from owm_service import _lab
from owm_service.app import create_app
from owm_service.config import Settings, load_settings
from owm_service.decisions import Decisions

LAB = Path(__file__).resolve().parents[2]
EXAMPLE: dict[str, Any] = json.loads(
    (LAB / "lab/owm_service/contract/s22.example.json").read_text()
)
P15: dict[str, Any] = {"request_id": "DR-9001", "account_id": "CRM-2048", "product": "NS-500",
                       "discount": 0.15}  # fmt: skip
P8 = {**P15, "discount": 0.08}
Headers = dict[str, str]


# -- fixtures and helpers -----------------------------------------------------------------------
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
    """A demo session through POST /lab/sessions, as the Authorization header to send."""
    r = client.post("/lab/sessions", json=body)
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def sarah_tok(client: TestClient) -> Headers:
    return sign_in(client, person_id="EMP-101")


@pytest.fixture
def michael_tok(client: TestClient) -> Headers:
    return sign_in(client, person_id="EMP-200")


@pytest.fixture
def agent_tok(client: TestClient) -> Headers:
    return sign_in(client, agent_id="AGT-DEALDESK", on_behalf_of="EMP-101")


def ask_s22(client: TestClient, tok: Headers) -> dict[str, Any]:
    r = client.post("/api/v1/decisions", json=EXAMPLE["ask"], headers=tok)
    assert r.status_code == 201, r.text
    out: dict[str, Any] = r.json()
    return out


def clearance(did: str, version: int, params: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {"decision_id": did, "decision_version": version, "action": "apply_discount",
            "params": params, **extra}  # fmt: skip


def codes(body: dict[str, Any]) -> list[str]:
    return [r["code"] for r in body["reasons"]]


def ready_s22(client: TestClient, agent: Headers, sarah: Headers, michael: Headers) -> str:
    """S22's main branch over HTTP to version 2, ready; the decision's id."""
    did = str(ask_s22(client, agent)["decision_id"])
    r = client.post(f"/api/v1/decisions/{did}/conditions/c1/resolve", headers=sarah,
                    json={"decision_version": 1, "resolution": "confirmed_record"})  # fmt: skip
    assert r.status_code == 200, r.text
    r = client.post(f"/api/v1/decisions/{did}/approve", json={"decision_version": 2},
                    headers=michael)  # fmt: skip
    assert r.status_code == 200 and r.json()["state"] == "ready", r.text
    return did


def clear15(client: TestClient, tok: Headers, did: str) -> str:
    r = client.post(f"/api/v1/decisions/{did}/clearance", json=clearance(did, 2, P15), headers=tok)
    assert r.status_code == 200 and r.json()["cleared"] is True, r.text
    return str(r.json()["clearance_id"])


# -- health, sessions, 401 ----------------------------------------------------------------------
def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "hdr",
    [{}, {"Authorization": "Bearer nope"}, {"Authorization": "Bearer "},
     {"Authorization": "Basic c2FyYWg6c2VjcmV0"}, {"Authorization": "nope"}],
)  # fmt: skip
def test_401_without_a_valid_token(client: TestClient, hdr: Headers) -> None:
    """Review Focus 5: a missing, unknown or malformed token is 401, never a default user."""
    r = client.get("/api/v1/me", headers=hdr)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json()["error"] == "unauthenticated"


def test_every_contract_route_needs_a_session(client: TestClient) -> None:
    for method, path in [
        ("get", "/api/v1/decisions"), ("get", "/api/v1/decisions/DEC-0001"),
        ("get", "/api/v1/approvals"), ("post", "/api/v1/clearances/CLR-00001/redeem"),
        ("post", "/api/v1/clearances/CLR-00001/report"),
    ]:  # fmt: skip
        assert client.request(method, path, json={}).status_code == 401, path


def test_me_is_the_session_actor(
    client: TestClient, sarah_tok: Headers, agent_tok: Headers
) -> None:
    me = client.get("/api/v1/me", headers=sarah_tok).json()
    assert me == {"actor": {"kind": "person", "person": {
        "id": "EMP-101", "name": "Sarah Chen", "title": "Enterprise Account Executive",
        "function": "Sales"}}}  # fmt: skip
    agent = client.get("/api/v1/me", headers=agent_tok).json()["actor"]
    assert (agent["kind"], agent["id"], agent["on_behalf_of"]["id"]) == (
        "agent", "AGT-DEALDESK", "EMP-101")  # fmt: skip
    assert agent["mandate"] == {"doc_id": "MANDATE-DEALDESK-2026"}


def test_signed_out_and_expired_sessions_are_401(client: TestClient, sarah_tok: Headers) -> None:
    assert client.get("/api/v1/me", headers=sarah_tok).status_code == 200
    assert client.delete("/lab/sessions/current", headers=sarah_tok).status_code == 204
    assert client.get("/api/v1/me", headers=sarah_tok).status_code == 401
    assert client.delete("/lab/sessions/current", headers=sarah_tok).status_code == 401
    later = sign_in(client, person_id="EMP-200")
    r = client.post("/lab/clock", json={"to": "2026-09-23T22:00:00-05:00"})
    assert r.status_code == 200, r.text
    assert client.get("/api/v1/me", headers=later).status_code == 401  # 12 h of demo time


def test_sign_in_as_nobody_is_404_and_an_odd_body_is_422(client: TestClient) -> None:
    assert client.post("/lab/sessions", json={"person_id": "EMP-999"}).status_code == 404
    assert client.post("/lab/sessions", json={"person_id": "EMP-101", "x": 1}).status_code == 422
    assert client.post("/lab/sessions", json={}).status_code == 422


# -- S22 end to end -----------------------------------------------------------------------------
def test_s22_over_http_end_to_end(
    client: TestClient, app: FastAPI, agent_tok: Headers, sarah_tok: Headers, michael_tok: Headers
) -> None:
    """Spec §6.9's main branch: the agent asks at 8%, is refused, Sarah confirms the CRM's 15%,
    Michael approves, the agent clears 15%, the adapter redeems and reports; the decision is
    spent and its history reads in order."""
    v1 = ask_s22(client, agent_tok)
    did = v1["decision_id"]
    assert (v1["version"], v1["state"], v1["gated_outcome"]) == (
        1, "not_ready", "APPROVE_WITH_AUTHORIZATION")  # fmt: skip
    assert "ticket" not in v1["subject"]  # R13: an absent `?:` field stays absent
    # Michael's queue holds the approval, held by Sarah's c1
    q = client.get("/api/v1/approvals", headers=michael_tok)
    assert q.status_code == 200
    (item,) = q.json()["waiting_on_you"]
    assert item["kind"] == "decision_approval" and item["raised_by"]["kind"] == "agent"
    assert [h["condition_id"] for h in item["held_by"]] == ["c1"]
    sarahs = client.get("/api/v1/approvals", headers=sarah_tok).json()
    assert [i["kind"] for i in sarahs["waiting_on_you"]] == ["condition"]
    # 8% on version 1: refused, every failing check in order (200: a refusal is an answer)
    r = client.post(f"/api/v1/decisions/{did}/clearance", json=clearance(did, 1, P8),
                    headers=agent_tok)  # fmt: skip
    assert r.status_code == 200
    refused = r.json()
    assert refused["cleared"] is False
    assert codes(refused) == [x["code"] for x in EXAMPLE["refused8"]["reasons"]]
    assert refused["reasons"][0] == EXAMPLE["refused8"]["reasons"][0]  # differs, as the example
    assert refused["reasons"][2] == EXAMPLE["refused8"]["reasons"][2]  # awaiting_approval
    assert "condition_id" not in refused["reasons"][2]  # R13: an absent `?:` stays absent
    # Sarah confirms; Michael approves version 2
    r = client.post(f"/api/v1/decisions/{did}/conditions/c1/resolve", headers=sarah_tok,
                    json={"decision_version": 1, "resolution": "confirmed_record"})  # fmt: skip
    assert r.status_code == 200 and (r.json()["version"], r.json()["state"]) == (
        2, "awaiting_approval")  # fmt: skip
    r = client.post(f"/api/v1/decisions/{did}/approve", json={"decision_version": 2},
                    headers=michael_tok)  # fmt: skip
    assert r.status_code == 200 and r.json()["state"] == "ready"
    mine = client.get("/api/v1/approvals", headers=michael_tok).json()
    assert mine["waiting_on_you"] == [] and [d["result"] for d in mine["done"]] == ["approved"]
    # 15% on version 2: cleared, bound to the version, params and the agent
    r = client.post(f"/api/v1/decisions/{did}/clearance", json=clearance(did, 2, P15),
                    headers=agent_tok)  # fmt: skip
    ok = r.json()
    assert r.status_code == 200 and ok["cleared"] is True and ok["single_use"] is True
    assert ok["bound"]["decision_version"] == 2 and ok["bound"]["params"] == P15
    assert ok["bound"]["actor"]["id"] == "AGT-DEALDESK"
    # the demo adapter redeems, writes the CRM and reports
    r = client.post("/lab/adapter/execute", json={"clearance_id": ok["clearance_id"]},
                    headers=agent_tok)  # fmt: skip
    assert r.status_code == 200, r.text
    assert (r.json()["redeemed"], r.json()["report"]) == (True, "applied")
    rec = client.get(f"/api/v1/decisions/{did}", headers=sarah_tok).json()
    assert rec["state"] == "spent"
    assert [(x["clearance_id"], x["report"]) for x in rec["executed"]] == [
        (ok["clearance_id"], "applied")]  # fmt: skip
    row = app.state.owm.org.sor.row("discount_requests", "DR-9001")
    assert (row["status"], row["approved_by"]) == ("Approved", "michael.torres@northstar.example")
    # reads: a version, the list, the attempts and the history
    r1 = client.get(f"/api/v1/decisions/{did}/versions/1", headers=sarah_tok).json()
    assert (r1["version"], r1["state"]) == (1, "spent")
    listed = client.get("/api/v1/decisions", params={"subject": "DR-9001"}, headers=sarah_tok)
    assert [d["decision_id"] for d in listed.json()] == [did]
    assert client.get("/api/v1/decisions", params={"state": "ready"},
                      headers=sarah_tok).json() == []  # fmt: skip
    attempts = client.get(f"/api/v1/decisions/{did}/clearances", headers=sarah_tok).json()
    assert [a["response"]["cleared"] for a in attempts] == [False, True]
    assert "dry_run" not in attempts[0]["request"]  # R13
    events = client.get(f"/api/v1/decisions/{did}/events", headers=sarah_tok).json()
    assert [e["kind"] for e in events] == [
        "requested",
        "decided",
        "clearance_refused",
        "condition_resolved",
        "decided",
        "approved",
        "clearance_cleared",
        "clearance_redeemed",
        "execution_reported",
    ]


def test_s22_crm_edit_is_ratcheted_over_http(
    client: TestClient, agent_tok: Headers, sarah_tok: Headers, michael_tok: Headers
) -> None:
    """Spec §6.9's other branch (G-46): Sarah edits the CRM to 8% and corrects c1; version 2 is
    APPROVE but below the floor, so a ratchet condition waits on Michael and clearance stays
    shut."""
    did = ask_s22(client, agent_tok)["decision_id"]
    r = client.patch("/lab/sor/discount_requests/DR-9001", json={"requested_discount_pct": "8.0"},
                     headers=sarah_tok)  # fmt: skip
    assert r.status_code == 200 and r.json()["row"]["requested_discount_pct"] == "8.0"
    r = client.post(f"/api/v1/decisions/{did}/conditions/c1/resolve", headers=sarah_tok,
                    json={"decision_version": 1, "resolution": "corrected_record"})  # fmt: skip
    v2 = r.json()
    assert (v2["version"], v2["gated_outcome"], v2["state"]) == (2, "APPROVE", "not_ready")
    assert {"self_sourced_basis", "ratchet"} <= {f["code"] for f in v2["flags"]}
    ratchet = v2["conditions"][-1]
    assert (ratchet["source"], [p["id"] for p in ratchet["who"]]) == ("ratchet", ["EMP-200"])
    (item,) = client.get("/api/v1/approvals", headers=michael_tok).json()["waiting_on_you"]
    assert (item["kind"], item["id"]) == ("condition", f"{did}:{ratchet['id']}")
    r = client.post(f"/api/v1/decisions/{did}/clearance", json=clearance(did, 2, P8),
                    headers=agent_tok)  # fmt: skip
    assert codes(r.json()) == ["condition_open"]
    assert r.json()["reasons"][0]["waiting_on"][0]["id"] == "EMP-200"


# -- status codes ---------------------------------------------------------------------------------
def test_rr1_body_actor_differs_is_403(
    client: TestClient, sarah_tok: Headers, agent_tok: Headers, michael_tok: Headers
) -> None:
    """A body principal that differs from the session's is 403 RR-1 (spec §6.8)."""
    did = ask_s22(client, agent_tok)["decision_id"]
    michael = client.get("/api/v1/me", headers=michael_tok).json()["actor"]
    body = clearance(did, 1, P15, actor=michael)
    r = client.post(f"/api/v1/decisions/{did}/clearance", json=body, headers=sarah_tok)
    assert r.status_code == 403
    assert [x["rule"] for x in r.json()["refusals"]] == ["RR-1"]
    assert set(r.json()["refusals"][0]) == {"rule", "detail"}  # R13: no null extras


def test_as_of_in_body_is_422(client: TestClient, sarah_tok: Headers) -> None:
    """An extra body field, such as S23's `as_of`, is refused with FastAPI's default 422 body."""
    body = {**EXAMPLE["ask"], "as_of": "2026-09-01"}
    r = client.post("/api/v1/decisions", json=body, headers=sarah_tok)
    assert r.status_code == 422
    (err,) = r.json()["detail"]
    assert (err["type"], err["loc"]) == ("extra_forbidden", ["body", "as_of"])
    assert client.get("/api/v1/decisions", headers=sarah_tok).json() == []


def test_dc6_second_decision_is_409_with_the_example_body(
    client: TestClient, sarah_tok: Headers, agent_tok: Headers
) -> None:
    did = ask_s22(client, agent_tok)["decision_id"]
    r = client.post("/api/v1/decisions", json=EXAMPLE["ask"], headers=sarah_tok)
    assert r.status_code == 409
    want = json.loads(json.dumps(EXAMPLE["secondDecision"]).replace("DEC-0418", did))
    assert r.json() == want


def test_dc5_stale_version_is_409_and_other_rules_422(
    client: TestClient, sarah_tok: Headers, agent_tok: Headers, michael_tok: Headers
) -> None:
    did = ask_s22(client, agent_tok)["decision_id"]
    r = client.post(f"/api/v1/decisions/{did}/approve", json={"decision_version": 3},
                    headers=michael_tok)  # fmt: skip
    assert r.status_code == 409 and r.json()["refusals"][0]["rule"] == "DC-5"
    r = client.post(f"/api/v1/decisions/{did}/approve", json={"decision_version": 1},
                    headers=michael_tok)  # fmt: skip
    assert r.status_code == 422 and [x["rule"] for x in r.json()["refusals"]] == ["DC-4"]
    r = client.post(f"/api/v1/decisions/{did}/approve", json={"decision_version": 1},
                    headers=agent_tok)  # fmt: skip
    assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "DC-1"
    body = clearance("DEC-9999", 1, P15)
    r = client.post(f"/api/v1/decisions/{did}/clearance", json=body, headers=agent_tok)
    assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "DC-2"
    bad = client.get("/api/v1/decisions", params={"state": "bogus"}, headers=sarah_tok)
    assert bad.status_code == 422
    assert client.get(f"/api/v1/decisions/{did}/versions/x", headers=sarah_tok).status_code == 422


def test_rerun_decline_and_withdraw_over_http(
    client: TestClient, sarah_tok: Headers, agent_tok: Headers, michael_tok: Headers
) -> None:
    did = ask_s22(client, agent_tok)["decision_id"]
    r = client.post(f"/api/v1/decisions/{did}/rerun", json={"decision_version": 1},
                    headers=sarah_tok)  # fmt: skip
    assert r.status_code == 200 and (r.json()["version"], r.json()["state"]) == (2, "not_ready")
    r = client.post(f"/api/v1/decisions/{did}/decline", json={"decision_version": 2},
                    headers=michael_tok)  # fmt: skip
    assert r.status_code == 422 and "note" in r.json()["refusals"][0]["detail"]
    r = client.post(f"/api/v1/decisions/{did}/decline", headers=michael_tok,
                    json={"decision_version": 2, "note": "Not at 15% this quarter."})  # fmt: skip
    assert r.status_code == 200 and r.json()["state"] == "declined"
    (done,) = client.get("/api/v1/approvals", headers=michael_tok).json()["done"]
    assert (done["kind"], done["result"]) == ("decision_approval", "declined")
    again = ask_s22(client, agent_tok)["decision_id"]  # the subject is free again
    r = client.post(f"/api/v1/decisions/{again}/withdraw", json={"decision_version": 1},
                    headers=sarah_tok)  # fmt: skip
    assert r.status_code == 200 and r.json()["state"] == "withdrawn"
    kinds = [e["kind"] for e in client.get(f"/api/v1/decisions/{did}/events",
                                           headers=sarah_tok).json()]  # fmt: skip
    assert kinds == ["requested", "decided", "rerun", "decided", "declined"]


def test_404s(client: TestClient, sarah_tok: Headers) -> None:
    r = client.get("/api/v1/decisions/DEC-9999", headers=sarah_tok)
    assert r.status_code == 404 and r.json() == {"error": "not_found",
                                                 "detail": "decision DEC-9999"}  # fmt: skip
    for path in ["/api/v1/decisions/DEC-9999/events", "/api/v1/decisions/DEC-9999/clearances",
                 "/api/v1/decisions/DEC-9999/versions/1"]:  # fmt: skip
        assert client.get(path, headers=sarah_tok).status_code == 404, path
    body = {"params": {}, "executor": {"system": "crm", "adapter": "x"}}
    r = client.post("/api/v1/clearances/CLR-99999/redeem", json=body, headers=sarah_tok)
    assert r.status_code == 404
    r = client.post("/lab/adapter/execute", json={"clearance_id": "CLR-99999"}, headers=sarah_tok)
    assert r.status_code == 404
    r = client.post("/api/v1/decisions", json={"decision_type": "discount",
                    "subject": {"request_id": "DR-0000"}}, headers=sarah_tok)  # fmt: skip
    assert r.status_code == 404  # Review Focus 1


def test_503_body(client: TestClient, app: FastAPI, sarah_tok: Headers) -> None:
    """Review Focus 3 over HTTP: a row whose requester isn't in the HR export can't be decided:
    503 with the cannot_decide body, and nothing versioned."""
    row = dict(app.state.owm.org.sor.row("discount_requests", "DR-9001"))
    row |= {"request_id": "DR-9199", "requested_by": "nobody@northstar.example"}
    r = client.post("/lab/sor/discount_requests", json=row, headers=sarah_tok)
    assert r.status_code == 201, r.text
    r = client.post("/api/v1/decisions", headers=sarah_tok, json={
        "decision_type": "discount", "subject": {"request_id": "DR-9199"}})  # fmt: skip
    assert r.status_code == 503
    body = r.json()
    assert set(body) == {"error", "detail"} and body["error"] == "cannot_decide"
    assert isinstance(body["detail"], str) and body["detail"]
    assert client.get("/api/v1/decisions", headers=sarah_tok).json() == []


def test_jev_unavailable_is_503(
    client: TestClient, sarah_tok: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    def miss(self: Decisions, **filters: str) -> list[Any]:
        raise _lab.JevUnavailable("not recorded: abc")

    monkeypatch.setattr(Decisions, "list", miss)
    r = client.get("/api/v1/decisions", headers=sarah_tok)
    assert r.status_code == 503
    assert r.json() == {"error": "cannot_decide", "detail": "not recorded: abc"}


def test_an_unexpected_error_is_not_hidden(
    app: FastAPI, sarah_tok: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    """There is no catch-all: a bug surfaces as a 500 (and raises under the test client)."""

    def boom(self: Decisions, **filters: str) -> list[Any]:
        raise RuntimeError("a bug")

    monkeypatch.setattr(Decisions, "list", boom)
    with pytest.raises(RuntimeError, match="a bug"):
        TestClient(app).get("/api/v1/decisions", headers=sarah_tok)
    r = TestClient(app, raise_server_exceptions=False).get("/api/v1/decisions", headers=sarah_tok)
    assert r.status_code == 500


def test_dry_run_that_would_clear_is_passed_through(
    client: TestClient, agent_tok: Headers, sarah_tok: Headers, michael_tok: Headers
) -> None:
    """Ruling R34: a dry run nothing stops answers `{cleared: false, reasons: []}`."""
    did = ready_s22(client, agent_tok, sarah_tok, michael_tok)
    r = client.post(f"/api/v1/decisions/{did}/clearance",
                    json=clearance(did, 2, P15, dry_run=True), headers=agent_tok)  # fmt: skip
    assert r.status_code == 200 and r.json() == {"cleared": False, "reasons": []}


# -- redeem and report over HTTP (R35) ------------------------------------------------------------
def test_redeem_and_report_need_a_session_and_record_it(
    client: TestClient, app: FastAPI, agent_tok: Headers, sarah_tok: Headers, michael_tok: Headers
) -> None:
    did = ready_s22(client, agent_tok, sarah_tok, michael_tok)
    cid = clear15(client, agent_tok, did)
    body = {"params": P15, "executor": {"system": "crm", "adapter": "web-next"}}
    assert client.post(f"/api/v1/clearances/{cid}/redeem", json=body).status_code == 401
    r = client.post(f"/api/v1/clearances/{cid}/redeem", json=body, headers=michael_tok)
    assert r.status_code == 200 and r.json()["redeemed"] is True and set(r.json()) == {
        "redeemed", "at"}  # fmt: skip
    again = client.post(f"/api/v1/clearances/{cid}/redeem", json=body, headers=michael_tok)
    assert again.status_code == 200 and codes(again.json()) == ["used"]
    rep = {"status": "failed", "external_ref": None, "detail": "CRM rejected the write"}
    assert client.post(f"/api/v1/clearances/{cid}/report", json=rep).status_code == 401
    r = client.post(f"/api/v1/clearances/{cid}/report", json=rep, headers=michael_tok)
    assert r.status_code == 200 and r.json() == {"incident_id": "INC-0001"}
    org = app.state.owm.org
    michael = client.get("/api/v1/me", headers=michael_tok).json()["actor"]
    kinds = ("clearance.redeemed", "redeem.refused", "execution.reported", "incident.opened")
    evs = org.log.read(org.org_id, kinds=kinds)
    assert len(evs) == 4 and all(e.payload["by"] == michael for e in evs)


# -- lab routes ---------------------------------------------------------------------------------
def test_lab_routes_absent_when_disabled(tmp_path: Path) -> None:
    s = load_settings({"OWM_STATE_DIR": str(tmp_path / "state"), "OWM_LAB_ROUTES": "0"})
    app = create_app(s)
    client = TestClient(app)
    assert client.post("/lab/sessions", json={"person_id": "EMP-101"}).status_code == 404
    assert client.post("/lab/reset").status_code == 404
    assert client.get("/healthz").status_code == 200
    assert client.get("/api/v1/me").status_code == 401
    paths = set(client.get("/openapi.json").json()["paths"])
    assert "/api/v1/me" in paths and not any(p.startswith("/lab") for p in paths)
    on = TestClient(create_app(load_settings({"OWM_STATE_DIR": str(tmp_path / "on")})))
    assert "/lab/sessions" in on.get("/openapi.json").json()["paths"]


def test_sor_edits_are_checked_and_attributed(
    client: TestClient, app: FastAPI, sarah_tok: Headers
) -> None:
    """Review Focus 2 over HTTP: a malformed value is 422 at PATCH /lab/sor, before any kernel."""
    url = "/lab/sor/discount_requests/DR-9001"
    for bad in [{"requested_discount_pct": "abc"}, {"request_date": "23/09/2026"},
                {"requested_discount_pct": 8.0}, {"nope": "1"}, {}]:  # fmt: skip
        r = client.patch(url, json=bad, headers=sarah_tok)
        assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "RR-5", bad
    assert client.patch(url, json={"status": "Draft"}).status_code == 401
    assert client.patch("/lab/sor/discount_requests/DR-0000", json={"status": "x"},
                        headers=sarah_tok).status_code == 404  # fmt: skip
    assert client.patch("/lab/sor/no_such_table/X", json={"status": "x"},
                        headers=sarah_tok).status_code == 404  # fmt: skip
    r = client.patch(url, json={"status": "Draft"}, headers=sarah_tok)
    assert r.status_code == 200 and r.json()["row"]["status"] == "Draft"
    org = app.state.owm.org
    (e,) = org.sor.edits("discount_requests", "DR-9001")
    me = client.get("/api/v1/me", headers=sarah_tok).json()["actor"]
    assert (e.payload["field"], e.payload["now"], e.actor) == ("status", "Draft", me)
    dup = dict(org.sor.row("discount_requests", "DR-9001"))
    assert client.post("/lab/sor/discount_requests", json=dup,
                       headers=sarah_tok).status_code == 409  # fmt: skip


def test_sor_writes_outside_the_request_tables_are_refused(
    client: TestClient, app: FastAPI, sarah_tok: Headers, agent_tok: Headers
) -> None:
    """Ruling R60 over HTTP, the final review's probe: Sarah can't insert HR rows that make a rep
    the VP Sales, nor edit an account's tier; nothing is logged, and DR-9001's approval still
    waits on Michael Torres."""
    base = {"preferred_name": "", "department": "Sales", "location": "Chicago, IL"}
    rows = [
        {**base, "employee_id": "EMP-200", "full_name": "Michael Torres", "manager_id": "EMP-500",
         "title": "Enterprise Account Executive", "email": "michael.torres@northstar.example"},
        {**base, "employee_id": "EMP-500", "full_name": "Kelly Floyd", "manager_id": "EMP-300",
         "title": "VP Sales", "email": "kelly.floyd@northstar.example"},
    ]  # fmt: skip
    for row in rows:
        r = client.post("/lab/sor/employees", json=row, headers=sarah_tok)
        assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "RR-5", r.text
    for url, fields in [("/lab/sor/crm_accounts/CRM-2048", {"account_tier": "Commercial"}),
                        ("/lab/sor/employees/EMP-500", {"title": "VP Sales"})]:  # fmt: skip
        r = client.patch(url, json=fields, headers=sarah_tok)
        assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "RR-5", url
    org = app.state.owm.org
    assert org.log.read(org.org_id, stream="sor") == []
    (approval,) = ask_s22(client, agent_tok)["approvals"]
    assert (approval["role"], approval["person"]["id"]) == ("VP Sales", "EMP-200")


def test_clock_moves_forward_only(client: TestClient) -> None:
    r = client.post("/lab/clock", json={"to": "2026-09-24T09:00:00-05:00"})
    assert r.status_code == 200 and r.json()["now"].startswith("2026-09-24T09:00")
    for bad in [{"to": "2026-09-23T09:00:00-05:00"}, {"to": "2026-09-25T09:00:00"},
                {"to": "tomorrow"}, {"to": "2026-09-25T09:00:00-05:00", "x": 1}]:  # fmt: skip
        assert client.post("/lab/clock", json=bad).status_code == 422, bad


def test_reset_archives_the_log_and_starts_afresh(
    client: TestClient, settings: Settings, sarah_tok: Headers, agent_tok: Headers
) -> None:
    did = ask_s22(client, agent_tok)["decision_id"]
    assert did == "DEC-0001"
    r = client.post("/lab/reset")
    assert r.status_code == 200
    archived = settings.state_dir / "northstar" / r.json()["archived"]
    assert archived.is_file() and archived.name.startswith("events-")
    assert client.get("/api/v1/me", headers=sarah_tok).status_code == 401  # sessions went too
    fresh = sign_in(client, agent_id="AGT-DEALDESK", on_behalf_of="EMP-101")
    assert client.get("/api/v1/decisions", headers=fresh).json() == []
    assert ask_s22(client, fresh)["decision_id"] == "DEC-0001"


def test_main_runs_uvicorn_on_port_8000(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`python -m owm_service`: uvicorn on 0.0.0.0:8000 with the environment's settings."""
    import uvicorn

    seen: dict[str, Any] = {}

    def fake_run(app: Any, **kw: Any) -> None:
        seen.update(app=app, **kw)

    monkeypatch.setattr(uvicorn, "run", fake_run)
    monkeypatch.setenv("OWM_STATE_DIR", str(tmp_path / "state"))
    importlib.import_module("owm_service.__main__").main()
    assert (seen["host"], seen["port"]) == ("0.0.0.0", 8000)
    assert isinstance(seen["app"], FastAPI)
    assert seen["app"].state.owm.settings.state_dir == tmp_path / "state"
