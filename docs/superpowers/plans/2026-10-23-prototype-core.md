# The Prototype Core (Sub-project 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** build the free-standing prototype core in a new private repo, phase by phase (P0–P6).
Contracts come first. Then the lab's kernel and service are ported to parity and generalized into
packs and org profiles. Real identity, an MCP server, a reference agent and an approver's tool go in
front, and credit is added as data at the end.

**Architecture:** a uv workspace whose members are the spec's directories (`contract/`, `core/`,
`ports/`, `service/`, `adapters/`, `mcp/`, `agent/`, `approver/`, `org/`, `cli/`).
- `core/` is stdlib only and does no I/O. Everything else reaches the world through `ports/`, which
  `adapters/` implement.
- Each phase ends at a gate the lab runs from outside, through `owmctl` and the HTTP API. The next
  phase starts only after that gate passes.

**Tech stack:**
- Python ≥3.11 with uv.
- The service: FastAPI, uvicorn, pydantic 2 and SQLite.
- jsonschema for contract documents; PyJWT for tokens.
- Authorizer 2.4.2 (embedded OpenFGA on SQLite) for identity and access.
- The MCP Python SDK 2.x; Agno 3.x for the reference agent; Textual 8.2 for the approver's screen.
- OpenTelemetry 1.45 (API, SDK, OTLP/HTTP export), the OTel GenAI instrumentations and
  `opentelemetry-util-genai` (§9.7). No vendor SDK.
- pytest, mypy (strict) and ruff.

**Spec:** `docs/superpowers/specs/2026-10-23-prototype-core-design.md`, approved by the user on
2026-10-23, and its Appendix A, `docs/superpowers/specs/2026-10-23-prototype-core-rulings.md`. "§"
below means a section of the spec. Both files reach you in the port bundle, beside this plan.

**Who runs it:** the builder, a fresh session working in the new repo, reading only what §11.3
allows. The lab's own work (L1–L4) has a separate plan, which the builder doesn't read.

## Global Constraints

- **What you read:** this plan, the spec, Appendix A and the port bundle (§11.4). Nothing else from
  the lab.
  - Never ask for scenario ids, expected outcomes, the acceptance suite, or anything about a second
    org.
  - Gate results come back to you as counts and mechanism notes.
- **Get the user's own go in chat** before each of these. One approval never covers another.
  - Creating the GitHub repo. The name is the user's to choose.
  - Any download: Authorizer, the OpenFGA CLI, the TypeScript compiler, the PyPI packages below.
  - The first spend on Jev, and the first spend on the reference agent's model.
- **Python:**
  - `requires-python = ">=3.11"`.
  - mypy: `python_version = "3.11"`, `strict = true`, tests included.
  - ruff: `line-length = 100`, `target-version = "py311"`,
    `select = ["E", "F", "I", "B", "UP", "N", "W"]`.
- **Dependencies.** Floors are as of 2026-10-23. Adding anything else needs the user's OK.
  - Runtime: `fastapi>=0.162`, `uvicorn>=0.54`, `httpx>=0.28.1`, `pydantic>=2.14`,
    `pyyaml>=6.0.3`, `jsonschema>=4.26`, `pyjwt[crypto]>=2.15`, `mcp>=2.3,<3`,
    `agno>=3.1.10,<4`, `textual>=8.2,<9`.
  - Dev: `pytest>=8.2`, `mypy>=1.11`, `ruff>=0.6`, `types-PyYAML`, `types-jsonschema`.
  - Only if P0 picks standalone OpenFGA: `openfga-sdk>=0.10.5`.
  - **Telemetry, pinned exactly, not floors** (§9.7), from P3 on:
    - `opentelemetry-api==1.45.1`, `opentelemetry-sdk==1.45.1`,
      `opentelemetry-exporter-otlp-proto-http==1.45.1`;
    - `opentelemetry-instrumentation-fastapi==0.66b1`, `opentelemetry-instrumentation-httpx==0.66b1`;
    - `opentelemetry-util-genai==1.3b0`;
    - in `agent/` only, `opentelemetry-instrumentation-genai-agno==1.3b0`. If it doesn't work with
      Agno 3.x, the fallback is `openinference-instrumentation-agno==1.0.15`. Never install both.
- **Boundaries.** `tests/boundaries/test_imports.py` (Task 1.1) enforces all of these:
  - `owm_contract` imports only the stdlib.
  - `owm_ports` imports only the stdlib and `owm_contract`.
  - `owm_core` imports only the stdlib, `owm_contract` and `owm_ports`, and does no I/O.
  - None of those three ever imports `opentelemetry` (§9.7).
  - `owm_mcp`, `owm_agent`, `owm_approver` and `owm_org` never import `owm_core`, `owm_service`,
    `owm_ports`, `owm_adapters` or `owm_cli`. They reach the OWM over HTTP.
  - Nothing imports a lab module. Ported code is copied in and renamed.
  - YAML is read only at the edge: `cli/`, `service/`, `org/` and `adapters/`. `core/` takes parsed
    mappings.
- **No use-case or org names** in `contract/`, `core/`, `service/` or `mcp/` once P4 is done (§3.3).
  The names are listed in `tests/boundaries/names.txt`.
- **Fail closed** (§9). Nothing fills a gap: no cached policy, no agent claim standing in for a
  record, no other model standing in for Jev. An exception escaping a port means no decision, never
  a default.
- **Time.**
  - Datetimes are timezone-aware UTC inside the system.
  - The profile's `time_zone` sets day boundaries and display only.
  - `as_of` never comes from a request body.
- **Errors.**
  - 401 and 5xx responses use the typed error (§9.4, Task 1.3).
  - 403, 409 and 422 keep v1.4's `Refusals` body.
- **Credentials.** Credentials are never printed, logged or committed. They are: Authorizer client
  secrets, the operator token, the Jev key, the agent model's key and the Opik workspace key
  (PL-16).
  - Each lives in a file under `var/secrets/`. The Jev key's file is the one named by
    `TYPESAFE_API_KEY_FILE`.
  - `.env` and `var/` are gitignored.
  - Before every commit, run `scripts/scan_staged.sh` (Task 1.1) on the staged diff. It must report
    0 hits.
  - **No token ever enters a model's context**, whether as a tool argument, a prompt or a log the
    model reads.
- **Jev recordings.** The adapter records every live call to `var/jev-recordings/`. It may replay
  only those recordings. It never reads anything from the lab's `runs/`.
- **Telemetry** (§9.7):
  - The exporter is built only from `OWM_OTLP_ENDPOINT`, plus `OWM_OTLP_HEADERS_FILE`. If the
    endpoint isn't set, nothing is exported.
  - Never use the OTel default endpoint or the `OTEL_EXPORTER_OTLP_*` variables. On this machine,
    `localhost:4318` is another system's collector.
  - GenAI content capture stays `NO_CONTENT`. Agno's usage telemetry is off: `AGNO_TELEMETRY=false`,
    and `telemetry=False` on the agent.
  - No token, key or message content ever goes in a span, an event or a metric.
- **After the freeze** (Task 1.12), the contract changes only through the user, as amendments.
- **Commits:** small and frequent. No amend, no force-push, no history rewrite. Use the trailers
  your session's harness gives you.

## Rulings made in planning

Each of these was decided while writing this plan, where the spec was silent, or where a fact about
the lab's code forced a choice.

- **PL-1. P0 and P1 are written as steps; P2–P6 only as tasks.**
  - Each later task names its files, the interfaces other tasks rely on, the tests that prove it, and
    what "done" means.
  - At the start of each phase, once the gate before it has passed, expand that phase's tasks into
    steps (with superpowers:writing-plans) in `docs/plans/P<n>-steps.md`. The user reviews the
    expansion before work starts.
  - *Why:* P0's answers and the frozen contract decide details of P2–P6, and §11.3 has the builder
    write its own tests.
  - *Cost if wrong:* one extra review per phase.
- **PL-2. The parity counts are 32, 22 and 10, not 42.**
  - The lab's 42 decision scenarios include 10 SLA scenarios, and SLA isn't in v1 (§1.3).
  - P2's gate runs 32 through the ported kernel: 22 discount and 10 credit.
  - P4's gate runs the 22 discount scenarios, because credit has no pack until P6.
  - P6's gate runs credit's 10.
  - The spec is corrected to match.
- **PL-3. The spec's directory names stay; import names start with `owm_`.**
  - For example `core/owm_core/` and `mcp/owm_mcp/`, so the MCP SDK's `mcp` package is never
    shadowed.
  - The empty-diff check then reads exactly as §11.1 says.
- **PL-4. `contract/` holds language-neutral files plus one stdlib Python package.**
  - owm-decisions v2 stays TypeScript declarations, as v1.4 is, for web-next.
  - Data documents are JSON Schema 2020-12: packs, profiles, grants, delegations, register entries,
    the vocabulary, the error shape and the MCP tools' schemas.
  - `authz.fga` comes with OpenFGA model tests.
  - `routes.yaml` lists every route in machine-readable form.
  - The `owm_contract` package holds the frozen dataclasses that `core/` and `ports/` share.
  - Tests keep the dataclasses, the schemas and `routes.yaml` in step.
- **PL-5. The interfaces the lab calls are contract, frozen with it.**
  - These are `owmctl` (`contract/owmctl.md`), the org package layout (`contract/org-package.md`),
    the test-mode operator routes (`contract/operator.md`) and `sor_stub`'s routes
    (`contract/sor-stub.md`).
  - The lab's suite drives the prototype only through these and owm-decisions v2.
- **PL-6. Northstar's org package belongs to the lab.**
  - The lab writes and registers Northstar's profile, register entries, principals, grants and
    delegations (§11.5).
  - The profile carries the bindings for both request types from the start. At P6 the lab registers
    the profile version that enables credit.
  - The builder's P6 delivers the credit pack and its own org's credit configuration.
  - The spec's P6 row had the builder write Northstar's credit bindings. This ruling keeps
    truth-derived entries, and the lab's org, on the lab's side.
- **PL-7. The builder runs its own Knowledge Foundation: a v0.2 document server.**
  - It lives in `adapters/owm_adapters/kf_devserver/`, works over a directory, and has fault
    switches.
  - It serves K0, K1, K2, K3 (upload), K4, K5, K7 and K9.
  - The lab runs the gates against B-20, the real v0.2 implementation.
  - *Why:* the adapter is written to the contract, and the builder needs faults it can switch on.
    B-20's build and running costs stay on the lab's side.
- **PL-8. An empty field and a malformed field end differently.**
  - An empty required input means something the decision needs is absent. The decision routes, with
    a `missing_input` finding that names the field.
  - A value that doesn't parse in its declared type or unit means no decision. Examples are a date
    that isn't ISO 8601, or `"12,5"` where a number is declared. The response is 503
    `record_unreadable`, not retryable, with `who_can_fix: requester`. The value is never coerced.
- **PL-9. Decision type names.** At P2 the types are the lab's: `discount` and `credit`. From P4
  they are the packs' `use_case` names, `discount_approval` and `credit_limit`, the names from the
  spec's examples, now fixed.
- **PL-10. The builder's test org is `fernhill`, a made-up tool distributor in `orgs/fernhill/`.**
  - It is set up to differ from Northstar wherever a binding can differ:
    - `time_zone: Asia/Kolkata`, which has a half-hour offset;
    - discounts stored in basis points;
    - quote ids matching `^FH-Q-\d{6}$`;
    - an HR export with different column names.
  - Its name goes into `names.txt`.
- **PL-11. `GET /healthz` is the one route that takes no token.**
  - It returns only `{"ok": bool, "ports": {name: "up" | "down"}}`.
  - While Access is unhealthy, it returns 503.
- **PL-12. `GET /api/v1/me` also returns what the caller may see.**
  - The shape is `visible: {decide: [use_case], request_clearance: [action], approve: [use_case]}`,
    worked out with `list_objects` for the actor and, under delegation, for the person behind it.
  - With it come the token's binding (`subject` or null) and its `expires_at`.
  - The MCP server and the approver's tool learn their permissions from this route. They never ask
    Access directly (§10.1, Global Constraints).
- **PL-13. The MCP server speaks streamable HTTP on loopback, at `/mcp`.**
  - The agent's runtime sends the agent's token as the bearer header of each HTTP request. The model
    never sees it.
  - If Agno's MCP client can't vary the header per call, the agent opens one MCP session per
    delegated token.
- **PL-14. The sovera-owm ports are abstract base classes (`ABC`), as sovera-owm wrote them.**
  - The spec's §6.6 said "verbatim", and they are ABCs. So `IdentityProvider` and
    `AuthorizationProvider` stay ABCs.
  - Their adapters must pass the contract tables in the bundle's copies (I1–I8 for identity, and the
    authorization table).
  - The prototype's own ports (§9.5) are `Protocol`s.
- **PL-15. The telemetry contract is contract, frozen with the rest (PL-5).**
  - It consists of `contract/telemetry.yaml` and `owm_contract.telemetry`. The latter is stdlib
    string constants: span names, attribute names, and the forbidden list.
  - An eleventh workspace member, `telemetry/` (`owm_telemetry`), holds the one setup function that
    every process calls: the service, `owmctl`, the MCP server and the agent. It may import only the
    stdlib, `owm_contract` and `opentelemetry`.
  - Everyone may import `owm_telemetry` except `owm_contract`, `owm_ports` and `owm_core`. The front
    door may too, since it isn't the OWM.
  - The spec's other directory names stay (PL-3).
- **PL-16. Your traces go to the user's Opik cloud workspace. Tests never use a network backend.**
  - Tests use the SDK's in-memory span exporter.
  - For your own runs, the endpoint is the workspace's OTLP traces URL,
    `https://www.comet.com/opik/api/v1/private/otel/v1/traces`. The user puts the workspace's key
    and name in the file that `OWM_OTLP_HEADERS_FILE` names, as `Authorization`, `Comet-Workspace`
    and `projectName` header lines. You never print it.
  - Opik builds a trace only from a root span, so every request starts one.
  - The lab's instance isn't yours. You are never given its address, and you never look for it.

## Review Focus

These are the inputs and failure modes the spec implies but no task's own tests would otherwise
cover, most likely first. Each has a pinning test in the task named.

1. **Two calls race on one subject.**
   - Two `decide` calls on the same subject give one decision version; the other call gets 409 with
     the live decision as `existing`.
   - Two `execute` calls on one clearance give one write. The second gets the first one's report.
   - *Tests:* Tasks 3.1, 3.4 and 3.8.
2. **A delegated token is used outside its binding.**
   - A token bound to subject *s* is used on *s′*, or used after its 5 minutes. Either way it is
     refused (403 `token_binding` or 401 `unauthenticated`), and nothing is recorded.
   - *Tests:* Tasks 5.1 and 5.4.
3. **Day boundaries in the org's time zone.**
   - Example: 2026-03-31T19:00Z is already 2026-04-01 in Asia/Kolkata.
   - A clock-derived `as_of`, and a grant's per-day cap, both count in the org's day.
   - *Tests:* Tasks 4.2 and 5.3.
4. **An empty field, a malformed field, and a padded id.**
   - An empty or malformed field ends as PL-8 says.
   - A subject id with surrounding spaces, or in the wrong case, gets 422 naming `subject`. It is
     never normalized.
   - *Tests:* Task 4.2.
5. **A governing document saved with a UTF-8 byte-order mark and CRLF line endings.** The adapter's
   fingerprint equals the `text.sha256` that the Knowledge Foundation reports for it in K5.
   - *Tests:* Task 3.7.
6. **A token, a key or message text ends up in an exported span.**
   - Across a whole journey, no span name, attribute, event or resource holds a bearer token, a key
     file's content, or the word `Bearer`.
   - This holds even when someone sets the HTTP header-capture variable to `.*`: the `Authorization`
     header is then redacted or absent.
   - *Tests:* Tasks 3.9 and 5.7.

## File structure

```
<repo>/
├─ pyproject.toml                 workspace root: members below, dev tools, mypy/ruff/pytest config
├─ contract/                      member owm-contract
│  ├─ owm-decisions.ts            owm-decisions v2 (TypeScript declarations)
│  ├─ routes.yaml                 every route: method, path, auth, request/response types, errors
│  ├─ authz.fga                   the OpenFGA model
│  ├─ authz.fga.yaml              its model tests (OpenFGA store-test format)
│  ├─ errors.yaml                 the closed list of error codes
│  ├─ telemetry.yaml              spans, kinds, required and forbidden attributes; conventions commit
│  ├─ schemas/                    JSON Schema 2020-12: vocabulary, error, pack, profile, grant,
│  │                              delegation, register-entry, owmctl-decide-output, mcp/*.json
│  ├─ owmctl.md · org-package.md · operator.md · sor-stub.md · mcp-tools.md
│  ├─ CHANGES-v2.md               every §3.2 change, mapped to the TypeScript diff
│  ├─ README.md                   index and version
│  └─ owm_contract/               stdlib dataclasses: vocabulary, errors, shapes, auth; telemetry names
├─ ports/owm_ports/               Protocols (§9.5) and the two ABCs (§6.6), plus port errors
├─ core/owm_core/                 the ported kernel, register rules, and the decision rules
├─ service/owm_service/           the HTTP API, bindings layer, event log, register queue
├─ adapters/owm_adapters/         dirfake/, kf/, kf_devserver/, sor_stub/, df_stub/, jev/,
│                                 authorizer/, executor/, sqlite_events/, fakes/
├─ mcp/owm_mcp/                   the MCP server
├─ agent/owm_agent/               the reference Agno agent
├─ approver/owm_approver/         the approver's CLI and Textual screen
├─ org/owm_org/                   the org loader
├─ cli/owm_cli/                   owmctl
├─ telemetry/owm_telemetry/       the one OTel setup function (PL-15), from P3
├─ packs/<use_case>/              definition.yaml, procedure.yaml, terms/*.schema.json,
│                                 findings.schema.json   (from P2 for procedures, P4 for the rest)
├─ orgs/fernhill/                 the builder's own org package (PL-10)
├─ inputs/                        the bundle's read-only inputs (Northstar's content, contracts)
├─ docs/spikes/ · docs/plans/     the P0 report; each phase's expanded steps
├─ scripts/scan_staged.sh
└─ tests/<part>/ · tests/boundaries/
```

---

## Phase P0: the Authorizer spike

Settle §6.7's three questions before anything is built on them. Spike code is throwaway, lives in
`spikes/p0/`, and nothing imports it.

### Task 0.1: Start the repo and get the go-aheads

**Files:**
- Create: `README.md`, `.gitignore`, `spikes/p0/README.md`

- [ ] **Step 1: Ask the user, in one message, for their own go on each item:**
  1. The repo's name, and creating it as a private GitHub repo.
  2. Downloading Authorizer 2.4.2 (the latest release, published 2026-10-14) for this machine.
  3. Downloading the OpenFGA CLI (`fga`), for model tests.
  4. Using the TypeScript compiler through `npx` (`typescript@5.6.3`), to check the contract.
  5. Installing the PyPI packages listed in Global Constraints.

  Wait for the answer. Do only what was approved, and note what wasn't.
- [ ] **Step 2: Create the repo and commit the skeleton.**
  - Run `gh repo create <name> --private --clone`.
  - The README is one paragraph, taken from §0: what this is, and that it's the reference the OWM
    team implements from.
  - `.gitignore` covers `.env`, `.venv/`, `var/`, `*.db` and `spikes/p0/var/`.
  - Commit and push.

### Task 0.2: Authorizer on SQLite, with the draft model

**Files:**
- Create: `spikes/p0/authz.fga` (§6.5's draft, verbatim), `spikes/p0/run.md`

- [ ] **Step 1: Start Authorizer 2.4.2 on SQLite,** with its database under `spikes/p0/var/`. Record
  the exact flags or variables in `run.md`, with any secrets redacted.
- [ ] **Step 2: Load `authz.fga`.**
  - Write tuples for a toy org:
    - `agent:g1 acts_for person:p1`;
    - `function:sales member person:p1`;
    - `use_case:uc1 org org:o1`;
    - `use_case:uc1 may_decide function:sales#member`;
    - `action:a1 use_case use_case:uc1`;
    - `action:a1 may_request_clearance agent:g1`.
  - Check these. Expected: `true`, `false`, `[action:a1]`.
    - `check(person:p1, may_decide, use_case:uc1)`;
    - `check(person:p2, may_decide, use_case:uc1)`;
    - `list_objects(agent:g1, may_request_clearance, action)`.
- [ ] **Step 3: Record in `run.md`, for each check:** the request shape, the answer, and the latency.

### Task 0.3: The actor check, and token exchange

**Files:**
- Create: `spikes/p0/actor.md`, `spikes/p0/exchange.md`

- [ ] **Step 1: Token exchange.**
  - Find out whether RFC 8693 token exchange is in the open-source build, and under what licence.
    Cite the file or the docs page.
  - If it's there, try each of these and record pass or fail with the request shape (no secrets):
    1. Exchange a person's session token (subject) plus an agent's `client_credentials` token
       (actor), with a narrower scope and a resource. The result should have `sub` = the person and
       `act.sub` = the agent.
    2. A subject-only exchange, which should be refused.
    3. A request for a wider scope than the subject holds, which should be refused or narrowed.
    4. A 5-minute lifetime.
    5. The resource appearing in the token, as a `resource` or `aud` claim.
- [ ] **Step 2: Checking the actor as well as the subject.**
  - Try (a) an org-scoped admin role used only for checks, and (b) passing the actor as a
    contextual tuple.
  - For each, record whether Authorizer allows it, what the call looks like, and whether it can test
    `agent:g1`'s rights while the caller's token is the delegated one.

### Task 0.4: The spike report (gate)

**Files:**
- Create: `docs/spikes/p0-authorizer.md`

- [ ] **Step 1: Write the report.**
  - Answer each of §6.7's three questions in one paragraph, citing the evidence in `spikes/p0/`.
  - Then recommend one of:
    - Authorizer as it is;
    - standalone OpenFGA beside Authorizer, for the checks;
    - a Casbin adapter behind the same port;
    - another issuer for the delegated token, if exchange is enterprise-only.
  - Give the days each option adds (§14, risk 1).
- [ ] **Step 2: Commit, push, and ask the user to read it and choose.** P1 starts once the user has
  chosen and the port bundle is in hand.

---

## Phase P1: the contract

`contract/` is written before any code (§11.1). The tests here check the contract's own documents.

### Task 1.1: The workspace and its boundaries

**Files:**
- Modify: `pyproject.toml`
- Create:
  - `<member>/pyproject.toml` and `<member>/owm_<member>/__init__.py` for each of the ten members;
  - `tests/boundaries/test_imports.py`, `tests/boundaries/names.txt` (empty until P4);
  - `scripts/scan_staged.sh`.

- [ ] **Step 1: Write the failing test** `tests/boundaries/test_imports.py`.

```python
INNER = {"owm_contract": set(), "owm_ports": {"owm_contract"},
         "owm_core": {"owm_contract", "owm_ports"}}
FRONT_DOOR = ("owm_mcp", "owm_agent", "owm_approver", "owm_org")
NOT_FROM_FRONT_DOOR = {"owm_core", "owm_service", "owm_ports", "owm_adapters", "owm_cli"}
LAB = {"owm_kernel", "owm_register", "decision_engine", "rounds", "northstar",
       "spec_admission", "owm_standin"}
IO_IN_CORE = {"os", "io", "pathlib", "sqlite3", "socket", "subprocess", "shutil", "tempfile",
              "urllib", "http", "asyncio"}

def test_inner_packages_import_only_what_they_may() -> None: ...
    # for each .py under each INNER package: every imported top-level name is in
    # sys.stdlib_module_names, or the package itself, or in INNER[pkg]
def test_inner_packages_never_import_opentelemetry() -> None: ...
    # covered by the stdlib rule; asserted by name too, so the message is plain (§9.7)
def test_core_does_no_io() -> None: ...
    # owm_core imports nothing in IO_IN_CORE and never calls open(), .read_text(), .write_text(),
    # .read_bytes(), .write_bytes()
def test_front_door_reaches_the_owm_only_over_http() -> None: ...
def test_nothing_imports_the_lab() -> None: ...
def test_no_use_case_or_org_names_in_the_named_parts() -> None: ...
    # every word in names.txt, case-insensitive, absent from contract/, core/, service/, mcp/
    # (examples live in tests/, not contract/)
```

- [ ] **Step 2: Run `uv run pytest tests/boundaries -v`.** Expected: it fails, because the packages
  don't exist yet.
- [ ] **Step 3: Create the workspace.**
  - In the root `pyproject.toml`, put `[tool.uv.workspace] members = [...]` with the ten members,
    the dev group, `[tool.pytest.ini_options] testpaths = ["tests"]`, and the mypy and ruff settings
    from Global Constraints.
  - Each member's `pyproject.toml` declares only what its row in §2.1 allows. `owm-contract` has no
    dependencies; `owm-ports` depends on `owm-contract`; `owm-core` depends on both.
- [ ] **Step 4: Write `scripts/scan_staged.sh`.**
  - It reads every file in `var/secrets/`, and exits non-zero if any added line of
    `git diff --cached -U0` contains one of those values.
  - It also fails on a staged private-key header, or a JWT-shaped string (three base64url segments
    starting `eyJ`).
  - It prints the file and line, never the value.
- [ ] **Step 5: Run the boundary tests, `uv run mypy`, `uv run ruff check` and
  `scripts/scan_staged.sh`.** Expected: everything passes.
- [ ] **Step 6: Commit** ("chore: workspace and its boundaries").

### Task 1.2: The core vocabulary, the reference shapes and the actor chain

**Files:**
- Create: `contract/schemas/vocabulary.schema.json`, `contract/owm_contract/vocabulary.py`,
  `tests/contract/test_vocabulary.py`

**Interfaces:**
- **Produces** `owm_contract.vocabulary`:
  - `CoreType(StrEnum)` with exactly six members: org, person, agent, function, customer, document.
  - `RecordRef(source: str, key: str, version: str)`, frozen.
  - `ActorKind(StrEnum)`: `person`, `agent`, `service`. `service` is the executor or the OWM itself.
  - `Actor(kind, id, on_behalf_of: str | None = None, delegation: str | None = None,
    grant: str | None = None)`, frozen, validated in `__post_init__`.
- The schema's `$defs`: `core_type`, `record_ref` and `actor`.

- [ ] **Step 1: Write the failing tests.**

```python
def test_core_vocabulary_is_exactly_six_types() -> None:
    assert {t.value for t in CoreType} == {
        "org", "person", "agent", "function", "customer", "document"}

def test_record_is_a_reference_shape_not_a_type() -> None:
    ref = RecordRef(source="df:crm.quotes", key="FH-Q-000123", version="v7")
    assert "record" not in {t.value for t in CoreType}
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.key = "other"  # type: ignore[misc]

@pytest.mark.parametrize("kwargs", [
    {"kind": "person", "id": "FH-E-0001"},
    {"kind": "agent", "id": "ag-1"},                                   # its own mandate
    {"kind": "agent", "id": "ag-1", "on_behalf_of": "FH-E-0001", "delegation": "DL-1"},
    {"kind": "agent", "id": "ag-1", "grant": "GR-1"},
    {"kind": "service", "id": "executor"},
])
def test_valid_actor_chains(kwargs: dict[str, str]) -> None:
    Actor(**kwargs)  # type: ignore[arg-type]

@pytest.mark.parametrize("kwargs", [
    {"kind": "person", "id": "FH-E-0001", "on_behalf_of": "FH-E-0002"},  # people act as themselves
    {"kind": "agent", "id": "ag-1", "on_behalf_of": "FH-E-0001"},         # no delegation named
    {"kind": "agent", "id": "ag-1", "delegation": "DL-1"},                # delegation, but for whom?
    {"kind": "agent", "id": "ag-1", "on_behalf_of": "FH-E-0001", "delegation": "DL-1",
     "grant": "GR-1"},                                                    # one authority per step
    {"kind": "service", "id": "executor", "grant": "GR-1"},
])
def test_invalid_actor_chains_are_refused(kwargs: dict[str, str]) -> None:
    with pytest.raises(ValueError):
        Actor(**kwargs)  # type: ignore[arg-type]

def test_actor_schema_and_dataclass_agree() -> None: ...
    # every valid case validates against $defs/actor; every invalid case fails it
```

- [ ] **Step 2: Run them.** Expected: FAIL, the module doesn't exist.
- [ ] **Step 3: Implement `vocabulary.py` and `vocabulary.schema.json`.**
  - The schema expresses the actor rules with `if`/`then`/`not`.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit** ("contract: core vocabulary, record reference, actor chain").

### Task 1.3: The error shape, and the closed list of codes

**Files:**
- Create: `contract/errors.yaml`, `contract/schemas/error.schema.json`,
  `contract/owm_contract/errors.py`, `tests/contract/test_errors.py`

**Interfaces:**
- **Produces** `owm_contract.errors`:
  - `ErrorCode(StrEnum)`.
  - `ERRORS: Mapping[ErrorCode, ErrorSpec]`, where
    `ErrorSpec(status: int, retryable: bool, port: str | None, who_can_fix: str)`.
  - `OwmError(error: ErrorCode, retryable: bool, port: str | None, subject: str | None,
    event: str | None, who_can_fix: str)`, frozen.
  - `OwmError.of(code, *, subject=None, event=None, who_can_fix=None) -> OwmError`, which fills
    the rest from `ERRORS`.
  - `OwmError.to_json() -> dict[str, object]`.
- `who_can_fix` is one of `caller`, `requester`, `operators`, or `role:<role>` (a pack role).

The closed list, with a status, retryable flag, port and default `who_can_fix` for each code:

| code | status | retryable | port | who_can_fix |
|---|---|---|---|---|
| `unauthenticated` | 401 | false | identity | caller |
| `identity_unavailable` | 503 | true | identity | operators |
| `access_unavailable` | 503 | true | access | operators |
| `evidence_unavailable` | 503 | true | evidence | operators |
| `evidence_unreadable` | 503 | false | evidence | `role:` the kind's owner when registered, else operators |
| `records_unavailable` | 503 | true | records | operators |
| `record_unreadable` | 503 | false | records | requester (PL-8) |
| `judgment_unavailable` | 503 | true | judgment | operators |
| `judgment_out_of_type` | 503 | true | judgment | operators |
| `judgment_cap_reached` | 503 | false | judgment | operators |
| `event_store_unavailable` | 503 | true | event_store | operators |
| `execution_failed` | 502 | true | executor | `role:` the action's incident owner |

- [ ] **Step 1: Write the failing tests.**
  - `test_codes_are_a_closed_list`: the codes in `errors.yaml` equal `ErrorCode`, and equal
    `ERRORS`' keys.
  - `test_each_code_matches_the_table`: the status, retryable flag, port and default for each code
    are as in the table above.
  - `test_spec_example_validates`: the §9.4 example validates against `error.schema.json`, with
    `"subject": "Q00001234"` and `"event": "EV-0001"`.
  - `test_who_can_fix_forms`: `caller`, `requester`, `operators` and `role:pricing_owner` are
    accepted; `someone` and `role:` are refused, by both the schema and `OwmError`.
  - `test_unknown_code_is_refused`: a code that isn't in the list fails the schema.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement the three files.**
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit** ("contract: typed error and its closed code list").

### Task 1.4: The pack definition schema

**Files:**
- Create: `contract/schemas/pack.schema.json`,
  `tests/contract/examples/pack.discount.example.yaml` (§4.2's YAML, verbatim),
  `tests/contract/test_pack_schema.py`, `contract/README.md` (the section "Rules the structural
  check enforces")

- [ ] **Step 1: Write the failing tests.**
  - `test_spec_example_validates`.
  - `test_refused` is parametrized over copies of the example, each with one mutation. Each must
    fail the schema:
    - `route_to` removed;
    - `agent_approval: sometimes`;
    - an action without `allowed_on`;
    - a `judgments` item without an answer type;
    - an input with neither `type` nor `ref`;
    - `version: "1"` as a string;
    - an unknown top-level key (`additionalProperties: false`).
  - `test_answer_types`: a judgment question takes one of these answer types:
    - `{type: choice, options: [...], criteria: {...}}`;
    - `{type: number, unit: ...}`;
    - `{type: boolean}`.
    Any other type fails.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Write `pack.schema.json`.**
  - Write the cross-field rules the schema can't express under "Rules the structural check
    enforces" in `contract/README.md`, numbered SC-1 onward. These are rules such as:
    - `route_to` ∈ `outcomes`;
    - `allowed_on` ⊆ `outcomes`;
    - `as_of` names a date input;
    - every param path resolves;
    - the procedure names only declared inputs, governing kinds and judgments.
  - P4 implements them (Task 4.7).
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit** ("contract: pack definition schema").

### Task 1.5: The org profile schema

**Files:**
- Create: `contract/schemas/profile.schema.json`,
  `tests/contract/examples/profile.example_org.yaml` (§5.1's YAML, verbatim),
  `tests/contract/test_profile_schema.py`

- [ ] **Step 1: Write the failing tests.**
  - `test_spec_example_validates`.
  - `test_refused` is parametrized over copies of the example, each with one mutation. Each must
    fail the schema:
    - `time_zone` removed;
    - `time_zone: "CET+1"`, which isn't an IANA name pattern;
    - a field with `unit: percentage`;
    - `packs: [discount_approval]` with no `@version`;
    - `people.identity` removed;
    - a type with no `source`;
    - an action target that doesn't start `sor:`.
  - `test_units`: a field binding is either a column name, or `{column, unit}` with `unit` in
    `fraction`, `percent`, `basis_points` or `amount`.
    - An `amount` passes through unconverted. v1 has no currency conversion.
    - Dates bind as a plain column and must be ISO 8601 in the source (PL-8).
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Write `profile.schema.json`.** Add the profile's cross-field rules to the README's
  structural-check section: every binding resolves; every governing kind has an owning function.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit** ("contract: org profile schema").

### Task 1.6: Grants, delegations and register entries

**Files:**
- Create: `contract/schemas/{grant,delegation,register-entry}.schema.json`, one example of each
  under `tests/contract/examples/`, `tests/contract/test_registered_kinds.py`

**What the entry carries:** v1.4's entry fields (Appendix A and the bundle's registrar), with two
changes from §3.2:
- `file` is gone. In its place come `source_id: string | null` and `source_version: integer | null`,
  meaning the foundation's document id and version. Both are null when the foundation doesn't hold
  the document.
- `registered_by`, `approved_by`, `registered_on` and `approved_on` are set by the system from the
  actors. They are refused in a submitted file.

- [ ] **Step 1: Write the failing tests.**
  - Each example validates.
  - Each of these fails:
    - a delegation with `redelegation: true`, since v1 requires `const: false`;
    - a delegation operation outside `decide`, `request_clearance`, `approve` and `action:<name>`;
    - a grant without `accountable`;
    - a grant or delegation without `window.from` or `window.to`;
    - a grant limit with an unknown key (limits are `figure_max`, `scope`, `per_day_max`,
      `window`);
    - a register entry with a `file` key;
    - a register entry carrying `approved_by`.
  - A register entry with `source_id: null` validates.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Write the three schemas.** Add `window.to > window.from`, and "the approver is
  neither the submitter nor anyone acting for them", to the README's structural-check section.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit** ("contract: grants, delegations, register entries").

### Task 1.7: owm-decisions v2 and its route list

**Files:**
- Create:
  - `contract/owm-decisions.ts`, starting from the bundle's v1.4 file, with every §3.2 change;
  - `contract/routes.yaml`;
  - `contract/CHANGES-v2.md`;
  - `tests/contract/test_routes.py`.

**What changes in the TypeScript:**
- The decision type becomes `string`.
- Outcomes, findings and actions become pack-typed: `string` plus a `pack` reference.
- Every event gets `actor: Actor` (Task 1.2's shape).
- Basis documents get `source_id` and `source_version`.
- `missing_record` is replaced by the `no_record` finding.
- Decision records gain `pack: {use_case, version}` and `profile: {org, version}`.
- `About` (contract version, packs enabled) is added.
- `OwmError` is added.
- `Me` is extended (PL-12).
- The DC rules carry their meanings as doc comments, with DC-1 replaced by the grant rule (§6.4).

- [ ] **Step 1: Write the failing tests** in `test_routes.py`.
  - `test_v14_routes_kept`: every v1.4 route is in `routes.yaml` with the same method and path. They
    are:
    - `GET /healthz`;
    - `GET /api/v1/me`;
    - `POST` and `GET /api/v1/decisions`, `GET /api/v1/decisions/{id}`;
    - `GET /api/v1/decisions/{id}/versions/{v}`, `GET /api/v1/decisions/{id}/events`;
    - `POST /api/v1/decisions/{id}/conditions/{cid}/resolve`;
    - `POST /api/v1/decisions/{id}/{approve,decline,withdraw,rerun,clearance}`;
    - `GET /api/v1/decisions/{id}/clearances`;
    - `POST /api/v1/clearances/{id}/redeem`, `POST /api/v1/clearances/{id}/report`;
    - `GET /api/v1/approvals`;
    - `GET /api/v1/register`, `GET /api/v1/register/entries/{doc_id}`,
      `GET /api/v1/register/entries/{doc_id}/text`;
    - `GET` and `PUT /api/v1/register/settings`;
    - `POST` and `GET /api/v1/register/changes`, `GET /api/v1/register/changes/{id}`;
    - `POST /api/v1/register/changes/{id}/{submit,approve,decline,withdraw,remind}`;
    - `GET /api/v1/procedures`, `GET /api/v1/procedures/{proc_id}`.
  - `test_v2_routes_added`: `GET /api/v1/about` and `POST /api/v1/clearances/{id}/execute` are
    present.
  - `test_no_lab_routes`: no path starts with `/lab/`.
  - `test_every_route_needs_a_token`: `auth: bearer` everywhere except `GET /healthz` (PL-11).
  - `test_every_route_names_its_errors`: each route lists its statuses. Every 401 or 5xx code
    listed is in `ErrorCode`.
  - `test_ts_and_routes_agree`: every request and response type named in `routes.yaml` is
    declared in `owm-decisions.ts`, found by a regex over `export (interface|type) Name`.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Write `owm-decisions.ts`, `routes.yaml` and `CHANGES-v2.md`.** `CHANGES-v2.md`
  has one row per §3.2 change: what changed in the TypeScript, and why.
- [ ] **Step 4: Run them.** Expected: PASS.
  - If the user approved TypeScript at Task 0.1, also run
    `npx --yes typescript@5.6.3 tsc --noEmit --strict contract/owm-decisions.ts`. Expected: no
    output.
- [ ] **Step 5: Commit** ("contract: owm-decisions v2 and its route list").

### Task 1.8: `authz.fga` and its model tests

**Files:**
- Create: `contract/authz.fga` (§6.5's draft; relations may be renamed, but no use-case or org
  names may be added), `contract/authz.fga.yaml`

- [ ] **Step 1: Write the model tests** in OpenFGA's store-test format. Tuples for a toy org:
  - two people in `function:f1`;
  - `agent:g1 acts_for` one of them;
  - `use_case:u1` with `may_decide` and `may_approve` granted to `function:f1#member`;
  - `action:x1` under `u1`, with `may_request_clearance` granted to `agent:g1`;
  - `decision:d1` under `u1`, with `requester` one of the two people.

  Assertions:
  - each member `may_decide` on `u1`, and an outsider doesn't;
  - `agent:g1` has no `may_approve` on `u1`, since a grant would add it;
  - `viewer` on `d1` holds for the requester, and for a `may_approve` holder through the use case;
  - `list_objects(agent:g1, may_request_clearance, action)` gives `[action:x1]`;
  - `may_register` holds only for members of the function given it.
- [ ] **Step 2: Run `fga model test --tests contract/authz.fga.yaml`.** Expected: FAIL, since there
  is no model yet.
- [ ] **Step 3: Write `authz.fga`.**
- [ ] **Step 4: Run the model tests again.** Expected: every test passes. Then load the model into
  P0's Authorizer and record that it loaded in `docs/spikes/p0-authorizer.md`.
- [ ] **Step 5: Commit** ("contract: OpenFGA model and its tests").

### Task 1.9: The ports

**Files:**
- Create:
  - `contract/owm_contract/shapes.py` (`VersionRef`, `Unread`, `Snapshot`, `RecordRead`,
    `JudgmentQuestion`, `JudgmentAnswer`, `Clearance`, `ActionDef`, `ExecutionReport`, `Event`);
  - `contract/owm_contract/auth.py` (`AuthOutcome`, `TokenClaims` and the reason enum, verbatim from
    the bundle's sovera-owm contracts, plus `act: Actor | None = None` on `TokenClaims`, A-1);
  - `ports/owm_ports/{evidence,records,judgment,executor,events,clock,identity,access,errors}.py`;
  - `tests/ports/test_ports.py`.

**Interfaces:**
- **Produces:**
  - The §9.5 Protocols, with exactly the spec's method names and signatures: `EvidenceProvider`,
    `RecordReadProvider`, `JudgmentEngine`, `ActionExecutor`, `EventStore` and `Clock`.
  - `IdentityProvider` and `AuthorizationProvider` as ABCs (PL-14).
  - Port errors in `owm_ports.errors`: `EvidenceUnavailable`, `RecordsUnavailable`,
    `UndeclaredRead`, `JudgmentUnavailable(reason: Literal["down", "cap", "out_of_type"])`,
    `EventConflict`, `EventStoreUnavailable`, `ExecutionFailed`. `ExecutionFailed` is defined but
    not raised before P3.
  - `AccessHealth` (Protocol): `healthy() -> bool`, which the Access adapter implements alongside
    the port (§9.2).
  - `JudgmentQuestion` carries its `answer` type, using Task 1.4's three forms.
  - `Snapshot`, `VersionRef` and `Unread` are F1's shapes, as in the spec's §9.5 and the bundle.

- [ ] **Step 1: Write the failing tests.**
  - `test_shapes_are_frozen`.
  - `test_minimal_fakes_satisfy_the_protocols`: a few-line fake of each Protocol, assigned to a
    variable annotated with the Protocol. mypy checks this.
  - `test_auth_ports_are_abcs_with_async_methods`: `inspect.iscoroutinefunction` holds for
    `whoami`, `verify_token`, `check` and `list_objects`.
  - `test_token_claims_act_is_optional`.
- [ ] **Step 2: Run `uv run pytest tests/ports -v` and `uv run mypy`.** Expected: FAIL.
- [ ] **Step 3: Write the files.**
- [ ] **Step 4: Run both again.** Expected: PASS.
- [ ] **Step 5: Commit** ("contract, ports: the seams").

### Task 1.10: The interfaces the lab calls (PL-5), and the MCP tools

**Files:**
- Create:
  - `contract/owmctl.md`, `contract/org-package.md`, `contract/operator.md`,
    `contract/sor-stub.md`, `contract/mcp-tools.md`;
  - `contract/schemas/owmctl-decide-output.schema.json`, `contract/schemas/mcp/*.json`;
  - `tests/contract/test_interfaces.py`.

**`owmctl`** writes JSON to stdout and diagnostics to stderr. Exit codes:

| Exit code | Meaning |
|---|---|
| 0 | Done, including a routed decision |
| 2 | Usage or configuration error |
| 3 | No decision. stdout holds `{"error": OwmError}` |
| 4 | Refused. stdout holds a v1.4 `Refusals` body |

```
owmctl decide   --corpus DIR --register STORE --type TYPE --subject ID --clock ISO8601
                [--org PACKAGE]                       # required from P4 on
                [--jev live|replay] [--jev-cap-usd N] [--recordings DIR]
owmctl register --store STORE --corpus DIR submit ENTRY.yaml --text DOC --as PERSON_ID
owmctl register --store STORE --corpus DIR approve|decline|withdraw CHANGE_ID --as PERSON_ID
owmctl register --store STORE --corpus DIR revoke DOC_ID --as PERSON_ID
owmctl register --store STORE list [--on DATE]
owmctl org load PACKAGE --service URL --kf URL --sor URL      # from P4 on
```

- `--corpus DIR` holds `documents/` and `structured/`, as the bundle's evidence does. Until P3 it
  is read only through the directory-backed fakes.
- From P4, `--org PACKAGE` supplies the profile and the record exports (`exports/`). Documents
  still come from `--corpus DIR/documents/`, so the lab can point at a corpus variant. Variants
  differ in documents only.
- `--clock` is timezone-aware.
- `--jev live` is the default and requires `--jev-cap-usd`.
- `--jev replay` replays only `--recordings DIR`. A miss is `judgment_unavailable`.
- `decide`'s stdout matches `owmctl-decide-output.schema.json`:

  ```
  {record, procedure: {id, version, sha256}, pack: null | {use_case, version},
   profile: null | {org, version}}
  ```

  `record` is the kernel's decision record exactly as the ported kernel returns it, so the lab can
  compare like with like.

**The org package** (`org-package.md`):

```
package.yaml                 {org, profile: profile.yaml, kf_corpus}
profile.yaml
documents/                   Markdown or text only → one Knowledge Foundation base (K3)
exports/<source>/<table>.csv → sor_stub, read as df:<source>.<table>
principals.yaml              people: [{employee_id, email}], agents: [{id, accountable}]
register/NN-<slug>.yaml      in registration order: {entry, text, submitted_by, approved_by}
grants/*.yaml · delegations/*.yaml   each with submitted_by and approved_by
```

- The loader acts as each named person in turn.
- Generated test credentials go to `var/secrets/` and are never printed.
- The package holds no expected outcomes.

**The test-mode operator surface** (`operator.md`):
- It exists only when the service starts with `OWM_TEST_MODE=1`. The service then binds 127.0.0.1
  only.
- Every call needs the token in the file named by `OWM_OPERATOR_TOKEN_FILE`.
- Routes:
  - `GET` and `PUT /api/v1/operator/clock` `{now}`;
  - `POST /api/v1/operator/reset`, which goes back to the loaded package;
  - `PUT /api/v1/operator/faults`
    `{evidence, records, judgment, access, executor: null | "down" | "slow" | "unreadable" | "out_of_type"}`;
  - `POST /api/v1/operator/tokens` `{principal, act, subject, ttl_seconds}`, which mints a test
    token. It works only while the Identity adapter is the fake, so through P4, or later with
    `OWM_IDENTITY=fake`.

**sor_stub** (`sor-stub.md`):
- Reads:
  - `GET /sor/{source}/{table}?fields=`;
  - `GET /sor/{source}/{table}?field=&value=&fields=`;
  - `GET /sor/{source}/{table}/{key}?fields=` → `{key, version, fields, read_at}`, or 404.
- Writes:
  - `POST /sor/{source}/{table}` creates a row. It takes a person's token.
  - `PATCH /sor/{source}/{table}/{key}` `{fields, expect_version}` takes either a person's token,
    or the executor's token with `clearance`. It returns 409 on a version mismatch.
  - Agent tokens get 403 on every write.
- `GET /sor/log?since=` is the edit log.
- `version` is opaque, and changes on any edit.

**MCP tools** (`mcp-tools.md`):
- Each tool has an input and output schema in `contract/schemas/mcp/`. The core tools are
  `decide`, `get_decision`, `request_clearance` (with `dry_run`), `report`, `register`, `evidence`
  and `approve` (§10.1).
- The generated-tool rule: an action's tool takes its name from the action, and its input schema
  from the action's `params`. A param path `subject.key` becomes a string property; an
  `inputs.<name>` path becomes a property of that input's type.
- Visibility comes from `GET /api/v1/me`'s `visible` (PL-12).
- Errors pass through unchanged.

- [ ] **Step 1: Write the failing tests.**
  - `test_owmctl_output_example_validates`.
  - `test_each_mcp_schema_has_an_example_that_validates`.
  - `test_generated_tool_rule_example`: §4.2's `apply_discount` params give exactly the input
    schema in `tests/contract/examples/apply_discount.tool.json`, which you write by hand from the
    rule.
  - `test_operator_routes_are_not_in_routes_yaml`. They're test-mode only and documented apart.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Write the five documents and their schemas.**
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit** ("contract: owmctl, org package, operator surface, sor_stub, MCP tools").

### Task 1.11: The telemetry contract (PL-15)

**Files:**
- Create:
  - `contract/telemetry.yaml`;
  - `contract/owm_contract/telemetry.py`;
  - `tests/contract/test_telemetry.py`.

**Interfaces:**
- **Produces:** `owm_contract.telemetry`, which holds stdlib constants only.
  - `SPANS: Mapping[str, SpanSpec]`. `SpanSpec(name_template: str, kind: str,
    required: tuple[str, ...], on_success: tuple[str, ...] = (), on_error: tuple[str, ...] = ())`
    is a frozen dataclass. `required` always holds. `on_success` holds when the span's work
    succeeded (a decision was made), and `on_error` when it didn't. The keys are `http_route`, `decide`, `port`,
    `judgment`, `mcp_tool_call`, `execute` and `agent`, matching §9.7's table row for row.
  - `ALWAYS_FORBIDDEN: tuple[str, ...]`:
    - `http.request.header.authorization`;
    - `http.request.header.cookie`;
    - `http.request.header.x-api-key`.
  - `CONTENT_ATTRIBUTES: tuple[str, ...]`. These appear only when someone turns content capture on:
    - `gen_ai.input.messages`, `gen_ai.output.messages`;
    - `gen_ai.system_instructions`;
    - `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result`.
  - `CONVENTIONS_COMMIT: str`, the `semantic-conventions-genai` commit the contract follows.
  - The attribute-name constants, `ATTR_DECISION_ID = "owm.decision.id"` and so on, one per
    attribute in §9.7.

- [ ] **Step 1: Write the failing tests** in `tests/contract/test_telemetry.py`.
  - `test_spans_match_the_spec_table`: the seven keys above.
    - `decide` is `("owm.decide {decision_type}", "INTERNAL", ...)`.
    - It has `required == ("owm.decision.type",)`.
    - Its `on_success` is `owm.decision.id`, `owm.outcome`, `owm.procedure.id`,
      `owm.procedure.version`, `owm.pack.version` and `owm.profile.version`.
    - Its `on_error` is `("error.type", "owm.error.who_can_fix")`. `mcp_tool_call` is
    `("tools/call {tool}", "SERVER", ...)` and requires `mcp.method.name`, `mcp.session.id` and
    `gen_ai.tool.name`.
  - `test_yaml_and_constants_agree`: every span and attribute in `telemetry.yaml` has a constant,
    and every constant appears in the YAML.
  - `test_on_success_and_on_error_disjoint`: for every span, `on_success` and `on_error` share
    nothing.
  - `test_conventions_commit_is_a_full_sha`: it matches `^[0-9a-f]{40}$`.
  - `test_forbidden_and_content_lists_disjoint_from_required`: no span may list a forbidden or
    content attribute in `required`, `on_success` or `on_error`.
- [ ] **Step 2: Run `uv run pytest tests/contract/test_telemetry.py -v`.** Expected: FAIL, because
  the module doesn't exist.
- [ ] **Step 3: Write `telemetry.yaml` and `owm_contract/telemetry.py`.**
  - Take the conventions commit from
    `gh api repos/open-telemetry/semantic-conventions-genai/commits/main --jq .sha` on the day you
    write it.
  - Check the GenAI and MCP attribute names against that commit's `docs/gen-ai/` pages.
- [ ] **Step 4: Run the tests.** Expected: PASS.
- [ ] **Step 5: Commit** ("contract: telemetry (spans, attributes, forbidden list)").

### Task 1.12: The contract's README and the freeze (gate)

**Files:**
- Modify: `contract/README.md`, which indexes every file, gives the version `2.0-rc1`, and lists the
  structural-check rules SC-n

- [ ] **Step 1: Run `uv run pytest`, `uv run mypy`, `uv run ruff check` and
  `fga model test --tests contract/authz.fga.yaml`.** Expected: everything passes.
- [ ] **Step 2: Commit and push. Ask the user and the lab to review `contract/`.** Make each review
  round's changes as new commits.
- [ ] **Step 3: Once the user says it's frozen, tag `contract-v2.0-rc1` and push the tag.** From
  then on, the contract changes only by amendment.

---

## Phase P2: the port

The ported kernel runs behind the ports with directory-backed fakes, reached through `owmctl`. Use
case wiring stays hand-written in this phase, in `cli/` and in modules the P4 tasks will remove.

**Gate:** the lab runs its 32 discount and credit scenarios through `owmctl decide`, and they give
the lab's results (PL-2).

### Task 2.1: The directory-backed fakes and the evidence facade

**Files:**
- `adapters/owm_adapters/dirfake/{evidence,records}.py`
- `core/owm_core/evidence.py`
- `tests/adapters/test_dirfake.py`, `tests/core/test_evidence_facade.py`

**Interfaces:**
- **Produces:**
  - `DirEvidence(root: Path)`, an `EvidenceProvider` over `root/documents/`. `source_id` is the file
    name and `version` is 1. Text comes from the file.
  - `DirRecords(root: Path, declared: Mapping[str, Sequence[str]])`, a `RecordReadProvider` over
    `root/structured/<table>.csv`. Its source is `dir:<table>`, and the version is the sha256 of the
    row's bytes. It raises `UndeclaredRead` for any read outside `declared`.
  - `owm_core.evidence.EvidenceView(snapshot, texts: Mapping[VersionRef, str], tables)`, which keeps
    the ported kernel's interface:
    - `docs() -> list[Doc]`;
    - `table(name) -> list[dict[str, str]]`;
    - `ref_of(filename) -> VersionRef`.
  - The edge builds the view by calling the ports, so `core/` stays free of I/O.

**Tests:**
- A snapshot lists documents sorted by file name.
- `text()` checks the text against `text_sha256`.
- `find_text` returns only current matches.
- An undeclared read raises.
- `EvidenceView.docs()` parses each text the way the bundle's kernel does.
- A document whose text can't be decoded goes into `unread`, never silently dropped.

**Done when** the tests pass and the boundary tests still pass.

### Task 2.2: The spec runner and the kernel in `core/`

**Files:**
- `core/owm_core/{kernel,flow,governed,additions}.py`, ported from the bundle, without the SLA
  branch
- `packs/discount/procedure.yaml` and `packs/credit/procedure.yaml`: the bundle's `discount.yaml`
  and `credit_v3.yaml`
- `tests/core/test_flow.py`, `tests/core/test_kernel.py`

**Interfaces:**
- **Produces:**
  - `owm_core.flow.run(spec: Mapping[str, Any], eng: JudgmentEngine, ev: EvidenceView,
    inputs: Mapping[str, Any], register: Register | None = None, trace: Trace | None = None)
    -> dict[str, Any]`. It takes a parsed spec; YAML is parsed by the caller.
  - `owm_core.governed.decide(decision_type: str, eng, ev, inputs, at: datetime,
    register: Register, procedures: Sequence[Procedure]) -> dict[str, Any]`. It picks the
    procedure in force on `at` and adds `procedure: {id, version, sha256}`.
  - `owm_core.kernel.Register(entries, text_of: Callable[[str], str | None])`. Its `store_dir` is
    replaced by a lookup the edge supplies.
  - `owm_core.kernel.fingerprint(text: str) -> str`. It strips a leading UTF-8 byte-order mark
    before the kernel's existing normalization (§9.6).
- **Consumes:** Task 2.1's `EvidenceView`, and Task 1.9's `JudgmentEngine`.

**Tests:**
- The runner's expression language follows the bundle's `SPEC_FORMAT.md`: each construct it lists
  evaluates, and an unknown name raises `SpecError`.
- On a small org of your own, a governed decision picks the procedure in force on `at`, and none in
  force raises `NoProcedureError`.
- `fingerprint` gives the same value with and without a byte-order mark.
- Judgments go only through the `JudgmentEngine` port.

**Done when** the tests pass and `test_core_does_no_io` passes.

### Task 2.3: The judgment adapter (Jev)

**Files:**
- `adapters/owm_adapters/jev/{client,recorder,cap}.py`, ported from the bundle's Jev client
- `adapters/owm_adapters/fakes/judgment.py`
- `tests/adapters/test_jev.py`

**Interfaces:**
- **Produces:**
  - `JevEngine(key_file: Path, cap_usd: Decimal, recordings: Path, mode: Literal["live", "replay"])`,
    implementing `JudgmentEngine`.
  - The fake `ScriptedJudgment(answers: Mapping[str, JudgmentAnswer])`.
- **Environment:** `TYPESAFE_API_KEY_FILE`, `OWM_JEV`, `OWM_JEV_CAP_USD`, `OWM_JEV_RECORDINGS`.

**Tests** (with an HTTP fake; nothing calls Jev):
- Live mode records each call as JSONL, keyed by a sha256 of model, state and questions.
- Replay reads only the recordings directory it was given. A miss raises
  `JudgmentUnavailable("down")`.
- Reaching the cap raises `JudgmentUnavailable("cap")` before the request is sent.
- The key is read from the file, never from the environment's value, and never appears in a log or
  a recording.

**Done when** the tests pass. The first live call waits for the user's go on spend.

### Task 2.4: The register's rules, and `owmctl register`

**Files:**
- `core/owm_core/register/{rules,state}.py`, ported from the bundle's registrar: rules RR-1 to
  RR-14
- `cli/owm_cli/register.py`, `cli/owm_cli/store.py` (a SQLite file: entries, changes, and the texts
  by sha256)
- `tests/core/test_register_rules.py`, `tests/cli/test_owmctl_register.py`

**Interfaces:**
- **Produces:**
  - `owm_core.register.rules.check(change: Change, state: RegisterState, people: People,
    on: date) -> list[Refusal]`.
  - The `owmctl register` commands exactly as in `contract/owmctl.md`.

**Tests:**
- Each rule from RR-1 to RR-14 refuses its own case on your own org, with the rule's code in the
  `Refusals` body.
- Submit, then approve by a second person, puts an entry in force.
- The submitter approving their own change is refused.
- `list --on` gives only the entries whose window covers the date.

**Done when** the tests pass.

### Task 2.5: `owmctl decide`

**Files:**
- `cli/owm_cli/decide.py`
- `cli/owm_cli/prepare.py`: the bundle's per-type preparation (`TABLE`, `SOURCE`, `NEEDS`), ported
  as it is. Task 4.3 removes it.
- `tests/cli/test_owmctl_decide.py`

**Interfaces:**
- **Consumes:** Tasks 2.1–2.4.
- **Produces:** `owmctl decide`, exactly as in `contract/owmctl.md`.

**Tests:**
- On your own org, a decision prints JSON that validates against
  `owmctl-decide-output.schema.json`, with exit code 0.
- A subject with no row behaves the way v1.4 did. The catalog gate replaces this in Task 4.4.
- A judgment failure exits 3 with `judgment_unavailable`, and writes nothing.
- An unknown `--type` exits 2.

**Done when** the tests pass, and a run on the bundle's Northstar content completes for each
decision type. The lab supplies the clocks and the register at its gate, so these runs check only
that the command completes.

### Task 2.6: The builder's own org, end to end (PL-10)

**Files:**
- `orgs/fernhill/` (documents, exports, register entries)
- `tests/e2e/test_fernhill_p2.py`

**Tests:** these run on fernhill, through `owmctl` only.
- A request inside the requester's own band is approved.
- One above it needs approval.
- One with no policy in force routes.

**Done when** they pass. Then push, and ask the lab to run the P2 gate.

---

## Phase P3: the service

owm-decisions v2's routes are served. Decision behaviour stays v1.4's; P4 changes it.

**Gate:** the lab's 24 register attacks run through the register API, and none is admitted.

### Task 3.1: The SQLite event store

**Files:**
- `adapters/owm_adapters/sqlite_events/store.py`
- `adapters/owm_adapters/fakes/events.py`
- `tests/adapters/test_sqlite_events.py`

**Interfaces:**
- **Produces:** `SqliteEventStore(path: Path)`, an `EventStore`. Events are append-only, with a
  per-stream `seq`.
  - `append(..., expect_last_seq=n)` raises `EventConflict` unless the stream's last `seq` is `n`.

**Tests:**
- Append, then read, gives the events back in order.
- No update or delete path exists.
- **Review Focus 1:** in `test_concurrent_appends_one_wins`, two threads both append with
  `expect_last_seq=n`. One succeeds and the other raises `EventConflict`.

### Task 3.2: The service's skeleton

**Files:**
- `service/owm_service/{app,errors,access,operator,config}.py`
- `adapters/owm_adapters/fakes/{identity,access}.py`, implementing I1–I8 and the authorization
  table
- `tests/service/test_skeleton.py`

**Interfaces:**
- **Produces:** the FastAPI app factory `create_app(config: Config) -> FastAPI`.
  - Typed-error handlers: `OwmError` maps to its status, and `Refusals` stays as v1.4 has it.
  - A dependency that checks Access on every route, for the actor and the subject (§6.5).
  - `GET /api/v1/about`, `GET /api/v1/me` (PL-12) and `GET /healthz` (PL-11).
  - The operator surface from `contract/operator.md`, mounted only in test mode.

**Tests:**
- `routes.yaml` and the app's route table agree, for method, path and auth.
- A request without a token gets 401 `unauthenticated`.
- With the fake Access unhealthy, every route returns 503 `access_unavailable`, and `/healthz`
  returns 503.
- Operator routes return 404 when test mode is off.
- In test mode, the service refuses to bind anything but 127.0.0.1.

### Task 3.3: The register API and its queue

**Files:**
- `service/owm_service/register/{api,queue,view}.py`, ported from the bundle's register queue and
  routes
- `tests/service/test_register_api.py`

**Interfaces:**
- **Consumes:** Task 2.4's `rules.check`.
- **Produces:** v1.4's register routes, now with Task 1.6's entry shape. Each step does a dry run,
  then the real run, with the scoped RR-13 check. RR-1 maps to 403, RR-13 to 409, and everything
  else to 422.

**Tests:**
- Each RR rule refuses its case through HTTP.
- Two people put an entry in force. One person can't do it alone.
- `source_id` is null for a document the foundation doesn't hold.
- A change approved concurrently by two approvers is applied once.

### Task 3.4: Decisions

**Files:**
- `service/owm_service/decisions/{ask,read,write}.py`
- `service/owm_service/records.py`, the decision record and its assembly, ported
- `tests/service/test_decisions.py`

**Interfaces:**
- **Produces:**
  - `POST /api/v1/decisions` and the read routes.
  - The level, the floor and the ratchet, assessed from the subject's stream (ported from the
    bundle's ratchet module).
  - Every event carries `actor`.
  - A port failure appends `decision.failed` to the subject's stream and returns the typed error.
  - The procedure runs outside any write transaction. The write re-checks DC-6 and the stream's last
    `seq`.

**Tests:**
- A decision is recorded with its procedure.
- DC-6 gives 409 with `existing`.
- Each port failure ends with no decision, a `decision.failed` event, and that port's code.
- Who hears about it follows §9.3:
  - a port outage records a health event on the operators' stream;
  - an unreadable governing document also opens a work item for the role that owns its kind.
- **Review Focus 1:** in `test_two_decides_same_subject_one_409`, two concurrent requests give
  exactly one version.

### Task 3.5: People's steps, and the inbox

**Files:**
- `service/owm_service/steps/{resolve,approve,decline,withdraw,rerun}.py`
- `service/owm_service/approvals.py`
- `tests/service/test_steps.py`

**Interfaces:** v1.4's people steps and `GET /api/v1/approvals`.
- The rules run first, then the write with its re-checks. The rules are DC-2 to DC-5, plus v1.4's
  DC-1, which Task 5.3 replaces with the grant rule.
- Approvers are resolved live from the HR export.

**Tests:**
- Each DC rule refuses its case.
- The requester can't approve.
- A wrong `decision_version` gets DC-5.
- The inbox lists exactly the decisions waiting on the caller, filtered by access.

### Task 3.6: `sor_stub` and `df_stub`

**Files:**
- `adapters/owm_adapters/sor_stub/{app,store}.py`, a separate FastAPI app, as in
  `contract/sor-stub.md`
- `adapters/owm_adapters/df_stub/records.py`
- `tests/adapters/test_sor_stub.py`, `tests/adapters/test_df_stub.py`

**Interfaces:**
- **Produces:** `DfStubRecords(sor_url: str, token_file: Path, declared: Mapping[str, Sequence[str]])`,
  a `RecordReadProvider`.
  - It reads `sor_stub` only through its read routes, never its database file.
  - It raises `UndeclaredRead`, and raises `RecordsUnavailable` on transport errors or 5xx.

**Tests:**
- An edit changes the row's version and appends to the log.
- An agent's token can't write.
- The executor's token writes only with a clearance.
- `PATCH` with a stale `expect_version` gets 409.
- `df_stub` refuses an undeclared field.
- `get` on an absent key returns `None`.

### Task 3.7: The Knowledge Foundation dev server, and the KF adapter

**Files:**
- `adapters/owm_adapters/kf_devserver/app.py` (PL-7)
- `adapters/owm_adapters/kf/provider.py`
- `tests/adapters/test_kf_adapter.py`

**Interfaces:**
- **Produces:** `KfEvidence(base_url: str, token_file: Path)`, an `EvidenceProvider` that follows
  §9.6's rules:
  - one snapshot per decision, with texts cached by `(doc_id, version)`;
  - an `unread` entry raises `evidence_unreadable` at decide time;
  - a media-type guard;
  - `find_text` returns current versions of documents that aren't deleted;
  - `current()` reads K4 and K5.

**Tests** (against the dev server):
- A snapshot over every K2 page.
- An unreadable document means no decision.
- A deleted document's version isn't returned by `find_text`.
- A new version changes what `current()` returns.
- A transport error raises `EvidenceUnavailable`.
- **Review Focus 5:** in `test_bom_crlf_fingerprint_matches_k5`, a document saved with a byte-order
  mark and CRLF endings gets a `fingerprint` equal to its K5 `text.sha256`.

### Task 3.8: Clearance, execution and the executor

**Files:**
- `service/owm_service/clearance/{issue,redeem,execute}.py`
- `adapters/owm_adapters/executor/sor.py`
- `tests/service/test_clearance.py`

**Interfaces:**
- **Produces:**
  - `POST /api/v1/decisions/{id}/clearance`, which supports `dry_run` and answers `would_clear`
    with its reasons.
  - `POST /api/v1/clearances/{id}/execute`, plus the `redeem` and `report` routes the executor uses.
  - `SorExecutor`, an `ActionExecutor` that writes only the action's declared effect fields, with
    the clearance id as the idempotency key.

**Tests:**
- Issuing re-checks the approval, the row version and every basis document by `current()`.
- A changed row refuses the clearance.
- A failed write leaves the clearance unspent, records `execution.failed`, and opens an incident for
  the action's incident-owner role.
- **Review Focus 1:** in `test_execute_twice_concurrently_writes_once`, two concurrent executes give
  one write. The second call gets the first one's report.

### Task 3.9: Telemetry: the setup, the service and port spans, and the secret scan

**Files:**
- `telemetry/pyproject.toml`, `telemetry/owm_telemetry/{__init__,setup,spans}.py`
- `service/owm_service/tracing.py`; the port calls in `adapters/` are wrapped by
  `owm_telemetry.port_span`
- `tests/telemetry/test_setup.py`, `tests/service/test_spans.py`, `tests/helpers/spans.py`
- Modify: the root `pyproject.toml` (the eleventh member), and `tests/boundaries/test_imports.py`
  (`owm_telemetry` imports only the stdlib, `owm_contract` and `opentelemetry`)

**Interfaces:**
- **Consumes:** `owm_contract.telemetry` (Task 1.11).
- **Produces:**
  - `owm_telemetry.setup(service_name: str, env: Mapping[str, str]) -> TracerProvider | None`. It
    returns `None` and installs nothing when `OWM_OTLP_ENDPOINT` is unset. It sets
    `AGNO_TELEMETRY=false` for its process.
  - `owm_telemetry.port_span(port: str, operation: str) -> ContextManager[Span]`. It sets
    `error.type` from a port error's class.
  - The Jev adapter's judgment span, built with `opentelemetry-util-genai`'s `TelemetryHandler`. It
    adds `owm.judgment.question`, `owm.judgment.answer_type` and `owm.judgment.out_of_type`.
  - `tests/helpers/spans.py: assert_matches_contract(spans: Sequence[ReadableSpan]) -> None`.
    - It checks `required` on every span.
    - It checks `on_error` on spans with status ERROR, and `on_success` on the rest.
    - Task 5.7 reuses it.

**Tests:**
- With `OWM_OTLP_ENDPOINT` unset and `OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:<test port>`, a
  decision exports nothing. A listener on the test port receives no request.
- With the in-memory exporter, one `decide` call gives the HTTP route span, `owm.decide {type}`,
  and one `owm.port` span per port call. They are all in one trace, and all pass
  `assert_matches_contract`.
- A run with no decision sets `error.type` to the typed code, plus `owm.error.who_can_fix`.
- An out-of-type Jev answer sets `owm.judgment.out_of_type` to true.
- Executing a clearance gives `owm.execute {action}`.
- **Review Focus 6:** in `test_no_secret_in_any_span`, a register, decide, clearance and execute
  sequence runs with a known fake token and a fake Jev key file. It runs again with
  `OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST=".*"`. Each time, a scan of every
  exported span's name, attributes, events and resource finds neither value, nor `Bearer`.

**Then, once, by hand:**
- Ask the user for the Opik workspace's key (PL-16). They write the headers file themselves.
- Run one fernhill decision with the endpoint set, and confirm it shows as one trace in the
  workspace.
- Report the trace id, never the key.

**Done when** Tasks 3.1–3.9 pass. Then push, and ask the lab to run the P3 gate.

---

## Phase P4: generalize

Use cases become packs and orgs become profiles. The hand-wired places go, and the catalog gate,
authority from terms, typed judgments and the structural check come in.

**Gate:**
- The 22 discount scenarios match again, with Northstar now just configuration.
- The 24 attacks are still not admitted.
- No org or pack names are left in code.

### Task 4.1: Packs as registered data

**Files:**
- `core/owm_core/packs.py`
- `service/owm_service/packs.py` (registration, and writing use-case and action tuples through
  Access)
- `packs/discount_approval/{definition.yaml,procedure.yaml,terms/*.schema.json,findings.schema.json}`
- `tests/core/test_packs.py`

**Interfaces:**
- **Produces:**
  - `PackDefinition` (frozen), and `parse_pack(data: Mapping[str, Any]) -> PackDefinition`, which
    raises `PackError(rules: list[str])` naming the SC rules that failed.
  - Registering a pack is a register kind. Two people approve it.

**Tests:**
- The spec's example parses.
- Each SC rule refuses its case.
- Registering writes `use_case:<name>` and `action:<name>` tuples, and leaves the model unchanged.

### Task 4.2: The profile, and the bindings layer

**Files:**
- `core/owm_core/profile.py`
- `service/owm_service/bindings.py`
- `adapters/owm_adapters/dirfake/records.py` also reads a package's `exports/<source>/<table>.csv`
  as `df:<source>.<table>`
- `orgs/fernhill/profile.yaml`
- `tests/service/test_bindings.py`

**Interfaces:**
- **Produces:**
  - `parse_profile(data) -> Profile`.
  - `Bindings(profile, records: RecordReadProvider)`, with:
    - `read_subject(type, key) -> SubjectRead | None`, which returns values in pack units and None
      when the subject isn't in its catalog;
    - `person_for(claims: TokenClaims) -> PersonRecord | None`;
    - `holders(role) -> list[PersonRecord]`, read live;
    - `org_date(at: datetime) -> date`, in the profile's `time_zone`.

**Tests:**
- Percent and basis points both convert to the same fraction.
- `amount` passes through unchanged.
- **Review Focus 4**, three tests:
  - `test_empty_required_field_routes_missing_input`;
  - `test_malformed_field_is_record_unreadable`, covering `"12,5"`, `"12.5%"` and `"31/03/2026"`;
  - `test_padded_or_wrong_case_subject_id_is_422`.
- **Review Focus 3:** in `test_clock_fallback_as_of_uses_org_date`, with `Asia/Kolkata` and a clock
  of 2026-03-31T19:00Z, the derived `as_of` is 2026-04-01.

### Task 4.3: Removing the hand-wired places

**Files:** the ported counterparts of the bundle's hand-wired places, listed in the table below.
- `tests/service/test_no_hand_wiring.py`

| Bundle source | What's hand-wired there | Becomes |
|---|---|---|
| `models.py` | `DecisionType`, `ROUTE_TO`, outcome literals, the findings union | `outcomes`, `route_to`, `findings` |
| `owm-decisions.ts` | closed decision types, findings, `ActionName` | v2's open types (done in Task 1.7) |
| `_lab.py` | decision type and `ROUTE_TO`; the subject id by type | the pack |
| `procedures.py` | `KIND_OF`, decision type to policy kind | `governing` |
| `prepare.py` | `TABLE`, `SOURCE` and `NEEDS` per type (now `cli/owm_cli/prepare.py`) | the profile's type bindings |
| `sor.py` | key columns per table | the profile's `key` |
| `decisions.py` | request-id prefixes | `id_pattern` |
| `ratchet.py` | `POLICY_KIND` and `FIGURE`; a per-type branch | `ratchet` |
| `clearance.py` | the owning function per type; percent and amount params | `incident_owner_role`, `params` |
| `assemble.py` | findings and actions per type | `findings`, `actions` |
| `conditions.py` | system names | the profile's sources |
| `lab_adapter.py` | action to system and table | the profile's `actions` targets |
| `sessions.py` | decision type literals | gone with sessions |
| `register_view.py` | labels per type | the pack's names |
| `registrar.py` | `OWNER`, `SCHEMA`, per-kind term checks | `governing` plus terms schemas |
| tool server | the hand-written `apply_discount` | the generated tool (Task 5.4) |

**Tests:**
- On fernhill, with its own units, columns, time zone and id pattern, a full decision runs.
- Adding `fernhill` and both packs' names to `names.txt` keeps
  `test_no_use_case_or_org_names_in_the_named_parts` passing.

### Task 4.4: The catalog gate, the as-of rule and claims

**Files:**
- `core/owm_core/deciding.py`, the §7.1 flow, steps 2–10
- `tests/core/test_deciding.py`

**Interfaces:**
- **Produces:** `decide(request: DecideRequest, ctx: DecideContext) -> DecisionResult`. The
  service's step 1 (identity and access) and step 11 (the write) wrap it.

**Tests:**
- A subject or customer that isn't in its catalog routes with a `no_record` finding addressed to the
  requester, and the result has no action.
- A body `as_of` gets 422.
- The requester comes from the token, never from the body.
- A claimed figure that differs from the record's opens a blocking input-conflict condition for the
  requester. The record keeps both figures.
- A pack whose governing documents aren't in force routes (§5.2).
- The record names the pack version and the profile version it ran under.

### Task 4.5: Discount authority from registered terms

**Files:**
- `packs/discount_approval/procedure.yaml`, which reads the bands from terms as the credit
  procedure already does
- `packs/discount_approval/terms/pricing_policy.schema.json`
- `tests/core/test_authority_from_terms.py`

**Tests:**
- The bands come from the entry in force, never from the document's prose.
- Rewording a document's prose, with its terms unchanged, doesn't change who may approve.
- With no entry in force, the decision routes.

### Task 4.6: Typed judgments

**Files:**
- `core/owm_core/judgments.py`
- `tests/core/test_judgments.py`

**Tests:**
- An answer outside its declared type raises `JudgmentUnavailable("out_of_type")`, which becomes a
  503 `judgment_out_of_type`. This applies to a choice not in the options, a number without its
  unit, and a string where a boolean was declared.
- No answer is ever coerced.

### Task 4.7: The structural check, the org loader and the name scan

**Files:**
- `core/owm_core/structure.py` (the SC rules from Tasks 1.4–1.6)
- `org/owm_org/load.py`, `cli/owm_cli/org.py`
- `tests/org/test_load.py`

**Interfaces:**
- **Produces:**
  - `check_structure(pack, profile, records, evidence) -> list[StructureProblem]`.
  - `owmctl org load`, as in `contract/owmctl.md`. It loads documents into a Knowledge Foundation
    base through K3, exports into `sor_stub`, principals as test identities, then registers as the
    named people.

**Tests:**
- Enabling a pack whose binding doesn't resolve is refused.
- Loading fernhill twice is idempotent.
- The loader never puts a CSV into the Knowledge Foundation base.

**Done when** Tasks 4.1–4.7 pass. Then push, and ask the lab to run the P4 gate.

---

## Phase P5: the front door

**Gate** (run by the lab):
- The §8 journey, driven once by the reference agent and once by a plain MCP client.
- The claim test.
- The delegation and grant attacks.
- Failure ends for each port.

### Task 5.1: The Authorizer identity adapter, and token exchange

**Files:**
- `adapters/owm_adapters/authorizer/identity.py`, `adapters/owm_adapters/authorizer/exchange.py`
  (or P0's chosen issuer)
- `tests/adapters/test_authorizer_identity.py` (marked `authorizer`; it needs a local instance)

**Tests:**
- I1–I8 pass.
- An exchanged token has `sub` = the person, `act` = the agent, and the narrowed scope.
- A subject-only exchange is refused.
- **Review Focus 2:**
  - `test_delegated_token_refused_on_other_subject` gives 403 `token_binding`, with nothing
    recorded;
  - `test_expired_delegated_token_401`.

### Task 5.2: The Authorizer access adapter, and its health

**Files:**
- `adapters/owm_adapters/authorizer/access.py`, plus P0's fallback adapter if one was chosen
- `tests/adapters/test_authorizer_access.py`

**Tests:**
- The authorization table passes.
- `check` covers both the actor and the subject, by P0's method.
- With Authorizer stopped, `healthy()` is false, and every service route returns 503
  `access_unavailable`. It never reads as "no access".

### Task 5.3: Grants and delegations in the OWM

**Files:**
- `core/owm_core/authority/{grants,delegations,sod}.py`
- `service/owm_service/steps/grant_rule.py`, which replaces DC-1
- `tests/core/test_grants_delegations.py`

**Tests:**
- An approved grant writes only `may_approve` for its agent on the use case; its limits stay in the
  OWM.
- A delegation writes `acts_for` when it starts and deletes it when it ends.
- The window and scope are checked on every call, so a late tuple deletion still gets a refusal.
- Every grant limit is checked on every step.
- Separation of duties is computed over the humans behind actors.
- The same agent can't hold both sides of one decision.
- `agent_approval: never` refuses an agent approval whatever grants exist.
- A person's own conditions can't be resolved under a delegation.
- Re-delegation is refused.
- **Review Focus 3:** in `test_per_day_cap_counts_in_org_day`, two approvals that fall on the same
  org day but on different UTC dates both count against one day's cap.

### Task 5.4: The MCP server

**Files:**
- `mcp/owm_mcp/{server,tools,generated,visibility}.py`
- `tests/mcp/test_server.py`

**Interfaces:**
- **Produces:** a streamable-HTTP MCP server at `/mcp` on loopback (PL-13).
  - It has the core tools, plus one generated tool per registered action.
  - Visibility comes from `GET /api/v1/me`.
  - Calling an action's tool requests the clearance, then executes it.
  - It reaches the service only through its HTTP API.
  - Each tool call is a `tools/call {tool}` SERVER span (§9.7).
    - It continues the trace from `params._meta.traceparent` and carries the context on to the
      service in the request headers.
    - The OTel Python MCP SDK has no instrumentation, so the span is written by hand to the
      conventions.

**Tests:**
- An agent without an approval grant never sees `approve`.
- An action's tool appears only once the action is registered and `visible`.
- Service errors pass through unchanged.
- **Review Focus 2:** in `test_tool_call_with_token_bound_elsewhere_refused`, a token bound to one
  subject is refused on another.
- No tool's schema has a token field.
- A tool call with a `traceparent` in `_meta` gives spans in that trace, down to the service's
  `owm.decide`.

### Task 5.5: The approver's tool

**Files:**
- `approver/owm_approver/{cli,screen}.py`
- `tests/approver/test_cli.py`

**Tests:**
- A person signs in, lists their inbox, reads a decision, confirms, and approves, each with their own
  token.
- No code path in the package imports a model client. A test checks this, alongside the boundary
  test.

### Task 5.6: The reference agent

**Files:**
- `agent/owm_agent/{agent,mandate,kf_read}.py`
- `agent/config.example.yaml`
- `tests/agent/test_tools.py`

**Interfaces:**
- **Produces:**
  - An Agno agent, configured by its mandate (the person it serves, and its delegation).
  - Its tools are a direct Knowledge Foundation read tool and the OWM's MCP tools. It has no write
    tool.
  - The model and the cap come from its config.
  - It is traced by the Agno instrumentation named in Global Constraints. Its MCP client puts
    `traceparent` in `params._meta`. It is built with `telemetry=False`.

**Tests** (with a scripted model):
- The tool list has no write tool.
- The runtime adds the token header; the model never sees it.
- A refused action is reported as refused, not retried as a write somewhere else.
- With the in-memory exporter, one agent turn gives `invoke_agent` → `execute_tool` →
  `tools/call` in one trace.

### Task 5.7: The journey, and the failure ends, on fernhill

**Files:**
- `tests/e2e/test_journey_fernhill.py`
- `tests/e2e/test_failure_ends.py`

**Tests:**
- §8's journey in symbols, on fernhill, driven by a plain MCP client. It ends with exactly one write,
  of the record's figure, and the claim kept beside it.
- The variants:
  - the row edited to the claimed figure before clearance;
  - the delegation revoked mid-decision;
  - a re-delegation attempt;
  - two hats;
  - over the cap.
- With each port faulted through the operator surface, there is no decision, the typed error comes
  back, and nothing else is written.
- The journey's trace, from the in-memory exporter, is one connected trace from the client's call
  to the port calls, and passes `assert_matches_contract`.
- **Review Focus 6:** the secret scan of Task 3.9, run over the whole journey, finds 0 hits.

**Done when** Tasks 5.1–5.7 pass. Then tag `p5-gate`, push the tag, and ask the lab to run the P5
gate. Its runs use the reference agent, under a spend cap that the lab pre-registers. P6's empty
diff is measured from this tag.

---

## Phase P6: credit as data

**Gate:**
- An empty diff under `core/`, `service/`, `contract/` and `mcp/` since the P5 gate's tag.
- Credit's 10 scenarios match.

### Task 6.1: The credit pack

**Files:**
- `packs/credit_limit/{definition.yaml,procedure.yaml,terms/*.schema.json,findings.schema.json}`.
  The procedure is the bundle's `credit_v3.yaml`, which already reads terms.
- `orgs/fernhill/` gets credit bindings, register entries and a profile version.
- `tests/e2e/test_fernhill_credit.py`

**Tests:**
- On fernhill, a credit decision runs end to end, and its generated tool appears.
- `agent_approval: never` on credit refuses every agent approval.

### Task 6.2: The empty-diff proof

**Files:**
- `scripts/empty_diff.sh`

- `git diff --stat p5-gate HEAD -- core service contract mcp` must print nothing. The script
  lives in `scripts/`, outside the diff it checks.

**Done when** the script prints nothing and Task 6.1 passes. Then push, and ask the lab to run the
P6 gate. Handover to sub-project 3 follows.
