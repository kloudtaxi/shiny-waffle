# Semantica's bi-temporal queries on the OWM register (2026-10-09)

> **Status: done. With transaction times on every entity, Semantica 0.7.0 answers all 8
> questions exactly as an independent calculation does.** That covers valid time ("in force on
> V"), transaction time ("registered by T"), and the two together ("as known on T, in force on
> V"), the question G-38 says the OWM can't yet ask.
> **The pitfall:** an entity with no `recorded_at` counts as recorded *now* (wall-clock time).
> Every earlier transaction-time query then silently returns nothing (2 of 8 agree), and the
> answer depends on the day the query runs. No model calls; cost $0.

The code is `check.py`; the results are in `results.json`. This is a library check against
expectations computed in the script from the register's own fields. Nothing in it needed
predictions.

| Question | Entities untimed | Entities timed |
|---|---|---|
| In force on 2026-09-23 | agrees (12) | agrees (12) |
| In force on 2027-02-01 | agrees (11) | agrees (11) |
| Registered by 2025-12-01 | **empty** (expected 12) | agrees (12) |
| Registered by 2026-09-20 | **empty** (expected 17) | agrees (17) |
| As known on 2025-12-01, in force on 2026-02-01 | **empty** (expected 9) | agrees (9) |
| As known on 2026-01-15, in force on 2026-02-01 | **empty** (expected 12) | agrees (12) |
| As known on 2026-09-01, in force on 2027-03-01 | **empty** (expected 10) | agrees (10) |
| As known on 2026-09-20, in force on 2027-03-01 | **empty** (expected 11) | agrees (11) |

**What "as known at" shows on the lab's own data.**
- On 2025-12-01 the organization had not yet registered the 2026 pricing policy, the 2026 credit
  policy or the Acme guarantee (registered 2025-12-08 to 2025-12-18). So, as known that day,
  **9** governing documents would apply on 2026-02-01, against **12** as known on 2026-01-15.
- An audit question such as "was the decision right given what we knew then?" needs exactly this
  distinction. The kernel's `entry_in_force` answers only the valid-time half.

**For BlueLeaf (G-38):**
- The model works and is a reasonable reference design. Semantica takes one time per call, so a
  true two-coordinate query is composed (filter by transaction time, then by valid time).
- **If reused, make transaction time mandatory on every entity,** or wrap the library so a
  missing `recorded_at` is an error, not "now".
