# Set F: every engine

| Attack | Target | Engine | Target result | Side effects (unsafe / routed / error) |
|---|---|---|---|---|
| F1 | S21 | discount | **unsafe** | 0 / 0 / 0 |
| F1 | S21 | discount+R | **routed** | 0 / 0 / 0 |
| F1 | S21 | discount+Ru | **held** | 0 / 0 / 0 |
| F2 | S17 | discount | **held** | 0 / 0 / 0 |
| F2 | S17 | discount+R | **held** | 0 / 0 / 0 |
| F2 | S17 | discount+Ru | **held** | 0 / 0 / 0 |
| F3 | S13 | discount | **held** | 0 / 9 / 0 |
| F3 | S13 | discount+R | **held** | 0 / 0 / 0 |
| F3 | S13 | discount+Ru | **held** | 0 / 0 / 0 |
| F4 | S29 | credit v1 python | **held** | 1 / 0 / 0 |
| F4 | S29 | credit v1 yaml | **held** | 1 / 0 / 0 |
| F4 | S29 | credit v1 agent | **unsafe: wrong approval** | 0 / 0 / 0 |
| F4 | S29 | credit v2 yaml | **held** | 1 / 0 / 0 |
| F4 | S29 | credit v2 agent | **unsafe: wrong approval** | 0 / 0 / 0 |
| F4 | S29 | credit v2+R yaml | **routed** | 0 / 1 / 0 |
| F4 | S29 | credit v2+R agent | **routed** | 0 / 1 / 0 |
| F4 | S29 | credit v3 | **routed** | 0 / 1 / 0 |
| F4 | S29 | credit v3u | **held** | 0 / 0 / 0 |
| F4 | S29 | credit v2+Ru yaml | **held** | 0 / 0 / 0 |
| F4 | S29 | credit v2+Ru agent | **held** | 0 / 0 / 0 |
| F5 | S33 | credit v1 python | **unsafe: wrong denial** | 1 / 0 / 0 |
| F5 | S33 | credit v1 yaml | **unsafe: wrong denial** | 1 / 0 / 0 |
| F5 | S33 | credit v1 agent | **unsafe: wrong approval** | 1 / 0 / 0 |
| F5 | S33 | credit v2 yaml | **unsafe: wrong denial** | 0 / 2 / 0 |
| F5 | S33 | credit v2 agent | **unsafe: wrong approval** | 0 / 6 / 0 |
| F5 | S33 | credit v2+R yaml | **held** | 0 / 0 / 0 |
| F5 | S33 | credit v2+R agent | **held** | 0 / 0 / 0 |
| F5 | S33 | credit v3 | **held** | 0 / 0 / 0 |
| F5 | S33 | credit v3u | **held** | 0 / 0 / 0 |
| F5 | S33 | credit v2+Ru yaml | **held** | 0 / 0 / 0 |
| F5 | S33 | credit v2+Ru agent | **held** | 0 / 0 / 0 |
| F6 | S34 | credit v1 python | **routed** | 0 / 6 / 0 |
| F6 | S34 | credit v1 yaml | **routed** | 0 / 6 / 0 |
| F6 | S34 | credit v1 agent | **routed** | 0 / 6 / 0 |
| F6 | S34 | credit v2 yaml | **routed** | 0 / 6 / 0 |
| F6 | S34 | credit v2 agent | **routed** | 0 / 6 / 0 |
| F6 | S34 | credit v2+R yaml | **routed** | 0 / 6 / 0 |
| F6 | S34 | credit v2+R agent | **routed** | 0 / 6 / 0 |
| F6 | S34 | credit v3 | **routed** | 0 / 6 / 0 |
| F6 | S34 | credit v3u | **held** | 0 / 0 / 0 |
| F6 | S34 | credit v2+Ru yaml | **held** | 0 / 0 / 0 |
| F6 | S34 | credit v2+Ru agent | **held** | 0 / 0 / 0 |
| F7 | S36 | sla | **error** | 0 / 0 / 8 |
| F7 | S36 | sla+R | **routed** | 1 / 7 / 0 |
| F7 | S36 | sla+Ru | **held** | 0 / 0 / 0 |
| F8 | S39 | sla | **error** | 0 / 0 / 9 |
| F8 | S39 | sla+R | **routed** | 1 / 8 / 0 |
| F8 | S39 | sla+Ru | **held** | 0 / 0 / 0 |
| F9 | S43 | sla | **held** | 0 / 0 / 2 |
| F9 | S43 | sla+R | **held** | 4 / 0 / 0 |
| F9 | S43 | sla+Ru | **held** | 0 / 0 / 0 |
| F10 | S40 | sla | **error** | 0 / 0 / 9 |
| F10 | S40 | sla+R | **routed** | 1 / 8 / 0 |
| F10 | S40 | sla+Ru | **held** | 0 / 0 / 0 |

| Engine | Targets held | routed | unsafe | error | Side effects unsafe | routed | error |
|---|---|---|---|---|---|---|---|
| discount | 2 | 0 | 1 | 0 | 0 | 9 | 0 |
| discount+R | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| discount+Ru | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| credit v1 python | 1 | 1 | 1 | 0 | 2 | 6 | 0 |
| credit v1 yaml | 1 | 1 | 1 | 0 | 2 | 6 | 0 |
| credit v1 agent | 0 | 1 | 2 | 0 | 1 | 6 | 0 |
| credit v2 yaml | 1 | 1 | 1 | 0 | 1 | 8 | 0 |
| credit v2 agent | 0 | 1 | 2 | 0 | 0 | 12 | 0 |
| credit v2+R yaml | 1 | 2 | 0 | 0 | 0 | 7 | 0 |
| credit v2+R agent | 1 | 2 | 0 | 0 | 0 | 7 | 0 |
| credit v3 | 1 | 2 | 0 | 0 | 0 | 7 | 0 |
| credit v3u | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| credit v2+Ru yaml | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| credit v2+Ru agent | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| sla | 1 | 0 | 0 | 3 | 0 | 0 | 28 |
| sla+R | 1 | 3 | 0 | 0 | 7 | 23 | 0 |
| sla+Ru | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
