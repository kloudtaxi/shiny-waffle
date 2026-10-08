# G-18: hybrid identity routing (pre-registration, 2026-10-07)

**The question (G-18, an ROI item).** At I2's operating point, identity made 0 wrong merges in
about 41,600 pairs, but it sent 4.4% (base) and 3.8% (replication) of pairs to a person. Can a
second judge on that band cut the share people review to **under 1%**, with **zero false merges
and zero missed merges**, without tuning anything on this data?

The idea comes from Hu's Jev entity-resolution test (reading list,
`docs/reading-list-notes-2026-10-07.md`): Jev first, a frontier model on the uncertain band, and
a person for what's left.

## Data (I2's, unchanged)

- The labelled pairs of both scale knowledge bases (`../2026-10-02-jev-probe/i2/local/`):
  - **base:** 21,661 pairs, 108 truly the same;
  - **replication** (missing-contract): 19,956 pairs, 93 truly the same.
- Jev's committed answers (`judged-*.csv.gz`).
- **The band is I2's pre-registered operating point:**
  - the guard (two id-named sides of different kinds are kept apart);
  - merge when Jev says `same` at ≥ 0.9;
  - keep when Jev says `different` at ≥ 0.5;
  - route the rest.

  That's **945** base pairs and **768** replication pairs, **1,051** distinct inputs across both.

**What the band holds** (known before this plan; Jev's lean × truth):

| Jev's lean in the band | base: truly same / different | replication: truly same / different |
|---|---|---|
| `different` (confidence < 0.5) | 0 / 772 | 0 / 610 |
| `unsure` | 84 / 67 | 74 / 63 |
| `same` (confidence < 0.9) | 21 / 1 | 19 / 2 |

The band's true matches are name variants that need organizational knowledge to resolve:
- legal-suffix variants ("Smith Inc LLC" ~ "Smith Inc"; 24 and 23 "Holdings" pairs);
- product short codes ("NS-EDGE" ~ "NS-Edge Monitoring Package");
- people.

## The second judge

- **Model:** Opus 5.5 (`claude-opus-5-5`), through headless `claude -p`. Each call runs in a fresh
  temporary directory outside the repo, with no tools, no MCP and one turn.
- **Input:** exactly what Jev saw (name, type, also-known-as, facts as of the decision time), with
  Jev's question and criteria word for word.
- **Output:** JSON `{"answer": same | different | unsure, "reason": …}`. An unparsable reply counts
  as `unsure`.
- **No confidence is asked for.** Verbalized confidence isn't calibrated.
- **Each distinct input is asked once.** Opus has never seen these pairs: the cost probe used 3
  pairs outside the band (`probe.jsonl`).
- **Repeatability:** a fixed random 100 of the inputs (seed 20261007) are asked a second time.

## Arms

All arms come from the same answers. Decisions are merge, keep, or **person**.

| Arm | Rule | Status |
|---|---|---|
| `jev` | I2 as pre-registered: the band goes to a person | Reference |
| **R1** | Opus decides the band: `same` → merge, `different` → keep, `unsure` → person | **Primary** (Hu's pattern) |
| **R2** | Act only when Opus **agrees** with Jev's lean in the band; otherwise a person | **Primary** (two-judge agreement) |
| `jev-low`, `r1-low`, `r2-low` | The same rules with keep bar 0.3 | **Not confirmatory.** 0.3 was found on this data (I2's exploratory note) |

**What R2 gets by construction here.** On these labels Jev's `different` lean is never wrong about
a true pair. So R2 can't miss a merge, and R2 always sends Jev's `unsure` pairs to a person: at
least 151 (0.70%) and 137 (0.69%). The prediction is about what Opus adds on top.

## Predictions (fixed before any band answer exists)

| # | Prediction | Why |
|---|---|---|
| P1 | **R1 false merges ≤ 3 on each KB** | Opus separates different order and CRM numbers well (probe: 3/3) |
| P2 | **R1 is not safe on its own: missed merges ≥ 1 on each KB** | Some true variants ("X Holdings" ~ "X") look like different legal entities to a careful judge without the organization's naming conventions |
| P3 | **R1 person share between 0.1% and 1.5% on each KB** | Sparse records invite `unsure`; Opus is decisive on clear id pairs |
| P4 | **R2 false merges = 0 on each KB** | A false merge needs both judges wrong in the same direction |
| P5 | **R2 person share < 1.0% on each KB** (at least 0.70% / 0.69% by construction) | Opus agrees with Jev's `different` lean on nearly all of the 772 / 610 |
| P6 | **Opus repeatability ≥ 90%** identical answers on the 100 repeats | Temperature default; the inputs are short |

**Success for G-18:** R2 meets P4 and P5 on both KBs. That would be under 1% to a person, 0 false
and 0 missed merges, with no threshold tuned on this data. If R1 meets P1 with zero missed merges,
P2 is refuted and R1 is reported as the stronger result.

## Reported alongside

- Opus against gpt-4o (Utopia's governance with its identity rulebook) on the same band.
- R2's person queue ranked by Jev's P(same): how many true matches are in the top 50, 100 and 200.

## Cost and guard

- **Estimate:** about $0.0093 per pair (probe), so about **$10** for 1,051 inputs and about $1 for
  the 100 repeats.
- **Guard:** stop if the first 8 calls average over $0.03 per pair.
- Jev, Utopia and OpenAI: none, because every Jev answer is already recorded.

## Limits, stated before the run

- **Not fresh data.** The band and its composition were known from I2. Opus's answers are new;
  R2's zero-missed property depends on Jev's behaviour on this data. **A fresh confirmation needs a
  new-seed dataset ingested into Utopia.** That's about 95 minutes, plus OpenAI spend that hit the
  project's limit last time. It's stage 2, and it waits for the user's go.
- **The two KBs share most of their content,** so the replication guards against luck, not
  against overfitting.
- **Opus judges the records as rendered by Utopia's extraction.** A first-party foundation would
  render different records.

## Commands

    uv run python runs/2026-10-07-identity-hybrid/run_hybrid.py ask
    uv run python runs/2026-10-07-identity-hybrid/run_hybrid.py repeat
    uv run python runs/2026-10-07-identity-hybrid/run_hybrid.py score
