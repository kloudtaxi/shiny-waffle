# B-06 OWM service: open items after the build (2026-10-12)

The service is built, reviewed and green. This note lists what is still open. The rulings made during the
build are in the spec's Appendix A (`docs/superpowers/specs/2026-10-10-owm-service-design.md`, R1–R65), and
the slice-1 result is in `docs/owm-service-slice1-2026-10-11.md`.

## Update: contract v1.3 and the first live run (later on 2026-10-12)

- **Merged and pushed:** B-06 is on `main` at f59d710. G-45 and G-46 have log entries, and the two gap candidates in
  §1 are now Ledger gaps G-47 and G-48.
- **The garbanzo message (§2)** was delivered straight to the garbanzo session, which had been brought local.
  web-next already had most of it (B-08, B-09, U-24 to U-26). Its review is garbanzo
  `owm/docs/owm-service-handover-2026-10-12.md`.
- **The user ruled on R26, R34 and R58,** and garbanzo issued them as contract v1.3 (589e0c7; §6.2 wording at 7732488).
  The service was rebuilt to v1.3. The spec's rulings R61 to R64 record the details:
  - **R26:** a dropped credit concurrence's holder confirms too, with one ratchet condition per confirmer (R61, R62, R63);
  - **R34:** a dry run answers `{dry_run: true, would_clear, reasons}` (R64);
  - **R58:** adopted as built. It binds the actor, not the token, and a fresh sign-in can still report;
  - **`href`:** the OWM resource path, as built.
- **The §3 nits are fixed:** R26 and R58 wording, and the status block. The R53 credit in §7.3 stands.
- **Contract v1.4** (garbanzo 6b6619e, the user's D-24): the five lists are pages, `{items, next_cursor}`, each served
  whole with `next_cursor` null (R65).
- **D-23:** BlueLeaf has its own knowledge base, loaded by garbanzo from `dataset/evidence` at 571baac, whose tree is
  identical to today's. The experiment's base is untouched.
- **Verified live by web-next:** B-14 (Try to act, R34) and an R26 journey, against 2af58b6. Both passed.
- **First live run:** web-next ran S22 end to end against the service at f59d710 and the user's Utopia. Sarah resolved
  c1, Michael approved, and the decision reached `ready`. Credit and SLA haven't been run live yet.

## Replay coverage at the demo clock (probe, 2026-10-12, $0)

Every request and ticket in the demo corpus was asked once, in replay mode, on a throwaway copy of the state.

| Kind | Decides | 503 `cannot_decide` |
|---|---|---|
| Discount | **26 of 26** (DR-7001 to DR-7024, DR-8104, DR-9001) | none |
| Credit | **11 of 11** since `runs/2026-10-12-owm-credit-recordings/` (1 of 11 before it) | none |
| SLA | **10 of 10** | none |

- **Edits mostly replay.**
  - DR-9001 decides at 8%, 9%, 10%, 12%, 15%, 20% and 25%, and with its date or status changed.
  - Copies under new ids (DR-9002, DR-9003 at 12%, CR-9299) decide.
  - CR-9201 decides with its limit at $450,000 or $650,000, or with its customer changed.
  - So the questions the kernel sends the model don't depend on the request's figures, date or status. The customer
    is different: changing it changes the questions.
- **What misses:**
  - DR-9001 moved to another customer (CRM-3001);
  - a request the CRM doesn't hold (DR-9999 with submitted figures);
  - 10 of the 11 credit requests, until they were recorded with one live call (the run linked above);
  - after approving a register entry that decisions read (§5 below).
- **For a demo:**
  - discount and SLA are safe on the demo data, Sarah's edit to 8% included;
  - credit is safe too, now that the other ten are recorded. One live call covered them, because the kernel's only
    credit question reads the justification text, and all ten say "Order growth";
  - a credit request with a new justification text would still need a recording.

## After the build (as first written)

**Where it stood:**
- **Branch:** `worktree-b06-owm-service`, 52 commits on a69b4c9. Since merged to `main` (f59d710) and pushed.
- **Tests:** 853 pass (`uv run --group owm-service pytest`). ruff and mypy (strict) are clean, and
  `scripts/owm-gate.sh` is GREEN with `runs/` byte-identical.
- **Acceptance:** §12.2 passes:
  - 42/42 scenarios reproduce the kernel;
  - 14/14 input conflicts match the oracle;
  - the must-fixes and the `spent` cases all pass;
  - the register attack set gives 24/24 identical admitted/refused results through the two-step queue.
- **Docker image:** 260 MB. It holds only the service and the three lab packages it imports, with no
  truth, no answer key and no key. Lab routes are off by default. The container smoke test gives
  `S22: spent`.
- **Cost:** $0. Every Jev answer was replayed.

## 1. For you to decide

| Item | What we found | Suggested next step |
|---|---|---|
| **Gap candidate: RR-14 doesn't check a parent is live** | The registrar's RR-14 checks that an `under` agreement exists and matches, not that it is in force. A child submitted under an already-revoked agreement passes. The queue's R45 only catches a revoke approved after submission. The registrar is frozen, so the service can't fix it without changing a rule | Log it on the Ledger as a new gap (registrar rule change, with an attack-set re-run) |
| **Gap candidate: a second SLA payment** | After S36's $4,200 credit is issued, a new decision on SR-39385 offers another $2,100, because the cap counts that ticket's own credit. Only the service's `spent` guard stops it. `test_spent.py` pins the current behaviour, so a kernel fix will show up there | Log it on the Ledger as a kernel/truth gap |
| **Ledger updates for G-45 and G-46** | The plan's Task 21 appends "service implementation landed" to their logs, using a pinned `ArtifactData` update that only appends | Do it when the branch is merged, so the log can cite a commit on `main` |
| **Merge** | The branch is complete | Done: merged and pushed (f59d710) |
| **Record the other 10 credit requests** | Only CR-9201 replayed at the demo clock | Done: one live call, cap 150 (`runs/2026-10-12-owm-credit-recordings/`) |

## 2. For the garbanzo session (done: delivered and answered, see the update above)

The slice-1 note (`docs/owm-service-slice1-2026-10-11.md`) carries the paste-ready message. Add these points:
- **Contract smells to settle:**
  - R26: the band holder alone can waive a dropped credit concurrence. This weakens separation of duties.
  - R34: a dry run that would clear returns `{cleared: false, reasons: []}`. The contract has no "would clear" shape.
  - R35/R58: CLR ids are sequential. Only the session that redeemed a clearance may report on it.
- **Contract example vs the kernel:** `v2Ratchet` shows `authority.required_role`/`approver` as null for an
  authorized requester. The kernel and the truth (S14) name the requester's own role and the requester.
- **Shapes web-next needs:**
  - the procedure-change request shape (the TS has no procedure fields on `RegisterChange`); it is
    documented in `app_register.py`;
  - procedure reads add `id` beside `proc_id`, plus the statuses `scheduled` and `expired`;
  - how dry runs and refused redemptions appear in history;
  - the work-item id and href formats.
- **web-next work:**
  - a session bridge to `/lab/sessions`;
  - the `OWM_API_URL` route;
  - a Northstar demo org;
  - *Effective from* defaulting to the register's clock (the demo clock starts 2026-09-23);
  - a plain message for the 503 `cannot_decide`.

## 3. Spec wording nits (the last re-review; fixed with v1.3 except §7.3)

- **§6.5 and Appendix A R26** say "flagged to garbanzo". That becomes true once you send section 2.
- **§6.7 and R58** say "the session that redeemed". The code binds the actor, so two sessions of one person count
  as the same.
- **§7.3** credits the ADM `type` check to R53. It came from the Task 18 review.
- **The status block** still says "No code is written…".

## 4. Open minors, worth doing next (none blocks merge)

Highest first:
1. **M-5: subject ids aren't normalised.** `"DR-9001 "` with a trailing space is a new subject with no floor.
   Strip the id, and check it against the type's pattern.
2. **M-6: the mandate's effective window is never checked at clearance.** The Deal Desk Agent would still clear after
   2026-12-31.
3. **M-3: two threads can rewrite the kernel register's store files at once,** without atomicity.
4. **M-4: `python -m owm_service` binds 0.0.0.0 with the lab routes on.** Locally, anyone on the LAN can sign in as anyone.
   Bind to 127.0.0.1 by default.
5. **M-8: the procedures read presents a self-attested admission report as passed gates.** R55 records this as a known limit.
6. **M-9: `Org.policy_terms` returns a reference into the cached register state.**
7. **R60 doesn't purge old writes.** Old state directories keep any writes to tables that are now read-only.
   Use a fresh state directory or `/lab/reset` for demos.
8. **The replay-file count depends on where the image is built.** A build from the main checkout, which holds a 32 MB untracked file,
   ships 14 files rather than 13.
9. **Test-hygiene items from the per-task reviews.** None is a correctness issue:
   - the clearance race isn't forced to interleave;
   - S23's CRM date equals the default clock date;
   - `ApprovalRequirement.role` isn't checked against the truth;
   - `judged_columns()` misses indirect judgment inputs, though the end-to-end `spent` tests cover them;
   - the gate script's diagnostics (tee the governed run's output; `git clean -fd -- runs/`; count `^P[1-5] HOLDS`).

## 5. Known limits (bounded, documented in the README)

- **Registering a new entry can force a live call.** Approving an entry of a kind decisions read can change
  what the kernel asks Jev, so the next such decision misses the replay and returns 503 in replay mode.
  Live mode needs a spend cap agreed with you.
- **Self-sourced edits:** `self_sourced_basis` only sees edits made through the service.
- **Live calls:** a failed live call doesn't count toward the cap, and a missing key surfaces as a 503 `cannot_decide`.
- **Sign-in:** demo sign-in only. A real deployment replaces `sessions.py` and sets `OWM_LAB_ROUTES=0`.
- **Request ids:** a new request id is a new subject (DR-9002), so the ratchet can't link it.
