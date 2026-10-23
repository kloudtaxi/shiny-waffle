"""The private scan (lab plan L1.3): truth-derived terms are caught, and never written down."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from prototype_bundle.scan import Hit, scan


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
    # The org's own documents may name its people and requests (spec §11.3); a lab marker such as
    # a scenario id must still never appear there.
    root = _tree(
        tmp_path,
        {
            "inputs/northstar/documents/memo.md": "From Sarah Chen about DR-9001.\n",
            "inputs/northstar/structured/notes.csv": "id,note\n1,see S05\n",
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
