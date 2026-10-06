# Kickoff: write the build plan for the BlueLeaf lab MCP server

**For:** the agent who writes the implementation plan. **From:** the design session, 2026-10-06.
**Branch:** `skunkworks/blueleaf-mcp` (never `main`).

## Your job

Write a step-by-step implementation plan for the design in
`docs/superpowers/specs/2026-10-06-blueleaf-mcp-design.md`. Read §11, the buildability review,
before anything else in the spec.

- Use the `superpowers:writing-plans` skill if your environment has it.
- Save the plan as `docs/superpowers/plans/2026-10-06-blueleaf-mcp-plan.md` on this branch. Commit
  it and push it.
- **Write no product code.** The user runs the build separately, from your plan. A short spike that
  only checks an API is fine if you throw it away.
- **Spend nothing:** no reader calls, no live Jev calls, no Utopia.

When you're done, reply with the plan's path and five lines at most: the number of tasks, the
order, anything you couldn't resolve, and the spec items you'd change (with reasons).

## What the server is, in four lines

A local stdio MCP server for Claude Desktop with two modes:
- **experimenter** (`blueleaf-lab`): sandboxes, documents, the register, procedures, engines and
  scoring against the answer key;
- **subject** (`blueleaf-subject --arm plain|register|owm`): blind, so it must never reach the
  answer key. Three walls guarantee that: imports, files, and a seal.

Everything is over the Northstar corpus and the six sealed attack sets.

## Read first, in this order

1. `CLAUDE.md`: the lab's rules. The ones that bind you are below.
2. The spec, §11 first.
3. `lab/owm_kernel/README.md` and `lab/owm_kernel/SPEC_FORMAT.md`: the decision core and spec format.
4. `lab/owm_kernel/kernel.py`: `Evidence`, `Register` (`load` reads `<yaml>/../store`) and
   `register_screen`.
5. `lab/owm_kernel/flow.py`: `load`, and `run(spec, eng, ev, inputs, register=None)`, including
   `withhold()`.
6. `lab/decision_engine/engine.py`: `Recorder`, `Replay` (raises `KeyError` on a miss),
   `TypeSafe` (reads `TYPESAFE_API_KEY_FILE`) and `request_hash`.
7. `lab/owm_register/serve.py` (`served`, `approved_text`, `COVERAGE`) and `build_register.py` (the
   registrar and its text checks).
8. `lab/owm_standin/server.py`: an earlier stdlib MCP stand-in. It's prior art; don't extend it.
9. **The engine table and attack application to re-declare:**
   - `runs/2026-10-05-register/run_set.py`: `engines()`, eleven credit engines;
   - `runs/2026-10-05-register-all/run_all.py`: `specs()`, the discount and SLA register mappings;
   - `runs/2026-10-05-register-all/run_set_f.py`: `build()`, attack manifests; `sla_class`.
10. **The rule T5 depends on:** `runs/2026-10-06-register-fixes/check_withhold.py`, where a
    `withheld:` decision counts as routed.
11. **The graders `scoring.py` loads by path:**
    - `runs/2026-10-03-adversarial/run_reader.py`: `classify`, `scorer`;
    - `runs/2026-10-03-exp5-credit/run_reader.py`: `grade`, `scorer`;
    - `runs/2026-10-03-exp6-sla/run_reader.py`: `grade`, `people`;
    - `runs/2026-10-03-exp5-credit/run_set_c_reader.py`: `unsafe_type`;
    - how `runs/2026-10-05-register-all/run_reader_set_f.py` combines them per decision type.

## Rules that bind the plan

- **The answer key never reaches the subject side.**
  - `subject_server.py` and `service/` never import or read `scoring.py`, `truth/`,
    `dataset/answer-key/`, `dataset/evaluation/` or `site/`.
  - `subject.json` holds no outcome.
  - Tests T1, T2 and T4 prove it; put them early in the plan.
- **Secrets:** `_owm-local/` holds live credentials, including `typesafe.key`. Nothing from it goes
  into a tracked file, a commit, a log or a tool output. The server learns only the key file's path,
  from `TYPESAFE_API_KEY_FILE`. Test T7 uses a dummy key.
- **`dataset/` is never written.** It is generated and committed, and test T6 hashes it before and
  after.
- **Committed run folders are results:** never edit them. `promote` writes a new folder and refuses
  to overwrite one.
- **Leave the `dataset-*` git tags alone.** The client demo depends on them.
- **Dependencies:** the MCP SDK goes in a new `mcp` dependency group. Nothing changes in
  `src/northstar`, the dataset build or the default install.
- **Quality gates:** `uv run pytest`, `uv run ruff check`, `uv run ruff format --check` and
  `uv run mypy`. mypy is strict and must cover `lab/blueleaf_mcp` (spec §11, B9). Line length
  is 100.
- **Determinism:** no dates relative to today; decisions use each scenario's own date.

## How the plan should be shaped

1. **Walls first, as tests that fail before the code exists.** That means T1, T2, T4, T6 and T7,
   plus `service/_lab.py` (the only place that touches `sys.path`) and the mypy settings.
2. **Sandboxes:** the seeds `clean`, `set:X` and `attack:Xn`, including checking each attack set's
   seal hashes. Then document changes, and the copied register and its `store/`.
3. **Engines:** the re-declared table, then the layered Jev engine (replay, then the sandbox's
   recording, then live under the cap), then `needs_live_jev`. T5 and T9 close this step.
4. **Scoring:** the graders loaded by path. T10 closes this step.
5. **The experimenter server:** tool groups in the order of spec §4.1, each with a test through the
   in-memory MCP client (T8).
6. **The subject server and its three arms,** then the seal and its auto-lift (T3).
7. **`promote`,** then the README (the Desktop config, using the absolute path of `uv`).
8. **A manual acceptance step for the user:** spec §10, the F6 walk-through in Claude Desktop.
   Mark it as the user's step; an agent can't run Claude Desktop.

Each task should name its files, give the test to write first, give the command that proves it,
and say what is committed. Keep tasks small enough to review on their own.

## Decide or flag

- **The MCP SDK major version** (spec §11, B1): check what's current and pin it. v2 uses
  `MCPServer` and `mcp.client.Client`.
- **Arms as server-side tool sets.** Confirm that a tool can be left unregistered per arm at start-up
  in the pinned SDK.
- **The merged Jev recording.** Every `engine-calls.jsonl` and `*engine-calls*.jsonl` under `runs/`
  goes in, de-duplicated by `hash`, about 32,000 lines. Build it on first start and cache it in
  `.blueleaf/`; say how the cache is invalidated.
- **Anything in the spec you find unbuildable or ambiguous:** don't quietly redesign it. List it in
  the plan's "Spec changes proposed" section, with a recommendation.

## Done for you, when

The plan file is committed and pushed on `skunkworks/blueleaf-mcp`. Someone who has read only the
spec and the plan can build the server task by task. Every test in spec §8 (T1–T10) appears in a
task.
