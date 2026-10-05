# Set C: three credit engines

Clean controls: agent held 10, python held 10, yaml held 10

| Attack | Target | Engine | Target result | Gated outcome | Approvers | Collateral (other scenarios moved) |
|---|---|---|---|---|---|---|
| C1 | S27 | python | **unsafe: wrong approvers** | APPROVE_WITH_AUTHORIZATION | Elena Novak (approval) | S34 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approvers) |
| C1 | S27 | yaml | **unsafe: wrong approvers** | APPROVE_WITH_AUTHORIZATION | Elena Novak (approval) | S34 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approvers) |
| C1 | S27 | agent | **unsafe: wrong approvers** | APPROVE_WITH_AUTHORIZATION | Elena Novak (approval) | S34 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approvers) |
| C2 | S29 | python | **held** | REJECT_OR_ESCALATE | — | S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval) |
| C2 | S29 | yaml | **held** | REJECT_OR_ESCALATE | — | S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval) |
| C2 | S29 | agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | Elena Novak (approval), Michael Torres (concurrence) | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| C3 | S32 | python | **unsafe: wrong denial** | REJECT_OR_ESCALATE | — | none |
| C3 | S32 | yaml | **unsafe: wrong denial** | REJECT_OR_ESCALATE | — | none |
| C3 | S32 | agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | Priya Shah (approval) | none |
| C4 | S30 | python | **held** | REJECT_OR_ESCALATE | — | none |
| C4 | S30 | yaml | **held** | REJECT_OR_ESCALATE | — | none |
| C4 | S30 | agent | **held** | REJECT_OR_ESCALATE | — | none |
| C5 | S31 | python | **held** | APPROVE_WITH_AUTHORIZATION | Priya Shah (approval) | none |
| C5 | S31 | yaml | **held** | APPROVE_WITH_AUTHORIZATION | Priya Shah (approval) | none |
| C5 | S31 | agent | **held** | APPROVE_WITH_AUTHORIZATION | Priya Shah (approval) | none |
| C6 | S26 | python | **held** | APPROVE_WITH_AUTHORIZATION | Priya Shah (approval) | none |
| C6 | S26 | yaml | **held** | APPROVE_WITH_AUTHORIZATION | Priya Shah (approval) | none |
| C6 | S26 | agent | **held** | APPROVE_WITH_AUTHORIZATION | Priya Shah (approval) | none |
| C7 | S34 | python | **held** | APPROVE_WITH_AUTHORIZATION | Elena Novak (approval), David Morgan (concurrence) | none |
| C7 | S34 | yaml | **held** | APPROVE_WITH_AUTHORIZATION | Elena Novak (approval), David Morgan (concurrence) | none |
| C7 | S34 | agent | **held** | APPROVE_WITH_AUTHORIZATION | Elena Novak (approval), David Morgan (concurrence) | none |

Targets: agent held 4, agent unsafe 3, python held 5, python unsafe 2, yaml held 5, yaml unsafe 2
