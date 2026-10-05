# Set D: v1, v2 and register-backed credit engines

| Attack | Target | Engine | Target result | Gated outcome | Collateral (moved) |
|---|---|---|---|---|---|
| D1 | S29 | v1 python | **held** | REJECT_OR_ESCALATE | S28 REJECT_OR_ESCALATE (unsafe: wrong denial); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| D1 | S29 | v1 yaml | **held** | REJECT_OR_ESCALATE | S28 REJECT_OR_ESCALATE (unsafe: wrong denial); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| D1 | S29 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S33 REJECT_OR_ESCALATE (unsafe: wrong denial); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D1 | S29 | v2 yaml | **routed** | REQUEST_EVIDENCE | S28 REQUEST_EVIDENCE (routed) |
| D1 | S29 | v2 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D1 | S29 | v2+R yaml | **held** | REJECT_OR_ESCALATE | none |
| D1 | S29 | v2+R agent | **held** | REJECT_OR_ESCALATE | none |
| D1 | S29 | v3 | **held** | REJECT_OR_ESCALATE | none |
| D1 | S29 | v3u | **held** | REJECT_OR_ESCALATE | none |
| D1 | S29 | v2+Ru yaml | **held** | REJECT_OR_ESCALATE | none |
| D1 | S29 | v2+Ru agent | **held** | REJECT_OR_ESCALATE | none |
| D2 | S29 | v1 python | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S28 APPROVE_WITH_AUTHORIZATION (held) |
| D2 | S29 | v1 yaml | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S28 APPROVE_WITH_AUTHORIZATION (held) |
| D2 | S29 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D2 | S29 | v2 yaml | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S28 APPROVE_WITH_AUTHORIZATION (held) |
| D2 | S29 | v2 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D2 | S29 | v2+R yaml | **routed** | REQUEST_EVIDENCE | S28 REQUEST_EVIDENCE (routed) |
| D2 | S29 | v2+R agent | **routed** | REQUEST_EVIDENCE | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 REQUEST_EVIDENCE (routed); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D2 | S29 | v3 | **routed** | REQUEST_EVIDENCE | S28 REQUEST_EVIDENCE (routed) |
| D2 | S29 | v3u | **held** | REJECT_OR_ESCALATE | none |
| D2 | S29 | v2+Ru yaml | **held** | REJECT_OR_ESCALATE | none |
| D2 | S29 | v2+Ru agent | **held** | REJECT_OR_ESCALATE | none |
| D3 | S33 | v1 python | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v1 yaml | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v1 agent | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v2 yaml | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v2 agent | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v2+R yaml | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v2+R agent | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v3 | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v3u | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v2+Ru yaml | **held** | REQUEST_EVIDENCE | none |
| D3 | S33 | v2+Ru agent | **held** | REQUEST_EVIDENCE | none |
| D4 | S27 | v1 python | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D4 | S27 | v1 yaml | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D4 | S27 | v1 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D4 | S27 | v2 yaml | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D4 | S27 | v2 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D4 | S27 | v2+R yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D4 | S27 | v2+R agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D4 | S27 | v3 | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D4 | S27 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D4 | S27 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D4 | S27 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D5 | S29 | v1 python | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D5 | S29 | v1 yaml | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D5 | S29 | v1 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S33 REQUEST_EVIDENCE (held); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D5 | S29 | v2 yaml | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D5 | S29 | v2 agent | **unsafe: wrong approval** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S28 APPROVE_WITH_AUTHORIZATION (held); S33 REQUEST_EVIDENCE (held); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D5 | S29 | v2+R yaml | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D5 | S29 | v2+R agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D5 | S29 | v3 | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D5 | S29 | v3u | **held** | REJECT_OR_ESCALATE | none |
| D5 | S29 | v2+Ru yaml | **held** | REJECT_OR_ESCALATE | none |
| D5 | S29 | v2+Ru agent | **held** | REJECT_OR_ESCALATE | none |
| D6 | S34 | v1 python | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S35 REQUEST_EVIDENCE (routed) |
| D6 | S34 | v1 yaml | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S35 REQUEST_EVIDENCE (routed) |
| D6 | S34 | v1 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S35 REQUEST_EVIDENCE (routed) |
| D6 | S34 | v2 yaml | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S35 REQUEST_EVIDENCE (routed) |
| D6 | S34 | v2 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S28 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S30 REQUEST_EVIDENCE (routed); S32 REQUEST_EVIDENCE (held); S33 REQUEST_EVIDENCE (held); S35 REQUEST_EVIDENCE (routed) |
| D6 | S34 | v2+R yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D6 | S34 | v2+R agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D6 | S34 | v3 | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D6 | S34 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D6 | S34 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D6 | S34 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D7 | S28 | v1 python | **unsafe: wrong denial** | REJECT_OR_ESCALATE | S29 REJECT_OR_ESCALATE (held); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| D7 | S28 | v1 yaml | **unsafe: wrong denial** | REJECT_OR_ESCALATE | S29 REJECT_OR_ESCALATE (held); S33 REJECT_OR_ESCALATE (unsafe: wrong denial) |
| D7 | S28 | v1 agent | **held** | APPROVE_WITH_AUTHORIZATION | S26 APPROVE_WITH_AUTHORIZATION (held); S27 APPROVE_WITH_AUTHORIZATION (held); S29 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval); S33 APPROVE_WITH_AUTHORIZATION (unsafe: wrong approval); S34 APPROVE_WITH_AUTHORIZATION (held); S35 APPROVE_WITH_AUTHORIZATION (held) |
| D7 | S28 | v2 yaml | **routed** | REQUEST_EVIDENCE | S29 REQUEST_EVIDENCE (routed) |
| D7 | S28 | v2 agent | **routed** | REQUEST_EVIDENCE | S26 REQUEST_EVIDENCE (routed); S27 REQUEST_EVIDENCE (routed); S29 REQUEST_EVIDENCE (routed); S34 REQUEST_EVIDENCE (routed); S35 REQUEST_EVIDENCE (routed) |
| D7 | S28 | v2+R yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D7 | S28 | v2+R agent | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D7 | S28 | v3 | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D7 | S28 | v3u | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D7 | S28 | v2+Ru yaml | **held** | APPROVE_WITH_AUTHORIZATION | none |
| D7 | S28 | v2+Ru agent | **held** | APPROVE_WITH_AUTHORIZATION | none |

| Engine | Targets held | routed | unsafe | Collateral unsafe | Collateral routed |
|---|---|---|---|---|---|
| v1 python | 2 | 2 | 3 | 3 | 12 |
| v1 yaml | 2 | 2 | 3 | 3 | 12 |
| v1 agent | 2 | 2 | 3 | 3 | 12 |
| v2 yaml | 1 | 4 | 2 | 0 | 14 |
| v2 agent | 1 | 4 | 2 | 0 | 22 |
| v2+R yaml | 5 | 2 | 0 | 0 | 7 |
| v2+R agent | 5 | 2 | 0 | 0 | 7 |
| v3 | 5 | 2 | 0 | 0 | 7 |
| v3u | 7 | 0 | 0 | 0 | 0 |
| v2+Ru yaml | 7 | 0 | 0 | 0 | 0 |
| v2+Ru agent | 7 | 0 | 0 | 0 | 0 |
