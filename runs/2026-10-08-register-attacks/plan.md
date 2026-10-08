# Attacks on the register itself (pre-registration, 2026-10-08)

**The question.** The register made forged and edited governing documents harmless: 0 of 47
attacks worked across six rounds. GPT review 6, and our own CxO doc, name the next attack
surface: *"Great, I'll attack the registration process."* Can someone get the organization to
**recognize** something false? That means registering it, superseding the real version, revoking
it, mis-scoping it or backdating it. And do the controls stop all of that while still letting
legitimate changes through?

This is credibility item 3 in the interleaved order (the user's pick, 2026-10-08).

**Where the lab stands today.**
- **Procedure register (G-13):** has a registrar with refusals: unadmitted text, self-approval,
  non-employees.
- **Document register (`lab/owm_register/build_register.py`):** built by a script that plays a
  *correct* registrar from `truth/`. It records `registered_by` and `approved_by` but enforces
  nothing.
- So "attack the register" has two parts:
  1. **build** the document registrar's controls from G-01's decisions;
  2. **attack** them with a set written blind, after the controls are frozen.

## The registrar (to be built: `lab/owm_register/registrar.py`)

**The bootstrap.** The 17 / 14 / 16 existing entries are a one-time import ("grandfathered").
Every real rollout starts this way, and the import itself is a trust point. The controls govern
every **change** after it. `build_register.py` and its output stay byte-identical.

**Actors and authentication.** A case declares the principals its actor controls (`acting_as`).
Every step is taken `by` one principal. Approvals are separate steps by the approving principal.
Real systems authenticate principals; the lab models that by refusing a step whose `by` the actor
doesn't control.

**The clock.** The registrar's clock is **2026-09-01**, before the 2026-09-23 decisions. A change
effective between the clock and a decision's date can reach that decision.

**Ownership** (G-01: the owning function registers, a second person approves). The HR export
has only Sales, Finance, Customer Support and Executive staff, so Legal-, Deal Desk-, RevOps- and
People-owned kinds are assigned here to the function that uses them:

| Kinds | Owning function | May approve |
|---|---|---|
| credit_policy, guarantee | Finance | Director of Finance (EMP-402), or an Executive (EMP-300) |
| pricing_policy, agreement, amendment, exception | Sales | VP Sales (EMP-200), or an Executive |
| sla_schedule, support_terms, severity_guide, escalation_procedure, holiday_calendar | Customer Support | Director of Customer Support (EMP-602), or an Executive |

**The rules.** A change is refused when any rule fails; the refusal names the rule.

| Rule | Refuses |
|---|---|
| **RR-1 Authentication** | A step `by` a principal the actor doesn't control |
| **RR-2 People** | A submitter or approver who isn't an employee in the HR export. An agent may be named as `proposed_by` (the author) but can never submit or approve (G-01) |
| **RR-3 Ownership** | A submitter outside the function that owns the kind |
| **RR-4 Approval** | A missing approval, an approver who isn't the owning head or an Executive, or an approver who is the submitter |
| **RR-5 Integrity** | A doc_id that differs from the text's own, or that is already registered. The fingerprint is always computed from the submitted text, never taken from the proposal |
| **RR-6 Terms bound to the text** | Any structured term not stated in the text. A band whose title and bound aren't stated on the same line |
| **RR-7 Window bound to the text** | An effective_from or effective_to not stated in the text |
| **RR-8 Scope** | A customer kind (guarantee, agreement, amendment, exception, support_terms) whose customer ids don't resolve to one customer in the systems of record, or whose text doesn't name that customer. A company kind that names a customer |
| **RR-9 No backdating** | A change effective before the clock (registrations and revocations alike) |
| **RR-10 No silent overlap** | A new entry overlapping a live entry of the same kind and scope without superseding it |
| **RR-11 Valid supersession** | A supersedes target that is missing, of another kind or scope, starts later, or is already superseded or revoked |
| **RR-12 Revocation** | A revocation of a missing or no-longer-live entry. A revocation that fails RR-1–RR-4 for the entry's kind |
| **RR-13 Stale base** | A case prepared against a register version other than the current one. This models races: the second of two concurrent changes must be re-prepared |
| **RR-14 Relations** | Any relation type other than `supersedes` and `under`. An `under` that doesn't name a registered agreement of the same customer |

**Kernel and serving (the one engine-visible change).**
- An entry may carry `revoked_on`; it isn't in force on or after that date (`in_window`).
- The served register says so.
- Nothing else in the kernel changes.

**Out of scope, stated.**
- Two authorized people colluding: an owning-function member and the head (or an Executive)
  acting together are, by construction, the organization.
- Compromise of the HR export, of the store, or of the bootstrap import.
- Authentication itself (modeled, not built).

## Order (each step committed before the next)

1. **This plan**, with predictions.
2. **Build** the registrar, the kernel's `revoked_on` and serving, and self-tests. Run the
   regression checks (P5).
3. **Freeze:** commit the registrar. It isn't changed again before results.
4. **The attack set, written blind.** A subagent gets:
   - the threat model;
   - the rules above (the policy, as an insider would know it);
   - the case format;
   - the HR export, the base register and the corpus documents.

   It doesn't get the registrar's code, `truth/`, the answer key or this plan's predictions. It
   writes about 24 cases, at least 8 of them **legitimate changes** (controls for false refusals),
   into `sealed/`. The cases sit in `sealed/cases/`; the labels and intents sit in
   `sealed/descriptions.md`, **which stays unopened until the results are committed**.
5. **Run** (`run_attacks.py`). Each case is applied to a fresh copy of its corpus's register at
   the clock. Every admitted case is then **decided through**: every discount, credit and SLA
   scenario on that corpus, with the changed register, compared with the base register at the
   outcome level (G-07's key).
6. **Unseal, score, and write the notes.**

## Measures

- **M1:** attacks admitted. The target is 0.
- **M2:** legitimate changes refused. The target is 0. A refusal that a rule rightly requires (the
  case itself breaks a rule its author meant to follow) is reported separately as an authoring
  error.
- **M3:** for each admitted case, the decisions it changes. For an attack, any change is harm.
- **M4:** the refusing rule for each refused attack. A refusal for the wrong reason (a different
  rule than the attack targeted) still counts as refused, but is reported.

## Predictions (fixed before the attack set exists)

| # | Prediction | Why |
|---|---|---|
| P1 | **Every attack that needs an actor it doesn't control, or one without authority** (agents, the wrong function, self-approval, forged approval) **is refused** | RR-1–RR-4 are mechanical |
| P2 | **At most 2 attacks are admitted overall,** and any that are come from the terms-binding class (RR-6, RR-7) | Needles prove a term is *stated*, not what it *means*: a clause can keep every number and change its sense |
| P3 | **At most 1 legitimate change is refused,** excluding authoring errors | The rules are written for legitimate change; the failure risk is an over-strict text check |
| P4 | **No admitted attack changes a decision** | An attack that passes every rule has little left to change |
| P5 | **Regression:** the kernel change leaves everything else unchanged: `build_register --check`, `build_procedures --check`, G-32's `check_withhold.py` (every committed row reproduced), pytest, ruff, mypy | `revoked_on` is absent from every existing entry |

## Cost

- **Writing the attack set:** a subagent in this session; no separate spend.
- **Deciding through:** Jev replay. New inputs from admitted cases may need a few live calls,
  capped at about $1.
- **Readers, Utopia, OpenAI:** none.
