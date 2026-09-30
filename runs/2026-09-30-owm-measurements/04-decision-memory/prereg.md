# Item 4: decision memory with a fair baseline — pre-registration (2026-09-30)

**Question (PRD-3 §21):** once a decision is made, can a later agent retrieve and correctly use it,
including after the rules change? And does it matter *where* the decision lives: as a typed record
in an OWM, or as a document in the knowledge foundation? A naive test ("save the decision, then ask
about it") beats no memory by construction, so the fair baseline is arm (b).

## The world

- **Truth change (lab extension):** `pricing_policy_2027`, valid 2027-01-01..2027-12-31. Its bands
  are Enterprise AE ≤5%, VP Sales >5%..≤12%, CRO >12%. It is published 2026-09-15, ahead of its
  effective date, as `dataset/evidence/documents/pricing_policy_2027.md`. Facts F19–F21. Oracle
  scenario **S21** (the DR-9001 request again on 2027-02-01): `APPROVE_WITH_AUTHORIZATION`, required
  role **CRO**, approver **David Morgan**. In 2026 the same request was Michael Torres's to approve.
- **Phase 1, agent A:** a real run, T2 r1 S01 (`../01-02-procedure/`: blind B1n, procedure v2 via
  the stand-in). It decided DR-9001 `APPROVE_WITH_AUTHORIZATION`: eligible under
  EXC-ACME-NS500-15, 2026 policy, Sarah not authorized, VP Sales, Michael Torres.
  `make_record.py` carries that decision JSON unchanged into two carriers with **identical
  content**:
  - (c) `decisions.json`, a typed record served by the stand-in's `find_decisions` / `get_decision`;
  - (b) `decision_log_DEC-2026-0001.md`, the same record as a document uploaded into Utopia.
- **Lab fixtures, disclosed:** the decision id DEC-2026-0001, and **Michael Torres's approval on
  2026-09-24**. The corpus's CRM still shows DR-9001 "Pending Approval", so without the fixture
  "who approved it" has no answer. The fixture is the same in both carriers.

## Arms (agent B)

All three use the same reader: blind B1n on the uncurated scale base KB (curation stays withdrawn
from items 1–2), procedure v2 served by the stand-in, n = 3, the same questions (`questions.tsv`).
The 2027 policy document is ingested into the base KB **before any arm runs**.

| Arm | Decision memory | How |
|---|---|---|
| **(a)** | none | the foundation as it is: DR-9001 is "Pending Approval" in the CRM |
| **(b)** | the decision **as a document** in the foundation | `decision_log_DEC-2026-0001.md` uploaded to the base KB **after** (a) and (c) have run |
| **(c)** | the decision **as a typed record** | stand-in `--standin-decisions decisions.json` (`find_decisions`, `get_decision`) |

## Questions

- **M1:** was DR-9001 decided, and if so: outcome, approver, policy, eligibility basis?
- **M2** (today = 2027-02-01): was the decision valid under the rules in force when it was made?
- **M3** (today = 2027-02-01): the same request now, with its CRM record: S21. **The trap**: a
  memory-equipped reader that reuses the 2026 approver (Michael) instead of applying the 2027 policy
  (CRO) fails.

Scoring rules are in `score.py`'s docstring, fixed before any run. Also recorded per answer: turns,
cost, source-document reads (`search_chunks`, `get_document`) and decision-tool calls.

## Predictions, stated before any run

1. **(a) fails M1 and M2 in 3/3 each, by construction.** The evidence says pending, and no approval
   exists. It passes **M3 in 3/3** (reconstruction from the 2027 policy). This row is the floor, not
   a competitor.
2. **(c) passes M1 and M2 in 3/3**, with fewer turns and fewer source reads than (b).
3. **(b) passes M1 and M2 in at least 2/3.** Finding one decision document among ~14,000 facts is
   the risk.
4. **M3:** all arms pass at least 2/3. **Any M3 failure that reuses Michael Torres as the approver is
   the headline result**: memory applied without re-checking the rules.

**Cost:** 27 reader answers (~$9). Utopia gpt-4o: two small documents ingested (the 2027 policy and
the decision log), a few cents.
