# Insights

Durable things the lab has learned about measuring, cost and time, and working together. These
aren't failure patterns ([patterns.md](patterns.md)) or checklists ([playbooks/](playbooks/)).
They're how this work behaves, for an agent planning the next experiment. Each insight names its
evidence. Keep an insight only while the evidence still holds; when it stops holding, rewrite it
and say why.

> **Never-load notice.** Insights say how to run and measure, never what a foundation should
> extract, resolve or answer. Don't use them to tune or shape a foundation under test
> (CLAUDE.md, 854091d).

## Measuring

1. **A realistic end-to-end condition can hide the component under test.** Pair it with an
   isolating condition that removes the fallback path. The exam's arms decided alike with all
   tools, because the reader read documents. Only graph-only separated them.
   ([exam](retrospectives/2026-10-18-b20-northstar-exam.md#about-measuring))
2. **A ceiling turns a score into a gap.** Run the same reader with all the evidence handed to it
   (the gold ceiling), so a miss can be placed in the reader, the retrieval or the foundation.
   (experiments 5 and 6; the exam)
3. **Safety numbers need their abstention beside them.** A system that stops without deciding
   looks safe on any rule that counts only wrong decisions. ([exam](retrospectives/2026-10-18-b20-northstar-exam.md#about-measuring))
4. **A system differs from itself.** One extraction per base is one sample. Measure the spread
   between repeated builds before comparing two systems. ([exam](retrospectives/2026-10-18-b20-northstar-exam.md#about-measuring))
5. **The noise rule must be pre-registered,** and applied as written: in the exam, a difference
   smaller than the spread of three runs is no difference. A single run supports no claim of
   difference.
6. **An instrument between the reader and the system is part of the experiment.** The adapter, the
   contract reader, the slimming and the scorer each need their own guard, with a positive
   assertion, run on the exam's own provisioning path.
   ([exam, incident 2](retrospectives/2026-10-18-b20-northstar-exam.md#2-the-adapter-couldnt-see-todays-foundations-fresh-bases-caught-by-guard-3))

## Cost and time

7. **Turns are the cost.** All-tools reader answers cost about $0.30. Graph-only answers cost
   $0.76–0.89, with 27–47 tool calls, and multi-step SLA questions cost the most. A weak graph
   multiplies turns.
8. **Price per question from a pilot, then from the run itself.** A single average misprices a
   batch by 2–4×. A per-question model was within 7% on the exam's last 121 answers.
9. **The binding limit is usually not dollars.** Account windows, concurrency and permissions set
   the pace. The exam spent 73% of its cap and took twice its planned time.
10. **The supervisor shares the account with its workload.** A batch that empties the window
    stops the agent supervising it.

## Working together

11. **Pre-registration plus numbered amendments makes deviations cheap.** Every change carries a
    reason, a time and a decider, so the result stays credible through the surprises.
12. **The user decides best from short options with a recommendation.** The exam's four mid-run
    rulings were each one or two words.
13. **Sealing works when it's by design on both sides,** with counts-only watching and "share
    after the record". It needed no policing.
14. **Approval and permission are per session.** Plan them per session, before the go.
15. **Facts travel badly between agents.** Ids, "nothing changed" and summaries lose accuracy in
    every relay. Read at the source.
