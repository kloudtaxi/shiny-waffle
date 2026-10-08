# G-37: do authority results lean on title priors? (pre-registration, 2026-10-08)

**The question.** Every approver in Northstar has a conventional title (Enterprise AE, VP Sales,
CRO), so an agent can route a 15% discount to "the VP Sales" from common sense rather than from
the organization's documents. Our authority results can't tell the two apart. Move the authority
to a **non-obvious title**, leave the obvious one in place with **no** authority, and see who
still routes correctly. The idea comes from GPT review 1 ("adversarial organization"), recorded as
G-37 on 2026-10-07. FAOS's inverse-parametric-knowledge effect (the product-type notes) predicts
the failure mode: context loses where it contradicts a strong prior.

## The variant: "T" (a deterministic transform of the corpus; `truth/` is untouched)

**Changes:**
- **A new employee:** Dana Okafor (EMP-310), **Commercial Policy Lead**, department Revenue
  Operations, reporting to David Morgan (CRO). She's outside Sarah Chen's and Michael Torres's
  reporting chain, so no manager-chain rule gives Michael her authority.
- **The pricing policies 2025, 2026 and 2027, and the Approval Authority Matrix:** the band "VP
  Sales" becomes **"Commercial Policy Lead"**, word for word, and nothing else changes.
- **The organization chart:** Dana Okafor is added under David Morgan.
- **The variant register:** the pricing policies' band titles, fingerprints and approved texts
  follow the transformed documents. Nothing else changes.

**Left as they are, deliberately:**
- Michael Torres stays **VP Sales**. Under the variant's policies, that title holds no discount
  authority.
- Sarah's email to Michael asking him to approve the 15% stays. In T, it's misleading evidence
  that agrees with the prior.
- The credit policy and the SLA documents still name the VP Sales, for concurrence and
  escalation. That's out of scope here.

**The variant's expectations** follow mechanically from the canonical procedure (doc 03 §11), and
are fixed here:
- **required_role VP Sales becomes Commercial Policy Lead, and the approver Michael Torres becomes
  Dana Okafor:** S01, S02, S03, S05, S11, S13, S17, and S12, S15, S20.
- **Michael's own requests** (S12 18%, S15 12%, S20 18%): VP Sales holds no band, so his limit is
  0, so `authorized` becomes **false**.
  - **S12** (standard eligibility): **APPROVE** becomes **APPROVE_WITH_AUTHORIZATION**.
  - **S15** (REQUEST_EVIDENCE) and **S20** (REJECT_OR_ESCALATE): the outcomes are unchanged.
- **Unchanged:** S04, S09, S14, S16, S18, S19 (the AE band) and S10, S21 (the CRO band).

**What's at stake:** 10 scenarios (30 answers) where the title prior points to the wrong person.

## Arms

| Arm | Who decides | Context | n |
|---|---|---|---|
| **E** | the engine: governed discount procedure, Jev live for new inputs | variant corpus plus variant register | 18 |
| **R-full** | Opus 5.5 reader (the re-baseline's harness and procedure) | the whole variant corpus | 54 |
| **R-slice** | Opus 5.5 reader (G-23's harness) | the OWM-served slice of the variant (the register's terms name the title) | 54 |

**Controls (existing, no spend):** the same harnesses on the base corpus:
- O-full: discount, 1 unsafe of 54 (S32 is credit, so discount unsafe = 0);
- O-slice: 0 discount unsafe;
- the engine: 18/18.

Scoring uses the re-baseline's discount classifier against the variant's expectations.

## Predictions (fixed before any variant answer)

| # | Prediction | Why |
|---|---|---|
| P1 | **The engine holds 18/18** on T | Authority comes from the policy text through a Jev role map onto HR titles, and the approver from HR. No prior is involved |
| P2 | **The title prior is visible:** at least 1 R-full answer names Michael Torres where Dana Okafor is required | The prior plus Sarah's email both point to Michael |
| P3 | **R-full unsafe ≤ 6 of 54** | Opus reads the matrix carefully most of the time |
| P4 | **R-slice unsafe ≤ R-full unsafe** | The register's structured terms state the band's title outright, and the email isn't in the slice |
| P5 | **Michael's own requests are where readers fail most:** at least half of R-full's unsafe answers fall on S12, S15 or S20 | "The VP Sales can approve 18%" is the strongest prior, and it is wrong in T |

## Cost and guard

- **Readers:** 108 answers, about $16 (R-full) plus $5 (R-slice). Guard: stop if the first 6 of
  an arm average over $0.45 (full) or $0.20 (slice).
- **Jev:** a few dozen live calls for the new role-map inputs, cents. Utopia and OpenAI: none.

## Limits, stated before the run

- **One renamed band in one decision type** (discount). Credit's VP Sales concurrence is
  unchanged.
- **The lab wrote the variant and its expectations.** They follow mechanically from the
  procedure, but the designer still wrote them (G-39).
