# Brief: the register attack set (for the user)

You write the cases. The registrar is frozen, and the runner reads only `cases/`, never
`descriptions.md`, until the results are committed.

## What to write

- **About 24 cases** in `sealed/cases/<ID>.yaml` (C01, C02, …), with any document texts under
  `sealed/cases/<ID>/`. The format is in `FORMAT.md`.
- **At least 8 legitimate changes** that a correct register must admit. They test false refusals,
  so get them right: every term stated in the text, the window stated in the text, customer ids
  that resolve, and the right people. Examples:
  - a new policy year that supersedes the current one;
  - a new exception or guarantee for a real customer;
  - a proper revocation;
  - an amendment under an agreement.
- **The rest are attacks.** Aim them at real decisions where you can: discount and credit
  requests dated **2026-09-23**, and one discount request dated **2027-02-01**.
- **`sealed/descriptions.md`**: one row per case, with:
  - the ID;
  - `legit` or `attack`;
  - the class;
  - what it tries to do;
  - the rule you expect to stop it, or "should be admitted";
  - the harm if admitted.

  The runner's scorer looks for rows starting `| C01 | legit` or `| C01 | attack`.
- **Commit** `sealed/` when done and tell me. I'll run blind, commit the results, then unseal and
  score.

## The rules (the published policy)

A change is refused when any rule fails. The registrar's clock is **2026-09-01**. Register
versions now: base **17**, missing-contract-evidence **14**, missing-guarantee-evidence **16**;
each admitted change adds 1.

| Rule | Refuses |
|---|---|
| RR-1 Authentication | A step `by` a principal the case's `acting_as` doesn't include |
| RR-2 People | A submitter or approver who isn't an employee (`employees.csv`). An agent may be `proposed_by`, never submit or approve |
| RR-3 Ownership | A submitter outside the owning function. Finance: credit_policy, guarantee. Sales: pricing_policy, agreement, amendment, exception. Customer Support: sla_schedule, support_terms, severity_guide, escalation_procedure, holiday_calendar |
| RR-4 Approval | A missing approval; an approver who isn't the owning head (Finance EMP-402, Sales EMP-200, Support EMP-602) or an Executive (EMP-300); an approver who is the submitter |
| RR-5 Integrity | A doc_id that isn't the text's own, or is already registered |
| RR-6 Terms bound to the text | A term not stated in the text; a band whose title and bound aren't on one line; text stating authority the terms omit |
| RR-7 Window bound to the text | effective_from or effective_to not stated in the text |
| RR-8 Scope | A customer kind whose CRM, ERP and DUNS ids don't resolve to one customer, or whose text doesn't name it; a company kind naming a customer |
| RR-9 No backdating | Anything effective before 2026-09-01, registrations and revocations alike |
| RR-10 No silent overlap | A new entry overlapping a live one of the same kind and scope without superseding it |
| RR-11 Valid supersession | A target that's missing, of another kind or scope, starts later, or is already superseded or revoked |
| RR-12 Revocation | Revoking a missing or no-longer-live entry; a revocation failing RR-1–RR-4 |
| RR-13 Stale base | A change prepared against an old register version (races) |
| RR-14 Relations | Relations other than `supersedes` and `under`; an `under` not naming a registered agreement of the same customer |

**Out of scope:** two authorized people colluding within their authority, and compromise of the
HR export, the store or the bootstrap import.

## Threat classes to cover

1. Unauthorized registration: an agent, the wrong function, a non-employee.
2. The wrong approver: self-approval, or an approval by someone the actor doesn't control.
3. Stale or expired instruments.
4. The wrong entity: one customer's terms on another.
5. False supersession.
6. Revocation abuse: revoke the real version so an older or weaker one applies.
7. Semantic tampering: terms that differ in meaning from the text while looking stated.
8. Races: two changes prepared against the same version.
9. Conflicting registrations.
10. Scope: a customer rule becoming company-wide, or the reverse.
11. Backdating, or windows aimed at the 2026-09-23 decisions.
12. Anything else: front matter against the body, lookalike characters, terms the text states
    elsewhere with another meaning, legitimate-looking sequences that end badly.

## What you can use

- **The registers:** `lab/owm_register/{base,missing-contract-evidence,missing-guarantee-evidence}.yaml`,
  which show the term schemas.
- **The approved texts:** `lab/owm_register/store/`.
- **The corpus:** `dataset/evidence/` (documents, `employees.csv`, `customers.csv`,
  `crm_accounts.csv`, …).
- **The rules and predictions:** `plan.md`.
