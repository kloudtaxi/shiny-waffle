from __future__ import annotations

from pathlib import Path

from owm_service.config import load_settings


def test_defaults() -> None:
    s = load_settings({})
    assert (s.jev, s.jev_cap, s.clock, s.clearance_ttl, s.lab_routes) == (
        "replay",
        100,
        "2026-09-23T09:00:00-05:00",
        300,
        True,
    )
    assert s.state_dir == Path(".owm-service")
    assert s.corpus == "base"
    assert s.key_file is None
    assert s.suspended == frozenset()


def test_key_file_is_a_path_only() -> None:
    assert load_settings({"TYPESAFE_API_KEY_FILE": "/x/k"}).key_file == Path("/x/k")


def test_overrides() -> None:
    s = load_settings(
        {
            "OWM_STATE_DIR": "/data",
            "OWM_CORPUS": "no-org-chart",
            "OWM_JEV": "live",
            "OWM_JEV_CAP": "5",
            "OWM_CLOCK": "real",
            "OWM_CLEARANCE_TTL_SECONDS": "60",
            "OWM_SUSPENDED": "AGT-DEALDESK, AGT-X@abc",
            "OWM_LAB_ROUTES": "0",
        }
    )
    assert s.state_dir == Path("/data") and s.corpus == "no-org-chart"
    assert (s.jev, s.jev_cap, s.clock, s.clearance_ttl) == ("live", 5, "real", 60)
    assert s.suspended == frozenset({"AGT-DEALDESK", "AGT-X@abc"})
    assert s.lab_routes is False
