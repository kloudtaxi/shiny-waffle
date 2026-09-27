# OWM spec — Northstar lab (v0.1, candidate)

The conceptual model the lab is trying to **discover**, written down so we can
see where the knowledge foundation stops and the OWM has to start. It is
deliberately independent of Utopia/OG-RAG: the OWM contract must not depend on
the foundation beneath it.

## The split

| Knowledge foundation (Utopia / OG-RAG) | Organizational World Model |
|---|---|
| Evidence, documents, extraction | Meaning, domain model, ontology |
| Entities, identity, provenance | Relationships in organizational context |
| Temporal facts | Temporal organizational *state* (which policy governs now) |
| Search, graph | Policies, authority, exceptions, decisions |

**Knowledge foundation answers:** *what do we know, and what evidence supports it?*
**OWM answers:** *what does it mean here, and what should happen?*

## Layers in `ontology.yaml`

Every type is tagged `layer: foundation` or `layer: owm`. That tag is a
**hypothesis**. The experiment's job is to move tags when the evidence says so:
if Utopia composes "Sarah → reports to Michael → VP Sales → band 10–20%" unaided,
then `AuthorityBand` was not an OWM concept after all.

## The five questions the dataset makes answerable

| # | Question | Teaches |
|---|---|---|
| S01 | Can Sarah approve Acme's 15%? | authority + policy + relationship |
| S02 | Can we offer Acme 18%? | exception as a constraint |
| S04 | Could Sarah have approved 15% last year? | temporal organizational state |
| S07 | Why is Acme eligible for 15%? | evidence + provenance |
| S05 | What if the contract is missing? | uncertainty + evidence requirements |

S03 (product scope), S06 (conflicting exceptions) and S08 (similar names) come
from doc 03 and doc 02's experiments.

## Candidate OWM capabilities (the `owm_needed` rows)

Each is a place where the foundation holds the pieces but not the implication:

1. **Authority composition:** role + reporting line + policy band gives the required approver.
2. **Eligibility ≠ authority:** a contract permits a price; it does not empower a person.
3. **Temporal state:** the same request gets a different answer under a different policy.
4. **Narrow exceptions:** a product-scoped term must not generalise.
5. **Honest failure:** refuse to decide when the basis is hearsay (`REQUEST_EVIDENCE`).
6. **Decisions as objects:** outcome, reasons and evidence, recorded (doc 03 §21).

## Open questions this lab should answer

- What is organizational *state*, as opposed to a set of temporal facts?
- Which inferences does the OWM assert, and which does it keep as derived?
- What needs human confirmation before it enters the model?
- How does a recorded decision feed back into the model?
