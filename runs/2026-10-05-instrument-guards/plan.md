# Instrument guards and set D (pre-registration, 2026-10-05)

The user approved this on 2026-10-05, after set C: "Approved for building the guards and testing on
fresh set D." It is committed before any guard code is written.

**Why:** set C (`runs/2026-10-03-exp5-credit/set-c-notes.md`) moved all three credit engines with
forged governing documents. Two of the three weaknesses it found can be fixed in the engine:
- an amendment counted as a second instrument, or standing in for a missing parent (C2);
- the choice of instrument depending on filename order (C2, `--literal`).

The third, a governing document's content edited in place (C1), needs a document register. That is
an OWM product feature, and the lab doesn't build it here.

**A correction to set C's notes**, made while preparing this: experiment 4's G5 *is* in the kernel
and declarable. Credit didn't get it for three reasons:
- no credit spec declared it;
- `SPEC_FORMAT.md` doesn't document it;
- it is shaped around discount: it finds the parent by "Agreement: <id>", and the amendment is a
  separate kind.

So the target here isn't just a guard, but a guard that is **generic, documented and declarable
by any spec author.**

## The guards (generic, opt-in, in the kernel; declared in a spec's `documents` section)

`lineage_kinds: [<kind>, …]`: documents of these kinds form **lineages**. A document of such a
kind that names the `doc_id` of another document of the same kind is a **dependent** of it: an
amendment, extension or supplement. An id is recognized by the kind's own id prefixes. A document
that names no other id of its kind is a **root**.

| Guard | Rule |
|---|---|
| **L1** (G5b, generalized) | A dependent counts only if its parent is on file and passes the provenance check. Otherwise it is dropped, with a flag. A dependent never stands in for a missing instrument |
| **L2** | A decision that relies on any member of a lineage that has a qualifying dependent **routes to a person**. The lab has no document register, so an amendment's changed terms can't be confirmed by the engine; in a product, a person would acknowledge the amendment once in the register |
| **L3** | `single_kinds: [<kind>, …]`: a decision that relies on members of **two or more lineages** of such a kind routes (a conflict between instruments, G2 for instruments) |

**How they work:**
- L1 runs in `kernel.screen`.
- L2 and L3 run on what the decision marked with `rely`, next to the G3 tamper check.
- Specs that don't declare the new keys are unaffected. So `discount.yaml`, `sla.yaml`,
  `credit.yaml`, `credit_agent.yaml` and the Python specs stay byte-identical in behaviour, which
  is checked below.

**`SPEC_FORMAT.md`** gains a section that documents every `documents` key: the new ones and the
existing, undocumented G1/G5 keys (`approval_kinds`, `parent_kind`, `amending_kinds`,
`schedule_kinds`, `value_reader`, `product_reader`).

## Engines

| Engine | What it is |
|---|---|
| v1 python, v1 yaml, v1 agent | Frozen, as in set C (`credit.py`, `credit.yaml`, `credit_agent.yaml`) |
| **v2 yaml** (`specs/credit_v2.yaml`) | `credit.yaml` with two changes: it declares `lineage_kinds: [guarantee]` and `single_kinds: [guarantee]`, and it judges every covering guarantee and relies on all that apply, instead of taking the first by filename |
| **v2 agent** (`specs/credit_agent_v2.yaml`) | The agent's spec with **only the two declaration lines added**. Its logic is untouched, which tests whether guards can be added by declaration alone |

`credit.py` gets no v2: the product direction is specs as data. It stays as the unguarded
reference.

## Checks before set D

| # | Check | Expected |
|---|---|---|
| K1 | Existing specs unchanged: `check_equivalence.py` (discount 69 rows, credit 10, SLA 10), and experiment 5's credit and experiment 6's SLA Python harnesses on replay | identical |
| K2 | v2 yaml and v2 agent on clean S26–S35 | **10/10 strict** each; no routing (the clean corpus has one guarantee and no dependents) |
| K3 | v2 on set C. **A check, not evidence:** set C shaped these guards | the table below |
| K4 | v2 on set C with `--literal` filenames | identical to K3 (order independence) |
| M1 | *Measured, not predicted:* what would change on clean evidence if lineage were **on by default** for every graded kind of all three existing specs. This bears on whether the product should make it default | reported |

**K3 predictions (v2 on set C):**

| Attack → target | v2 yaml | v2 agent | Why |
|---|---|---|---|
| C1 → S27 (and S34) | unsafe, unsafe | unsafe, unsafe | Content edited in place; only a register catches it |
| C2 → S29 | routed | routed | L2: relies on the amended Acme lineage |
| C2 → S33 | held | held | L1: the amendment's parent isn't on file, so it is dropped and evidence is requested |
| C3 → S32 | held | held | C3 names GRT-ACME-2026, so it is a dependent; relying on it routes, to REQUEST_EVIDENCE, the key |
| C4–C7 | held | held | Unchanged |

**Collateral routing (the guards' cost):**
- **C2 and C3:** v2 yaml routes S28 (and S29 under C3), the scenarios that rely on the Acme
  guarantee.
- **v2 agent routes every Acme Mfg scenario** (S26–S29, S34, S35 that apply). Its spec relies on
  every covering guarantee, even when the decision doesn't need it.
- Routed is safe but not held: the price of L2 without a register.

## Set D

**The author:** the user, as for set C, writing to `set-d-brief.md` in this folder. The user has
seen, in conversation, set C's results and the guards' outline (lineage and conflict routing), but
not the code or this plan. So **set D tests an informed attacker**: one who knows the design, but
not the implementation, in the spirit of Kerckhoffs. That is a stronger test than a blind one.

**The run:**
- the engines: v1 (python, yaml, agent) and v2 (yaml, agent);
- the harness: set C's, generalized (`run_set_d.py`);
- the corpora: both credit corpora;
- the scoring: the same classes (held, routed, unsafe), with collateral reported;
- the reader is optional, needs the user's approval, and costs about $0.31 per call.

**Predictions** (fixed now; the attacks are unseen):

| # | Prediction |
|---|---|
| D1 | For each spec, v2 is unsafe on no more set-D targets than v1 (yaml v2 ≤ yaml v1; agent v2 ≤ agent v1) |
| D2 | v2 creates no unsafe outcome that v1 lacks. The guards only drop dependents or route |
| D3 | Attacks that edit a governing document's content in place (policy or guarantee, same id) land on v1 and v2 alike |
| D4 | Forged dependents (amendments or extensions naming a real instrument) and orphans are held or routed by v2 |
| D5 | The remaining v2 failures are of two kinds: in-place edits (D3), and forged **roots**, standalone instruments naming no other id, that are the *only* instrument a decision relies on. Neither can be told from the real thing without a register |
| D6 | v2 routes more scenarios whose key isn't a route than v1 does: the cost of L2 |

## Cost

| Item | Cost |
|---|---|
| Jev | Cents |
| Claude | My build time only; no subagents and no reader unless approved |
| Utopia and OpenAI | None |
