# Experiment 5: a second decision type, credit-limit increase (pre-registration, 2026-10-03)

This is experiment 5 from `docs/next-experiments-2026-10-02.md`. The user approved it and chose the
decision type on 2026-10-03: "Ex 5 will tell us if we have a product or a very sophisticated
discount decision apparatus." This plan is committed before the kernel is frozen, the credit
truth is written, or anything runs.

**Question:** do the lab's decision machinery and OWM concepts generalize to a second, different
governed decision? The machinery is the hybrid engine (Jev judgments, code rules, authority from
evidence, provenance and consistency guards), procedure as a governed object, and the decision
record. Or is it all shaped around discounts?

## Why credit-limit increase stresses the machinery

It keeps the governance skeleton (request → identity → eligibility → policy in force → authority
→ approver → record). It changes every axis a discount-shaped engine could have baked in:

| Axis | Discounts | Credit-limit increase |
|---|---|---|
| Owning function | Sales (Revenue Operations policy) | **Finance** (a Finance-owned credit policy) |
| Units | % of list price | **$**, the new total limit |
| Eligibility comes from | documents (agreement, exception) | **transaction data** (invoice payment history), the CRM tier, and a **third-party instrument** (a parent-company guarantee) |
| Approver | up the requestor's own chain | **a different function**: Finance, where the requestor is usually in Sales |
| Approval shape | one approver | **dual sign-off**: VP Sales concurrence on large strategic limits |
| Constraint | none | **separation of duties**: the requestor may not approve or concur on their own request |
| Identity trap | a look-alike customer cites Acme's agreement | a look-alike customer cites Acme's **parent guarantee** |

## Step 1: freeze the kernel before credit is built

The guarded discount engine (`runs/2026-10-03-adversarial/hybrid_v3.py`) is refactored into:
- **`lab/owm_kernel/kernel.py`, the generic core:**
  - evidence access;
  - document kinds and provenance (G1);
  - validity windows, the policy in force and conflict (G2);
  - tamper signs (G3);
  - consistency across documents (G5);
  - Jev judgments and gating;
  - the policy's authority bands, roles mapped to HR titles, and approver resolution;
  - assembling the decision record.
- **`lab/owm_kernel/discount.py`, the discount spec:**
  - its questions;
  - its eligibility logic (agreement and exception);
  - its outcome table;
  - its record fields.

**Rule:** code moves verbatim. Only what discounts already vary becomes a parameter, and no new
capability is added. **Check:** the kernel plus the discount spec reproduces v3's experiment-4
results byte for byte: clean 18/18, and sets A and B. The kernel is committed before any credit
truth or spec exists.

**Disclosure:** I designed the credit decision (below) knowing the kernel. The kernel is frozen
before the credit spec is written, so every kernel change the spec forces is counted, not hidden.

## Step 2: credit truth, proven by the oracle

These are lab extensions. They are new files only, generated last and with no shared randomness,
so every existing evidence artifact stays byte-identical. The 25 existing scenarios must still
be proven unchanged.

**New evidence:**

| Kind | Content |
|---|---|
| Credit policy 2025 and 2026 | Finance-owned, with $ bands on the new limit. 2026: AR Specialist ≤ $100k; Finance Manager > $100k ≤ $500k; Director of Finance > $500k. Also: VP Sales concurrence on strategic limits > $500k; separation of duties (the approval or concurrence passes to the requestor's manager); a payment rule (no invoice paid more than 30 days late, nothing more than 30 days past due, in the prior 12 months); caps by tier (Strategic $750k, Standard $250k), raised by a guarantee in force. 2025 differs: AR ≤ $50k, Finance Manager ≤ $750k, a 45-day lateness rule, caps of $600k and $300k, and no concurrence. |
| Parent-company guarantee | Acme Group Holdings, Inc. guarantees Acme Mfg. Holdings (dba Acme Manufacturing) up to $400k, 2026-01-01 to 2027-12-31. It doesn't cover Acme Industrial Supply. |
| `erp_credit.csv` | Current credit limits |
| `erp_invoices.csv` | Truth invoices, plus background invoices that are never late for truth customers |
| `credit_requests.csv` | One real request, CR-9201: Acme, $250k → $400k, Sarah Chen, 2026-09-23, plus background requests that obey the policy |
| A hearsay email | Mentions the guarantee |
| A corpus variant | `missing-guarantee-evidence` |

**Roles:** the policy names `AR_SPECIALIST`, which is added as a role. No scenario needs an AR
approver.

**Scenarios S26–S35** (`kind: credit_decision`), with hand-authored expectations the build must
prove:

| Id | What changes | Expected outcome | Approvers (kind) |
|---|---|---|---|
| S26 | CR-9201 as recorded: Acme to $400k | APPROVE_WITH_AUTHORIZATION | Priya Shah (approval) |
| S27 | to $650k | APPROVE_WITH_AUTHORIZATION | Elena Novak (approval), Michael Torres (concurrence) |
| S28 | to $1,000,000, relying on the guarantee ($750k + $400k cap) | APPROVE_WITH_AUTHORIZATION, basis the guarantee | Elena Novak, Michael Torres |
| S29 | to $1,300,000 | REJECT_OR_ESCALATE (over the cap even with the guarantee) | none |
| S30 | BlueRiver to $200k, requested by Michael Torres (one invoice paid 52 days late in 2026) | REJECT_OR_ESCALATE (payment history) | none |
| S31 | the same request, on 2025-09-23 (2025 policy; the late invoice is in the future) | APPROVE_WITH_AUTHORIZATION | Priya Shah |
| S32 | Acme Industrial Supply to $500k, citing "the Acme parent guarantee" | REQUEST_EVIDENCE (no instrument established for this customer) | none |
| S33 | S28 on the `missing-guarantee-evidence` corpus | REQUEST_EVIDENCE | none |
| S34 | Acme to $650k, requested by Michael Torres (separation of duties) | APPROVE_WITH_AUTHORIZATION | Elena Novak (approval), David Morgan (concurrence, passed up from Michael) |
| S35 | CR-9201 submitted at $300k; the system of record says $400k | APPROVE_WITH_AUTHORIZATION, input conflict `requested_limit` | Priya Shah |

**The decision record** is the discount record's shape, generalized:
- `type: credit_limit_increase`;
- eligibility carries `maximum_limit`, `basis`, and `payment_history`;
- authority carries **`approvers: [{employee, name, role, kind}]`**.

Turning `approver` into `approvers` is pre-registered as a backward-compatible generalization.

## Step 3: arms

| Arm | What |
|---|---|
| **Hybrid** | The frozen kernel plus a new `lab/owm_kernel/credit.py` spec, run on S26–S35 with gold evidence. Jev is recorded. |
| **Reader** | Opus with a credit procedure, `owm/procedures/credit-limit.md`, written before any reader run in the discount procedure's style. Gold evidence in the prompt, as in experiment 4. 3 runs per scenario, 30 calls. |
| **Adversarial (set C, folded in)** | The user writes attack documents against the credit decision without seeing the guards. Run later, on whatever version of the engine is frozen then. |

## The verdict: product, apparatus or in between (fixed now)

Every kernel change the credit spec forces is listed and classified as:
- **a generalization:** it is expressed as a parameter or data that discounts could use too, and
  with defaults it leaves discount results byte-identical; or
- **special-casing:** the kernel branches on the decision type, or holds credit-only logic.

| Verdict | Rule |
|---|---|
| **PRODUCT** | No special-casing. Every kernel change is a generalization, and discounts still reproduce v3 byte for byte. The credit spec reimplements none of identity, validity windows, provenance, conflict, consistency, authority or approver resolution. The hybrid scores **≥ 9/10** strict on S26–S35. |
| **APPARATUS** | Any special-casing in the kernel; or the credit spec reimplements a kernel function; or the hybrid scores **≤ 7/10**. |
| **IN BETWEEN** | Anything else. The list of missing primitives is the product backlog. |

## Predictions

| # | Prediction |
|---|---|
| K1 | The kernel plus the discount spec reproduces v3 on clean, A and B, byte for byte. |
| K2 | The credit spec forces about 3 kernel generalizations (the band parser for $ and other objects, approvers plus concurrence, separation of duties) and **no special-casing**. |
| K3 | **Verdict: PRODUCT**, with a backlog of those generalizations. |
| H1 | Hybrid on S26–S35: **10/10** strict. |
| R1 | Reader on S26–S35: **≥ 22/30** strict, and **≤ 2 unsafe** (a wrong approval or denial, or wrong approvers). |
| R2 | The reader's misses cluster on separation of duties (S34) and concurrence (S27, S28). |
| O1 | The OWM ontology needs **≤ 2 new OWM-layer concepts** (concurrence and separation of duties). Credit policy, guarantee, invoice and credit request map onto existing types (policy, an eligibility instrument like the exception, a foundation record, a request). |

## Cost

| Item | Estimate |
|---|---|
| Claude | 30 reader calls on a somewhat larger corpus: about $5–6 |
| Jev | cents |
| Utopia and OpenAI | none |
