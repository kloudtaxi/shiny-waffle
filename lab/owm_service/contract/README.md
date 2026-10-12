# Vendored contract

These files are copies from `kloudtaxi/glowing-garbanzo` (https://github.com/kloudtaxi/glowing-garbanzo)
at commit **6b6619e** (contract v1.4):

| Here | There |
|---|---|
| `owm-decisions.ts` | `web-next/lib/contract/owm-decisions.ts` |
| `s22.example.ts` | `web-next/lib/contract/s22.example.ts` |
| `s22.example.json` | generated from `s22.example.ts` (below) |

The service models (`../models.py`) mirror `owm-decisions.ts`. `tests/owm_service/test_contract_drift.py`
parses every export of `s22.example.json` through them, so a change to the contract that the models
don't follow fails there. Node is only needed to regenerate the JSON, not to run the tests.

Two later contract versions re-vendor only `owm-decisions.ts`:
- **v1.4 (6b6619e):** every list is a `Page<T>`, `{items, next_cursor}` (D-24);
- **v1.3 (589e0c7):** the dry run's own response (R34), and notes on R58 and `WorkItem.href`.

`s22.example.ts` hasn't changed since 30977cd, so `s22.example.json` stands.

## Regenerate

```bash
G=<a glowing-garbanzo clone>
git -C $G show 6b6619e:web-next/lib/contract/owm-decisions.ts > lab/owm_service/contract/owm-decisions.ts
git -C $G show 6b6619e:web-next/lib/contract/s22.example.ts   > lab/owm_service/contract/s22.example.ts
(cd lab/owm_service/contract && node -e "import('./s22.example.ts').then(m=>process.stdout.write(JSON.stringify(m,null,1)+'\n'))" > s22.example.json)
```

Node 22.6 or later is needed for the TypeScript type-stripping.
