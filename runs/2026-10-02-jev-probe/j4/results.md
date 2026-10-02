# J4: Jev against gpt-4o on Utopia's duplicate queue (sample)

## All sampled pairs (n = 1445, truly same = 57)

| | merge | keep | routed | false merges | missed merges | right when acting |
|---|---|---|---|---|---|---|
| gpt-4o | 215 | 1000 | 230 | 161 | 2 | 1052/1215 |
| Jev | 11 | 1155 | 279 | 3 | 0 | 1163/1166 |

## Excluding composite 'SO-n C-m' names (n = 995, truly same = 57)

| | merge | keep | routed | false merges | missed merges | right when acting |
|---|---|---|---|---|---|---|
| gpt-4o | 57 | 774 | 164 | 3 | 2 | 826/831 |
| Jev | 8 | 884 | 103 | 0 | 0 | 892/892 |

## Stratum: pairs gpt-4o merged (n = 215, truly same = 54)

| | merge | keep | routed | false merges | missed merges | right when acting |
|---|---|---|---|---|---|---|
| gpt-4o | 215 | 0 | 0 | 161 | 0 | 54/215 |
| Jev | 11 | 1 | 203 | 3 | 0 | 9/12 |

## Stratum: pairs gpt-4o routed (unsure or proposed) (n = 230, truly same = 1)

| | merge | keep | routed | false merges | missed merges | right when acting |
|---|---|---|---|---|---|---|
| gpt-4o | 0 | 0 | 230 | 0 | 0 | 0/0 |
| Jev | 0 | 208 | 22 | 0 | 0 | 208/208 |

## Stratum: random 1,000 of gpt-4o's applied keeps (n = 1000, truly same = 2)

| | merge | keep | routed | false merges | missed merges | right when acting |
|---|---|---|---|---|---|---|
| gpt-4o | 0 | 1000 | 0 | 0 | 2 | 998/1000 |
| Jev | 0 | 946 | 54 | 0 | 0 | 946/946 |

**Jev ECE on P(same): 0.043** (n = 1445)

**Cost on these 1445 pairs:** Jev $0.0299 measured (712,331 input tokens). gpt-4o about $1.31 estimated (292,255 input and 57,800 output tokens at $2.5/$10.0 per million, system prompt shared across batches of 12). Ratio 2.29%.
