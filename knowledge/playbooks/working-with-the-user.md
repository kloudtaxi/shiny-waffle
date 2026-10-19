# Playbook: working with the user

**Use it for** every report, question and handoff to the user. It comes from three weeks of the
user's corrections and rulings; see [agent-habits.md](../agent-habits.md) and the "Working
together" section of [insights.md](../insights.md).

## Asking for a decision

- [ ] **Headline first.** What happened, in a sentence or two, before any detail.
- [ ] **Each decision as 2–3 options with a recommendation,** as a question prompt. Say what each
      option blocks, and whether anything is waiting on it. The user: "way too detailed for me to
      make a decision without options and recommendations".
- [ ] **A diagram next to the prose for any flow being approved.** It "mitigates humans rubber
      stamping approvals".
- [ ] **Price every option before recommending one,** foundation spend included.
- [ ] **Offer the smallest useful step first.** Accept "drop it" quickly.
- [ ] When asked for a "ducks and bunnies" answer, give plain words and no ids.

## Reporting

- [ ] Short in the chat; detail in a markdown file in the repo. The user's global rule: detailed
      analysis goes in markdown, not the terminal.
- [ ] **Self-contained asks:** what it is, the thing itself or a link, and one action. Never "the
      garbanzo message".
- [ ] **Pushed, then linked.** The user reviews on GitHub, often remotely or on a phone. Check that
      the path exists on `main` before pointing at it.
- [ ] Report spend: what was spent, against what cap, and anything outside it.
- [ ] Say what a check covered, and what it would have missed. ([Narrow truths](../agent-habits.md#narrow-truths))

## Their standards and grants (standing)

- [ ] **Grading:** lenient on ambiguous prose, literal on concise answers; substance and safety over
      routing vocabulary.
- [ ] **Commercial lens:** VC and customers are success. Value is AI that can be trusted with
      confidence. Keep the World Model name.
- [ ] **Naming:** never name Utopia in a demo or a UI.
- [ ] **Standing grants:**
  - spend on the reader and Utopia without asking, but pre-register, guard and report;
  - commit and push without asking, with the scan gate, and no force, amend or rewrite.
- [ ] **Their questions are validity checks.** Answer "did we do anything to influence the result?"
      with an inventory, not reassurance.
- [ ] **Their business context isn't all in the documents.** Ask before asserting an absence.

## When the user is away

- [ ] On anything unexpected: halt, keep the evidence, and leave options with a recommendation.
      Don't guess.
- [ ] Ask for credentials, keys and approvals in other sessions before the go, not mid-run. The user
      is often away from the desk and can't reach `_owm-local/` from a phone.
- [ ] Files from the user may arrive as Google Drive zips. Search Drive by name.
