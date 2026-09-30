"""Every scenario's hand-authored expectation follows from truth + generated evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import SEED
from northstar.build import Dataset, IncoherentTruthError, assemble


def test_all_scenarios_coherent(ds: Dataset) -> None:
    outcomes = {sid: r.get("decision", {}).get("outcome") for sid, r in ds.results.items()}
    assert outcomes == {
        "S01": "APPROVE_WITH_AUTHORIZATION",
        "S02": "REJECT_OR_ESCALATE",
        "S03": "REVIEW_REQUIRED",
        "S04": "APPROVE",
        "S05": "REQUEST_EVIDENCE",
        "S06": None,
        "S07": None,
        "S08": None,
        # held-out decisions (added 2026-09-29, after the OWM procedure was frozen)
        "S09": "REJECT_OR_ESCALATE",
        "S10": "APPROVE_WITH_AUTHORIZATION",
        "S11": "APPROVE_WITH_AUTHORIZATION",
        "S12": "APPROVE",
        "S13": "REQUEST_EVIDENCE",
        "S14": "APPROVE",
        # fresh held-out decisions (added 2026-09-30 with procedure v2, before any reader run)
        "S15": "REQUEST_EVIDENCE",
        "S16": "APPROVE",
        "S17": "REVIEW_REQUIRED",
        "S18": "APPROVE",
        "S19": "APPROVE",
        "S20": "REJECT_OR_ESCALATE",
        # the 2027 policy (lab extension, OWM measurements item 4)
        "S21": "APPROVE_WITH_AUTHORIZATION",
    }


def test_s01_matches_the_canonical_decision_object(ds: Dataset) -> None:
    """doc 03 §21, field for field."""
    r = ds.results["S01"]
    assert r["commercial_eligibility"] == {
        "status": "eligible",
        "maximum_discount": 0.15,
        "basis": "EXC-ACME-NS500-15",
    }
    assert r["authority"]["requestor"] == {
        "employee": "EMP-101",
        "maximum_discount": 0.10,
        "authorized": False,
    }
    assert r["authority"]["required"] == {"role": "VP_SALES", "maximum_discount": 0.20}
    assert r["authority"]["approver"] == {
        "employee": "EMP-200",
        "name": "Michael Torres",
        "authorized": True,
    }
    assert r["evidence"] == [
        "CRM-2048",
        "C-1001",
        "MSA-ACME-2025",
        "EXC-ACME-NS500-15",
        "pricing_policy_2026",
        "approval_authority_matrix",
        "organization_chart",
        "DR-9001",
    ]


def test_s06_keeps_both_exceptions_and_selects_by_date(ds: Dataset) -> None:
    r = ds.results["S06"]
    assert r["preserved"] == ["EXC-ACME-NS500-10", "EXC-ACME-NS500-15"]
    assert [p["exception"] for p in r["probes"]] == ["EXC-ACME-NS500-15", "EXC-ACME-NS500-10", None]


def test_s07_hearsay_is_not_a_basis(ds: Dataset) -> None:
    r = ds.results["S07"]
    assert r["authoritative"] == ["acme_master_supply_agreement", "acme_pricing_exception"]
    assert {"acme_account_strategy", "email_sarah_to_michael"} <= set(r["hearsay"])


@pytest.mark.parametrize(
    ("scenario_file", "wrong", "right"),
    [
        ("01-standard-discount.yaml", "outcome: APPROVE_WITH_AUTHORIZATION", "outcome: APPROVE"),
        (
            "05-missing-evidence.yaml",
            "outcome: REQUEST_EVIDENCE",
            "outcome: APPROVE_WITH_AUTHORIZATION",
        ),
        ("04-historical-policy.yaml", "requestor_authorized: true", "requestor_authorized: false"),
    ],
)
def test_incoherent_expectation_refuses_to_build(
    truth_copy: Path, scenario_file: str, wrong: str, right: str
) -> None:
    p = truth_copy / "scenarios" / scenario_file
    p.write_text(p.read_text().replace(wrong, right, 1))
    with pytest.raises(IncoherentTruthError):
        assemble(truth_copy, SEED, "small")


def test_scenario_5_hinges_on_the_corpus_not_the_truth(truth_copy: Path) -> None:
    """Same truth, full corpus → the S05 request would be approvable with authorization."""
    p = truth_copy / "scenarios" / "05-missing-evidence.yaml"
    text = p.read_text().replace("corpus: missing-contract-evidence", "corpus: base")
    p.write_text(text)
    with pytest.raises(IncoherentTruthError, match="S05 outcome"):
        assemble(truth_copy, SEED, "small")
