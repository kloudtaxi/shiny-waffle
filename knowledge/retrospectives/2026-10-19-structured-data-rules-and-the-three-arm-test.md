# Retrospective: structured data, a rules engine, and the three-arm test (2026-10-19)

**Scope:** one day of work, done at the user's questions:
- G-51: should structured data be read by query, not extraction?
- G-52: a rules engine (GoRules ZEN)?
- G-53: the component names;
- the ZEN spike;
- G-51's three-arm test on a re-stood B-20, from pre-registration to teardown.

**Written by:** the lab's agent, the same day, at the user's go.
**Sources:**
- `runs/2026-10-19-sor-reads-arms/` (`plan.md`, `notes.md` amendments 1–8, `results.md`);
- `runs/2026-10-19-zen-rules-spike/`;
- the Ledger's G-51 to G-53;
- git history (22 commits, 0f37051 to 2f51e79);
- the session itself.

> **Never-load notice.** This file cites recorded runs. Nothing here may tune or shape a foundation
> under test. Its lessons are about how to run and measure.

## At a glance

| | Planned | Actual |
|---|---|---|
| Three-arm test answers | 120 (3 clean runs × 3 arms + 3 attack variants) | 120, plus 2 session-limit attempts asked again |
| Reader spend | stop at $200, about $190 priced | **$166.05**, plus $1.02 for authors and about $0.4 for probes |
| Amendments after pre-registration | none foreseen | 8, all logged before the step they changed |
| Blind authors | 2, run once | 2, run twice: the first runs weren't blind |
| Secrets leaked | 0 | 0. One commit was made before its scan (9df0c97); the scan afterwards found 0 hits |
| ZEN spike | $0, about a day | $0, about 15 minutes of running; all five checks passed |

## Timeline (local time, 10-19)

- **Morning:** the structured-data question and its analysis. The user shared their Vanna/R2R
  notes. Utopia's mounted-source design was read. G-51 was logged with five decisions.
- **13:21** ZEN evaluated (G-52). The canon check found the canon's own rules-engine note.
- **14:01** DataIQ was re-evaluated on MCP Toolbox + sqlglot (the user's proposal), and the names
  went to G-53. **Before this, a canon check had found that DataIQ already owned the question
  path.** G-51 was reframed, and no choice had been made yet.
- **14:43** ContextForge was assessed; the declared-reads amendment candidate was written.
- **14:46–14:51** The ZEN spike was pre-registered and run: all five checks passed.
- **14:58** The three-arm test was pre-registered, with the user's four design choices.
- **15:00–15:17** The loader and briefs; the gate and wiring; **the authors re-run blind**
  (incident 1); the freeze.
- **15:46** The pre-flight passed on garbanzo's base, built on the user's own go.
- **16:08** Clean run 1 was recorded, and **the spend guard was found undercounting** (incident 2).
- **16:25** Paused at the account's usage limit, with run 2 at 28 of 30 answers.
- **18:59–19:45** Resumed: run 2 completed; the attack phase run and judged blind; run 3;
  results; teardown.
- **20:31** The user closed G-52 and set G-53 open, P3.

## Incidents, by consequence

### 1. The "blind" authors weren't blind (caught by the author; about $1 and 20 minutes to redo)

**What happened:** the plan called for blind subagents to write the declared tools and the forged
attack. Author A's own report said the harness had loaded the repo's CLAUDE.md, the user's global
CLAUDE.md and the memory index into its context before it read its brief. The memory index
summarises run results, so on a strict reading the never-load rule was breached for a system under
test. Author B ran the same way.

**Root cause:** a subagent inherits the session's ambient context. "Blind" was a label in the brief,
not a property of the runtime. The lab's blindness checklist existed, but it was written for the
reader, and nobody applied it to authors.

**Fix:**
- both authors re-ran as `claude -p` in an empty temp directory with copies of their allowed
  inputs, `--setting-sources project` and file tools only;
- a probe confirmed that nothing else loaded;
- the first outputs are kept, unused (amendment 4).

### 2. The spend guard undercounted across parallel arms (caught at run 1; no overspend)

**What happened:**
- the exam reader's guard reads the folder's spend once, when a process starts, then adds that
  process's own answers;
- with three arms in parallel, the printed totals ($11.60, $14.29, $16.31) hid a real total of
  **$42.20**;
- the playbook said the guard "sums every answer in the run folder", which is true only at start.

**Fix (amendment 6):** each of the k parallel processes gets a cap of spent + (200 − spent) / k,
and the true total is computed from the folder between phases.

### 3. G-51's first framing missed the canon (caught by a canon check the same hour; nothing decided)

**What happened:** G-51's "who owns it" and "which engine" decisions were written as open
questions. The canon (owm-edd) already gave structured data to DataIQ, with Vanna over Spice and
definitions in OpenMetadata, and GatewayIX already included MCP Toolbox.

**Root cause:** the analysis read the lab and Utopia, not the canon, so the canon's silence was read
as absence. The check came when ZEN needed the canon's substrate rules.

**Fix:** G-51 was reframed, and its log says so. Lesson: read the canon before framing a platform
decision.

### 4. Two gate defects (caught by the gate's tests, before the freeze)

- `SELECT load_extension(…)` passed as an ordinary SELECT. A function deny-list was added
  (amendment 3).
- A trailing comment after the semicolon was refused as a second statement. It showed up while
  checking the conventions page's examples (amendment 5).

The read-only database file was the real boundary throughout: a write that reached SQLite failed
there.

### 5. Filenames would have given the attack away (caught by garbanzo)

B-20 serves a document's filename to the reader, so `forged-1.md` and `forged-2.md` would have named
the attack. Garbanzo asked before uploading. Corpus-style names were derived from each document's
title by script, after the build was frozen.

### 6. Smaller ones

- **ZEN spike:** P4's first requestor held no band, so the check couldn't show anything. Re-run with
  an AR Specialist, and both outputs kept.
- **A commit before its scan** (9df0c97). The scan ran right after: 0 hits.
- **A probe call with the wrong argument name** (`q` for `query`). It was caught before it could be
  read as "search is broken".
- **Two session-limit refusals in run 2.** They were kept aside and asked again, under the user's
  rule.

## What worked: keep doing it

- **Pre-register, then amend in the open.** Eight amendments, each logged before the step it
  changed, kept a messy day auditable.
- **A blind judge from a coded packet:** shuffled codes, masked tool names, the mapping written
  read-only beside it. The judge never knew the arms existed, which is stricter than "the lab reads
  blind to the arm".
- **Garbanzo's own-go rule.** It held each build for the user's direct go, even after the user had
  chosen the design here. Its filename question also saved the attack.
- **Verifying a peer's report through our own token** (K1 and K2 counts, the other base's token
  refused) before spending.
- **A differential grid in the spike** (1,445 points against the kernel). It proved equivalence and
  exposed the `limit_for` quirk.
- **Price from the exam's recorded per-answer cost** ($1.58). The re-price ($190 for 120) beat the
  analysis's first sketch ($80) and held: the real cost was $166.

## Insights

- **Exact reads help a reader decide, but the decision step is the remaining gap.** At least
  core-right went from 1 to 4–5 of 10, and unsafe decisions fell by 44–67%, at a lower cost per
  answer. Strict stayed at 2–3 of 10, against a ceiling of 8.
- **A forgery that the data contradicts dies against exact rows.** The forged UTC claim was rejected
  against stored offsets. A test of the sync risk needs a forgery the data can't contradict.
- **A subagent is never blind.** Anything that must be blind (an author, a judge, a reader) runs as
  `claude -p` under the blindness checklist, with a probe.
- **A guard that reads state once is local, not global.** Parallel processes need a shared or
  partitioned budget.

## Decisions to keep

- **G-51:** both platform and test. Declared Toolbox tools via GatewayIX for decisions. The Data
  Foundation (was DataIQ) built on Toolbox + sqlglot. The service desk first.
- **G-52, closed by the user:** for registered business tables only; our format, with ZEN behind a
  port.
- **G-53:** the Knowledge Foundation and the Data Foundation. The user applies the canon rename by
  hand (open, P3).

## Open questions and actions

- **Why did unsafe decisions rise on the attacked base, on the same three cases in every variant?**
  The hypothesis is the attacked base's separate extraction. Unchecked.
- **A sync-risk test** with a forgery the data can't contradict, such as a business definition.
- **G-50's pre-flight scripts** would have caught incident 1 (agent context) and incident 2 (the
  spend guard). This day is fresh evidence for building them.
