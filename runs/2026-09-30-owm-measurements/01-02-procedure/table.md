| Scenario | expected | v1 in prompt (baseline) | T1: v1 via tool | T2: v2 via tool |
|---|---|---|---|---|
| S01 | APPROVE_WITH_AUTHORIZATION | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S02 | REJECT_OR_ESCALATE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S03 | REVIEW_REQUIRED | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S04 | APPROVE | ✓✓✓ | ✓✓✗ | ✓✓✓ |
| S05 | REQUEST_EVIDENCE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S09 | REJECT_OR_ESCALATE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S10 | APPROVE_WITH_AUTHORIZATION | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S11 | APPROVE_WITH_AUTHORIZATION | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S12 | APPROVE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S13 | REQUEST_EVIDENCE | ✗✗✗ | ✗✗✗ | ✓✓✓ |
| S14 | APPROVE | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| S15 | REQUEST_EVIDENCE | — | ✗✗✗ | ✓✓✓ |
| S16 | APPROVE | — | ✓✓✓ | ✓✓✓ |
| S17 | REVIEW_REQUIRED | — | ✓✓✓ | ✓✓✓ |
| S18 | APPROVE | — | ✓✓✓ | ✓✗✗ |
| S19 | APPROVE | — | ✓✓✓ | ✓✓✓ |
| S20 | REJECT_OR_ESCALATE | — | ✓✓✓ | ✓✓✓ |
| **passes** | | **30/33** | **44/51** | **49/51** |

T1: get_procedure called in 51/51 answers · turns 10–29 · cost $12.75

T2: get_procedure called in 51/51 answers · turns 10–29 · cost $13.33
