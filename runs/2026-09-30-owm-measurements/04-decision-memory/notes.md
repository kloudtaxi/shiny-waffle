# Item 4: decision memory with a fair baseline (2026-09-30)

Pre-registered in `prereg.md` (commit `fe41e59`) before any run.

- **Reader:** blind B1n on the uncurated scale base KB, with procedure v2 served by the stand-in.
- **Runs:** n = 3 per arm, 27 answers, 0 errors, every token revoked.
- **Order:**
  1. The 2027 policy was ingested.
  2. Arms (a) and (c) ran.
  3. `decision_log_DEC-2026-0001.md` was ingested.
  4. Arm (b) ran.
- **Scoring:** the rules are in `score.py`'s docstring and are unchanged since pre-registration.

## Results

| Arm | M1 decided? | M2 valid when made? | M3 same request in 2027 | cost |
|---|---|---|---|---|
| **(a)** no memory | ✗✗✗ | ✗✗✗ | ✓✓✓ | $1.66 |
| **(b)** decision as a document in Utopia | ✓✓✓ | ✓✓✓ | ✓✓✓ | $1.81 |
| **(c)** typed decision record (stand-in) | ✗✓✓ | ✓✓✓ | ✓✓✓ | $1.61 |

Per question, as the mean of 3 runs:

| | M1 turns | M1 source reads | M1 cost | M2 turns | M2 source reads | M3 turns |
|---|---|---|---|---|---|---|
| (a) | 6.0 | 3.0 | $0.13 | 7.7 | 3.7 | 17.3 |
| (b) | 5.3 | 2.3 | $0.10 | 9.7 | 6.3 | 17.7 |
| (c) | **3.3** | **0** | **$0.07** | 10.3 | 5.3 | 18.3 |

"Source reads" are `search_chunks` + `get_document`. In (c), M1 was answered with
`find_decisions` → `get_decision` plus one `entity_facts` check, and no document was read.

**The (c) r1 M1 "fail".** The answer's `outcome` was
`"APPROVE_WITH_AUTHORIZATION (approved; 15% discount on NS-500)"`, which is the right value with a
note appended. The pre-registered rule requires the exact value, so it stays a fail. On substance,
(c) is 3/3 on M1. The rule is not changed after the fact.

## Against the predictions

1. **"(a) fails M1 and M2 3/3 by construction, passes M3 3/3":** **held.**
   - All three (a) readers answered `decided: false` or `decision_found: false`, with nulls
     elsewhere. None invented an approver.
   - On M3, all three named the CRO under the 2027 policy. Two hedged that the org chart is dated
     2026-09 ("confirm he is still CRO").
2. **"(c) passes M1 and M2 3/3, with fewer turns and fewer source reads than (b)":** **partly
   held.**
   - Accuracy: M1 is 2/3 by rule (3/3 on substance, see above) and M2 is 3/3.
   - Cost: on M1, (c) is cheaper as predicted, at 3.3 vs 5.3 turns, 0 vs 2.3 source reads and
     $0.07 vs $0.10.
   - **On M2 it is not.** (c) took 10.3 turns against (b)'s 9.7, though it read fewer sources
     (5.3 vs 6.3). M2 asks whether the decision was valid *under the rules then*. Both arms
     re-read the 2026 policy and the org chart to check it, and neither carrier removes that work.
     A record that stated its own validity check would not have to be re-derived, but it would
     have to be trusted.
3. **"(b) passes M1 and M2 at least 2/3":** **held, 3/3 each.** The risk I named, finding one
   document among ~14,000 facts, did not materialize. Search found the decision log in 2–3 reads.
   With one decision in memory this is an easy retrieval; see Limits.
4. **"M3: all arms ≥2/3; any reuse of Michael Torres is the headline":** **held, 9/9.** No arm
   reused the 2026 approver. The readers who had memory used it as **precedent** and said the
   rules had changed. From (c) r1: *"Under the 2027 policy, even VP Sales Michael Torres can only
   approve up to 12%, so this one has to go to the CRO."* The trap did not fire.

## What the predictions did not cover: the document carrier becomes evidence

Uploading the decision as a document did more than make it findable. **Utopia extracted the
decision's conclusions into the graph as facts.** The facts are in `extracted-from-decision-log.tsv`,
captured before the document was deleted. They include:

| subject | predicate | object | validity |
|---|---|---|---|
| Sarah Chen | limit | 10% | **none** |
| Sarah Chen | authorized | no | **none** |
| discount request DR-9001 | outcome | APPROVE_WITH_AUTHORIZATION | none |
| Michael Torres | approved | discount request DR-9001 | 2026-09-24 |

`Sarah Chen limit 10%` is the 2026 policy's band, which an agent derived for one request. In the
graph it became a timeless fact about a person. Under the 2027 policy it is wrong: her limit is 5%.

The (b) readers then used the decision as **evidence**, not only as memory:

- **Two of three (b) M3 answers** cited DEC-2026-0001 for the customer identity
  (CRM-2048 ≡ C-1001).
- Both also listed `decision_log_DEC-2026-0001.md` in their `evidence` array. In r1's words:
  *"I relied on the mapping recorded in last September's decision (DEC-2026-0001) and didn't
  recheck it against the source files."*
- r1 also found the stale fact: *"The knowledge graph still shows Sarah's limit as '10%' from that
  2026 decision; it's out of date for 2027 requests."*

That is **circular provenance**. An agent's conclusion re-enters the foundation as a source that
the next agent relies on without re-checking. Here the conclusion happened to be right, so no
answer was wrong. The mechanism is still the failure: a wrong decision would have been laundered
the same way.

In (c), every M3 reader called `find_decisions` once. **No (c) answer cited the decision record as
evidence** (0 of 3 mention DEC-2026-0001), and all three re-derived identity and authority from the
sources. The typed record stayed a record.

## What it shows

- **Decision memory makes "was it decided, and by whom" answerable at all.** Without it, the
  foundation correctly says "pending" (arm a). That is the naive result, and the reason (b) exists.
- **For retrieval, where the decision lives barely matters at n = 1 decision.** The typed record is
  cheaper on the direct question (about 40% fewer turns, no source reads) and no better on the
  validity question.
- **The difference that does matter is contamination.** A decision stored as a document is
  indistinguishable from evidence:
  - The foundation extracts its derived conclusions as undated facts.
  - Later agents cite it as a source.

  A typed record, served apart from evidence, was consulted as precedent and not cited as a source.
- This supports PRD-3 §21's case for decisions as their own object, on different grounds than
  expected. The case is not "easier to find". It is **"must not be mistaken for evidence"**. For
  BlueLeaf it bears on the provenance principle: a decision record needs a provenance class of its
  own, *derived by an agent under procedure P at version V*. The foundation should not ingest it as
  a primary source. This is an amendment candidate; see the reconciliation doc.
- **Rule change:** memory did not cause stale reuse, 0 of 6 memory-equipped M3 answers. With the
  procedure served and the new policy in the corpus, the readers re-applied the rules.

## Lab fixtures and state changes (disclosed)

- **Fixtures, identical in both carriers:** the decision id DEC-2026-0001, and Michael Torres's
  approval on 2026-09-24. The corpus shows DR-9001 as "Pending Approval".
- **Agent A** is a real run: T2 r1 S01 (`make_record.py`).
- **The 2027 policy is now evidence.**
  - `pricing_policy_2027.md` is in `dataset/evidence/` and in the missing-contract variant.
  - It is ingested only into the scale base KB.
  - The scale missing-contract KB and both small KBs are one document behind the dataset.
- **The decision-log document is deleted** from the scale base KB (`DELETE /documents/…`, 32 facts
  invalidated).
  - Of the 57 facts that cite it, 34 are now invalidated, including every fact in the table above.
  - **The 23 still live are all `known_as` name facts. For 15 of them, the deleted document is
    their only evidence.** Examples: "Decision record DEC-2026-0001" and "discount-approval
    procedure version 478c8c81676c".
  - Document deletion in Utopia does not invalidate alias facts. The residue carries names only and
    no decision content, but a later run on the base KB can find an entity called "Decision record
    DEC-2026-0001". I did not write to Utopia's database to remove it.
- Curation was reapplied after the runs (`toggle_curation.py reapply --apply`, 8 actions; see
  `curation_log.jsonl`).

## Limits

- **One decision in memory.** Whether (b) keeps finding the right decision among hundreds of
  decision documents, as a record store would, is the real retrieval test. It is not run.
- n = 3, one reader model. M2 and M3 tell the reader the date ("Today is 2027-02-01"), which makes
  the rule change easy to notice.
- The contamination finding is observed in 2 of 3 (b) answers, and in the extraction, on one
  document. It is a mechanism shown once, not a rate.
