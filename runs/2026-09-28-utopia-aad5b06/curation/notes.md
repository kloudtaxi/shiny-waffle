# Curation arm (2026-09-28)

**Question:** do answers move if the *facts* are fixed rather than identity? Graph-only B2
is rerun after curating what extraction got wrong or missed. It uses the same blind reader,
prompt and questions as `../arm-b`, and n = 3.

## What was curated

Everything comes from each KB's own corpus. The script is `curate.py`; the log is
`curation_log.jsonl`; the before-and-after state is in `snapshot/` (RDF plus
`curated-facts.txt`).

| Fix | Source document | Base | Missing-contract |
|---|---|---|---|
| Reject the inverted `reports to` edges (manager → report) | organization_chart.md | 13 | 13 |
| Push the correct reporting lines: Sarah, Kelly, Anthony, Zachary → Michael; Michael → David; Priya → Elena (doc_time 2026-09-01) | organization_chart.md | 6 | 6 |
| Push approval bands on the policy entities, valid for the calendar year: 2025 (AE ≤ 15%, VP > 15%) and 2026 (AE ≤ 10%, VP > 10% ≤ 20%, CRO > 20%) | pricing_policy_2025/2026.md | 5 | 5 |
| Push exception values: 15% (2025-04-01 to 2028-03-31) and 10% (2023-04-01 to 2025-03-31), on each exception and on Acme | acme_pricing_exception*.md | 4 | — (the corpus lacks them) |

Totals: live facts 267 → 269 (base) and 264 → 262 (missing-contract). Entities are
unchanged at 149 and 175.

**Not curated:**

- Reporting edges for the seven background staff with duplicate entities (Glenn Hayes, Misty
  Peterson, Courtney Barron, Bryan Rivera, Robert Hernandez, Shari Brown, Stephanie
  Romero). Their inverted edges were rejected and no replacement was pushed: a statement
  naming an ambiguous entity makes Utopia mint a new one.
- Dates on roles, and the source-system ids (C-1001, CRM-2048, ACME-MFG-2025). The source
  gives no role start dates; the ids are identity, not facts.

## How writing back to Utopia actually works

1. **The Statements contract can't say which entity it means.** It takes names only (`e`:
   `[name, kind word, named]`) and refuses any other key. A pushed name is a *claim*
   (ADR 0041).
2. **Exact names don't guarantee attachment.** The one-statement pilot ("Sarah Chen reports
   to Michael Torres") created **new** Sarah Chen and Michael Torres entities and queued each
   pair for a human, at match scores of 0.52 and 0.54. In the full push, most names attached
   to the existing entities directly. Sarah and Michael became new entities again in
   missing-contract, and the agent auto-merged "Zachary Brown" into his email entity (0.95).
   The one outcome guaranteed is that the pair gets reviewed.
3. **So curating facts means curating identity too.** Each new entity was confirmed in Review
   (`curate.py resolve`: exactly one same-named pre-existing entity, or skip and report). The
   pushes also raised two *new* candidate pairs in base: Acme Mfg. Holdings ≟ Acme Industrial
   Supply Co. (0.77), and EXC-ACME-NS500-10 ≟ NS-500 Industrial Controller (0.65). Both were
   answered *keep*, so the hourly agent can't auto-merge them.
4. **A reject is a retraction, not a delete.** It sets `invalidated_at`, and reads before
   that moment still show the fact. There's no un-reject route.
5. **Withdrawing the pushes:** push `deleted: true` for each `external_id` (Utopia marks the
   documents "Not in source"), then delete them in the Library.

**For the OWM:** an OWM that writes back to the foundation (decisions, curated facts) can't
address entities by id through the push contract. Every write-back becomes an identity
review. So either the write path needs an id slot, or the OWM keeps its own model and treats
the foundation as read-only evidence. This run's evidence favours the second.

## Results: graph-only B2 on the curated graph, n = 3

The runs are in `arm-b/r1..r3/B2`, started 21:18 UTC, with the same blind setup; every run
saw 9 tools with 0 denials. Tokens `northstar-curated-r1..3` are revoked. Cost $2.21 + $2.34
+ $2.26; turns 162 + 172 + 164.

| B2 on… | S01 | S02 | S03 | S04 | S05 | S06a | S06b | S06c | S07 | S08 | ✓ / ◐ / ✗ | turns | cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pre-correction (×3) | ◐ | ✓ | ◐ | ✓✓✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 6/4/0, 6/4/0, 5/4/1 | 240–248 | $2.99–3.19 |
| corrected (×3) | ✗ | ✗✗◐ | ◐ | ✗ | ◐ | ✓ | ✓ | ✓ | ✓ | ◐ | 4/3/3, 4/3/3, 4/4/2 | 218–238 | $2.71–2.88 |
| **curated (×3)** | **✓** | **✓** | ◐ | **✓** | **✗** | ✓ | ✓ | ✓ | ✓ | ◐ | **7/2/1 ×3** | **162–172** | **$2.21–2.34** |

Grades are provisional (Claude's first read). A single mark means all three runs agreed.

### What moved, and why

1. **Authority is fixed.** S01, S02 and S04 are right in all 9 runs, and on S01 every run names
   Michael Torres (VP Sales) as the approver. The bands and exception values now come
   straight from `entity_facts`. No run needed the `changes` dig on an authority question (0
   of 9), and it didn't matter. Curated runs took 27–32% fewer turns and 19–26% less spend than the
   uncurated B2 runs (vs corrected and pre-correction respectively).
   **The gap was missing facts, not reader reasoning.**
2. **S05 went the wrong way.** In the missing-contract KB the reader now answers "yes, with
   Michael Torres's approval" in 3 of 3 runs, and never asks whether the contract behind the
   request exists. Uncurated, it declined in 3 of 3 (◐). The graph now holds complete
   *authority* facts and, correctly, no *eligibility* facts. Nothing in it says that approval
   requires established eligibility, so the reader decided on authority alone. B1 (with
   text) got S05 right because the request row's "Contract pricing per Acme MSA" and the
   hearsay sent it looking for the contract. In the graph, DR-9001 has "no details on
   record".
3. **S03 is unchanged (◐).** The exception's NS-500-only scope holds in every run; the
   framing is "needs VP sign-off" where the answer key says review. That matches B1.
4. **S08 is unchanged (◐).** The ids were not curated.

### For the OWM

- **Facts are necessary, and they aren't the decision.** The discount procedure (doc 03 §11:
  check the active contract, then the exception, *then* authority), and the rule that a
  decision needs its evidence, are not facts any foundation holds. With them missing, a more
  complete graph produced a more confident wrong answer. That's the OWM's "honest failure"
  capability (`owm/owm-spec.md` #5), shown by its absence.
- **Adding facts can make answers worse.** S05 regressed exactly where the curation (rightly)
  added nothing. An OWM needs a regression eval over the scenarios on every foundation
  change, and this run is one.
- **Write-back is an identity review** (see above). That argues for an OWM that keeps its own
  model and reads the foundation as evidence.
