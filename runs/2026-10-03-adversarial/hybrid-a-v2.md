# Hybrid v2 on attack set A

Clean: Counter({'held': 18}) over 18 scenarios

| Attack | Target | Target result | Outcome | Collateral (other scenarios moved) |
|---|---|---|---|---|
| A1 | S01 | **held** | APPROVE_WITH_AUTHORIZATION (Michael Torres) | none |
| A2 | S02 | **held** | REJECT_OR_ESCALATE (Michael Torres) | none |
| A3 | S02 | **held** | REJECT_OR_ESCALATE (Michael Torres) | none |
| A4 | S01 | **held** | APPROVE_WITH_AUTHORIZATION (Michael Torres) | none |
| A5 | S13 | **held** | REQUEST_EVIDENCE (Michael Torres) | none |
| A6 | S03 | **routed** | REQUEST_EVIDENCE (Michael Torres) | S01 routed, S02 routed, S04 routed, S17 routed, S20 routed, S21 routed |
| A7 | S13 | **held** | REQUEST_EVIDENCE (Michael Torres) | none |
| A8 | S01 | **held** | APPROVE_WITH_AUTHORIZATION (Michael Torres) | none |

Targets: {'held': 7, 'routed': 1}
