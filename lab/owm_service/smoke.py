"""Container smoke test: S22's main branch over HTTP against a running service.

    python lab/owm_service/smoke.py --base http://localhost:8000

The service must have been started with OWM_LAB_ROUTES=1 (the image defaults them off). Exits 0
and prints `S22: spent` when the decision ends spent; anything else exits 1. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

P15: dict[str, Any] = {
    "request_id": "DR-9001", "account_id": "CRM-2048", "product": "NS-500", "discount": 0.15,
}  # fmt: skip


def call(base: str, method: str, path: str, token: str | None = None,
         body: dict[str, Any] | None = None) -> Any:  # fmt: skip
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path}: HTTP {e.code}: {e.read().decode()[:500]}") from e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    base = ap.parse_args().base.rstrip("/")
    api = "/api/v1"
    session = "/lab/sessions"
    agent = call(base, "POST", session,
                 body={"agent_id": "AGT-DEALDESK", "on_behalf_of": "EMP-101"})["token"]  # fmt: skip
    sarah = call(base, "POST", session, body={"person_id": "EMP-101"})["token"]
    michael = call(base, "POST", session, body={"person_id": "EMP-200"})["token"]

    rec = call(base, "POST", f"{api}/decisions", agent, {
        "decision_type": "discount", "subject": {"request_id": "DR-9001"},
        "submitted": {"requested_discount": 0.08}})  # fmt: skip
    did = rec["decision_id"]
    resolved = call(base, "POST", f"{api}/decisions/{did}/conditions/c1/resolve", sarah,
                    {"decision_version": rec["version"],
                     "resolution": "confirmed_record"})  # fmt: skip
    v2 = call(base, "POST", f"{api}/decisions/{did}/approve", michael,
              {"decision_version": resolved["version"]})  # fmt: skip
    cleared = call(base, "POST", f"{api}/decisions/{did}/clearance", agent, {
        "decision_id": did, "decision_version": v2["version"],
        "action": v2["actions"][0]["action"], "params": P15})  # fmt: skip
    out = call(base, "POST", "/lab/adapter/execute", agent,
               {"clearance_id": cleared["clearance_id"]})  # fmt: skip
    final = call(base, "GET", f"{api}/decisions/{did}", agent)
    if not (out.get("redeemed") and out.get("report") == "applied" and final["state"] == "spent"):
        print(f"S22: expected spent, got {final.get('state')!r}; adapter {out}", file=sys.stderr)
        return 1
    print("S22: spent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
