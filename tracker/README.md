# Northstar Lab Ledger

The experiment tracker, published at <https://claude.ai/artifact/FsSXn3ADwvDgBzG85b3Vyq>
(private to its owner; share it from the page's Share menu).

It shows a results matrix (scenario × condition) with grade chips. Pick any cell to read
the answer, the answer key and the reader's tool calls, and to grade it against the runbook
step 8 rubric. There's also a findings log and a conditions table. Your grades and findings
are stored in the artifact's database, so Claude can read them back when the experiment
resumes.

## Data

`build_seed.py <run folder>` compiles a run into `seed/<collection>.json` plus one file per
document under `seed/docs/`. Claude writes those into the artifact's database with
`ArtifactData` batch writes (up to 50 per batch).

| Collection | Written by | Shape |
|---|---|---|
| `experiments` | seed | status, next steps, commits, docs |
| `conditions` | seed | reader, tools, graph state, turns, spend |
| `scenarios` | seed | question, as-of date, answer key, traps |
| `answers` | seed | `inputs` / `outputs` / `expectations` (an `mlflow.genai.evaluate` row) + Claude's provisional grade |
| `grades` | the page | human rubric (outcome, approver, basis, time, honesty), overall, note — keyed by answer id; **never reseeded** |
| `findings` | seed + the page | category, title, body, status, evidence paths |

Answer ids are `<experiment>~<condition>~<scenario>~r<repeat>`. A repeat run adds `~r2`,
`~r3` documents and the matrix shows one chip per repeat, with no page change.

Access rules: everyone who can open the page reads everything; only editors write the run
data; contributors can write `grades` and `findings`.

## Moving to MLflow later

See `docs/tracking-mlflow-review.md`. Each `answers` document is already an evaluate row, and
each `grades` document maps to `mlflow.log_feedback` with a `HUMAN` source.
