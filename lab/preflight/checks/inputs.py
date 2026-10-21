"""The inputs check: every id a question names is in the evidence for its corpus (G-36)."""

from __future__ import annotations

from preflight.config import InputsConfig
from preflight.observe.inputs import InputsObservation, appears
from preflight.record import CheckResult, Value

_SOURCE = "questions file + evidence"


def check_inputs(obs: InputsObservation, cfg: InputsConfig) -> CheckResult:
    """Fail when a question names an id its corpus's evidence does not hold."""
    problems: list[str] = []
    if not obs.header_ok:
        problems.append("questions file header is not id, corpus, process, question")
    for corpus, n in obs.file_counts.items():
        if n == 0:
            problems.append(f"corpus {corpus} has no evidence files")
    missing = 0
    unknown: set[str] = set()
    n_ids = 0
    n_supplied = 0
    for q, ids, supplied in zip(obs.questions, obs.ids, obs.supplied, strict=True):
        n_ids += len(ids)
        n_supplied += len(supplied)
        if q.corpus not in cfg.evidence:
            if q.corpus not in unknown:
                unknown.add(q.corpus)
                problems.append(f"corpus {q.corpus} has no evidence entry")
            continue
        text = obs.corpus_text[q.corpus]
        for ident in ids:
            if ident in supplied or appears(ident, text):
                continue
            missing += 1
            problems.append(f"{q.id} names {ident}, not in {q.corpus}'s evidence")
    if problems:
        summary = f"{missing} ids missing" if missing else f"{len(problems)} problems"
        return CheckResult(name="inputs", status="fail", summary=summary, problems=problems)
    summary = (
        f"{len(obs.questions)} questions · {n_ids} ids · every id found in its corpus's evidence"
    )
    if n_supplied:
        summary += f"; {n_supplied} supplied by their questions"
    return CheckResult(name="inputs", status="pass", summary=summary, values=inputs_values(obs))


def inputs_values(obs: InputsObservation) -> list[Value]:
    """The values this check observed."""

    def v(field: str, label: str, value: object, compare: str = "record") -> Value:
        return Value.model_validate(
            {
                "field": field,
                "label": label,
                "group": "inputs",
                "value": value,
                "source": _SOURCE,
                "state": "read",
                "compare": compare,
            }
        )

    out = [v("inputs.questions_sha256", "questions sha256", obs.questions_sha256, "equal")]
    out += [
        v(f"inputs.evidence_tree.{c}", f"evidence tree ({c})", h, "equal")
        for c, h in obs.tree_hash.items()
    ]
    out.append(v("inputs.questions", "questions", len(obs.questions)))
    out.append(v("inputs.ids", "ids named", sum(len(i) for i in obs.ids)))
    supplied = [
        f"{q.id}: {ident} ({key})"
        for q, s in zip(obs.questions, obs.supplied, strict=True)
        for ident, key in s.items()
    ]
    out.append(v("inputs.supplied", "ids supplied by questions", supplied))
    return out
