"""Properties the evidence corpus must hold for the experiment to mean anything."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from conftest import SEED, TRUTH
from northstar.build import Dataset, assemble, build


def _rows(ds: Dataset, artifact_id: str) -> list[dict[str, str]]:
    a = next(a for a in ds.artifacts if a.id == artifact_id)
    return list(csv.DictReader(io.StringIO(a.content)))


def _text(ds: Dataset, artifact_id: str) -> str:
    return next(a.content for a in ds.artifacts if a.id == artifact_id)


# -- "No single artifact contains the answer" (doc 02 §4) ------------------------


def test_derived_facts_are_stated_nowhere(ds: Dataset) -> None:
    derived = {f.id for f in ds.truth.facts if f.kind == "derived"}
    assert not [(a.id, f) for a in ds.artifacts for f in a.asserts if f in derived]


def test_every_asserted_fact_is_stated_somewhere(ds: Dataset) -> None:
    stated = {f for a in ds.artifacts for f in a.asserts}
    asserted = {f.id for f in ds.truth.facts if f.kind == "asserted"}
    assert asserted <= stated


def test_authority_is_distributed_across_artifacts(ds: Dataset) -> None:
    people = [e.name for e in ds.truth.employees]
    for role_doc in ("approval_authority_matrix", "pricing_policy_2025", "pricing_policy_2026"):
        assert not [p for p in people if p in _text(ds, role_doc)], role_doc
    for people_doc in ("organization_chart", "employees"):
        assert "%" not in _text(ds, people_doc), people_doc
    for a in ds.artifacts:
        assert not ("Michael" in a.content and "20%" in a.content), a.id


def test_source_systems_never_use_canonical_customer_ids(ds: Dataset) -> None:
    """CUST-* ids are the laboratory's; resolving to them is the foundation's job."""
    assert not [a.id for a in ds.artifacts if re.search(r"CUST-\d+", a.content)]


def test_scenario_5_corpus_removes_contracts_but_keeps_hearsay(ds: Dataset) -> None:
    ids = {a.id for a in ds.corpora["missing-contract-evidence"]}
    assert not ids & {
        "acme_master_supply_agreement",
        "acme_pricing_exception",
        "acme_pricing_exception_2023",
    }
    assert {"acme_account_strategy", "email_sarah_to_michael", "discount_requests"} <= ids


# -- Background noise never contradicts the truth ------------------------------


def test_background_holds_no_second_vp_or_cro(ds: Dataset) -> None:
    titles = [r["title"] for r in _rows(ds, "employees")]
    assert titles.count("VP Sales") == 1
    assert titles.count("Chief Revenue Officer") == 1


def test_background_names_do_not_collide_with_truth(ds: Dataset) -> None:
    names = [r["account_name"] for r in _rows(ds, "crm_accounts")]
    assert sorted(n for n in names if "acme" in n.lower()) == [
        "Acme Industrial Supply Co.",
        "Acme Manufacturing",
    ]


def test_background_approvals_obey_the_policy_in_force(ds: Dataset) -> None:
    t = ds.truth
    for r in ds.background.discount_requests:
        policy = t.policy_on(r.request_date)
        assert policy is not None
        band = policy.band_for(r.requested_discount)
        expected = r.requestor if band.role == "ENTERPRISE_AE" else t.holders_of(band.role)[0].id
        assert r.approved_by == expected, r.id


def test_ids_are_unique_within_every_table(ds: Dataset) -> None:
    for artifact_id, key in [
        ("crm_accounts", "account_id"),
        ("customers", "erp_customer_id"),
        ("employees", "employee_id"),
        ("products", "product_id"),
        ("erp_orders", "order_id"),
        ("discount_requests", "request_id"),
    ]:
        ids = [r[key] for r in _rows(ds, artifact_id)]
        assert len(ids) == len(set(ids)), artifact_id


# -- Reproducibility (doc 04: "seeded and reproducible") ------------------------


def _tree(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()
    }


def test_same_seed_is_byte_identical(tmp_path: Path) -> None:
    build(TRUTH, tmp_path / "a", SEED, "small")
    build(TRUTH, tmp_path / "b", SEED, "small")
    assert _tree(tmp_path / "a") == _tree(tmp_path / "b")


def test_other_seed_changes_noise_not_truth(ds: Dataset) -> None:
    other = assemble(TRUTH, SEED + 1, "small")
    assert _text(ds, "crm_accounts") != _text(other, "crm_accounts")
    assert ds.results == other.results
    for doc in ("pricing_policy_2026", "approval_authority_matrix", "acme_pricing_exception"):
        assert _text(ds, doc) == _text(other, doc)


def test_large_scale_stays_coherent() -> None:
    big = assemble(TRUTH, SEED, "large")
    assert len(big.background.customers) == 200
    assert len(big.background.discount_requests) == 1000


def test_build_leaves_foreign_files_alone(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("mine")
    build(TRUTH, tmp_path, SEED, "small")
    assert (tmp_path / "notes.md").read_text() == "mine"
    assert (tmp_path / "evidence" / "MANIFEST.yaml").exists()
    assert (tmp_path / "evidence-variants" / "missing-contract-evidence" / "MANIFEST.yaml").exists()


def test_generated_amounts_vary(ds: Dataset) -> None:
    """Guards the observed polyfactory `multiple_of` collapse to the lower bound."""
    assert len({o.order_value_usd for o in ds.background.orders}) > len(ds.background.orders) // 2
    assert len({p.list_price_usd for p in ds.background.products}) > 1


def test_background_ids_follow_dates(ds: Dataset) -> None:
    orders, requests = ds.background.orders, ds.background.discount_requests
    assert [o.order_date for o in orders] == sorted(o.order_date for o in orders)
    assert [o.id for o in orders] == sorted(o.id for o in orders)
    assert [r.request_date for r in requests] == sorted(r.request_date for r in requests)
    assert [r.id for r in requests] == sorted(r.id for r in requests)
