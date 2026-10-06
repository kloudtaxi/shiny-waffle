# Procedures governed (G-13): results, 2026-10-06

> **Status:** done. **Every prediction holds** (P1–P5). It is free: Jev replay only, with no
> reader, Utopia or live Jev spend. Pre-registered in `plan.md` (`036aada`). Its addendum
> (`8148f41`) changed P4's tamper before any run.

**The shape:** agents propose a procedure, the gate admits it, a person approves it, and the
register holds it. Each decision runs the version in force on its date, from the approved text,
and records which version made it.

## What was built

| Piece | What it does |
|---|---|
| `lab/owm_register/build_procedures.py` | **The registrar.** It refuses a version without a passing admission report for its exact text (normalised sha256), a version whose approver is the registrar, and any non-employee, so an agent can never approve. It is deterministic (`--check`) |
| `lab/owm_register/procedures.yaml` + `procedure-store/` | **The register**, with four versions (below), and the approved texts by sha256 |
| `lab/owm_kernel/governed.py` | **A governed decision.** It runs the version in force at the decision's date, from the store, with its deployment terms. It stamps `procedure: {id, version, sha256}` on the record, raises an incident when the file on disk differs, and refuses when no version is in force |
| `flow.loads(text, name)` | The spec loader, from text; `flow.load(path)` now calls it |
| `admit.py` | Reports carry the spec's `sha256`, and the replay loads every Jev recording under `runs/` |

| Procedure | v | Spec | In force | Registered by, approved by | Author |
|---|---|---|---|---|---|
| PROC-DISCOUNT | 1 | `discount.yaml` | 2025-01-01 → | Michael Torres, David Morgan | the lab |
| PROC-CREDIT | 1 | `credit_v3.yaml` | 2025-01-01 → | Priya Shah, Elena Novak | the lab |
| PROC-SLA | 1 | `sla.yaml` | 2025-01-01 → 2026-10-05 | Hannah Lindqvist, Marcus Adeyemi | the lab, from a blind subagent's rules |
| PROC-SLA | 2 | `sla_agent.yaml` | 2026-10-06 →, supersedes v1 | Hannah Lindqvist, Marcus Adeyemi | **an agent**: revision 1, after the gate's report |

All four were re-admitted with their hashes (`admission/`).

## Results (`run_governed.py`, `results.json`)

| # | Prediction | Result |
|---|---|---|
| P1 | The four versions register and the build is stable; four bad requests are refused | **Holds.** Refused: `credit_agent.yaml` (failed gate C), `sla_agent_v1` (failed gate C), approver = registrar, and "an agent approves" (not an employee) |
| P2 | Governed decisions equal the deployed specs' decisions, apart from the stamp, and all are stamped | **Holds:** 18/18 discount, 10/10 credit, 10/10 SLA |
| P3 | Clean SLA scenarios run v1; at 2026-10-07, v2 runs and equals `sla_agent.yaml` | **Holds:** all 10 ran v1. S36 at 2026-10-07 ran v2, which equals the agent spec's decision |
| P4 | An in-place edit of `credit_v3.yaml` (the reject-if-ineligible rule deleted) changes no governed decision; every record is flagged; ungoverned, the edit moves at least one decision | **Holds:** 10/10 unchanged and 10/10 flagged. Ungoverned, the tampered file **wrongly approves S29 and S30** |
| P5 | No procedure in force means a refusal | **Holds:** "no discount procedure is in force on 2024-06-01" |

## What it shows

1. **A procedure is now a governed object, like a policy.** A tampered procedure file is as
   harmless as a tampered policy. Without governance, one deleted line turned two rejections into
   approvals.
2. **"Which version made this decision?" now has an answer on every record:** id, version and the
   exact text's hash.
3. **An agent-authored procedure is in force (from 2026-10-06)** through the whole chain. An agent
   proposed it, the gate refused it, it was revised from the gate's report, the gate admitted it,
   and the owning function registered it and a second person approved it. No agent approved
   anything.
4. **A decision runs on the version in force on its own date**, so the 2026 tickets still run v1.
   Whether a decision should use the version in force at its event date or at the time it is
   decided is a policy question for BlueLeaf. The lab uses the scenario's date.

## Checks

The register's K3 and K4 pass by replay after the loader change. pytest (40), ruff and mypy pass.
