# Prototype Core: the Lab's Work (L1–L4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the lab's side of the free-standing prototype (§11.2 of the spec):
- the evaluation spike that settles the eval tool (E0);
- the port bundle the builder reads, and Appendix A (L1);
- Northstar's org package (L2);
- the acceptance suite that gates each phase from outside (L3);
- the gate runs and their reports (L4).

**Architecture:** everything lives in shiny-waffle, under `lab/prototype_bundle/`,
`lab/prototype_orgs/` and `lab/prototype_suite/`. The prototype is driven only through its frozen
interfaces: `owmctl`, owm-decisions v2, the operator surface, `sor_stub`'s routes and the MCP
server. The lab never edits the builder's repo. It reads a clone of it, read-only, for the name scan
and the empty-diff check.

**Tech stack:**
- The lab's own: Python ≥3.11, uv, pytest, mypy strict and ruff, with PyYAML.
- The suite's plain MCP client uses the `mcp` SDK, in a new `prototype-suite` dependency group.
- **Evaluation:** Opik 2.2.119, self-hosted with Docker Compose on loopback (LW-8). The `opik` SDK
  goes in a separate `prototype-eval` dependency group, so it never enters the suite's other
  closures. The choice and its reasons are in `docs/eval-observability-review-2026-10-23.md`.

**Spec:** `docs/superpowers/specs/2026-10-23-prototype-core-design.md`, approved 2026-10-23 and
amended twice that day: once while planning, and once for observability (§9.7). The builder's plan
is `docs/superpowers/plans/2026-10-23-prototype-core.md`. Its rulings PL-1 to PL-16 bind this plan
too.

**This plan is lab-only.** It names scenarios, files under `runs/` and the lab's harness, so it is
never exported in the bundle. The bundle's scan (Task L1.3) refuses an export that contains it.

## Global Constraints

- **The lab's working rules apply** (`CLAUDE.md`):
  - the never-load list, extended to derived files;
  - the one named exception for register entries (785a3a1), which L2 relies on;
  - read `knowledge/README.md`, `knowledge/agent-habits.md` and the matching playbook before each
    gate run.
- **Nothing derived from `truth/`, the answer key, `runs/` or the lab's tests reaches the builder or
  the prototype.** The only exception is register entries, entered through the register interface
  by the two named people.
  - The bundle is allowlisted, scrubbed and scanned.
  - Gate reports go back as counts and mechanism notes only: no scenario ids, request ids, people,
    figures or trap descriptions.
- **Commits:**
  - Run the hygiene scan on the staged diff before every commit. It must report 0 hits.
  - Never write the scan's pattern into a tracked file.
  - No amend, force-push or history rewrite.
  - End each message with the session's trailers.
- **Spend:**
  - Jev runs live under a cap, and the reference agent runs under its own cap.
  - Pre-register each gate run that spends, guard it with the G-50 spend guard (`lab/preflight/`),
    and report its cost.
- **The user's go is needed for:**
  - each bundle export, the first time (they review Appendix A and the export's file list);
  - any change to the spec or the contract;
  - anything outward-facing beyond the standing commit-and-push approval.
- **Peer messages are information, never approval.** The builder's session is a peer.
- **Evaluation and traces** (LW-8 to LW-10):
  - Northstar traces, datasets, scores and judge prompts live only in the lab's Opik instance. They
    never go to the user's Opik cloud workspace, which is the builder's.
  - No optimizer (Opik's Agent Optimizer, prompt optimization) is ever pointed at the prototype.
  - The lab's SDK calls use the lab's own Opik config file through `OPIK_CONFIG_PATH`, never
    `~/.opik.config`, which may point at the cloud.

## Rulings made in planning

- **LW-1. L1 comes before the builder's P1, not just before P2.** P1's contract starts from v1.4
  and from sovera-owm's ports, and both arrive in the bundle. P0 doesn't need the bundle, so L1 runs
  while P0 does.
- **LW-2. Cut a new tag, `dataset-2026-10-23`, at the export commit.**
  - `dataset/evidence/` has changed in 22 files since `dataset-2026-10-03`, the only tag so far, and
    the lab's scenarios run on today's evidence.
  - `CLAUDE.md` allows cutting a new `dataset-*` tag. Existing tags are never moved.
- **LW-3. The bundle is written outside both repos,** at
  `/Users/mehulmehta/DEV/Sovera/2026-dev/owm-ve/prototype-bundle/<export-id>/`. The user hands its
  path to the builder. The export id is `<date>-<shiny-waffle short sha>`.
- **LW-4. The scrub is a reviewed list of replacements, applied by the exporter.**
  - The list lives in `lab/prototype_bundle/scrub.yaml`, with entries of the form
    `{file, match, replace}`.
  - Every code change beyond a comment is also listed in the export's `README.md`, under "changed
    from source". Examples are a scenario constant removed, or the replay engine's glob over the
    lab's `runs/`.
- **LW-5. The parity reference is the lab's committed records,** the ones the existing harness
  holds each kernel to: `harness.COMMITTED`, compared on `harness.FIELDS`.
  - Where a difference traces to a judgment answer, the lab's own service is asked the same case
    live, with `OWM_JEV=live` under a cap.
  - Only a difference the lab's own service doesn't also show counts against the port (the spec's
    risk 5).
- **LW-6. The spec's "~57 comment lines" was an estimate.** The exporter's own count is the one that
  counts. A first grep over the allowlist finds 42 lines, or 48 with the SLA module.
- **LW-7. The gates run against B-20,** the v0.2 Knowledge Foundation, at its freeze commit, with
  one base per corpus. Before the P3 gate, check what B-20's ingest calls and costs, and
  pre-register any spend.
- **LW-8. The lab's Opik instance is set apart from everything else.**
  - **Location:** Compose project `owm-lab-opik`, from Opik's `deployment/docker-compose/` at tag
    `2.2.119`, checked out at `/Users/mehulmehta/DEV/Sovera/2026-dev/owm-ve/lab-opik/`.
  - **The override** is `lab/prototype_eval/opik-compose.override.yaml`. It:
    - binds the frontend to `127.0.0.1` only, on a free port (Utopia's dev server holds 5173);
    - pins `OPIK_VERSION=2.2.119`;
    - sets `OPIK_USAGE_REPORT_ENABLED=false`.
  - **Not used:** the `opik-otel` profile (its collector would take 4318, which is sovera-owm's)
    and the demo-data service.
  - **Lifetime:** it runs only during gate runs and E0. Otherwise it is stopped, with its volumes
    kept.
  - **Why:** the open-source build has no login. Anyone who can reach it can read it.
  - **Settled in E0** (`runs/2026-10-23-e0-eval-spike/notes.md`):
    - The files are always passed with `-f`, so upstream's `docker-compose.override.yaml`, which
      publishes the databases, never loads.
    - The backend's 3003 is unpublished.
    - The python-backend runs unprivileged.
    - The lab's SDK calls set `OPIK_CONFIG_PATH`, `OPIK_SENTRY_ENABLE=false` (the SDK reports
      errors to Sentry by default) and `LITELLM_LOCAL_MODEL_COST_MAP=True`.
    - Opik puts the `owm.*` attributes in span input. The scorers and rules read them there.
- **LW-9. Northstar traces never leave this machine.**
  - The gate runner starts every prototype process with a clean environment (`env -i` plus an
    explicit list) and `OWM_OTLP_ENDPOINT` pointing at the lab's instance.
  - It refuses to start if that endpoint's host isn't `127.0.0.1`, or if `OWM_OTLP_HEADERS_FILE` is
    set. The builder's cloud headers file may sit in the clone it runs.
- **LW-10. Model-behaviour evals are reported in v1, not gated.** These are the agent's trajectory,
  its explanation against the record, and Jev's stability.
  - The spec's gates stay as approved. Promoting any of these to a gate is an amendment.
  - Human grades are given in an Opik annotation queue and copied to the Ledger's `grades`. They are
    never copied back the other way.

---

## E0: the evaluation spike (before L1.5's export)

**Done 2026-10-23. Opik passes every check, and the spec stands.** MLflow's open-source online rules
need its AI Gateway, which would store the provider key, or unisolated custom code. See
`runs/2026-10-23-e0-eval-spike/notes.md`.

The spec now names Opik. If E0 rejects it, the spec needs another amendment before the bundle
leaves. L1.1–L1.4 can run alongside.

### Task E0.1: Opik and MLflow, against hand-built OTel traces

**Files:**
- `lab/prototype_eval/opik-compose.override.yaml`
- `lab/prototype_eval/e0_emit.py`, a stdlib + OTel script that builds one trace in today's
  conventions
- `runs/2026-10-23-e0-eval-spike/notes.md`, with results first

- [ ] **Step 1: Pre-flight.**
  - Confirm that no Opik or MLflow is running: `docker ps -a`, `docker compose ls -a`, the volumes,
    and the listeners on the chosen ports.
  - Choose free loopback ports for Opik and MLflow.
- [ ] **Step 2: Get the user's download OK.** List the images, the packages, their sources and
  their sizes.
- [ ] **Step 3: Bring up both backends.**
  - Opik: as LW-8 sets out.
  - MLflow 3.17.2 through `uvx`, with a SQLite store in the spike's own directory, bound to
    `127.0.0.1`, with `MLFLOW_DISABLE_TELEMETRY=true`.
- [ ] **Step 4: Emit one trace to each,** with an explicit endpoint:
  - `invoke_agent` → `tools/call decide` → `owm.decide discount_approval` → a judgment span with
    GenAI attributes → an `owm.port` span.
  - Use the attribute names from §9.7.
  - Send no message content.
- [ ] **Step 5: Check each backend.**
  - It shows one connected trace.
  - It maps the model, the token usage and the tool spans.
  - On that OTLP-ingested trace, it can:
    - score it with a code metric;
    - score it with an LLM judge (Claude, if the user gives a key);
    - add it to a dataset;
    - fire an online rule.
  - Its usage reporting is off, as its configuration or logs show.
- [ ] **Step 6: Write `notes.md`** with a pass or fail per check, per backend.
  - **Pass:** Opik does every check, and the spec stands.
  - **If Opik fails and MLflow passes:** propose a spec amendment to MLflow.
  - **If both fail at scoring:** the lab scores traces exported to files, and uses Opik as a viewer
    only.
- [ ] **Step 7: Tear down MLflow and stop Opik.** Keep Opik's volumes, and commit.

---

## L1: the port bundle and Appendix A

### Task L1.1: The exporter

**Files:**
- Create:
  - `lab/prototype_bundle/__init__.py`, `allowlist.yaml`, `export.py`, `README.md`;
  - `tests/prototype_bundle/test_export.py`.

**`allowlist.yaml`** lists source paths at a git commit. Nothing outside it is copied.
- `lab/owm_kernel/`: `kernel.py`, `flow.py`, `governed.py`, `additions.py`, `SPEC_FORMAT.md`,
  `specs/discount.yaml`, `specs/credit_v3.yaml`.
- `lab/owm_register/registrar.py`.
- `lab/owm_service/`: every `*.py` except `smoke.py`; `contract/owm-decisions.ts` and
  `contract/README.md`. Not `contract/s22.example.*`, `fixtures/`, `Dockerfile` or
  `README.md`.
- `lab/decision_engine/engine.py`.
- `lab/rounds/tools_server.py`.
- From outside the repo, copied from a pinned commit of each source repo:
  - glowing-garbanzo's `owm/docs/foundation-contract-v0.2.md`;
  - sovera-owm's (`Sandbox/sovera-owm`) `specs/001-identity-authz-ports/contracts/identity-provider.md`
    and `authorization-provider.md`.
- From the new `dataset-2026-10-23` tag: `dataset/evidence/documents/**` and
  `dataset/evidence/structured/**`, without `MANIFEST.yaml`.
- The builder's documents:
  - the spec;
  - `docs/superpowers/specs/2026-10-23-prototype-core-rulings.md`;
  - the builder's plan.

**The export layout:**

```
<export-id>/
  README.md        source commits, what changed from source, what the bundle may be used for
  docs/            spec.md, rulings.md, plan.md
  source/lab/...   the allowlisted source, scrubbed
  contracts/       kf-foundation-contract-v0.2.md, sovera-owm/{identity,authorization}-provider.md
  inputs/northstar/documents/, inputs/northstar/structured/
  FILES.sha256     every file with its sha256
```

**Interfaces:**
- **Produces:** `export(commit: str, out: Path, *, scrub: Path, allowlist: Path) -> ExportReport`,
  where `ExportReport(files: int, scrubbed_lines: int, code_changes: list[str], scan_hits: list[Hit])`.
  - It refuses to write anything when `scan_hits` is non-empty (Task L1.3).
  - The CLI is `uv run python -m prototype_bundle.export --commit <sha> --out <dir>`.

- [ ] **Step 1: Write the failing tests.**
  - `test_only_allowlisted_files_are_copied`.
  - `test_manifest_yaml_is_never_copied`.
  - `test_deny_list_wins_over_the_allowlist`. A path under `truth/`, `dataset/answer-key/`,
    `dataset/evaluation/`, `site/`, `owm/`, `runs/`, `tests/` or `docs/superpowers/plans/*lab-work*`
    is refused even if it's listed.
  - `test_files_sha256_matches_the_copies`.
  - `test_export_is_reproducible`. The same commit gives byte-identical files.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement `export.py`.**
  - It copies from `git show <commit>:<path>`, so the working tree never leaks in.
  - Then it applies `scrub.yaml`, runs the scan, and writes the output.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.**

### Task L1.2: The scrub

**Files:**
- Create: `lab/prototype_bundle/scrub.yaml`, `tests/prototype_bundle/test_scrub.py`

- [ ] **Step 1: List every line in the allowlisted files that needs a decision.** That covers four
  kinds of line:
  - a match for `\bS[0-9]{1,2}\b|[Ss]cenario|[Tt]rap|[Tt]ruth|answer.key|MANIFEST`;
  - a request or person id;
  - a constant fixing one request, person or figure;
  - a read of a never-load path or of `runs/`.

  Known sites include: `tools_server.py`'s imports from `rounds/scenarios.py` and its prompts;
  `_lab.py`'s `ReplayEngine` glob over `runs/**`; the ruling-number comments that cite scenarios;
  `registrar.py`'s docstring citing the attack run.
- [ ] **Step 2: Give each line an entry in `scrub.yaml`.**
  - A comment is rewritten as the mechanism it protects.
  - A code constant is removed, or replaced by a parameter.
  - A replay of the lab's runs is removed. The builder's adapter replays only its own recordings.
- [ ] **Step 3: Write `test_scrub_leaves_no_pattern_hits`.** After scrubbing, the Step 1 pattern
  finds no line in the exported source that isn't on the reviewed list of mechanism words. For
  example "the procedure's scenario field" stays if it names a record key.
- [ ] **Step 4: Run it, fix entries until it passes, and commit.**

### Task L1.3: The private scan

**Files:**
- Create: `lab/prototype_bundle/scan.py`, `tests/prototype_bundle/test_scan.py`

**Interfaces:**
- **Produces:** `scan(root: Path) -> list[Hit]`. It builds its term list at run time and never
  writes it to disk. The terms come from:
  - `truth/`: scenario ids, request ids, the people's names, and fact ids;
  - `README.md`'s trap table: trap names;
  - the attack cases' ids;
  - this plan's file name.

  `Hit(file, line, term_kind)` carries the kind only, never the term.

- [ ] **Step 1: Write the failing tests** on a temporary tree:
  - a planted scenario id is caught;
  - a planted person's name is caught;
  - a clean tree gives no hits;
  - `Hit` never holds the term.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement `scan.py`.**
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Run the scan over the spec and the builder's plan as they are now.** Expected: 0
  hits.
- [ ] **Step 6: Commit.**

### Task L1.4: Appendix A, the rulings as mechanisms

**Files:**
- Create: `docs/superpowers/specs/2026-10-23-prototype-core-rulings.md`

- [ ] **Step 1: Write one row for each of R1–R65,** from the OWM service spec's Appendix A
  (`docs/superpowers/specs/2026-10-10-owm-service-design.md`).
  - Keep the number. State what the code must do and why, in terms of the contract and the ports.
  - Mark each row's fate:
    - **kept**;
    - **changed by the prototype spec**, naming the section. For example, the catalog gate replaces
      the `missing_record` rulings, and Authorizer tokens replace the session rulings;
    - **dropped as lab-only**, naming why.
- [ ] **Step 2: Run the scan over it.** Expected: 0 hits.
- [ ] **Step 3: Commit, and ask the user to review it.**

### Task L1.5: The first export

- [ ] **Step 1: Cut and push `dataset-2026-10-23` at the export commit** (LW-2).
- [ ] **Step 2: Run the exporter.** Expected: 0 scan hits.
- [ ] **Step 3: Ask the user to review `README.md` and `FILES.sha256`** in the export. On their go,
  give them the path to hand to the builder. Record the export id in the spec's amendment log, and
  in the Ledger.

---

## L2: Northstar's org package

Everything here lives in `lab/prototype_orgs/northstar/`, in the layout of the frozen
`contract/org-package.md`. The profile carries both request types' bindings, but enables only the
discount pack until P6 (PL-6).

### Task L2.1: Register entries and stores, before the P2 gate

**Files:**
- Create:
  - `lab/prototype_orgs/convert_register.py`, which turns `lab/owm_register/base.yaml` and the two
    `missing-*-evidence.yaml` registers into v2 entry files;
  - `register/NN-<slug>.yaml`;
  - `tests/prototype_orgs/test_convert.py`.

**What the converter does:**
- `file` becomes `source_id: null` and `source_version: null`, filled in later by the loader, from
  the KF base.
- `registered_by` and `approved_by` become `submitted_by` and `approved_by`. These are the two
  named people acting as the function owners, and the loader acts as them.
- Terms are copied unchanged.

**Tests:**
- Every entry validates against the frozen `register-entry.schema.json`.
- The converted terms equal the source terms.
- No output file carries anything but an entry, its document's file name, and the two people.

**Then:** build three stores with `owmctl register`: base, `missing-contract-evidence` and
`missing-guarantee-evidence`. Every change must be accepted.

### Task L2.2: The profile and the package, before the P4 gate

**Files:**
- `package.yaml`, `profile.yaml`
- `exports/<source>/<table>.csv`, mapped from `dataset/evidence/structured/*.csv`. For example
  `discount_requests.csv` becomes `exports/crm/discount_requests.csv`.
- `tests/prototype_orgs/test_profile.py`

**Tests:**
- The profile validates.
- Every binding names a column that exists in its export.
- `id_pattern` matches every key in its export.
- Packs: `[discount_approval@1]`.

### Task L2.3: Principals, delegations and grants, before the P5 gate

**Files:** `principals.yaml`, `delegations/`, `grants/`

**Contents:**
- `principals.yaml` lists the people (`employee_id` and work email, from the HR export) and one
  agent, G. G's accountable person is the journey's requester.
- The delegation D for the journey.
- One grant, for the "agent approving over its cap" attack.
- Each entry names its submitter and approver.

**Tests:** each file validates, and each delegation's delegator exists in the HR export.

---

## L3: the acceptance suite

It lives in `lab/prototype_suite/`. Its runners write their results to
`runs/<date>-prototype-gate-P<n>/`, with `notes.md` first.

### Task L3.1: The parity runner (gates P2, P4 and P6)

**Files:**
- `lab/prototype_suite/parity.py`
- `tests/prototype_suite/test_parity.py`

**Interfaces:**
- **Produces:** `run_parity(kinds: Sequence[str], owmctl: Path, stores: Mapping[str, Path],
  cap_usd: Decimal, out: Path) -> ParityReport`.
- For each scenario in `harness.DECISIONS[kind]`, it runs `owmctl decide` with:
  - the scenario's corpus directory;
  - its register store, chosen by corpus;
  - `--clock` from `harness.clock_for`;
  - the subject's request id;
  - `--org lab/prototype_orgs/northstar` from P4 on.

  It then compares `record` with `harness.COMMITTED` on `harness.FIELDS`, and classifies each
  difference following LW-5.

**Tests:** with a fake `owmctl`, these give the counts expected:
- a matching record;
- a mismatching record;
- a mismatch traced to a judgment that the live lab service also shows;
- exit 3.

**The report holds counts:** matched, differing on the port, differing on a judgment shared with
the lab, and no decision. Mechanism notes say what differed in contract terms.

### Task L3.2: The attack runner (gates P3 and P4)

**Files:**
- `lab/prototype_suite/attacks.py`
- `tests/prototype_suite/test_attacks.py`

**What it does:**
- It replays `runs/2026-10-08-register-attacks/sealed/cases/C01–C24` through the prototype's
  register routes, with test-mode tokens from the operator surface.
- It counts the attacks admitted. The gate requires 0.
- It also reports any legitimate case that gets refused, a false refusal, measured against each
  case's intended outcome.

**Tests:** the runner, on a fake service, counts an admitted case and a refused one correctly.

### Task L3.3: The journey, the claim test and the delegation attacks (gate P5)

**Files:**
- `lab/prototype_suite/journey.py`, `lab/prototype_suite/mcp_client.py` (the plain client)
- `tests/prototype_suite/test_journey_offline.py`

**What it does:**
- Runs §8's journey on Northstar with its real values: R, G, A, s, r and c from the lab's truth,
  kept lab-side. It runs twice, once driven by the reference agent and once by the plain client.
- Asserts exactly one write, carrying r, with c kept beside it as the claim.
- Then runs the variants and the §12 attacks:
  - the row edited to c;
  - D revoked mid-decision, and D expired mid-decision;
  - a re-delegation attempt;
  - two hats;
  - over the cap;
  - `agent_approval: never` against every grant.
- Then the failure ends, through `PUT /api/v1/operator/faults`.

- **The trace** (spec §12, §9.7), read from the lab's Opik instance by
  `lab/prototype_suite/traces.py`:
  - one connected trace per journey run;
  - every span the telemetry contract names, with its required attributes;
  - no token, key or message content in any span.

**Tests:**
- The runner's assertions, checked offline against recorded responses from the builder's fernhill
  run.
- The trace checks, run against recorded spans.

### Task L3.4: The name scan and the empty-diff check (gates P4 and P6)

**Files:**
- `lab/prototype_suite/static_checks.py`
- `tests/prototype_suite/test_static_checks.py`

**What it does:** works on a read-only clone of the builder's repo.
- No pack, org or lab name appears in `contract/`, `core/`, `service/` or `mcp/`.
- `git diff --stat p5-gate HEAD` under those four directories is empty.

### Task L3.5: Model-behaviour evals, reported (LW-10)

**Files:**
- `lab/prototype_suite/behaviour.py`, which uses the `prototype-eval` group
- `lab/prototype_suite/judges/`, which holds the judge prompts. They stay lab-side.
- `tests/prototype_suite/test_behaviour.py`

**What it does:** these evals read the gate runs' traces in the lab's Opik instance.
- **The agent's trajectory.** These are code metrics over the spans:
  - the tools it called, and their order;
  - it never calls `approve` on a decision it requested;
  - it asks for clearance only after approval.
- **The agent's explanation,** judged by Claude against the decision record. Is every figure and
  reason it states in the record?
- **Jev's stability.** Over the parity runs' judgment spans: the rate of out-of-type answers, and
  how often the same question gets the same answer.
- **Human grades,** given in an annotation queue, then copied to the Ledger.

**Tests:** the code metrics, run on recorded spans: a trajectory that passes, and one that
approves its own request.

---

## L4: running the gates

### Task L4.1: The gate playbook

**Files:**
- Create: `knowledge/playbooks/prototype-gates.md`

For each gate it records:
- what the builder must have pushed and tagged;
- the pre-registration, with the model, caps and the expected spend;
- the commands, and where the results go;
- the report template: counts and mechanism notes only;
- the lab's Opik instance (LW-8): start it, check it listens only on `127.0.0.1`, give the gate
  run's environment (LW-9), and stop it afterwards;
- how the report reaches the builder, as paste-ready text the user relays.

### Task L4.2: Each gate, after its phase

Run the gate per the playbook, write `notes.md`, update the Ledger with a pinned update that appends
to the gap's log, and relay the report. A gate that fails goes back to the builder with mechanism
notes, and the next phase waits.
