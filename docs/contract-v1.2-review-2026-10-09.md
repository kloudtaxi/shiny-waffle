# Review: contract v1.2 on `owm-decisions` (glowing-garbanzo b9ab487, 2026-10-09)

**What was reviewed:**
- `owm/docs/contract-v1.2.md`;
- `web-next/lib/contract/owm-decisions.ts`;
- `web-next/lib/contract/s22.example.ts`.

All three are on `v1/use-manage-operate` at b9ab487. This is the lab's B-05/B-06 review.

**How it was checked:**
- Every claim the draft makes about the kernel was checked against shiny-waffle `deebdd8`.
- S01, S22, S23, S27 and S34 were replayed through `governed.decide` from recorded judgment answers.
- **Cost: $0.** No live calls.

## Verdict

**A strong draft. Accept its structure, and fix three holes before the lab builds the service.**
- **What it gets right:**
  - it reports the kernel honestly (§5.1);
  - resolutions never take a value from the body;
  - "redeem" makes single use real;
  - the ratchet is a high-water mark;
  - Try to act is a dry run.
- **The three holes:** each one lets the requester reach her own authority by a route the ratchet
  doesn't watch. **One of them is S23's trap, built into the API.**

## What was verified (all correct)

| The draft says | Checked |
|---|---|
| S22 replays identical to S01 apart from the scenario id (the kernel has no `submitted` input) | **Yes:** no field differs |
| S22 makes 14 judgments: `role` 5, `party` 4, `covers_product` 4, `basis` 1. The lowest choice confidence is 0.94; the lowest yes/no is 0.96 | **Yes** |
| `CHOICE_FLOOR` 0.5, a yes/no band of 0.30–0.70; `judge`, `gate`, `governed` line references | **Yes** (`kernel.py` 43, 411–423, 578–590; `governed.py` 74–75) |
| PROC-DISCOUNT v1 sha256 `f49c4a68…` | **Yes** (`procedures.yaml`) |
| Credit approvers are names with no roles, and S34's concurrence moved to David Morgan with nothing saying why | **Yes:** S27 gives Elena Novak (approval) and Michael Torres (concurrence); S34 gives Elena Novak and David Morgan, with no `passed_from` |
| `requestor_authorized = amount <= limit and not sod` | **Yes** (`kernel.py` 736–737). The answer to §12.6 is below |
| CREDIT-POLICY-2026: VP Sales concurrence over $500,000 for Strategic accounts | **Yes** (`base.yaml` terms) |
| S36: the claim decision is Marcus Adeyemi's | **Yes:** `decide_claim`, EMP-602, by 2026-07-24 |

## Must fix (P1): three ways to self-approve that the ratchet doesn't see

### 1. `as_of` from the request body is S23's trap

`POST /decisions` accepts `as_of?`, and `as_of` picks the policy in force. S23 is exactly this
trap: a submission dated 2025, where "following the submission applies the 2025 policy, under
which Sarah could approve 15% herself."

**Replayed** (the kernel, with recorded answers, on DR-9001):

| `as_of` | Policy | Outcome | Sarah authorized | Approver |
|---|---|---|---|---|
| 2026-09-23 (the CRM's date) | PRICING-POLICY-2026 | APPROVE_WITH_AUTHORIZATION | No (limit 10%) | Michael Torres |
| **2025-09-23 (from the body)** | **PRICING-POLICY-2025** | **APPROVE** | **Yes (limit 15%)** | **Sarah Chen** |

**What follows under the contract as drafted:**
- version 1 is APPROVE, with no approvals, so there's no floor above Sarah's band;
- with no `submitted`, there's no conflict condition;
- the state is `ready`, and clearance issues 15%.

**The fix:**
- `as_of` is always the system of record's request date, read like `requested_by`.
- Drop it from `DecisionRequest`. If a "what if" read is wanted, give it its own endpoint, which
  produces no `actions` and carries a flag.
- `submitted.request_date` stays a compared figure, as in S23 (`input_conflicts: [request_date]`).

### 2. A new decision on the same subject resets the floor

- `POST /decisions` "returns version 1", and nothing stops a second decision for DR-9001.
- **The route:** Sarah (or her agent) edits the CRM to 8% and asks again. The new decision's
  version 1 is level 0, so it has no floor, no ratchet condition and no second person.
- The ratchet only watches re-runs *within* a decision.

**The fix:**
- **one live decision per subject:** `POST` for a subject that already has a decision returns it
  (409, with its id), or re-runs it;
- the floor is keyed to the subject (`request_id` or `ticket`), not to `decision_id`;
- a withdrawn or declined decision keeps its floor for that subject.

### 3. The ratchet's level is undefined when version 1 has no action

§6.2 defines the discount level as "the band the decided discount falls in". It doesn't say what
happens when version 1's outcome is REJECT_OR_ESCALATE or REQUEST_EVIDENCE.

**The route:**
1. A request at 25% exceeds the exception's 15% maximum, so it's rejected.
2. Sarah edits the CRM to 8%.
3. The re-run is APPROVE, within her own band.

If the rejection had no level, there's no floor.

**The fix:**
- **The level comes from the record's figure, for every outcome.** 25% is band 2, rejected or not.
- When the figure is missing (`missing_record`), the level comes from the submitted figure.
- A re-run that goes from no action to an action below the floor gets the ratchet condition like
  any other.

**Add all three to G-46's kernel check** (§12.15) before anything claims the ratchet works.

## Should fix

1. **The rest of `subject` comes from the record.** `DecisionRequest.subject` accepts `account_id`
   and `product`. Name only the subject id (`request_id` or `ticket`) and read the rest from its
   row. A body value that differs is compared, as `submitted` is, never used.
2. **`actor` comes from the session.** `ClearanceRequest.actor` "must match the caller". Derive it
   from the session, as `on_behalf_of` is, and ignore or compare a body copy. The body's
   `decision_id` must equal the path's.
3. **A revocation should make a decision stale for clearance.** A decision reads the register as of
   the request date, but the action happens later. If a document in `register_used` is
   **revoked** with effect on or before the action date (the C01x probe: revoking EXC-ACME-NS500-15
   from 2026-09-15), clearance should refuse with `stale`. A superseding document shouldn't: the
   policies govern "requests dated on or after" their start.
4. **Mandate limits need a refusal.** `may_do.limits` (for example, 200 a day) has no code. Use
   `outside_mandate` with a detail, and say so.
5. **Name the fields and their units in one table.** The condition's `field: "discount"`, the
   truth's `requested_discount`, the CRM's `requested_discount_pct` ("15.0", a percentage string)
   and the params' `discount` (0.15, a fraction) all appear. Add one mapping table, so
   `self_sourced_basis` and `differs` compare like with like.
6. **A record is a version plus its events.** Ground rule 4 says nothing is edited in place, but
   `approvals[].given` and `state` change on a version after it's written. Say so explicitly, and
   label the S22 example's `v2` as v2 after Michael's approval.
7. **Draft checks can act as an oracle.** `submit: false` returns the rules' findings to anyone,
   agents included. That helps an agent fix a draft, and it also lets someone tune a meaning flip
   against RR-6's checks (G-44, pinned). It's acceptable for v1.2, because a person submits and
   another approves, but it belongs on the known-limits list.

## Answers to §12

| # | Item | Lab answer |
|---|---|---|
| 1 | RR-13 in a queue | **Accept** the scoped check: same kind and scope, or the change's targets. Every other rule runs again in full at approval |
| 2 | Conditions come from the service | **Accept for v1.2, if they're tested against the oracle.** `src/northstar/oracle.py` already computes input conflicts. The truth declares them for 14 scenarios: S22 `requested_discount`, S23 `request_date`, S24 `status`, S35 `requested_limit_usd`, and 10 with none. The service's comparison must match all 14 |
| 3 | The kernel has no `submitted` | **Confirmed** (S01 ≡ S22). The service's harness carries S22–S25 and S35 |
| 4 | Judgments say what they were about | **Accept.** The lab adds `about` to `judge` |
| 5 | Flags are free text | **The kernel should emit `{code, text, routes}`.** The gate knows which input routed, and parsing about 20 string formats is fragile |
| 6 | Approvers by id and role | **Accept:** ids, roles and `passed_from` (S34), plus a check that the approver isn't the concurrer. **The credit APPROVE question:** it's intended. Both registered credit policies set separation of duties, so a requester never approves their own credit, and no credit scenario expects APPROVE. Keep APPROVE in the enum for a policy without it |
| 7 | Revoked isn't missing (G-43) | **Accept** the flag. Changing the outcome is the lab's fix |
| 8 | Change history | **Accept:** the lab service logs its own CRM writes. The demo's CSVs are static, so `self_sourced_basis` only sees writes made through the service. Say so on screen |
| 9 | Who owns the CRM | **Accept:** only the floor-level approver confirms until an owner is named |
| 10 | A `declined` code | **Accept** |
| 11 | The floor as a high-water mark | **Accept.** It's better than G-46's wording |
| 12 | Approvals bind to a version | **Accept.** In S22's main flow nobody approves twice, because DC-4 holds version 1 |
| 13 | The SLA claim gates the credit | **Confirmed** (S36). Also, S36's `issue_memo` belongs to Paul Brennan (EMP-604, Support Billing Manager). He's the natural actor for `issue_service_credit` once Marcus decides the claim |
| 14 | `agent_mandate` ownership | **Held,** with phases 2–3. When it's picked up: a mandate is the one kind whose owner comes from its entry (`owner.function`), not its kind |
| 15 | G-46's kernel check first | **Agree,** with must-fix 1–3 added to it |

## What the lab builds against it (B-06)

**The demo service's acceptance:**
1. All 42 decision scenarios (22 discount, 10 credit, 10 SLA) reproduce the kernel's committed records through the service.
2. The additions the service makes (conditions, approvals, actions) match the truth's `expected`
   wherever the truth states them.
3. A test for each must-fix:
   - `as_of` from the body refused or ignored;
   - a second decision on DR-9001 refused, or the same decision returned;
   - a 25% → 8% re-run ratcheted.

## Reply you can paste to the garbanzo session

> The lab reviewed contract v1.2 (shiny-waffle `docs/contract-v1.2-review-2026-10-09.md`). Every
> kernel claim checks out on a replay, including S01 ≡ S22, the 14 judgments and S34's unexplained
> concurrence. The structure is accepted. **Three P1 holes to fix first, all routes to
> self-approval the ratchet doesn't watch:**
> 1. **Drop `as_of` from `POST /decisions`** and read it from the record's request date. Replayed
>    with `as_of` 2025-09-23, DR-9001 decides APPROVE under the 2025 policy with Sarah authorized:
>    S23's trap, through the API.
> 2. **One live decision per subject.** A second `POST` for DR-9001 after a CRM edit starts at
>    version 1 with no floor. Key the floor to the subject.
> 3. **Define the ratchet level from the record's figure for every outcome**, so a rejected 25%
>    still sets band 2.
>
> **Should fix:**
> - the subject and `actor` come from the record and the session, not the body;
> - revocation of a document in `register_used` makes a decision `stale` for clearance;
> - say which code a mandate limit uses;
> - one table for field names and units;
> - a record is a version plus its events.
>
> **§12:** accept 1, 4, 7–12 and 15 as proposed; 2, 3 and 6 with the notes in the review (credit
> APPROVE being unreachable under separation of duties is intended); 13 confirmed (also,
> `issue_memo` belongs to Paul Brennan); 14 held.
