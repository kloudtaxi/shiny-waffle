# Spike E0: Opik and MLflow on OTLP-ingested traces (2026-10-23)

**Status:** done.
- **Result: Opik passes every check.** The spec's choice (§9.7, the plans' LW-8) stands.
- MLflow passes the mapping and offline scoring. In open source, though, its online rules need its AI
  Gateway, which stores the provider key in MLflow, or its custom-scorer flag, which runs code with
  `exec()` in the server and no isolation.
- The judge spend was 2 calls on `openai/gpt-5-nano`, a fraction of a cent, against the cap of 4
  calls and $0.05.

## Pre-registration (written before any judge call)

- **What is tested:** spec §9.7's trace shape, sent over OTLP/HTTP to Opik 2.2.119 (local, loopback
  :5180) and MLflow 3.17.2 (local, loopback :5055, SQLite). The traces are hand-built and synthetic
  (`lab/prototype_eval/e0_emit.py`). No Northstar data is used.
- **The checks per backend:**
  1. one connected trace;
  2. the GenAI mapping (model, usage, tool spans);
  3. a code metric on an ingested trace;
  4. an LLM judge on an ingested trace;
  5. adding it to a dataset (plus an experiment);
  6. an online rule;
  7. telemetry off.
- **The judge:** the OpenAI token from the user's vault (the user's choice), read in place and never
  printed. At most 4 calls on `openai/gpt-5-nano` across both backends. Cap: $0.05.

## Results

| Check | Opik 2.2.119 | MLflow 3.17.2 |
|---|---|---|
| 1. One connected trace | ✅ 10 spans per trace, 1 root, 0 orphans | ✅ 10 spans per trace, 1 root, 0 orphans |
| 2. GenAI mapping | ✅ The `chat` spans become `llm`, with model, provider and usage. The trace input and output come from `gen_ai.input/output.messages`. Error status carries. ⚠️ The `owm.*` attributes land in span **input**, not metadata. `execute_tool` shows as `general` when no tool arguments are sent | ✅ AGENT, CHAT_MODEL and TOOL span types, with usage. The `owm.*` attributes stay attributes. Error status carries |
| 3. Code metric on an ingested trace | ✅ Logged as a feedback score and read back | ✅ `mlflow.genai.evaluate(data=[trace])` attaches it to the original trace. ⚠️ Only once `set_experiment` is called; otherwise it logs to experiment 0 and attaches nothing |
| 4. LLM judge on an ingested trace | ✅ G-Eval, 1 call; the score was attached | ✅ Guidelines judge, 1 call; scored in the run |
| 5. Dataset, plus an experiment | ✅ A dataset item built from the trace, and an experiment over it, scored | ⚠️ `merge_records([trace])` **fails**: the GenAI message list isn't a dict of inputs. A record built from the trace works |
| 6. Online rule | ✅ A Python rule runs in Opik's separate executor (network off, 256 MB). Both new OTLP traces were scored within seconds (1.0 and 0.0, as expected) | ❌ Not without more setup. Online judges must use an **AI Gateway** model, which stores the provider key in MLflow. Online custom code needs `MLFLOW_SERVER_ENABLE_CUSTOM_SCORERS`, which runs `exec()` in the server, unisolated. Not done: storing the key breaks the spike's key rule |
| Human feedback | ✅ An annotation queue holding 2 traces | ✅ `log_feedback` with a HUMAN source, on an ingested trace |
| 7. Telemetry off | ✅ The server's `OPIK_USAGE_REPORT_ENABLED=false` (confirmed in the container). ⚠️ The **SDK sends errors to Sentry by default**; `OPIK_SENTRY_ENABLE=false` turns this off | ✅ `MLFLOW_DISABLE_TELEMETRY=true`, `DO_NOT_TRACK=true` |

The judge scores (0.0 on both) mean nothing about the judges. The synthetic answer adds "Nothing is
applied until then", which isn't in the record, and `gpt-5-nano` runs only at temperature 1. The
spike tested the mechanics.

## Found on the way (for the lab's instance, LW-8)

- **Opik's upstream Compose file:**
  - It publishes the frontend on every interface, and the backend's 3003 on an ephemeral port on
    every interface.
  - Its `docker-compose.override.yaml` publishes MySQL, Redis, ClickHouse, ZooKeeper and MinIO. That
    file loads automatically unless the files are passed with `-f`.
  - The lab's override (`lab/prototype_eval/opik-compose.override.yaml`, with `opik.env`) closes all
    of these. Only `127.0.0.1:5180` is published, and a request to the LAN address is refused.
- **Opik's python-backend** runs `privileged: true` upstream (for Docker-in-Docker). With the
  process executor it runs **unprivileged** (`privileged: false`; default capability set). Its rule
  scoring still works.
- **The Opik SDK** reads `~/.opik.config` unless `OPIK_CONFIG_PATH` is set, and sends errors to
  Sentry unless `OPIK_SENTRY_ENABLE=false`.
- **LiteLLM**, which Opik's judges use, fetches a model price list from GitHub when imported, unless
  `LITELLM_LOCAL_MODEL_COST_MAP=True`.
- **Opik puts unrecognised attributes in span input.** The lab's scorers read `owm.*` there, and
  rules map arguments from `input`.
- **MLflow's server log addresses AI coding agents.** It prints a line telling them to load a
  "skill" file shipped inside MLflow (silenced by `MLFLOW_DISABLE_AGENT_HINT=1`). It is tool output,
  and nothing acted on it. It's worth knowing about when agents read logs.

## Files

- `lab/prototype_eval/e0_emit.py`: the two hand-built traces, sent to an explicit endpoint only.
- `lab/prototype_eval/e0_check_opik.py`, `e0_check_mlflow.py`: the checks, one step per command.
- `lab/prototype_eval/opik-compose.override.yaml`, `opik.env`: the lab's instance (LW-8).
- **Not committed, in the session scratchpad:**
  - the throwaway environment, about 680 MB;
  - the MLflow SQLite store;
  - small ad-hoc inspection scripts.
- **Left on the machine:**
  - Opik's checkout at `../lab-opik` (tag 2.2.119, sparse);
  - its 9 images, about 3.9 GB;
  - its stopped Compose project, `owm-lab-opik`, with its volumes, which hold only this spike's
    synthetic traces.
