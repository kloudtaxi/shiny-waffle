# Set C (literal filenames): v1 and v2 credit engines

| Attack | Target | Engine | Target result | Gated outcome | Collateral (moved) |
|---|---|---|---|---|---|
| C2 | S29 | v1 python | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S28 APPROVE_WITH_AUTHORIZATION (held); S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval) |
| C2 | S29 | v1 yaml | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S28 APPROVE_WITH_AUTHORIZATION (held); S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval) |
| C2 | S29 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| C2 | S29 | v2 yaml | **routed** | REQUEST_EVIDENCE | S28 REQUEST_EVIDENCE (routed) |
| C2 | S29 | v2 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| C3 | S32 | v1 python | **unsafe: wrong denial** | REJECT_OR_ESCALATE | none |
| C3 | S32 | v1 yaml | **unsafe: wrong denial** | REJECT_OR_ESCALATE | none |
| C3 | S32 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | none |
| C3 | S32 | v2 yaml | **held** | REQUEST_EVIDENCE | S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed) |
| C3 | S32 | v2 agent | **held** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| C4 | S30 | v1 python | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v1 yaml | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v1 agent | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v2 yaml | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v2 agent | **held** | REJECT_OR_ESCALATE | none |
| C5 | S31 | v1 python | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v1 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v1 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v2 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v2 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v1 python | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v1 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v1 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v2 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v2 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |

| Engine | Targets held | routed | unsafe | Collateral unsafe | Collateral routed |
|---|---|---|---|---|---|
| v1 python | 3 | 0 | 2 | 1 | 0 |
| v1 yaml | 3 | 0 | 2 | 1 | 0 |
| v1 agent | 3 | 0 | 2 | 1 | 0 |
| v2 yaml | 4 | 1 | 0 | 0 | 3 |
| v2 agent | 4 | 1 | 0 | 0 | 11 |
