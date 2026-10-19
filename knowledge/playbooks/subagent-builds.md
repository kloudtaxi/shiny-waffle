# Playbook: a subagent-driven build (a spec, a plan, tasks, reviews)

**Use it for** a multi-task build run with fresh subagents per task: B-06 (the OWM service), B-15
(proof rounds) and B-19 (finish mode) all ran this way. See R4 in
[patterns.md](../patterns.md).

## Before the first task

- [ ] Get the spec approved, with a diagram for every flow and section-by-section sign-off. Then the
      plan, then the user's choice of execution method.
- [ ] **If the build reuses a component in a new mode,** list the old mode's guarantees it relies on
      (for example "reset before every run"), and the new mode's answer to each, in the spec.
      ([The stranded lesson](../patterns.md#the-stranded-lesson))
- [ ] Read earlier build ledgers and run notes for every component you reuse.
- [ ] Ask for every credential, token and key the build will need now, not when the step is reached.
      ([The unpriced limit](../patterns.md#the-unpriced-limit))
- [ ] Check what a subagent's shell can do, Docker and network included, before planning steps that
      need it.

## During the build

- [ ] A review per task, with both verdicts (spec and quality). Record each ruling with what it costs
      if wrong.
- [ ] **Guards in the build must be able to fail.** Test each once with a case that should trip it.
      ([Success-shaped failure](../patterns.md#success-shaped-failure))
- [ ] After any commit that adds data the tests read (`runs/`, fixtures, stores), run the full suite.
- [ ] Every commit goes through the gated scan and lint.
      ([The advisory gate](../patterns.md#the-advisory-gate))

## At the end

- [ ] **One whole-branch review on the most capable model.** In all three builds, it found what the
      per-task reviews missed (3 important, 5 important, 1 critical).
- [ ] One fix wave, a scoped re-review, and the residuals ruled on and recorded.
- [ ] Push, then ask for the user's review with a link.
- [ ] Write open minors into a tracked open-items doc, and say which gaps they touch.
