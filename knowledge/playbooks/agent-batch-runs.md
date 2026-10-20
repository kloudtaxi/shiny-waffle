# Playbook: batches of agent runs (`claude -p` readers, judges, graders)

**Use it for** any job that starts many agent runs and keeps their outputs as results. The lab's
reference implementation is `lab/exam/reader.py`; `lab/exam/judge.py` is a smaller one.

## Classify every result by its content

| What came back | What it is | What to do |
|---|---|---|
| A result with work done and an answer | an answer | keep it as the answer |
| `subtype: error_max_turns` | an answer: the reader ran out of turns | keep it; it's counted and scored as no decision |
| `is_error: true`, subtype `success`, $0, about 1 turn, text such as "session limit" or "usage limit" | **the account refused it**, so not an answer | keep it aside (`<id>.infra-error-<k>.jsonl`), halt, and ask again after the reset; it never counts against the question |
| Any other `is_error` with nothing spent | an infra error, so not an answer | keep it aside and ask once more; two strikes go to the user |
| No result event, or a crash with no stdout | an infra error | the same |

Never trust the `subtype` field alone. In 2026-10, Claude Code reported the account's session
limit as subtype `success` ([Success-shaped failure](../patterns.md#success-shaped-failure)).

## Run it so a stop costs minutes

- **Resumable:** an item whose answer file exists is never asked again.
- **Halting:** after the first infra error, start nothing new, and let the driver stop too. The
  lab's `part2-arm.sh` greps for `INFRA ERROR` after each pass.
- **A resumed pass keeps its first `setup.json`,** and writes `setup-resume-<n>.json` beside it.
- **The spend guard sums every answer in the run folder,** refused attempts included, but only once,
  when its process starts. After that it adds its own answers. **With k processes in parallel,** give
  each `--cap-usd` = spent + (budget − spent) / k, and compute the true folder total between phases
  (R6: three arms printed $11–16 each while the folder held $42.20).
- **Monitors match every terminal state:** done, halted, skipped, failed, crashed, and the spend
  guard. Silence isn't success.

## Size it against the account, not only the dollars

- **The supervising agent shares the account's limit.** A batch that empties the window stops the
  supervisor too.
- **Concurrency multiplies burn.** At 10 workers across three arms, the exam emptied a window in
  15–40 minutes. Pilot at the planned concurrency, and keep the supervisor headroom.
- **Graph-only answers cost about 3× all-tools answers,** and SLA-style multi-step questions cost
  the most: up to $2.21 an answer, with an average of 47 calls per graph-only answer on the weaker
  graph. Price per question from a pilot, then re-price from
  the run's own answers. In the exam, that predicted $115, and $123 was spent.

## Price it, and check it, before trusting it

- **Re-price per call from the current corpus** before each batch. Never reuse an old run's unit
  price: $0.18 assumed, $0.31 actual after the corpus grew.
- **A probe of 3–8 calls for any new model or arm,** and an early guard on the first calls. A probe
  of 3 pairs predicted $11, and it cost $10.99.
- **An extreme result means checking the harness before reporting it.** 18,402 false merges turned
  out to be a scoring rule, not a bug, and the check was worth it.
- **Run code lives in the repo before its results are cited,** never only in a session scratchpad.
- **Load a sibling run's module by path, under a unique name** (`importlib.util`). Run folders share
  file names, so `import run_reader` can load the wrong one.

## Blindness checklist (the reader and judge controls)

- Use a fresh temp directory outside the repo, `--tools ""`, `--strict-mcp-config`,
  `--setting-sources project` and `--no-session-persistence`.
- Hide tools with `--disallowedTools`. Leaving a tool off an allowlist isn't enough.
- Use one tool surface for every arm, with the same descriptions. Drop any field only one arm
  serves, such as a search score.
- Run a probe before every batch: the tools in context, the MCP server connected, no permission
  denials.
- Use a read token per run, scoped to the run's bases and revoked at the end. Probe the agent's
  ambient context too: who it works for, and today's date.
- For a judge: show no arm name, give a fixed prompt, take three runs and the majority (a
  three-way split counts as partial), and keep every run's answer.
- **Blind authors and judges never run as subagents.** A subagent inherits CLAUDE.md and the memory
  index. Run them as `claude -p` in an empty temp directory holding only their brief and copies of
  their allowed inputs, with file tools only, and probe that nothing else loaded (R6; the three-arm
  test's `run_authors.py`).
- **For a judge that must not know the arms,** build a coded packet: shuffle the answers under
  random codes, mask tool names that reveal an arm, and write the mapping read-only beside it,
  unopened until the verdicts are in (R6, `attack/judging/`).
