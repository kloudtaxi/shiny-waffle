"""Spike E0: check what MLflow 3.17 does with OTLP-ingested traces (local server on loopback).

    python -I e0_check_mlflow.py setup | structure | evaluate | feedback | dataset |
                                  rule-create | rule-poll

Each step prints one JSON object. `evaluate` makes one judge call; the online rule makes one per
new trace. Judge calls need OPENAI_API_KEY (in the server's environment for the online rule).
MLFLOW_DISABLE_TELEMETRY must be true.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import mlflow
from mlflow.entities import AssessmentSource, AssessmentSourceType
from mlflow.genai.scorers import Guidelines, scorer

URI = "http://127.0.0.1:5055"
EXPERIMENT = "e0-spike"
JUDGE = "openai:/gpt-5-nano"
RECORD = (
    "Decision D-E0-0001, discount_approval, outcome route_to_approver: the requested 12% is above "
    "the 10% limit for a sales rep in the policy in force; the sales director must approve."
)


def _setup() -> str:
    if os.environ.get("MLFLOW_DISABLE_TELEMETRY", "").lower() != "true":
        sys.exit("refusing: set MLFLOW_DISABLE_TELEMETRY=true")
    mlflow.set_tracking_uri(URI)
    exp = mlflow.get_experiment_by_name(EXPERIMENT)
    exp_id = exp.experiment_id if exp else mlflow.create_experiment(EXPERIMENT)
    mlflow.set_experiment(experiment_id=exp_id)  # else evaluate() logs to experiment 0 and the
    return exp_id  # scores don't attach to the ingested trace


def _agent_traces(exp_id: str) -> list[Any]:
    ts = mlflow.search_traces(locations=[exp_id], return_type="list", max_results=50)
    return sorted(
        (
            t
            for t in ts
            if any(s.parent_id is None and s.name.startswith("invoke_agent") for s in t.data.spans)
        ),
        key=lambda t: t.info.request_time,
    )


@scorer
def mentions_approval(outputs: Any) -> bool:
    return "approv" in json.dumps(outputs).lower()


def structure(exp_id: str) -> dict[str, Any]:
    out: dict[str, Any] = {"traces": []}
    for t in _agent_traces(exp_id)[:2]:
        spans = t.data.spans
        ids = {s.span_id for s in spans}
        out["traces"].append(
            {
                "trace_id": t.info.trace_id,
                "state": str(t.info.state),
                "request_preview": (t.info.request_preview or "")[:120],
                "response_preview": (t.info.response_preview or "")[:120],
                "spans": len(spans),
                "roots": [s.name for s in spans if s.parent_id is None],
                "orphans": [s.name for s in spans if s.parent_id and s.parent_id not in ids],
                "span_view": [
                    (
                        s.name,
                        str(s.span_type),
                        str(s.status.status_code),
                        s.attributes.get("mlflow.chat.tokenUsage"),
                        s.attributes.get("mlflow.llm.model")
                        or s.attributes.get("gen_ai.request.model"),
                    )
                    for s in spans
                ],
                "decide_attrs": sorted(
                    k
                    for s in spans
                    if s.name.startswith("owm.decide")
                    for k in s.attributes
                    if k.startswith("owm.")
                ),
            }
        )
    return out


def evaluate(exp_id: str) -> dict[str, Any]:
    t = _agent_traces(exp_id)[0]
    judge = Guidelines(
        name="faithful_to_record",
        model=JUDGE,
        guidelines=[
            "Every figure and reason in the response appears in this decision record: " + RECORD
        ],
    )
    res = mlflow.genai.evaluate(data=[t], scorers=[mentions_approval, judge])
    time.sleep(2)
    back = mlflow.get_trace(t.info.trace_id)
    return {
        "metrics": {k: v for k, v in res.metrics.items()},
        "assessments_on_trace": [
            (a.name, getattr(a, "value", None)) for a in back.info.assessments
        ],
    }


def feedback(exp_id: str) -> dict[str, Any]:
    t = _agent_traces(exp_id)[0]
    mlflow.log_feedback(
        trace_id=t.info.trace_id,
        name="e0_human_grade",
        value=True,
        rationale="spike: a human grade on an OTLP-ingested trace",
        source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id="e0-lab"),
    )
    back = mlflow.get_trace(t.info.trace_id)
    return {
        "assessments_on_trace": [(a.name, getattr(a, "value", None)) for a in back.info.assessments]
    }


def dataset(exp_id: str) -> dict[str, Any]:
    from mlflow.genai.datasets import create_dataset

    t = _agent_traces(exp_id)[0]
    ds = create_dataset(name="e0-spike", experiment_id=[exp_id])
    ds.merge_records([t])
    return {"dataset": ds.name, "records": len(ds.to_df())}


def rule_create(exp_id: str) -> dict[str, Any]:
    from mlflow.genai.scorers import ScorerSamplingConfig

    mlflow.set_experiment(experiment_id=exp_id)
    judge = Guidelines(
        name="e0_online_mentions_approval",
        model=JUDGE,
        guidelines=["The response says whether the decision needs someone's approval."],
    )
    reg = judge.register(name="e0_online_mentions_approval", experiment_id=exp_id)
    reg.start(sampling_config=ScorerSamplingConfig(sample_rate=1.0), experiment_id=exp_id)
    return {"registered": "e0_online_mentions_approval"}


def rule_poll(exp_id: str) -> dict[str, Any]:
    deadline = time.time() + 240
    while time.time() < deadline:
        hits = []
        for t in _agent_traces(exp_id):
            for a in mlflow.get_trace(t.info.trace_id).info.assessments:
                if a.name == "e0_online_mentions_approval":
                    hits.append((t.info.trace_id, getattr(a, "value", None)))
        if hits:
            return {"rule_scores": hits}
        time.sleep(10)
    return {"rule_scores": [], "note": "no online score within 240s"}


def main(argv: list[str]) -> int:
    exp_id = _setup()
    if argv[0] == "setup":
        print(json.dumps({"experiment_id": exp_id}))
        return 0
    steps = {
        "structure": structure,
        "evaluate": evaluate,
        "feedback": feedback,
        "dataset": dataset,
        "rule-create": rule_create,
        "rule-poll": rule_poll,
    }
    print(json.dumps(steps[argv[0]](exp_id), default=str, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
