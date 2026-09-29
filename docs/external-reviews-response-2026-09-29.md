# Response to the external reviews (2026-09-29)

Three reviews by an external observer, written at different points in the run:

- **Review 1:** after the correction run (Sep 28).
- **Review 3:** after the request-record arm (15/15, small).
- **Review 2:** after the B1 scale result.

None has seen the held-out decisions (`runs/2026-09-28-utopia-aad5b06-scale-large/heldout/`).
This note says where the evidence supports them, where it doesn't yet, and what I'd run next.

## Where they're right, and the lab agrees

1. **The thesis shift.** A capable agent with retrieval, the procedure and the request record
   reconstructs the organization's decision at query time. At scale, the all-tools reader gets
   45 of 45 on S01–S05 with and without curation, and 15 of 18 on held-out decisions. So
   "RAG can't reason across organizational relationships" is refuted here. The reviews'
   reframing ("the foundation remembers what the organization said; the OWM remembers how it
   works") is the right direction for positioning.
2. **Procedures, outcome definitions and decision inputs are OWM primitives, not "more
   entities".** This is the lab's own conclusion (`request/notes.md`, `b1/notes.md`).
3. **Applicability as a first-class concept** (Review 3 §6). **The held-out run now supports
   this directly.** S13 failed 6 of 6 because the procedure scopes special terms by product and
   date, but says nothing about *customer*. Every reader resolved the identity correctly and
   still had no rule. That's an applicability gap in the OWM's own procedure, found by a test
   it wasn't written for.
4. **Identity as organizational identity claims, not names** (Reviews 1 and 2). This is
   supported by upstream issue 3 (a correct merge dropped C-1001 and CRM-2048 from lookup),
   S08, and the scale run's "Acme" attached to the wrong customer.
5. **Don't build a decision engine or a big agent runtime yet.** Agreed. Nothing so far
   needs one.

## Factual corrections

- **Review 2, "what the foundation lost".** The list merges the small and scale runs. CSV
  truncation happened at *small* scale (all six CSVs). At scale there was none, and DR-9001
  kept its justification in base. At scale the 10% AE limit and the 2025 band sentence did
  reach the graph. What scale lost: the exception's 15%, the agreement's terms (a bare name),
  all reporting lines, and a correct "Acme" attachment.
- **Review 3 §12, "scale it to 200 customers, ~40 employees, ~80 products, ~1,000
  requests…".** Already done: that is the scale arm
  (`runs/2026-09-28-utopia-aad5b06-scale-large/`).
- **Review 3 §5, "facts + procedure got S03 right where the stronger text reader did
  not".** True only for the text reader *without* the procedure. With the procedure and the
  record, the text reader gets S03 right in 3 of 3 runs on the *uncurated* graph (B1PR,
  B1nPR). The procedure's outcome definitions did the work, not the curated facts.
- **Review 1 §5, "evidence can remain unstructured; organizational semantics should become
  typed".** Only partly supported now. The text reader reached 45/45 from untyped text. Typing
  matters for **graph-only or deterministic consumers**, and the curated graph-only reader
  also reached 15/18 on held-out. The better principle is to type what a deterministic
  consumer needs (authority bands, validity windows, applicability), not all semantics.

## Where I'd push back

1. **Persistence, governance and consistency are the proposed value, not a finding yet.**
   Nothing in the lab has tested them. So far it shows that reconstruction *works*. It hasn't
   shown that persisting the result is better. Before that goes in a PRD as the moat, the
   next experiment should be able to fail.
2. **A naive persistence test is rigged.** "Write the decision to the OWM, then ask about it"
   beats a reader without memory by construction. The fair baseline is the same decision
   record **written back into the knowledge foundation as a document**; Utopia would ingest it
   like any other evidence. The real boundary question is *where decision memory should
   live*: a typed decision object in the OWM, or a decision document in the foundation.
3. **Consistency has little headroom in this lab.** The text reader was 45/45 across runs.
   Any persistence gain has to come from somewhere else: correctness **after the evidence
   changes**, cost and latency per decision, or cross-agent agreement under conflicting
   evidence.
4. **Contradiction detection is only partly OWM's.** Utopia already checks asymmetric,
   irreflexive and functional axioms, but only on *typed* relations. In all four Northstar KBs
   nothing is typed except names (0 phrase bindings, 0 other typed facts), so the checker
   never had anything to check. Role-rank
   constraints ("a VP doesn't report to an AE") need organizational semantics and are OWM's.
   Cycle and uniqueness checks could live in either place.

## What I'd run next, in order

| # | Experiment | Question it answers | Cost |
|---|---|---|---|
| 1 | **Procedure v2 + fresh held-out** | Does adding an applicability rule (customer, product, date) fix the S13 class without breaking S01–S14? New held-out scenarios, pre-registered, no new evidence | Claude only, ≈ $10 |
| 2 | **Adversarial organization** (Review 1 exp. 2) | Does reconstruction survive without title priors? The approver is "Director, Strategic Commercial Operations" by delegation; authority flows role → delegation → policy | New truth and evidence, so ingestion into the *small* KBs only (gpt-4o, small); Claude ≈ $10 |
| 3 | **Decision memory, with a fair baseline** (all three reviews) | After the evidence *changes* (a policy revision, a revoked exception), can agents answer "what did we decide on DR-9001, under which policy, and was it valid then?" Arms: (a) no memory, (b) the decision written back to Utopia as a document, (c) a typed OWM decision object. Measure correctness after change, cross-agent agreement, cost and turns | (b) ingests a few small documents (gpt-4o, cents); Claude ≈ $15 |
| 4 | **Constraint check as a deterministic OWM function** | Run `reports_to` acyclicity and role-rank checks over the foundation's facts: are the small run's inverted edges flagged, not silently fixed? | No model calls |

Experiment 3 is the one the reviews care about most, and the one that decides whether
"persistent organizational understanding" is a measured advantage or a positioning line. 1 and
2 come first because they're cheaper and they test the finding persistence rests on: that
reconstruction works.
