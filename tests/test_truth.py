"""The laboratory control loads, and refuses to load when it is inconsistent."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import TRUTH
from northstar.model import load_truth
from northstar.model.truth import TruthError


def test_truth_matches_doc_03_anchors() -> None:
    t = load_truth(TRUTH)
    acme = t.customer("CUST-1001")
    assert acme.source_ids == {"crm": "CRM-2048", "erp": "C-1001", "contract_ref": "ACME-MFG-2025"}
    assert t.employee("EMP-101").manager == "EMP-200"
    assert t.employee("EMP-200").role == "VP_SALES"
    assert t.exception("EXC-ACME-NS500-15").maximum_discount == 0.15
    assert [len(t.scenarios), len(t.holders_of("VP_SALES")), len(t.holders_of("CRO"))] == [14, 1, 1]


def test_dangling_reference_is_refused(truth_copy: Path) -> None:
    p = truth_copy / "entities.yaml"
    p.write_text(p.read_text().replace("manager: EMP-200", "manager: EMP-999", 1))
    with pytest.raises(TruthError, match="EMP-101: unknown manager EMP-999"):
        load_truth(truth_copy)


def test_relationship_contradicting_an_attribute_is_refused(truth_copy: Path) -> None:
    p = truth_copy / "relationships.yaml"
    p.write_text(
        p.read_text().replace("[EMP-101, reports_to, EMP-200]", "[EMP-101, reports_to, EMP-300]")
    )
    with pytest.raises(TruthError, match="reports_to disagrees with manager"):
        load_truth(truth_copy)
