# Semantica's deduplication on Northstar's labelled identity pairs (pre-registration, 2026-10-09)

**The question.** Semantica would merge entities with its `DuplicateDetector` (fuzzy similarity
≥ 0.7, confidence ≥ 0.6, no review tier). On the same 41,617 labelled pairs where I2 and G-18
measured identity, what would it merge wrongly, and what would it miss? This is commercially
direct: a buyer comparing an open-source stack with BlueLeaf will ask. The user's go: "Run all
the tests you would like", 2026-10-09.

## Setup

- **Data:** I2's labelled pairs, both scale KBs (`../2026-10-02-jev-probe/i2/local/pairs-*.jsonl`):
  - **base:** 21,661 pairs, 108 truly the same;
  - **replication:** 19,956 pairs, 93 truly the same.

  Each side is what Utopia's governance saw: name, type, also-known-as and facts.
- **The library:** Semantica 0.7.0 in the isolated environment. Each pair is decided by
  `DuplicateDetector(similarity_threshold=0.7, confidence_threshold=0.6).detect_duplicates([a,
  b])`. Duplicate means merge; anything else means keep. Semantica has no routing tier.
- **Entities:**
  - `id`;
  - `name`;
  - `aliases` (also-known-as);
  - `type`, which depends on the arm;
  - `properties`: the facts, keyed by relation.

| Arm | Types | What it asks |
|---|---|---|
| **D0** | Utopia's own types. Almost all are "untyped", which is passed as no type | Semantica's defaults on the records as extracted |
| **D1** | Types derived from id prefixes: SO- is an order, DR- a request, CRM- and C- customers, EMP- an employee, PROD- a product. This is the knowledge behind I2's one-line guard | Does Semantica's type check do what our guard did? |
| **Sweep** | D1, similarity threshold from 0.5 to 0.95 | The best Semantica can do without a review tier |

**Reference points** (base / replication):

| | False merges | Missed merges | Routed to a person |
|---|---|---|---|
| gpt-4o (Utopia governance) | 161 / 158 | 53 / 44 | — |
| Jev + guard (I2) | 0 / 0 | 0 / 0 | 4.4% / 3.8% |
| R2, two-judge agreement (G-18) | 0 / 0 | 0 / 0 | 0.79% / 0.94% |

## Predictions (fixed before any pair is scored)

| # | Prediction | Why |
|---|---|---|
| Q1 | **D0 makes more than 100 false merges on each KB** | Fuzzy names: "SO-5463 C-2134" against "SO-5082 C-2134", or "CRM-3118" against "CRM-3137" |
| Q2 | **D0 misses more than 20 true matches on each KB** | Name variants such as "Ballard LLC" against "Ballard, Lee and Powers", or "NS-EDGE" against "NS-Edge Monitoring Package" |
| Q3 | **D1 cuts D0's false merges by over 80%, but not to 0** | The type check removes cross-type merges; same-type ids that differ (CRM-3118, CRM-3137) remain |
| Q4 | **No threshold in the sweep reaches 0 false merges with at most 10 missed merges on base** | With no judge and no review tier, there's no safe operating point |

## Cost

None: no model calls, local CPU only.
