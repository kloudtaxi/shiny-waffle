# Appendix A to the prototype core spec: the lab service's rulings, as mechanisms

**What this is.** The lab's OWM service, which the prototype ports, was built under 65 rulings
(R1–R65). This appendix restates each one as what the code must do and why, in terms of the
contract and the ports, and marks its fate in the prototype:

- **kept:** the prototype does the same. Spec §3.2's rule applies: everything in owm-decisions v1.4
  stays unless something in the spec changes it.
- **changed:** the spec changes it, and the row names the section. **changed (proposed)** marks
  a change the spec implies but doesn't decide; it needs the user's ruling before P1 freezes it.
- **dropped:** it concerned only the lab's own build, tests or demo, or the SLA use case (not in
  v1, §1.3). The row says which.

The numbers are the lab's, so a gate's mechanism notes can cite them. "§" means a section of the
spec (`docs/spec.md` in the bundle), and "PL-n" means a ruling in the builder's plan.

**Summary:** 26 kept, 22 changed (3 of them proposed, pending the user's ruling: R25, R31, R62), 17 dropped (2 of them superseded by later rulings).

## Deciding and the record

| # | What the code must do, and why | Fate |
|---|---|---|
| R2 | The kernel's judgment capture is a context manager keyed by the decision's subject, yielding what each judgment was about. The boundary needs the subject to attribute judgments | kept |
| R4 | Approval and concurrence items are listed only for an outcome that needs authorization; any other outcome lists none. Otherwise an outcome needing no approval would name the requester as its approver and raise a conflict | kept (its SLA half dropped) |
| R13 | Emitted JSON omits absent optional fields (TypeScript `?:`), and always includes required-but-nullable ones. The contract's types tell the two apart | kept |
| R19 | Any error while building the kernel's inputs from a record ends with no decision, never an unhandled 500 | changed: PL-8 and §9.1. An empty required field routes the decision (`missing_input`); a malformed one ends with no decision and the typed error `record_unreadable` (§9.4) |
| R20 | `register_used` lists every registered document the decision relied on, not only those whose terms were read. The stale check then watches more, which is stricter | kept |
| R21 | The procedure runner records the register entries it read terms from (`relied_entries`), and they join the basis documents and `register_used`. A policy read as a register entry must count as relied on | kept |
| R22 | When the system of record has no row, the requester is the signed-in person or the agent's principal, and a submitted requester stays in `submitted` | changed: §7.1. The catalog gate routes a subject with no row (`no_record`), and the requester is always the token's `sub`, never the body |
| R23 | For the self-sourced-basis flag, the reference time is the subject's first ask. The floor belongs to the subject, so a fresh ask must not reset the window | kept |
| R24 | When another decision set the floor, the ratchet's condition and flag name that decision. Two "version 1"s from different decisions would read as a contradiction | kept |
| R25 | A version below the floor whose confirmer would be the requester is not recorded. The requester never confirms their own lower level | changed (proposed): v1.4 ended this with 503 and `decision.failed`, but §9.1 keeps 503 for a port that can't answer. Proposed: a 403 refusal, since it is a people rule (§6.4), with the rule code named at P1. Pending the user's ruling |
| R26 | (A dropped concurrence confirmed by the floor band's holder alone) | dropped: superseded by R61 |
| R28 | A resolution must fit its condition's source: an input conflict takes a confirmed or corrected record; a ratchet takes a confirmed lower level. Anything else is refused (DC-2) | changed: §3.2. `missing_record` is gone with the catalog gate, so its corrected-record resolution goes too |
| R29 | A decline isn't held back by an open condition (DC-4) and closes the decision; "declined" is derived before "not ready". Otherwise the decision stays live and the next re-run drops the decline | kept |
| R31 | A re-run whose record now names a different requester is not recorded. This blocks reassigning a request to oneself and then approving it; a legitimate reassignment needs a new decision | changed (proposed): as R25, but proposed as a 409 refusal, since the record moved under the decision. Pending the user's ruling |
| R32 | A resolved input conflict covers its figure again if the record returns to the exact value confirmed. Approvals reset per version, and the ratchet catches a lower level | kept |
| R33 | Every event that changes a decision's derived state goes on the subject's stream: redemptions, reports and incidents included. Writes re-check the stream's last sequence, so an approval can't land on a spent decision | kept (Review Focus 1 in the plan) |
| R61 | A lower level below the floor opens one ratchet condition per confirmer, each naming one person. The conditions one version opens are a round. A round keeps its ids while re-runs stay below the floor at that version's level for the same confirmers, and the floor drops only when every condition in the round is confirmed; `floor.confirmed_by` names whoever completed it. The round's size is read from the log, so an old round never completes short of its confirmers. A new level opens a new round, and a confirmation in an unfinished round lowers nothing. The concurrence holder's condition reads "Confirm dropping the <title> concurrence: …" | kept |
| R62 | One person in two confirmer roles is not recorded: the confirmers are never the same person | changed (proposed): as R25, a 403 refusal (separation of duties, §6.4). Pending the user's ruling |
| R63 | After one of a round's confirmations, `what_changed` names who the round still needs. "Still below the floor" alone reads as if the confirmation did nothing | kept |

## Clearance, redemption and reporting

| # | What the code must do, and why | Fate |
|---|---|---|
| R12 | (The lab's choice of pydantic root models for validating external JSON) | dropped: an implementation choice with no contract effect |
| R34 | (A dry run that would clear answered as a refusal with no reasons) | dropped: superseded by R64 |
| R35 | Redeeming and reporting need an authenticated caller, whose actor is recorded | changed: §3.2 and R58. Every route needs an Authorizer token; R58 sets who may report |
| R36 | A clearance refused for an open condition gives the condition's full sentence as its detail, because the full sentence says what's needed | kept |
| R40 | The caller behind a redemption or report is recorded beside the executor | changed: §3.2. Every event carries the actor chain `{kind, id, on_behalf_of, delegation, grant}`; R58 binds the reporter |
| R58 | Any authenticated actor may redeem a clearance, but only the actor who redeemed it may report on it; anyone else's report is refused (DC-2). It binds the actor, not the token: the person, or the agent with the person it acts for. Clearance ids are sequential, so holding one proves nothing, and a hostile report would open a false incident and block the real one | kept, with the actor read from the token's claims (§6.2) |
| R64 | Every dry run answers `{dry_run: true, would_clear, reasons}`, refused or not, and the response type tells a dry run from a real clearance by `dry_run`, then `cleared`. The history still records a dry run that would clear without issuing anything | kept (§10.1's `request_clearance` dry run) |

## Lists, the clock and the systems of record

| # | What the code must do, and why | Fate |
|---|---|---|
| R14 | The clock's mode and base are recorded when it starts, and that record is the source of truth; outside test mode it can't be set. A restart must not change the clock's history | changed: §3.2 and §9.5. One injected clock, set only through the operator surface in test mode |
| R16 | A systems-of-record edit with a malformed value is 422 naming the column; a duplicate insert key is 409; an unknown table or key is 404 | changed: §2.2. These become `sor_stub`'s own responses (`contract/sor-stub.md`), not register rule codes |
| R60 | The systems of record accept edits only on the request tables, and inserts only where a pack needs them. The tables that decide approvers, tiers and customers (people, accounts, customers) are never editable through this route | changed: §2.2, kept as `sor_stub`'s rule, people editing with their own tokens |
| R65 | The lists are `Page<T>`, `{items, next_cursor}`, served whole as one page with `next_cursor` null; a cursor the service never issued is ignored | kept |

## The register and its queue

| # | What the code must do, and why | Fate |
|---|---|---|
| R42 | A draft may be dismissed by its drafter, by the person an agent drafted for, or by the owning function. An agent's draft also waits on that person | changed: §6.3. "The agent's principal" is its delegator, or a grant's accountable person |
| R43 | What an agent may propose is recorded at draft, not enforced there; drafting grants nothing, and the steps that follow are checked | changed: §6.3. Delegations and grants replace mandates. Whether an agent may draft a register entry at all is not in the spec, so P1 decides it; an agent never approves one (RR-2) |
| R44 | A reminder by anyone but the submitter is refused (RR-3); a step in the wrong state is refused (DC-2) before the people rules (RR-4); a direct submit has no `proposed_by`; a registrar error that isn't a rule is refused (RR-5), narrowed by R59 | kept |
| R45 | At approval, a scoped clash (RR-13) also counts `under` dependencies, but never `under` against `under`. RR-14 checks that an agreement exists, not that it's live | kept |
| R46 | The register's content store reads and writes text as UTF-8 with newlines untouched, and removes a stale partial file on failure. Register text must be served byte for byte | kept |
| R47 | An entry past its window whose successor is in force reads `superseded`; `expired` only when nothing live follows | kept |
| R48 | Every register entry belongs to exactly one series; a lone document is a series of one | kept |
| R49 | A missing copy on file reads `{sha256: "", matches: false, detail: "missing", source_id: null}` | kept (agrees with §3.2's null `source_id`) |
| R50 | Approving a procedure writes its own event kind, which the register's replay and the scoped clash check never read, so a procedure version can't break either | kept: packs and procedures are registered apart from documents (§4.1) |
| R52 | No backdating against the register's clock (RR-9) applies to procedure versions at draft, submit and approval. Backdating a procedure into past decisions is the threat RR-9 blocks for documents | kept |
| R53 | A procedure text that declares no registered kinds is refused; versions number in order, one procedure per decision type, with the window checked (RR-5, RR-7). Numbering is a procedure's stale check | changed: §4.2 and §5.3. The pack definition's schema and the structural check carry these rules |
| R54 | Decisions run the approved procedure text from the store, checked by fingerprint, never a file on disk | changed: §4.1. The text is the registered pack's procedure |
| R55 | (The lab's procedure admission report, self-attested and supplied with the change) | changed: §5.3. A pack is enabled by two people after the structural check; the lab's admission gate isn't part of the prototype |
| R56 | Register changes "waiting on me" is empty for an agent: an agent takes no register step (RR-2) | kept for register changes. Its other half, an agent's approvals inbox being empty too, is changed by §6.4: an agent under a grant sees the approvals it may take |
| R59 | At approval, an error that isn't a rule propagates and the change stays pending; draft and submit keep RR-5. The rules already passed at submit, so the error is environmental | kept |

## Identity, sessions and the front door

| # | What the code must do, and why | Fate |
|---|---|---|
| R18 | Whoever is accountable for an agent is resolved to a person at load, and an unknown id is refused | changed: §6.3. A grant's accountable person and a delegation's delegator are resolved through Identity; an unknown id is refused |
| R37 | A switch that opens extra routes is read strictly, and an unknown value refuses to start, so "False" can't leave a door open | changed: §3.2. The lab routes are gone. Test mode (`OWM_TEST_MODE`) is read the same strict way, and binds to loopback only |
| R39 | A failed write writes no effect, and every API route needs authentication; the lab's clock and reset routes needed none | changed: §3.2 and PL-11. Every route needs a token except `/healthz`; the operator surface needs the operator token |

## SLA (not in v1)

| # | What the code must do, and why | Fate |
|---|---|---|
| R9 | (SLA flag codes) | dropped: SLA |
| R17 | (The SLA basis digest of a ticket's events) | dropped: SLA |
| R30 | (The SLA asker counting as the requester) | dropped: SLA |
| R41 | (The clock for SLA cases without a decision time) | dropped: SLA |

## The lab's own build, tests and demo

| # | What it was | Fate |
|---|---|---|
| R1 | The lab's test packages and import layout | dropped: lab build |
| R3 | One registrar-messages test run by the lab's gate | dropped: lab gate |
| R5 | Where the lab's gate runs its linter | dropped: lab gate |
| R6 | The lab's routing-consistency test set | dropped: lab tests |
| R7 | The lab's gate re-running scripts over its own committed results | dropped: lab gate |
| R8 | A commit-hygiene scan on every commit | changed: the plan's `scripts/scan_staged.sh` (Task 1.1) does this for the prototype |
| R10 | Commit attribution and no amends | changed: the plan's Global Constraints set the prototype's commit rules |
| R11 | Copying the contract from a staged copy, not by git against another repo | dropped: lab tooling (the bundle carries the contracts, §11.4) |
| R15 | A scan for the demo org's name in code | changed: §3.3. The name scan covers `contract/`, `core/`, `service/` and `mcp/` from P4 |
| R27 | A refactor of the lab service's decision module | dropped: lab refactor |
| R38 | The dependency group the lab's gate type-checks with | dropped: lab gate |
| R51 | A refactor of the lab service's change model | dropped: lab refactor |
| R57 | How the lab's attack test submits its cases | dropped: lab tests (the gate's attack runner is the lab's) |
