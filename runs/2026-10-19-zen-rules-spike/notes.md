# ZEN rules spike: notes

**Status: done, 2026-10-19.** All five checks passed. $0: no LLM calls; live Jev 0 in both gate
arms. Results: `results.md`.

## Amendment to the plan (the test, not the system)

**P4's first pass** used the first credit request's requestor (`sarah.chen@…`). She holds no credit
band, so her limit is 0 whatever separation of duties says. Switching it off in the table therefore
couldn't change her result, and the check showed nothing either way. This was the spike's own
choice of example: the plan didn't name a requestor.

**The second pass** uses an Accounts Receivable Specialist (`robert.hernandez@…`), who holds the
first band, and compares against the kernel's own `authority_from_terms` for the same call.

The first pass's full output is kept as `outputs/results-first-pass.json`. P1, P2 and P3 were the
same in both passes.

## Run log

1. `uv run --with zen-engine==2.1.3 python runs/2026-10-19-zen-rules-spike/spike.py all`, giving
   `outputs/results-first-pass.json`.
2. P4's requestor changed (above), then the same command again, giving `outputs/results.json`, the
   gate reports and `traces.jsonl`.

Before and after both runs, the 24 protected files under `lab/owm_kernel/`, `lab/owm_register/` and
`lab/spec_admission/` had the same sha256 (`guards.unchanged: true`).
