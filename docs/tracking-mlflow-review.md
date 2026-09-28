# Tracking the experiment: MLflow review (2026-09-28)

**Question:** should the Northstar lab track its runs in MLflow
(<https://github.com/mlflow/mlflow>), or is that overkill?

**Verdict:** MLflow is the right tool at the wrong time. Build a lightweight tracker now, with
a data model in MLflow's shape, and move to MLflow when run volume or an OWM eval harness
justifies it.

The review is based on MLflow's own docs (`/mlflow/mlflow` via Context7): GenAI evaluation,
assessments, and Claude Code tracing.

## What MLflow does that we need

| Need | MLflow feature | Fit |
|---|---|---|
| Score pre-computed answers against expected results | `mlflow.genai.evaluate(data=[{inputs, outputs, expectations}], scorers=[…])` with no `predict_fn`; custom `@scorer` functions return a `Feedback` with a rationale | Good. `questions.tsv` + `answers/` + the answer key map 1:1 |
| Human grading (runbook step 8) | `mlflow.log_feedback` / `mlflow.log_expectation` with a `HUMAN` source (3.2+), or **Assessments → Add Feedback** on a trace in the UI | Good, but it's one trace at a time: 5 rubric checks × 50 answers is 250 clicks |
| See what the reader did | `mlflow autolog claude` (hooks into Claude Code) captures each `claude -p` run as a trace, with tool calls as spans | Very good for arm B, and free once enabled |
| Compare conditions | Runs, params and metrics, plus the eval results table | Adequate for metrics; there's no native scenario × condition grid |
| Automated grading | Built-in LLM judges (`Correctness`, `Guidelines`) and a judge-alignment workflow | Useful at scale, but needs an LLM API key, and none is set in this shell |
| Setup | `mlflow server --backend-store-uri sqlite:///mlflow.db` (a SQL backend is required for traces) | Easy; run it through `uvx` so MLflow stays out of the lab's dependency closure |

## Why not now

- **The unit of work is small and the output is qualitative.** There are 10 scenarios × 5
  conditions (≈ 50 answers) so far. The valuable output is *findings* about the
  foundation/OWM boundary (the silent repair of inverted edges, the identifier lost by a
  merge, the `changes` trick). MLflow has no place for findings linked to evidence.
- **The lab's key view isn't MLflow's.** We read scenario × condition matrices (A · B1 · B2 ·
  after correction) and set the experimental controls (graph state, blindness, tool
  hiding) beside the grades. In MLflow those become tags and params spread across runs.
- **Arm A isn't traced.** Utopia's in-app chat (SSE) would need hand-built spans.
- **No judge without an API key.** The subscription-based `claude -p` path we use for
  readers doesn't give MLflow's judges a model to call.

## When to switch

1. **Repeat runs and the scale arm** push the volume into the hundreds of answers. Variance
   analysis and judge pre-grading are MLflow's strengths.
2. **The OWM gets a regression eval.** Every OWM version needs scoring against the Northstar
   scenarios, and that continuous eval is exactly what `mlflow.genai.evaluate` plus
   evaluation datasets are for.

**Migration stays cheap** because the tracker stores each answer as `inputs` (question, KB,
as-of date), `outputs` (answer text, tool calls, cost), `expectations` (the answer key) and
`assessments` (human rubric grades with a rationale). That's the dataset
`mlflow.genai.evaluate` takes, and the grades map to `mlflow.log_feedback`.
