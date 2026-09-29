# Held-out decisions S09–S14 (2026-09-29)

## Pre-registration (written and committed before any reader saw these scenarios)

**Question.** The OWM layer (procedure + request record) took S01–S05 to 15/15. But the
procedure was written knowing those five scenarios, and they all concern one request (DR-9001).
Does it decide correctly on decisions it was never developed against?

**Frozen inputs.**

- **Procedure:** `owm/procedures/discount-approval.md`, sha256 `6e72951c…a9da94`, unchanged
  since `a9189a9`. It will not be edited during this arm.
- **Reader:** `lab/utopia/blind_reader.py`, with the fixed system prompt and blind controls.
- **Scoring:** the fixed rule in `../../2026-09-28-utopia-aad5b06/procedure/score.py`, applied
  by `heldout.py score`:
  - *pass* — outcome, eligibility and requestor-authorized all match, and the approver matches
    whenever the expected outcome is an approval
  - *partial* — the outcome matches but another field doesn't
  - *fail* — anything else

**The scenarios.** They are in `truth/scenarios/09-…14-*.yaml`, proven by the oracle
(`northstar check`: 14 scenarios coherent). Each varies DR-9001 into a new pending request, so
the evidence corpus is byte-identical at both scales, verified by diffing a fresh build against
`../dataset/`. No Utopia KB changes and no ingestion.

| | Request | What it tests that S01–S05 didn't | Expected (oracle) |
|---|---|---|---|
| S09 | 15% NS-500, Acme, **2025-03-31**, contract pricing | An exception-validity boundary: the 10% exception's last day, a day before the 15% one starts | `REJECT_OR_ESCALATE`: eligibility exceeded (EXC-…-10); Sarah authorized; AE band, approver Sarah |
| S10 | 25% NS-Edge, Acme, 2026, **standard pricing** | The CRO band, which no original scenario reached | `APPROVE_WITH_AUTHORIZATION`: CRO, David Morgan |
| S11 | 22% NS-Edge, Acme, **2025**, standard | Policy-version bands: 2025 has no CRO band | `APPROVE_WITH_AUTHORIZATION`: VP Sales, Michael Torres |
| S12 | 18% NS-Cloud, **BlueRiver**, requested by **Michael**, standard | A different customer and a non-AE requestor | `APPROVE`: within VP authority, approver Michael |
| S13 | 15% NS-500, **Acme Industrial Supply**, contract pricing citing the Acme agreement | Identity: the agreement belongs to another customer | `REQUEST_EVIDENCE`: eligibility unknown; VP Sales, Michael |
| S14 | 8% NS-Edge, Acme, 2026, standard | Within authority: no escalation | `APPROVE`: approver Sarah |

`questions.tsv` holds the reader's input: the scenario's verbatim question, then the request as
the CRM would record it. `heldout.py questions` builds the record from the truth with the
oracle's `resolve_request` and the CRM generator's conventions.

**Conditions** (scale base KB, n = 3 each):

1. **Primary: B1n + procedure + request record, uncurated.** All tools but `changes`, with the
   scale curation withdrawn (`../b1/toggle_curation.py`), then restored. This is the
   configuration that reached 45/45 on S01–S05.
2. **Secondary: B2 + procedure + request record, curated (B2kPR).** Graph tools only, on the
   curated graph. Curation covers all bands (including the CRO band), both exceptions' values
   and dates, reporting lines and the agreement's term, but was chosen for S01–S05.

**What would count as generalizing.** The primary condition matches the key on the large
majority of the 18 decisions, and no miss is an unsafe approval: approving when the key
says don't, or naming the wrong approver for an approval. Predicted hardest: S13 (identity)
and S09 (a one-day validity boundary).

## Results

*(appended after the runs)*
