# Experiment 6: a non-approval decision, SLA breach response (2026-10-03)

**STATUS: DONE.** Pre-registered in `plan.md` (`ad490d0`), with the kernel frozen at `47238c6`.
The rules and situations were written by a blind subagent and committed unchanged (`f998502`).

**The question:** discount and credit share one approval skeleton. Does the decision substrate
hold for a decision whose core question isn't "who may approve this?"? SLA breach response is
event-triggered, with no requestor. Its answer is obligations with deadlines, and clocks drive it.

## Verdict: SUBSTRATE, by the pre-registered rule, with caveats

| The rule's test | Result |
|---|---|
| (a) No kernel code branches on the decision type | ✓ The kernel mentions discounts and credit only in docstrings |
| (b) Discount and credit behave identically | ✓ `check_behaviour.py`: discount sets A and B byte-identical to v3, credit S26–S35 identical. It was run after every kernel change, and after `employees.csv` gained the four support staff. |
| (c) The new capabilities are kernel modules any spec could use | ✓ K-5 to K-9 (below) |
| (d) The SLA spec reimplements none of provenance, windows, conflict, identity, role mapping or routing | ✓, after **three fixes found in my own audit** before the reader runs: coverage start (K-9 and `covering`); the DUNS match (`linked`); and "one schedule in force" (`in_force`, exposed from inside `authority_from_evidence`) |
| (e) All three decision types fit one envelope | ✓ `envelope.py`: 42 decision records (22 discount, 10 credit, 10 SLA) |
| (f) Hybrid ≥ 90% strict | ✓ **10/10**, raw and gated. That covers every severity, breach, credit, and obligation with its due time. |

## How it was built

| Step | Commit | What |
|---|---|---|
| Plan, with the brief verbatim | `ad490d0` | Kernel frozen; verdict rule fixed |
| The blind rule sheet | `f998502` | R1–R55, situations S36–S45, written by a subagent that read only `dataset/evidence/` |
| Truth, evidence, oracle | `566b8fd` | `truth/support.yaml`, `generators/support.py`, `src/northstar/sla.py`. **The oracle reproduced all ten of the subagent's hand-worked outcomes on the first build,** including about 30 escalation deadlines. |
| SLA spec on the kernel | `571baac`, `735198d` | `lab/owm_kernel/sla.py`, kernel K-5 to K-9, and `in_force` |
| Reader | `d91e007` | The SLA procedure and harness, committed before any reader call |

## The kernel changes the SLA spec forced

The diff against the experiment-6 freeze is +160 / −11 lines (500 → 649).

| # | Change | Class |
|---|---|---|
| K-5 | **Clocks:** a business calendar (zone, hours, holidays) and a 24×7 or business-hours clock with excluded intervals (pauses, maintenance windows). Elapsed time, and the moment a duration is reached. | New primitive, generic |
| K-6 | **Obligations:** who owes what, by when, or whether a counterparty's duty was met | New primitive, generic |
| K-7 | **Routing without a requestor:** the single holder of a title; the owner a system-of-record row names | New primitive, generic |
| K-8 | The gate's routing outcome as a parameter (it was hard-coded to `REQUEST_EVIDENCE`) | Generalization |
| K-9 | Open-ended validity windows (`effective_from` with no `effective_to`) | Generalization |
| `in_force` | The G2 "one in force, else conflict" rule, exposed as a function | Refactor of existing logic |

The pipeline assumption the plan worried about didn't block anything.
- **The worry:** "a request with a requestor and an amount".
- **Why it didn't bite:** that assumption sits only in `authority_from_evidence`, which the SLA
  spec doesn't call.
- **What that says:** the kernel is a toolkit of governed primitives, and each spec writes its own
  flow. That is a finding in itself (below).

## Results

| Arm | Result | Prediction |
|---|---|---|
| Hybrid (kernel + SLA spec) | **10/10 strict**, raw and gated. Jev's severity judgments were all correct, at confidence 0.97–1.0. It flagged the one note that asserts the customer-caused exclusion (S45: 0.84) and passed the others (0.02, 0.17). | P3: ≥ 90% ✓ |
| Reader (Opus + SLA procedure, gold evidence, 2 runs each) | **16/20 strict, 20/20 core** (every outcome, severity, breach finding and credit right), **0 unsafe** | P4: ≥ 70% strict ✓, ≤ 2 unsafe ✓ |
| Where the reader missed | **Obligation-listing conventions only:** see below. **No clock arithmetic was wrong.** It got the Memorial Day clock, the weekend clock, the pause that lands exactly on the target, the EDT→CT claim deadline, and the v1.0/v2.0 boundary. | P4: misses on clocks and exclusions ✗ |
| Kernel primitives needed | 5 (K-5 to K-9), plus one exposed, with no special-casing | P1: ≥ 3 ✓ |
| One envelope | ✓ with `obligations[]` | P5 ✓ |
| Verdict | SUBSTRATE | P2 ✓ |

**The reader's four non-strict answers** all had the right outcome, severity, breach and credit:
- **S45, runs 1 and 2:** listed the credit memo (Paul Brennan, by 2026-09-19). The situation itself
  calls that duty conditional on approval; my answer key leaves conditional duties out. This is a
  convention of mine, not a reader error.
- **S37, run 2:** added a "phone report: not applicable" line.
- **S43, run 2:** listed customer obligations for an out-of-scope ticket. The rules say none arise
  there. This is a small substantive slip.

## What it shows

1. **The substrate holds for a decision of a different shape.** An event-triggered decision with
   no requestor, whose answer is obligations with deadlines and clocks, ran on the same kernel.
   - **What it took:** five generic additions, and nothing that branches on the type.
   - **What it reused:** provenance, validity windows, the conflict rule, identity by a
     registered key, role mapping, gating and products-in-text, all unchanged.
   - **What it left alone:** discount and credit didn't move.
2. **One decision envelope covers all three types:** an outcome from a declared vocabulary, plus
   `obligations[]`, reasons and evidence. For BlueLeaf, the OWM decision record can be one shape,
   with obligations as a first-class part of it. A discount approval is an obligation too ("Michael
   Torres must approve"), which the current records don't yet say that way.
3. **The kernel is a toolkit, not a pipeline.** Each spec writes its own flow: discount 210 lines,
   credit 207, SLA 456. That is why SLA didn't trip over the approval assumptions, and it is also
   what's left for "spec as data".
   - **The flow is the procedure's job:** a governed procedure object whose steps call kernel
     primitives (screen, judge, in_force, clocks, routing, obligations, gate).
   - **The backlog:** a generic flow runner over the procedure.
4. **On clean gold evidence, the agent is good at this too:** 20/20 on substance, with perfect
   clock arithmetic. The substrate's case doesn't rest on accuracy over clean evidence. It rests on:
   - safety under adversarial documents (experiment 4: the reader unsafe on 17/24 subtle forgeries);
   - determinism and auditability (the same answer every time, each obligation traced to a rule);
   - cost: well under a cent of Jev per decision, against about $0.33 per Opus reader answer here.

## Caveats (read these before quoting the verdict)

- **Only the rules and situations were blind.** I wrote the truth transcription, the oracle, the
  evidence, the kernel additions, the SLA spec and the harnesses. The oracle and the spec are both
  my implementations of the rules.
  - **The independent check:** both reproduce the subagent's hand-computed answers, and so does
    the reader.
- **I found three spec shortcuts in my own audit,** and fixed them by routing through the kernel
  before the readers ran. A fourth reviewer might find more.
- **Documents are still parsed by pattern:** the targets table, the credit table, the cap, the
  windows, the procedure's numbers. The product answer is unchanged: schedules, terms and
  procedures as structured, registered objects.
- **The tickets were written by an expert to be unambiguous.** Jev's severity calls were at
  confidence 0.97–1.0. Real ticket text is messier, so the severity question will route more often.
- **One synthetic company,** gold evidence only, 2 reader runs per situation.
- **Data changes:**
  - `employees.csv` gained four support staff (logged). Every other existing evidence file is
    byte-identical, and so are the 35 earlier answer-key entries.
  - Account owners of background-owned accounts are recorded by CRM account, so results stay
    seed-stable.
- **Housekeeping:** `owm/ontology.yaml` wasn't updated for SLA. Concepts the experiment surfaced
  for the ontology are Ticket and Event, Clock and Calendar, Obligation, Exclusion and
  ServiceLevel targets.

## For BlueLeaf (amendment candidates)

- **The decision record is one envelope:** an outcome from a declared vocabulary, plus
  `obligations[]` (who owes what, by when; or whether a counterparty met a duty).
- **Clocks and calendars are kernel primitives.** That covers business hours, holidays, time
  zones, pauses and exclusion windows. Every service, compliance and contract decision needs them.
- **Routing is a primitive separate from approval:** a role's single holder, a record's owner.
- **Specs should become data:** a procedure object whose steps call kernel primitives. That
  closes the toolkit gap and is the natural next build.
- **Across experiments 4, 5 and 6:** governed approvals, a second approval type and a non-approval
  decision all ran on one kernel with one record shape. The open risks are integrity (signed
  forgeries need a register), structured policy objects, and a flow runner.

## Cost

| | Cost |
|---|---|
| Claude, readers | 20 calls, **$6.58** (reduced from 30, as pre-registered) |
| Claude, the rules subagent | about 231k tokens |
| Jev | 23 new calls, under $0.001 |
| Utopia, OpenAI | none |

## Files

| File | What it holds |
|---|---|
| `plan.md` | The pre-registration, the brief and the reader addendum |
| `rules/` | The blind subagent's rule sheet and situations |
| `envelope.py` | Verdict test (e) |
| `check_behaviour.py` | Verdict test (b) |
| `run_hybrid.py`, `hybrid-results.md`, `hybrid-decisions.json` | The SLA hybrid |
| `run_reader.py`, `reader-results.{md,json}`, `reader/` | The reader, with transcripts |
| `engine-calls.jsonl` | The Jev recording |
| `lab/owm_kernel/sla.py`, `src/northstar/sla.py`, `truth/support.yaml`, `owm/procedures/sla-response.md` | The SLA spec, the oracle, the truth and the procedure |
