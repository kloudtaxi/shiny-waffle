# Experiment 6: a non-approval decision, SLA breach response (pre-registration, 2026-10-03)

The user proposed this after experiment 5, and chose the decision and the rule authorship on
2026-10-03. Discount and credit share one skeleton (request → eligibility → authority → approval →
record), so experiment 5's PRODUCT verdict covers approval-shaped decisions only. This experiment
tests whether the decision substrate holds for a decision whose core question isn't "who may
approve this?". The background is in `docs/next-experiment-non-approval-2026-10-03.md`.

**The decision:** a support ticket has happened.
- Did Northstar breach its service levels?
- What does Northstar owe, and by when?
- Who at Northstar must act or be told, and by when?
- What must the customer do?

It is event-triggered, with no requestor. Its answer is obligations and actions with deadlines,
driven by clocks.

## What is frozen before anything is built

- **The kernel** is `lab/owm_kernel/kernel.py` at commit `47238c6`, sha256
  `f87b5ef5cba31275bf2036e084531b068d312309318702a01b70d0ce44e2acf9`. Every later change to it is
  listed and classified.
- **Discount** (`discount.py`, `d85d02b9…`) and **credit** (`credit.py`, `7dc1ab40…`) must stay
  byte-identical in behaviour:
  - `../2026-10-03-exp5-credit/check_kernel.py` must still match v3;
  - the credit hybrid must still replay to 10/10 with identical decisions.

## Who writes the rules: a blind subagent (fixes experiment 5's main caveat)

The business rules and the situations are written by a subagent that reads only
`dataset/evidence/`. It never sees `lab/`, `runs/`, `src/` or this plan's predictions. The rules
cover the SLA schedule, severities, clocks, remedies, escalation and customer obligations. The
situations come with their expected outcomes, in business terms.

Its brief is below, verbatim. Its output (`rules/`) is committed as soon as it arrives, before
any truth, evidence or code is written from it.

**How I turn the rule sheet into truth, evidence and an oracle:**
- Where the rule sheet is ambiguous, I take its literal text and log the choice in the notes.
- If the build's oracle disagrees with one of the subagent's expected outcomes, the cause is
  logged: my implementation bug (fixed), or a contradiction in the rule sheet (reported, with the
  rule-sheet reading kept).
- **No expected outcome is changed silently.**

## Steps

1. This plan and the brief, committed.
2. The subagent's rule sheet, committed.
3. Truth, evidence and an oracle in the lab, proven by the build. Existing artifacts and answer
   keys stay byte-identical.
4. An SLA spec on the kernel. Each kernel change is classified. The hybrid runs on the situations
   (gold evidence).
5. An SLA procedure, written before any reader run, then the Opus reader with 3 runs per
   situation.
6. The verdict.

## The verdict (fixed now)

| Verdict | Rule |
|---|---|
| **SUBSTRATE** | (a) No kernel code branches on the decision type. (b) Discount and credit are byte-identical in behaviour (see above). (c) Every new capability the SLA spec needs is added as a kernel module that any spec could use: clocks and deadlines, obligations, routing without a requestor. (d) The SLA spec reimplements none of provenance, validity windows, conflict, identity, role mapping or routing. (e) The answer-key records of all three decision types validate against **one decision envelope** (below). (f) The hybrid scores **≥ 90%** strict on the situations. |
| **APPROVAL ENGINE** | The SLA decision can't use the kernel's pipeline without faking what it assumes, such as a requestor or a requested amount. Or its spec has to reimplement time, identity or routing logic. Or no single envelope can hold its answer next to the other two. |
| **IN BETWEEN** | Anything else. The list of missing primitives is the substrate backlog. |

**The decision envelope** that test (e) checks every record against. The fields are
`decision_id`, `type`, `as_of` and `subject`, then exactly one `decision.outcome` from a declared
vocabulary for that type, then `reason[]` and `evidence[]`, and optionally `request`, `authority`
and `obligations[]`. Type-specific bodies are allowed, but they sit alongside the envelope and
never replace it. Discount and credit already satisfy this, apart from `obligations`.

## Predictions

| # | Prediction |
|---|---|
| P1 | The SLA spec forces **at least 3 new kernel primitives** (clocks and deadlines, obligations, routing without a requestor), and **no special-casing**. |
| P2 | **Verdict: SUBSTRATE** (I give it about 60%), otherwise IN BETWEEN. APPROVAL ENGINE is unlikely, because the request-centric parts of the kernel are confined to `authority_from_evidence` and can be generalized. |
| P3 | Hybrid: **≥ 90%** strict on the situations. |
| P4 | Reader: **≥ 70%** strict. Misses cluster on clock arithmetic (business hours, paused clocks) and exclusions. **≤ 3 unsafe**, where unsafe means a remedy owed and denied, a remedy not owed and granted, or a required escalation or notice missed. |
| P5 | One envelope covers all three types, once it has `obligations[]`. |

## Cost

| Item | Estimate |
|---|---|
| The subagent | about $1 |
| Readers | 3 runs × 8–10 situations, about $5–6 |
| Jev | cents |
| Utopia and OpenAI | none |

## The subagent's brief (verbatim)

> You are writing business rules for a fictional company, as a domain expert in customer support
> and service-level agreements. Your output will become the ground truth for a lab experiment, so
> it must be precise and internally consistent.
>
> **Context.** The repo at /Users/mehulmehta/DEV/Sovera/2026-dev/owm-ve/shiny-waffle models a
> fictional company, Northstar Industrial Systems (industrial controllers and software, Chicago).
> Its document store and system exports are in `dataset/evidence/` (Markdown documents with YAML
> front matter in `documents/`, CSV exports in `structured/`). READ ONLY `dataset/evidence/`, to
> learn the company: its customers (Acme Manufacturing, a strategic account, legally "Acme Mfg.
> Holdings", CRM-2048 / ERP C-1001; Acme Industrial Supply Co., a *different* company with a
> similar name, CRM-2091 / C-1044; BlueRiver Logistics; Cedar Health Systems), its products
> (NS-500 controller, NS-Cloud, NS-Edge), its people and its document style. DO NOT read anything
> else in the repo: not `lab/`, `runs/`, `src/`, `truth/`, `docs/`, `owm/`, `tests/`, any `*.py`,
> `README.md` or `CLAUDE.md`. Do not run any code.
>
> **Your task.** Write the rules for one business decision that Northstar makes: **responding to
> a support ticket under a customer's service-level agreement.** When a ticket is opened, Northstar
> must work out:
> (1) the ticket's true severity;
> (2) whether a service level was breached;
> (3) what Northstar owes the customer as a remedy (for example a service credit) and by when;
> (4) who at Northstar must be engaged or notified, and by when;
> (5) what the customer must do (for example claim a credit within a window);
> (6) when the decision can't be made from the evidence and what is missing.
>
> **The rules must cover at least:**
> - **Severity levels** defined by business impact (not by what the customer typed). Severity can
>   be corrected by Northstar.
> - **Response and restoration targets** per severity. At least one severity uses **business
>   hours** (state the hours and time zone), and at least one runs 24×7.
> - **Clock rules:** when the clock starts, and what pauses it (for example waiting on the
>   customer).
> - **Exclusions:** for example scheduled maintenance windows announced in advance, or an outage
>   caused by the customer.
> - **Remedies:** a service-credit schedule (for example a % of the monthly support fee per breach
>   level), and a cap per month.
> - **Customer obligations:** for example a credit must be claimed within N days, or a severity-1
>   incident must be reported by phone.
> - **Escalation:** who must be engaged or notified at each severity and elapsed time. Use roles,
>   and give each role exactly one named holder, a new Northstar person you invent. Don't use
>   these job titles as escalation targets, because many people hold them: Sales Engineer, Sales
>   Operations Analyst, Customer Success Manager, Financial Analyst, Accounts Receivable
>   Specialist. You may use the account's owner (Acme's is Sarah Chen) or existing executives.
> - **Versions over time:** the SLA schedule changes at least once (an older version applies to
>   tickets opened before a date).
> - **Scope:** the SLA applies only to the customer and products it names. Acme's SLA does not
>   cover Acme Industrial Supply.
>
> Keep the dates between 2025-01-01 and 2026-09-30.
>
> **Write these files** into
> `/Users/mehulmehta/DEV/Sovera/2026-dev/owm-ve/shiny-waffle/runs/2026-10-03-exp6-sla/rules/`
> (create it), and nothing else, anywhere:
> 1. `rule-sheet.md`: the complete rules, numbered so they can be cited (R1, R2, …). They must be
>    unambiguous, with every number, hour, time zone, percentage and window stated. Include the
>    SLA schedule versions with effective dates, the escalation roles and their holders, and the
>    monthly support fee for each covered customer.
> 2. `situations.md`: 8–10 situations, S36 onward. Each one has the ticket facts (customer as
>    named on the ticket, product, opened timestamp with time zone, reported severity, description,
>    first-response and restoration timestamps, any pause, any maintenance notice, any claim date)
>    and the expected outcome:
>    - the true severity;
>    - breached (yes/no, and which target);
>    - the remedy owed (amount and by when, or none, and why);
>    - who must be notified or engaged and by when;
>    - the customer's obligation and whether it was met;
>    - or "cannot decide: missing X".
>
>    Each expectation cites the rules it follows from. Cover a variety: a clear breach with a
>    credit; a target met; a breach excused by an exclusion; a severity the customer under-reported;
>    a business-hours clock that crosses a weekend or night; a paused clock; an older schedule
>    version; a ticket for a company the SLA doesn't cover; a credit claimed too late; one where a
>    needed document or fact is missing. Make at least two situations hinge on careful time
>    arithmetic.
>
> Write as a careful contracts-and-support expert. Every expected outcome must follow from the
> rules alone. Your final message: list the files with their sha256 (`shasum -a 256`), the number
> of rules and situations, and one line confirming you read nothing outside `dataset/evidence/`.

## Addendum before the reader runs (2026-10-03)

- **Reps reduced from 3 to 2 per situation (20 calls).** The gold-evidence bundle grew to about 18k
  tokens with the SLA documents and exports. Three reps would cost about $10–12, against the
  plan's $5–6. Two reps is about $7.
- **P4, scaled to 20 answers:** reader ≥ 70% strict, and **≤ 2 unsafe**.
- **Reader scoring,** fixed now:
  - **strict pass:** outcome, scope, true severity, both breach findings, the credit, and every
    obligation all match the answer key;
    - Northstar's duties are compared as (duty, holder, due). A holder named by the reader is
      mapped to the employee, or to the account owner of that CRM account. A due date where the
      reader gives a datetime is compared by its CT date. Datetimes are compared as instants.
    - The customer's duties are compared as (duty, met or not met).
  - **core:** outcome, scope, severity, breach and credit match, but not every obligation does;
  - **fail:** otherwise.
- **Unsafe:** any of
  - a credit owed and the reader gives none;
  - no credit owed and the reader gives one;
  - an engagement or notification the key requires that is missing from the reader's obligations
    altogether. A wrong time is not "missing".
