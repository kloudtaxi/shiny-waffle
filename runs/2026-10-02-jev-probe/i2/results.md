# I2: customer matching on the whole duplicate queue

## base KB: 21661 labelled pairs, 108 truly the same

| | merged | kept | routed (share) | false merges | missed merges | right when acting |
|---|---|---|---|---|---|---|
| gpt-4o (Utopia governance) | 215 | 21216 | 230 (1.1%) | 161 | 53 | 21217/21431 (99.00%) |
| Jev + guard, τ = 0.5 | 9 | 20713 | 939 (4.3%) | 1 | 0 | 20721/20722 (100.00%) |
| Jev + guard, τ = 0.6 | 7 | 20713 | 941 (4.3%) | 1 | 0 | 20719/20720 (100.00%) |
| Jev + guard, τ = 0.7 | 6 | 20713 | 942 (4.3%) | 1 | 0 | 20718/20719 (100.00%) |
| Jev + guard, τ = 0.8 | 5 | 20713 | 943 (4.4%) | 1 | 0 | 20717/20718 (100.00%) |
| Jev + guard, τ = 0.9 **(chosen)** | 3 | 20713 | 945 (4.4%) | 0 | 0 | 20716/20716 (100.00%) |

## missing-contract KB: 19956 labelled pairs, 93 truly the same

| | merged | kept | routed (share) | false merges | missed merges | right when acting |
|---|---|---|---|---|---|---|
| gpt-4o (Utopia governance) | 206 | 19548 | 202 (1.0%) | 158 | 44 | 19552/19754 (98.98%) |
| Jev + guard, τ = 0.5 | 6 | 19188 | 762 (3.8%) | 2 | 0 | 19192/19194 (99.99%) |
| Jev + guard, τ = 0.6 | 6 | 19188 | 762 (3.8%) | 2 | 0 | 19192/19194 (99.99%) |
| Jev + guard, τ = 0.7 | 5 | 19188 | 763 (3.8%) | 2 | 0 | 19191/19193 (99.99%) |
| Jev + guard, τ = 0.8 | 2 | 19188 | 766 (3.8%) | 2 | 0 | 19188/19190 (99.99%) |
| Jev + guard, τ = 0.9 **(chosen)** | 0 | 19188 | 768 (3.8%) | 0 | 0 | 19188/19188 (100.00%) |

Operating point, by the pre-registered rule on the base KB: **τ = 0.9**, applied unchanged to the missing-contract KB.
