# E2E: the agent retrieves, the hybrid engine decides (T1 + T2 transcripts)

## Evidence set: seen

- retrieval sufficient: **102/102**
- hybrid strict pass: **102/102**, against the readers' own **93/102**
- unsafe: **0**
- governing policy found in the set: 102/102
- when retrieval was insufficient (0): hybrid outcomes {}

| reader \ hybrid | pass | partial | fail |
|---|---|---|---|
| **pass** | 93 | 0 | 0 |
| **partial** | 0 | 0 | 0 |
| **fail** | 9 | 0 | 0 |

## Evidence set: read

- retrieval sufficient: **87/102**
- hybrid strict pass: **21/102**, against the readers' own **93/102**
- unsafe: **0**
- governing policy found in the set: 21/102
- when retrieval was insufficient (15): hybrid outcomes {'REQUEST_EVIDENCE': 15}

| reader \ hybrid | pass | partial | fail |
|---|---|---|---|
| **pass** | 21 | 9 | 63 |
| **partial** | 0 | 0 | 0 |
| **fail** | 0 | 6 | 3 |

Hybrid misses (arm, scenario, outcome, missing documents) × count:

- ('T1', 'S01', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md',)) × 2
- ('T1', 'S01', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md', 'acme_pricing_exception.md')) × 1
- ('T1', 'S02', 'REQUEST_EVIDENCE', ()) × 2
- ('T1', 'S02', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md',)) × 1
- ('T1', 'S03', 'REQUEST_EVIDENCE', ()) × 3
- ('T1', 'S04', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md',)) × 2
- ('T1', 'S04', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md', 'acme_pricing_exception.md')) × 1
- ('T1', 'S09', 'REQUEST_EVIDENCE', ()) × 1
- ('T1', 'S09', 'REQUEST_EVIDENCE', ('acme_pricing_exception_2023.md',)) × 2
- ('T1', 'S10', 'REQUEST_EVIDENCE', ()) × 1
- ('T1', 'S11', 'REQUEST_EVIDENCE', ()) × 3
- ('T1', 'S12', 'REQUEST_EVIDENCE', ()) × 1
- ('T1', 'S13', 'REQUEST_EVIDENCE', ()) × 3
- ('T1', 'S15', 'REQUEST_EVIDENCE', ()) × 3
- ('T1', 'S16', 'REQUEST_EVIDENCE', ()) × 2
- ('T1', 'S17', 'REQUEST_EVIDENCE', ()) × 3
- ('T1', 'S18', 'REQUEST_EVIDENCE', ()) × 1
- ('T1', 'S18', 'REQUEST_EVIDENCE', ('acme_pricing_exception_2023.md',)) × 2
- ('T1', 'S19', 'REQUEST_EVIDENCE', ()) × 1
- ('T1', 'S20', 'REQUEST_EVIDENCE', ()) × 1
- ('T1', 'S20', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md', 'acme_pricing_exception.md')) × 1
- ('T1', 'S20', 'REQUEST_EVIDENCE', ('acme_pricing_exception.md',)) × 1
- ('T2', 'S01', 'REQUEST_EVIDENCE', ()) × 2
- ('T2', 'S02', 'REQUEST_EVIDENCE', ()) × 1
- ('T2', 'S02', 'REQUEST_EVIDENCE', ('acme_master_supply_agreement.md',)) × 2
- ('T2', 'S03', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S04', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S05', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S09', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S10', 'REQUEST_EVIDENCE', ()) × 1
- ('T2', 'S11', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S12', 'REQUEST_EVIDENCE', ()) × 2
- ('T2', 'S13', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S14', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S15', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S16', 'REQUEST_EVIDENCE', ()) × 1
- ('T2', 'S17', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S18', 'REQUEST_EVIDENCE', ()) × 3
- ('T2', 'S19', 'REQUEST_EVIDENCE', ()) × 1
- ('T2', 'S20', 'REQUEST_EVIDENCE', ()) × 3

