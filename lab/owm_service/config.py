"""Settings from the environment (spec §12). The Jev key is reached only through a file path."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DEFAULT_CLOCK = "2026-09-23T09:00:00-05:00"


@dataclass(frozen=True)
class Settings:
    state_dir: Path
    corpus: str
    jev: Literal["replay", "live"]
    jev_cap: int
    key_file: Path | None
    clock: str
    clearance_ttl: int
    suspended: frozenset[str]
    lab_routes: bool


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    jev = env.get("OWM_JEV", "replay")
    if jev == "replay":
        mode: Literal["replay", "live"] = "replay"
    elif jev == "live":
        mode = "live"
    else:
        raise ValueError(f"OWM_JEV must be 'replay' or 'live', not {jev!r}")
    key_file = env.get("TYPESAFE_API_KEY_FILE")
    return Settings(
        state_dir=Path(env.get("OWM_STATE_DIR", ".owm-service")),
        corpus=env.get("OWM_CORPUS", "base"),
        jev=mode,
        jev_cap=int(env.get("OWM_JEV_CAP", "100")),
        key_file=Path(key_file) if key_file else None,
        clock=env.get("OWM_CLOCK", DEFAULT_CLOCK),
        clearance_ttl=int(env.get("OWM_CLEARANCE_TTL_SECONDS", "300")),
        suspended=frozenset(
            part.strip() for part in env.get("OWM_SUSPENDED", "").split(",") if part.strip()
        ),
        lab_routes=env.get("OWM_LAB_ROUTES", "1") not in ("0", "false", "no", ""),
    )
