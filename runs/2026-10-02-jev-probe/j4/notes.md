# J4: Jev against gpt-4o on Utopia's duplicate queue (2026-10-02)

Pre-registered in `../plan-2.md` (commit `de1e073`). Read-only against Utopia.

- **Population:** the scale base KB's 22,759 duplicate pairs that carry a governance decision.
  Every decision is gpt-4o's, and none has precedents.
- **Labels:** 21,661 pairs (95%) resolve to lab objects on both sides (`build_pairs.py`). The
  corpus it resolves against is byte-identical to what Utopia ingested (six CSV sha256 match).
- **Sample, as pre-registered:** 1,445 pairs:
  - every labelled merge (215 applied, 1 proposed);
  - every "unsure" (151) and proposed keep (78);
  - 1,000 random applied keeps.
- **Jev's input:** the adjudicator's own view (name, type, also-known-as, top four facts),
  rebuilt as of the decision.
- **Jev's question:** neutral. Jev did not get Utopia's 5,200-character identity rulebook.

## A reconstruction bug, found and fixed before reporting

The first run gave **every merged pair an empty side**. Merges are recorded about 30 ms *before*
their decision row, so "facts as of the decision" treated the merge as already done. The
merged-away side lost its facts. gpt-4o had seen both sides before merging.

On that wrong input, Jev nearly tied gpt-4o (158 false merges against 161).

`build_pairs.py` now rebuilds each view as of just before the merge. Both runs' engine calls are in
`engine-calls.jsonl`. **The results below are from the corrected run.**

## Results (`results.md`)

| On 1,445 labelled pairs | gpt-4o (Utopia governance) | Jev (`jev-1.13.0`) |
|---|---|---|
| merged | 215 | 11 |
| **false merges** | **161** | **3** |
| missed merges | 2 | 0 |
| routed to a person | 230 | 279 (19%) |
| **right when it acted** | 1,052/1,215 (**86.6%**) | 1,163/1,166 (**99.7%**) |
| ECE on P(same) | — | **0.043** |
| cost | ≈ $1.31 (estimate) | **$0.030** (measured) |

**By stratum:**

| Stratum | n | gpt-4o | Jev |
|---|---|---|---|
| pairs gpt-4o merged | 215; 54 truly the same | merged all 215 (161 wrong) | merged 11 (8 right), kept 1, **routed 203** |
| pairs gpt-4o routed | 230; 1 truly the same | routed all | **decided 208, all right**; routed 22 |
| random applied keeps | 1,000; 2 truly the same | kept all (missed 2) | kept 946, all right; routed 54, including both true matches |

**Excluding composite "SO-n C-m" names (995 pairs):**

| | false merges | missed merges | right when acting |
|---|---|---|---|
| gpt-4o | 3 | 2 | 826/831 |
| Jev | **0** | **0** | **892/892** |

## Against the predictions

1. **"At least 10% of gpt-4o's merges are false":** held. **161 of 215 (75%)**. Excluding the
   composites, 3 of 57 (5%).
2. **"Jev makes fewer false merges":** held. **3 against 161** (0 against 3 excluding composites).
3. **"Jev routes at most 20%":** held, just: 19.3%.
4. **"Jev's ECE ≤ 0.10":** held: 0.043.
5. **"Jev's cost under 1% of gpt-4o's": failed.** It came to 2.3%, about 44× cheaper.
   - Jev bills about 490 input tokens per call. That includes its own question overhead: a
     near-empty state billed 343 in the smoke test.
   - gpt-4o's batched prompt is about 200 tokens per pair.

## What gpt-4o merged wrongly

- **158 orders merged into customers.** The extractor named order entities "SO-n C-m", for example
  "SO-5004 C-2007", and governance merged them into the customer "C-m".
  - The two sides usually carry visibly different kinds of facts. "C-2007" has customer facts
    (DUNS number, bill-to postal code). "SO-5004 C-2007" has order facts (status, order value).
  - gpt-4o's stated reason: "A name with a prefix removed is usually the same thing abbreviated."
- **3 more:**
  - NS-500-EQU and NS-500-SOF (two background products), each merged into the NS-500 Industrial
    Controller;
  - DR-7089 merged with DR-7008 (two different discount requests).
- **The sample holds 215 of the 226 merges governance applied in this KB. So the scale graph
  carries about 160 order→customer merges.** That is an upstream finding for Utopia. It has not
  been filed.

## What Jev did instead

- **It routed what it couldn't tell apart.** Of the 215 pairs gpt-4o merged, Jev was unsure about
  203 and sent them to a person, 46 true matches included. It merged 11, at low-to-moderate
  confidence.
- **Its three false merges are composites decided at confidence 0.50–0.57,** just over the gate.
- **It cleared gpt-4o's escalations.** Of the 230 pairs gpt-4o routed to a person, Jev decided 208,
  every one of them correctly.
- **The cost of zero false merges is human review.** Jev auto-merged only 8 of the 54 true matches
  among gpt-4o's merges. That is the trade Utopia's own rule 4 asks for: "a wrong merge is far more
  damaging than leaving two records separate".

## Exploratory (not pre-registered)

- **A one-line code rule**, "an order id never merges with a customer id", would cut gpt-4o's false
  merges from **161 to 12**, keeping all 54 correct merges. It cuts Jev's from 3 to 0.
  - Entities in this KB are untyped (`type_id` is null), so nothing stops a cross-kind merge.
  - A typed ontology, or this rule, is foundation work. It is "keep code in control" again.
- **A stricter merge threshold for Jev** (confidence ≥ 0.6, from the asymmetric cost) would remove
  its three false merges.

## Limits

- **Labels come from a name resolver.** It covers 95% of the queue. Pairs it can't resolve, or
  where a name is ambiguous, are left out.
- **The composite labels ("an order, not the customer") rest on the extraction.** The order facts
  on most composites support that reading. The results are reported with composites excluded as
  well.
- **The rebuilt fact lines approximate `entity_fact_lines` at the time.** The other entity's name
  is today's, and the "why paired" line is not rebuilt.
- **gpt-4o's cost is estimated:** characters ÷ 4, at an assumed list price of $2.50 / $10 per
  million tokens. Utopia logs usage only to a terminal.
- **One run of Jev.** Its variance between repeat calls was small in J2.
- **Cost counts the corrected run only** (1,445 calls, 712,331 input tokens). The recording also
  holds the first, flawed run's calls.
