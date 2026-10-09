# Knowledge-foundation bake-off: langextract vs Semantica vs a baseline (2026-10-09)

> **Status: done, Markdown and PDF rounds. On clean text, extraction quality doesn't separate the
> three: all find 98–100% of the gold facts. They differ in source grounding, in cost, and in the
> one thing none of them does well, structure.**
> - **langextract** gives native character spans at the baseline's cost ($0.35).
> - **The plain baseline** (one structured call per document, with quotes) is as accurate
>   ($0.42).
> - **Semantica** has no spans and costs about 6–7× more ($2.45), extracting 249 facts against
>   97 to find the same ones.
> - **Reporting lines carried by indentation** can't be grounded in a span, and all three made the
>   same prior-driven error (Elena Novak "reports to" the CRO).
> - **After a PDF round trip through Docling,** text and tables survive 100% but the nesting is
>   gone: reporting-line recall falls from 16 to 3.
> - Cost: **$4.10** in all (231 Haiku calls), plus $0.02 for a smoke test on a made-up text.

The plan is in `plan.md` (pre-registered, 130637b) and `addendum-pdf.md` (f32c860), both before any
extraction or parse. The code: `bakeoff.py`, `pdf_round.py`, `adapters.py`, `claude_cli.py`. The data:
- `gold.json`;
- `out/*.json` (each pipeline's facts, Markdown and PDF);
- `results.json`, `pdf-fidelity.json`, `pdf-results.json`;
- `calls.jsonl` (every model call; a re-run replays it for $0);
- `env.txt` (package versions).

## Results, Markdown round (84 gold facts, as pre-registered)

| Pipeline | Recall | Precision | Native span contains the value | Value locatable in source | Person-level authority claims | Cost |
|---|---|---|---|---|---|---|
| **langextract** 1.7.1 | 0.976 (82) | 0.943 | 0.471 | 1.0 | 0 | **$0.35** |
| **Semantica** 0.7.0 | 0.988 (83) | 0.933 | **none (no spans)** | 1.0 | 0 | **$2.45** |
| **Baseline** (one call per document) | 0.988 (83) | 0.954 | 0.759 (from its quotes; 9 of 97 quotes not verbatim) | 1.0 | 0 | $0.42 |

**Reviewing the misses and "false positives"** (by hand, after scoring):
- **A gold error.** "Michael Torres reports to David Morgan" in the support org chart isn't stated
  there: the two appear in a contacts table with no reporting line. The gold builder added a line
  whenever both names appeared in a chart. All three pipelines rightly omitted it. **Corrected
  gold: 83 facts.** Corrected recall: langextract 0.988, Semantica 1.0, baseline 1.0.
- **Correct facts the gold lacks,** in every pipeline: Laura Whitfield is the guarantor's CFO, and
  David Morgan is CRO (from the exception's approval line).
- **Ambiguous:** the org chart's "as of 2026-09-01", read as an effective date (all three).
- **Real errors:**

  | Pipeline | Wrong facts | What |
  |---|---|---|
  | Baseline | 1 | "Elena Novak reports to David Morgan" |
  | langextract | 2 | the same, plus "VP Sales: $500,000" read as an approval limit (it's the concurrence threshold) |
  | Semantica | 3 | the same, plus the SLA documents' service-credit caps (20%, 30%) read as credit-limit caps |

  **Elena Novak is a top-level entry** in the org chart. Every pipeline inferred the CRO as her
  manager: a structural fact supplied from the prior, not the page.

**Span grounding by predicate** (exploratory; "the span contains the subject or the object"):
- langextract and the baseline each ground **66 of 70 facts (94%)**, excluding reporting lines.
- **0 of 17 reporting lines** in either. A reporting line encoded by indentation has no single
  stating span.
- The pre-registered measure (the span contains the *object*) undercounts langextract. It anchors
  `has_title` spans on the person's name, which is correct but leaves out the title.

## Results, PDF round (Docling 2.135.0 on PDFs rendered from the same documents)

| Fidelity | Kept |
|---|---|
| Gold values present in Docling's text | **100%** (84/84) |
| Table data rows recovered as table rows | **100%** (65/65, across 12 documents) |
| Org-chart items keeping a nesting level | **0%** (0/13). Docling flattens the nested list into one level. The text still says "Indentation shows who reports to whom" |

| Extraction on Docling's text | Recall | Precision | reports_to | Every other predicate |
|---|---|---|---|---|
| Baseline | 0.833 | 0.959 | **3** of 17 (16 on Markdown) | identical to the Markdown round |
| langextract | 0.833 | 0.933 | **3** of 17 (16 on Markdown) | identical to the Markdown round |

PDF extraction cost $0.87. No OCR engine was installed: born-digital PDFs only, no scans.

## Predictions

| # | Prediction | Result |
|---|---|---|
| K1 | langextract native span accuracy ≥ 90% | **Missed as measured: 0.471.** Exploratory: 94% excluding reporting lines (subject or object in span); reporting lines 0/17 |
| K2 | Semantica has no native spans; locatable ≥ 80% | **Held:** no spans; locatable 100% |
| K3 | Recall: baseline ≥ 0.85; langextract ≥ 0.75; Semantica < langextract | **Partly:** the first two held; Semantica *matched or beat* langextract (0.988 against 0.976) |
| K4 | langextract's reports_to recall < the baseline's | **Missed:** both 16 |
| K5 | Precision ≥ 0.85 for all three | **Held** (0.93–0.95) |
| K6 | At most 2 person-level authority claims | **Held:** 0 |
| K7 | Each pipeline ≤ $3 | **Held:** $0.35, $2.45, $0.42 |
| R1 | Docling keeps ≥ 95% of gold values | **Held:** 100% |
| R2 | ≥ 90% of table rows recovered | **Held:** 100% |
| R3 | < 80% of nested items keep a level | **Held:** 0% |
| R4 | Extraction on Docling within 5 points of Markdown except reports_to, which drops ≥ 15 points | **Held:** identical elsewhere; reports_to 16 to 3 |

## What it shows (for BlueLeaf's first-party knowledge foundation)

1. **Extraction isn't the differentiator; grounding and cost are.**
   - With one capable model and clear instructions, a single structured call per document finds as
     much as either framework.
   - langextract's value is **native character spans at no extra cost**, the basis for the
     byte-range citations design partners want.
   - Semantica's extraction adds nothing here and costs 6–7× more.
   - **Docling + langextract stays the right choice. Semantica's extractor isn't needed.**
2. **Structure must come from systems of record, not documents.**
   - Reporting lines are the one fact type every pipeline struggled with. They can't be grounded
     in a span, all three supplied the same wrong manager from the prior, and a PDF round trip
     erases them entirely.
   - The OWM's design already resolves authority from the HR export plus the policy's bands. This
     result says to keep it that way, and to treat org charts in documents as evidence to check,
     never as the source.
3. **Docling is reliable on born-digital PDFs.** It kept text and tables exactly. Its known weak
   spot is list nesting; scanned documents (OCR) are untested.

## Limits

- **One synthetic corpus and one model** (Haiku 4.5). The tools ran with documented defaults plus
  our adapters. Tuning (langextract's chunking or passes, Semantica's prompt) could move the
  numbers.
- **The gold is the register's terms and the HR export,** filtered to what the body states. One
  gold error was found and corrected after scoring (above); both numbers are reported.
- **PDFs were rendered from HTML,** so they're cleaner than real-world scans or forms.
