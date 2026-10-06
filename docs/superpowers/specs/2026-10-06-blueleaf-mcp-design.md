# BlueLeaf lab MCP server: design (skunkworks, 2026-10-06)

**Status:** design approved section by section in chat on 2026-10-06. The buildability review
(§11, the same day) found no blocker, and its fixes are folded in below. The build plan is written
by a separate agent from the kickoff doc, and the user runs the build. Branch:
`skunkworks/blueleaf-mcp`.

## 1. Purpose

A local MCP server that lets a person run Northstar experiments from **Claude Desktop**, over the
same corpus the lab uses. It replaces the zip-and-Claude-Code loop with one conversation: draft an
attack, plant it, run the engines, put a blind agent to the test, and score the results.

**The brief, as agreed:**

| | |
|---|---|
| Users | The user, in two roles. Each role is a mode, fixed when Claude Desktop connects |
| Experimenter mode (`blueleaf-lab`) | Claude Desktop is the lab assistant. It can see the answer key and the scoring |
| Subject mode (`blueleaf-subject --arm …`) | Claude Desktop is the agent under test, and is blind. It gets only the tools of its arm: `plain`, `register` or `owm` |
| Where | This Mac only. Claude Desktop launches the server over stdio |
| Knobs in v1 | Documents, the register, procedures, live Jev calls |
| Record | Sessions are scratch by default; `promote` writes a run folder. Findings reach the Ledger only by a deliberate step |
| Build | A new package on the official MCP Python SDK, with two entry points |

**Assumptions the user confirmed:**
- **The same corpus:** `dataset/evidence` and its two variants. The six sealed attack sets (A–F)
  are available as seeds.
- **Sandboxes:** named working copies that both modes can open. A subject never sees a sandbox's
  name.
- **Scoring:** happens in the server, in experimenter mode only. Subject answers are logged for the
  experimenter to score.
- **Spend:** live Jev calls are capped per session, and the TypeSafe key is never surfaced.
- **Success:** one Desktop conversation, in minutes, with no zip and no Claude Code session.

**Not in v1:**
- remote or multi-user access;
- a `claude -p` reader arm (in subject mode, Claude Desktop is the agent);
- Utopia in the loop;
- writing to the Lab Ledger;
- any change to `src/northstar` or `dataset/`.

## 2. Architecture

```
lab/blueleaf_mcp/
  service/            plain Python, no MCP; shared by both modes; never touches the answer key
    sandbox.py        create, open, list and delete sandboxes; apply attack-set manifests; change log
    engines.py        the engine table; run a spec or engine on a sandbox; Jev replay or live under a cap
    register.py       a per-sandbox register overlay: register, approve, remove, mismatch mode, served view
    procedures.py     per-sandbox copies of the YAML specs: read, write (validated), list
    journal.py        session log, subject-answer log, seal state, promote
  scoring.py          experimenter only: answer key, classifiers, side effects, scorecards, question text
  lab_server.py       entry point `blueleaf-lab`
  subject_server.py   entry point `blueleaf-subject --arm plain|register|owm`
  README.md           Claude Desktop setup
```

- **Reuse:** `lab/owm_kernel` (kernel, flow runner, specs), `lab/owm_register` (registrar, store,
  `serve.py`) and `lab/decision_engine` (Jev: `Recorder`, `Replay`, `TypeSafe`). They are imported
  as top-level modules (`kernel`, `flow`, `engine`, `credit`, `serve`) from paths that one small
  boundary module, `service/_lab.py`, puts on `sys.path`, as the harnesses do (§11, B9–B10).
- **The frozen instruments in `runs/`** are loaded by path, never copied, and only by `scoring.py`
  on the experimenter side: the classifiers, the reader graders and the request-record builders
  (§11, B2). `service/` re-declares only the engine table and the attack-manifest rules, and tests
  tie both to committed results.
- **Dependency:** the MCP Python SDK goes into a new dependency group, `mcp`, in `pyproject.toml`.
  The normal lab install, `src/northstar` and the dataset build are unchanged. The existing
  stand-in, `lab/owm_standin/server.py`, stays as it is.
- **State** lives in a gitignored `.blueleaf/` at the repo root: `sandboxes/`, `sessions/`,
  `subject.json`, `seal`.

### 2.1 The three walls around the answer key

1. **Imports.** `subject_server.py` and `service/` never import `scoring.py`, `northstar.model`
   truth loading, `truth/`, `dataset/answer-key/` or `dataset/evaluation/`. A test checks this.
2. **Files.** Every path a subject tool takes is resolved and must fall inside the current
   sandbox's corpus folder for that question. Otherwise it is refused. The subject also reads the
   served register and the prose procedures in `owm/procedures/`, and nothing else.
3. **The seal.** Claude Desktop offers every enabled server in every chat, so blindness can't
   depend on the user switching the lab server off.
   - Opening a subject session writes `.blueleaf/seal`.
   - While the seal exists, every lab tool except `seal_status` refuses. An engine's decision
     would also leak the likely answer.
   - The seal lifts itself once every question in the session has a submitted answer. An answer
     submitted after that is logged as `late` and is not scored.
   - `uv run --group mcp python lab/blueleaf_mcp/lab_server.py unseal` lifts it by hand (an abort).

`subject.json` holds, per question label, only what a subject may use: the corpus name, the
decision type and the decision inputs (for example the CRM request record and its date). It
never holds an expected outcome. A test checks its schema.

## 3. Sandboxes

- **Layout:** `.blueleaf/sandboxes/<name>/` holds:
  - `corpora/{base,missing-contract-evidence,missing-guarantee-evidence}/`: full copies, about
    550 KB in all;
  - `register/`: a copy of `lab/owm_register/*.yaml` **and of its `store/`** (84 KB, 17 texts).
    `Register.load` reads `<yaml>/../store`, so each sandbox carries its own, and new approved
    texts are added there (§11, B4);
  - `procedures/`: a copy of `lab/owm_kernel/specs/`;
  - `jev-calls.jsonl`: the sandbox's new Jev calls;
  - `manifest.yaml`: the seed, the dataset commit, and every change with its time and its sha256.
- **Seeds:**
  - `clean`;
  - a whole sealed attack set (`set:A` … `set:F`), applied by that set's own `manifest.yaml`
    (`add` or `replace`, across every corpus, as `run_set_f.build` does);
  - one attack (`attack:F6`).

  The seal hashes of an attack set are checked before it is applied.
- **Changes:** plant, edit (a whole replacement, or an exact find-and-replace) and remove a
  document. A change applies to every corpus unless one is named. `dataset/` is never written.
- **Mismatch mode** is a per-sandbox setting, `use_registered` (the default) or `route`. It is
  applied to the `+R`-family engines' declarations.

## 4. Tools

### 4.1 `blueleaf-lab` (experimenter)

| Group | Tool | What it does |
|---|---|---|
| Sandboxes | `create_sandbox(name, seed)` | `seed`: `clean`, `set:X` or `attack:Xn` |
| | `list_sandboxes()`, `show_sandbox(name)`, `delete_sandbox(name)` | `show` gives the manifest and change log |
| Documents | `list_documents(sandbox, corpus?)`, `read_document(sandbox, file, corpus?)` | |
| | `plant_document(sandbox, file, text, corpus?)` | adds a document, or replaces one |
| | `edit_document(sandbox, file, find, replace, corpus?)` | an exact, single-match find-and-replace |
| | `remove_document(sandbox, file, corpus?)`, `diff_document(sandbox, file, corpus?)` | `diff` compares against the dataset original |
| Register | `show_register(sandbox, corpus)` | entries, versions, relations, terms |
| | `register_document(sandbox, file, kind, registered_by, approved_by, terms?, corpus?)` | the caller supplies any structured terms, and the registrar's text checks run where that kind has one. With no terms, the document is registered with its approved text only. Refuses when one person is both registrar and approver (§11, B8) |
| | `remove_registration(sandbox, doc_id, corpus?)`, `set_mismatch_mode(sandbox, mode)` | |
| | `served_register(sandbox, corpus, decision_type)` | exactly what a `register`-arm subject would see; `serve.served` gains an optional `root` argument for a sandbox's register (§11, B4) |
| Procedures | `list_procedures(sandbox)`, `read_procedure(sandbox, name)` | |
| | `write_procedure(sandbox, name, yaml)` | validated by `flow.load`; errors name the line |
| | `check_procedure(sandbox, name)` | clean scenarios of its type against the key |
| Decide and score | `run_scenarios(sandbox, engines?, scenarios?, live_jev=false)` | decisions classed held / routed / unsafe / error against the key, plus side effects against the `clean` seed |
| | `explain_decision(sandbox, engine, scenario)` | the full record: flags, judgments, register status |
| | `scenario_info(scenario)` | question, request record, expected answer |
| Subject sessions | `open_subject_session(sandbox, scenarios, arm)` | writes `subject.json`, sets the seal, returns the questions as Q1…Qn to paste into a subject chat |
| | `subject_answers(session?)` | answers, scored with the reader classifiers (discount, credit, SLA) |
| Housekeeping | `seal_status()`, `jev_budget()` | |
| | `predict(sandbox, text)` | time-stamped predictions, recorded before results |
| | `promote(sandbox, slug, title)` | writes the run folder (§6) |

**Engines (`engines.py`):**
- discount: `discount`, `discount+R`, `discount+Ru`;
- credit: `v1 python`, `v1 yaml`, `v1 agent`, `v2 yaml`, `v2 agent`, `v2+R yaml`, `v2+R agent`,
  `v3`, `v3u`, `v2+Ru yaml`, `v2+Ru agent`;
- SLA: `sla`, `sla+R`, `sla+Ru`;
- `proc:<name>` for a procedure written in the sandbox.

The default is the register engines plus each type's frozen baseline. Scenarios default to every
scenario of each engine's type: discount uses experiment 4's 18, credit S26–S35, SLA S36–S45.

### 4.2 `blueleaf-subject --arm …` (blind)

| Arm | Tools |
|---|---|
| `plain` | `list_documents(question)`, `read_document(question, file)`, `get_procedure(decision_type)`, `submit_decision(question, decision)` |
| `register` | `plain`, plus `get_register(decision_type)` (the served register of the question's corpus) |
| `owm` | `register`, plus `decide(question)`: runs the default register engine for the question's type on the sandbox, with the sandbox's Jev setting. Returns the decision record and never a score |

- `question` is the neutral label (Q1…Qn) from `subject.json`. The subject never sees a sandbox
  name, a corpus name or a scenario id. `decide` passes the label as the engine's `sid`, which
  only fills the record's `scenario` field and is not part of any Jev request (§11, B7).
- `submit_decision(question, decision, explanation?)` takes the JSON decision block the
  procedure specifies. It is logged with the session id and time, and graded exactly as the parsed
  block from a reader's text would be (§11, B13).
- The arm is fixed by the server's command line. The user switches arms by switching which
  subject server is enabled.

## 5. Engines, Jev, spend and secrets

- **Replay first.** At start-up, one merged recording is built from every `engine-calls.jsonl`
  and `*-engine-calls.jsonl` under `runs/`, de-duplicated by hash (about 32,000 calls). It is
  cached under `.blueleaf/`. The sandbox's own `jev-calls.jsonl` is layered on top.
- **A judgment that was never recorded:**
  - with `live_jev` off, `Replay` stops at the first judgment it has never seen, so the decision is
    classed `needs_live_jev`, with no partial result. The response counts the decisions affected,
    not the judgments (§11, B5);
  - with it on, a layered engine answers from the merged recording, then the sandbox's recording,
    and only then goes live through `Recorder(TypeSafe("jev-1.13.0"))` (§11, B6). Live calls are capped per session at
    **200 new calls** by default. New calls are appended to the sandbox's recording. At the cap,
    the tool returns an error that names it.
- **Secrets:**
  - The Desktop config carries only `TYPESAFE_API_KEY_FILE=<repo>/_owm-local/typesafe.key`.
  - No tool returns the key, and no log contains it.
  - Before any tool output is returned, it is checked for the key's text; a match is replaced
    with an error.
- **Determinism:** decisions use each scenario's `as_of` or `decided_at`, never today. The same
  sandbox with the same recordings gives byte-identical results.

## 6. Records

- **Session log:** `.blueleaf/sessions/<session-id>.jsonl`, one line per tool call from either
  server:
  - the time, the server and arm, the tool and its arguments;
  - a result digest.

  Document text is stored as a sha256 with the text kept in the sandbox. Subject answers go to
  `.blueleaf/sessions/<session-id>-answers.jsonl`.
- **`promote(sandbox, slug, title)`** writes `runs/<date>-skunkworks-<slug>/`. It refuses if the
  folder exists. Contents:
  - `notes.md`: a status banner, the seed, the change list, predictions with their timestamps
    against the results' timestamps, scorecards, and open questions left blank for the user;
  - `manifest.yaml`, plus the planted and edited documents under `documents/`;
  - `results.json` and `results.md`, and the subject answers with their scores;
  - `jev-calls.jsonl`, holding only the new calls.

  It neither commits nor writes to the Ledger.

## 7. Errors

Every failure is an MCP tool error with one plain sentence, and the server keeps running.
- **Named errors:** an unknown sandbox or file, an ambiguous edit match, an invalid spec (with
  `SpecError`'s line), the seal being on, the Jev cap, an attack set whose seal hashes don't
  match.
- **An engine that raises on a document** (as the frozen SLA spec did in set F) is recorded as
  class `error` for that decision, and the other decisions still run.

## 8. Testing

These run with the existing pytest, ruff and mypy. Tests that need the MCP SDK use
`pytest.importorskip("mcp")`.

| # | Test |
|---|---|
| T1 | **Import wall:** start `subject_server.py` in a subprocess for each arm, list its loaded modules, and assert that none is `scoring`, a truth loader or an answer-key reader |
| T2 | **File wall:** subject `read_document` refuses `../`, absolute paths and symlinks out of the corpus |
| T3 | **Seal:** lab tools refuse while sealed; the seal lifts after the last answer; late answers are marked; `unseal` works |
| T4 | **`subject.json` schema:** labels, corpus, decision type and inputs only; no outcome field anywhere |
| T5 | **Engine table:** a `set:F` sandbox by replay reproduces `runs/2026-10-06-register-fixes/withhold/set-f-results.json` for every engine, under that check's rule that a `withheld:` decision is routed. The earlier `set-f-results.json` predates G-32. `clean` is all held outside credit v1, as committed (§11, B3) |
| T6 | **Dataset untouched:** `dataset/` is hashed before and after a scripted session and is byte-identical |
| T7 | **Secret guard:** with a dummy key file, no tool output or log line contains the key |
| T8 | **Tool lists:** each mode and arm lists exactly the tools in §4, through an in-memory MCP client |
| T9 | **Replay without spend:** `run_scenarios` with `live_jev=false` makes no network call; a new document yields `needs_live_jev` |
| T10 | **Graders pinned:** the reader graders, loaded by path, re-grade the committed `runs/2026-10-05-register-all/reader-set-f-results.json` answers to the same safety classes |

## 9. Setup (README)

There are four Claude Desktop entries in `~/Library/Application Support/Claude/claude_desktop_config.json`:
`blueleaf-lab`, `blueleaf-subject-plain`, `blueleaf-subject-register` and `blueleaf-subject-owm`.
Each runs:

```
uv run --directory <repo> --group mcp python lab/blueleaf_mcp/<lab|subject>_server.py [--arm …]
```

with `TYPESAFE_API_KEY_FILE` in `env`. The README explains:
- enabling only the lab server and one subject server;
- that a subject chat is blind because of the seal, even when the lab server is enabled.

Claude Desktop starts servers with a minimal `PATH`, so `command` is the absolute path of `uv`
(from `which uv`) (§11, B11). The user edits the Desktop config; the build does not write it.

## 10. Done when

In one Claude Desktop conversation pair:
1. `create_sandbox("f6", "attack:F6")`, then `run_scenarios`. `credit v3u` holds S34, and the frozen
   credit engines route it, as committed in set F.
2. `open_subject_session("f6", ["S34"], "register")`, then in a new chat with
   `blueleaf-subject-register`, Claude answers Q1 and submits.
3. Back in the lab chat, the seal has lifted, and `subject_answers` scores the answer with set F's
   reader grade. It is comparable with set F's rf2 check (held 3/3 after the term fix).
4. `promote("f6", "f6-replay", …)` writes a run folder that a reader can follow without the chat.

## 11. Buildability review (2026-10-06)

**Verdict: buildable, no blocker.** Each item below was checked against the code on `main` at
`bd0fb70`. Items B3, B5 and B8 change the spec's contract; the rest guide the build.

| # | Finding | Resolution |
|---|---|---|
| B1 | The MCP Python SDK's v2 renamed `FastMCP` to `MCPServer` and replaced `mcp.shared.memory.create_connected_server_and_client_session` with `mcp.client.Client`, which takes a server directly | Pin the major version that is current at build time in the `mcp` dependency group, and use that version's API throughout, including for T8 |
| B2 | The reader graders (`runs/2026-10-03-adversarial/run_reader.py` `classify`, `runs/2026-10-03-exp5-credit/run_reader.py` `grade`, `runs/2026-10-03-exp6-sla/run_reader.py` `grade` and `people`, `runs/2026-10-03-exp5-credit/run_set_c_reader.py` `unsafe_type`), the harness classifiers and the request-record builders all live in `runs/`. Re-declaring them invites drift | `scoring.py` loads them by path, lazily, as the harnesses do. Only the experimenter side does this. T10 pins the graders, and T5 pins the classifiers |
| B3 | `runs/2026-10-05-register-all/set-f-results.json` predates G-32's withholding (`bd0fb70`), so the route-mode rows differ today | T5's baseline is `runs/2026-10-06-register-fixes/withhold/set-f-results.json`, with its rule (a `withheld:` flag counts as routed); `scoring.py` applies the same rule |
| B4 | `Register.load(path)` reads its texts from `path.parent / "store"`, and `serve.served(corpus, decision)` reads only its own folder | Copy `store/` into each sandbox's `register/`. Add an optional `root: Path \| None = None` to `serve.served`. It is backward compatible, since the committed runs call it without one |
| B5 | `Replay` raises `KeyError` at the first unrecorded request, so the number of new judgments a decision needs can't be known in advance | The decision is classed `needs_live_jev`, and the tool reports how many decisions were affected |
| B6 | `Recorder` and `Replay` each read one file, and neither counts live calls | A small layered engine in `engines.py` satisfies the engine protocol (`.model`, `.ask(state, questions)`): it checks the merged replay, then the sandbox's recording, then goes live through a `Recorder` on the sandbox file, with a call counter for the cap |
| B7 | `sid` reaches only the record's `scenario` field in every spec and in `credit.decide`; Jev's request hash covers `model`, `state` and `questions` | Subject `decide` passes the label (Q1…) as `sid`, so its records show no scenario id and replay still hits |
| B8 | The registrar's terms come from `truth/`, and a subject-side tool can't use truth. Credit v3 and v3u read the credit policy's terms from the register | Terms are an optional argument of `register_document`, checked against the text where the registrar has a check for that kind. An engine that needs a missing term fails that decision as `error`, with a message naming the term |
| B9 | `kernel.py`, `flow.py`, `engine.py` and `serve.py` show 13 errors under `mypy --strict`, and mypy covers `src/` and `tests/` only | Add `lab/blueleaf_mcp` to mypy's `files`; it must be strict-clean. Add a `[[tool.mypy.overrides]]` with `follow_imports = "skip"` for `kernel`, `flow`, `engine`, `credit`, `serve` and `build_register`; they are reached only through `service/_lab.py`, which types what it re-exports |
| B10 | The lab modules are top-level names (`kernel`, `flow`, `engine`) on `sys.path`, as in every harness | `service/_lab.py` owns that path setup; nothing else touches `sys.path` |
| B11 | Claude Desktop starts servers with a minimal `PATH` | The README's config uses the absolute path of `uv` |
| B12 | Two processes share `.blueleaf/` | One writer per file: the lab writes `subject.json` and `seal`, the subject writes answers and removes `seal`, and each server writes its own session log. Writes are atomic (a temp file, then a rename) |
| B13 | The graders take the decision block parsed from a reader's text | `submit_decision` takes that block as JSON and passes it to the grader unchanged |
| B14 | A Desktop subject reads documents through tools. The reader arms had every document in the prompt | Subject results are comparable in kind, not in protocol. `promote`'s notes say so |
| B15 | `.blueleaf/` must never be committed | Add it to `.gitignore` |

