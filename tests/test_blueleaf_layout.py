"""BlueLeaf lab MCP server, task B-01: the package layout and the `_lab.py` boundary.

The plan is `docs/superpowers/plans/2026-10-06-blueleaf-mcp-plan.md` (task 1, conventions §1).
"""

from __future__ import annotations

from pathlib import Path

from service import _lab

LAB = Path(__file__).resolve().parents[1]
PACKAGE = LAB / "lab/blueleaf_mcp"


def test_lab_boundary_loads_a_frozen_spec() -> None:
    spec = _lab.load_spec(LAB / "lab/owm_kernel/specs/discount.yaml")
    assert spec["spec"] == "discount_approval"


def test_lab_boundary_loads_a_spec_from_text() -> None:
    text = (LAB / "lab/owm_kernel/specs/credit_v3.yaml").read_text()
    assert _lab.loads_spec(text, "credit_v3.yaml")["spec"] == "credit_limit_increase"


def test_only_the_boundary_touches_sys_path() -> None:
    offenders = [
        p.relative_to(LAB).as_posix()
        for p in sorted(PACKAGE.rglob("*.py"))
        if p.name != "_lab.py" and "sys.path" in p.read_text()
    ]
    assert offenders == []


def test_the_package_root_is_not_a_package() -> None:
    # The servers run as scripts, so `service` and `scoring` are top-level names (plan §1).
    assert not (PACKAGE / "__init__.py").exists()
    assert (PACKAGE / "service/__init__.py").exists()
