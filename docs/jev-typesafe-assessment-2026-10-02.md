# Jev (TypeSafe) for the OWM and BlueLeaf: assessment (2026-10-02)

**Ask:** learn what Jev is and how the OWM, or the platform more broadly, could use it for agent
decisions, routing and confidence. **Sources:** TypeSafe's public docs (`docs.typesafe.ai`, read
2026-10-02; list at the end), PRD-1 §18–19 (`docs/raw-material/…/01-sovera-owm-prd-1-…md`), and
this lab's results. Vendor claims are marked as claims; none has been tested here yet.

## 1. What Jev is

Jev is TypeSafe's "System One" model. **You send state and typed questions; you get probabilities
back, not text.**

| | |
|---|---|
| **Input** | `state`: a string, JSON object or array, text only. Plus named **questions**, each evaluated "in parallel and in isolation against the same state". |
| **Question types** | **Choice**: pick one of up to 255 options. **Score**: an ordered rubric of 2–10 levels. **Noul**: a yes/no probability. |
| **Output** | Choice and Score return the answer, the full `probabilities` distribution and a `confidence` from 0 to 1. Noul returns one probability. There are no explanations: "System One models do not write replies … or generate explanations of their reasoning." |
| **Confidence** | A summary of how peaked the distribution is, not the top probability. For Choice: `(p_max − 1/n) / (1 − 1/n)`. Suggested bands: >0.9 act, 0.5–0.9 confirm, <0.5 route to a human. "The correct threshold values depend on your domain." |
| **Calibration** | Claimed: "Outcomes assigned a probability of 0.8 should occur about 80% of the time." **No published calibration metrics.** |
| **Consistency** | Not documented as deterministic (no seed). In their own test, repeated identical calls had a per-question probability standard deviation of 0.0102. |
| **Speed and cost** | Their cookbook: 111 ms and $0.000043 for a 14-question call, against 1.1–13.9 s for LLMs. Price $0.042 per million input tokens; output tokens free. Context is 64k tokens per request, 32k of it for state. |
| **Deployment** | Cloud API only (`POST https://api.typesafe.ai/v1/systemone`); no on-prem or VPC option documented. Zero data retention for enterprise, and a commitment not to train on customer data. |
| **Versions** | `jev-1.13.0`, with the aliases `jev-latest` and `jev-preview`. Pin the version once thresholds are tuned against it. |
| **Tooling** | Python and JavaScript SDKs. A Claude Code skill (`claude plugin marketplace add typesafe-ai/skills`). No MCP server documented. |

**Their architecture:**
- "Keep code in control." Code owns the control flow, the rules and the side effects; the model
  appears "only where the system needs programmable common sense or needs to interpret
  unstructured data".
- Questions should be **atomic**, and code combines the answers.
- Agent loops are listed as an anti-pattern.

**Known weak spots in Jev 1.13** (their "jaggedness" page). The ones that matter here:
- **Dates:** "reads dates as text, not as ordered quantities … whether one falls inside a window
  is unreliable."
- **Numbers:** it doesn't count, and isn't reliable on numeric closeness.
- **Literal reading:** "answers the question you wrote, not the one you meant."
- **Indirection:** double negatives and "a property of a property" cost accuracy.
- **Distractors:** unrelated content in state lowers accuracy.
- **Adversarial content** "can move the answer".
- **No consistency guarantee** between inverse questions.

## 2. The fit: Jev is the missing middle of the lab's own conclusion

Item 2 ended with: *a governed procedure plausibly needs both forms. Prose for agents, and an
executable, test-covered reference for governance.*
- The oracle is that executable reference. It can only run on **clean typed truth**.
- The readers work from **messy evidence**.
- The gap between the two is the soft judgments: is this the same customer, does this agreement
  apply to *this* customer, is this email a grant or hearsay, does this record match the CRM.

That gap is exactly what Jev is for.

The split falls almost exactly where Jev's weak spots are:

| Step in the discount decision | Who should do it | Why |
|---|---|---|
| Find the evidence (search the foundation, read documents) | **agent / foundation** | Jev doesn't retrieve and doesn't do multi-hop work |
| "Is CRM-2048 the same customer as C-1001, and is Acme Industrial a different one?" | **Jev** (Score: same / related / different, plus field Nouls) | This is their entity-alignment cookbook |
| "Does this agreement name *this* customer?" | **Jev** (Noul / Choice) | The S13/S15 judgment: the only place readers and the key disagreed |
| "Does the exception cover this product?" | **Jev** (Noul) | S03/S17 |
| "Is this statement an authoritative grant, hearsay, or precedent?" | **Jev** (Choice) | S07 and the email trap |
| "Does the record we were handed agree with the system of record?" | **Jev** (Choice: consistent / conflicts / absent) | **the caveat-#2 scenarios** |
| Is the date inside the agreement window? Which policy is in force? | **code** | Jev 1.13 is unreliable on date windows |
| Which band does 15% fall in? Who holds that role? | **code** (the oracle's `band_for`, `_approver`) | numbers and org-chart walks |
| Combine into a decision, and route by confidence | **code** | "keep code in control" |
| Record it | **OWM decision record** | with each atomic answer, its probability, confidence and model version |

**What this buys, measured against this lab's own results:**
- **The routing boundary becomes a threshold, not a wording problem.** Readers disagreed with the
  key only on "commercial review" vs "request evidence" (item 5). Built from atomic answers, that
  boundary is a rule in code. The user's ruling ("route to the accountable approver when unsure")
  becomes confidence-gated routing: low confidence on any input means hold or route; high
  confidence means act.
- **Over-caution becomes tunable.** Item 6's over-caution count has a dial: the confidence
  threshold. Today the only lever is procedure wording, and v2 showed that moving the wording
  moves the failure.
- **The decision record gets real provenance.** PRD-1 §18 already lists "candidate outcome,
  probability distribution, confidence, supporting evidence, model/provider, timestamp". Jev
  produces exactly those per atomic judgment. That is also item 4's point: a decision record needs
  its own provenance class (*derived by engine X at version V from evidence E*).
- **Cost and latency.** A blind Opus reader took 10–29 turns and about $0.25 per decision. If the
  vendor numbers hold, the judgment step drops to milliseconds and fractions of a cent. Evidence
  gathering still costs what it costs.

**What it doesn't buy:** Jev won't find evidence, plan, or explain. Explanations would come from
the composition code and the atomic answers, which is arguably better provenance than prose, but
it is a different artifact than the readers produce today.

## 3. Wider platform uses (BlueLeaf)

| Where | Use | Lab evidence it targets |
|---|---|---|
| **Foundation identity** (Utopia's duplicates queue; DocIQ) | Adjudicate candidate pairs with a Score plus field Nouls. Merge or reject automatically at high confidence; send the uncertain middle to a curator queue | Utopia's governance agent uses gpt-4o for this. The user's OpenAI spend was ~$75 by 2026-09-29, across ingestion and governance. The scale run's ~9,000 pairs is the obvious test set |
| **Extraction checks at ingest** | Citation check: does the attached quote *support* the extracted fact (supports / contradicts / says nothing)? | Item 3: the inverted `reports_to` facts carried quotes that "say nothing" about reporting. A says-nothing verdict flags them before they reach the graph |
| **Keeping decisions out of evidence** | At ingest, classify a document as primary evidence or a derived decision record | Item 4: a decision stored as a document became undated facts and was cited as evidence |
| **Agent tool and procedure selection** (agents-first) | Intent routing: which procedure applies to this request | 102/102 readers found `get_procedure` with one procedure; with many, selection becomes a decision |
| **Guardrails on agent outputs** | Noul: "does this answer approve a discount?", "does it name an approver?" A cheap check before an agent's output acts | The user's definition of unsafe |

## 4. Constraints and canon questions (amendment candidates, not decisions)

- **"No LLM in the OWM serving path" (canon).** Jev isn't a generative LLM, but it is a hosted
  model. PRD-1 already places TypeSafe as "an implementation of the decision layer, not a
  dependency of OWM". So it belongs in the decision and agent layer (LangGraph), not the kernel.
  The kernel would store procedures and decision records that cite the engine. Canon should say so
  explicitly.
- **Deployment.** Cloud-only, while BlueLeaf is single-tenant and internal. Data leaves the
  boundary unless the enterprise zero-retention terms are enough. This needs a DPA review.
  Synthetic Northstar data is fine for the lab.
- **Reproducibility.** The lab's builds are byte-reproducible; Jev has no seed. For the lab, record
  every Jev response alongside the run, the way transcripts are kept, and score from the recording.
  Pin `jev-1.13.0`.
- **Calibration is claimed, not shown.** Thresholds mean nothing until calibration is measured on
  our own data. The lab has ground truth for every atomic judgment, so it can do that.
- **Vendor and version risk.** It is young, and aliases move. Pin versions, and keep the
  decision-layer interface engine-neutral, as PRD-1 already says: rules, TypeSafe, LLM, human,
  composite.
- **Constitution (Principle VII, human-judgment gates).** Confidence-gated routing is a natural
  implementation, but the gate thresholds become governed content. Who sets 0.85, and how is a
  change to it reviewed? That makes thresholds a candidate amendment item.

## 5. A lab probe, before any canon or PRD commitment

Cheap, Northstar-native, and pre-registered like the earlier items:

1. **J1: judgment quality on gold evidence.**
   - For S01–S21, build each scenario's state from the artifacts its corpus actually contains
     (the `supports`-tagged ones, never `truth/` or the answer key).
   - Ask the atomic questions from §2, and let oracle-style code compose the decision.
   - Score it with both of the lab's scores (strict, and acceptable to act on with over-caution).
   - This is Jev's upper bound: perfect retrieval.
2. **J2: calibration.**
   - Every atomic question has a truth label, giving a few hundred labelled probabilities.
   - Report a reliability table: predicted against observed, by band.
3. **J3: the caveat-#2 scenarios.**
   - Requests whose record conflicts with the CRM, with a key that rewards flagging the conflict.
   - Run them through both the Opus reader and the Jev pipeline.
4. **J4 (optional): identity at scale.**
   - Jev on a sample of Utopia's governance pairs (synthetic data), against the lab's
     identity ground truth.
   - Compare with gpt-4o's merges on cost and accuracy.

**Cost:** cents of Jev (vendor pricing), no Utopia ingestion for J1–J3, plus Claude only for the
J3 reader arm.

**Prerequisites:**
- A TypeSafe API key. It stays outside the repo, like the Utopia tokens.
- The user's OK to send the synthetic corpus to TypeSafe's API.

## 6. Open questions

For the user:
- Is Jev intended for the platform (decision layer and foundation), or mainly for the OWM's
  decision records?
- Do you have, or want, enterprise terms with zero data retention?

For TypeSafe:
- Is there calibration evidence on any public benchmark?
- Is there an on-prem or VPC option?
- What is the determinism or variance guarantee per pinned version?
- What is the version deprecation window?

## Sources

`docs.typesafe.ai`, read 2026-10-02:
- `llms.txt`
- `introduction`, `concepts/system-one`, `concepts/state`, `concepts/how-to-build-with-system-one`
- `primitives`, `confidence`
- `patterns/confidence-routing`, `patterns/composite-scoring`, `patterns/fan-out`
- `model-jaggedness/jev-1.13`, `models`, `api`, `legal`, `agent-skill`
- `introduction/machine-learning-primer`
- `cookbooks/entity_alignment`, `cookbooks/citation_check`, `cookbooks/consistency_noul_cookbook`
