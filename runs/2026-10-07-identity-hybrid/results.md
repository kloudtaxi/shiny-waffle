# G-18: hybrid identity routing, results

## base KB: 21661 labelled pairs, 108 truly the same

| Arm | merged | kept | to a person (share) | false merges | missed merges |
|---|---|---|---|---|---|
| I2 as pre-registered: Jev + guard, routed band to a person | 3 | 20713 | 945 (4.36%) | 0 | 0 |
| Jev + guard, keep bar 0.3 (I2 exploratory; tuned on this data) | 3 | 21453 | 205 (0.95%) | 0 | 0 |
| Hybrid R1: Opus decides I2's band; unsure to a person | 67 | 21507 | 87 (0.40%) | 0 | 1 |
| Hybrid R2: act only when Opus agrees with Jev's lean | 23 | 21467 | 171 (0.79%) | 0 | 0 |
| R1 on the keep-bar-0.3 band | 67 | 21524 | 70 (0.32%) | 0 | 1 |
| R2 on the keep-bar-0.3 band | 23 | 21484 | 154 (0.71%) | 0 | 0 |

Opus on I2's band (n = 945), (answer, truth): different/different 793, different/same 1, same/same 64, unsure/different 47, unsure/same 40

gpt-4o (Utopia governance) on the same band, (call, truth): keep/different 814, keep/same 53, merge/different 11, merge/same 51, route/different 15, route/same 1

- R2's person queue ranked by Jev P(same): top 50 hold 44 of 85 true matches
- R2's person queue ranked by Jev P(same): top 100 hold 82 of 85 true matches
- R2's person queue ranked by Jev P(same): top 200 hold 85 of 85 true matches

## missing-contract KB: 19956 labelled pairs, 93 truly the same

| Arm | merged | kept | to a person (share) | false merges | missed merges |
|---|---|---|---|---|---|
| I2 as pre-registered: Jev + guard, routed band to a person | 0 | 19188 | 768 (3.85%) | 0 | 0 |
| Jev + guard, keep bar 0.3 (I2 exploratory; tuned on this data) | 0 | 19764 | 192 (0.96%) | 0 | 0 |
| Hybrid R1: Opus decides I2's band; unsure to a person | 71 | 19786 | 99 (0.50%) | 0 | 1 |
| Hybrid R2: act only when Opus agrees with Jev's lean | 18 | 19750 | 188 (0.94%) | 0 | 0 |
| R1 on the keep-bar-0.3 band | 71 | 19833 | 52 (0.26%) | 0 | 1 |
| R2 on the keep-bar-0.3 band | 18 | 19797 | 141 (0.71%) | 0 | 0 |

Opus on I2's band (n = 768), (answer, truth): different/different 597, different/same 1, same/same 71, unsure/different 78, unsure/same 21

gpt-4o (Utopia governance) on the same band, (call, truth): keep/different 656, keep/same 44, merge/different 10, merge/same 48, route/different 9, route/same 1

- R2's person queue ranked by Jev P(same): top 50 hold 47 of 75 true matches
- R2's person queue ranked by Jev P(same): top 100 hold 73 of 75 true matches
- R2's person queue ranked by Jev P(same): top 200 hold 75 of 75 true matches

Opus repeatability: 95/100 answers identical on a second ask.
Opus calls: 1051 distinct inputs plus 100 repeats, $10.99.
