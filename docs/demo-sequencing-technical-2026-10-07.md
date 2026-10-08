# Demo sequencing for a technical audience (alternate version, 2026-10-07)

**This builds on** "Shiny-Waffle Demo sequencing RAW - 2" (dated) and its review
(`demo-sequencing-feedback-2026-10-07.md`), and uses the lab's results through 2026-10-07. The
audience is technical: engineers, architects, AI and platform leads.

## The thesis, in one slide

> **Retrieval isn't the bottleneck. Decisions are.**
> - RAG and GraphRAG agents find the evidence: **102 of 102** in our tests.
> - They decide mostly right: **93 of 102**.
> - But they fail where it matters most: on edge cases, on forged documents (**25 of 47**), and in
>   the structured output that other systems act on (**59 of 757** answers said "confirm first"
>   while their decision said "approve").
>
> The OWM adds the organization's governed state on top of the knowledge foundation:
> - the approved documents;
> - who may decide what, and when;
> - procedures as versioned, admitted objects;
> - decisions as typed records.
>
> With it: **0 of 47** attacks succeeded, **102 of 102** decisions were right, and every decision
> names the policy and procedure version that made it.

The draft's arc was "RAG → GraphRAG → OWM". This version makes it **"where agents on RAG or
GraphRAG break, and what fixes each break"**. Every fix is a lab measurement, not a diagram.

## Ground rules for a technical room

1. **Name the baselines, and give both sides the same model:**
   - **RAG:** Claude with the written procedure and the request, plus the documents (retrieved
     chunks, or the whole corpus);
   - **GraphRAG:** the same agent with the knowledge graph's tools (the lab's B1 and B2 arms);
   - **OWM:** the same agent gathers the evidence, Jev answers narrow questions, rules decide, and
     the OWM records the decision.
2. **Show distributions, not single draws.** Run each live round **×5–10** and show the tally
   ("baseline 3 of 5 approved the forgery; OWM 0 of 5"). Technical people distrust one lucky run,
   and so should we: one live draw is how demos lie.
3. **Concede what the baseline does well, early and with numbers:** 102 of 102 retrieval, 93 of 102
   decisions, 77 of 84 clean decisions in our latest re-baseline. It buys trust for the rounds
   where it fails.
4. **Show the artifacts:** the JSON decision record, the YAML procedure, a register entry, a
   flagged incident. In this room they are the product.
5. **Show the method:** pre-registered predictions, sealed attack sets written by people who knew
   the design, misses reported. Mention one honest miss (see the close). Nothing sells rigour like a
   reported failure.

## The sequence (about 30 minutes; rounds 4–6 are the heart)

| # | Round | Question / action | Lab scenario and assets | RAG / GraphRAG agent (lab evidence) | OWM (lab evidence) | Live or recorded |
|---|---|---|---|---|---|---|
| 0 | **Setup** | The synthetic company, its messy evidence, and the three-layer architecture | `dataset/evidence`, the trap table | — | — | Slides (2 min) |
| 1 | **Calibration** | "Is Acme eligible for 15% on the NS-500?", then "Can Sarah approve it?" | S01 | **Right, in prose.** Agents find every document (102 of 102) and decide well (93 of 102) | Same answer, as a **typed decision**: APPROVE_WITH_AUTHORIZATION, approver Michael Torres, the policy version, the evidence | Live ×5 (4 min) |
| 2 | **Edge cases and identity** | "Can Sarah approve 15% for *Acme Industrial*?" Then the merge queue | S13 (another company's contract); identity pairs | **Misses some edge cases:** all 9 of the agents' misses were edge cases like this. General-purpose cleanup made **319** wrong merges in 41,600 pairs, mostly orders merged into customers | Identity guardrail: **0** wrong merges. The decision applies only the right customer's contract | Live ×5, plus a recorded merge chart (4 min) |
| 3 | **Time** | "And in February 2027?" | S21 (the 2027 policy, so the CRO) | **Usually right** on clean data (3 of 3 in our re-baseline). Say so | David Morgan, **from the policy in force on the request date**, with the version stamp | Live ×3 (3 min) |
| **4** | **Integrity: the punch** | Edit the 2027 pricing policy in the shared drive, or drop in a "CRO email" moving its start date. Ask round 3 again | Attack B2 (CRO email: the reader was fooled **3 of 3**); D2 or F1 (in-place policy edits) | **Follows the forgery.** Across all six attack rounds, agents alone were fooled by **25 of 47**. Planted "ignore your rules" instructions moved nothing, but convincing documents worked | **Unchanged.** The register holds the approved version; the edited copy raises an incident to its owner. **0 of 47** across six rounds | Live ×5, plus the 47-attack chart (6 min) |
| **5** | **The record systems act on** | The submitted request says 8%; the CRM says 15% (S22) | S22; G-16 and G-35 results | **Explains the conflict, then approves in its JSON** (3 of 3 in J3). Across all runs, **59 of 757** answers did this | The decision carries a **blocking condition** ("confirm the figure") and decides on the system of record. With the adopted `conditions` field, holds reached the record **26 of 26** on fresh cases, even for the agent | Live ×5 (5 min) |
| **6** | **Governed procedures** | "Who wrote the procedure that just decided?" | G-07, G-12, G-13 | An agent's procedure is a prompt: unversioned, unreviewed, editable by anyone | An agent **wrote** the SLA procedure (10 of 10 at its first attempt). The **admission gate refused it** (it relied on a document it didn't need). It fixed itself from the gate's report, was admitted, and a person approved it. Now **every decision is stamped** with the procedure version. **Delete one rule from the procedure file:** governed decisions don't change, and are flagged (ungoverned, the same edit wrongly approves 2 credit requests) | Live for the tamper demo (3 min); recorded for the gate story (3 min) |
| 7 | **Close** | One decision record, end to end; the numbers; the honest limits | The CxO doc's numbers | — | — | Slides (3 min) |

**If time is short,** cut round 2, then round 3. **Never cut 4 or 5:** those are the rounds a RAG
system can't win by retrieving better.

### Why this order

- **Rounds 1–3** let the baseline succeed, mostly. The audience relaxes, and the comparison is fair.
- **Round 4** breaks the assumption that whatever is retrieved is true. It is the lab's largest and
  most repeatable gap (25 of 47 against 0 of 47), and no retrieval improvement closes it. Only
  knowing which version is approved does.
- **Round 5** breaks the assumption that a good explanation is a good decision. Technical people
  feel this immediately: their systems consume the JSON.
- **Round 6** answers the next question in the room, "so who writes and controls these
  procedures?", with agents writing them under governance.

## The close (three slides)

1. **One decision record, end to end:**
   - request → evidence (with provenance) → narrow judgments (with confidence) → rules → outcome →
     approver → conditions;
   - the policy version, the procedure version, and the register versions read.
2. **The numbers:**

   | Measure | Agents alone | With the OWM |
   |---|---|---|
   | Decisions right (102) | 93 | 102 |
   | Attacks that worked (47) | 25 | 0 |
   | Wrong merges (41,600 pairs) | 319 (general-purpose cleanup) | 0 |
   | Answers whose JSON contradicts the text (757) | 59 | holds go into `conditions` |
   | Cost per decision | about $0.25–0.31 (agent reasoning) | a fraction of a cent for judging; the agent's search dominates |

3. **What isn't proven yet:**
   - **Scope:** one synthetic company, three decision types, small repeat counts.
   - **The register's own controls** (who may register) were designed, not attacked.
   - **Executors that honour blocking conditions** aren't built.
   - **An honest miss:** we found and fixed a lab input inconsistency on 6 October. Reader numbers
     before it were measured on inconsistent inputs, and the re-baseline came back 83 of 84 safe.
   - **Next:** a fresh red-team round run by people, through the agents-first OWM server.

## Questions to prepare for (lab-backed answers)

| Likely question | Answer |
|---|---|
| "Isn't the register just an allowlist?" | It is an allowlist **of approved versions**, with structured terms, explicit relations (supersedes, amends), validity windows and an owner. A changed copy isn't ignored: it raises an incident to its owner, and the decision proceeds on the approved version. Without it, guards alone still let forged or edited governing documents through (13 of 47) |
| "Why not just a better prompt?" | We tried: procedure v2 fixed two scenarios and broke another. Prompt rules shift outcomes; versioned procedures with an admission gate make them testable |
| "Prompt injection?" | Overt injections moved nothing, for agents or engines. The danger is **plausible documents**, not instructions |
| "Who writes the procedures, and doesn't that just move the problem?" | Agents can write them (credit 10 of 10, SLA 10 of 10 at the first attempt). The gate checks them against clean cases, every sealed attack set and reliance; a person approves. Agents propose and never approve |
| "Isn't this just a rules engine or BPM?" | The rules are a thin layer. The OWM's substance is **governed state**: which documents are approved, who holds what authority on which date, which procedure version is in force, and what was decided on what evidence. The LLM handles evidence-gathering and narrow judgments; code composes the decision |
| "Does it generalize past discounts?" | Three decision types (discount, credit, SLA response; SLA isn't even an approval) on one decision core, with no type-specific branches. Procedures are data, at 0.5–0.7× the lines of code |
| "Latency and cost?" | Judging is a fraction of a cent per decision; the agent's evidence gathering dominates. Choosing a cheaper agent tier is the next experiment |
| "What does the LLM still decide?" | Narrow, calibrated judgments: does this guarantee name this customer? Is this title the VP Sales? Each is recorded with its confidence, and the uncertain ones route to a person |

## What has to exist for this demo

| Need | State | Where |
|---|---|---|
| Side-by-side runner (baseline vs OWM, ×N, tallies) | **To build.** The skunkworks MCP server's experimenter mode does most of it; a thin presenter view on top would finish it | `skunkworks/blueleaf-mcp` (your build) |
| Scenarios S01, S13, S21, S22; attacks B2, D2, F1 | In the lab | `truth/`, `runs/` |
| Register, admission gate, governed procedures, `conditions` | In the lab (`lab/owm_register`, `lab/spec_admission`, `lab/owm_kernel/governed.py`, `owm/procedures`) | `main` |
| Consistent request records for readers | In the lab (G-36 overlay) | `lab/reader_inputs/overlay.py` |
| Recorded fallbacks for every live round | To record during rehearsal | — |
| Slides: thesis, the 47-attack chart, the numbers, the limits | The chart and numbers exist in the CxO doc | Claude Docs |

**An optional finale, if the MCP server lands:** "bring your own forgery". A volunteer writes one
document in Claude Desktop (subject mode is blind to the answer key), plants it, and asks. The lab's
sets C–F were exactly this, written by someone who knew the design: the register engines held all
of them. It is memorable, but run it only after rehearsals give the same result every time.

## Decisions (the user, 2026-10-07)

### 1. Utopia is never named

The intent is to absorb all of Utopia's capabilities, and Utopia stays behind the curtain until our
own knowledge foundation replaces it.
- **On stage,** the GraphRAG baseline is "graph retrieval on the knowledge foundation". The RAG
  baseline doesn't touch Utopia at all: the documents go straight into context.
- **Nothing visible may leak the name:** transcripts, tool names, API paths, error messages,
  environment banners. See section 2 for what `web-next` shows today.

### 2. The demo lives in `kloudtaxi/glowing-garbanzo`, branch `v1/use-manage-operate`, folder `web-next`

This was checked read-only on 2026-10-07, at `ad34c11`: "web-next v1.1: fold OWM governance into
Use / Manage / Operate".

**What's there.** A Next.js 16 Use / Manage / Operate UI that proxies the foundation's API, or runs
on a built-in demo organization. Governance v1.1 is already designed: the register, mismatch modes,
procedures with authors (person or agent), registrar and approver, admission gates A/B/C, approvals,
and decision records with conditions. Its five proposed endpoints map one to one onto lab work that
is already computed:

| `web-next` proposes (`owm/docs/ops-api-gaps.md`) | The lab already computes |
|---|---|
| #16 `GET /register`, with coverage and stated absences | `lab/owm_register/*.yaml` and `serve.py` (G-01, G-31) |
| #17 approve / return; `settings.mode` = `on_mismatch` | The registrar's rules (the registrar ≠ the approver; agents never approve); `use_registered` / `route` in `flow.py` (G-01, G-32) |
| #18 `GET /procedures`, with admission reports | `lab/owm_register/procedures.yaml`, `build_procedures.py`, `lab/spec_admission/admit.py` (G-13, G-07) |
| #19 `GET /approvals` | Pending registrations, plus conditions that name a person (G-35) |
| #20 the answer's `governance` and `decision` (conditions, procedure stamp, register used) | `lab/owm_kernel/governed.py` + the `conditions` field (G-13, G-35) |

**Two gaps for a technical showing:**
- **"Utopia" is visible in the UI:** about a dozen strings. They include the page titles, the
  header wordmark, sign-in, empty states, "Ask Utopia anything", "Loading Utopia…", "The Utopia
  backend is unreachable", and a procedure author named "Utopia procedure agent". All need
  rebranding before any audience sees the app.
- **The governance screens run on a hand-built sample organization** (Bluefin and its people),
  marked with **Sample** badges. A sharp audience will ask "is this real?". The proof rounds have
  to be computed.

**Recommendation:** serve endpoints #16–#20 for real, for a Northstar organization, from a thin
HTTP layer over the lab modules above. The skunkworks MCP server's `service/` layer (spec §2) is
designed to be exactly that core. `web-next`'s Sample badges then switch to live on the
Northstar screens, and the proof rounds run in the product UI, not a lab console.

### 3. Predictable, not scripted

The audience is too smart for anything canned. Predictability comes from **how the system
works**, not from controlling what it's asked:

1. **The OWM side is deterministic by construction.** Register lookups, rules and procedure
   versions are code. Jev's answers are recorded by request hash: a repeated input replays, and a
   new one costs cents. The same evidence gives the same decision, every time, whoever chooses the
   input.
2. **The audience chooses the inputs, within a bounded sandbox.**
   - They pick the scenario, the date, which governing document to tamper with, and how
     (change a number, move a date).
   - Or, the finale, they write the forgery themselves.
   - The mechanism is fixed; the inputs aren't.
3. **The baseline's variance is shown, not hidden.**
   - Run it ×5 in parallel and show the tally.
   - Open one transcript at random, not the best one.
   - Put the rehearsal rate on screen ("in 30 rehearsal runs, the baseline followed this forgery
     28 times"). The live run is one more sample, not the claim.
4. **The same model on both sides: Opus 5.5,** the model behind every lab number.
   - A weaker baseline invites "you nerfed it".
   - A cheaper OWM agent is unmeasured (experiment 3), so it isn't claimed.
5. **Show the machinery and its seams.**
   - Show the JSON record, the YAML procedure, the register entry, timings and cost per run.
   - Include one case the OWM routes to a person instead of answering: uncertainty handled is
     more convincing than another win.
   - State one measured miss.
6. **The fallback is a labelled replay.** Every run is logged. If the network fails, replay the
   logged run, marked "replay". Never a mock-up.

## Open questions for you

Questions 1–3 are answered above. The follow-ups were settled on 2026-10-07:

1. **Rebranding `web-next`:** it will be rebranded in place, after it works. Before any outside
   showing, every visible "Utopia" string must go.
2. **Who builds the OWM API for #16–#20:** a lab session, in shiny-waffle. This was Claude's
   call, at the user's invitation.
   - **The service:** the OWM endpoints run as a separate service that `web-next` reaches through
     its own `OWM_API_URL`, apart from the foundation proxy. `ops-api-gaps.md` already says
     governance is "served by the OWM, not Utopia".
   - **The contract** is `web-next`'s `lib/types.ts` shapes for #16–#20.
   - **The code** sits on the same lab modules that the MCP server's `service/` core reuses, so the
     two can merge later. The product repo never depends on the lab, and a real OWM service later
     replaces the lab one behind the same endpoints.
   - **`web-next` needs** an `OWM_API_URL` route for the OWM paths, and a Northstar organization
     at sign-in (Priya and Elena for Finance, Hannah and Marcus for Support).
