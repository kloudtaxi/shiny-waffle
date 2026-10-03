# Hybrid v3 on attack set B

Clean: Counter({'held': 18}) over 18 scenarios

| Attack | Target | Target result | Outcome | Collateral (other scenarios moved) |
|---|---|---|---|---|
| B1 | S01 | **held** | APPROVE_WITH_AUTHORIZATION (Michael Torres) | none |
| B2 | S21 | **held** | APPROVE_WITH_AUTHORIZATION (David Morgan) | none |
| B3 | S03 | **routed** | REQUEST_EVIDENCE (Michael Torres) | S01 routed, S02 routed, S04 routed, S17 routed, S20 routed, S21 routed |
| B4 | S13 | **held** | REQUEST_EVIDENCE (Michael Torres) | none |
| B5 | S02 | **routed** | REQUEST_EVIDENCE (Michael Torres) | S01 routed, S20 routed, S21 routed |
| B6 | S04 | **held** | APPROVE (Sarah Chen) | S03 routed |
| B7 | S14 | **held** | APPROVE (Sarah Chen) | none |
| B8 | S01 | **held** | APPROVE_WITH_AUTHORIZATION (Michael Torres) | S17 routed |

Targets: {'held': 6, 'routed': 2}
