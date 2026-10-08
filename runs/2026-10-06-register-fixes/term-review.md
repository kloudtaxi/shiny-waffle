# G-33: term review, every registered kind (2026-10-06)

**The question:** for each rule in an approved governing document, is it held in the register's
structured terms, only in engine code, or only in the document's prose?

**The two fixes:**
1. Terms were extended where the rule is simple and decision-relevant. Each new term is checked
   against the document's text by the registrar.
2. The served register now carries **every document's approved text** as well as its terms. No
   rule can be lost to an incomplete schema, whatever the kind.

| Kind | Rule in the approved document | Before | Now |
|---|---|---|---|
| Credit policy | Approval bands, concurrence, payment rule, caps | terms | terms |
| | Separation of duties, *and the approval passing to the requestor's manager* | `true` only; the hand-off was in engine code | **terms** (set F fix) |
| | Authority applies to the new total limit | prose | **terms** |
| | Account tiers as recorded in Northstar CRM | engine code | **terms** |
| | A guarantee raises the maximum by its amount, for the customer it names | engine code | **terms** |
| | Decisions recorded in Northstar ERP | prose | **terms** |
| Guarantee | Guarantor, customer (registered ids), amount, window, "no other company" | terms | terms |
| Pricing policy | Approval bands; evidence threshold | terms | terms |
| | List price as the basis; exceptions must be reviewed | prose | **terms** (`rules`) |
| | The Approval Authority Matrix as the operational reference (2026) | prose | **terms** |
| Agreement | Customer, products, window; grants no approval authority | terms | terms (the no-authority clause checked against the text) |
| | Its pricing clause (15% on NS-500, set out in Schedule B) | the exception's terms only | **terms** (`pricing`) |
| | Termination and other commercial clauses | prose | approved text (not decision-relevant) |
| Exception | Customer, product, maximum, window; supersedes; under | terms and relations | terms and relations |
| | Product-only; grants no approval authority | prose | **terms**. EXC-15 states it; the 2023 exception is silent, so the value comes from truth |
| SLA schedule | Targets, credits, cap, claim period, notice | terms | terms |
| | Version chosen by open time in CT; business hours; clock rules; pauses; met at the boundary; open time; exclusions (notice, root cause); claim decisions | prose (and the SLA spec's readers) | **approved text served** (too rich for a schema) |
| Support terms | Customer, plan, products, coverage start | terms | terms |
| | Fees; "not covered" clauses | prose | approved text |
| Holiday calendar | The holidays | terms | terms |
| Severity guide, escalation procedure | Every rule | prose only | approved text served (as since set F) |

**Engine-only conventions,** not in any document, left as they are and noted:
- the approver is the first holder of the required title up the requestor's manager chain, else
  any holder;
- if two policies are in force, it is a conflict.

These are the engine's resolution rules, not the company's.

**Checks:**
- the registrar's text checks pass for every new term;
- the registers rebuild identically (`--check`);
- engines read none of the new terms, so they are unchanged (verified by re-running every set).
