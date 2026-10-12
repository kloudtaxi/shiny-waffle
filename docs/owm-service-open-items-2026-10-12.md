# B-06 OWM service: open items after the build (2026-10-12)

The service is built, reviewed and green. This note lists what is still open. The rulings made during the
build are in the spec's Appendix A (`docs/superpowers/specs/2026-10-10-owm-service-design.md`, R1–R60), and
the slice-1 result is in `docs/owm-service-slice1-2026-10-11.md`.

**Where it stands:**
- **Branch:** `worktree-b06-owm-service`, 52 commits on a69b4c9. Not merged or pushed.
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
| **Merge** | The branch is complete | See the finishing options |

## 2. For the garbanzo session

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

## 3. Spec wording nits (the last re-review)

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
