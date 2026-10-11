from __future__ import annotations

from pathlib import Path

import pytest

from owm_service.config import load_settings
from owm_service.org import Org

SARAH = {"kind": "person", "id": "EMP-101"}


@pytest.fixture
def org(tmp_path: Path) -> Org:
    return Org(load_settings({"OWM_STATE_DIR": str(tmp_path / "state")}))


@pytest.fixture
def sarah() -> dict[str, str]:
    return dict(SARAH)
