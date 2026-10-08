# Set E: v1, v2 and register-backed credit engines

| Attack | Target | Engine | Target result | Gated outcome | Collateral (moved) |
|---|---|---|---|---|---|
| E1 | S32 | v1 python | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | none |
| E1 | S32 | v1 yaml | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | none |
| E1 | S32 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | none |
| E1 | S32 | v2 yaml | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | none |
| E1 | S32 | v2 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | none |
| E1 | S32 | v2+R yaml | **held** | REQUEST_EVIDENCE | none |
| E1 | S32 | v2+R agent | **held** | REQUEST_EVIDENCE | none |
| E1 | S32 | v3 | **held** | REQUEST_EVIDENCE | none |
| E1 | S32 | v3u | **held** | REQUEST_EVIDENCE | none |
| E1 | S32 | v2+Ru yaml | **held** | REQUEST_EVIDENCE | none |
| E1 | S32 | v2+Ru agent | **held** | REQUEST_EVIDENCE | none |
| E2 | S29 | v1 python | **held** | REJECT_OR_ESCALATE | S28 REJECT_OR_ESCALATE (unsafe: wrong denial); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| E2 | S29 | v1 yaml | **held** | REJECT_OR_ESCALATE | S28 REJECT_OR_ESCALATE (unsafe: wrong denial); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| E2 | S29 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S33 REJECT_OR_ESCALATE (unsafe: wrong denial); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| E2 | S29 | v2 yaml | **routed** | REQUEST_EVIDENCE | S28 REQUEST_EVIDENCE (routed); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| E2 | S29 | v2 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S33 REJECT_OR_ESCALATE (unsafe: wrong denial); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| E2 | S29 | v2+R yaml | **held** | REJECT_OR_ESCALATE | none |
| E2 | S29 | v2+R agent | **held** | REJECT_OR_ESCALATE | none |
| E2 | S29 | v3 | **held** | REJECT_OR_ESCALATE | none |
| E2 | S29 | v3u | **held** | REJECT_OR_ESCALATE | none |
| E2 | S29 | v2+Ru yaml | **held** | REJECT_OR_ESCALATE | none |
| E2 | S29 | v2+Ru agent | **held** | REJECT_OR_ESCALATE | none |
| E3 | S33 | v1 python | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S28 APPROVE_WITH_AUTHORIZATION (held); S29 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval) |
| E3 | S33 | v1 yaml | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S28 APPROVE_WITH_AUTHORIZATION (held); S29 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval) |
| E3 | S33 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S29 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| E3 | S33 | v2 yaml | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed) |
| E3 | S33 | v2 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| E3 | S33 | v2+R yaml | **held** | REQUEST_EVIDENCE | none |
| E3 | S33 | v2+R agent | **held** | REQUEST_EVIDENCE | none |
| E3 | S33 | v3 | **held** | REQUEST_EVIDENCE | none |
| E3 | S33 | v3u | **held** | REQUEST_EVIDENCE | none |
| E3 | S33 | v2+Ru yaml | **held** | REQUEST_EVIDENCE | none |
| E3 | S33 | v2+Ru agent | **held** | REQUEST_EVIDENCE | none |
| E4 | S27 | v1 python | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| E4 | S27 | v1 yaml | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| E4 | S27 | v1 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| E4 | S27 | v2 yaml | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| E4 | S27 | v2 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| E4 | S27 | v2+R yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E4 | S27 | v2+R agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E4 | S27 | v3 | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E4 | S27 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E4 | S27 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E4 | S27 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E5 | S30 | v1 python | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v1 yaml | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v1 agent | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v2 yaml | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v2 agent | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v2+R yaml | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v2+R agent | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v3 | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v3u | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v2+Ru yaml | **held** | REJECT_OR_ESCALATE | none |
| E5 | S30 | v2+Ru agent | **held** | REJECT_OR_ESCALATE | none |
| E6 | S26 | v1 python | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v1 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v1 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v2 yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v2 agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v2+R yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v2+R agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v3 | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E6 | S26 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E7 | S28 | v1 python | **unsafe: wrong denial** | REJECT_OR_ESCALATE | S29 REJECT_OR_ESCALATE (held); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| E7 | S28 | v1 yaml | **unsafe: wrong denial** | REJECT_OR_ESCALATE | S29 REJECT_OR_ESCALATE (held); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| E7 | S28 | v1 agent | **held** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S29 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval); S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| E7 | S28 | v2 yaml | **routed** | REQUEST_EVIDENCE | S29 REQUEST_EVIDENCE (routed); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| E7 | S28 | v2 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| E7 | S28 | v2+R yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E7 | S28 | v2+R agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E7 | S28 | v3 | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E7 | S28 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E7 | S28 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| E7 | S28 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |

| Engine | Targets held | routed | unsafe | Collateral unsafe | Collateral routed |
|---|---|---|---|---|---|
| v1 python | 3 | 1 | 3 | 4 | 6 |
| v1 yaml | 3 | 1 | 3 | 4 | 6 |
| v1 agent | 3 | 1 | 3 | 4 | 6 |
| v2 yaml | 2 | 3 | 2 | 2 | 10 |
| v2 agent | 2 | 3 | 2 | 2 | 22 |
| v2+R yaml | 7 | 0 | 0 | 0 | 0 |
| v2+R agent | 7 | 0 | 0 | 0 | 0 |
| v3 | 7 | 0 | 0 | 0 | 0 |
| v3u | 7 | 0 | 0 | 0 | 0 |
| v2+Ru yaml | 7 | 0 | 0 | 0 | 0 |
| v2+Ru agent | 7 | 0 | 0 | 0 | 0 |
