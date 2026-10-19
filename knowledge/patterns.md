# Patterns

The recurring shapes behind the lab's incidents. A pattern earns a place here when it has bitten
at least once, with consequences, or when the same kind of mistake has happened twice. Each one
says:
- **how to spot it early** (its signature);
- **why it happens** (the root cause);
- **what counters it.**

Its evidence is in the retrospectives. When you meet a pattern again, add the new evidence; don't
start a new entry. If a pattern hasn't bitten for a long time, say so, and leave it in.

| Pattern | One line |
|---|---|
| [Success-shaped failure](#success-shaped-failure) | A check passes because it looked only for failure labels |
| [The rehearsal isn't the performance](#the-rehearsal-isnt-the-performance) | The dry run ran somewhere, or at some scale, the real run didn't |
| [The unpriced limit](#the-unpriced-limit) | The run stops on a limit nobody budgeted |
| [Rules born mid-run](#rules-born-mid-run) | A rule invented under pressure fits only the failure in front of you |
| [Second-hand facts](#second-hand-facts) | A document or message is taken for the system it describes |
| [Cached absence](#cached-absence) | "Nothing there" is remembered after something arrives |
| [The metric that rewards giving up](#the-metric-that-rewards-giving-up) | Doing nothing scores as well as doing right |
| [The arm-independent miss](#the-arm-independent-miss) | A miss shared by every arm is read as a finding about the arms |
| [Provenance before it exists](#provenance-before-it-exists) | A hash, time or result is written before it's known |

---

## Success-shaped failure

**Signature:**
- a pass with suspicious numbers: zero hits, $0 cost, 250 ms answers, a pass of 47 answers in 14
  seconds;
- a verdict that holds as well for empty input as for full;
- a status field that says `success` on a reply nobody read.

**Root cause:** the check asks for the absence of a failure label ("no mismatch", "subtype isn't
an error") instead of positive evidence of success ("hits exist", "work was done", "a decision is
present"). An empty or refused result has no failure label, so it passes.

**Counter:**
- Assert the positive: a non-empty result, a non-zero cost, the expected count. Every comparison
  first checks that both sides are non-empty.
- Classify an agent's or API's result by its **content**, never its status field. A refusal can
  arrive as `is_error: true`, subtype `success`.
- Test the check on a known-bad input (empty, refused) before trusting its pass.
- Read the numbers under a verdict, not only the verdict.

**Evidence:**
- [Exam, incident 1](retrospectives/2026-10-18-b20-northstar-exam.md#1-refusals-saved-as-answers-203-attempts-four-stops-two-days):
  203 session-limit refusals saved as answers.
- [Exam, incident 2](retrospectives/2026-10-18-b20-northstar-exam.md#2-the-adapter-couldnt-see-todays-foundations-fresh-bases-caught-by-guard-3):
  parity passed with zero adapter hits.

---

## The rehearsal isn't the performance

**Signature:** the dry run used a different instance, data path, scale, concurrency or kind of
question than the real run. Typical tells: the live base instead of a fresh one; one worker
instead of ten; all-tools answers only.

**Root cause:** rehearsals are built from what's at hand, and what's at hand differs in exactly
the ways nobody thought to list. The live base had version rows; fresh uploads don't. One worker
never meets the account's limit.

**Counter:**
- Rehearse through the **same provisioning path** as the real run: a fresh instance, the same load
  command, at least one file.
- Pilot at the **real concurrency**, and long enough to meet the real limits.
- Price from a pilot of **every variant and process**, then per question, never from one average.
- Write down how the rehearsal differs from the real run, and close each difference or accept it
  on purpose.

**Evidence:**
- [Exam, incident 2](retrospectives/2026-10-18-b20-northstar-exam.md#2-the-adapter-couldnt-see-todays-foundations-fresh-bases-caught-by-guard-3):
  the dry run was on the live base, which has version rows, while the exam's fresh bases didn't.
- [Exam, incident 3](retrospectives/2026-10-18-b20-northstar-exam.md#3-the-pilot-priced-the-run-at-a-quarter-to-a-half-of-its-cost):
  the cap was set before any graph-only answer had run.

---

## The unpriced limit

**Signature:** a run stops, or stalls, on something other than the dollar cap: the account's
session limit, a rate limit, a permission prompt in another session, a turn cap, a machine going to
sleep.

**Root cause:** budgets list dollars, because dollars are what get approved. Every other limit is
discovered by hitting it. The supervising agent shares the account's limit with the workload, so
when the workload hits it, the supervisor stops too.

**Counter:**
- Budget every limit in the plan: dollars, account windows, rate, concurrency, turns, wall-clock,
  and the permissions each session needs.
- Pre-register what happens at each one: halt, keep aside, resume, or the user decides.
- Leave the supervisor headroom: lower concurrency, or a check of the account's recent refusals
  before each batch.
- Clear every session's permissions before the "go", not after.

**Evidence:**
- [Exam, incident 1](retrospectives/2026-10-18-b20-northstar-exam.md#1-refusals-saved-as-answers-203-attempts-four-stops-two-days):
  four session-limit stops, 18 hours waiting.
- [Exam, incident 6](retrospectives/2026-10-18-b20-northstar-exam.md#6-the-go-stalled-in-the-other-session):
  the other session's permission gate.

---

## Rules born mid-run

**Signature:** a rule for handling a failure is written after the failure appears, and while the
run is still going. It works for that failure, and is wrong for the next one.

**Root cause:** failure handling wasn't pre-registered, so it's designed under pressure from a
sample of one. Such rules confuse causes local to one item (this question failed) with causes that
hit every item (the account is out).

**Counter:**
- Pre-register a **failure taxonomy** before the first answer: answered, out of turns, refused
  (account), refused (rate), crashed, no output. Say for each whether it's an answer, a retry or a
  halt.
- Split causes local to an item from global ones. Global causes never count against an item.
- When a new rule is unavoidable: commit it with its time, before any answer it affects; apply it
  to every arm; and take any change to the user.

**Evidence:** [exam, incident 4](retrospectives/2026-10-18-b20-northstar-exam.md#4-a-failure-rule-made-mid-run-then-corrected-by-the-user):
the two-strike rule counted account refusals.

---

## Second-hand facts

**Signature:** a claim about live state comes from a plan, a doc, a summary, a progress notice or
a peer's message. Tells: "39 files"; "no reader has run on X"; ids copied from a chat.

**Root cause:** documents and messages describe a system at some moment, through someone's eyes.
Reading them is faster than asking the system, so they get used as if they were the system.

**Counter:**
- Before asserting live state, read it at the source: the base, the store's own listing (K1), git,
  or the run folder.
- Relay an identifier only as read from its store.
- Check a peer's claim before passing it on. A compaction summary is a lead, not evidence.
- When a claim turns out wrong, correct it everywhere it went: to the user, in the notes, to the
  peer, and in memory.

**Evidence:** [exam, incident 5](retrospectives/2026-10-18-b20-northstar-exam.md#5-facts-at-second-hand):
the relayed kb ids, "no reader has run" and the manifest in the live base.

---

## Cached absence

**Signature:** a fix lands upstream, and nothing changes downstream until a restart.

**Root cause:** an empty or "not found" result is cached with no expiry or invalidation, so the
system keeps remembering nothing.

**Counter:**
- Don't cache emptiness, or give it a short expiry.
- After fixing data under a running service, check the service's answer, not only the data.

**Evidence:** [exam, incident 2](retrospectives/2026-10-18-b20-northstar-exam.md#2-the-adapter-couldnt-see-todays-foundations-fresh-bases-caught-by-guard-3):
the adapter cached the empty version lists.

---

## The metric that rewards giving up

**Signature:** a system that does less scores as well as, or better than, one that does more. An
empty reader gets a perfect precision. An arm that never decides has no unsafe answers.

**Root cause:** the metric counts only one kind of error and leaves abstention out.

**Counter:**
- Report each rate beside its coverage. For decisions, that's decided, right, wrong and unsafe,
  no decision, and out of turns.
- Run every metric once on empty input, to see what giving up scores.

**Evidence:** [exam insights](retrospectives/2026-10-18-b20-northstar-exam.md#about-measuring):
in graph-only SLA, the arm that mostly didn't decide had fewer unsafe answers than the arm that
did.

---

## The arm-independent miss

**Signature:** the same miss, in the same way, on every arm.

**Root cause:** the miss comes from the shared parts of the instrument (the reader, the prompt,
the scorer), not from what differs between arms.

**Counter:** report such a miss apart, with its cause. Never read it as a difference between the
arms, or as a sameness. If it matters, fix it in the instrument, as its own pre-registered
condition.

**Evidence:** [exam insights](retrospectives/2026-10-18-b20-northstar-exam.md#about-measuring):
the reader's prose and its decision block disagreed, the same way on every arm.

---

## Provenance before it exists

**Signature:** a placeholder such as "22:3x", "this commit's parent" or "TBD" reaches a commit.
So does a claim written from memory of the data rather than from the data.

**Root cause:** a record is written in the same breath as the work it records, before the hash,
time or number it cites exists.

**Counter:**
- Write provenance after the fact it names exists: the commit made, the time read, the number
  computed.
- Before committing a report, check each claim against the data with a query, not memory.
- grep the staged record for placeholders.

**Evidence:** [exam, incident 7](retrospectives/2026-10-18-b20-northstar-exam.md#7-small-errors-in-the-written-record).
