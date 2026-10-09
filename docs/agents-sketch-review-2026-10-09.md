# Review: "Agents in BlueLeaf: a sketch" (glowing-garbanzo, ux v1.2, 2026-10-09)

**What was reviewed.** The sketch, relayed by the user, from the web-next session in
glowing-garbanzo. It was checked against the lab: `truth/scenarios/22-*.yaml`, G-18, G-23, G-35,
J3, the registrar and the register attacks.

## Verdict

**Adopt the stance and phase 0 now, and build phase 1 with the OWM API. Fix three things first:**
1. **The condition re-run lets the requester lower her own approval level.**
2. **The mandate's "at most the cleared value" contradicts refusal reason 3.**
3. **Clearance has to bind the action's parameters.**

**Hold phases 2 and 3** (Manage › Agents, mandate changes, trust records) until mandates are an
object the lab has tested. They're new, and the screens would show numbers nobody has measured.
That's the overclaim G-45 just removed.

## What's right

- **"Agents propose; BlueLeaf decides; systems act."** It matches G-23 (the OWM path held 28 of 28
  for at most $0.00026 a decision; the agent gathers and explains). It also matches the
  registrar's RR-2: agents propose, never submit or approve.
- **The check sits at the action, not in the prompt.** The credential is held by BlueLeaf's action
  tool, never by the agent, which makes clearance impossible to skip by construction. That's the
  right answer to "what stops the agent applying the discount?" and the honest boundary in §7
  ("enforced for actions through BlueLeaf's tools; other paths are audited, not stopped") is
  correct.
- **Mandates as governed state, registered in two steps.** It reuses machinery the lab has already
  built and attacked rather than inventing new machinery.
- **Resolving a condition re-runs the decision rather than ticking a box.** This agrees with G-45.
- **The flagship flow is S22, told with an agent.** It checks out against the truth: DR-9001 is 8%
  as submitted and 15% in the CRM, so the decision is APPROVE_WITH_AUTHORIZATION by Michael
  Torres. J3's plain readers put APPROVE in the record 3 of 3 times on S22. It's a strong demo
  moment.
- **The "what's real" table, the "won't build" list, and "exceptions first" at scale.**

## What to change

### 1. The re-run hole: the requester can lower her own approval level (fix before showing §6)

§6, step 4, says that if Sarah "had corrected the CRM to 8% instead, the re-run would decide on
8%, within her own authority." That's S22's danger again, by a different route:
- the person whose authority depends on a value changes that value;
- she resolves her own condition;
- the decision re-runs into her band.

**The lab never tested this.** Its threat model puts the systems of record (`structured/`) out of
the attacker's reach. In a real company, an account executive edits CRM opportunities every day.

**Proposed rule: approval levels only ratchet down with a second person.** A resolution or re-run
that lowers the required approver below what the decision first required needs one of these to
confirm it:
- the approver at the original level, or
- the system of record's owner.

Separately, a system-of-record change made by the requester after the request is recorded as a
**self-sourced basis** and flagged. Sarah can still confirm 15%, since that doesn't lower the level.

Logged as **G-46**. It's a design fix plus a cheap lab check: the kernel only, no model. Change
DR-9001 in the CRM as the requester, re-run, and see who approves, with and without the ratchet.

### 2. "At most the cleared value" contradicts refusal reason 3

- **The Deal Desk mandate** says "apply a cleared discount, at most the cleared value".
- **§5.4 and §6** refuse 8% when 15% was decided ("differs from the decision"). Under the
  mandate's wording, 8% ≤ 15% passes.

**Pick one: an exact match by default.** An action executes the decision, not a variant of it. "At
most" would be an explicit per-action option in a mandate, never the default. Without that, an
agent could apply any smaller discount under one clearance.

### 3. Clearance must bind parameters (a contract change for #21)

`{action, actor}` isn't enough to check reasons 3 and 5. **The proposed shape:**

```ts
// request
{ decision_id, decision_version, action, params, actor }
// response
| { cleared: true, clearance_id, bound: { decision_id, decision_version, action, params },
    expires_at }
| { cleared: false, reasons: { code: "condition_open" | "awaiting_approval" | "differs"
      | "outside_mandate" | "stale" | "suspended", detail: string,
      waiting_on?: { id: string; name: string } }[] }
```

- A clearance id is **single-use and short-lived**, and the adapter executes exactly the bound
  parameters.
- Otherwise a clearance for 15% on DR-9001 could be replayed, or reused for another account.

G-45 is updated with this.

### 4. Smaller points

- **"Delegation can't amplify"** is enforced by decide-then-clear, not by the mandate's "no item
  exceeds what the principal could ask for": anyone can *ask*. Say that a mandate limits which
  decision types and scopes an agent may originate, and that authority always comes from the
  decision's approver.
- **The §10 row "attacked (0 of 14)".** The one agent attack (C11) was stopped by RR-1, before
  RR-2. RR-2 is proven by the registrar's self-check. Better: "proven in the lab's registrar
  (self-check); the one agent attack was refused".
- **"Review minutes per 100 actions".** The lab measured a *routing rate* (G-18: 0.79% to a
  person), not minutes. Call it review load until minutes are measured.
- **The wireframes' numbers** (1,284 asks, 89% cleared, 3.4 min) need the existing Sample badge
  wherever they reach a screen.

## The open questions (§14): recommended answers

| # | Question | Recommendation |
|---|---|---|
| 1 | Mandate approvals | **The same rule as documents** for v1: the owning function's head or an Executive, never the submitter. A system-owner co-sign (for example, whoever owns the CRM) only when a mandate adds a new *write* action. Later, not v1 |
| 2 | Delegated agents | **One per team, acting for whoever asks** (the sketch's default), with `on_behalf_of` on every record |
| 3 | Pause in Use | **Yes, for themselves only.** Pausing only narrows, so it's safe without a second person |
| 4 | Where agent state lives | **Mandates as a register kind** (`agent_mandate`, structured terms). The registrar's rules then apply unchanged: owning function, head approval, no backdating, supersession for new versions, revocation for retirement. Clearance lives in `owm-decisions`. **No `owm-agents` context for v1.** Suspension is operational (Operate), not a registration. It's sovera-owm's call, as an amendment candidate |
| 5 | External agents over MCP | **Ask, yes; act, later.** An external agent can ask BlueLeaf to decide (read-and-ask), but enforcement is real only where BlueLeaf holds the credential. Acting stays on the roadmap |

## What it means for us (shiny-waffle and the OWM API)

- **The `owm-decisions` contract** (decided 2026-10-09) takes phase 0 now:
  - `Actor`;
  - `proposed_by`, people-only `submitted_by` and `approved_by`;
  - `requested_by` and `actor` on a decision;
  - `resolved_by` plus a re-run on conditions;
  - clearance in the bound shape above.
- **Lab order, when you pick it up:**
  1. G-46's ratchet check (cheap and deterministic).
  2. Clearance in the OWM API (G-45).
  3. Candidate 1, "clearance under pressure". It needs the MCP subject mode, so it waits on the
     MCP build with set G.

## Reply you can paste to the garbanzo session

> Reviewed against the lab (docs/agents-sketch-review-2026-10-09.md in shiny-waffle). The stance,
> phase 0 and the S22 flagship flow are right, and the cited numbers check out. Before the v1.2
> contract:
> 1. **§6 step 4 is a hole.** Sarah editing the CRM to 8% and re-running puts the decision in her
>    own band. Approval levels should only ratchet down with a second person: the original-level
>    approver or the system of record's owner. Flag a requester's own system-of-record change as
>    a self-sourced basis. Logged as G-46.
> 2. **The mandate's "at most the cleared value" contradicts refusal reason 3.** Make an exact
>    match the default, and "at most" an explicit per-action option.
> 3. **Clearance (#21) takes `{decision_id, decision_version, action, params, actor}`** and returns a
>    single-use, short-lived clearance bound to those parameters, or coded reasons.
>
> Answers to §14:
> 1. Mandate approvals: the same rule as documents.
> 2. Delegated agents: one per team.
> 3. Pause in Use: yes, for themselves only.
> 4. Agent state: mandates as a register kind, clearance in `owm-decisions`, no `owm-agents` for v1.
> 5. External agents: ask now, act later.
>
> Hold phases 2–3 until mandates are lab-tested, and Sample-badge any wireframe numbers. Also fix
> §10's RR-2 row: C11 was stopped by RR-1, and RR-2 is proven by the self-check.
