# Specs as data (pre-registration, 2026-10-04)

The user said "Go for Specs as data" on 2026-10-04. This was the next build that experiments 5 and 6
pointed to. Committed before any runner or spec code is written.

**Why now:**
- Three decision types run on one kernel, but each needs its own Python spec: discount 210 lines,
  credit 207, SLA 456.
- That code holds the decision's questions, its readings of its own documents, its flow, its
  outcome table and its record.
- Experiment 6 found that the kernel is a toolkit, not a pipeline, and that the flow is the gap.

**The question:** can a governed decision be written as **data** (a procedure object) and executed
by a generic runner over the kernel's primitives, with no decision-specific code? And can an agent
author such a spec correctly?

## The design (fixed now; details may change, the principles won't)

A spec is one YAML file, a governed procedure object, in `lab/owm_kernel/specs/`. It has:

| Section | Holds |
|---|---|
| `outcomes`, `route_to` | the declared outcome vocabulary, and the outcome a person should see when unsure |
| `documents` | the kinds, owners and provenance settings (G1 to G5), as the `Guards` today |
| `readers` | named readers over documents: a regex, a table row, a table, a paragraph, a section |
| `questions` | the Jev questions |
| `steps` | an ordered list of named values, each computed by **one generic operation** (look up a row, link by a key, judge, documents in force, select an instrument, authority and approvers, concurrence, a clock, a holder or owner, filter, map) or by an **expression** |
| `outcome` | an ordered decision table of conditions → outcome |
| `obligations` | rules of condition → obligation template |
| `record` | the decision envelope's fields, mapped from named values |

**Expressions** use a small, safe language, interpreted from the Python AST with a whitelist and
never `eval`ed. It allows:
- arithmetic, comparisons, boolean logic and conditionals;
- subscripts, and dict and list literals;
- comprehensions;
- whitelisted pure functions (`min`, `max`, `sum`, `len`, `round`, `any`, `all`, `float`, `int`,
  `date`, `datetime`, `days`, `minutes`, `latest`, …).

It does not allow imports, dunder access, lambdas or arbitrary calls. In industry terms this is
DMN-like: decision tables plus a FEEL-like expression language, with OWM-governed primitives
(provenance, judgment, clocks, routing, obligations) as the operations.

**The rule for the runner and its operations:** they must be generic. Logic a spec can't express
becomes either a generic kernel operation (counted, and classified as in experiments 5 and 6) or a
finding. **No decision-specific Python is allowed.**

## Phase 1: the three decision types as data, equivalent to their code specs

**Checks** (the existing harnesses, with each spec swapped from code to data):
- **Discount:** experiment 4's rows for sets A and B, byte-identical to `hybrid-{a,b}-v3.json`.
- **Credit:** the decision fields of S26–S35, identical to experiment 5's `hybrid-decisions.json`.
- **SLA:** the decisions of S36–S45, identical to experiment 6's `hybrid-decisions.json`, in
  outcome, gated outcome, uncertain, scope, severity, breach, credit and obligations.

**Measured:**
- the lines of decision-specific Python per type (the target is 0);
- the YAML lines per type;
- the lines of the generic runner, operations and expression evaluator;
- each new kernel operation, classified.

## Phase 2: can an agent author a spec as data?

- **The author:** a subagent writes the **credit** spec as YAML. It is given:
  - `lab/owm_kernel/SPEC_FORMAT.md`, the format reference (written in phase 1, describing
    sections, operations, expressions and primitives, with no decision logic);
  - the credit procedure (`owm/procedures/credit-limit.md`);
  - the company's documents (`dataset/evidence/`).
- **What it can't see:** the kernel code, the existing specs (YAML or Python), the answer key and
  the truth.
- **One attempt plus one fix round:** if the runner rejects the spec, the subagent gets only the
  runner's error messages. It never sees scores or expected answers.
- **Scoring:** run on S26–S35 and scored like experiment 5's hybrid (strict: outcome, eligibility,
  requestor-authorized, approvers).

## Predictions

| # | Prediction |
|---|---|
| D1 | All three data specs reproduce their code specs exactly (the three checks above) |
| D2 | **0 lines** of decision-specific Python. The YAML is about 1–1.5× the Python lines it replaces. The runner and operations are under about 800 lines |
| D3 | **At least 1 new generic kernel operation** is forced. The likely one is *select the governing instrument*: live by window and party, covering, not superseded, the latest, and a conflict when values disagree. It is shared by the discount exception and the credit guarantee, the EligibilityInstrument the ontology gained in experiment 5 |
| D4 | The agent-authored credit spec scores **≥ 8/10 strict** after at most one fix round, and the runner catches structural errors before any decision is made |
| D5 | Where the agent's spec is wrong, it is wrong in a **reviewable** way: a wrong regex, a wrong band reading, a missing condition, all visible in the YAML, not hidden in code |

## Cost

| Item | Estimate |
|---|---|
| Jev | Cents (the replays cover phase 1; phase 2 may ask a few new questions) |
| Claude | The phase-2 subagent, about $1–2 |
| Readers | None |
| Utopia and OpenAI | None |

## Phase 1 results (recorded before phase 2 starts)

- **D1 ✓.** All three data specs reproduce their code specs exactly:
  - discount sets A and B, byte for byte (69 rows);
  - credit S26–S35, identical;
  - SLA S36–S45, identical, including obligations, flags and the account owner.
- **D2 ✓, and better than predicted.** There is no decision-specific Python. The YAML is *smaller*
  than the Python it replaces: discount 142 lines against 210, credit 98 against 207, SLA 248
  against 456. The runner is 438 generic lines.
- **D3 ✗.** No new kernel operation was forced; `kernel.py` is byte-identical (sha256 `5bb188e3…`).
  Instrument selection (live, covering, not superseded, latest, conflict) was expressible with
  generic pure helpers in the runner (`latest`, `unique_by`, `union`) and comprehensions. The
  runner gained generic helpers (`latest`, `unique_by`, `intervals`, `union`, `paragraph`,
  `groups`, `maybe`) and allowed string methods. None of them knows a decision type.
- `SPEC_FORMAT.md` was written after these specs. It describes sections, expressions and functions
  only, with no decision logic and no example from the three decision types.
