from __future__ import annotations

from pathlib import Path

from owm_service.config import load_settings
from owm_service.org import Org


def test_policy_terms(org: Org) -> None:
    terms = org.policy_terms("PRICING-POLICY-2026")
    assert terms is not None
    assert [b["title"] for b in terms["bands"]] == [
        "Enterprise Account Executive", "VP Sales", "Chief Revenue Officer"]  # fmt: skip
    assert org.policy_terms("NOPE") is None


def test_org_wiring(org: Org, tmp_path: Path) -> None:
    assert (tmp_path / "state/northstar/events.sqlite").exists()
    assert org.engine.calls == tmp_path / "state/northstar/jev-calls.jsonl"
    assert org.engine.live is False
    assert org.on_mismatch() == "use_registered"
    assert org.procedures()[0]


def test_kernel_register_is_cached_per_version(org: Org, tmp_path: Path) -> None:
    a = org.kernel_register()
    assert org.kernel_register() is a
    assert (tmp_path / "state/northstar/store").is_dir()


def test_state_survives_a_restart(org: Org, tmp_path: Path, sarah: dict[str, str]) -> None:
    with org.log.transaction() as tx:
        org.sor.edit(tx, "discount_requests", "DR-9001", {"requested_discount_pct": "8.0"},
                     actor=sarah, at=org.clock.now())  # fmt: skip
    again = Org(load_settings({"OWM_STATE_DIR": str(tmp_path / "state")}))
    row = again.sor.row("discount_requests", "DR-9001")
    assert row is not None and row["requested_discount_pct"] == "8.0"
