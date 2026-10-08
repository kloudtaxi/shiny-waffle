# G-18: hybrid identity routing (2026-10-08)

> **Status: done on I2's data; all six predictions held.** Two-judge agreement (R2) sent
> **0.79% and 0.94%** of pairs to a person, against I2's 4.36% and 3.85%. It made **zero false and
> zero missed merges** on both knowledge bases, and no threshold was tuned on this data. Letting Opus
> decide the band (R1) halved the review load again, to 0.40% and 0.50%, but missed one true match
> in each KB. Both misses were the same pair, and the cause is a naming convention, not a lack of
> intelligence. **Not fresh data:** stage 2 needs a new-seed ingest, which waits for the user.
> Opus cost **$10.99**.

The plan is in `plan.md` (pre-registered, e830d40, before any band answer). The code is
`run_hybrid.py`; the full tables are in `results.md`. The answers are in `answers.jsonl` (1,051
distinct inputs) and `answers-repeat.jsonl` (100 repeats).

## Results

| Arm | base: to a person | false / missed | replication: to a person | false / missed |
|---|---|---|---|---|
| I2 as pre-registered (Jev + guard) | 945 (4.36%) | 0 / 0 | 768 (3.85%) | 0 / 0 |
| **R2: act only when Opus agrees with Jev's lean** | **171 (0.79%)** | **0 / 0** | **188 (0.94%)** | **0 / 0** |
| **R1: Opus decides the band** | **87 (0.40%)** | 0 / **1** | **99 (0.50%)** | 0 / **1** |
| *Keep bar 0.3, Jev only (tuned on this data)* | *205 (0.95%)* | *0 / 0* | *192 (0.96%)* | *0 / 0* |
| *R2 on the 0.3 band (tuned)* | *154 (0.71%)* | *0 / 0* | *141 (0.71%)* | *0 / 0* |
| *R1 on the 0.3 band (tuned)* | *70 (0.32%)* | *0 / 1* | *52 (0.26%)* | *0 / 1* |

Rows in italics use the keep bar found on this data in I2, so they aren't confirmatory.

## Predictions

| # | Prediction | Result |
|---|---|---|
| P1 | R1 false merges ≤ 3 on each KB | **0 and 0** ✓ |
| P2 | R1 isn't safe alone: missed merges ≥ 1 on each KB | **1 and 1** ✓ |
| P3 | R1 person share between 0.1% and 1.5% | **0.40% and 0.50%** ✓ |
| P4 | R2 false merges = 0 on each KB | **0 and 0** ✓ |
| P5 | R2 person share < 1.0% on each KB | **0.79% and 0.94%** ✓ (the replication is close to the bar) |
| P6 | Opus repeatability ≥ 90% | **95/100** ✓ |

**G-18's success criterion is met.** R2 sent under 1% to a person, with zero false and zero missed
merges, on both KBs.

## What it shows

1. **A second judge cuts human review about fivefold with no errors.**
   - R2 sends people 8–9 pairs per 1,000 candidates instead of 38–44.
   - Nothing was tuned here: the band is I2's pre-registered point, and the rule is "two judges
     agree".
   - **The caveat:** R2's zero missed merges is partly by construction. On these labels, Jev's
     `different` lean is never wrong about a true pair.
2. **Letting Opus decide halves the load again, and the one miss is a convention.**
   - R1's only miss, in both KBs, is "Ballard LLC" ~ "Ballard, Lee and Powers" (ERP customer C-2083
     and its CRM account).
   - The generator builds the ERP name by cutting the CRM name at the first comma and adding a
     legal suffix (`background.py`). Opus answered "different", reasoning that "a single-name LLC
     versus a three-partner firm" are two companies. That's sensible without the convention.
   - So the residual error is **organizational knowledge, not intelligence**: this company's ERP
     drops partners' names. An OWM could hold that as an identity convention. A bigger model
     can't know it.
   - **Product read:** a missed merge leaves a duplicate (recoverable); a false merge corrupts
     records. R1 trades one duplicate per ~20,000 pairs for half the review load. It's a reasonable
     opt-in, with R2 as the safe default.
3. **Opus is a far better band judge than gpt-4o with Utopia's identity rulebook.** On the same
   945 / 768 pairs:

   | | Opus | gpt-4o |
   |---|---|---|
   | False merges | **0 / 0** | 11 / 10 |
   | True matches kept apart silently | **1 / 1** | 53 / 44 |
   | Sent to a person | 87 / 99 | 16 / 10 |

   Opus says "unsure" when the records are thin, and gpt-4o decides anyway.
4. **Ranking keeps people's time short.** Sorting R2's person queue by Jev's P(same), the first 100
   items hold **82 of 85** and **73 of 75** true matches, and the first 200 hold all of them.
5. **Opus's flips are in the safe direction.** All 5 changed answers on the second ask moved
   between "different" and "unsure". None went between "same" and "different", so a flip moves a
   pair between *keep* and *person*, never towards a merge. All 5 pairs are truly different.

## Cost

- **Opus:** $10.99 (1,051 inputs plus 100 repeats; about $0.009 each). **Jev:** nothing new; all
  answers are recorded from I2 ($0.62 then).
- **Per candidate pair** over all 41,617: about **$0.00026** of Opus, because Opus sees only about
  4% of pairs. Opus on every pair would cost about $283 (30,446 distinct inputs × $0.0093). The
  band cost $10.04, about **3.5%** of that; Jev narrows the rest.
- **ROI framing** for the product: human reviews per 1,000 candidate pairs drop from about 41 to
  about 9 (R2) or 4–5 (R1), at about a quarter of a cent per 10 pairs.

## Limits

- **Not fresh data.** The band and its composition were known from I2; only Opus's answers are new.
  **Stage 2:** a new-seed scale dataset ingested into Utopia, with the frozen rules (R2 default,
  R1 opt-in) applied unchanged. That needs about 95 minutes of ingest and OpenAI spend (the project
  hit its limit last time). It waits for the user's go.
- **The two KBs share most content;** the replication is not independent.
- **Opus judged Utopia's rendering** of the records (its extracted names and facts). A first-party
  foundation would render different records, and the band would change.
- **One synthetic company and one naming convention family.** Real data will have more
  conventions, and the share Opus can't resolve will differ.

## Possible next steps (not run)

- **Conventions arm (exploratory).** Give the band judge the organization's identity conventions
  as OWM-held rules, and see whether R1's miss closes without new errors.
  - To avoid the designer writing the answer (G-39), derive each convention from evidence, not
    from the generator. For example, F02's "Acme Mfg. Holdings is Acme Manufacturing" shows the
    ERP-name pattern.
  - Cost: about $10.
- **Stage 2** (above), the confirmatory version.
