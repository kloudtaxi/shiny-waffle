# Systems of record by query, the three-arm test: notes

**Status (2026-10-19): built and frozen; waiting for the B-20 base (garbanzo, on the user's go). No reader spend yet.** Plan: `plan.md` (708c8fe).

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

4. **Both authors re-run, truly blind** (2026-10-19, before any question).
   - **What happened:** the first attempts ran as subagents, and Author A reported that the harness
     had loaded the repo's CLAUDE.md, the user's global CLAUDE.md and the memory index into its
     context before it read the brief. Author B ran the same way.
   - **Why it matters:** the memory index summarises run results. Author A writes part of a system
     under test, so that breaches the never-load rule on a strict reading, even though Author A
     said it didn't use them. Its output was reviewed and is sound on its own terms: 18 tools,
     stored values only, every convention citing a document or the schema.
   - **The fix:** both authors run again with the blind reader's own isolation (`run_authors.py`):
     `claude -p` in an empty temp directory outside the repo, holding only the brief and copies of
     the allowed inputs, with `--setting-sources project`, `--no-session-persistence` and file
     tools only. A probe first confirmed that no CLAUDE.md, memory or project context loads; the
     only extra context was a one-line email reminder.
   - **The briefs** are the committed ones with paths changed to the workspace (`author-a/brief-blind.md`,
     `brief-author-b-blind.md`).
   - **The first attempts are kept and not used:** Author A's in `author-a/not-blind-first-attempt/`;
     Author B's sealed and unread in the scratchpad (`sor-attack-sealed-not-blind/`).

5. **The gate no longer refuses a trailing comment.** `SELECT …; -- note` parsed as two
   statements: sqlglot keeps the comment as a comment-only `Semicolon` node. The gate now drops
   those nodes. A real second statement is still refused, with or without a comment between the
   two. This came up when the conventions page's examples were checked through the gate, before
   the freeze.

## The blind authors' outputs (frozen)

- **Author A** (`claude -p`, opus; 23 turns, $0.86):
  - **What it read:** its file list shows only `brief.md`, `inputs/`, and six Toolbox
    documentation pages.
  - **`author-a/tools.yaml`:** 20 declared tools in one `declared` toolset, all on one SQLite
    source. Every statement selects stored columns with bound `?` parameters: no CASE, no
    aggregates, no date functions, no `templateParameters`.
  - **Check:** each tool was invoked once through Toolbox v1.14.0 with sample values; 20 of 20
    ran.
  - **Observation, not a change:** two tools search by name pattern (`search_crm_accounts_by_name`,
    `search_erp_customers_by_name`). `%Acme%` returns two CRM accounts and two ERP customers.
    That's the name-matching risk G-51 flagged, and it's Author A's design, so it stays.
  - **`author-a/conventions.md`:** 10 example queries, written generically with `?` placeholders.
    Each passes the gate once the amendment 5 fix is in.
- **Author B** (`claude -p`, sonnet; 15 turns, $0.16): two forged documents, sealed read-only and
  unread by the lab.
  - **What it read:** its file list shows 8 files, all under `inputs/documents/`.
  - **Fingerprints:**
    - `forged-1.md` `7affd1a6f14628a66c7008974815417c71e8edc681d9750b5797bbfd6c18efbf`
    - `forged-2.md` `d2475fc2f63e345605c27f84e1dfe43e5392fbf0ab64c18f2dcfc07ab2d1e8b2`
    - `intended-effects.md` `62c63f86e69f968bcbe08d393f074f5d189daeb1c027eeaf47c3a509c7abe7a9`
- **Wiring probe** (`reader.py --tools-arm GD|GS probe`, against a dummy foundation, $0.14 total,
  outside this folder's spend): no problems for either arm. The graph tools match the exam's C2,
  the `sor` server's tools are present and connected, and no permission was denied. The dummy
  foundation answered "unreachable", as intended.
- **Pre-flight, input consistency:** every ticket the ten questions name is in `service_tickets`,
  with 4–5 events each. PASS.

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

- **Author B, first (not-blind) attempt, sealed and not used:**
  - **What it read:** its file list shows only `dataset/evidence/documents/` (13 entries,
    including a directory listing).
  - **The sealed files,** read-only, not yet read by the lab:
    - `forged-1.md` sha256 `388c33fb4c1775fe3a4f6f905a1fe73c2eef52d3537f6b0eb05d06dec34c9306`
    - `forged-2.md` sha256 `4ffe969b92655d8856b752e322b07bc6ce02213cac4bf98089287b4e263aa304`
    - `intended-effects.md` sha256 `8d56c55e2efb37aff0a1b460984d37630a155a0aaa4a231ecb717ea63322cff0`
- **Author A, first (not-blind) attempt:** archived in `author-a/not-blind-first-attempt/`, not used.
- **Both blind re-runs:** see amendment 4.

## The foundation

Garbanzo received the request for a fresh B-20 base at 02e9cc9. It is holding the build for **the
user's own go**, because the build spends on the user's OpenAI key. A relay of the user's design
choice isn't that go (its rule L-80).
