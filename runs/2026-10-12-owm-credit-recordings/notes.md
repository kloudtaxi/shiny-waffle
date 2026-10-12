# Recording the credit requests the OWM service can't replay (2026-10-12)

> **Status: pre-registered, before any live call.** Results are appended below this plan. The plan
> itself isn't edited after this commit.

## Why

The OWM service (`lab/owm_service/`, contract v1.3, `main` at 940a21a) answers every Jev question
from recordings under `runs/`. A request it has never seen gets a 503, `cannot_decide`. A probe at
the demo clock on 2026-10-12 found:
- discount: 26 of 26 decide;
- SLA: 10 of 10 decide;
- credit: 1 of 11 decides (CR-9201).

The probe is in `docs/owm-service-open-items-2026-10-12.md` ("Replay coverage at the demo clock").
The other ten are the background credit history, CR-7001 to CR-7010. A live demo that opens one of
them stalls.

The user approved one capped live run to record them, so they replay at $0 from then on.

## What runs

- **Subjects:** CR-7001 to CR-7010, from `dataset/evidence/structured/credit_requests.csv` at
  940a21a.
- **How:**
  - one fresh service state, under the session's scratch directory, not in the repo;
  - the default demo clock (2026-09-23 09:00 CT);
  - `OWM_JEV=live` and `OWM_JEV_CAP=150`.
- **The ask:** each subject is asked once, as `POST /decisions` would ask it (`Decisions.ask`),
  with no `submitted` figures, by Sarah Chen (EMP-101). Who asks shouldn't change what Jev is
  asked; the check below tests that.
- **Model:** `jev-1.13.0`, pinned in `lab/owm_service/_lab.py`.
- **Recording:**
  - the engine appends each live exchange to the state's `jev-calls.jsonl`;
  - that file is copied here as `owm-credit-jev-calls.jsonl`, where the replay finds it
    (`*jev-calls*.jsonl`).
- **Script:** `record.py`, committed with the results.

## Guards

- **The cap is enforced by the engine** (`ReplayEngine`): a 151st live call raises, and the
  decision gets a 503.
- **Stop on the first error:** an error other than a recorded answer stops the run.
- **The key:** the engine reads it from `TYPESAFE_API_KEY_FILE`, set for this one command. It's
  never printed, logged, recorded or committed.
- **What stays untouched:** nothing under `dataset/`, `truth/` or other `runs/` folders is written.
  The committed results stay byte-identical, and the gate checks that.

## Expected cost

- **Calls:** at most 150. Replaying CR-9201 takes 1 Jev call, and DR-9001 takes 12.
- **Dollars:** well under $1. G-23 measured the OWM path at ≤ $0.00026 per decision.
- The cap bounds calls, not dollars. The actual spend goes below.

## Success criteria

1. In replay mode, on a fresh state, all 11 credit requests decide (no 503), asked by Sarah Chen
   and again by Priya Shah (EMP-401).
2. The full service suite and `scripts/owm-gate.sh` stay green, with `runs/` byte-identical apart
   from this folder.

The outcomes are recorded, not graded. These are background requests with no scenario or answer
key, and nothing here is scored.
