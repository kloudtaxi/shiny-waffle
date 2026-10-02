# I2: customer matching on the whole duplicate queue (2026-10-02)

Pre-registered in `../plan-3.md` (commit `01f16c8`). J4 measured a 1,445-pair sample; I2 runs on
every labelled pair in two KBs and picks an operating point by the rule fixed beforehand.

**Code:** `run.py`. Pairs are labelled and rebuilt by `../j4/build_pairs.py` (`label_all`, with
the merge-time fix). Jev answers J4's question unchanged.
**Outputs:** `results.md` (the full sweep) and `judged-{base,missing-contract}.csv.gz` (one row per
pair: names, truth label, gpt-4o's decision, Jev's answer). The recording and the pair files are
large, so they stay in `local/` (gitignored).

## Populations

| KB | Pairs with a governance decision | Labelled by the resolver | Truly the same |
|---|---|---|---|
| Scale base | 22,759 | 21,661 | 108 |
| Scale missing-contract (replication) | 20,071 | 19,956 | 93 |

Unlabelled pairs have a side the resolver cannot tie to a corpus row. They are left out, as in J4.

## Results at the chosen operating point

The rule, applied on the base KB, picked **τ = 0.9**: it is the only threshold with zero false
merges. The same τ was then applied, unchanged, to the replication.

| | gpt-4o (Utopia governance) | Jev + guard, τ = 0.9 |
|---|---|---|
| **Base:** false merges | **161** | **0** |
| Base: missed merges (kept apart, silently) | 53 | 0 |
| Base: routed to a person | 230 (1.1%) | 945 (4.4%) |
| Base: true matches merged automatically | 54 of 108 | 3 of 108 |
| **Replication:** false merges | **158** | **0** |
| Replication: missed merges | 44 | 0 |
| Replication: routed to a person | 202 (1.0%) | 768 (3.8%) |
| Replication: true matches merged automatically | 48 of 93 | 0 of 93 |

The full sweep (τ from 0.5 to 0.9) is in `results.md`.

## Predictions

| # | Prediction | Result |
|---|---|---|
| 1 | Base: at most 3 false merges at τ = 0.5; zero at the chosen τ | **1** at τ = 0.5; **0** at τ = 0.9 ✓ |
| 2 | Routed at the chosen τ is at most 10% | **4.4%** ✓ |
| 3 | Replication at the same τ: false merges at most 0.05%, routed at most 10% | **0%** and **3.8%** ✓ |
| 4 | gpt-4o makes more than 100 false merges on each KB | **161** and **158** ✓ |

All four held.

## What it shows

- **No wrong merges, in about 41,600 pairs across two KBs.** gpt-4o's governance made 319 wrong
  merges on the same pairs. It also kept 97 true matches apart, and nobody reviews those.
- **The guard does most of the safety work, and it is one line of code.** "An order is never a
  customer" decided 1,628 base pairs and 1,571 replication pairs, and none of them is a true match.
  Among those pairs are 149 and 148 of gpt-4o's false merges, over 90% of them. With the guard and
  nothing else, gpt-4o's false merges drop to 12 and 10.
- **What got past the guard was two different orders for one customer.** The only false merges at
  τ ≤ 0.8 were pairs such as "SO-5463 C-2134" vs "SO-5082 C-2134", where Jev said "same" at
  0.82–0.86. A second rule would close this: two ids of the same kind that differ are different
  things. This is exploratory and was not pre-registered.
- **The price of zero wrong merges is people's time.** At τ = 0.9, Jev merges almost nothing
  automatically: 3 of 108 true matches on the base KB and 0 of 93 on the replication. Every other
  true match is routed to a person. The design is "Jev narrows, people confirm", not "Jev merges".

## Exploratory, not pre-registered

These were computed after seeing both KBs. Each one needs its own pre-registration before anyone
relies on it.

- **Most of the routed load is low-confidence "different".** Of the 945 routed base pairs, Jev
  said "different" on 772, "unsure" on 151 and "same" on 22. On these labels it never said
  "different" about a true pair, at any confidence. Lowering the keep bar from 0.5 to 0.3 cuts the
  routed load from 945 to 205 (base) and from 768 to 192 (replication), with no missed merges.
- **Ranking the routed queue works.** Sorted by Jev's P(same), the first 100 routed base pairs
  hold 82 of the 105 routed true matches, and the first 200 hold 104. The replication gives 84
  of 93 and 93 of 93. So a reviewer working down the list finds nearly all the matches in the first
  couple of hundred items.

Together, these suggest an operating point of about 1% routed, with zero false and zero missed
merges. They were found on the same data they would be judged on, though, so this is a hypothesis
for the next pre-registration, not a result.

## Cost

- **Jev:** 29,012 new calls and 14.7M input tokens, about **$0.62**. The plan estimated about
  $0.90. The rest of the 41,617 pairs were answered from the recording: J4's 1,445 calls, plus
  pairs whose inputs were identical in both KBs.
- **gpt-4o** spent its share when Utopia ingested the KBs. I2 adds nothing to it.
- **Claude, Utopia and OpenAI:** none. All database access was read-only SQL.

## Limits

- **One synthetic company.** The id prefixes (`SO-`, `C-`, …) are what make the guard possible.
  Real data needs typed entities, or a typed id field, for the same rule to apply. That points at
  the ontology (entity kinds), not at Jev.
- **The labels come from the lab's resolver,** which is sha256-checked against the corpus. Pairs it
  cannot label (about 5% and 0.6%) are not measured.
- **The two KBs share most of their content.** The replication guards against a lucky τ. It is not
  independent data.
- **One run per pair.** Jev's repeatability was not measured here (see the small add-ons in
  `docs/next-experiments-2026-10-02.md`).
