# Procedures governed (G-13): pre-registration, 2026-10-06

The user chose G-13 from the board on 2026-10-06: "an admitted procedure goes into the register
(who wrote it, who approved it, which version), and every decision record is stamped with the
procedure version it ran". Free: Jev replay only. This file is committed before the code.

**Why now:** the admission gate (G-07) decides whether a procedure *may* be used. Nothing yet
records which procedure *is* in force, who approved it, or which version made a decision. A
procedure file can also be edited in place, just as a policy could before the register (G-01).

## What gets built

1. **A procedure register**, `lab/owm_register/procedures.yaml`. It is company-wide (procedures
   don't vary by corpus), and its approved texts are content-addressed in
   `lab/owm_register/procedure-store/<sha256>.yaml`. `fingerprint` is the kernel's normalised
   sha256. It is built deterministically by `lab/owm_register/build_procedures.py` (`--check`).

   Each entry holds:
   - `proc_id`, `decision_type`, `version`, `file`, `sha256`, `effective_from` and
     `effective_to`;
   - `relations` (`supersedes`);
   - `deployment`: the `registered_kinds` mapping and the mismatch mode it is admitted in;
   - `author`: transcribed by the lab, or an agent;
   - `admission`: the gate's report, its verdict, and the sha256 it was run on;
   - `registered_by`, `approved_by`, and dates.

| Procedure | Version | Spec | In force | Registered by, approved by |
|---|---|---|---|---|
| PROC-DISCOUNT | 1 | `discount.yaml` | 2025-01-01 → | Michael Torres (VP Sales), David Morgan (CRO) |
| PROC-CREDIT | 1 | `credit_v3.yaml` | 2025-01-01 → | Priya Shah, Elena Novak (Finance) |
| PROC-SLA | 1 | `sla.yaml` | 2025-01-01 → 2026-10-05 | Hannah Lindqvist, Marcus Adeyemi (Support) |
| PROC-SLA | 2 | `sla_agent.yaml` (revision 1, proposed by an agent) | 2026-10-06 →, supersedes v1 | Hannah Lindqvist, Marcus Adeyemi |

2. **The registrar refuses** a version when:
   - no admission report exists for that exact sha256, or its verdict isn't admitted;
   - the approver is the registrar;
   - the registrar or the approver isn't an employee in the HR export (an agent can propose a
     registration but never approve one; G-01).

   The admission report gains the spec's `sha256` (a one-line change to `admit.py`). The four
   versions above are re-gated so their reports carry it.

3. **A governed decision**, `lab/owm_kernel/governed.py`:
   `decide(decision_type, ev, inputs, at, register, procedures)`.
   - It picks the version in force at `at`, which is the decision's `as_of` or `decided_at`.
   - It runs the version's **approved text from the store**, not the file on disk, with its
     deployment terms.
   - It stamps the record with `procedure: {id, version, sha256}`.
   - A file on disk that differs from its registered version raises an incident flag; the
     approved version is what runs.
   - With no version in force at `at`, it refuses and decides nothing.

## Predictions

| # | Prediction |
|---|---|
| P1 | The four versions register, and the build is stable (`--check`). The registrar refuses all four bad requests: `credit_agent.yaml` (not admitted), `sla_agent_v1.yaml` (not admitted), approver = registrar, and an agent as approver |
| P2 | On every clean scenario of every type (18 discount, 10 credit, 10 SLA), the governed decision equals the deployed spec's decision in every field but the new stamp, and every record is stamped |
| P3 | All ten clean SLA scenarios are dated before 2026-10-06, so all are decided by PROC-SLA v1. At `at` = 2026-10-07, version 2 is selected, and S36's decision is stamped v2 and equals `sla_agent.yaml`'s deployed decision |
| P4 | **An in-place edit** of a registered procedure file (`credit_v3.yaml`'s separation-of-duties rule removed, in a temporary copy) **changes no decision**. Every credit record carries the incident flag, and the approved text is what ran |
| P5 | A decision with no procedure in force (discount at 2024-06-01) is refused with a plain error, and nothing runs |

## Cost

Free: Jev replay. No reader, Utopia or live Jev spend.
