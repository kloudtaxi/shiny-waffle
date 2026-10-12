"""HTTP for slice 2 (B-06 Task 19; spec §11 and §7): the register and procedure routes, and the
`register_change` and `register_draft` work items in `GET /approvals`. Replay only.

These run only with the `owm-service` dependency group; in the default group FastAPI isn't
installed and the module skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from owm_service.app import create_app
from owm_service.changes import ChangeBody
from owm_service.config import load_settings

from .test_procedures import procedure
from .test_register_queue import credit, edge, mandate, revoke_brl

Headers = dict[str, str]


# -- fixtures and helpers -----------------------------------------------------------------------
@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(load_settings({"OWM_STATE_DIR": str(tmp_path / "state")})))


def tok(client: TestClient, **body: str) -> Headers:
    r = client.post("/lab/sessions", json=body)
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def person(client: TestClient, emp: str) -> Headers:
    return tok(client, person_id=emp)


@pytest.fixture
def agent(client: TestClient) -> Headers:
    return tok(client, agent_id="AGT-DEALDESK", on_behalf_of="EMP-101")


def payload(b: ChangeBody, **over: Any) -> dict[str, Any]:
    """A change as the contract's request: what was set, plus the nullable `effective_to`."""
    raw = b.model_dump(mode="json", exclude_unset=True)
    if raw["action"] == "register" and raw.get("kind") != "procedure":
        raw.setdefault("effective_to", None)
        raw.setdefault("relations", [])
        raw.setdefault("title", str(raw["doc_id"]))
    return raw | over


def post(client: TestClient, h: Headers, b: ChangeBody, **over: Any) -> dict[str, Any]:
    r = client.post("/api/v1/register/changes", json=payload(b, **over), headers=h)
    assert r.status_code == 201, r.text
    out: dict[str, Any] = r.json()
    return out


def items(client: TestClient, h: Headers, bucket: str) -> list[dict[str, Any]]:
    r = client.get("/api/v1/approvals", headers=h)
    assert r.status_code == 200, r.text
    out: list[dict[str, Any]] = r.json()[bucket]
    return out


def of_kind(rows: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [i for i in rows if i["kind"] == kind]


# -- reads --------------------------------------------------------------------------------------
def test_register_routes_need_a_session(client: TestClient) -> None:
    for method, path in [
        ("get", "/api/v1/register"), ("get", "/api/v1/register/entries/X"),
        ("get", "/api/v1/register/entries/X/text"), ("get", "/api/v1/register/settings"),
        ("put", "/api/v1/register/settings"), ("post", "/api/v1/register/changes"),
        ("get", "/api/v1/register/changes"), ("get", "/api/v1/register/changes/CHG-0001"),
        ("post", "/api/v1/register/changes/CHG-0001/submit"),
        ("post", "/api/v1/register/changes/CHG-0001/approve"),
        ("post", "/api/v1/register/changes/CHG-0001/decline"),
        ("post", "/api/v1/register/changes/CHG-0001/withdraw"),
        ("post", "/api/v1/register/changes/CHG-0001/remind"),
        ("get", "/api/v1/procedures"), ("get", "/api/v1/procedures/PROC-SLA"),
    ]:  # fmt: skip
        assert getattr(client, method)(path).status_code == 401, (method, path)


def test_register_view_entry_and_text(client: TestClient) -> None:
    h = person(client, "EMP-101")
    view = client.get("/api/v1/register", headers=h).json()
    assert view["version"] == 17 and view["settings"] == {"on_mismatch": "use_registered"}
    doc = view["entries"][0]["doc_id"]
    assert client.get(f"/api/v1/register/entries/{doc}", headers=h).json()["doc_id"] == doc
    assert client.get("/api/v1/register/entries/NOPE", headers=h).status_code == 404
    assert client.get("/api/v1/register/entries/NOPE/text", headers=h).status_code == 404
    early = client.get("/api/v1/register", params={"as_of": "2020-01-01"}, headers=h)
    assert early.status_code == 200
    assert {e["status"] for e in early.json()["entries"]} <= {"scheduled", "in_force"}
    bad = client.get("/api/v1/register", params={"as_of": "not-a-date"}, headers=h)
    assert bad.status_code == 422


def test_text_is_the_approved_text_byte_for_byte(client: TestClient) -> None:
    priya, elena = person(client, "EMP-401"), person(client, "EMP-402")
    b = credit()
    made = post(client, priya, b)
    r = client.post(f"/api/v1/register/changes/{made['change_id']}/approve", headers=elena)
    assert r.status_code == 200 and r.json()["state"] == "approved", r.text
    t = client.get(f"/api/v1/register/entries/{b.doc_id}/text", headers=priya)
    assert t.status_code == 200 and t.headers["content-type"] == "text/plain; charset=utf-8"
    assert t.content == (b.text or "").encode()


def test_text_with_crlf_is_returned_byte_for_byte(client: TestClient) -> None:
    priya, elena = person(client, "EMP-401"), person(client, "EMP-402")
    b = credit()
    b = b.model_copy(update={"text": (b.text or "").replace("\n", "\r\n")})
    assert b.text and "\r\n" in b.text
    made = post(client, priya, b)
    r = client.post(f"/api/v1/register/changes/{made['change_id']}/approve", headers=elena)
    assert r.status_code == 200 and r.json()["state"] == "approved", r.text
    t = client.get(f"/api/v1/register/entries/{b.doc_id}/text", headers=priya)
    assert t.status_code == 200 and t.headers["content-type"] == "text/plain; charset=utf-8"
    assert t.content == b.text.encode()


def test_waiting_on_me_is_empty_for_an_agent(client: TestClient, agent: Headers) -> None:
    priya, elena = person(client, "EMP-401"), person(client, "EMP-402")
    c = post(client, priya, credit())
    mine = client.get("/api/v1/register/changes", params={"waiting_on": "me"}, headers=elena)
    assert [x["change_id"] for x in mine.json()] == [c["change_id"]]
    theirs = client.get("/api/v1/register/changes", params={"waiting_on": "me"}, headers=agent)
    assert theirs.status_code == 200 and theirs.json() == []


def test_settings_get_put_executives_only(client: TestClient) -> None:
    sarah, david = person(client, "EMP-101"), person(client, "EMP-300")
    assert client.get("/api/v1/register/settings", headers=sarah).json() == {
        "on_mismatch": "use_registered"}  # fmt: skip
    no = client.put("/api/v1/register/settings", json={"on_mismatch": "route"}, headers=sarah)
    assert no.status_code == 422 and no.json()["refusals"][0]["rule"] == "RR-4"
    bad = client.put("/api/v1/register/settings", json={"on_mismatch": "nope"}, headers=david)
    assert bad.status_code == 422
    ok = client.put("/api/v1/register/settings", json={"on_mismatch": "route"}, headers=david)
    assert ok.status_code == 200 and ok.json() == {"on_mismatch": "route"}
    assert client.get("/api/v1/register", headers=sarah).json()["settings"] == {
        "on_mismatch": "route"}  # fmt: skip


def test_procedures_reads(client: TestClient) -> None:
    h = person(client, "EMP-101")
    rows = client.get("/api/v1/procedures", headers=h).json()
    assert {p["id"] for p in rows} == {"PROC-DISCOUNT", "PROC-CREDIT", "PROC-SLA"}
    one = client.get("/api/v1/procedures/PROC-SLA", headers=h).json()
    assert one["decision_type"] == "sla" and len(one["versions"]) == 2
    assert client.get("/api/v1/procedures/PROC-NOPE", headers=h).status_code == 404


# -- work items ---------------------------------------------------------------------------------
def test_agent_draft_appears_for_all_of_sales(client: TestClient, agent: Headers) -> None:
    d = post(client, agent, edge())
    assert d["state"] == "draft" and d["proposed_by"]["kind"] == "agent"
    for emp in ("EMP-200", "EMP-101"):  # Michael and Sarah, both in Sales
        mine = of_kind(items(client, person(client, emp), "waiting_on_you"), "register_draft")
        assert [i["id"] for i in mine] == [d["change_id"]]
        assert mine[0]["raised_by"]["kind"] == "agent"
        assert mine[0]["href"] == f"/api/v1/register/changes/{d['change_id']}"
        assert {"EMP-101", "EMP-200"} <= {p["id"] for p in mine[0]["waiting_on"]}
    finance = person(client, "EMP-401")
    assert of_kind(items(client, finance, "waiting_on_you"), "register_draft") == []


def test_unknown_kind_draft_waits_on_the_principal_only(client: TestClient, agent: Headers) -> None:
    d = post(client, agent, mandate(submit=False))
    mine = of_kind(items(client, person(client, "EMP-101"), "waiting_on_you"), "register_draft")
    assert [i["id"] for i in mine] == [d["change_id"]]
    assert [p["id"] for p in mine[0]["waiting_on"]] == ["EMP-101"]
    michael = person(client, "EMP-200")
    assert of_kind(items(client, michael, "waiting_on_you"), "register_draft") == []


def test_a_persons_own_draft_lists_only_them(client: TestClient) -> None:
    sarah = person(client, "EMP-101")
    d = post(client, sarah, edge(), submit=False)
    mine = of_kind(items(client, sarah, "waiting_on_you"), "register_draft")
    assert [(i["id"], [p["id"] for p in i["waiting_on"]]) for i in mine] == [
        (d["change_id"], ["EMP-101"])]  # fmt: skip
    michael = person(client, "EMP-200")
    assert of_kind(items(client, michael, "waiting_on_you"), "register_draft") == []


def test_draft_submit_dismiss_land_in_done(client: TestClient, agent: Headers) -> None:
    first = post(client, agent, edge())
    second = post(client, agent, edge())
    michael, sarah = person(client, "EMP-200"), person(client, "EMP-101")
    r = client.post(f"/api/v1/register/changes/{first['change_id']}/submit",
                    json={"base_version": 17}, headers=michael)  # fmt: skip
    assert r.status_code == 200 and r.json()["state"] == "pending", r.text
    r = client.post(f"/api/v1/register/changes/{second['change_id']}/withdraw", headers=sarah)
    assert r.status_code == 200 and r.json()["state"] == "withdrawn"
    assert items(client, michael, "waiting_on_you") == []
    done = items(client, michael, "done")
    assert [(i["kind"], i["id"], i["result"]) for i in done] == [
        ("register_draft", first["change_id"], "submitted")]  # fmt: skip
    assert [(i["kind"], i["result"]) for i in items(client, sarah, "done")] == [
        ("register_draft", "dismissed")]  # fmt: skip


def test_pending_change_is_work_for_its_approvers_then_done(client: TestClient) -> None:
    priya, elena, hannah = (person(client, e) for e in ("EMP-401", "EMP-402", "EMP-601"))
    c = post(client, priya, credit())
    assert c["state"] == "pending"
    mine = of_kind(items(client, elena, "waiting_on_you"), "register_change")
    assert [i["id"] for i in mine] == [c["change_id"]]
    assert mine[0]["raised_by"]["person"]["id"] == "EMP-401"
    assert mine[0]["href"] == f"/api/v1/register/changes/{c['change_id']}"
    assert of_kind(items(client, priya, "waiting_on_others"), "register_change")
    assert items(client, hannah, "waiting_on_you") == []
    client.post(f"/api/v1/register/changes/{c['change_id']}/approve", headers=elena)
    assert of_kind(items(client, elena, "waiting_on_you"), "register_change") == []
    assert [(i["kind"], i["result"]) for i in items(client, elena, "done")] == [
        ("register_change", "approved")]  # fmt: skip


def test_decline_needs_a_note_and_lands_in_done(client: TestClient) -> None:
    priya, elena = person(client, "EMP-401"), person(client, "EMP-402")
    c = post(client, priya, credit())
    url = f"/api/v1/register/changes/{c['change_id']}/decline"
    r = client.post(url, headers=elena)
    assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "DC-2"
    r = client.post(url, json={"note": "  "}, headers=elena)
    assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "DC-2"
    r = client.post(url, json={"note": "Not this quarter."}, headers=elena)
    assert r.status_code == 200 and r.json()["declined"]["note"] == "Not this quarter."
    assert [(i["kind"], i["result"]) for i in items(client, elena, "done")] == [
        ("register_change", "declined")]  # fmt: skip


# -- changes ------------------------------------------------------------------------------------
def test_get_one_change_includes_drafts(client: TestClient, agent: Headers) -> None:
    d = post(client, agent, edge())
    r = client.get(f"/api/v1/register/changes/{d['change_id']}", headers=person(client, "EMP-401"))
    assert r.status_code == 200
    assert r.json()["state"] == "draft" and "checks" in r.json()
    assert client.get("/api/v1/register/changes/CHG-9999", headers=agent).status_code == 404


def test_list_changes_filters(client: TestClient, agent: Headers) -> None:
    d = post(client, agent, edge())
    c = post(client, person(client, "EMP-401"), credit())
    michael = person(client, "EMP-200")
    allc = client.get("/api/v1/register/changes", headers=michael).json()
    assert [x["change_id"] for x in allc] == [d["change_id"], c["change_id"]]
    pend = client.get("/api/v1/register/changes", params={"state": "pending"}, headers=michael)
    assert [x["change_id"] for x in pend.json()] == [c["change_id"]]
    me = client.get("/api/v1/register/changes", params={"waiting_on": "me"}, headers=michael)
    assert [x["change_id"] for x in me.json()] == [d["change_id"]]
    bad = client.get("/api/v1/register/changes", params={"state": "nope"}, headers=michael)
    assert bad.status_code == 422
    other = client.get("/api/v1/register/changes", params={"waiting_on": "EMP-1"}, headers=michael)
    assert other.status_code == 422


def test_submit_takes_base_version(client: TestClient, agent: Headers) -> None:
    d = post(client, agent, edge())
    michael = person(client, "EMP-200")
    url = f"/api/v1/register/changes/{d['change_id']}/submit"
    assert client.post(url, headers=michael).status_code == 422  # no body
    assert client.post(url, json={}, headers=michael).status_code == 422
    r = client.post(url, json={"base_version": 17, "x": 1}, headers=michael)
    assert r.status_code == 422  # an extra field
    r = client.post(url, json={"base_version": 17}, headers=michael)
    assert r.status_code == 200 and r.json()["submitted_by"]["id"] == "EMP-200"
    assert client.post(url, json={"base_version": 17}, headers=michael).status_code == 422  # DC-2


def test_rr13_refused_over_http(client: TestClient) -> None:
    priya, elena = person(client, "EMP-401"), person(client, "EMP-402")
    # two changes at version 17 for the same credit policy; the first approval moves the register
    first = post(client, priya, credit())
    second = post(client, priya, credit())
    ok = client.post(f"/api/v1/register/changes/{first['change_id']}/approve", headers=elena)
    assert ok.status_code == 200, ok.text
    r = client.post(f"/api/v1/register/changes/{second['change_id']}/approve", headers=elena)
    assert r.status_code == 409 and r.json()["refusals"][0]["rule"] == "RR-13"
    got = client.get(f"/api/v1/register/changes/{second['change_id']}", headers=priya).json()
    assert got["state"] == "refused" and got["refused"][0]["rule"] == "RR-13"
    # the refused approval is no longer waiting on Elena and shows in her done
    mine = items(client, elena, "waiting_on_you")
    assert second["change_id"] not in [i["id"] for i in of_kind(mine, "register_change")]
    done = [i for i in of_kind(items(client, elena, "done"), "register_change")
            if i["id"] == second["change_id"]]  # fmt: skip
    assert [d["result"] for d in done] == ["refused"]
    stale = client.post("/api/v1/register/changes", headers=priya,
                        json=payload(credit(), base_version=16))  # fmt: skip
    assert stale.status_code == 409


def test_status_codes(client: TestClient, agent: Headers) -> None:
    priya, elena = person(client, "EMP-401"), person(client, "EMP-402")
    r = client.post("/api/v1/register/changes", headers=priya,
                    json=payload(credit(), submitted_by="EMP-402"))  # fmt: skip
    assert r.status_code == 403 and r.json()["refusals"][0]["rule"] == "RR-1"
    c = post(client, priya, credit())
    r = client.post(f"/api/v1/register/changes/{c['change_id']}/approve", headers=agent)
    assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "RR-2"
    for bad in ({"action": "register"}, payload(credit(), surprise=1), {}):
        r = client.post("/api/v1/register/changes", json=bad, headers=priya)
        assert r.status_code == 422, bad
    for step in ("approve", "withdraw", "remind", "decline"):
        r = client.post(f"/api/v1/register/changes/CHG-9999/{step}", headers=elena)
        assert r.status_code == 404, step
    nope = client.post("/api/v1/register/changes/CHG-9999/submit", json={"base_version": 1},
                       headers=elena)  # fmt: skip
    assert nope.status_code == 404
    url = f"/api/v1/register/changes/{c['change_id']}/remind"
    assert client.post(url, headers=priya).status_code == 200
    assert client.post(url, headers=priya).status_code == 422  # once a clock day
    w = client.post(f"/api/v1/register/changes/{c['change_id']}/withdraw", headers=priya)
    assert w.status_code == 200 and w.json()["state"] == "withdrawn"


def test_revoke_over_http(client: TestClient) -> None:
    hannah, marcus = person(client, "EMP-601"), person(client, "EMP-602")
    c = post(client, hannah, revoke_brl())
    assert c["action"] == "revoke" and c["state"] == "pending"
    r = client.post(f"/api/v1/register/changes/{c['change_id']}/approve", headers=marcus)
    assert r.status_code == 200 and r.json()["state"] == "approved", r.text


# -- procedures ---------------------------------------------------------------------------------
def test_procedure_version_over_http(client: TestClient) -> None:
    hannah, marcus = person(client, "EMP-601"), person(client, "EMP-602")
    c = post(client, hannah, procedure(version=3))
    assert c["state"] == "pending" and c["doc_id"] == "PROC-SLA v3"
    r = client.post(f"/api/v1/register/changes/{c['change_id']}/approve", headers=marcus)
    assert r.status_code == 200 and r.json()["state"] == "approved", r.text
    one = client.get("/api/v1/procedures/PROC-SLA", headers=hannah).json()
    assert [v["version"] for v in one["versions"]] == [1, 2, 3]


def test_procedure_request_shape_is_strict(client: TestClient) -> None:
    hannah = person(client, "EMP-601")
    ok = payload(procedure(version=3))
    for bad in (ok | {"surprise": 1}, {k: v for k, v in ok.items() if k != "report"},
                ok | {"version": "three"}, ok | {"doc_id": "X"}):  # fmt: skip
        r = client.post("/api/v1/register/changes", json=bad, headers=hannah)
        assert r.status_code == 422, bad.keys()
    r = client.post("/api/v1/register/changes", json=ok | {"decision_type": "nope"}, headers=hannah)
    assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "RR-5"
    r = client.post("/api/v1/register/changes", json=ok | {"report": {"x": 1}}, headers=hannah)
    assert r.status_code == 422 and r.json()["refusals"][0]["rule"] == "ADM"
