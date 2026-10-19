# ZEN rules spike: pre-registration (G-52)

**Registered 2026-10-19, before the spike's code was written or run.** The user chose "Run the
spike: yes, now ($0, about a day)" on G-52. The analysis is in
`docs/rules-engine-zen-evaluation-2026-10-19.md`.

## Question

Can the register's business tables live as ZEN decision tables, evaluated through a port, with
every decision unchanged?

## Design

- **Engine:** `zen-engine==2.1.3` (PyPI's latest on 2026-10-19), MIT. Run with
  `uv run --with zen-engine==2.1.3`, so it never enters `pyproject.toml` or the lab's dependency
  closure.
- **Tables:** a converter turns each register entry's terms into one JDM graph, saved under
  `tables/`. It does this once, and the evaluated tables are those files.
  - **Credit policies** (2025, 2026), one graph each, with four nodes:
    - a first-hit band table (amount → required title);
    - a first-hit limit table (title → the requestor's limit);
    - a collect concurrence table (amount and tier → concurring titles);
    - an expression node holding separation of duties and its hand-off (`passes_to`).
  - **Pricing policies** (2025, 2026, 2027): a band table (discount → required title).
  - **SLA schedules** (1.0, 2.0): a targets table (severity and plan → response, restoration,
    clock) and a credits table (severity, target and band → percentage).
- **The engine path:** the spike's runner replaces, *in its own process only*,
  `flow.authority_from_terms` and `flow.concurrences_from_terms` with versions that:
  - evaluate the entry's credit table through a `RulesPort` with a ZEN adapter;
  - take the required title, the requestor's limit, the concurrences, separation of duties and its
    hand-off from the table's output;
  - leave resolving *people* to the kernel (the manager-chain walk).

  The kernel, the register files, the specs and the admission gate are not edited.
- **Corpus and register:** the committed ones, read-only. Set G's pre-registered inputs aren't
  touched.

## Checks (pass or fail)

| | Check | Pass if |
|---|---|---|
| **P1** | The admission gate on `credit_v3.yaml` (`--replay`), baseline vs ZEN-backed: A clean, B sealed attack sets, C reliance | The two report JSONs are identical, and live Jev calls are 0 in both |
| **P2** | Equivalence over a boundary grid for every table: each band edge, edge ± 0.01, 0, a negative, 10× the top edge; every tier including an unknown one; every severity × plan × target × band, including unknown values | ZEN's output equals the bespoke evaluation (the kernel's `in_band`, `limit_for`, concurrence rule; a direct lookup for SLA) at every point. The one pre-declared exception is below |
| **P3** | Registration checks. A validator admits only input, output, decision-table and expression nodes, and refuses anything else. A coverage check on band tables flags gaps and overlaps | The real tables pass both. A planted function node is refused. A planted gap and a planted overlap are flagged |
| **P4** | G-33: the separation-of-duties hand-off lives in the table | The ZEN-backed authority reads `separation_of_duties` and `passes_to` from the table output, not the YAML terms. A `passes_to` the kernel can't resolve raises rather than guessing |
| **P5** | Trace | Each ZEN-backed call yields the table file, the entry's version and the matched row id. The clean scenarios' traces are recorded |

**The pre-declared exception (P2):** the kernel's `limit_for` returns `1.0` for a title whose band
is unlimited (`max_inclusive: null`). That's the discount convention, 1.0 = 100%, applied to dollar
amounts. The table states the limit as unlimited instead. The two differ only for a requestor who
holds an unlimited band *and* when separation of duties is off. Separation of duties is on in every
credit policy in all three committed registers (checked before registration). So P1 can't move
because of it. P2 reports it as the one expected difference and does not count it as a failure. It
is logged as a finding.

## Measures (reported, not pass or fail)

- Term size, YAML against JDM (lines and bytes).
- What still lives in code or in the specs:
  - the manager-chain walk;
  - `caps`, which the credit spec reads from the terms directly;
  - SLA targets and credits, which the SLA specs read from the schedule's prose;
  - the people resolution.
- Evaluation time per call.
- **Afterwards, not part of the result:** the user's read-through of one table in the JDM editor,
  for G-11.

## Guards

- **Cost: $0.** No LLM calls; the gate replays recorded Jev answers. Live calls are asserted to be 0.
- **No edits:** `lab/owm_kernel/`, `lab/owm_register/`, `lab/owm_kernel/specs/` and
  `lab/spec_admission/` are checked by sha256 before and after, and must not change.
- **Fail closed:** any difference in P1, or any unexpected one in P2, is reported as found. If the
  *converter* mistranslated, the fix and its reason go into `notes.md` as an amendment to this plan.
  The kernel is never tuned to make a check pass.

## The dry pass (before registration)

`admit.py lab/owm_kernel/specs/credit_v3.yaml --type credit --replay --no-reference` ran once to
confirm the gate replays at $0. The result was A 10/10, B 0 unsafe in 24 attacks, C 0 idle, live
Jev 0. Separately, `zen-engine` 2.1.3 was installed in a throwaway environment and probed on toy
tables: interval cells, collect, list membership, `outputPath`, and an expression node. No register
data went into it.

## Outputs

`tables/*.json`, `outputs/` (the two gate reports, the grid, the traces), `results.md` and
`notes.md`. The code is `spike.py` and `tables.py`, labelled throwaway.
