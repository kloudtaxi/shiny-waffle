# Arms A · B1 · B2: first read

Same graph for all three: both KBs as snapshotted in `snapshot/` (268 and 265 live facts), with
no Review-queue action. Same verbatim questions (`questions.tsv`).

| Arm | Reader | Tools | Cost | Turns |
|---|---|---|---|---|
| **A** | Utopia's in-app chat (gpt-4o-mini per notes, unverified) | all, through Utopia's own loop | not measured | 2–6 steps each |
| **B1** | Opus 5.5, blind, headless | all 11 MCP tools | $1.45 | 85 in total (~17 s per question) |
| **B2** | Opus 5.5, blind, headless | 9 MCP tools; text tools **hidden** | $3.19 | 248 in total (~30 s per question) |

Probes and one discarded run add $0.43. See `arm-b/B2-discarded/README.txt` for why that run
was discarded.

**These grades are provisional**, one reader's first pass against the expected outcome. They
are not the step 8 rubric scoring. ✓ means correct, ◐ partly right, ✗ wrong or no answer.

| Id | Expected | A | B1 | B2 |
|---|---|---|---|---|
| S01 | APPROVE_WITH_AUTHORIZATION, Michael Torres | ✗ cannot determine | ✓ exact: eligibility ≠ authority, 2026 policy, VP Sales = Michael, DR-8104 explained | ◐ right "no" and right reasoning, but the VP band isn't in the graph, so the approver is only "obvious", not established |
| S02 | REJECT_OR_ESCALATE | ✗ | ✓ exceeds the 15% cap; escalation path; notes DR-9001 was logged at 15% | ✓ exceeds the cap; can't say who could escalate |
| S03 | REVIEW_REQUIRED (don't transfer the NS-500 exception) | ✗ | ◐ doesn't transfer the exception ✓, but frames the outcome as "needs VP sign-off" | ◐ same framing, no approver |
| S04 | APPROVE (2025 policy) | ✗ | ✓ plus the DR-8104 precedent | ✓ with the caveat that Sarah's role is undated |
| S05 | REQUEST_EVIDENCE (contract missing) | ✗ doesn't say what's missing | ✓ asks for the MSA and exception; treats "I believe 15%" as unconfirmed; still names Michael | ◐ declines to decide ✓, but asks for the **authority limits**, not the contract |
| S06a | 15% (EXC-…-15) | ✗ no facts | ✓ | ✓ |
| S06b | 10% (EXC-…-10) | ✗ **"100%"** | ✓ | ✓ |
| S06c | none | ✓ (only because nothing is dated then) | ✓ | ✓ |
| S07 | EXC-ACME-NS500-15 under MSA-ACME-2025, not hearsay | ✓ | ✓ contract + schedule; account plan used as background only | ✓ same; account plan quoted as "why granted", not as the basis |
| S08 | CRM-2048 = C-1001 = ACME-MFG-2025; Acme Industrial is different | ◐ | ✓ matched on shared DUNS, address and ID cross-references | ◐ Acme Industrial different ✓; can't link the IDs, which aren't in the graph |
| **✓ / ◐ / ✗** | | 2 / 1 / 7 | 9 / 1 / 0 | 6 / 4 / 0 |

## What this says about the boundary

1. **The reader is the largest variable.** On the same graph, A gets 2 of 10 right and B1
   gets 9. Arm A measured Utopia's reference chat loop, not the foundation. Utopia's own
   record says the same: the app surface is MCP (ADR 0046).

2. **With text access, a strong reader did the OWM's work at question time on this corpus.**
   B1 composed role + reporting line + policy band into the required approver, kept
   eligibility separate from authority, selected the policy and exception by date, refused
   hearsay as a basis, and resolved identity on shared DUNS. Those are the five "OWM
   questions" in `owm/owm-spec.md`. So on 17 artifacts, **Utopia as retrieval plus a capable
   agent reproduces the canonical decision** (doc 03 §21) nearly field for field. The OWM's
   case therefore can't rest on "the foundation + agent can't compose it". It has to rest on
   what B1 does **not** give you:
   - **Persistence.** B1's decision exists only in a transcript. Nothing is recorded, dated
     or reviewable, and the next question recomposes it from scratch. That's the gap ADR
     0047 names: "the answer evaporates when the tab closes — it never becomes a fact, so it
     has no interval, no proof, and no place in a review queue". Doc 03 §23's "evergreen,
     rather than reconstructing it from scratch for every question" is exactly this.
   - **Consistency and audit.** Ten runs gave ten differently shaped answers. There's no
     decision object, no fixed evidence list, and no guarantee that tomorrow's run reaches the
     same verdict.
   - **Scale.** All 17 artifacts fit in a few searches. At `--scale large` or real-corpus
     size, retrieval stops surfacing every piece, and composing at question time stops being
     free. That's the next experiment.
   - **Cost and latency.** Even here, B2 took 3× the turns and 2× the cost of B1.

3. **B2 (graph only) shows what Utopia modelled, and it's less than it looks.** B2 reached
   6 ✓ largely because **graph tools return provenance quotes**: `changes` and `entity_facts`
   carry each fact's source sentence and filename. B2 quoted the MSA clause and the policy
   text verbatim. So Utopia's "graph" is really *open-graph edges plus their quotes*.
   What B2 still couldn't get, even with quotes:
   - **The VP Sales band (> 10% ≤ 20%).** It's missing entirely, so no approver can be
     established (S01, S03). The authority matrix had `unknown_ref` and `object_undeclared`
     drops.
   - **The source-system ids.** `CRM-2048` and `ACME-MFG-2025` aren't entities or names, so S08
     can't be linked.
   - **Percentages as values.** "The base doesn't store the actual discount figures" (B2
     S06c). They're recoverable only by reading quotes.
   - **Dated roles.** "The employee record for Sarah has no dates, so I'm assuming…" (B2 S04).

   **The B1 − B2 gap is the OWM/extraction worklist:** authority bands as structured,
   dated facts; source ids as identity keys; percentages as typed values; validity on roles
   and reporting lines.

4. **A strong reader silently repairs foundation errors.** Utopia's MCP returns
   `Michael Torres —reports to→ Sarah Chen` and `David Morgan —reports to→ Michael Torres`
   (from `organization_chart.md`; every reporting edge is inverted). B2 read those edges and
   wrote "Sarah is an Enterprise Account Executive who reports to Michael Torres", fixing
   the direction from title priors (a VP doesn't report to an AE). **Right answer, wrong
   data, and nothing in the answer shows it.** In an organization where titles don't give
   the hierarchy away (a matrix org, an interim role, a manager with a junior title), the
   same repair gives the wrong approver just as confidently. **Candidate OWM capability:
   structural constraints on organizational relations** (single manager, acyclic
   `reports_to`, role rank consistent with reporting direction) that *flag* a foundation
   error instead of letting the reader's priors hide it.

5. **"What needs human confirmation" (doc 01) has a concrete answer here.** Utopia's
   governance agent sent 5 SKU trivia items to humans and auto-applied the identity decisions
   that change answers (Acme CRM↔ERP kept apart in the variant KB, NS-CLOUD ≠ NS-Cloud
   Operations Suite), deciding from names, not shared identifiers. B1 got S08 right by using
   exactly the identifiers the adjudicator ignored.

## Suggested next runs

- **Correction arm:** apply the review corrections and the missing identity merges, rerun
  B1 and B2, and measure the delta. That says what the human nod is worth.
- **Scale arm:** `northstar build --scale large` into fresh KBs, then B1 and B2 again. Does
  B1's question-time composition survive 200 customers and 1,000 requests of noise?
- **Adversarial org arm:** a truth variant where the approver's title doesn't reveal the
  hierarchy (e.g. the VP band held by a "Director, Strategic Deals"). Does B2's silent repair
  turn into a confident wrong answer?
- **Repeat runs:** 3× B1 per question, to measure how consistent the verdicts are (point 2).
