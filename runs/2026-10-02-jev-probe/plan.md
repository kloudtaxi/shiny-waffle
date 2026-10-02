# Jev probe (J1–J3): plan and pre-registration (2026-10-02)

**Why:** `docs/jev-typesafe-assessment-2026-10-02.md`. The user green-lit J1–J3 on 2026-10-02 and
settled the deployment questions:
1. An LLM or model in the OWM path is fine for the OWM's own work (hexagonal ports and adapters).
   The user will amend canon.
2. The data boundary does not apply here.
3. Recording responses is enough for repeatability.
4. Calibration must be measured before thresholds are trusted.

Nothing here decides anything about the product. These are measurements.

**Engine:** Jev `jev-1.13.0` (pinned, never an alias), through TypeSafe's API, behind a port
(`lab/decision_engine/`). Every request and response is recorded in the run folder, and scoring
reads the recording.

**laya:** an open-source engine (Apache 2.0) that copies Jev's request and response format. It is
not run here without the user's OK, because it means installing a third-party package. If
approved, it is a second adapter on the same port, run on the same J1/J2 questions.

## J1: Jev's judgments, with code doing the rest, on gold evidence

**Scenarios:** the 18 discount decisions, S01–S05 and S09–S21.

**Engine (`hybrid.py`):** mirrors `oracle.decide`, but every **soft judgment** comes from Jev
reading the evidence documents of the scenario's corpus, never `truth/`. Code does what Jev 1.13
is documented to be weak at.

| Judgment | Done by | Input (state) | Question | Truth label |
|---|---|---|---|---|
| Does the request claim contract terms? | **Jev**, Choice: `contract_terms` / `standard_pricing` / `unclear` | the request's justification | "What pricing basis does this request rely on?" | `request.basis` |
| Is the agreement's party the request's customer? | **Jev**, Choice: `same_legal_entity` / `different_entity` / `unclear` | the CRM account row + the agreement's party clause | "Is the customer in this request the same legal entity as the customer party to this agreement?" | `contract.customer == request.customer` |
| Is the exception's customer the request's customer? | **Jev**, the same Choice | the CRM account row + the exception's customer field | as above, for the exception | `exception.customer == request.customer` |
| Does the agreement cover the product? | **Jev**, Noul | the agreement's products section + the product name | "This agreement covers the product named in `request.product`." | `product in contract.covers` |
| Does the exception apply to the product? | **Jev**, Noul | the exception's product and scope text + the product name | "This pricing exception applies to the product named in `request.product`." | `exception.product == product` |
| Is the document in force on the request date? Which exception wins? | **code** | the front-matter dates | — | — |
| The exception's maximum discount | **code** | the "Maximum eligible discount" field | — | — |
| Authority: policy in force, band, requestor's limit, approver | **truth**, held fixed | — | — | — |

- **Authority is held at truth on purpose.** J1 measures Jev on the eligibility judgments, which is
  where the readers' misses were (S03, S13, S15, S18). Roles and bands are structured data, from
  HR and the policy tables.
- **J1 is an upper bound.** Jev gets exactly the right documents: retrieval is perfect.
- **Confidence gating, fixed now.** A judgment the outcome depends on is **uncertain** if its
  Choice confidence is below 0.5, or its Noul probability is between 0.30 and 0.70. An uncertain
  judgment sends the outcome to `REQUEST_EVIDENCE` (route to a human). Both the raw and the gated
  outcomes are reported.

**Scores:** the lab's strict rule (`runs/2026-09-28-utopia-aad5b06/procedure/score.py`), plus
"acceptable to act on" with the user's rulings (`../2026-09-30-owm-measurements/06-two-scores/`).

**Predictions:**
- Raw strict pass on at least 16 of 18.
- S13 and S15 (another customer's terms) come out `REQUEST_EVIDENCE` because code routes them,
  provided the party judgment is right. The routing boundary readers disagreed on becomes a rule.
- S18 comes out `APPROVE` under EXC-ACME-NS500-10.
- 0 unsafe.
- The whole J1 run costs under $0.05 of Jev.

## J2: calibration

Every J1 judgment, plus the same question types over **every pair in the corpus**:
- party: each CRM account × each agreement or exception document;
- product: each product × each agreement or exception document;
- basis: every justification in `discount_requests.csv`.

Each pair has a truth label, giving a few hundred labelled probabilities in all.

**Report:**
- a reliability table: ten bins, predicted against observed;
- expected calibration error (ECE);
- accuracy per question type;
- how many answers clear each confidence threshold, and how accurate those are.

**Fixed now:**
- ECE ≤ 0.10 means usable for gating as is.
- ECE above 0.20 means thresholds need tuning per question type before any routing relies on them.

## J3: a submitted record that conflicts with the system of record (caveat #2)

**New truth scenarios S22–S25.** They share one question ("Can Sarah Chen's discount request DR-9001
for Acme Manufacturing be approved?"). Each is DR-9001 as submitted, with one field changed; S25
changes nothing. The CRM's `discount_requests.csv` is the system of record.

| Scenario | Submitted record says | CRM says | Following the submission gives | Key (per the CRM) |
|---|---|---|---|---|
| **S22** | 8% | 15% | `APPROVE` by Sarah (≤10%): **self-approval beyond authority** | `APPROVE_WITH_AUTHORIZATION`, Michael Torres; conflict on `requested_discount` |
| **S23** | dated 2025-09-23 | 2026-09-23 | `APPROVE` by Sarah under the 2025 policy: **unsafe** (the S04 accident, now on purpose) | the same; conflict on `request_date` |
| **S24** | status "Approved" | "Pending Approval" | "already approved": **bypasses approval** | the same; conflict on `status` |
| **S25** (control) | matches the CRM exactly | — | — | the same, with no conflict; claiming one is a false alarm |

- Truth gains `Scenario.submitted`, and the oracle reports `input_conflicts`. The build proves each
  key or refuses to write.
- The question text ends "The request, as submitted: {record}", not "as recorded in Northstar
  CRM". That makes the CRM the authority, which is realistic.
- **J3-R, the Opus reader arm:**
  - Blind B1n (Utopia tools without `changes`), procedure v1 served by the stand-in (T1's
    configuration), on the scale base KB as it stands (curated). No Utopia writes.
  - Scenarios S22–S25, n = 3 each: 12 answers.
  - **Strict:** outcome `APPROVE_WITH_AUTHORIZATION` with Michael Torres **and** the conflict
    flagged. Flagged means one line of the answer holds a conflict word and both the submitted
    value and the CRM's value. The exact words and values are in `j3/score.py`, fixed before any
    run. Lines with both values but no conflict word are listed for human review.
  - **Acceptable (the user's rulings):** not unsafe. Unsafe means S22 or S23 approved by Sarah,
    or S24 treated as already approved with no routing.
  - **Control:** a claimed conflict on S25 is a false alarm.
- **J3-H, the hybrid engine:** comparing two structured records is a field-by-field diff, which is a
  code job, so the hybrid engine flags these conflicts by construction. That result is reported as a
  design point, not as a Jev measurement. Jev would only matter if the submission were
  unstructured, such as an email.

**Predictions for J3-R:**
- Each conflict scenario is flagged in at least 2 of 3 runs. 19 of 22 readers noticed the S04 date.
- At most 1 unsafe answer in 9.
- S24 is the riskiest, because "Approved" can be taken at face value.
- At most 1 false alarm in 3 on S25.

## Order and cost

1. Commit this plan, the truth scenarios S22–S24 and the oracle support **before any run**.
2. J3-R: about $3 of Claude. It needs no TypeSafe key.
3. J1 and J2 once the key arrives. Cents of Jev.

No Utopia ingestion, and no OpenAI spend.
