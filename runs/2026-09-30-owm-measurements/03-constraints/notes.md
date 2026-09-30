# Item 3: organizational constraints, flagged rather than fixed (2026-09-30)

`check.py` is a deterministic checker over the foundation's own `reports to` facts: read-only SQL on
Utopia's database, no model calls, nothing written back. It reconstructs each graph **at a record
time**: a fact is live at T if it was recorded by T and not invalidated by T. That is how the small
KB's "as ingested" state is recovered after its curation. It emits conflict records that **keep the
evidence**, with status `REQUIRES_REVIEW`. Rules were fixed in `../plan.md` before running. Output:
`results.json` (every edge, its truth class, the flags) and `table.md`.

**The constraints (PRD-3 §5.5 / §9), declared in `check.py`:**
- **C1** `reports_to` is acyclic.
- **C2** each person has at most one live manager.
- **C3** the manager's role rank is at least the subordinate's.

Ranks come from a declared title table: individual contributors (AE, sales engineer, finance
manager and the like) 1, VP Sales and Director of Finance 2, CRO 3. A person's role is read from
their `is <title>` fact. **Coverage** (reported, not a conflict): someone below the top rank with
no manager.

## Results

| Snapshot | Record time | `reports_to` edges | correct / inverted / other | conflicts C1 / C2 / C3 | defective edges flagged | correct edges flagged | titled people with no manager |
|---|---|---|---|---|---|---|---|
| small base, as ingested | 2026-09-28 20:00 UTC | 13 | 0 / **13** / 0 | 0 / 2 / 11 | **13 / 13** | 0 / 0 | 10 of 13 |
| small base, now (corrected + curated) | now | 6 | 6 / 0 / 0 | 0 / 0 / 0 | 0 / 0 | **0 / 6** | 6 of 13 |
| scale base, as ingested (before curation) | 2026-09-29 13:40 UTC | **0** | — | 0 / 0 / 0 | — | — | **25 of 26** |
| scale base, now (curated) | now | 43 | 43 / 0 / 0 | 0 / 0 / 0 | 0 / 0 | **0 / 43** | 1 of 26 |

**Every prediction held.**
- The as-ingested small graph is flagged completely: every inverted line trips C3, C2, or both.
  Michael Torres "has 8 managers" and Elena Novak "has 4", because their reports were stored as
  their managers. No correct line was flagged in any snapshot: 0 of 49.
- The scale graph before curation has **nothing to conflict with**. The org chart produced no
  reporting lines at all, so the finding is coverage, not conflict: 25 of 26 people with a title
  have no manager.
- There are no cycles anywhere. An inverted tree is still a tree, so C1 alone would have caught
  none of this; the **rank** constraint did the work.

## An example conflict record

```json
{"constraint": "C3 rank", "fact_id": "01a0e787-b9c1-7b40-8196-10ef8f29ee7e",
 "claim": "David Morgan (chief revenue officer) reports to Michael Torres (vp sales)",
 "evidence": {"document": "organization_chart.md", "quote": "**Michael Torres** — VP Sales"},
 "status": "REQUIRES_REVIEW"}
```

**The preserved evidence is itself informative.** The quote the extractor attached is a list line that
says nothing about who reports to whom. A reviewer shown the conflict *with its evidence* can see the
extraction misread the indentation. That is the argument for flagging over fixing: the silent
"correction" a reader made at small scale (a VP doesn't report to an AE) would have hidden it.

## Limits

- **The coverage heuristic has one false alarm:** Elena Novak (Director of Finance) is a root in the
  org chart, with no manager in the truth either. "Everyone below CRO has a manager" is not an
  organizational fact here. Coverage rules need the same governed status as constraints.
- **The rank table and the title-to-role mapping are declared by hand.** They are organizational
  knowledge, and in BlueLeaf they would be governed OWM content, not code.
- Two KBs, one relation. The checker reads open-layer phrases (`reports to`, `is`); a typed ontology
  would make it independent of wording.
