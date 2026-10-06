# G-32 addendum: a forced route withholds its findings (check)

- register_run_set --check --replay: ran
- register_run_set --set C --replay: ran
- register_run_set --set D --replay: ran
- register_run_set --set E --replay: ran
- register_all --replay: ran
- run_set_f --replay: ran

| Set | Route-mode unsafe | Routed | Forced routes | Withheld | Re-scored by the rule | Default/frozen reproduce | Other route rows unchanged |
|---|---|---|---|---|---|---|---|
| credit C | 0  | 30 | 30 | 30 | 6 [('v2+R agent', 'S32'), ('v2+R agent', 'S33'), ('v2+R yaml', 'S32'), ('v2+R yaml', 'S33'), ('v3', 'S32'), ('v3', 'S33')] | True | True |
| credit D | 0  | 57 | 57 | 57 | 9 [('v2+R agent', 'S32'), ('v2+R agent', 'S33'), ('v2+R yaml', 'S32'), ('v2+R yaml', 'S33'), ('v3', 'S32'), ('v3', 'S33')] | True | True |
| credit E | 0  | 0 | 0 | 0 | 0  | True | True |
| discount A | 0  | 16 | 16 | 16 | 2 [('discount+R', 'S13'), ('discount+R', 'S15')] | True | True |
| discount B | 0  | 16 | 16 | 16 | 2 [('discount+R', 'S13'), ('discount+R', 'S15')] | True | True |
| set F | 0  | 131 | 131 | 131 | 18 [('credit v2+R agent', 'S32'), ('credit v2+R agent', 'S33'), ('credit v2+R yaml', 'S32'), ('credit v2+R yaml', 'S33'), ('credit v3', 'S32'), ('credit v3', 'S33'), ('discount+R', 'S05'), ('discount+R', 'S13'), ('discount+R', 'S15'), ('sla+R', 'S45')] | True | True |

## P-32d: the records

- F9 → S45, sla+R: {'outcome': None, 'gated_outcome': 'CANNOT_DECIDE', 'scope': None, 'severity': None, 'breach': {}, 'credit_usd': None, 'obligations': [], 'account_owner': None}
  - flags: ['SUP-ACME-C: differs from its registered version 1; set aside', 'out of scope: no support terms cover this customer and product', 'routed: SUP-ACME-C set aside (on_mismatch: route)', 'withheld: subject, outcome, scope, severity, breach, credit_usd, obligations, account_owner (computed without SUP-ACME-C)']
  - **states no finding: True**
- credit C C1 → S26, v3: {'outcome': None, 'eligibility': {}, 'authority': {}, 'approvers': [], 'registered': []}; **states no finding: True**
- credit D D2 → S26, v3: {'outcome': None, 'eligibility': {}, 'authority': {}, 'approvers': [], 'registered': []}; **states no finding: True**

**All addendum predictions: hold**
