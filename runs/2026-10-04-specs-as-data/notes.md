# Specs as data (2026-10-04)

**STATUS: DONE** (phases 1 and 2). Pre-registered in `plan.md` (`714c263`).

**The question:** can a governed decision be written as data (a procedure object) and executed by
a generic runner over the kernel's primitives, with no decision-specific code? And can an agent
author one?

**The short answer:** yes to both, on this evidence.
- The three decision types now run as YAML specs, with identical decisions.
- An agent that never saw the kernel, the existing specs or the answer key wrote a credit spec
  that scored 10/10 at its first attempt.

## Phase 1: the three decision types as data

| | Python spec | YAML spec | Equivalence |
|---|---|---|---|
| Discount | 210 lines | 142 lines | **69/69 rows byte-identical** to experiment 4's v3 (clean, sets A and B: every attack, flag and uncertain judgment) |
| Credit | 207 lines | 98 lines | **10/10 identical** to experiment 5's decisions |
| SLA | 456 lines | 248 lines | **10/10 identical** to experiment 6's decisions: obligations, due times, flags, account owner |

**The runner** is `lab/owm_kernel/flow.py`, 438 lines, generic. A spec has:
- sections: `documents` (provenance), `helpers`, `readers`, `questions`, `steps`, an `outcome`
  decision table, `then`, `obligations` and `record`;
- values that are expressions in a safe subset of Python syntax. The runner interprets them from
  the AST against a whitelist, and never calls `eval`.

In industry terms this is DMN-like: decision tables plus a FEEL-like expression language. The
operations are the OWM's governed primitives: provenance, judgment, policy in force, identity by
key, authority, concurrence, clocks, routing and obligations.

| # | Prediction | Result |
|---|---|---|
| D1 | All three data specs reproduce their code specs exactly | ✓ |
| D2 | No decision-specific Python; YAML about 1–1.5× the Python; runner under 800 lines | ✓, and the YAML is **0.5–0.7×** the Python. Runner: 438 lines |
| D3 | At least one new generic kernel operation is forced (instrument selection) | **✗** `kernel.py` is byte-identical. Instrument selection (live, covering, not superseded, latest, conflict) needed only generic helpers in the runner (`latest`, `unique_by`, `union`) and comprehensions. |

**How the specs were made:** I transcribed the three YAML specs from the Python specs. The runner
gained generic pieces while I did it, none of which knows a decision type:
- pure helpers (`latest`, `unique_by`, `intervals`, `union`, `paragraph`, `groups`, `maybe`);
- a `then` section;
- `ask`, for questions built from governed content;
- lazy generator expressions;
- a few allowed string methods.

The whitelist rejected `isdigit` and `rstrip` until I added them. That is the safety design
working.

## Phase 2: an agent authors the credit spec

- **What the agent could see:** only `SPEC_FORMAT.md` (the format reference written after
  phase 1), the credit procedure, and `dataset/evidence/`.
- **What it couldn't see:** the kernel code, the other specs, the truth or the answer key.
- **How it worked:** it wrote YAML only and ran no code.
- **What it produced:** a 242-line `credit_agent.yaml`, committed as delivered (`989dbc2`).

| Step | Result |
|---|---|
| The runner loads and runs it on S26–S35 | **No errors at the first attempt.** The fix round wasn't needed. |
| Scored against the answer key | **10/10 strict, raw and gated:** outcome, eligibility, requestor-authorized, and every approver and concurring signer |

| # | Prediction | Result |
|---|---|---|
| D4 | At least 8/10 strict after at most one fix round, with structural errors caught before deciding | ✓ **10/10 with no fix round** (there were no structural errors to catch) |
| D5 | Errors are reviewable in the YAML | **Not tested:** it made no errors. The spec is reviewable: every step is commented, and it raises 13 kinds of flags for missing or odd data |

**What the agent's spec does, read by me afterwards:**
- **It reads every number from the policy text:** the look-back period, the separate lateness
  allowances for paid and unpaid invoices, and the per-tier maximums by tier name. It hard-codes
  no amount, name or answer.
- **It uses the governed primitives:** `linked` (identity by DUNS), `in_force`, `authority`,
  `concurrences`, `covering`, and recorded judgments, so gating works.
- **It asks two narrow judgment questions,** with careful instructions. One asks what the request
  relies on ("a remark that support might be used later does not count"). The other asks whether
  the guarantee covers this customer ("the guaranteed party, not the guarantor … a parent, a
  subsidiary or a similar name is a different company").
- **On two points it is more faithful to the policy wording than my spec.** It ages invoices by
  calendar months rather than 365 days, and applies the paid and unpaid allowances separately.
  Neither changes any outcome here.

## What it shows

1. **Decision logic can live as governed data.** All three decision types, approvals and a
   non-approval, run from YAML on one runner, with no decision-specific code. The data is smaller
   than the code it replaced.
2. **An agent can author a correct governed decision spec** from a format reference, a procedure
   and the documents, without code access, at its first attempt. This is the agents-first shape
   BlueLeaf wants:
   - **agents author and propose procedure objects;**
   - **the OWM validates and executes them deterministically,** with provenance and gating;
   - **people review the YAML,** which is readable, commented and diffable.
3. **The kernel needed nothing new for data specs.** The primitives from experiments 4–6 were
   enough; the missing piece was the flow, and the runner supplies it generically.

## Caveats

- **The primitives the agent relied on were shaped around credit,** in experiment 5:
  `authority()`'s band sentences, `concurrences()`'s "For <Tier> accounts … also require <Role>
  concurrence", and separation of duties. `SPEC_FORMAT.md` documents those contracts.
  - A spec for a decision type the primitives weren't shaped around is the harder test of agent
    authorship. That could be the SLA decision, written by an agent, or a new type.
- **The expression language is code-like.** Readable for an analyst or an agent, and reviewable,
  but not for a non-technical approver. The decision tables and obligations are the readable part.
- **I wrote `SPEC_FORMAT.md`,** knowing the three specs. It contains no decision logic or example
  from them. Still, its choice of primitives and helpers reflects what those specs needed.
- **One synthetic company and gold evidence.** The agent read the same documents the specs run
  on.
- **The phase-1 YAML specs are transcriptions,** so their equivalence shows the runner's
  expressiveness, not authoring ease. Phase 2 is the authoring test.

## For BlueLeaf (amendment candidates)

- **Procedure objects as executable data.** A governed decision is a YAML procedure object: its
  provenance rules, readers, questions, steps, decision table, obligations and record envelope.
  That is the "procedure as a governed object" that experiment 2 (OWM measurements) argued for,
  now executable.
- **Authoring by agents, validation and execution by the OWM.** The OWM:
  - loads and validates (syntax, outcome vocabulary, whitelist);
  - executes deterministically over governed primitives;
  - gates uncertain judgments to people.

  A spec is versioned and diffable, so it can be reviewed like any governed document.
- **Next build candidates:**
  - an agent-authored SLA spec (the harder authorship test);
  - procedure objects stored and versioned in the OWM, with provenance (who authored, who
    approved);
  - the reader-facing prose procedure generated from the same object, so agents and the engine
    read one source.

## Cost

| | Cost |
|---|---|
| Claude, the authoring subagent | about 133k tokens |
| Jev | a handful of new calls (the agent's own questions), under $0.001 |
| Readers, Utopia, OpenAI | none |

## Files

| File | What it holds |
|---|---|
| `lab/owm_kernel/flow.py` | The runner |
| `lab/owm_kernel/SPEC_FORMAT.md` | The format reference |
| `lab/owm_kernel/specs/{discount,credit,sla}.yaml` | The data specs, equivalent to the Python specs |
| `lab/owm_kernel/specs/credit_agent.yaml` | The agent-authored spec, as delivered |
| `check_equivalence.py` | Phase 1 |
| `run_agent_spec.py`, `agent-results.md`, `agent-decisions.json` | Phase 2 |
| `engine-calls.jsonl` | The Jev recording |
