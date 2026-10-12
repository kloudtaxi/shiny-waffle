from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from owm_service.config import Settings, load_settings


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
    assert s.suspended == frozenset()


def test_settings_never_hold_the_key_or_its_path() -> None:
    """M-1: the service's settings don't read the key variables (the lab engine does, in live
    mode only), so neither can reach a log or a response through them."""
    assert not [f.name for f in dataclasses.fields(Settings) if "key" in f.name]
    keyed = {"TYPESAFE_API_KEY": "not-a-key", "TYPESAFE_API_KEY_FILE": "/x/k"}
    assert load_settings(keyed) == load_settings({})


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


@pytest.mark.parametrize("raw", ["0", "false", "False", "no", "off", "OFF", " 0 ", "", "  "])
def test_lab_routes_off(raw: str) -> None:
    """Ruling R37: the flag that gates sign-in-as-anyone reads case-insensitively and stripped."""
    assert load_settings({"OWM_LAB_ROUTES": raw}).lab_routes is False


@pytest.mark.parametrize("raw", ["1", "true", "True", "yes", " on "])
def test_lab_routes_on(raw: str) -> None:
    assert load_settings({"OWM_LAB_ROUTES": raw}).lab_routes is True


@pytest.mark.parametrize("raw", ["disabled", "2", "enable"])
def test_lab_routes_unknown_value_refuses(raw: str) -> None:
    """A value that is neither on nor off fails loudly, as OWM_JEV does, rather than guessing."""
    with pytest.raises(ValueError, match="OWM_LAB_ROUTES"):
        load_settings({"OWM_LAB_ROUTES": raw})
