"""Spike E0: check what Opik does with OTLP-ingested traces (the lab's local instance only).

Run with OPIK_CONFIG_PATH pointing at the spike's own config (never ~/.opik.config, which may point
at the user's cloud workspace) and OPIK_SENTRY_ENABLE=false.

    python -I e0_check_opik.py structure | code-metric | judge | dataset | rule-create | rule-poll

Each step prints one JSON object. `judge` needs OPENAI_API_KEY and makes one judge call.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import GEval, base_metric, score_result

PROJECT = "e0-spike"
JUDGE_MODEL = "openai/gpt-5-nano"
RECORD = (
    "Decision D-E0-0001, discount_approval, outcome route_to_approver: the requested 12% is above "
    "the 10% limit for a sales rep in the policy in force; the sales director must approve."
)


def _guard() -> None:
    path = os.environ.get("OPIK_CONFIG_PATH", "")
    if not path or path.endswith(".opik.config") and "/scratchpad/" not in path:
        sys.exit("refusing: OPIK_CONFIG_PATH must name the spike's own config")
    if os.environ.get("OPIK_SENTRY_ENABLE", "").lower() != "false":
        sys.exit("refusing: set OPIK_SENTRY_ENABLE=false")


def _client() -> opik.Opik:
    _guard()
    c = opik.Opik(project_name=PROJECT)
    if "127.0.0.1" not in c.config.url_override:
        sys.exit(f"refusing: client points at {c.config.url_override}")
    return c


def _agent_traces(c: opik.Opik) -> list[Any]:
    ts = c.search_traces(project_name=PROJECT, max_results=50)
    return sorted(
        (t for t in ts if (t.name or "").startswith("invoke_agent")), key=lambda t: t.start_time
    )


def _output_text(t: Any) -> str:
    return json.dumps(t.output) if t.output is not None else ""


class MentionsApproval(base_metric.BaseMetric):
    """A code metric: the agent's answer says the decision needs approval."""

    def __init__(self, name: str = "e0_mentions_approval") -> None:
        super().__init__(name=name, track=False)

    def score(self, output: str, **ignored: Any) -> score_result.ScoreResult:
        ok = "approv" in output.lower()
        return score_result.ScoreResult(
            name=self.name,
            value=1.0 if ok else 0.0,
            reason="mentions approval" if ok else "no approval",
        )


def structure(c: opik.Opik) -> dict[str, Any]:
    out: dict[str, Any] = {"traces": []}
    for t in _agent_traces(c)[:2]:
        spans = c.search_spans(project_name=PROJECT, trace_id=t.id, max_results=100)
        ids = {s.id for s in spans}
        orphans = [s.name for s in spans if s.parent_span_id and s.parent_span_id not in ids]
        out["traces"].append(
            {
                "id": t.id,
                "name": t.name,
                "has_input": t.input is not None,
                "has_output": t.output is not None,
                "spans": len(spans),
                "orphans": orphans,
                "error": bool(getattr(t, "error_info", None)),
                "span_view": sorted(
                    (
                        s.name,
                        s.type,
                        s.model,
                        s.provider,
                        (s.usage or {}).get("prompt_tokens"),
                        (s.usage or {}).get("completion_tokens"),
                    )
                    for s in spans
                ),
                "decide_metadata_keys": sorted(
                    k
                    for s in spans
                    if s.name and s.name.startswith("owm.decide")
                    for k in (s.metadata or {})
                ),
            }
        )
    return out


def code_metric(c: opik.Opik) -> dict[str, Any]:
    t = _agent_traces(c)[0]
    r = MentionsApproval().score(output=_output_text(t))
    c.log_traces_feedback_scores(
        [
            {
                "id": t.id,
                "name": r.name,
                "value": r.value,
                "reason": r.reason,
                "project_name": PROJECT,
            }
        ]
    )
    c.flush()
    time.sleep(2)
    back = c.get_trace_content(t.id).feedback_scores or []
    return {"logged": r.value, "read_back": [(f.name, f.value) for f in back]}


def judge(c: opik.Opik) -> dict[str, Any]:
    t = _agent_traces(c)[0]
    g = GEval(
        task_introduction="You check that an agent's explanation of a decision is faithful to "
        "the decision record.",
        evaluation_criteria="Score 1 if every figure and reason in OUTPUT appears in the record "
        "below, else 0. Record: " + RECORD,
        model=JUDGE_MODEL,
        track=False,
    )
    r = g.score(output=_output_text(t))
    c.log_traces_feedback_scores(
        [
            {
                "id": t.id,
                "name": "e0_judge_faithful",
                "value": r.value,
                "reason": (r.reason or "")[:300],
                "project_name": PROJECT,
            }
        ]
    )
    c.flush()
    time.sleep(2)
    back = c.get_trace_content(t.id).feedback_scores or []
    return {"judge_value": r.value, "read_back": [(f.name, f.value) for f in back]}


def dataset(c: opik.Opik) -> dict[str, Any]:
    t = _agent_traces(c)[0]
    ds = c.get_or_create_dataset(name="e0-spike")
    ds.insert(
        [
            {
                "input": t.input,
                "expected_output": "routes to approval",
                "source_trace_id": t.id,
                "trace_output": _output_text(t),
            }
        ]
    )
    res = evaluate(
        dataset=ds,
        task=lambda item: {"output": item["trace_output"]},
        scoring_metrics=[MentionsApproval()],
        experiment_name="e0-from-otlp-trace",
        project_name=PROJECT,
        verbose=0,
    )
    scores = [s.value for tr in res.test_results for s in tr.score_results]
    return {
        "dataset_items": len(ds.get_items()),
        "experiment": res.experiment_name,
        "scores": scores,
    }


RULE_METRIC = """
from typing import Any
from opik.evaluation.metrics import base_metric, score_result

class E0RuleMentionsApproval(base_metric.BaseMetric):
    def __init__(self, name: str = "e0_rule_mentions_approval"):
        self.name = name

    def score(self, output: Any, **ignored_kwargs: Any):
        ok = "approv" in str(output).lower()
        return score_result.ScoreResult(value=1.0 if ok else 0.0, name=self.name,
                                        reason="rule: mentions approval" if ok else "rule: no")
"""


def rule_create(c: opik.Opik) -> dict[str, Any]:
    from opik.rest_api.types import (
        AutomationRuleEvaluatorWrite_UserDefinedMetricPython,
        UserDefinedMetricPythonCodeWrite,
    )

    project = c.get_project(c.rest_client.projects.retrieve_project(name=PROJECT).id)
    c.rest_client.automation_rule_evaluators.create_automation_rule_evaluator(
        request=AutomationRuleEvaluatorWrite_UserDefinedMetricPython(
            name="e0 rule: mentions approval",
            project_ids=[project.id],
            sampling_rate=1.0,
            enabled=True,
            trigger_scope="production",
            action="evaluator",
            code=UserDefinedMetricPythonCodeWrite(
                metric=RULE_METRIC, arguments={"output": "output"}
            ),
        )
    )
    return {"rule_created_on_project": project.id}


def rule_poll(c: opik.Opik) -> dict[str, Any]:
    deadline = time.time() + 120
    while time.time() < deadline:
        hits = []
        for t in _agent_traces(c):
            full = c.get_trace_content(t.id)
            for f in full.feedback_scores or []:
                if f.name == "e0_rule_mentions_approval":
                    hits.append((t.id, f.value))
        if hits:
            return {"rule_scores": hits}
        time.sleep(5)
    return {"rule_scores": [], "note": "no rule score within 120s"}


def main(argv: list[str]) -> int:
    steps = {
        "structure": structure,
        "code-metric": code_metric,
        "judge": judge,
        "dataset": dataset,
        "rule-create": rule_create,
        "rule-poll": rule_poll,
    }
    c = _client()
    print(json.dumps(steps[argv[0]](c), default=str, indent=1))
    c.end()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
