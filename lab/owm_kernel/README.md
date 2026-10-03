# The decision kernel (lab)

This is the generic core of the lab's hybrid decision engine: Jev makes the narrow judgments, and
code applies the rules.

- **Where it came from:** refactored for experiment 5 (`runs/2026-10-03-exp5-credit/plan.md`) out
  of experiment 4's guarded discount engine.
- **What it is:** lab code, not BlueLeaf's OWM. It exists to measure what a general core would need.

| File | What it is |
|---|---|
| `kernel.py` | Evidence access, document kinds and provenance (G1), validity windows and conflict (G2), tamper signs (G3), consistency across documents (G5), judgments and gating, authority bands, and approvers |
| `discount.py` | The discount-approval spec: its questions, eligibility, outcomes and record |

## Using it

Specs import the kernel by module name, so put this folder on the path:

```python
sys.path.insert(0, "lab/owm_kernel")
import discount
from kernel import Evidence
decision = discount.decide(engine, Evidence(corpus_root), as_of, request_record, scenario_id)
```

`engine` is a `lab/decision_engine` engine (`Recorder`, `Replay`, `TypeSafe`).

## Changes

**Frozen on 2026-10-03,** before the credit spec existed. Every later change to `kernel.py` is
listed in experiment 5's notes and classed as a generalization or as special-casing.
