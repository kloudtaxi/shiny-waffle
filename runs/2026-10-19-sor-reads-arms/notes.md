# Systems of record by query, the three-arm test: notes

**Status (2026-10-19): building. No reader spend yet.** Plan: `plan.md` (708c8fe).

## Amendments and clarifications to the plan (all before any question)

1. **Empty cells are NULL.** The loader stores an empty CSV cell as NULL, as a database export
   renders NULL. Everything else is as the plan says: INTEGER or REAL only when every non-empty
   value parses, TEXT otherwise, unchanged.
2. **The conventions page is a tool, not a description.** Claude Code may cut a long MCP tool
   description short, so the G+S arms carry the page in a second tool, `read_conventions`, and
   `run_sql`'s description says to call it first. Same content, reached the same way an agent
   retrieves its context.
3. **The gate also refuses SQLite's file and extension functions** (`load_extension`, `readfile`,
   `writefile` and the like). Before that, the gate tests showed `SELECT load_extension(…)` passing
   as an ordinary SELECT. The database file is read-only either way: a write that got past the gate
   fails at SQLite ("attempt to write a readonly database"), as a probe showed.

## The build

| Piece | What | Fingerprint |
|---|---|---|
| Loader | `lab/sor_reads/load_sqlite.py` | output: 13 tables, 221 rows, canonical dump sha256 `daa9878d08e7c8233b5a683128af2b995d6e053d34976937128900c299eecb90` (two builds identical) |
| MCP Toolbox | v1.14.0, darwin/arm64, from the release's storage link | sha256 `d1578b3f551b1aa0947c7b377716cd5e8b9448ac5a79fdc1e06dc11a69bbe334`, matching the release notes. `toolbox version 1.14.0+binary.darwin.arm64.6b743ef` |
| Executor config | `exec.yaml` (Toolbox's `sqlite-execute-sql`), called only by the gate | in git |
| Gate | `lab/sor_reads/gate_server.py`, sqlglot 30.23.0 (`uv run --with`, not in `pyproject.toml`) | in git |
| Arm wiring | `lab/sor_reads/reader.py`: the exam reader with three functions swapped to add the `sor` server | in git |
| Questions | `questions.tsv`: S36–S45, copied verbatim from the exam's | in git |

**Gate tests (before any question):**
- **Ran:** a plain SELECT; a CTE with a join; UNION (wrapped); small limits (kept); `LIMIT 5000`
  (cut to 200); `lower()`; `datetime()`; a trailing comment, which became an inert block comment.
- **Refused:**
  - two statements; DELETE, INSERT…SELECT, PRAGMA, ATTACH, DROP, and UPDATE inside a CTE;
  - `sqlite_master` (an unknown table);
  - unparseable text. sqlglot read it leniently as an alias, so it was refused on type;
  - `load_extension()` and `readfile()`.

## The blind authors

- **Author B (forged documents): done, sealed.**
  - **What it read:** its file list shows only `dataset/evidence/documents/` (13 entries,
    including a directory listing).
  - **The sealed files,** read-only, not yet read by the lab:
    - `forged-1.md` sha256 `388c33fb4c1775fe3a4f6f905a1fe73c2eef52d3537f6b0eb05d06dec34c9306`
    - `forged-2.md` sha256 `4ffe969b92655d8856b752e322b07bc6ce02213cac4bf98089287b4e263aa304`
    - `intended-effects.md` sha256 `8d56c55e2efb37aff0a1b460984d37630a155a0aaa4a231ecb717ea63322cff0`
- **Author A (declared tools, conventions page): running.**

## The foundation

Garbanzo received the request for a fresh B-20 base at 02e9cc9. It is holding the build for **the
user's own go**, because the build spends on the user's OpenAI key. A relay of the user's design
choice isn't that go (its rule L-80).
