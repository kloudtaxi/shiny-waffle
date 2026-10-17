> **STATUS: PREPARING (2026-10-17).** Nothing from Northstar has been loaded into either foundation
> for the exam yet. B-20 isn't frozen. Pre-registration:
> `docs/b20-northstar-exam-preregistration-2026-10-17.md`.

# B-20's Northstar exam

## What's here so far

| File | What |
|---|---|
| `questions.tsv` | The 47 questions (§4), built by `lab/exam/questions.py`. A test checks the committed file is what the builder builds |
| `arms.json` | Each arm's foundation, written at the freeze (not yet) |

## The harness (lab commit of this note)

- `lab/contract_reader/`: the one tool surface. Checked live through web-next's adapter on
  2026-10-17: every tool answers, and K16 is `not_served` for today's foundation.
- `lab/exam/reader.py`: the reader runs and the probe.
- `lab/exam/score_part2.py`: Part 2's scoring, with each process's own scorer.
- To come: Part 1's scorers, today's foundation's loader, the adapter parity probe, and the pilot.
