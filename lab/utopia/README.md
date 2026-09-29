# Utopia experiment scripts

These scripts drive the Northstar × Utopia boundary experiment (`docs/experiment-runbook.md`)
against a running Utopia. They use only the standard library, need no install, and stay out
of the `northstar` package's dependency closure. Run them from the repo root.

| Script | What it does |
|---|---|
| `utopia.py` | REST client and CLI: `create-kb`, `upload`, `export` (RDF Turtle), `get` (any `/api/v1` path), `ask` (arm A: one question to Utopia's in-app chat), `delete-kb` |
| `blind_reader.py` | Arm B: a blind headless `claude -p` reader over Utopia's MCP. Variants `B1` (all tools), `B1n` (all but `changes`, for a graph with withdrawn curation) and `B2` (graph only) |
| `status.sh` | Read-only pipeline state for KB ids: documents, dates, facts by layer, active and failed jobs |

The correction applied on 2026-09-28 is kept with its run:
`runs/2026-09-28-utopia-aad5b06/correction/correct.py`. It prints the plan unless given
`--apply`.

## Configuration

| Variable | Default | Used for |
|---|---|---|
| `UTOPIA_API` | `http://localhost:1516/api/v1` | every call |
| `UTOPIA_EMAIL`, `UTOPIA_PASSWORD` | read from the gitignored `_owm-local/utopia-getting-started.md` | REST login (the JWT stays in memory) |
| `UTOPIA_WORKSPACE` | the first workspace the user can see | `create-kb` |
| `UTOPIA_DB_CONTAINER` | `utopia-db-1` | `status.sh` and `correct.py` (read-only SQL through `docker exec`) |

Nothing secret is written to disk or printed.

## Examples

```bash
python3 lab/utopia/utopia.py create-kb "Northstar Industrial Systems" schema-org w3c-org
python3 lab/utopia/utopia.py upload <kb> dataset/evidence/structured/*.csv dataset/evidence/documents/*.md
lab/utopia/status.sh <kb> <kb2>                      # until everything is ready/done
python3 lab/utopia/utopia.py export <kb> runs/<run>/snapshot/base.ttl

# arm A: every question in a new conversation, verbatim
tail -n +2 runs/<run>/questions.tsv | while IFS=$'\t' read -r sid kb q; do
  python3 lab/utopia/utopia.py ask "$kb" "$sid" "$q" runs/<run>/answers; done

# arm B: probe first (about $0.06), then the runs
python3 lab/utopia/blind_reader.py probe --run runs/<run> --variant B2
python3 lab/utopia/blind_reader.py run --run runs/<run> --out runs/<run>/arm-b B1 B2
python3 lab/utopia/blind_reader.py run --run runs/<run> --out runs/<run>/repeats/r2 B2
# with an OWM procedure appended to the fixed system prompt (path and sha256 go in setup-*.json)
python3 lab/utopia/blind_reader.py run --run runs/<run> --out runs/<run>/procedure/arm-b/r1 \
  --procedure owm/procedures/discount-approval.md B2
```

## The blind reader's controls

Changing any of these changes the experiment. Record the change in the run's notes.

- **Blindness.** Every reader call runs in a fresh, empty temp directory **outside the
  repo**. It has no built-in tools (`--tools ""`), `--strict-mcp-config`,
  `--setting-sources project` and `--no-session-persistence`. The reader must never see
  `truth/`, `dataset/answer-key/` or this repo's `CLAUDE.md`. The analysing session can't be
  the reader either: it has read the answers.
- **Hide, don't just withhold.** B2 removes `search_chunks` and `get_document` with
  `--disallowedTools`. Tools that are only left off the allowlist stay visible and are
  refused at call time, which tells the reader that documents exist. The first B2 attempt was
  discarded for this reason.
- **The fixed system prompt** is in `SYSTEM_PROMPT`. It has been verbatim since 2026-09-28.
- **Token.** Each invocation mints a `read` token limited to the KBs in `questions.tsv`,
  with a 2-day expiry. It is passed to `claude` only through `UTOPIA_MCP_TOKEN`, which the
  MCP config expands, and is revoked when the invocation ends, even on failure.
- **Resumable.** A question whose `.jsonl` exists is never asked again.
- **Probe before a batch.** The init event must list only `mcp__utopia__*` tools (11 for
  B1, 9 for B2), the MCP server must be `connected`, and there must be 0 permission denials.
- **Cost.** About $1.5 for a B1 batch and $2.7–3.2 for a B2 batch (10 questions each, Opus
  5.5), billed to the Claude Code plan in use.
