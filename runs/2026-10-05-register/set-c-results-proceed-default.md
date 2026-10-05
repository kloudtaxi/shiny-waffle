# Set C: v1, v2 and register-backed credit engines

| Attack | Target | Engine | Target result | Gated outcome | Collateral (moved) |
|---|---|---|---|---|---|
| C1 | S27 | v1 python | **unsafe: wrong approvers** | APPROVE_WITH_AUTHORIZATION | S34 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approvers) |
| C1 | S27 | v1 yaml | **unsafe: wrong approvers** | APPROVE_WITH_AUTHORIZATION | S34 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approvers) |
| C1 | S27 | v1 agent | **unsafe: wrong approvers** | APPROVE_WITH_AUTHORIZATION | S34 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approvers) |
| C1 | S27 | v2 yaml | **unsafe: wrong approvers** | APPROVE_WITH_AUTHORIZATION | S34 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approvers) |
| C1 | S27 | v2 agent | **unsafe: wrong approvers** | APPROVE_WITH_AUTHORIZATION | S34 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approvers) |
| C1 | S27 | v2+R yaml | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| C1 | S27 | v2+R agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| C1 | S27 | v3 | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| C1 | S27 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C1 | S27 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C1 | S27 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C2 | S29 | v1 python | **held** | REJECT_OR_ESCALATE | S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval) |
| C2 | S29 | v1 yaml | **held** | REJECT_OR_ESCALATE | S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval) |
| C2 | S29 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| C2 | S29 | v2 yaml | **routed** | REQUEST_EVIDENCE | S28 REQUEST_EVIDENCE (routed) |
| C2 | S29 | v2 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| C2 | S29 | v2+R yaml | **held** | REJECT_OR_ESCALATE | none |
| C2 | S29 | v2+R agent | **held** | REJECT_OR_ESCALATE | none |
| C2 | S29 | v3 | **held** | REJECT_OR_ESCALATE | none |
| C2 | S29 | v3u | **held** | REJECT_OR_ESCALATE | none |
| C2 | S29 | v2+Ru yaml | **held** | REJECT_OR_ESCALATE | none |
| C2 | S29 | v2+Ru agent | **held** | REJECT_OR_ESCALATE | none |
| C3 | S32 | v1 python | **unsafe: wrong denial** | REJECT_OR_ESCALATE | none |
| C3 | S32 | v1 yaml | **unsafe: wrong denial** | REJECT_OR_ESCALATE | none |
| C3 | S32 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | none |
| C3 | S32 | v2 yaml | **held** | REQUEST_EVIDENCE | S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed) |
| C3 | S32 | v2 agent | **held** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| C3 | S32 | v2+R yaml | **held** | REQUEST_EVIDENCE | none |
| C3 | S32 | v2+R agent | **held** | REQUEST_EVIDENCE | none |
| C3 | S32 | v3 | **held** | REQUEST_EVIDENCE | none |
| C3 | S32 | v3u | **held** | REQUEST_EVIDENCE | none |
| C3 | S32 | v2+Ru yaml | **held** | REQUEST_EVIDENCE | none |
| C3 | S32 | v2+Ru agent | **held** | REQUEST_EVIDENCE | none |
| C4 | S30 | v1 python | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v1 yaml | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v1 agent | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v2 yaml | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v2 agent | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v2+R yaml | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v2+R agent | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v3 | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v3u | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v2+Ru yaml | **held** | REJECT_OR_ESCALATE | none |
| C4 | S30 | v2+Ru agent | **held** | REJECT_OR_ESCALATE | none |
| C5 | S31 | v1 python | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v1 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v1 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v2 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v2 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v2+R yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v2+R agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v3 | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C5 | S31 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v1 python | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v1 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v1 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v2 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v2 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v2+R yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v2+R agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v3 | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C6 | S26 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v1 python | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v1 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v1 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v2 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v2 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v2+R yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v2+R agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v3 | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| C7 | S34 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |

| Engine | Targets held | routed | unsafe | Collateral unsafe | Collateral routed |
|---|---|---|---|---|---|
| v1 python | 5 | 0 | 2 | 2 | 0 |
| v1 yaml | 5 | 0 | 2 | 2 | 0 |
| v1 agent | 4 | 0 | 3 | 2 | 0 |
| v2 yaml | 5 | 1 | 1 | 1 | 3 |
| v2 agent | 5 | 1 | 1 | 1 | 11 |
| v2+R yaml | 6 | 1 | 0 | 0 | 6 |
| v2+R agent | 6 | 1 | 0 | 0 | 6 |
| v3 | 6 | 1 | 0 | 0 | 6 |
| v3u | 7 | 0 | 0 | 0 | 0 |
| v2+Ru yaml | 7 | 0 | 0 | 0 | 0 |
| v2+Ru agent | 7 | 0 | 0 | 0 | 0 |
