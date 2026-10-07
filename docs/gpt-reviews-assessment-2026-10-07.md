# Assessment: GPT's six reviews of shiny-waffle (2026-09-28 to 2026-10-07)

**This is** Claude's read of the six reviews the user shared on 2026-10-07, checked against the
lab's record. The reviews are external opinion: useful, but data, not direction.

## The short version

- **The reviews are good, mostly accurate, and right on the big calls.** They read the evidence
  fairly, and they keep the thesis honest. "Don't claim RAG can't reason. Claim OWM makes
  organizational understanding persistent, governed and decision-capable." Most of the experiments
  they recommended were run, and those results backed the recommendations.
- **Their weak spots are architectural churn and a few stale facts.** They also repeat claims
  about OWM's *benefits* (persistence, economics) that the lab hasn't measured.
- **Two of their ideas aren't on our board yet and should be:** authority without title priors,
  and "as known at" time. **Their top recommendation for what's next is right:** attack the
  register itself.

## Where the reviews are right

| Review | Call | What happened in the lab |
|---|---|---|
| 1–3 (Sep 28–29) | Don't overclaim. A capable agent *can* reconstruct organizational reasoning at query time; the OWM's case is persistence, governance and typed semantics | The B1 arm held 15/15 across curated and uncurated graphs, as they noted. Every later framing of ours, including "Retrieval isn't the bottleneck. Decisions are.", follows this line |
| 1 | The inverted `reports_to` was "fixed" silently by the agent's priors. Make organizational constraints flag it instead | Tested on 2026-09-30: **13/13** inverted lines flagged, **0/49** false flags (`03-constraints`) |
| 1, 2 | Identity ≠ canonical name: source-system ids are identity claims | Kept as lab invariant (`CUST-*` never in sources); identity guard result (0 wrong merges in 41,600 pairs) |
| 3 | Applicability and decision inputs are first-class: S05 needed the *request* to know which evidence was missing | The procedure-plus-request arm (15/15), and since then decision inputs as spec inputs |
| 4 (Oct 5) | Specs as data plus agent authorship: "governed, executable organizational knowledge" | Then built: the admission gate (G-07), an agent-written SLA procedure admitted after one revision (G-12), and procedures governed and stamped on decisions (G-13) |
| 4 | Every residual unsafe v2 decision was an in-place edit, so a trusted register is needed | The register (G-01): 0/14 on sets C and D, then 0/47 across all six rounds |
| 5 (Oct 6) | `use_registered` (v3u) is the strongest semantics: the organization's truth isn't the file's current contents | Decided by the user on 2026-10-05; the default since |
| 5 | Absence must be explicit: "no guarantee returned" ≠ "the organization has none" | G-31 (coverage plus explicit "none"); E3 held 3/3 in a check |
| 6 (Oct 7) | G-36 matters more than G-35: separating *model* failure from *experimental-input* failure makes the evidence more credible | Agreed. The re-baseline (83/84 safe) is now the number to cite |
| 5, 6 | Next frontier: **attack the register itself** (unauthorized registration, wrong approver, false supersession, revocation, semantic tampering, races, scope) | Already listed as a next test in the CxO doc; their attack table is a better starting list than ours |

Their best one-liners are worth keeping:
- "The knowledge foundation remembers what the organization has said. OWM remembers how the
  organization works."
- "Retrieval was not the limiting factor. The failures appeared when retrieved information had to
  become governed organizational state and then an executable decision."
- "The problem isn't getting AI to find the answer. It's establishing what the organization
  recognizes as true, applicable, authorized and safe to act on."

## Where they're stale or slightly off

1. **Review 5 says the register is "credit-shaped" (G-30 open).** It was generalized to discount
   and SLA on **2026-10-05** (`45a4c71`, `3625d99`), and set F then tested all three types. The
   review read an older state.
2. **Reviews 2–3 treat constraints and decision memory as future work.** Both were tested on
   2026-09-30 (`03-constraints`, `04-decision-memory`):
   - the typed decision record was retrievable;
   - a decision stored as a document became undated "facts" and was cited as evidence;
   - stale reuse was 0/9.

   Decision memory *at scale* (G-19) is still open.
3. **Review 6's G-35 summary stops at the 26/26 fresh-scenario result.** After the G-36 fix, the
   re-baseline found **3 of 8 holds marked `blocking: false`** although the text said to wait.
   Holds reach the record, but the blocking flag isn't yet reliable. A one-line rule is pending.
4. **Review 3's "facts + procedure beat the stronger reader on S03"** was a point-in-time result.
   With the procedure and the request, the stronger reader also reached 15/15.

## What the reviews repeat but the lab hasn't measured

These shouldn't go into decks yet:

- **"OWM means agents don't rediscover the organization every time"** (reviews 1–3), and Review
  3's "economically and operationally necessary as the enterprise gets larger".
  - **Unmeasured:** cost per decision, latency and run-to-run consistency, with and without OWM
    context, at scale.
  - **What we do have:** engines are deterministic while readers vary, and judging costs a
    fraction of a cent while the agent's search dominates.
  - **The experiment that would settle it:** the cheap-agent pipeline (G-23) plus a consistency
    measure.
- **Persistence as "the strongest moat"** (reviews 1, 3). What the lab has proven is
  **governance**: approved versions, admitted procedures, typed and stamped decisions. It hasn't
  proven *reuse* of persisted understanding across agents or over time. The governance story is
  the stronger evidence today.
- **"OWM + Agno"** (review 3). That is an architecture decision outside the lab, with no evidence
  either way here.

## What the reviews miss

1. **Instrument validity: the same designer wrote the truth, the key and the engines.**
   - Agreement between engines and the answer key is partly by construction.
   - The independent checks are the readers, the blind-subagent SLA rules, the agent-authored
     specs, held-out scenarios, and engines frozen before every attack set.
   - Review 6 notes "no independent external red team". The deeper issue is that one team wrote
     the questions, the answers and the solver.
   - **Mitigations worth adding:** an external red team, and a second synthetic company built by
     someone else.
2. **Jev is a dependency.** The calibration (ECE ≤ 0.10) and the cost claims are partly verified
   by us, and it is a young vendor product. The reviews treat it as a given.
3. **The gold-evidence gap is bigger than it looks.** Review 4 flags it (C), but later reviews
   drop it. Credit and SLA have never been decided on *retrieved* evidence, only on evidence handed
   over. "Agents find the evidence, 102/102" is a **discount-only** result (G-22, G-23).

## Two ideas from the reviews that aren't on our board

1. **Authority without title priors** (review 1, "adversarial organization").
   - Today an approver's title ("VP Sales") makes authority guessable from common sense, so an
     agent can be right for the wrong reason.
   - **The test:** make authority flow through a delegation instrument to a non-obvious title
     ("Director, Strategic Commercial Operations"), and see whether agents and engines still
     route correctly.
   - It is cheap, and it attacks a real validity threat in our authority results.
2. **"As known at" time** (review 3: world time against record time).
   - Today we answer "what was in force on date D". We don't answer "what did the organization
     know or recognize at time T", for example a policy registered on the 10th that applies from
     the 1st.
   - The register has `registered_on`, but nothing queries it.
   - This matters for audit ("was the decision right given what we knew then?").

## Recommendations

1. **Keep using the reviews as a sounding board,** but anchor every claim to a lab number. Their
   framing drifts toward architecture; ours should stay with evidence.
2. **Pick one vocabulary and map theirs onto it.** The reviews rename layers almost every time
   (five-layer model, Decision Substrate, Decision Procedure). A short glossary would stop
   documents diverging:

   | Their term | Ours |
   |---|---|
   | Decision Substrate | kernel + flow runner |
   | Decision Procedure | spec |
   | Registered Instruments | register |

   The canon in owm-edd should win.
3. **Next lab work, in order:**
   1. Set G, through the MCP server: the bundled fresh agent test.
   2. **Attacks on the register itself**, starting from Review 6's table.
   3. **Retrieval-backed credit and SLA** (the gold-evidence gap).
   4. **Authority without title priors**.
4. **Add three gaps to the board:**
   - authority without title priors;
   - "as known at" time;
   - instrument validity (an external red team, or a second company by another author).
