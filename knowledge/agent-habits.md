# Agent habits: how we go wrong, and what stops it

The other files are about systems. This one is about us, the agents doing the work. Each habit is
something an agent here actually did. It says how it showed up, why it's tempting, and the
countermeasure that worked or would have. Write entries plainly, in the first person plural, with
no blame: the point is that the next agent recognises the habit in itself.

| Habit | Countermeasure |
|---|---|
| [Asserting from memory](#asserting-from-memory) | Read the source, then speak |
| [Trusting the label](#trusting-the-label) | Classify by content; distrust anything too fast or too cheap |
| [Watching for the failures we expect](#watching-for-the-failures-we-expect) | Monitors cover every end state; anomalies count as events |
| [Sizing for speed](#sizing-for-speed) | Size for the binding limit; leave the supervisor headroom |
| [Rules from a sample of one](#rules-from-a-sample-of-one) | Separate global from local causes before writing a rule |
| [Recording ahead of the facts](#recording-ahead-of-the-facts) | Write provenance after it exists; check claims before committing |
| [Narrow truths](#narrow-truths) | Report what was checked, and what wasn't |

---

## Asserting from memory

- **How it showed up:**
  - "No reader has run on credit or SLA": experiments 5 and 6 had.
  - "The live base holds MANIFEST.yaml": it didn't. A plan's "39 files" was taken for the base.
  - Both were said to the user, then corrected.
- **Why it's tempting:** the answer feels known, and checking feels slow. After a compaction, a
  summary's confident line reads like a memory.
- **Countermeasure:** before stating live state or history, run the one query or grep that settles
  it. If you can't, say "I haven't checked". When wrong, correct it everywhere it went: to the
  user, in the notes, to peers, and in memory.

## Trusting the label

- **How it showed up:** the monitor read `subtype`, and so did the first inventory after the stop.
  Both saw "success" on 186 refusals. The inventory's report, "no answer was cut off", was true,
  and hid the problem.
- **Why it's tempting:** status fields exist to be read, and reading content is more code.
- **Countermeasure:** classify by content (cost, turns, text, a decision present). Treat answers
  that are too fast, cost $0 or are identical as alarms. The exam's problem was found by a
  14-second pass, not by a check. Make that kind of finding deliberate.

## Watching for the failures we expect

- **How it showed up:** the first watch flagged `error_max_turns` as an API error (noise), and
  missed the real refusals (silence).
- **Why it's tempting:** a monitor gets written for the failure in mind.
- **Countermeasure:** list every end state before writing the filter, and match all of them. Before
  arming it, ask: "if this died right now, or returned nothing, would the filter say anything?"

## Sizing for speed

- **How it showed up:** three arms at 3–4 workers each ran together, to finish sooner. Nobody had
  piloted at that concurrency. The account's window emptied four times, and the supervising session
  stopped with it each time.
- **Why it's tempting:** wall-clock is visible, and the account's window isn't, until it's empty.
- **Countermeasure:** find the binding limit before choosing the concurrency. Leave the
  supervisor headroom. Prefer a run that finishes slowly to one that stops repeatedly.

## Rules from a sample of one

- **How it showed up:** the two-strike rule was written after one failure. It counted the
  account's limit against individual questions, and needed the user's ruling to fix.
- **Why it's tempting:** the run is waiting, and the failure in front of you looks like the only
  kind.
- **Countermeasure:** before writing a rule mid-run, ask whether the cause is local to this item
  or hits every item. Write it to separate the two. Commit it with its time, and take any change
  to the user.

## Recording ahead of the facts

- **How it showed up:**
  - "22:3x" and "this commit's parent" were committed into the notes;
  - a results draft said the adapter doesn't serve x-holds, and that one arm put identifiers on no
    documents. Both were wrong, and caught before the commit by checking.
- **Why it's tempting:** writing the record in the same breath as the work feels efficient.
- **Countermeasure:** write hashes and times after they exist. Run a claim-by-claim check against
  the data before committing any report, and grep for placeholders.

## Narrow truths

- **How it showed up:** "No answer was cut off mid-way" was literally true (every file had a
  result event), and missed 186 hollow answers. "Parity passes" was literally true, with zero
  hits.
- **Why it's tempting:** a narrow true statement is easy to defend, and it closes the question.
- **Countermeasure:** report what was checked and how ("every file has a result event; costs not
  yet checked"). When a check passes, say what it would have missed.
