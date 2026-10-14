# B-15 proof rounds

The runner behind web-next's `/present` page. A round puts the same Deal Desk Agent (Claude via
headless `claude -p`) through Sarah's ask on DR-9001 (scenario S22) several times in three arms:
the agent alone with a realistic prompt, the agent alone with the lab's neutral prompt, and the
agent with BlueLeaf. Each run's outcome is derived from the systems of record, never from what
the agent says. The design, the record shapes and the outcome rules are in
`docs/superpowers/specs/2026-10-13-b15-proof-rounds-harness-design.md`.

It runs from the repo root, needs the `owm-service` group and uses only the standard library
beyond that.

## Starting it

```bash
ROUNDS_KB=<base id> uv run --group owm-service python -m rounds
```

| Variable | Default | Used for |
|---|---|---|
| `ROUNDS_PORT` | `8010` | the API, bound to 127.0.0.1 |
| `ROUNDS_STATE_DIR` | `.owm-rounds` | live state (below) |
| `ROUNDS_CAP_USD` | `30` | the spend cap for a round |
| `ROUNDS_SERVICE_PORT` | `8001` | the OWM service the runner starts for itself |
| `ROUNDS_KB` | none | the knowledge base id; required unless scripted |
| `ROUNDS_SCRIPTED` | unset | `1` swaps Claude for a deterministic agent: no spend, no foundation |

Rehearse the page without spend:

```bash
ROUNDS_SCRIPTED=1 uv run --group owm-service python -m rounds
```

## Routes

| Route | What it does |
|---|---|
| `POST /lab/rounds` | body `{scenario, runs_per_arm (1 to 5), started_by}`; 202 and the queued round, 409 while a round runs, 400 on a bad body |
| `GET /lab/rounds` | live and committed rounds |
| `GET /lab/rounds/{round_id}` | one round with its runs embedded, or 404 |

There is no auth and no CORS. web-next calls it server-side.

## Where records live

Live state is under `.owm-rounds/` (gitignored): `rounds/<round_id>/round.json`, each run's
record, transcript and call log, and the service child's own state.

A pre-registered round is copied by hand into
`runs/<date>-b15-proof-round/rounds/<round_id>.json`, with its transcripts and call logs under
`runs/<date>-b15-proof-round/rounds/<round_id>/`. Set `source` to that path and
`pre_registration` to the notes' commit, then commit the copy like any run. The runner never
writes under `runs/`: it only reads committed copies, serves them read-only next to live rounds,
and a committed copy wins when an id is in both places. Runs are results, so add to them and
never rewrite them.

## Fixture for web-next

`tests/rounds/fixtures/round-scripted.json` is a scripted round (two runs per arm) that
`/present` is tested against. `tests/rounds/test_fixture.py` regenerates it and fails when the
committed copy is stale. To regenerate after changing the record shape:

```bash
uv run --group owm-service python lab/rounds/fixture.py --out tests/rounds/fixtures/round-scripted.json
```

## Controls

Changing any of these changes the experiment.

- **Blindness.** The agent runs in a fresh temp directory outside the repo with no built-in
  tools, `--strict-mcp-config` and `--no-session-persistence`. It never sees the repo, `truth/`
  or the answer key.
- **Tokens in env only.** The session token and the knowledge foundation's read token reach
  their servers through the agent's environment. The MCP config holds only `${...}` references.
  Nothing secret reaches a file, a record, a log or argv.
- **Neutral names.** The servers are `kb` and `deal_desk`. No record names the foundation, and
  none carries a raw tool name.
- **The cap.** After each run the round stops if the cost so far plus the largest run so far
  would pass `ROUNDS_CAP_USD`. The remaining runs are recorded as `incomplete`, "spend cap".
- **The base stays still.** The runner records the knowledge base's document count and latest
  update at the start and end of a round, and sets `base_check.changed` on a difference.
