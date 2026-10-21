"""The inputs check: every id a question names must be in its corpus's evidence."""

from __future__ import annotations

from pathlib import Path

from preflight.checks.inputs import check_inputs, inputs_values
from preflight.config import InputsConfig
from preflight.observe.inputs import (
    appears,
    evidence_tree_hash,
    find_ids,
    observe_inputs,
    supplied_ids,
)

PATS = [r"\bCRM-\d{4}\b", r"\bDR-\d{4}\b", r"\bCR-\d{4}\b", r"\bSR-\d{5}\b", r"\bNS-[A-Z0-9]+\b"]
EXAM_EVIDENCE = {
    "base": ["dataset/evidence"],
    "missing-contract-evidence": ["dataset/evidence-variants/missing-contract-evidence"],
    "missing-guarantee-evidence": ["dataset/evidence-variants/missing-guarantee-evidence"],
}
HEADER = "id\tcorpus\tprocess\tquestion"


def _setup(
    tmp_path: Path,
    rows: list[str],
    evidence_text: bytes = b"CRM-0001,Acme\n",
    header: str = HEADER,
) -> tuple[InputsConfig, Path]:
    run = tmp_path / "runs" / "r"
    run.mkdir(parents=True)
    (run / "questions.tsv").write_text(header + "\n" + "\n".join(rows) + "\n")
    ev = tmp_path / "evidence"
    ev.mkdir()
    (ev / "crm.csv").write_bytes(evidence_text)
    cfg = InputsConfig(
        id_patterns=PATS, supplied_keys=["request_id"], evidence={"base": ["evidence"]}
    )
    return cfg, run


def test_g36_ids_missing_from_the_evidence_fail(tmp_path: Path) -> None:
    cfg, run = _setup(
        tmp_path,
        [
            "S01\tbase\tp\tCompare CRM-0001 with CRM-0002 and CRM-0002 again",
            "S02\tbase\tp\tWhat about CRM-0003?",
        ],
    )
    r = check_inputs(observe_inputs(cfg, run, tmp_path), cfg)
    assert r.status == "fail"
    assert r.problems == [
        "S01 names CRM-0002, not in base's evidence",
        "S02 names CRM-0003, not in base's evidence",
    ]
    assert r.summary == "2 ids missing"


def test_a_whole_token_match() -> None:
    assert appears("NS-500", "sku NS-500,") and not appears("NS-500", "sku NS-5000")
    assert not appears("NS-500", "sku NS-500-B")


def test_find_ids_keeps_first_appearance_order_once() -> None:
    assert find_ids("DR-1111 CRM-0001 DR-1111", PATS) == ["DR-1111", "CRM-0001"]


def test_supplied_request_ids_are_reported_not_failed(tmp_path: Path) -> None:
    q = 'S09\tbase\tp\tDecide {"request_id": "DR-9101", "account_id": "CRM-0001"}'
    cfg, run = _setup(tmp_path, [q])
    r = check_inputs(observe_inputs(cfg, run, tmp_path), cfg)
    assert r.status == "pass"
    supplied = next(v for v in r.values if v.field == "inputs.supplied")
    assert supplied.value == ["S09: DR-9101 (request_id)"]
    assert r.summary.endswith("; 1 supplied by their questions")


def test_a_supplied_record_s_other_ids_are_still_checked(tmp_path: Path) -> None:
    q = 'S09\tbase\tp\tDecide {"request_id": "DR-9101", "account_id": "CRM-9999"}'
    cfg, run = _setup(tmp_path, [q])
    assert check_inputs(observe_inputs(cfg, run, tmp_path), cfg).problems == [
        "S09 names CRM-9999, not in base's evidence"
    ]


def test_supplied_ids_skips_bad_json_and_non_strings() -> None:
    text = '{bad json} {"request_id": 5} {"request_id": "DR-1"}'
    assert supplied_ids(text, ["request_id"]) == {"DR-1": "request_id"}


def test_the_b20_exam_questions_pass(repo: Path) -> None:
    run = repo / "runs/2026-10-17-b20-northstar-exam"
    cfg = InputsConfig(id_patterns=PATS, supplied_keys=["request_id"], evidence=EXAM_EVIDENCE)
    r = check_inputs(observe_inputs(cfg, run, repo), cfg)
    assert r.status == "pass", r.problems
    supplied = next(v for v in r.values if v.field == "inputs.supplied").value
    assert (
        isinstance(supplied, list)
        and supplied
        and all(isinstance(s, str) and "(request_id)" in s for s in supplied)
    )


def test_the_g51_questions_pass_with_nothing_supplied(repo: Path) -> None:
    run = repo / "runs/2026-10-19-sor-reads-arms"
    cfg = InputsConfig(
        id_patterns=PATS, supplied_keys=["request_id"], evidence={"base": ["dataset/evidence"]}
    )
    r = check_inputs(observe_inputs(cfg, run, repo), cfg)
    assert r.status == "pass"
    assert next(v for v in r.values if v.field == "inputs.supplied").value == []


def test_latin1_evidence_does_not_crash(tmp_path: Path) -> None:
    cfg, run = _setup(
        tmp_path,
        ["S01\tbase\tp\tAbout CRM-0001"],
        evidence_text="CRM-0001,Müller".encode("latin-1"),
    )
    assert check_inputs(observe_inputs(cfg, run, tmp_path), cfg).status == "pass"


def test_manifest_and_dotfiles_are_outside_the_tree_hash(tmp_path: Path) -> None:
    ev = tmp_path / "ev"
    ev.mkdir()
    (ev / "a.md").write_text("x")
    h = evidence_tree_hash([ev], tmp_path)
    (ev / "MANIFEST.yaml").write_text("hints")
    (ev / ".DS_Store").write_bytes(b"\0")
    assert evidence_tree_hash([ev], tmp_path) == h
    (ev / "a.md").write_text("y")
    assert evidence_tree_hash([ev], tmp_path) != h


def test_manifest_text_is_not_evidence(tmp_path: Path) -> None:
    cfg, run = _setup(tmp_path, ["S01\tbase\tp\tAbout CRM-7777"])
    (tmp_path / "evidence" / "MANIFEST.yaml").write_text("CRM-7777")
    assert check_inputs(observe_inputs(cfg, run, tmp_path), cfg).status == "fail"


def test_a_wrong_header_or_unknown_corpus_fails(tmp_path: Path) -> None:
    cfg, run = _setup(tmp_path, ["S01\tbase\tp\tCRM-0001"], header="id\tquestion")
    obs = observe_inputs(cfg, run, tmp_path)
    assert obs.header == ["id", "question"] and obs.questions == []
    assert check_inputs(obs, cfg).problems[0] == (
        "questions file header has no corpus column (it needs id, corpus, question)"
    )
    cfg, run = _setup(tmp_path / "b", ["S01\tother\tp\tCRM-0001"])
    r = check_inputs(observe_inputs(cfg, run, tmp_path / "b"), cfg)
    assert r.status == "fail"
    assert "corpus other has no evidence entry" in r.problems


def test_values(tmp_path: Path) -> None:
    cfg, run = _setup(tmp_path, ["S01\tbase\tp\tCRM-0001"])
    vals = {v.field: v for v in inputs_values(observe_inputs(cfg, run, tmp_path))}
    assert set(vals) == {
        "inputs.questions_sha256",
        "inputs.evidence_tree.base",
        "inputs.questions",
        "inputs.ids",
        "inputs.supplied",
    }
    assert vals["inputs.questions_sha256"].compare == "equal"
    assert vals["inputs.evidence_tree.base"].label == "evidence tree (base)"
    assert vals["inputs.questions"].value == 1 and vals["inputs.ids"].value == 1


def test_supplied_ids_reads_nested_and_brace_bearing_records() -> None:
    nested = 'x {"request_id": "DR-9101", "meta": {"a": 1}} y'
    assert supplied_ids(nested, ["request_id"]) == {"DR-9101": "request_id"}
    braced = 'x {"request_id": "DR-9102", "note": "a } b { c"} y'
    assert supplied_ids(braced, ["request_id"]) == {"DR-9102": "request_id"}
    assert supplied_ids('{oops {"request_id": "DR-1"}', ["request_id"]) == {"DR-1": "request_id"}


def test_a_nested_supplied_record_is_not_reported_missing(tmp_path: Path) -> None:
    q = 'S09\tbase\tp\tDecide {"request_id": "DR-9101", "meta": {"a": 1}}'
    cfg, run = _setup(tmp_path, [q])
    assert check_inputs(observe_inputs(cfg, run, tmp_path), cfg).status == "pass"


def test_a_corpus_with_no_evidence_files_fails(tmp_path: Path) -> None:
    cfg, run = _setup(tmp_path, ["S01\tbase\tp\tCRM-0001"])
    cfg = InputsConfig(
        id_patterns=PATS, supplied_keys=["request_id"], evidence={"base": ["nowhere"]}
    )
    r = check_inputs(observe_inputs(cfg, run, tmp_path), cfg)
    assert r.status == "fail"
    assert "corpus base has no evidence files" in r.problems


# --- final review (F-2): the Utopia questions format -------------------------------------------

LUNA = "runs/2026-10-13-utopia-aad5b06+c4da9cc-luna-scale-large"
LUNA_KBS = {  # its notes.md: the base and the missing-contract knowledge bases
    "01a136fa-8e1d-77c0-b01d-bfc6423990b4": ["dataset/evidence"],
    "01a136fa-a00d-7421-b90b-4ad99714585b": ["dataset/evidence-variants/missing-contract-evidence"],
}


def test_the_utopia_questions_format_is_read_by_column_name(repo: Path) -> None:
    run = repo / LUNA
    assert (run / "questions.tsv").read_text().splitlines()[0].split("\t") == [
        "id",
        "kb",
        "question",
    ]
    cfg = InputsConfig(
        id_patterns=PATS, columns={"corpus": "kb"}, supplied_keys=["request_id"], evidence=LUNA_KBS
    )
    obs = observe_inputs(cfg, run, repo)
    assert [q.id for q in obs.questions][:2] == ["S01", "S02"] and len(obs.questions) == 10
    assert {q.corpus for q in obs.questions} == set(LUNA_KBS)
    r = check_inputs(obs, cfg)
    assert r.status == "pass", r.problems
    assert r.summary.startswith("10 questions · ")


def test_the_utopia_format_without_columns_fails_on_the_header(repo: Path) -> None:
    cfg = InputsConfig(id_patterns=PATS, evidence=LUNA_KBS)
    r = check_inputs(observe_inputs(cfg, repo / LUNA, repo), cfg)
    assert r.problems == [
        "questions file header has no corpus column (it needs id, corpus, question)"
    ]


def test_a_last_question_column_may_hold_tabs(tmp_path: Path) -> None:
    cfg, run = _setup(tmp_path, ["S01\tbase\tp\tAbout\tCRM-0001\tand CRM-0002"])
    obs = observe_inputs(cfg, run, tmp_path)
    assert obs.questions[0].text == "About\tCRM-0001\tand CRM-0002"
    assert check_inputs(obs, cfg).problems == ["S01 names CRM-0002, not in base's evidence"]


def test_columns_may_come_in_any_order(tmp_path: Path) -> None:
    cfg, run = _setup(tmp_path, ["CRM-0001 and CRM-0009\tS01\tbase"], header="question\tid\tcorpus")
    obs = observe_inputs(cfg, run, tmp_path)
    assert obs.questions[0].id == "S01" and obs.questions[0].corpus == "base"
    assert check_inputs(obs, cfg).problems == ["S01 names CRM-0009, not in base's evidence"]


def test_counts_in_summaries_agree_with_their_number(tmp_path: Path) -> None:  # F-14
    cfg, run = _setup(tmp_path, ["S01\tbase\tp\tCRM-0001"])
    assert check_inputs(observe_inputs(cfg, run, tmp_path), cfg).summary.startswith(
        "1 question · 1 id · "
    )
    cfg, run = _setup(tmp_path / "b", ["S01\tbase\tp\tCRM-0001", "S02\tbase\tp\tCRM-0001 CRM-0009"])
    r = check_inputs(observe_inputs(cfg, run, tmp_path / "b"), cfg)
    assert r.summary == "1 id missing"
    cfg, run = _setup(tmp_path / "c", ["S01\tbase\tp\tCRM-0001", "S02\tbase\tp\tCRM-0001"])
    assert check_inputs(observe_inputs(cfg, run, tmp_path / "c"), cfg).summary.startswith(
        "2 questions · 2 ids · "
    )
    cfg, run = _setup(tmp_path / "d", ["S01\tother\tp\tx"])
    assert check_inputs(observe_inputs(cfg, run, tmp_path / "d"), cfg).summary == "1 problem"
