# Semantica's deduplication on Northstar's labelled identity pairs (2026-10-09)

> **Status: done. Out of the box, Semantica 0.7.0 would merge 18,402 distinct records on the base
> KB (17,564 on the replication).** That's about 85% of the 21,661 lookalike pairs, against
> gpt-4o's 161 and Jev with the guard's 0.
> - The errors are **same-type lookalike ids** that differ by a digit ("DR-7813" against
>   "DR-7013", "CRM-3092" against "CRM-3096"). So its type check doesn't help.
> - **No threshold is safe:** at 0.9 it makes 0 false merges but finds 4 of 108 true duplicates
>   (5 of 93 on the replication).
> - 2 of 4 predictions held, and the 2 misses are in the "worse than predicted" direction. No
>   model calls; cost $0.

The plan is in `plan.md` (pre-registered, 158ca0b). The code is `dedup.py`; the results are in
`results.json`.

## Results (the library's own `detect_duplicates`, at its defaults)

| | Base: false merges | Base: missed | Replication: false merges | Replication: missed |
|---|---|---|---|---|
| **Semantica D0** (records as extracted) | **18,402** | 3 | **17,564** | 1 |
| **Semantica D1** (typed from id prefixes) | 18,402 | 3 | 17,564 | 1 |
| gpt-4o (Utopia governance) | 161 | 53 | 158 | 44 |
| Jev + guard (I2) | 0 | 0 (4.4% routed) | 0 | 0 (3.8% routed) |
| R2, two-judge agreement (G-18) | 0 | 0 (0.79% routed) | 0 | 0 (0.94% routed) |

**The false merges by kind** (base, D1):

| Kind | False merges |
|---|---|
| Request with request | 7,548 |
| Customer with customer | 4,840 |
| Order with order | 2,972 |
| Untyped names | 2,482 |
| Product with product | 560 |

**The threshold sweep** (D1, base; replication in `results.json`):

| Threshold | False merges | Missed (of 108) |
|---|---|---|
| 0.5–0.6 | about 19,300 | 0 |
| 0.7 (default) | 18,491 | 3 |
| 0.8 | 11,642 | 82 |
| 0.9 | 0 | 104 |
| 0.95 | 0 | 108 |

**Why the scores run high.** Semantica's similarity is 0.6 × string + 0.2 × property + 0.2 ×
relationship:
- the string score is high for sequential ids (0.94 for "DR-7813" against "DR-7013");
- two records with **no properties score a perfect 1.0** on properties;
- relationships default to a neutral **0.5**.

So "CRM-3092" against "CRM-3096" scores 0.87, above the 0.7 default.

## Predictions

| # | Prediction | Result |
|---|---|---|
| Q1 | D0 makes more than 100 false merges on each KB | **Held**, by two orders of magnitude: 18,402 and 17,564 |
| Q2 | D0 misses more than 20 true matches on each KB | **Missed:** 3 and 1. It merges almost everything, so it rarely misses |
| Q3 | D1 cuts D0's false merges by over 80% | **Missed:** no change. The errors are same-type, so a type check can't remove them |
| Q4 | No threshold reaches 0 false merges with at most 10 missed (base) | **Held:** the first zero-false-merge threshold (0.9) misses 104 of 108 |

## What it shows

1. **Fuzzy matching on enterprise identifiers is unsafe.** Sequential ids look alike by
   construction. Semantica's defaults merge requests, customers and orders that merely share a
   numbering scheme.
2. **The type check isn't enough.** Every false merge is same-type. I2's exploratory second rule,
   "two ids of the same kind that differ are different things", is what this needs. Better still
   is the judge-plus-routing design G-18 measured.
3. **For BlueLeaf:** don't adopt Semantica's deduplication as an identity authority. Its
   similarity could at most generate candidates, behind the OWM's guard, judge and routing. For
   the pitch: *an open-source stack's default deduplication would have merged 18,402 distinct
   records in this company. BlueLeaf's identity layer merged none wrongly and sent under 1% to a
   person.*

## Limits

- **The pairs are Utopia's candidates:** lookalikes by construction, the hard cases
  deduplication exists to handle. On random pairs, the rates would be far lower.
- **Defaults only.** No embedding model was configured (Semantica's similarity can add one), and
  no blocking or clustering beyond pairwise decisions. Clustering would add *transitive* merges
  on top.
- **The sweep re-applies the library's rule** to the similarity and confidence it computes. It
  matches the library on all but 89 of 21,661 base pairs (62 of 19,956), probably a prefilter.
  The headline counts are the library's own decisions.
