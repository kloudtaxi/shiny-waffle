# Experiment 5: a second decision type, credit-limit increase (2026-10-03)

**STATUS: DONE.** Pre-registered in `plan.md` (`a34a15a`).

**Set C** (2026-10-05), the user's seven attack documents against credit, is in `set-c-notes.md`:
- **targets unsafe:** python 2/7, yaml 2/7, agent 3/7;
- **collateral:** C2 approves S33 with the guarantee missing, on all three engines;
- **held:** every attack through a non-governing document (12/12);
- the reader is pending cost approval.

**The user's question:** "Ex 5 will tell us if we have a product or a very sophisticated discount
decision apparatus."

## Verdict: PRODUCT, by the rule fixed beforehand, with caveats that matter

| The rule's test | Result |
|---|---|
| No special-casing in the kernel | ✓ None. No kernel code branches on the decision type. |
| Every kernel change is a generalization, and discounts reproduce v3 byte for byte | ✓ 4 generalizations (below). `check_kernel.py`: sets A and B identical to v3 after every change, and after the dataset gained the credit documents. |
| The credit spec reimplements no kernel function | ✓, after one fix. My first draft checked the guarantee's date window inline instead of calling the kernel's `covering()`. I caught it in my own audit and fixed it before the reader runs. |
| Hybrid ≥ 9/10 strict on S26–S35 | ✓ **10/10**, raw and gated, with no uncertain judgments |

## What was built, in order

| Step | Commit | What |
|---|---|---|
| 1. Freeze the kernel | `3c001e0` | v3 split into `lab/owm_kernel/kernel.py` (generic, 425 lines) and `discount.py` (the spec, 210 lines). Byte-identical to v3. |
| 2. Credit truth | `5f85a74` | The new decision in the lab, proven by the build. **Every existing evidence file and all 25 existing answer-key entries are byte-identical.** |
| 3. Credit spec | `47238c6` | `credit.py` (207 lines) on the kernel, plus 4 kernel generalizations. Hybrid 10/10. |
| 4. Reader | `788aeed`, `9118dc7` | The credit procedure, committed before any reader call, then 30 reader calls. |

Step 2 in more detail:
- Finance-owned credit policies for 2025 and 2026;
- the Acme parent guarantee;
- the ERP credit master, invoices and credit requests;
- a hearsay email;
- the `missing-guarantee-evidence` corpus;
- scenarios S26–S35.

## The kernel changes the credit spec forced (`git diff 3c001e0 -- lab/owm_kernel/kernel.py`: +93 / −18)

| # | Change | Why credit needed it | Class |
|---|---|---|---|
| K-1 | Policy bands for **any approved object, in % or $** | The band reader only understood "may approve discounts up to and including N%" | Generalization: discount sentences parse identically |
| K-2 | **Separation of duties**: detected in the policy; a requestor who would be their own approver passes it to their manager; under it, a requestor is never "authorized" | The credit policy forbids approving or concurring on one's own request | Generalization: no discount policy has the clause, so the default is off |
| K-3 | **Concurrence**: a second sign-off from another function, read from the policy ("For T accounts, … greater than A also require ROLE concurrence") and resolved like an approver | Strategic credit limits over $500k need VP Sales concurrence | Generalization: a discount policy could add the sentence |
| K-4 | **Identity across systems by a registered key** (`linked`, by DUNS) | The ERP request names C-1001; the tier lives on CRM-2048 | Generalization: the kernel had no cross-system link at all |
| (refactor) | `map_role` and `resolve_approver` extracted | So concurrence reuses role mapping and approver resolution | No behaviour change |

I predicted about 3. It took 4: the identity link was the one I didn't foresee.

## Results

| Arm | Result | Prediction |
|---|---|---|
| Hybrid (kernel + credit spec) | **10/10** strict, raw and gated | H1: 10/10 ✓ |
| Reader (Opus + credit procedure, gold evidence, 3 runs each) | **27/30** strict; 1 unsafe by the rule (see S32) | R1: ≥ 22/30 and ≤ 2 unsafe ✓ |
| Where the reader missed | **S32 only**, the look-alike customer citing Acme's guarantee | R2: misses on separation of duties or concurrence ✗. The reader got S34 (separation of duties) and S27/S28 (concurrence) right 9/9. |
| New OWM concepts in `owm/ontology.yaml` | **3**: Concurrence; the separation-of-duties invariant; and an `EligibilityInstrument` supertype, so the guarantee and the pricing exception are the same kind of thing. Credit policy, credit request and invoice map onto existing or supertype concepts. | O1: ≤ 2 ✗ (by one) |

### S32: the reader's only miss, for you to grade

All three runs got the substance right: the guarantee names Acme Mfg. Holdings and covers no other
company. They disagree with the answer key's convention:
- **Runs 1 and 2:** `REQUEST_EVIDENCE` (matching the key), but eligibility recorded as "exceeded"
  where the key says "unknown". Graded partial.
- **Run 3:** `REJECT_OR_ESCALATE`. Without the guarantee, $500k is double the $250k Standard
  maximum, so it is ineligible. The procedure says to ask for evidence when the request relies on
  support that can't be established. The answer is defensible on the facts, but it departs from
  the procedure. The rule counts it as unsafe, a denial where the key says to ask.

This is the same boundary as S13 for discounts (`REVIEW_REQUIRED` against `REQUEST_EVIDENCE`): a
routing convention, not a misread fact. Under your standard I would expect run 3 to be a partial,
not unsafe. Your call.

## What it shows

1. **The decision machinery is not discount-shaped.** A second decision with a different owning
   function, different units, data-derived eligibility, a third-party instrument, dual sign-off
   and separation of duties ran on the same kernel. Each new rule was added as a general
   capability that discounts could use too. The decision-specific part is about 200 lines per
   type: its questions, how it reads its own documents, its eligibility logic and its outcome
   table.
2. **The kernel/spec split is the product shape.** The kernel does provenance, time, conflict,
   consistency, authority, approvers, concurrence, separation of duties, identity, judgments and
   gating. A spec says what the decision is.
   - The next step is for specs to become data, governed procedure objects, instead of code.
     The 200 lines are mostly "read this sentence pattern" and "this status maps to that
     outcome".
3. **Agents did well on gold evidence here,** 27/30 with nothing unsafe in substance. The credit
   procedure carried separation of duties and concurrence without trouble. The decision step for
   agents was not the problem this time. Experiment 4 showed where agents fail: plausible forged
   documents.

## Caveats (read these before quoting the verdict)

- **I designed both the credit decision and the kernel.** The kernel was frozen first, so every
  change it needed was counted. But the credit decision keeps the governance skeleton (request →
  identity → eligibility → policy → authority → approvers → record) on purpose.
  - What this shows: governed approval decisions generalize.
  - What it doesn't show: that every kind of decision does. A decision of a different shape, such
    as a contract renewal with deadlines and obligations, is untested.
- **The kernel reads policies by sentence pattern.** K-1 to K-3 depend on wording, and so do the
  credit spec's own readers (payment rule, caps, guarantee amount).
  - A differently worded policy needs the patterns extended.
  - The product answer is the same as experiment 4's: policies and instruments as **structured,
    registered objects**, not text the engine parses.
- **One synthetic company, one author,** gold evidence. No retrieval or Utopia arm for credit.
- **The adversarial test came later,** as set C (`set-c-notes.md`). Forged governing documents
  of the right kind and owner moved all three engines. Experiment 4's instrument guards (G2, G5)
  were spec-local and didn't carry over to credit.

## For BlueLeaf

- **Kernel + specs** is a credible product architecture. It is also the shape of the demo's
  "decide" service. A second app in the demo (a credit limit, alongside the discount) would show
  "platform, not a discount app" to clients directly.
- **Amendment candidates** (new primitives the kernel now has, and the OWM should own):
  - separation of duties;
  - concurrence, or multi-party sign-off;
  - authority in a different function from the requestor;
  - cross-system identity by registered keys;
  - eligibility instruments, with the exception and the guarantee as one concept.
- **The backlog:**
  - specs as data;
  - policies and instruments as registered objects;
  - set C on credit;
  - a non-approval decision type as the next generality test.

## Cost

| | Cost |
|---|---|
| Claude, readers | 30 calls, **$5.43** |
| Jev | 9 new calls, under $0.001 |
| Utopia, OpenAI | none |

## Files

| File | What it holds |
|---|---|
| `plan.md` | The pre-registration and verdict rule |
| `check_kernel.py` | The byte-identity check of kernel + discount spec against v3 |
| `run_hybrid.py`, `hybrid-results.md`, `hybrid-decisions.json` | The credit hybrid |
| `run_reader.py`, `reader-results.{md,json}`, `reader/` | The reader, with transcripts |
| `engine-calls.jsonl` | The Jev recording (replay with `--replay`) |
| `set-c-brief.md`, `set-c/`, `set-c.sha256`, `set-c-plan.md` | Set C: the brief, the sealed attacks, the pre-registration |
| `run_set_c.py`, `set-c-results.*`, `set-c-literal-results.*`, `set-c-notes.md` | Set C: the harness, results and analysis |
| `set-c-engine-calls.jsonl` | Set C's Jev recording |
| `lab/owm_kernel/` | `kernel.py`, `discount.py`, `credit.py` |
| `owm/procedures/credit-limit.md`, `owm/ontology.yaml` | The procedure, and the concepts credit added |
