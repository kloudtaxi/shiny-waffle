"""The private scan (lab plan L1.3): truth-derived terms are caught, and never written down."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from prototype_bundle.scan import Hit, ScanError, scan


def _tree(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def test_planted_scenario_id_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"source/lab/flow.py": "x = 1\n# see S07 for why\ny = 2\n"})
    hits = scan(root)
    assert hits == [Hit(file="source/lab/flow.py", line=2, term_kind="scenario_id")]


def test_planted_person_name_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"docs/spec.md": "# Spec\n\nThe rep, Sarah Chen, asks.\n"})
    assert [(h.file, h.line, h.term_kind) for h in scan(root)] == [("docs/spec.md", 3, "person")]


def test_clean_tree_gives_no_hits(tmp_path: Path) -> None:
    root = _tree(
        tmp_path,
        {
            "source/lab/kernel.py": "def decide(record):\n    return record['outcome']\n",
            "docs/spec.md": "The approver's tool has no model in it. Separation of concerns.\n",
        },
    )
    assert scan(root) == []


def test_hit_never_holds_the_term(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"README.md": "Request DR-9001 for Sarah Chen, as in S01.\n"})
    hits = scan(root)
    assert {h.term_kind for h in hits} == {"request_id", "person", "scenario_id"}
    for h in hits:
        rendered = repr(h) + str(dataclasses.astuple(h))
        for term in ("DR-9001", "Sarah", "Chen", "S01"):
            assert term not in rendered


def test_org_inputs_are_checked_for_lab_markers_only(tmp_path: Path) -> None:
    # The org's own documents may name its people and requests (spec §11.3), and use the ordinary
    # phrases the lab's trap labels were named after; a lab id such as a scenario id never appears.
    root = _tree(
        tmp_path,
        {
            "inputs/northstar/documents/memo.md": "From Sarah Chen about DR-9001.\n",
            "inputs/northstar/structured/notes.csv": "id,note\n1,see S05\n",
            "inputs/northstar/structured/tickets.csv": "id,note\n2,reported priority P1\n",
        },
    )
    assert [(h.file, h.term_kind) for h in scan(root)] == [
        ("inputs/northstar/structured/notes.csv", "scenario_id")
    ]


def test_unpadded_step_labels_are_not_scenario_ids(tmp_path: Path) -> None:
    # The spec's diagrams label steps S1..S4. Scenario ids are S01..S45; short forms in exported
    # source are the scrub's to catch (L1.2), not the scan's.
    root = _tree(tmp_path, {"docs/spec.md": '  S1["1 · enable"] --> S2["2 · check"]\n'})
    assert scan(root) == []


def test_design_vocabulary_passes_but_a_coined_trap_label_is_caught(tmp_path: Path) -> None:
    root = _tree(
        tmp_path,
        {
            "docs/spec.md": "The approval invariant and separation of duties.\n",
            "docs/plan.md": "Beware the temporal precedent here.\n",
        },
    )
    assert [(h.file, h.term_kind) for h in scan(root)] == [("docs/plan.md", "trap_name")]


def _kinds(root: Path) -> list[tuple[str, str]]:
    return [(h.file, h.term_kind) for h in scan(root)]


def test_lowercase_scenario_id_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"source/README.md": "| `s22.example.ts` | the worked example |\n"})
    assert _kinds(root) == [("source/README.md", "scenario_id")]


def test_id_beside_an_underscore_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"source/t.py": "def test_s22() -> None: ...\nS22_EXAMPLE = 1\n"})
    assert [h.line for h in scan(root)] == [1, 2]


def test_long_form_scenario_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"docs/a.md": "As Scenario 5 shows.\n"})
    assert _kinds(root) == [("docs/a.md", "scenario_id")]


def test_customer_alias_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"docs/a.md": "Acme asked for more.\n"})
    assert len(scan(root)) == 1


def test_ticket_id_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"source/state.py": "# the stream for SR-38655\n"})
    assert len(scan(root)) == 1


def test_corpus_variant_name_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"source/r.py": 'CORPORA = {"missing-contract-evidence": 1}\n'})
    assert _kinds(root) == [("source/r.py", "corpus_name")]


def test_undecodable_file_is_a_hit(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/blob.bin").write_bytes(b"\xff\xfe\x00\x81 not utf-8")
    assert scan(tmp_path) == [Hit(file="docs/blob.bin", line=0, term_kind="unscannable")]


def test_an_empty_term_source_fails_closed(tmp_path: Path, truth_copy: Path) -> None:
    # truth_copy is <tmp>/truth; the repo root has no README trap table and no attack cases
    (tmp_path / "README.md").write_text("# No trap table here\n")
    root = _tree(tmp_path / "bundle", {"docs/a.md": "clean\n"})
    with pytest.raises(ScanError, match="trap_name"):
        scan(root, repo=tmp_path)


def test_org_content_is_what_the_caller_names(tmp_path: Path) -> None:
    root = _tree(
        tmp_path,
        {
            "inputs/northstar/documents/memo.md": "From Sarah Chen.\n",
            "docs/org-memo.md": "From Sarah Chen.\n",
        },
    )
    hits = scan(root, org_content=frozenset({"docs/org-memo.md"}))
    assert [(h.file, h.term_kind) for h in hits] == [
        ("inputs/northstar/documents/memo.md", "person")
    ]


def test_condition_ids_are_not_attack_ids(tmp_path: Path) -> None:
    # The service numbers conditions c1, c2, ...; the lab's attack cases are C01-C24, upper case.
    root = _tree(
        tmp_path, {"source/conditions.py": '    """A condition id\'s number: `c12` is 12."""\n'}
    )
    assert scan(root) == []
