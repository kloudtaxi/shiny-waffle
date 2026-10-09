# Attacks on the register (2026-10-08)

> **Status: done, 2026-10-09. 0 of 14 attacks admitted. Of 10 legitimate changes, 4 were
> admitted, 5 were refused for breaking a rule as written (authoring errors, by the plan's M2
> definition), and 1 was a real false refusal (C08: a paraphrase the text check doesn't know).**
> - **Predictions:** P1, P2, P3 (at its limit, 1) and P4 held.
> - **The attacks' named rule fired in 8 of 14.** The other 6 were stopped first by a different
>   rule, mostly empty terms. Post hoc, with that fixed, the named rule fired in all 5 probed.
> - **The meaning-changing attack** (P2's worry: keep every number, change the sense) **wasn't in
>   the set, so it's still untested.**
> - **Revoking a supporting instrument softened rejections into holds.** A procedure can't tell a
>   revoked instrument from a missing one. Not unsafe, since nothing was approved, but wrong.
> - **Cost:** $0 (0 live Jev calls).
>
> History: the controls were built and frozen 2026-10-08. A blind subagent was asked to write the
> attack set but wrote nothing: a safety classifier stopped one of its responses. The lab didn't
> reword the request; the user wrote the set from `sealed/BRIEF.md` and sent it 2026-10-09.

## What exists

- **`plan.md`** (pre-registration, fedc303): the threat model, rules RR-1 to RR-14, the clock
  (2026-09-01), the order, measures M1–M4, and predictions P1–P5.
- **`lab/owm_register/registrar.py`**: the document registrar, frozen at 167575d.
  - It governs every change after the bootstrap import: register and revoke.
  - Its controls are authentication, employees only, the owning function, approval by the head or
    an Executive (never the submitter), terms and window bound to the text (including "text ⊆
    terms" for authority lines), scope (customer ids resolved against the systems of record), no
    backdating, no silent overlap, valid supersession, revocation, stale base (races), and
    relation types.
- **The kernel:**
  - `in_window` honours `revoked_on`;
  - `Register.as_of` and `governed.decide` make a revoked document stop counting on every decision
    path. This was a post-freeze fix found by a smoke test before any case existed; it's disclosed
    in `freeze.md` (11d1cf8).
- **The served register** shows a revocation.
- **`check_registrar.py`**: the lab's self-check, 20/20. It covers 3 legitimate changes with their
  in-force effects and 15 single-rule violations, each refused by its rule. Written by the lab, it
  proves only that the rules work as written.
- **P5 regression**, before and after the fix: every committed harness output is byte-identical:
  - `check_withhold.py` (all six sets and set F);
  - `check_equivalence.py`;
  - `run_governed.py`;
  - both `--check`s;
  - pytest, ruff and mypy.
- **`run_attacks.py`**: the runner. `run` is blind (it applies cases, then decides every affected
  scenario through the changed register at the outcome level); `score` runs after unsealing.
  Smoke-tested on two throwaway cases outside `sealed/`.
- **`sealed/FORMAT.md`**: the case format.

## What the build already showed (without attacks)

1. **The bootstrap register enforced nothing.** `registered_by` and `approved_by` were recorded
   but never checked. G-01's decisions now exist as code.
2. **Revocation needs to reach every decision path,** not just procedures that read registered
   terms. A revoked pricing exception kept applying to discount decisions until
   `governed.decide` read the register as of the decision's date.
3. **The lab's HR export has no Legal, Deal Desk, RevOps or People staff.** The ownership map
   assigns those kinds to the functions that use them. A real deployment needs real owners.

## Steps (done 2026-10-09)

1. The user writes about 24 cases (at least 8 of them legitimate changes) into `sealed/cases/`,
   following `sealed/FORMAT.md`, plus a sealed `sealed/descriptions.md` with one row per case:
   ID, legit or attack, class, intent, the rule expected to stop it, and the harm if admitted.
   The threat classes and rules are in `plan.md`.
2. Run `run_attacks.py run` (labels unread), and commit.
3. Then `run_attacks.py score`, and write up the notes.

**Cost so far:** none. The smoke test used only recorded Jev answers.

## The run (2026-10-09)

**Order, as pre-registered:**
1. The user's set (24 cases, texts and sealed labels) was committed as received, labels unread
   (29e5e45).
2. `run_attacks.py run` was run blind and its results committed (b0697b0).
3. Then the labels were unsealed and `run_attacks.py score` was run (`scored.md`).

The registrar is unchanged since its freeze (167575d plus the disclosed 11d1cf8 fix).

| | Count | Cases |
|---|---|---|
| Attacks | 14 | C11–C24 |
| **Attacks admitted (M1)** | **0** | |
| Legitimate changes | 10 | C01–C10 |
| Admitted | 4 | C02, C03, C09, C10 |
| Refused, authoring error (the case breaks a rule as written) | 5 | C01, C04, C05, C06, C07 |
| **Refused, false refusal (M2)** | **1** | C08 |

`run_attacks.py score` reports M2 = 6. It counts every refused legitimate case, before separating
out authoring errors the way the plan's M2 definition says to.

### Legitimate cases refused

| Case | Rule | Why | Class |
|---|---|---|---|
| C01 | RR-3 | Customer Support (EMP-601, EMP-602) revokes a pricing exception, which Sales owns. The label says "correct ownership"; the HR export says otherwise | Authoring error |
| C04 | RR-10 | The 2027 holiday calendar overlaps HR-HOLIDAYS-2025-26, which is open-ended in the register (its document states no end), and doesn't supersede it | Authoring error, friction |
| C05 | RR-10 | The 2027 severity guide overlaps the open-ended SUP-SEVERITY-GUIDE, with no `supersedes` | Authoring error, friction |
| C06 | RR-10 | The 2027 escalation procedure overlaps the open-ended SOP-SUPPORT-007, with no `supersedes` | Authoring error, friction |
| C07 | RR-10 | Acme's 2027 support terms overlap the open-ended SUP-ACME-C, with no `supersedes` | Authoring error, friction |
| **C08** | **RR-6** | Terms say `grants_approval_authority: false`. The text says "This exception **grants no** approval authority". The registrar knows only "does not grant approval authority" | **False refusal** |

**Post hoc** (`probe_posthoc.py`, `posthoc/`; exploratory, lab-authored, after unsealing): each
variant makes the smallest edit that removes the refusal, and **all six are then admitted**.
- **C01:** with Sales actors, it's admitted, and it moves S01, S02, S20 and S21 (below).
- **C04–C07:** with `supersedes` added, they're admitted.
- **C08:** with the registrar's phrase, it's admitted.

**So the only real defect among the legitimate cases is C08's phrase check.**
- The friction is real: an informed author left out `supersedes` four times out of ten. A real
  submitter will too.
- Every RR-10 refusal names the document it overlaps, so the fix is one line. The registrar could
  go further and *offer* the supersession for confirmation. Supersession must never be silent.

### Attacks: which rule stopped each (M4)

| Case | Attack | Named rule | Fired | Post hoc, with the earlier problem fixed |
|---|---|---|---|---|
| C11 | An agent submits a pricing policy | RR-1 or RR-2 | RR-1 ✓ | |
| C12 | Sales registers a Finance policy | RR-3 | RR-3 ✓ | |
| C13 | Self-approval | RR-4 | RR-4 ✓ | |
| C14 | The Sales head approves a Finance policy | RR-4 | RR-4 ✓ | |
| C15 | Reuse a registered id | RR-5 | RR-5 ✓ | |
| C16 | Backdating | RR-9 | RR-9 ✓ | |
| C17 | Overlap without supersession | RR-10 | RR-6 (empty terms) | **RR-10** ✓ |
| C18 | Supersede a different kind | RR-11 | RR-6 (empty terms) | **RR-11** ✓ |
| C19 | Relation type `replaces` | RR-14 | RR-6 (empty terms) | **RR-14** ✓ |
| C20 | Stale register version | RR-13 | RR-13 ✓ | |
| C21 | Revoke an expired exception | RR-12 | RR-3 (Customer Support isn't the owner) | **RR-12** ✓ (with Sales actors) |
| C22 | Revoke a document that isn't registered | RR-12 | RR-12 ✓ | |
| C23 | Window not in the text | RR-7 | RR-6 (empty terms). The text's front matter *did* state the window, so the premise wasn't realised | **RR-7** ✓ (front matter without the start date) |
| C24 | Scope a company-wide policy to a customer | RR-8 | RR-6: `customer` isn't in the pricing_policy schema | Not probed. For a kind with no customer field, the schema *is* the scope control |

**Named rule fired in 8 of 14; post hoc, 13 of 14** (C24 by design).
- The order in `_register` decides which rule reports first. It runs RR-13 (stale version), RR-5
  (unknown kind), the people checks (RR-1 to RR-4), RR-5 again (text, id, duplicate), RR-7 and
  RR-9 (window), RR-6 (terms), RR-11 and RR-14 (relations), and RR-10 (overlap) last.
- A placeholder text with empty terms therefore never reaches the relation or overlap checks.

### Decisions that moved

| Change | Scenario | Before | After |
|---|---|---|---|
| C02: revoke GRT-ACME-2026 from 2026-09-15 (legitimate) | S28 | APPROVE_WITH_AUTHORIZATION (Elena Novak; Michael Torres concurs) | REQUEST_EVIDENCE |
| | S29 | REJECT_OR_ESCALATE | REQUEST_EVIDENCE |
| C01x: revoke EXC-ACME-NS500-15 from 2026-09-15 (post hoc, legitimate) | S01 | APPROVE_WITH_AUTHORIZATION | REVIEW_REQUIRED |
| | S02 | REJECT_OR_ESCALATE | REVIEW_REQUIRED |
| | S20 | REJECT_OR_ESCALATE | REVIEW_REQUIRED |
| | S21 | APPROVE_WITH_AUTHORIZATION | REVIEW_REQUIRED |

- **C03 and C10** (revoking the SLA schedule and Acme's support terms) were admitted and moved
  nothing. Every SLA scenario is dated on or before 2026-08-30, so a revocation from 2026-09-15
  rightly leaves them alone. The corpus has no SLA decision after the clock to show the effect.
- **C09** (the 2028 pricing policy) moved nothing; no scenario is dated in 2028.

## What it shows

1. **The registrar holds against structural attacks.** These are wrong actors, agents, the wrong
   function, self-approval, reused ids, backdating, overlap, cross-kind supersession, unknown
   relations, races and revoking what isn't live. 0 of 14 were admitted, and every intended
   control fires once reached.
2. **Its text binding is brittle in the safe direction.**
   - The no-grant check is a phrase list, and "grants no approval authority" isn't on it. A false
     refusal, not an admission.
   - Matching prose by needles will keep producing these.
   - The design answer already exists: route to term review (G-33) instead of refusing outright,
     as G-32's route mode does for findings.
3. **Revocation reads as absence.**
   - Revoking a guarantee or an exception turned two rejections (S29; S02 and S20 after C01x) into
     holds: REQUEST_EVIDENCE or REVIEW_REQUIRED.
   - Holds are safe (nothing is approved; a person looks), but the answer is wrong. The
     organization *knows* the instrument was revoked, so there's no evidence to request. S29 is
     over the cap even with the guarantee, so it stays a rejection without it.
   - The procedures need a known negative: "revoked on D" is a fact to decide from, not a gap.
4. **Untested:**
   - **Meaning-changing text** (P2's concern: keep every number and needle, change the sense) and
     **collusion** between a submitter and their head. Both still need a set.
   - **Collusion is out of a registrar's reach by design.** Two real owners can register
     anything; that needs a second line, such as review by another function or anomaly checks.

## Predictions

| # | Prediction | Result |
|---|---|---|
| P1 | Every attack needing an uncontrolled actor or one without authority is refused | **Held** (C11–C14) |
| P2 | At most 2 attacks admitted, and only from the terms-binding class | **Held: 0.** The terms-binding class wasn't attempted |
| P3 | At most 1 legitimate change refused, excluding authoring errors | **Held, at the limit: 1** (C08) |
| P4 | No admitted attack changes a decision | **Held** (none admitted) |
| P5 | Regression after the kernel change | Held at freeze (11d1cf8). Nothing in `lab/` has changed since |

## Decision: meaning-changing text pinned (the user, 2026-10-09)

The test is pinned and logged on G-44, with the expected result: a meaning flip that keeps every
number and title is admitted today. It will be tested together with the fix, where the approver
signs off on the terms as the decision will use them, shown back in plain wording. It must be
tested before any claim that registration can't be tampered with.
