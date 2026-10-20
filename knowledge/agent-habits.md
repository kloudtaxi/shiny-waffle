# Agent habits: how we go wrong, and what stops it

The other files are about systems. This one is about us, the agents doing the work. Each habit is
something an agent here actually did, usually surfaced by the user's correction. It says how it
showed up, why it's tempting, and the countermeasure that worked or would have. We write it plainly,
in the first person plural, with no blame: the point is that the next agent recognises the habit in
itself. R1–R5 are the retrospectives listed in [patterns.md](patterns.md).

| Family | Habit | Countermeasure |
|---|---|---|
| Claims | [Asserting from memory](#asserting-from-memory) | Read the source, then speak |
| | [Reading silence as absence](#reading-silence-as-absence) | "The document doesn't say X", never "X isn't so" |
| | [Explaining before checking](#explaining-before-checking) | n = 3 and the code first; "unknown" until then |
| | [Narrow truths](#narrow-truths) | Report what was checked, and what wasn't |
| | [Recording ahead of the facts](#recording-ahead-of-the-facts) | Write provenance after it exists; compute, don't type |
| Checks | [Trusting the label](#trusting-the-label) | Classify by content; distrust anything too fast or too cheap |
| | [Watching for the failures we expect](#watching-for-the-failures-we-expect) | Cover every end state; anomalies are events |
| | [Running the guard beside the action](#running-the-guard-beside-the-action) | `if check; then act`; lint and tests before the commit |
| | [Writing over the record](#writing-over-the-record) | New name per run; refuse to overwrite tracked results |
| Decisions | [Deciding for the user](#deciding-for-the-user) | While a decision is with the user, change nothing shared |
| | [Deciding before measuring](#deciding-before-measuring) | Run the scope query before the call |
| | [Recommending before pricing](#recommending-before-pricing) | Price every option first |
| | [Recommending to defer](#recommending-to-defer) | Recommend the small test now; a deferral has a date |
| | [Rules from a sample of one](#rules-from-a-sample-of-one) | Separate global from local causes |
| | [Minimising a risk the user wants gone](#minimising-a-risk-the-user-wants-gone) | Show the cost of removing it; let the user pick |
| Communication | [Burying the decision](#burying-the-decision) | Headline first; options with a recommendation |
| | [Handing over by internal name](#handing-over-by-internal-name) | Each ask is self-contained, with one action |
| | [Saying done before it's delivered](#saying-done-before-its-delivered) | Pushed, sent and linked, then say so |
| Planning | [Sizing for speed](#sizing-for-speed) | Size for the binding limit; leave the supervisor headroom |
| | [Building the human's step last](#building-the-humans-step-last) | Calibrate with the user after the first arm, on their device |

---

## Claims

### Asserting from memory
- **How it showed up:**
  - "No reader has run on credit or SLA", and "the live base holds MANIFEST.yaml". Both were wrong
    (R5);
  - "cheap on gpt-4o-mini", repeated from a note marked "not verified" (R1). The user: "so far we
    have spent $75 on gpt-4o" (09-29);
  - U-32's acceptance claims, stated to garbanzo before checking Utopia's code (R4);
  - pointing the user at a file that existed only on the lab's disk (R3).
- **Why it's tempting:** the answer feels known; after a compaction, a summary's confident line reads
  like memory.
- **Countermeasure:** run the one query or grep that settles it. If you can't, say "I haven't
  checked", or ask the user, who sees the bill. An estimate inherits the confidence of its least
  verified input.

### Reading silence as absence
- **How it showed up:** a product-thesis review said "no customer" and "no evidence", because the
  document didn't mention them. The user: design partners exist (10-08, R3).
- **Why it's tempting:** in a review, the document feels like the whole case.
- **Countermeasure:** write "the document doesn't say X". Ask about business context before
  asserting an absence.

### Explaining before checking
- **How it showed up:**
  - "variance dominates", from one run per cell, overturned at n = 3 two hours later (R1);
  - "G5 was spec-local", inferred from an effect without opening the kernel, and corrected the same
    morning (R2).
- **Why it's tempting:** a mechanism that fits the effect feels like understanding.
- **Countermeasure:** before writing a cause, open the code or data that would show it, or run the
  replication that would settle it. Write "unknown" or "hypothesis" until then.

### Narrow truths
- **How it showed up:**
  - "no answer was cut off" was true, and hid 186 hollow answers;
  - "parity passes" was true, with zero hits (R5);
  - "held" was reported for holds that were luck (R2).
- **Why it's tempting:** a narrow true statement is easy to defend, and it closes the question.
- **Countermeasure:** say what was checked and how, and what the check would have missed.

### Recording ahead of the facts
- **How it showed up:**
  - "22:3x" and "this commit's parent" committed (R5);
  - "no new calls", which was 6, and "about 28", which was 22 (R2);
  - a $33.46 hand sum that was $31.46, and Ledger times typed as round numbers, some local time
    labelled UTC (R3);
  - "flagged to garbanzo" written before it was sent (R4);
  - a conclusion in a pushed commit message before the system had settled (R1).
- **Why it's tempting:** writing the record in the same breath as the work feels efficient.
- **Countermeasure:**
  - write hashes and times after they exist;
  - times from `date -u`, sums and counts from a computation;
  - check claims against the data before committing, and grep for placeholders.

## Checks

### Trusting the label
- **How it showed up:**
  - the monitor and the first inventory both read `subtype` and saw "success" on refusals (R5);
  - a run note called an answer a reasoning slip from its decision block, while its prose was right
    (R1).
- **Why it's tempting:** status fields exist to be read, and reading content is more code.
  - "blind subagent" was a label in a brief, not a property of the runtime. The subagents had the
    CLAUDE.md files and the memory index loaded (R6).
- **Countermeasure:** classify by content (cost, turns, text, a decision present). Treat answers that
  are too fast, cost $0 or are identical as alarms. For a property such as blindness, probe for it:
  ask the agent what context it was given.

### Watching for the failures we expect
- **How it showed up:** the first watch flagged running out of turns as an API error, and missed the
  real refusals (R5).
- **Why it's tempting:** a monitor gets written for the failure in mind.
- **Countermeasure:** list every end state, and match all of them. Ask "if this died now, or returned
  nothing, would the filter say anything?"

### Running the guard beside the action
- **How it showed up:**
  - `scan; commit; push` published the owner's email local part (R4);
  - 59 of 82 commit commands in one period ran no scan, and 23 ran it ungated (R3);
  - lint failures committed twice, one still failing on main (R3);
  - a data commit broke a test that expected an empty store, found 14 hours later (R4).
- **Why it's tempting:** the commit is the last step of a long turn, and printed output feels like
  checking.
- **Countermeasure:** one commit helper that gates on the scan's exit code, lints the staged files,
  runs the suite when data the tests read changes, and shows `git status` for any folder being
  handed off.

### Writing over the record
- **How it showed up:** a re-run wrote into committed results files. It was caught and restored
  before the commit (R2).
- **Countermeasure:** a harness takes an output suffix and refuses to overwrite a tracked file.

## Decisions

### Deciding for the user
- **How it showed up:** with a governance choice pending, the lab sent the change before asking. The
  permission check refused it, and the user then chose (R1).
- **Why it's tempting:** stopping spend felt obviously right, so the decision seemed made.
- **Countermeasure:** while a decision is with the user, change nothing shared. After any setting
  change, by anyone, read the state back.

### Deciding before measuring
- **How it showed up:**
  - a call on one scenario's input was made three minutes before its scope was measured: 24 of 28
    shared the cause;
  - a recommendation was approved, then found to add duplicates everywhere, and was asked again 12
    minutes later (R3).
- **Why it's tempting:** the decision is in front of you, and the scope query feels like a detour.
- **Countermeasure:** run the scope query (how many share the cause; what else the change touches)
  before making or recommending the call.

### Recommending before pricing
- **How it showed up:** a rebuild was recommended with its cost unknown. The user: "Last time it cost
  over $80+". The recommendation flipped to the $0 option (R4).
- **Countermeasure:** price every option from past spend before recommending one.

### Recommending to defer
- **How it showed up:** twice the lab recommended folding a fresh test into a later set. One never
  ran (G-31, G-33, 12 days and counting). The user overrode the other, and that run found G-36 (R3).
- **Why it's tempting:** bundling looks like saving a run.
- **Countermeasure:** recommend the small test now, unless it costs more than a stated threshold. A
  deferral names its date and its fallback.

### Rules from a sample of one
- **How it showed up:** the two-strike rule, written after one failure, counted the account's limit
  against individual questions. The user had to correct it (R5).
- **Countermeasure:** before writing a rule mid-run, ask whether the cause is local to one item or
  hits every item. Commit the rule with its time, and take any change to the user.

### Minimising a risk the user wants gone
- **How it showed up:** "No real harm", about the operator's identity in the runner. The user:
  "actually run claude -p let's get it out [of] our way" (10-14, R4).
- **Countermeasure:** give the cost of removing the risk beside the mitigation, and let the user
  pick.

## Communication

### Burying the decision
- **How it showed up:**
  - "Do I need to decide now? if so give some 3 options and your recommendation" (10-05);
  - eight hours later: "this is way too detailed for me to make a decision without options and
    recommendations" (10-06, R2 and R3).

  Once the decisions were put as options, three were answered in four minutes.
- **Why it's tempting:** the report is written as the work unfolds, and appending the decisions
  feels complete.
- **Countermeasure:**
  - headline first;
  - each decision as 2–3 options with a recommendation and what it blocks (a question prompt);
  - detail in the notes;
  - a diagram for any flow being approved;
  - when asked, a plain "ducks and bunnies" version.

### Handing over by internal name
- **How it showed up:** "what's 'The garbanzo message' and 'flagged for garbanzo'? And what action do
  I need to take?" (10-12, R4).
- **Countermeasure:** each ask says what it is, includes the thing itself or a link, and names one
  action.

### Saying done before it's delivered
- **How it showed up:**
  - a spec was committed locally and pointed to by path. The user: "Do you push the commits? I don't
    see the file in main" (10-14, R4);
  - a handoff file was left untracked (R3).
- **Countermeasure:** push, then link the URL. Check that the path exists on `main` before pointing
  the user at it. Say "sent" only after it was.

## Planning

### Sizing for speed
- **How it showed up:** three arms ran at 3–4 workers each without a pilot at that concurrency. The
  account's window emptied four times, and the supervising session stopped with it (R5).
- **Why it's tempting:** wall-clock is visible; the account's window isn't, until it's empty.
- **Countermeasure:** find the binding limit before choosing the concurrency. Leave the supervisor
  headroom. Prefer a run that finishes slowly to one that stops repeatedly.

### Building the human's step last
- **How it showed up:**
  - about 390 answers were in the Ledger with no human grade;
  - instructions came only when the user asked: "I'm holding us up. Can you please give me or tell
    me where I can find instructions";
  - the Ledger failed on a phone and showed raw JSON (R1).
- **Why it's tempting:** the human step is slow, so it gets scheduled last.
- **Countermeasure:** after the first arm, give the user a short, targeted grading list, in a tool
  that works where they are. Calibrate before scaling.
