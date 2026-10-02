# Experiments worth running next (2026-10-02)

These come from what the lab has measured so far, and from the assumptions it still leans on.
They are ranked by how much they would change a BlueLeaf decision per unit of effort. None has
been started.

## What is settled, and what is still assumed

**Settled:**
- Agents are good at retrieval (E2E: 102/102 sufficient).
- Jev is good at single-point judgments, and its confidence is calibrated on our labels (J2,
  J4).
- Code is good at rules (J1, J3-H).
- Agents' failures sit in turning evidence into a decision (E2E: 9/9 fixed).
- Decisions must not become evidence (item 4).
- Identity governance by an LLM over untyped entities makes false merges (J4: 161).

**Still assumed:**
- **authority** (policy, bands, roles, approver), held at truth in J1 and E2E;
- **one decision type** (discount approval) and **one organization**;
- **retrieval by Opus readers** that were asked to answer, not to gather;
- **trustworthy documents** (no adversarial content);
- **decision memory with one decision in it**;
- **identity measured on a 1,445-pair sample**, with no operating point chosen.

## Ranked

| # | Experiment | Question it answers | Effort | Cost |
|---|---|---|---|---|
| **1** | **Authority from evidence.** The hybrid engine reads the policy bands and the org chart or `employees.csv` itself (code parsers; Jev only for soft text such as titles). Re-run J1 and E2E. | Does the whole decision run off evidence, with truth used nowhere? Closes J1's last crutch. | hours | ~$0 |
| **2** | **Identity at full scale, with guards and an operating point.** Jev, plus the "order id ≠ customer id" rule, on the whole 22,759-pair queue. Sweep thresholds and plot false merges against human-review load. Pre-register on the base KB, replicate on the missing-contract KB's ~20k pairs. | The operating point for BlueLeaf's identity service, and what it costs in review. Turns J4 from a sample into a design. | hours | ~$1 Jev |
| **3** | **An agents-first pipeline with a cheap retriever.** Give Haiku 4.5 or Sonnet 5 a purpose-built OWM tool ("gather the governing documents for request X"). The hybrid decides and a typed decision record is persisted. Compare sufficiency, turns and cost with the Opus readers. | Which model tier the agent role needs once its job is retrieval only, and what a decision costs end to end. The biggest cost lever. | a day | ~$3–5 Claude |
| **4** | **Adversarial evidence.** A forged "CRO approved 20%" email, an exception carrying an injected instruction, an unsigned amendment. Run against the Opus reader and the hybrid. Gold-evidence first (no ingestion), then a few docs into Utopia (cents of gpt-4o). | Whether "adversarial content can move the answer" (Jev's own limits page) reaches our pipeline, and whether the code guards hold. Safety for an agents-first OWM. | a day | ~$3 |
| **5** | **A second decision type**, for example a credit-limit increase or a contract renewal in Northstar: new truth, an oracle function, a procedure and about 10 scenarios. Same arms: procedure via tool, hybrid, E2E. | Does procedure-as-governed-object plus Jev plus code generalize, or is it shaped to discounts? The biggest unknown for "OWM, not a discount app". | days | ~$10 + cents |
| **6** | **Decision memory at scale.** About 200 hybrid-made decision records over the 1,000 background requests. Readers asked precedent and audit questions; typed records against decision documents; contamination measured at scale. | Item 4's open question: retrieval among many decisions, and whether the document carrier's contamination grows. | a day | ~$10 |

**Small add-ons:**
- Jev repeatability: 3× repeats on the J2 and J4 samples, for cents.
- Per-question-type thresholds, tuned on half of J2 and tested on the other half.

## Suggested order

1 and 2 first: they're cheap and close the two loudest gaps. Then 3, the BlueLeaf-shaped end to
end, then 4, before anything acts automatically. 5 is the strategic test once the pipeline is
settled, and 6 when decision memory gets built.

## What not to spend on

More n = 3 replications of the arms already run. Their results are stable, and the open questions
above won't move with more of them.
