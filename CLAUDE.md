# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The **Northstar OWM Lab** is a seeded, byte-reproducible synthetic enterprise (the fictional
Northstar Industrial Systems). It exists to find the boundary between a *knowledge foundation*
(Utopia / OG-RAG) and the Sovera *Organizational World Model* (OWM). The generated dataset is
an instrument, not a sample: every conflicting, stale or fragmented piece of evidence is a
deliberate trap. `README.md` has the corpus table, the trap table and the scenario table, so
read it before changing anything under `truth/` or `src/northstar/generators/`.

Design rule: **evidence is messy, ground truth is clean.** Polyfactory supplies the structure
and Faker supplies the values, but neither decides what anything *means*. Meaning lives in
hand-authored `truth/`.

## Commands

```bash
uv sync                                      # install (Python ≥3.11, dev group included)
uv run northstar build                       # regenerate dataset/ (seed 20260923, scale small)
uv run northstar check                       # run the full coherence check, write nothing
uv run northstar build --scale large --out /tmp/ns-large   # 200 customers, 1000 requests
uv run pytest                                # all tests
uv run pytest tests/test_oracle.py::test_s07_hearsay_is_not_a_basis   # a single test
uv run ruff check && uv run ruff format --check
uv run mypy                                  # strict; covers src/ and tests/ (config in pyproject)
```

`northstar build` accepts `--seed`, `--scale {small,large}`, `--truth DIR` and `--out DIR`.
Line length is 100. mypy runs in `strict` mode with the pydantic plugin, **including on tests**.

## Architecture: the build pipeline

`build.assemble()` in `src/northstar/build.py` is the whole system in one function:

1. **`model.load_truth(truth/)`** loads the YAML into frozen pydantic models
   (`extra="forbid"`, so a typo in YAML fails loudly), then runs `_cross_check`, which
   raises `TruthError` on any dangling reference. It also rejects a relationship in
   `relationships.yaml` that contradicts the attribute form of the same fact (for example,
   `reports_to` against `manager`).
2. **`factories.build_background(truth, seed, scale)`** builds seeded noise (customers,
   employees, products, orders, discount requests) around the truth. Every generated approval
   obeys the pricing policy in force on its date, so the noise never contradicts the truth.
3. **`generators.generate_evidence()`** writes one module per source system (`crm`, `erp`,
   `documents` for Drive/Service, `emails`). The result is a list of `Artifact` objects.
4. **Corpora**: `truth/corpora.yaml` defines `base` plus variants, each being the base minus
   an `exclude` list of artifact ids.
5. **`oracle`** runs each scenario against *its* corpus and dispatches on `scenario.kind`
   (`discount_decision` → `decide`, `fact_selection` → `select_facts`, `provenance` →
   `trace_provenance`, `identity` → `resolve_identity`). `oracle.check()` then diffs the
   result against the scenario's hand-authored `expected:`. **Any mismatch raises
   `IncoherentTruthError` and nothing is written.**
6. **`write()`** deletes and rewrites only the paths in `OWNED` under the output dir. Any
   other file there is left alone.

### Artifact provenance tags (the core mechanism)

Each `Artifact` (`src/northstar/artifacts.py`) carries three tuples:

- `supports`: truth keys the artifact is **authoritative** evidence for. The oracle reasons
  *only* from the union of `supports` across the scenario's corpus (`oracle.available_keys`).
- `asserts`: fact ids from `truth/facts.yaml` that the artifact states outright.
- `mentions`: hearsay or precedent. It refers to a key without establishing it.

This is why S05's `REQUEST_EVIDENCE` comes from *removing documents* rather than from
assertion: point S05 at `base` and the build fails. When you add or edit a generator, getting
these tags right matters as much as the content does.

### The oracle is not the OWM

`oracle.py` is the lab's check on its own coherence. It implements the canonical discount
process (doc 03 §11). Nothing it outputs is evidence that any OWM behaves that way, so do not
evolve it into OWM logic. `owm/` (`owm-spec.md`, `ontology.yaml`) is the hand-authored
conceptual OWM. Every ontology type there is tagged `layer: foundation | owm` as a
*hypothesis*, and the experiment exists to move those tags.

## Invariants that tests enforce (and that are easy to break)

- **No single artifact contains a scenario's answer.** A `derived` fact is never in any
  artifact's `asserts`, and every `asserted` fact is in at least one. Authority is
  distributed: the policies and authority matrix name roles and never people, while the org
  chart and `employees.csv` name people and never contain `%`.
- **Source systems never use canonical `CUST-*` ids.** Resolving CRM-2048 ≡ C-1001 ≡
  ACME-MFG-2025 is the foundation's job.
- **Reproducibility.** The same seed must give byte-identical output. A different seed may
  change only background noise, never the results or the truth-carrying documents. All
  randomness goes through `SeededFactory` (each factory has its own `Faker`, reseeded with
  `seed + offset`) or the seeded `Faker` in `generate_evidence`. Generated dates must stay
  inside `WINDOW_START..WINDOW_END` in `factories/_base.py`; never use dates relative to today.
  Background names must not contain `RESERVED_TOKENS` (acme, blueriver, cedar, northstar).
  Reordering factory calls shifts the random stream, which changes the generated `dataset/`.
- **Background never adds a second VP Sales or CRO**, because approvers are resolved by role.

## Working rules

- **`dataset/` is generated and committed.** Never hand-edit it. Edit `truth/` (or a
  generator), run `uv run northstar build`, and commit the regenerated `dataset/` together with
  the change. Only the YAML manifests, the answer key and `DATASET.md` carry the
  "GENERATED … do not edit" header. The evaluation CSVs are fill-in sheets. Evidence artifacts
  deliberately have no header, because they must read as real source-system output, so do not
  add lab markers to them.
- **Adding a scenario**: add `truth/scenarios/NN-slug.yaml` with a `kind` from the four above
  and an `expected:` block. The build proves the expectation or refuses to write.
- **Adding a corpus variant** (for example, doc 02 Experiment A, which drops
  `organization_chart`): add it to `truth/corpora.yaml` and retarget a scenario with `corpus:`.
- **Adding a scale**: extend `SCALES` in `factories/background.py`.
- Truth entries marked `lab_extension: true` are not in doc 03. They are candidates for
  review, not canon.
- **Never load `dataset/answer-key/`, `dataset/evaluation/`, `truth/` or `site/` into the
  system under test.** Only `dataset/evidence/` and `dataset/evidence-variants/<name>/` go into
  Utopia, each as its own knowledge base. `site/index.html` is a self-contained landing page
  and counts as scenery.
- **Dependency direction**: this lab is standalone so that Polyfactory and Faker never enter
  the OWM's dependency closure. The OWM contract must not depend on this lab or on Utopia.

## Design docs and § references

Code comments cite the four design docs in `docs/owm-knowledge-foundation-experiment/`. The
filenames contain an em dash, so quote paths:

- **doc 01**, *OWM + Knowledge Foundation*: the foundation/OWM split.
- **doc 02**, *OWM + Utopia Experiment*: §1 decisions first, §5 deliberate ambiguity, §§6–9
  running the experiment, §9 Experiments A–F.
- **doc 03**, *OWM Domain Model + Ground Truth*: the canonical entities that `truth/`
  implements. §11 is the discount process (the oracle) and §21 is the canonical decision
  object that S01 must reproduce field for field.
- **doc 04**, *Synthetic Data Generation*: the Polyfactory/Faker split and the scale targets.

## Utopia experiment (runs, scripts, tracker)

- `runs/<date>-utopia-<sha>/`: one folder per live run: `notes.md` (start here, status banner on top),
  questions, answers, reader transcripts, snapshots. Runs are results: add to them, never rewrite them.
- `lab/utopia/`: the stdlib scripts that drive Utopia and the blind Opus reader. Its README lists the
  controls that define the experiment (blindness, hidden tools, fixed prompt, revoked tokens).
- `tracker/`: the Northstar Lab Ledger artifact (results matrix, human grades, findings). Human grades
  live in the artifact's `grades` collection; read them before scoring and never overwrite them.

## Local-only context (gitignored)

`_owm-local/` holds local notes on running Utopia (the knowledge foundation under test, a
separate Rust + web repo, `deeplethe/utopia` on the `dev` branch), its API surface and MCP
endpoint, plus a throwaway `utopia.mjs` CLI for poking at a running instance. **It contains
live credentials and tokens. Never copy anything from it into tracked files, commits or
artifacts.** `.vault/` is also local-only.
