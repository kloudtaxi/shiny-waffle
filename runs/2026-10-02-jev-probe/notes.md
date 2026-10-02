# Jev probe J1–J3 (2026-10-02)

> **STATUS: DONE.** Pre-registered in `plan.md` (commit `956a6fe`), with the J2b addendum added
> before any Jev call. Engine: `jev-1.13.0`, pinned, through `lab/decision_engine` (recorded, and
> replayable with `--replay`). Background: `docs/jev-typesafe-assessment-2026-10-02.md`.

## Results at a glance

| | Question | Result |
|---|---|---|
| **J1** | With perfect retrieval, does "Jev judges, code composes" reach the oracle's decisions? | **18/18**, raw and confidence-gated. 20 distinct calls, median 184 ms, **$0.0004** in all. |
| **J2** | Are Jev's probabilities calibrated on our labels? | **ECE ≤ 0.10 on every set**, the pre-registered "usable for gating as is" bar. Past the gate, accuracy is 98.9–100%. |
| **J3** | Do agents catch a submitted record that conflicts with the CRM? | Yes: 9/9 noticed. But on S22, 3/3 still put `APPROVE` in the decision block. A code diff catches it by construction. See `j3/notes.md`. |

## J1: the hybrid engine on 18 decisions (`j1/`)

**Every scenario passes**, including the three that split the readers and moved between procedure
versions:
- **S13 and S15** (another customer's terms) come out `REQUEST_EVIDENCE`. Code routes them from a
  party judgment, so the "commercial review" vs "request evidence" boundary becomes a rule rather
  than a wording problem.
- **S18** (the old exception's last day) comes out `APPROVE` under EXC-ACME-NS500-10. Code picks the
  exception in force by date; the cited agreement doesn't steer it.

**Uncertainty landed on the genuinely hard pair, and only there.**
- One judgment fell below the gate: Acme Industrial Supply (S13) against the 2023 exception, a
  document that names only "Acme Manufacturing", with no address. Jev split it 0.40 different, 0.28
  same, 0.32 unclear. The gated outcome is still the key's `REQUEST_EVIDENCE`.
- True matches (Acme Manufacturing against "Acme Mfg. Holdings, doing business as Acme
  Manufacturing") came in at confidence 0.86.

**Against the predictions:**
- at least 16/18: **18/18** ✓;
- S13 and S15 come out `REQUEST_EVIDENCE` ✓;
- S18 comes out `APPROVE` ✓;
- 0 unsafe ✓;
- under $0.05: **$0.0004** ✓.

**What J1 does not show:**
- **It is an upper bound.** Jev was given exactly the right documents; retrieval was perfect.
- Authority was held at truth.
- Code parsed dates and percentages from this corpus's document formats.
- The perfect-judge control (`j1/control.py`, 18/18) shows the pipeline itself is right, so J1
  isolates Jev's judgments. Those were all correct at n = 18. An end-to-end test, with an agent
  doing the retrieval, is still to do.

## J2: calibration (`j2/calibrate.py`, `j2/calibration.md`)

| Set | n (positives) | Accuracy | ECE | Past the gate | Accuracy past the gate |
|---|---|---|---|---|---|
| grid · party | 36 (3) | 1.000 | 0.025 | 97% | 1.000 |
| grid · product | 27 (5) | 1.000 | 0.042 | 100% | 1.000 |
| grid · basis | 2 (1) | 1.000 | 0.000 | 100% | 1.000 |
| **J2b-addr**: CRM→ERP identity, name and address | 612 (204) | **0.997** | **0.050** | **95%** | **1.000** |
| **J2b-name**: CRM→ERP identity, names only | 612 (204) | 0.874 | 0.087 | 74% | 0.989 |

- 1,289 calls took 33 s with 8 workers. Median 191 ms, p95 249 ms, **$0.024**.
- **With addresses, identity is near-solved:** 99.7% accurate, and 95% of answers can be acted on
  automatically at 100% accuracy.
- **With names only, Jev leans conservative.**
  - It said "different" on 73 true matches. The CRM display name and the ERP legal name can differ
    a lot: "Simon, Smith and Page" is "Simon LLC". Most of these fall in the gated band.
  - False merges, the dangerous identity error (the Acme Industrial trap), are rare: 4 of 408.
    The one confident false merge (0.99) is "Miller LLC" against "Miller LLC" in another city,
    which no name-only judge could resolve.
- **The reliability table shows under-confidence between 0.1 and 0.3.** Pairs scored 0.14–0.25 for
  "same" were the same company 39–53% of the time. Tuning thresholds per question type would win
  back coverage. As pre-registered, the probabilities are already usable for gating.
- **The grid is too small to say much.** It has 3 positive party pairs and 2 justifications, which
  is why J2b was added.

## What the probe shows

1. **The split works.** Jev answers single-point questions with probabilities. Code does dates,
   numbers, bands and composition. On gold evidence that reproduces the oracle: 18/18, sub-second,
   fractions of a cent. The prose procedure's two failure classes, the routing boundary (S13/S15)
   and the cited-vs-in-force agreement (S18), turn into code rules fed by judgments.
2. **Confidence-gated routing is real on our data.** Calibration is measured, not taken on trust.
   The gate keeps 74–100% of answers at 98.9–100% accuracy and sends the rest to a person. That is
   the user's ruled standard ("route to the accountable human when unsure") as a mechanism.
3. **Uncertainty shows up where the hard cases are:** S13's Acme Industrial pair, and name-only
   variants. Together with the conservative lean on identity, this matches what the lab needs:
   don't merge, and don't approve, on a guess.
4. **Inputs belong in code** (J3). Agents notice conflicts, but can still decide on a doubtful
   input. A diff of structured inputs before the decision, plus a typed `input_conflicts` field in
   the decision record, removes that path.

## Next steps (proposed, not run)

- **J4, identity at scale:** Jev on Utopia's governance duplicate pairs (synthetic), against the
  lab's identity truth. Compare accuracy, ECE and cost with gpt-4o's merges. J2b-addr suggests this
  is the platform's biggest near-term saving.
- **End to end:** an agent (the blind reader) gathers the evidence, and the hybrid engine decides.
  This drops J1's perfect-retrieval assumption, and it's the real comparison with the reader arms.
- **laya:** the same J1/J2 questions through a local laya adapter, if the user approves the
  install.
- **Ledger:** put the J3 answers on the grading list.

## Cost

| | Cost |
|---|---|
| Claude, J3-R | $3.96 |
| Jev, J1 + J2 + smoke | about $0.024 |
| Utopia | none: read-only, no ingestion |
| OpenAI | none |
