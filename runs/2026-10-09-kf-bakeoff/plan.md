# Knowledge-foundation bake-off: langextract vs Semantica vs a baseline (pre-registration, 2026-10-09)

**The question.** BlueLeaf will build its own first-party knowledge foundation, because design
partners asked for it, using Docling and langextract for document understanding and fact
extraction with source references. Semantica (`docs/semantica-evaluation-2026-10-09.md`) offers
another extraction path. On the same documents, with the **same model** and **the same
instructions**, which extracts the facts the OWM needs more completely and accurately? Which ties
each fact to its source text, and does either add value over a plain structured call? The user's
go: "Run all the tests you would like", 2026-10-09.

## Setup

- **Model:** Claude Haiku 4.5 for every pipeline, through the `claude` CLI (`claude_cli.py`).
  Calls are blind and cached in `calls.jsonl`, so a re-run replays without spend.
- **Isolated environment:** Semantica 0.7.0 and langextract 1.7.1 in a scratch virtualenv. The
  lab's dependencies are untouched (`adapters.py` holds the two thin model adapters).
- **Documents:** all 25 base-corpus documents, **YAML front matter stripped** (a parsed PDF has
  none). Docling isn't exercised: the corpus is already Markdown. A PDF round is a follow-up.
- **The same instructions** (`bakeoff.py: INSTRUCTION`) define eight predicates: approval_limit,
  effective_from, effective_to, reports_to, has_title, maximum_discount, guarantee_amount,
  credit_cap. Each tool gets them in its own idiom:
  - **langextract:** the prompt description, plus one few-shot example on a made-up "Zephyr" text
    (it requires examples). Its own chunking (1,000 characters) and source alignment.
  - **Semantica:** `TripletExtractor(method="llm", triplet_types=[each predicate with its
    definition], include_provenance=True)`. Its prompt and parsing are its own.
  - **Baseline:** one call per document returning a JSON array of facts, each with a quote. The
    span comes from finding the quote in the text.

## Gold (`gold.json`; built before any extraction, no model)

**84 facts in 16 documents**, from the OWM register's structured terms (truth-derived, and checked
against each text at registration) and the HR export. A fact is kept only if its value appears in
the stripped body as written.

| Predicate | n | From |
|---|---|---|
| approval_limit | 17 | Pricing policies 2025–2027, credit policies 2025–2026, the authority matrix |
| credit_cap | 4 | Credit policies |
| effective_from / effective_to | 13 / 9 | Registered governing documents (not the holiday calendar, whose start date appears only as a holiday) |
| maximum_discount | 2 | Pricing exceptions |
| guarantee_amount | 1 | The parent guarantee |
| has_title / reports_to | 21 / 17 | The two org charts (reporting lines shown by indentation) |

## Measures

- **Recall:** gold facts matched, out of 84.
- **Precision:** matched facts over facts of the eight predicates extracted from the 16 gold
  documents.
  - Matching rules: dates by ISO value; amounts and percentages by number; titles and names by
    normalised containment.
  - A correct fact the gold lacks counts against precision. Those are listed and reviewed in the
    notes.
- **Native span accuracy:** the tool's own character span contains the fact's value. Only
  langextract has native spans; the baseline's comes from its quote.
- **Locatable:** the value appears verbatim in the document. This applies to every pipeline, as a
  post-hoc grounding bound.
- **Inferred person-level authority:** an approval_limit whose subject is a person rather than a
  title. The documents never state one, so any is an inference.
- **Cost:** in dollars.

## Predictions (fixed before any extraction)

| # | Prediction | Why |
|---|---|---|
| K1 | **langextract native span accuracy ≥ 90%** | Its alignment step grounds each extraction in the source |
| K2 | **Semantica has no native spans**; locatable ≥ 80% | Its triples carry no character offsets (smoke test on a made-up text) |
| K3 | **Recall:** baseline ≥ 0.85; langextract ≥ 0.75; **Semantica < langextract** | The baseline sees the whole document; langextract's 1,000-character chunks can split context; Semantica's generic triple prompt is weakest on typed facts |
| K4 | **Org-chart reporting lines:** langextract's reports_to recall < the baseline's | Chunking can cut the indentation that encodes reporting |
| K5 | **Precision ≥ 0.85** for all three | Typed predicates and explicit-only instructions |
| K6 | **At most 2 inferred person-level authority claims** across all three | The instruction forbids inference |
| K7 | **Each pipeline ≤ $3** | Haiku, 25 short documents |

## Limits, stated before the run

- **One synthetic corpus, in Markdown, and one model** (Haiku). PDF parsing (Docling) isn't
  tested here.
- **Each tool runs in its documented default shape,** plus our adapter. Tuning (langextract's
  chunk size or passes, Semantica's methods) could change the ranking.
- **The gold is the register's terms and the HR export.** Facts outside the eight predicates
  aren't scored.
