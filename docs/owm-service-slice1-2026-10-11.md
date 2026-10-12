# B-06 slice 1: the OWM service passes §12.2 (2026-10-11)

**Status:** slice 1 of B-06 is built and passes the contract's §12.2 acceptance (contract v1.2,
spec `docs/superpowers/specs/2026-10-10-owm-service-design.md` §10). The regression gate is green.
All of it ran replay-only, at **$0**. Slice 2 (the register queue, procedures, the Dockerfile and
the container smoke test) comes next.

## 1. What passed

The acceptance suite is in `tests/owm_service/acceptance/`. It and `tests/owm_service/harness.py`
are the only code that reads the lab's truth; the service under `lab/owm_service/` never does.

| §12.2 | What it checks | Result |
|---|---|---|
| 1 | **All 42 decision scenarios** (22 discount, 10 credit, 10 SLA). Each gets a fresh org with its corpus, its clock (S45's `decided_at`; after every deadline on the ticket for the other SLA scenarios) and its request row seeded through the systems-of-record overlay. The requester asks with the scenario's `submitted`; Marcus Adeyemi asks the SLA ones. The kernel's record for version 1, as the service stored it, equals the reference (`governed.decide` called directly) on every key but `scenario`. It also equals the committed record on the fields `check_equivalence` compares: experiment 4 v3 for discount, experiment 5 for credit, experiment 6 for SLA | **42/42** |
| 2 | **Input conflicts** equal the oracle's on the 14 scenarios whose `expected:` lists them: S22 `requested_discount`, S23 `request_date`, S24 `status`, S35 `requested_limit_usd`, and 10 with none. Each conflict names the requester and blocks | **14/14** (and the count, 14, is pinned) |
| 2 | **Approvals and actions** match the truth: the discount approver by person id; the credit approvers as `(id, kind)`; for an SLA credit owed, the claim decision by the `decide_claim` holder and the credit's expected actor the `issue_memo` holder. Actions are decided exactly when the outcome clears, with the row's figures (the SLA amount equals the truth's `credit_usd`) | **42/42**. Version 1's gated outcome equals the truth's on all 42, so approvals were compared on every scenario |
| 3a | An `as_of` in the body is refused with 422 at the model and at the HTTP level, and nothing is decided. S23 then decides on the CRM's 2026-09-23 under PRICING-POLICY-2026, with Michael Torres as approver | pass |
| 3b | A second decision on DR-9001 is 409 DC-6, with `existing` naming the live one (core and HTTP) | pass |
| 3c | DR-9102 (S10) at 25% needs the CRO (floor 2). Sarah Chen edits the CRM to 8% and re-runs. Version 2 is APPROVE, but a blocking ratchet condition waits on David Morgan (EMP-300), and clearance is refused `condition_open` | pass, replayed |
| 3d | DR-9001 (S22's branch): the same with the CRM edited to 8%, and the ratchet condition names Michael Torres (EMP-200) | pass, replayed |
| 4a | S36 end to end. Marcus asks about SR-39385 (BREACH_CREDIT_OWED, $4,200) and gives the claim decision. Paul Brennan clears `issue_service_credit`, and the lab adapter redeems it and issues the credit. A new decision on SR-39385 is `spent` at version 1, its `executed` names the first decision and the clearance, and its clearance is refused `spent` | pass |
| 4b | Two clearances on one decision are redeemed at once in two threads. Exactly one is redeemed; the other is refused `spent` | pass |
| 4c | A `failed` report leaves the decision spent and opens INC-0001 for Customer Support, and a new clearance is refused `spent` | pass |
| + | **Rebuild:** after every acceptance test, a fresh org over the same log rebuilds the `clearances` and `executions` projections from the events. It reads back the same decisions and the same projections | **107/107** tests |

**Totals:** 107 acceptance tests. The full suite is **693 passed** in 76 s
(`uv run --group owm-service pytest -q`). `mypy` (strict) and `ruff` are clean, and
`scripts/owm-gate.sh` is **GREEN**. Without the `owm-service` group, the one HTTP acceptance test
skips and the other 106 run.

### Findings from the run

- **The SLA cap doesn't recognise a ticket's own credit (S36).** After the $4,200 is issued on
  SR-39385, the kernel counts it against the account's June cap (`sla.yaml`, `cap_used`). It finds
  $2,100 of room left and decides BREACH_CREDIT_OWED for $2,100 more, without seeing that the
  credit already paid was this ticket's own. **The service's `spent` is what stops a second
  payment** (the action is executed once per subject). This is pinned in the test. It's a kernel
  point for a later run, not a service defect.
- **Two SLA claim deadlines fall after the demo clock (S40, S44).** The nine SLA scenarios without
  a `decided_at` are asked at a clock after every deadline on their ticket (spec §10), so the clock
  decides exactly as `decided_at: None` ("after all events") does. The test proves it: every
  obligation falls due before the decision on all nine. Seven are asked at the service's default
  clock, 2026-09-23 09:00 CT. S40 and S44 are asked at 2026-10-01 09:00 CT, because the default
  clock comes before some of their deadlines:
  - S40's claim decision and credit memo are due 2026-09-27;
  - S44's claim decision is due 2026-09-29.

  The 42/42 comparison holds at those clocks. On the demo clock (2026-09-23), those duties show as
  still open.

## 2. What it lets us say (spec §1)

| Claim | Label |
|---|---|
| The OWM refuses clearance for actions taken through BlueLeaf's own tools: `differs`, `condition_open`, `awaiting_approval`, `spent` and the rest | **Proven** (items 3 and 4; the clearance suite covers every code) |
| The 42 decision scenarios give the kernel's results through an API, with conditions, approvals and actions matching the truth | **Proven** (items 1 and 2: 42/42, 14/14, 42/42) |
| A requester who edits the CRM to land in her own band is stopped by the ratchet (G-46) | **Proven** (items 3c and 3d, on the CRO's band and the VP Sales's) |
| `self_sourced_basis` sees only changes made through the service, not edits made in a real CRM | **Bounded** |
| Demo sign-in only. Jev is replay-only by default | **Bounded** |
| Executors outside BlueLeaf honour clearance; deciding without a revoked document (G-43); protection against meaning flips (G-44); linking re-entered requests (DR-9002) | **Roadmap** |

## 3. Cost

**$0.** Every Jev answer was a recorded one: the service's engine is replay-only (`OWM_JEV=replay`,
the default), so an unrecorded question would have failed the test as a 503. The item 1, 3c, 3d
and 4a tests also assert that the org's own `jev-calls.jsonl` was never created. The two 8% re-runs replay
because the discount judgments ask about the justification, the customer, the product and the
documents, never the figure. No live run was needed or made.

## 4. Paste-ready note for the garbanzo session

> **The lab's OWM service, slice 1, is ready to connect (contract v1.2, garbanzo 30977cd).**
>
> **Where it is.** Run it locally from shiny-waffle with
> `PYTHONPATH=lab uv run --group owm-service python -m owm_service`. It listens on
> `http://localhost:8000`. The contract is under **`/api/v1`**, and `GET /healthz` is the health
> check. Slice 1 serves `GET /me`, `GET /approvals` (#19), the decision routes (#20), and
> clearance, redeem and report (#21). The register and procedure routes (#16 to #18) arrive in slice 2.
>
> **The `OWM_API_URL` route.** Please add a server-side API route in web-next that forwards to
> `${OWM_API_URL}/api/v1/...`. The service sends no CORS headers: only web-next's server should
> reach it. The lab routes (`/lab/*`) are on by default locally. The Docker image (slice 2)
> defaults `OWM_LAB_ROUTES=0`, so a demo deployment must set it to `1` and keep the service
> reachable only from web-next's server.
>
> **Sign-in (a session bridge is needed).** There is no identity provider. `POST /lab/sessions`
> takes `{"person_id": "EMP-101"}` or `{"agent_id": "AGT-DEALDESK", "on_behalf_of": "EMP-101"}`
> and returns `201 {token, actor}`. Send the token as `Authorization: Bearer <token>` on every
> `/api/v1` call, reads included. A missing, unknown or expired token is 401. A session lasts
> 12 hours and survives a service restart. `DELETE /lab/sessions/current` signs out, and
> `GET /api/v1/me` returns the actor with their `function`.
>
> The bridge should map web-next's demo user to a Northstar person, then open and cache an OWM
> token server-side. The demo cast:
> - Sarah Chen, EMP-101, the requester;
> - Michael Torres, EMP-200, VP Sales;
> - David Morgan, EMP-300, CRO;
> - Marcus Adeyemi, EMP-602, Director of Customer Support;
> - Paul Brennan, EMP-604, Support Billing Manager;
> - the Deal Desk Agent, `AGT-DEALDESK`, for Sarah.
>
> **A 503 on `POST /decisions`.** The body is `{"error": "cannot_decide", "detail": "..."}`.
> Nothing was written, so it's safe to retry. A plain message: *"The OWM couldn't decide this
> request just now. Nothing was recorded, and you can try again."* Keep `detail` for a "details"
> disclosure, not the headline.
>
> **`file.source_id` is a corpus path.** On a register entry (slice 2), `file.source_id` is the
> document's path in the org's corpus, `documents/<file>.md`, not a garbanzo document id. Please
> map it to your own ids. The mandate fixture's is `fixtures/mandate-dealdesk-2026.md`.
>
> **`PUT /register/settings` is for Executives only,** and it's logged. It arrives in slice 2.
> Please show `on_mismatch` read-only for anyone else.
>
> **The demo clock starts at 2026-09-23 09:00 CT**, not today, and runs forward from there.
> *Effective from* should default to the register's `clock` (on `GET /register`, slice 2), not the
> browser's date.
>
> **Where we differ from the contract's examples:**
> - **`v2Ratchet` authority.** The example shows `authority.required_role` and `approver` as null
>   for an authorized requester. The kernel and the truth (S14) name the requester's own role
>   ("Enterprise Account Executive") and the requester (Sarah Chen). Please render the filled
>   form.
> - **A dry run that would clear** returns `{"cleared": false, "reasons": []}`: empty `reasons`
>   means *would clear*. `cleared: true` always carries a clearance id, and a dry run issues none.
> - **History kinds** (`GET /decisions/{id}/events`):
>   - a dry run that would clear is `clearance_cleared`, and its `detail` says nothing was issued;
>   - a refused redemption, such as a second redeem of a used clearance, is `clearance_refused`,
>     and its `detail` starts "Redeeming CLR-… was refused: …".
> - **Other small differences:**
>   - `register_used` lists every registered document the decision relied on (S22 has 3, the
>     example 2);
>   - judgments carry the kernel's full probability distribution;
>   - a `condition_open` reason's `detail` is the condition's full sentence;
>   - a decline closes a decision even while a condition is open, so it reads `declined`.
>
> **Work items** (`GET /approvals`):
> - ids are `DEC-0001:v2:approvals[0]` for a `decision_approval` and `DEC-0001:c2` for a
>   `condition`;
> - `href` is the decision's API path, `/api/v1/decisions/DEC-0001`;
> - other ids: `DEC-0001`, `CLR-00001`, `INC-0001`, counted per org from 1, and conditions `c1`,
>   `c2`… unique within a decision across versions.
>
> **Still yours:** a Northstar demo org (it's Bluefin today).
>
> **What's proven:** all 42 decision scenarios reproduce through the API; clearance refusals
> (`differs`, `condition_open`, `awaiting_approval`, `spent`…) hold; and the ratchet stops a
> requester who edits the CRM into her own band. All of it ran replay-only, at $0.

## Slice 2 addendum: the attack set through the queue

All 24 register attack cases (C01–C24, run 2026-10-08) were replayed through the two-step queue
(draft not used; submit, then approve) on the base corpus at the registrar's fixed clock.
**24/24 cases give the same admitted/refused result as the one-shot registrar (0 of 14 attacks
admitted), and 4 cases name a different rule, each explained below.** Three mechanisms cause the
differences. In C13 and C14, submit runs the content rules before approval runs RR-4. In C11, the
agent session is refused before any registrar run. In C19, the body model refuses the relation type
before the registrar runs. Every listed case breaks more than one rule. Registrar only: no kernel
decision, so no Jev and $0.

- **C11** (an agent proposes a pricing policy): one-shot RR-1, queue RR-2. The approver EMP-200 is
  not among the actors (RR-1), the submitter is an agent (RR-2), and the empty terms also miss the
  pricing schema (RR-6). The queue's submit session is an agent, which can never submit.
- **C13** (the submitter approves their own credit policy): one-shot RR-4, queue RR-6. The approver
  is the submitter (RR-4), and the empty terms miss the six required credit terms (RR-6), which
  submit checks before anyone is asked to approve.
- **C14** (the wrong person approves a credit policy): one-shot RR-4, queue RR-6. EMP-200 is neither
  the Finance head nor an Executive (RR-4), and the same empty terms miss the credit schema (RR-6).
- **C19** (a pricing policy with a `replaces` relation): one-shot RR-6, queue "malformed". The terms
  are empty so required terms are missing (RR-6), and `replaces` is not an allowed relation type
  (RR-14). The queue's request body admits only `supersedes` and `under`, so it refuses the body
  before the registrar runs.

The differences are listed in `tests/owm_service/fixtures/attack_rule_differences.json`, and
`tests/owm_service/test_attacks_through_queue.py` fails if they change.
