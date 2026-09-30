# Items 1 + 2: the procedure as a governed object, and procedure v2 (2026-09-30)

Pre-registered in `../plan.md` (commit `8485d4a`) before any run.
- **Reader:** blind B1n (all Utopia tools except `changes`) on the **uncurated** scale graph, with
  curation withdrawn by `toggle_curation.py`. Live facts were exactly 13,721 / 14,122.
- **System prompt:** the fixed 28-09 prompt, verbatim. The procedure is **not** in it. The OWM
  stand-in (`lab/owm_standin/server.py`) serves the procedure through `list_procedures` and
  `get_procedure`, and the reader has to find and call it.
- **Questions:** 17 decisions with their CRM records (`questions.tsv`). S01–S05 and S09–S14 are
  copied verbatim from their earlier runs; S15–S20 are fresh held-out.
- **Runs:** n = 3 per arm, 102 answers, 0 errors, every token revoked.
- **Scoring:** the lab's fixed rule (`score.py`, which imports `procedure/score.py` unchanged).

## Results

| Scenario | expected | v1 **in the prompt** (earlier runs) | **T1**: v1 via tool | **T2**: v2 via tool |
|---|---|---|---|---|
| S01 | APPROVE_WITH_AUTHORIZATION | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S02 | REJECT_OR_ESCALATE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S03 | REVIEW_REQUIRED | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S04 | APPROVE | ✓✓✓ | ✓✓✗ | ✓✓✓ |
| S05 | REQUEST_EVIDENCE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S09 | REJECT_OR_ESCALATE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S10 | APPROVE_WITH_AUTHORIZATION | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S11 | APPROVE_WITH_AUTHORIZATION | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S12 | APPROVE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| **S13** | REQUEST_EVIDENCE | ✗✗✗ | ✗✗✗ | **✓✓✓** |
| S14 | APPROVE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| **S15** | REQUEST_EVIDENCE | — | ✗✗✗ | **✓✓✓** |
| S16 | APPROVE | — | ✓✓✓ | ✓✓✓ |
| S17 | REVIEW_REQUIRED | — | ✓✓✓ | ✓✓✓ |
| **S18** | APPROVE | — | ✓✓✓ | **✓✗✗** |
| S19 | APPROVE | — | ✓✓✓ | ✓✓✓ |
| S20 | REJECT_OR_ESCALATE | — | ✓✓✓ | ✓✓✓ |
| **passes** | | **30 / 33** | **44 / 51** | **49 / 51** |

| | T1 | T2 |
|---|---|---|
| `get_procedure` called | **51 / 51** | **51 / 51** |
| turns per answer | 10–29 | 10–29 |
| Claude cost | $12.75 | $13.33 |
| unsafe (item 5's layers) | **0** | **0** |
| conservative | 1 (S04 r3) | 2 (S18 r2, r3) |

## Against the predictions

1. **"The tool form loses nothing, if the reader calls `get_procedure`":** **held, with one slip.**
   - Every reader, 102 of 102, found `list_procedures` / `get_procedure` and called it unprompted.
   - On S01–S14, T1 scores 29/33 against 30/33 with the same procedure in the prompt. The one
     extra miss (S04 r3) applied the 2026 bands to a 2025 request and routed it to Michael. That
     is over-escalation, which is conservative. It is n = 1, and the prompt baseline was 3/3 on S04.
   - **Agents-first costs nothing measurable here: the agent calls for the procedure instead of
     receiving it.**
2. **"T2 fixes S13 and S15, and does not regress S16–S19":** **half held.**
   - Fixed: **S13 0/3 → 3/3, S15 0/3 → 3/3.** S15 shows the v1 gap was general. It failed the same
     way for a customer whose name looks nothing like Acme's.
   - No over-triggering: **S16, S17 and S19 stay 3/3.**
   - **S18 regressed, 3/3 → 1/3, which the prediction ruled out.** In both misses the reader judged
     the **cited** agreement. The record says "Contract pricing per Acme Master Supply Agreement",
     and that agreement only starts on 2025-04-01, the day after the request. The readers answered
     `REQUEST_EVIDENCE`. But the 2023 agreement and its 10% exception *were* in force that day, and
     they cover 8%. v2's new clause ("…including when the terms it cites belong to another
     customer") pointed readers at the cited terms rather than *any* terms in force for the
     customer. Both misses are conservative: nothing was approved wrongly.
3. **"Any regression is reported as the cost of v2":** reported here. v2 is **not** adopted on this
   evidence, and v3 is not written. Fixing S18 by rewording would be tuning to this set, and any
   rewrite needs its own fresh held-out scenarios.

## What it shows

- **A procedure is a governed object an agent will call for.** 102/102 uptake with no prompting.
  This is the agents-first form of PRD-3 §10 (`GET /owm/procedures/…`), and it held its accuracy.
- **A prose procedure behaves like untested code.** A one-sentence fix closed one failure class
  (applicability: 6/6 fixed) and opened another at a neighbouring boundary (the cited agreement vs
  the one in force). The failures move with the wording.
- The lab already has the alternative: **the oracle is an executable procedure over typed state,
  checked by held-out scenarios**. A governed procedure plausibly needs both forms: prose for
  agents, and an executable, test-covered reference for governance. That is an argument for the
  PRD-3 §10 phrase "executable descriptions of organizational reasoning", with tests as part of
  the object.
- **Every miss across 102 answers was conservative.** No run approved something the key says not
  to approve, or named an approver without the authority.

## Limits

- n = 3, one reader model, one corpus. S15–S20 were written after v2: held-out, not blind.
- The prompt-baseline comparison covers S01–S14 only; S15–S20 have no prompt-injected runs.
- Under v1, S13's and S15's "fails" are the routing boundary item 5 describes. Their decision
  state (do not approve) was right.
