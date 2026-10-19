# Playbook: writing the record (notes, results, commits)

**Use it for** every `notes.md`, `results.md`, pre-registration amendment and commit message.
The record is what the next agent believes, so it gets the same rigour as the code.

## Before committing a report

- [ ] **Check every claim against the data with a query.** In the exam this caught two wrong
      claims, about x-holds and about identifier placement, before they went out.
- [ ] **grep for placeholders:** a digit followed by x (as in "22:3x"), `TBD`, `??`, "this commit",
      "parent". Write a hash or a time
      only after it exists. ([Provenance before it exists](../patterns.md#provenance-before-it-exists))
- [ ] **Separate observation from claim.** If a difference is inside the pre-registered noise, say
      "no difference". If a single run can't support it, say so.
- [ ] **Report abstention beside safety:** decided, right, unsafe, no decision, out of turns.
- [ ] **Report misses shared by every arm apart,** with their cause.
- [ ] **A deviations section:** every departure from the pre-registration, with its time, cause
      and who decided.
- [ ] **A spend table:** each component, including refused attempts and anything outside the cap.
- [ ] **Compute, don't type:** times from `date -u`, sums from a computation, counts from a count.
      Ledger times typed by hand went wrong; a hand sum was off by $2.
- [ ] **State findings with their conditions:** model, effort, instance fingerprint. Add a
      comparability line (before or after a named commit) to every headline number.
- [ ] **Failed predictions go under their own heading,** "reported, not tuned away".
- [ ] **Commercial lens, briefly:** what it means for the product. Keep it in the results, never in
      lessons.

## Commits

- [ ] Run the hygiene scan on the staged diff's added lines before every commit (the pattern is
      in memory, not here). Never write a secret's value anywhere; test for it as true or false.
- [ ] Don't force, amend or rewrite history. Runs are results: add to them, never rewrite them.
- [ ] One concern per commit, with a subject that says what changed and why it matters.
- [ ] **No conclusion in a commit message before the system has settled.** A pushed message is
      permanent.
- [ ] **Scrub provider error text from snapshots before committing.** Error messages can carry
      account identifiers; one did, at 9dc9ca9.
- [ ] Big artifacts: gzip snapshots. Transcripts are committed as they are, as in earlier runs.
      No file over 50 MB.

## Notes as the run goes

- [ ] A status banner on top, updated at each phase.
- [ ] A dated log with each event's time and its commit.
- [ ] Each deviation logged when it happens, not reconstructed later.
- [ ] Each user ruling quoted as given, with how it was read.
- [ ] **A superseded finding is flagged in place,** with a banner naming what superseded it. Never
      rewrite it silently.
- [ ] **A re-run never writes over committed results:** it gets a new name, and the harness refuses
      to overwrite a tracked file.
- [ ] **When a later run changes how an earlier one reads,** append an addendum to the earlier notes.
