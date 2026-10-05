# Gap tracker: moved to the Lab Ledger

The gap tracker lives in the **Northstar Lab Ledger**, under its **Gaps** tab, as of 2026-10-05:
<https://claude.ai/artifact/FsSXn3ADwvDgBzG85b3Vyq> (private to its owner).
- The `#G-01` … `#G-29` anchors open one gap directly, for example
  <https://claude.ai/artifact/FsSXn3ADwvDgBzG85b3Vyq#G-01>.
- The Ledger is the **source of truth**. Change a status, add an update or record a decision there.
- This file is only a pointer. The first version of the tracker, as written, is this file at commit
  `7678903` in git history.

**Where things are:**
- **The data:** the artifact's `gaps` collection, one document per gap. It holds:
  - id, title, area, owner and priority;
  - status (open, pending decision, partial, finding, decided, closed) and a status note;
  - the detail as markdown;
  - decisions (G-01's) and an update log.
- **The migration:** `tracker/seed_gaps.py` and `tracker/seed/gaps.json`. Never re-run it over the
  live ledger: it would overwrite the user's changes.

**For Claude:**
- **Before planning a build or closing a gap,** read the `gaps` collection with `ArtifactData`.
- **To change a gap,** use a pinned `update` (with `if_version` from the read), and append to
  `log` rather than rewriting it.
- **Status changes and decisions are the user's input.** Never overwrite them.
