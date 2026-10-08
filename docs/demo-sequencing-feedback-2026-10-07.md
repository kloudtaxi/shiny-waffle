# Feedback: "Shiny-Waffle Demo sequencing RAW - 2" (2026-10-07)

This reviews your draft against what the lab has measured.

**Verdict:** the narrative is right: use RAG and GraphRAG as the runway, then let the problem escape
retrieval. But two of the five planned rounds won't reliably show a difference live. The strongest
proof the lab has isn't in the sequence yet. Keep the arc, and swap in rounds where the
"before/after" gap is large and repeatable.

## What's strong

- **The audience's mental model is the runway.** "We all know RAG" lowers the barrier, and "don't
  strawman it" is right. The lab backs it: agents found every needed document in 102 of 102
  decisions. Say "search isn't the bottleneck" out loud; it sets up why OWM sits *above* the
  foundation, not instead of it.
- **"Can Sarah approve?" is the right boundary question.** A knowledge graph alone got 2 of 10
  fully right at scale. With the procedure and the request, agents got 15 of 15. So the gap is
  the OWM's job: procedure, inputs, authority.
- **The positioning line is good:** "RAG retrieves knowledge. GraphRAG organizes relationships. OWM
  represents the organization's governed state and how agents are allowed to act on it." I'd add
  *which documents count* (see risk 3).
- **Every scenario you name already exists in the repo:**
  - S01: Sarah, 15%, approve with authorization by Michael Torres;
  - S21: February 2027, so David Morgan (CRO);
  - S05: the contract is missing, so request evidence.

## Five risks

### 1. On clean data, the baseline will often be right, and live demos are single draws

A strong LLM with the documents in context already answers most of these correctly:
- the plain reader, with every document and the procedure, held **77 of 84** clean decisions in
  yesterday's re-baseline (6 more routed safely);
- **S21 (2027, so David Morgan): 3 of 3 correct**;
- **S05 (contract missing): 3 of 3 asked for evidence**, with no hallucination.

So "Can Sarah approve?", "What about 2027?" and "What if evidence is missing?" may come back
*right* from the baseline on stage. Then the punchline falls flat, or you are tempted to weaken the
baseline, which is the strawman you want to avoid.

**What the gap really is,** by the lab's measures:

| Where OWM clearly wins | Lab evidence |
|---|---|
| **Forged or altered documents** | AI agents alone were fooled by **25 of 47** attacks; OWM with the register, by **0 of 47** |
| **Edge cases** | Agents alone 93 of 102 (all 9 misses edge cases: another company's contract, an agreement not yet started); the split design 102 of 102 |
| **The structured decision agents act on** | **59 of 757** answers said "confirm first" in prose while the decision said "approve"; fixed by the conditions field |
| **Data cleanup and identity** | General-purpose AI made **319** wrong merges; with a guardrail, **0** |

### 2. The baseline definition decides the outcome, so fix it before rehearsing

"GraphRAG" can mean graph facts only (weak: 2 of 10) or graph plus document chunks (strong: close to
the reader's numbers). Pick one, say which on stage, and use the same model for both sides. A
baseline the audience can't check reads as a setup.

### 3. The strongest, newest differentiator is missing: which documents count

The register result is the most memorable thing the lab has:
- someone edits the pricing policy in the shared drive, or a "CRO-approved" email moves a date;
- the agent believes it;
- the OWM ignores it, because only the approved, registered version counts, and alerts the owner.

It is easy to show, hard to fake, and it answers "why not just RAG?" in one move. Add a row to your
table:

| | Basic RAG | GraphRAG | OWM |
|---|---|---|---|
| **Which documents count** | whatever is retrieved | whatever was ingested | **only approved, registered versions; a changed copy alerts its owner** |

### 4. "Remove a piece of evidence" won't trip a good baseline. "Missing plus misleading" will

The plain reader asks for evidence when the contract is missing (S05: 3 of 3). What fooled agents
in the lab was a *plausible substitute*. A master-data note claiming that Acme Industrial is
covered by Acme's agreement fooled the reader 2 of 3 times. A Finance "suspension" notice fooled it
3 of 3. Remove the contract **and** leave a convincing note in its place. That is where the baseline
answers and the OWM asks.

### 5. The audience question changes the wording

- **The client demo as set up on 2026-10-03:** clients, BlueLeaf brand, Utopia invisible, no JSON,
  model names or jargon on screen.
- **Your draft** speaks to an audience that knows RAG and GraphRAG.

Both can work, but not in the same deck:
- **For technical buyers or partners:** RAG → GraphRAG → OWM, as drafted.
- **For business clients:** translate the runway into "search → connected search → the
  organization". Show outcomes in plain words ("Needs Michael Torres's approval", "Needs more
  evidence"), not APPROVE_WITH_AUTHORIZATION or REQUEST_EVIDENCE. Label the baseline generically
  ("standard AI search"), and never show Utopia.

## A sequence I'd recommend

This keeps your four acts, with rounds chosen so the gap is large, repeatable and backed by the
lab.

| Round | Question | Scenario | Baseline, expected (lab) | OWM | The audience sees |
|---|---|---|---|---|---|
| 1. Knowledge | "Is Acme eligible for 15%?" | S01 | Right | Right | "That's RAG, and it works." Concede it |
| 2. Relationship | "Why? And which Acme?" | S01 vs S13 (Acme Industrial) | Usually right; sometimes picks up the other Acme's contract | Resolves the two Acmes, and shows the identity guardrail | Connected facts matter |
| 3. Authority | "Can Sarah approve it?" | S01 | Usually right *in prose* | A decision: needs Michael Torres's approval, sent to him and recorded with the policy version | Agents act on a decision, not a paragraph |
| 4. Time | "And in February 2027?" | S21 | Usually right | David Morgan, from the 2027 policy, with the version stamp | Rules change; the OWM knows which were in force |
| **5. The punch: integrity** | Same question, after someone edits the policy in the drive (or a "CRO email" moves the 2027 date) | Attack sets B2, D2 or F1 | **Follows the forgery** (lab: B2 fooled the reader 3 of 3; forged or edited governing documents fooled it in 21 of 21 runs across sets C and D) | **Unchanged.** It reads the approved version and alerts the policy owner | Why "just RAG" isn't safe for decisions |
| 6. Uncertainty | "The request says 8%, but the CRM says 15%" (S22), or the contract removed plus a misleading note | S22 / S05 + A7 | Explains the conflict but its decision says "approve" (J3: 3 of 3), or follows the note | Routes, with a blocking condition: "confirm the figure" | It knows what it doesn't know, and says so where systems look |

**Close:** one decision record, showing who decided, under which policy version and which procedure
version, from which evidence. "Every decision, explainable a year from now."

Rounds 1–4 are your runway, and shorter than in the draft. Rounds 5–6 carry the proof. If time is
short, cut round 2, never round 5.

## Before you rehearse

1. **Measure the baseline's failure rate per round.** Run each round 10 or more times, and keep
   only the rounds where the gap is stable. The lab's numbers are averages; the stage gets one draw.
2. **Have a recorded fallback** for every live round.
3. **Same model on both sides,** and say so.
4. **Ask the lab** (through the demo repo's `docs/requests-to-lab.md`) for:
   - the register and the conditions field, which postdate the demo's pinned `dataset-2026-10-03`
     tag;
   - a demo-safe attack document for round 5 (one of B2, D2 or F1);
   - a new dataset tag if the demo needs the per-scenario overlay (G-36).

## Small edits to the draft

- **The table:** keep only the rows the demo proves (one per round), and add "which documents
  count". "Agent action: constrained by organizational state" goes beyond what the lab has built:
  executors that honour conditions don't exist yet. Say "decisions an agent can act on" instead.
- **Round 3's answer** is accurate. Under the 2026 policy, account executives approve up to 10%;
  15% needs the VP Sales, Michael Torres.
- **"Nothing about Sarah changed" in 2027** is true in the data. Only the policy changed, which is
  exactly the point.
