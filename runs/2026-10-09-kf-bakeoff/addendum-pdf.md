# Addendum: the PDF round with Docling (pre-registration, 2026-10-09)

**The question.** Design partners will hand BlueLeaf PDFs, not Markdown. Does Docling recover the
facts the OWM needs from a PDF of the same documents? That means the text, the tables (pricing
exceptions, the SLA targets, the authority matrix) and the org charts' nesting, which encodes
reporting lines. And does extraction on Docling's output score as well as on the source?

Registered before any PDF is parsed. The Markdown bake-off's own results were not yet seen when
this was written.

## Setup (`pdf_round.py`)

1. **Render:** each of the 25 documents (front matter stripped) goes from Markdown to standalone
   HTML with pandoc, then to PDF with headless Chrome. Nested lists keep their indentation and
   tables stay tables. Rendering is deterministic; the PDFs are rebuilt in the scratchpad, not
   committed.
2. **Parse:** Docling's `DocumentConverter` (default PDF pipeline), exported to Markdown.
3. **Fidelity, with no model:**
   - **gold surfaces:** the share of the 84 gold facts whose value text appears in Docling's
     output (100% in the source by construction);
   - **tables:** data rows recovered as Markdown table rows, against the source tables;
   - **nesting:** of the org charts' indented list items, how many keep a nesting level.
4. **Extraction on Docling's output:** the baseline pipeline and langextract, unchanged (same
   model, instructions and examples). Scored against the same gold by value, with grounding
   measured against Docling's text.

## Predictions

| # | Prediction | Why |
|---|---|---|
| R1 | **Docling keeps at least 95% of gold surfaces** | Text PDFs rendered from HTML, not scans |
| R2 | **At least 90% of table data rows come back as table rows** | Docling's table model on clean, ruled tables |
| R3 | **Org-chart nesting is partly lost: under 80% of indented items keep a level** | PDF list indentation is visual. Docling's list-level recovery is the weak point |
| R4 | **Extraction recall on Docling's output is within 5 points of the Markdown run** for dates, bands, caps and exception or guarantee terms, and **at least 15 points lower for reports_to** | It follows from R1 and R3 |

## Cost

Docling runs locally ($0). The two extraction pipelines on the new text cost about $1–3 at
Haiku rates.
