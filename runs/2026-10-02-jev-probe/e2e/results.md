# E2E: the agent retrieves, the hybrid engine decides (T1 + T2 transcripts)

## Evidence set: seen

- retrieval sufficient: **102/102**
- hybrid strict pass: **102/102**, against the readers' own **93/102**
- unsafe: **0**
- governing policy found in the set: taken from truth
- when retrieval was insufficient (0): hybrid outcomes {}

| reader \ hybrid | pass | partial | fail |
|---|---|---|---|
| **pass** | 93 | 0 | 0 |
| **partial** | 0 | 0 | 0 |
| **fail** | 9 | 0 | 0 |

## Evidence set: read

- retrieval sufficient: **87/102**
- hybrid strict pass: **94/102**, against the readers' own **93/102**
- unsafe: **0**
- governing policy found in the set: taken from truth
- when retrieval was insufficient (15): hybrid outcomes {'APPROVE_WITH_AUTHORIZATION': 2, 'REJECT_OR_ESCALATE': 3, 'REQUEST_EVIDENCE': 7, 'REVIEW_REQUIRED': 1, 'APPROVE': 2}

| reader \ hybrid | pass | partial | fail |
|---|---|---|---|
| **pass** | 85 | 0 | 8 |
| **partial** | 0 | 0 | 0 |
| **fail** | 9 | 0 | 0 |

Hybrid misses (arm, scenario, outcome, missing documents) × count:

- ('T1', 'S01', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md', 'acme_pricing_exception.md')) × 1
- ('T1', 'S04', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md', 'acme_pricing_exception.md')) × 1
- ('T1', 'S09', 'REQUEST_EVIDENCE', ('acme_pricing_exception_2023.md',)) × 2
- ('T1', 'S18', 'REQUEST_EVIDENCE', ('acme_pricing_exception_2023.md',)) × 2
- ('T1', 'S20', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md', 'acme_pricing_exception.md')) × 1
- ('T1', 'S20', 'REVIEW_REQUIRED', ('acme_pricing_exception.md',)) × 1

