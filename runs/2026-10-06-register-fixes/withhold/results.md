# One register for all three decision types (G-30)

## discount: clean (K3) and re-saved (K5)

| Engine | Clean: matches the frozen spec | Re-saved: decisions changed |
|---|---|---|
| discount | 18/18  | 18/18 ['S01', 'S02', 'S03', 'S04', 'S05', 'S09', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S16', 'S17', 'S18', 'S19', 'S20', 'S21'] |
| discount+R | 18/18  | 18/18 ['S01', 'S02', 'S03', 'S04', 'S05', 'S09', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S16', 'S17', 'S18', 'S19', 'S20', 'S21'] |
| discount+Ru | 18/18  | 0/18  |

## sla: clean (K3) and re-saved (K5)

| Engine | Clean: matches the frozen spec | Re-saved: decisions changed |
|---|---|---|
| sla | 10/10  | 10/10 ['S36', 'S37', 'S38', 'S39', 'S40', 'S41', 'S42', 'S43', 'S44', 'S45'] |
| sla+R | 10/10  | 10/10 ['S36', 'S37', 'S38', 'S39', 'S40', 'S41', 'S42', 'S43', 'S44', 'S45'] |
| sla+Ru | 10/10  | 0/10  |

## Experiment 4's set A on discount

| Attack | Target | discount | discount+R | discount+Ru |
|---|---|---|---|---|
| A1 | S01 | held | held | held |
| A2 | S02 | held | held | held |
| A3 | S02 | held | held | held |
| A4 | S01 | held | held | held |
| A5 | S13 | held | held | held |
| A6 | S03 | routed | routed | held |
| A7 | S13 | held | held | held |
| A8 | S01 | held | held | held |

| Engine | Targets unsafe | routed | Collateral unsafe | Collateral routed |
|---|---|---|---|---|
| discount | 0 | 1 | 0 | 6 |
| discount+R | 0 | 1 | 0 | 15 |
| discount+Ru | 0 | 0 | 0 | 0 |

## Experiment 4's set B on discount

| Attack | Target | discount | discount+R | discount+Ru |
|---|---|---|---|---|
| B1 | S01 | held | held | held |
| B2 | S21 | held | held | held |
| B3 | S03 | routed | routed | held |
| B4 | S13 | held | held | held |
| B5 | S02 | routed | held | held |
| B6 | S04 | held | held | held |
| B7 | S14 | held | held | held |
| B8 | S01 | held | held | held |

| Engine | Targets unsafe | routed | Collateral unsafe | Collateral routed |
|---|---|---|---|---|
| discount | 0 | 2 | 0 | 11 |
| discount+R | 0 | 1 | 0 | 15 |
| discount+Ru | 0 | 0 | 0 | 0 |

**All pre-registered checks: pass**
