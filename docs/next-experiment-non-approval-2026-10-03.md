# Next experiment: prove the boundary with a non-approval decision (2026-10-03)

The user proposed this after experiment 5. Credit and discount share one skeleton (request →
eligibility → authority → approval → record), so experiment 5's PRODUCT verdict covers
**approval-shaped decisions**, not the decision substrate as a whole. This is the experiment
that tests the rest.

## Which candidates are actually different

The test of a candidate is whether its core question is something other than "who may approve
this?".

| Candidate | Its core question | Trigger | What it produces | Still approval-shaped? |
|---|---|---|---|---|
| **SLA breach response** | Did we breach, what do we owe, who must act and by when? | an **event** (a ticket and its clock) | **obligations and actions with deadlines**: a service credit, notifications, an escalation | **No** |
| **Contract renewal / obligation** | What must we do about this agreement, and by when? | the **calendar** (notice windows) | obligations with deadlines: notices, price-change limits | Mostly no (signing authority is a side question) |
| **Employee access entitlement** | What access *should* exist, and what must change? | a **state change** (joiner, mover, leaver) | a **desired-state diff**: grant, revoke, recertify | Mostly no (exceptions need approval) |
| Incident escalation | How severe is this, and who must be engaged? | an event | routing by severity and elapsed time | No, but it is a subset of SLA response |
| Procurement exception | May we deviate from procurement policy? | a request | approve or deny | **Yes**: the same skeleton again |
| Vendor onboarding | Is this vendor cleared to use? | a request | clear or block, then approval | **Largely**: an evidence checklist, then approval |

Procurement exception and vendor onboarding would reproduce experiment 5. The other four would
test something new.

## Recommendation: SLA breach response

**Why this one:**

1. **It differs on the most axes at once.**
   - It is event-triggered, not request-triggered.
   - Its answer is a set of obligations and actions with deadlines, not an outcome code.
   - Clocks and elapsed time drive it.
   - Escalation goes by severity and time, not by amount.
   - The obligations run both ways: Northstar owes a remedy, and the customer has to report
     within a window.
2. **It uses the corpus we already have.**
   - Northstar Service is already one of the source systems: SR-40418 is an Acme Industrial
     ticket.
   - The MSA can gain a service-level schedule.
   - The identity traps carry over: a ticket filed under "Acme Industrial" is not covered by Acme
     Manufacturing's SLA.
3. **It tests the record, not just the engine.** The discount and credit records share
   `outcome` + `authority`. An SLA response needs something like `obligations[]` (what, owed by
   whom, by when) and `actions[]`. Whether one decision-record shape covers both is itself a
   BlueLeaf design question.
4. **It is high value for clients.** "BlueLeaf noticed the breach, worked out the credit owed and
   who must call the customer by when" is a strong demo moment. It is also the kind of decision
   that gets missed in real companies.

**Second choice: contract renewal and obligations.** It reuses more of the kernel (agreements,
amendments, consistency), so it is a weaker boundary test. It is a natural follow-on, though,
and much of SLA's machinery (clocks and obligations) would carry over.

**Worth keeping in mind: access entitlement.** It is the most different kind of reasoning (a
desired-state reconciliation) and is commercially big. But it needs a whole new source system (an
IAM export) and moves the lab away from commercial decisions.

## What I expect to break (to pre-register)

Unlike experiment 5, I expect the kernel to need **new primitives**, not just generalizations.
The question is whether they **add** to the kernel, or whether the approval pipeline itself has to
be bypassed.

| The decision needs | The kernel today | Expected |
|---|---|---|
| Provenance of the SLA schedule and the escalation policy | G1 to G5 | **reused** |
| The policy or schedule in force on the date; validity windows | ✓ | **reused** |
| Ticket account ↔ customer ↔ contract | K-4 link plus the party judgment | **reused** |
| Escalation roles → people | `map_role` and `resolve_approver` | **reused** (escalation is routing, like approver resolution) |
| Severity from free text (is "line down" a Sev 1?) | the judgment mechanism | **reused** (a new question; Jev's kind of task) |
| Clocks: elapsed time, business hours, deadlines | none; dates are code but ad hoc | **new primitive** |
| Obligations: who owes what, by when, under which clause | none | **new primitive** |
| A breach → remedy calculation (service credit tiers) | none, beyond eligibility-style rules | spec logic, or a new primitive |
| An event-triggered evaluation (no requestor) | the pipeline assumes a request and a requestor | **the real test**: does the kernel assume "request"? |
| A record with obligations and actions | `outcome` + `authority` | **record generalization** |

## The verdict rule, sketched (to fix before building)

| Verdict | Rule |
|---|---|
| **SUBSTRATE** | The existing kernel modules are reused unchanged for what they do (provenance, time, identity, roles, gating). The new primitives (clocks, obligations, an event trigger) are added as kernel modules that discounts and credit could use, with no decision-type branches. One record shape covers all three decisions, with backward-compatible additions. Discount and credit stay byte-identical. The hybrid scores ≥ 90% on the new scenarios. |
| **APPROVAL ENGINE** | The new decision has to bypass the kernel's pipeline (it can't start without a request or requestor, or the record can't hold its answer), or its spec reimplements the time, identity or routing logic. |
| **IN BETWEEN** | Anything else. The list of missing primitives is the substrate backlog. |

## Fixing experiment 5's biggest caveat: I designed both sides

This time the **business rules should be authored by someone who hasn't seen the kernel.** The
rules are the SLA schedule, the escalation policy, the credit-tier remedy, the reporting windows,
and the scenarios with their expected outcomes. Two ways to do that:

- **You** write a one-page rule sheet (what the SLA says, and what should happen in 8–10
  situations). Claude turns it into truth and evidence, and the build proves it.
- **A subagent,** told not to read `lab/owm_kernel/`, writes the rule sheet from a brief. This is
  ordinary business content, not attack material, so it shouldn't trip a safety check the way set
  C did.

Either way, the kernel is frozen at its current commit before the rules are seen.

## Size and cost

It is about experiment 5's size: a day or so of build.
- Claude: about $5–6 for 30 reader calls.
- Jev: cents.
- If the subagent writes the rules: about $1.
