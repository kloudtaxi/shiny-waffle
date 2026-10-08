# G-23: cost per decision, by model tier and context (pre-registration, 2026-10-08)

**The question (an ROI item).** What does a decision cost end to end, and what does the OWM buy?
Two levers:
1. **Model tier:** Opus 5.5 against Haiku 4.5.
2. **Context:** the whole corpus, against the **OWM-served decision context**. This is the
   reading list's "small, decision-scoped context" (`docs/reading-list-notes-2026-10-07.md`, idea
   3) and the shape of the MCP server's `owm` arm.

The reference point is the **OWM path**: no agent decides; the kernel with Jev decides from the
same register.

## Design

The reader re-baseline's harness is unchanged (`runs/2026-10-06-baseline/run_baseline.py`):
- the fixed system prompt plus the adopted procedure (G-35);
- the question, with the request "as recorded in Northstar CRM/ERP" (G-36's overlay), or "as
  submitted" for S35;
- the 28 decision scenarios (discount 18, credit S26–S35), 3 runs each, 84 answers per arm;
- the same scoring (held / routed / unsafe) and conditions counting.

| Arm | Model | Context | Status |
|---|---|---|---|
| **O-full** | Opus 5.5 | every document and record of the overlaid corpus (about 73,000 characters) | **Exists**: the re-baseline (`5a1c1d9`): 77 held, 6 routed, 1 unsafe; $25.53, so $0.304 per answer; median 21.1 s; median 33,424 input tokens. Re-scored by `run_cost.py` with the same result |
| **O-slice** | Opus 5.5 | the OWM-served slice (about 12,600 characters on average) | New |
| **H-full** | Haiku 4.5 (`claude-haiku-4-5-20251001`) | the whole corpus | New |
| **H-slice** | Haiku 4.5 | the OWM-served slice | New |
| **OWM path** | none | the kernel and Jev on the same register (`governed.decide`) | Computed: decisions by replay, with Jev calls counted and priced at I2's rate |

**The slice** (`served_slice.py`, committed with this plan) is assembled from the request alone,
never from truth or the answer key:
- the **served register** for the decision type: coverage, every kind even when empty, approved
  terms and approved texts;
- documents the register **names** (the Approval Authority Matrix, for discount);
- **system-of-record rows** found through the request's own ids:
  - the request row;
  - the customer's CRM and ERP rows (joined by DUNS);
  - the employee table;
  - the product row (discount), or the customer's ERP credit and invoice rows (credit).

It leaves out the emails, the account strategy, other customers' records and other decision
types' documents.

**Measured per arm:**
- held, routed and unsafe;
- cost per answer (`total_cost_usd`);
- median latency (`duration_ms`);
- input tokens;
- answers that cite an email message (the re-baseline's residual). This is measured by
  `run_cost.py`'s pattern ("Sarah's email", "the email", "email to/from", or the file name), not
  the employee table's email column. On O-full the pattern finds **33**; the re-baseline's reads
  found 32.

## Predictions (fixed before any new answer)

| # | Prediction | Why |
|---|---|---|
| P1 | **O-slice unsafe ≤ 1 of 84** (no worse than O-full) | The slice holds everything the decision needs, and the register states absences explicitly |
| P2 | **O-slice cost ≤ 40% of O-full per answer** (≤ $0.12) | About a sixth of the context |
| P3 | **H-full unsafe > 1 of 84** (worse than Opus on the same inputs) | Authority, routing and conflicts are where cheaper models slip |
| P4 | **H-slice unsafe ≤ H-full unsafe** | Less to read and nothing irrelevant to be misled by |
| P5 | **H-slice cost ≤ 10% of O-full per answer** (≤ $0.03) | A cheaper tier on a sixth of the context |
| P6 | **Slice arms are faster:** median latency ≤ 60% of the same model's full-corpus arm | Fewer input tokens |
| P7 | **The OWM path: 28 of 28 held, under $0.001 per decision** | Known from G-13's P2 (governed equals the deployed specs) and I2's Jev rate |
| P8 | **The email residual drops to 0** in both slice arms (33 of 84 in O-full, by the pattern) | Emails aren't in the slice |

**The commercial claim tested:** "with OWM-served context, a cheap model is as safe as Opus on
everything, at a tenth of the cost". It holds if **H-slice unsafe ≤ 1 and P5 holds**. If not, the
claim becomes "the kernel decides; agents gather and explain".

## Cost and guard

- **New answers:** 252. Expected about $8 (O-slice) + $6 (H-full) + $2 (H-slice), about **$16**.
- **Guard:** each arm stops if its first 6 calls average over $0.20 (O-slice), $0.15 (H-full) or
  $0.06 (H-slice).
- **Jev:** replay only. Utopia and OpenAI: none.

## Limits, stated before the run

- **The slice is the lab's assembly rule.** A product's assembly could include more or less.
- **One synthetic company.** The scenarios and the overlay are those of the re-baseline.
- **Not tested here:** an agent that *retrieves* with a cheap model (the e2e run showed retrieval
  sufficient with Opus readers). The runtime, Agno or another, doesn't change model costs.
