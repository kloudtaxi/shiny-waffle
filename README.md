# Northstar OWM Lab

A seeded, reproducible **synthetic enterprise laboratory** for the Sovera OWM.
The fictional company is Northstar Industrial Systems. It exists to answer one
question:

> **Can we find the boundary between knowledge and organizational understanding?**

The dataset is an instrument, not a sample. Every messy, fragmented or
conflicting representation in it is there on purpose, so that particular
failures become *possible* and therefore observable. Nothing here generalises
by sampling logic.

```
Scenario / domain truth  →  Polyfactory  →  Faker  →  Evidence corpus  →  Utopia  →  OWM evaluation
   (hand-authored)          (structure)     (values)     (dataset/)       (foundation)   (answer key)
```

**Design rule:** evidence is messy, ground truth is clean, and the OWM is the
continuously evolving model between them. Neither generator library gets to
decide what anything *means*.

---

## Quick start

```bash
uv sync
uv run northstar build              # writes dataset/  (seed 20260923, scale small)
uv run northstar check              # verify truth coherence, write nothing
uv run northstar build --scale large --out /tmp/northstar-large   # 200 customers, 1000 requests
uv run pytest                       # 26 tests: coherence, corpus properties, reproducibility
```

The same seed produces **byte-identical** output. A different seed changes only
the background noise. The truth, the documents that carry it and the expected
answers stay exactly the same (both properties are tested).

## Site

`site/index.html` is the front door to the experiment: the fictional Northstar
company site, with the lab, the scenarios and the dataset "behind the panel".
It is a single self-contained page; open it in a browser. Scenario pages will
sit next to it as `site/scenarios/<id>.html`. The site is scenery. **Never load
it into the system under test**; the canonical facts live in `truth/`.

## Layout

```
northstar-owm-lab/
├── truth/                      HAND-AUTHORED laboratory control — never loaded into Utopia
│   ├── organization.yaml         org, systems, roles
│   ├── entities.yaml             customers, accounts, employees, products, contracts,
│   │                             pricing exceptions, orders, discount requests
│   ├── policies.yaml             2025 / 2026 pricing policies as authority bands
│   ├── relationships.yaml        canonical edges (cross-checked against entities)
│   ├── facts.yaml                the evaluation sheet rows (asserted vs derived)
│   ├── corpora.yaml              base corpus + variants (e.g. scenario 5)
│   └── scenarios/01…08.yaml      question, as-of date, corpus, expected result
├── owm/                        HAND-AUTHORED conceptual OWM — independent of Utopia
│   ├── owm-spec.md
│   └── ontology.yaml             entity/relationship types tagged foundation vs owm
├── src/northstar/
│   ├── model/                    typed truth + loader that refuses dangling references
│   ├── factories/                Polyfactory + Faker background (seeded, policy-consistent)
│   ├── generators/               crm · erp · documents · emails  → evidence artifacts
│   ├── export/                   csv · markdown · yaml
│   ├── oracle.py                 reference decision procedure (doc 03 §11)
│   └── build.py, cli.py
├── tests/
└── dataset/                    GENERATED — rebuild, never hand-edit
    ├── evidence/                 ← load this into Utopia as the "Northstar" knowledge base
    │   ├── structured/           6 CSVs (CRM, ERP, HR)
    │   ├── documents/            11 Markdown docs (Drive, Service, email)
    │   └── MANIFEST.yaml
    ├── evidence-variants/
    │   └── missing-contract-evidence/   ← load as a separate KB for scenario 5
    ├── answer-key/               expected results, evidence map, temporal facts — DO NOT LOAD
    ├── evaluation/               fact-checklist.csv, scenario-scorecard.csv — fill these in
    └── DATASET.md
```

## The evidence corpus (17 artifacts)

| Artifact | Source system | What it carries (and what it deliberately doesn't) |
|---|---|---|
| `crm_accounts.csv` | CRM | CRM-2048 "Acme Manufacturing", owner Sarah Chen, Strategic |
| `customers.csv` | ERP | C-1001 **"Acme Mfg. Holdings"**, same DUNS/address, no CRM id |
| `discount_requests.csv` | CRM | DR-9001 (pending) and **DR-8104, the 2025 precedent**. Uses SKUs and emails, not ids |
| `employees.csv` | ERP/HR | titles and manager ids, no percentages |
| `products.csv`, `erp_orders.csv` | ERP | item master; SO-7001/7002 by ERP id |
| `pricing_policy_2025.md` / `_2026.md` | Drive | authority by **role**, never by name |
| `approval_authority_matrix.md` | Drive | 2026 bands by role, never by name |
| `organization_chart.md` | Drive | names and reporting lines, never percentages |
| `acme_master_supply_agreement.md` | Drive | ref **ACME-MFG-2025**, "Acme Mfg. Holdings d/b/a Acme Manufacturing", 15% on NS-500 |
| `acme_pricing_exception.md` | Drive | EXC-ACME-NS500-15, NS-500 only, supersedes the 2023 exception |
| `acme_pricing_exception_2023.md` | Drive | the old 10% exception, with a **stale "Status: Active"** line |
| `sales_discount_sop.md` | Drive | the process (doc 03 §11), no thresholds |
| `acme_account_strategy.md` | Drive | **hearsay**: "I believe it's 15%" |
| `email_sarah_to_michael.md` | Email | "Mike", 15%, "what we did last September". No statement of authority |
| `service_ticket_acme_industrial.md` | Service | **"Acme Industrial"**, a different customer (Experiment F) |

**No single artifact contains any scenario's answer.** The authority matrix
never names a person, the org chart never states a percentage, and the contract
grants eligibility but never authority. Tests enforce all of this.

### Deliberate traps

| Trap | Where | Catches a system that… |
|---|---|---|
| Identity drift | CRM vs ERP vs contract names/ids | can't resolve CRM-2048 ≡ C-1001 ≡ ACME-MFG-2025 |
| Similar name | Acme Industrial Supply Co. (CRM-2091 / C-1044) | merges on name alone |
| Temporal precedent | DR-8104: Sarah approved 15% herself in Sept 2025 | reuses a 2025 fact under the 2026 policy |
| Stale status | 2023 exception says "Status: Active" | trusts a status line over validity dates |
| Superseded fact | 10% (2023–25) vs 15% (2025–28) | overwrites history, or picks the wrong one for the date |
| Hearsay | account plan and email assert 15% | treats "I believe" as the contractual basis (S05, S07) |
| Wrong department | Priya Shah, Finance Manager | routes discount approval to Finance |
| Product scope | 15% exception is NS-500 only | transfers it to NS-Cloud (S03) |

## Scenarios

| ID | Question (abridged) | Corpus | Expected |
|---|---|---|---|
| S01 | Can Sarah approve Acme's 15% on NS-500, 2026-09-23? | base | `APPROVE_WITH_AUTHORIZATION` by Michael Torres |
| S02 | …at 18%? | base | `REJECT_OR_ESCALATE` (exceeds the exception) |
| S03 | …15% on NS-Cloud? | base | `REVIEW_REQUIRED` (exception is NS-500 only) |
| S04 | …15% on 2025-09-23? | base | `APPROVE` (2025 policy: AE ≤15%) |
| S05 | …with no contract documents? | missing-contract-evidence | `REQUEST_EVIDENCE` |
| S06 | Acme's NS-500 cap on a given date? | base | 2026 → 15%, 2024 → 10%, 2022 → none. Both facts kept |
| S07 | Why is Acme eligible for 15%? | base | EXC-ACME-NS500-15 under MSA-ACME-2025, not hearsay |
| S08 | Do CRM-2048 / C-1001 / ACME-MFG-2025 match, and is Acme Industrial the same customer? | base | yes / no |

**Submitted-record conflicts (S22–S25, 2026-10-02, Jev probe J3).** DR-9001 as *submitted*, with
one field that contradicts the CRM (`Scenario.submitted`): 8% instead of 15% (S22), dated 2025-09-23
instead of 2026-09-23 (S23), and status "Approved" instead of pending (S24). S25 matches the CRM and
is the control. The oracle decides on the system of record, `APPROVE_WITH_AUTHORIZATION` by Michael
Torres for all four, and reports `input_conflicts`. No evidence is added.

**Request ids (2026-10-02).** S02–S04 vary DR-9001 into their own requests: DR-9002 (18%), DR-9003
(NS-Cloud) and DR-9004 (dated 2025-09-23). Before this they reused DR-9001 itself. The CRM record a
reader was given then contradicted the corpus's own `discount_requests.csv`. Runs before
2026-10-02 used the old ids; see `runs/2026-09-30-owm-measurements/06-two-scores/notes.md`.

**Held-out decisions (S09–S14).** Added on 2026-09-29, after the OWM decision procedure
(`owm/procedures/discount-approval.md`) was frozen, to test whether it generalizes. They vary
DR-9001 into new requests (DR-9101…DR-9106) and add no evidence, so the corpus is unchanged.

| # | Question | Corpus | Expected |
|---|---|---|---|
| S09 | Could Sarah approve Acme's 15% on NS-500 on 2025-03-31? | base | `REJECT_OR_ESCALATE` (the 10% exception was still in force) |
| S10 | Can Sarah approve 25% on NS-Edge (standard pricing), 2026-09-23? | base | `APPROVE_WITH_AUTHORIZATION` by David Morgan (CRO band) |
| S11 | Could Sarah approve 22% on NS-Edge (standard pricing), 2025-09-23? | base | `APPROVE_WITH_AUTHORIZATION` by Michael Torres (no CRO band in 2025) |
| S12 | Can Michael approve 18% for BlueRiver on NS-Cloud (standard), 2026-09-23? | base | `APPROVE` (within VP Sales authority) |
| S13 | Can Sarah's 15% NS-500 contract-pricing request for Acme Industrial Supply be approved? | base | `REQUEST_EVIDENCE` (the Acme agreement is another customer's) |
| S14 | Can Sarah approve 8% on NS-Edge (standard), 2026-09-23? | base | `APPROVE` (within AE authority) |

**Fresh held-out decisions (S15–S20).** Added on 2026-09-30 together with procedure v2
(`owm/procedures/discount-approval-v2.md`, which adds a customer-applicability rule) and committed
before any reader run. Held-out, not blind: they were written after v2. No evidence is added.

| # | Question | Corpus | Expected |
|---|---|---|---|
| S15 | Can Michael approve 12% NS-500 for BlueRiver, citing the Acme agreement? | base | `REQUEST_EVIDENCE` (no BlueRiver contract) |
| S16 | Can Sarah approve 8% NS-Edge for Acme Industrial Supply (standard)? | base | `APPROVE` (standard pricing needs no contract) |
| S17 | Can Sarah approve 12% NS-Edge for Acme Manufacturing (contract pricing)? | base | `REVIEW_REQUIRED` (agreement active, no NS-Edge exception) |
| S18 | Could Sarah approve 8% NS-500 on 2025-03-31? | base | `APPROVE` (within the 10% exception) |
| S19 | Can Sarah approve 6% NS-Cloud (standard) where the contract documents are missing? | missing-contract-evidence | `APPROVE` |
| S20 | Can Michael approve 18% NS-500 for Acme Manufacturing? | base | `REJECT_OR_ESCALATE` (above the 15% exception) |

**Decision memory (S21).** A lab extension added on 2026-09-30: `pricing_policy_2027` (AE ≤5%,
VP Sales ≤12%, CRO above), published in advance as a new evidence document. S21 is the DR-9001
request again on 2027-02-01: `APPROVE_WITH_AUTHORIZATION` by the **CRO**, where in 2026 it was
Michael Torres's to approve. It anchors the decision-memory measurement in
`runs/2026-09-30-owm-measurements/04-decision-memory/`.

S01 reproduces the canonical decision object from doc 03 §21 field for field
(see `dataset/answer-key/expected-results.yaml`).

## How the build keeps itself honest

`oracle.py` runs the canonical discount process against the truth, but it may
only use evidence keys that the *generated corpus* authoritatively supports.
Each artifact is tagged with three lists:

- `supports`: truth keys it is authoritative for;
- `asserts`: fact ids it states outright;
- `mentions`: hearsay or precedent.

If a scenario's hand-authored expectation disagrees with what follows from the
truth plus the evidence actually present, **the build refuses to write the
dataset**. Scenario 5's `REQUEST_EVIDENCE` is therefore produced by removing
documents, not by assertion. Point S05 at the base corpus and the build fails
(tested).

The oracle is the laboratory's check on its own coherence. It is **not** the
OWM, and nothing it outputs is evidence that any OWM behaves this way.

## Running the experiment (doc 02 §§6–9)

1. Create a Utopia knowledge base "Northstar Industrial Systems" and load
   `dataset/evidence/` (CSVs as structured, Markdown as documents).
2. Load `evidence-variants/missing-contract-evidence/` as a **separate** KB for S05.
3. Ask each question in `evaluation/scenario-scorecard.csv`. Record Utopia's
   answer, then the OWM's.
4. Fill in `evaluation/fact-checklist.csv`. Every row where the foundation
   knows X and Y but not the implication Z is a **candidate OWM capability**
   (`owm_needed = YES` marks the ones we expect).
5. Start removing pieces. Add a variant to `truth/corpora.yaml` (e.g. drop
   `organization_chart` for Experiment A), add or retarget a scenario, and run
   `northstar build`.

## Extending

- **Change the organization:** edit `truth/`, then run `northstar build`. The
  loader rejects dangling references, and the oracle rejects expectations that
  no longer follow.
- **Scale up:** use `--scale large` (doc 04's 200 customers / 40 employees /
  80 products / 500 orders), or add a scale to `SCALES` in
  `factories/background.py`.
- **Background noise is policy-consistent:** every generated approval obeys
  the policy in force on its date, so noise never contradicts the truth.

## Provenance of the truth

`truth/` implements *03 — OWM Domain Model + Ground Truth*. Items marked
`lab_extension: true` are not in doc 03. They were added to close the corpus
(EMP-402 is named as Priya's manager but never defined) or to run doc 02's
experiments (the similar-name customer, the 2023 predecessor agreement, the
DR-8104 precedent). They are **candidates for review**, not canon.

## Relationship to the Sovera OWM

This lab started in `kloudtaxi/sovera-owm` (`labs/northstar-owm-lab`) and lives
here as a standalone project, so that Polyfactory and Faker never enter the OWM
dependency closure. The OWM contract must not depend on this lab, or on Utopia.
