"""Loads the registrar and the register-attack self-check by path, the way the attack runs do."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
ATTACKS = ROOT / "runs/2026-10-08-register-attacks"


def load_check_registrar() -> ModuleType:
    """check_registrar.py puts lab/owm_register on sys.path and imports `registrar` itself."""
    spec = importlib.util.spec_from_file_location("check_registrar", ATTACKS / "check_registrar.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("check_registrar", mod)
    spec.loader.exec_module(mod)
    return mod


CHECK = load_check_registrar()
registrar: ModuleType = sys.modules["registrar"]
