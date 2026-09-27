from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from northstar.build import Dataset, assemble

LAB = Path(__file__).resolve().parents[1]
TRUTH = LAB / "truth"
SEED = 20260923


@pytest.fixture(scope="session")
def ds() -> Dataset:
    return assemble(TRUTH, SEED, "small")


@pytest.fixture
def truth_copy(tmp_path: Path) -> Path:
    """A writable copy of truth/ for tests that break it on purpose."""
    dst = tmp_path / "truth"
    shutil.copytree(TRUTH, dst)
    return dst
