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

## Results (appended after the runs)

Both conditions ran exactly as registered. The graph-only runs came first, on the curated
graph. Then the curation was withdrawn (live facts back to exactly 13,721 and 14,122) for the
B1n runs, and restored afterwards (exactly 13,774 and 14,170; 86 reporting lines; the
agreement's term). In the B1n runs no tool result mentions a curation document. The two `as_of`
calls (S12, `search_chunks`) are dated 2026-09-28 and 2026-09-29T00:00, before any curation
existed. Every run saw its expected tools with 0 denials, and every token was revoked.

| Scenario | Expected | B1n + procedure + record, uncurated (×3) | B2 + procedure + record, curated (×3) |
|---|---|---|---|
| S09 boundary | REJECT_OR_ESCALATE | ✓✓✓ | ✓✓✓ |
| S10 CRO band | APPROVE_WITH_AUTHORIZATION (David Morgan) | ✓✓✓ | ✓✓✓ |
| S11 2025 bands | APPROVE_WITH_AUTHORIZATION (Michael Torres) | ✓✓✓ | ✓✓✓ |
| S12 VP requestor | APPROVE (Michael) | ✓✓✓ | ✓✓✓ |
| S13 similar customer | REQUEST_EVIDENCE | ✗✗✗ REVIEW_REQUIRED | ✗✗✗ REVIEW_REQUIRED |
| S14 within authority | APPROVE (Sarah) | ✓✓✓ | ✓✓✓ |
| **Total** | | **15 / 18** | **15 / 18** |
| Claude cost / turns per answer | | $4.74 / 9–18 | $6.30 / 15–39 |

Scores: `scores-b1n-uncurated.json`, `scores-b2-curated.json`. Every B1n pass matches on
every field. In the graph-only condition, two S09 passes (r2, r3) left the required role and
approver empty (`null`). For a rejection the rule doesn't score them, and no approver acts;
r1 filled them in correctly (AE band, Sarah Chen).

### S13: a gap in the procedure, not a reader error

All six S13 runs resolve the identity correctly. The cited Acme Master Supply Agreement and
the 15% exception belong to Acme Mfg. Holdings (Milwaukee, C-1001). Acme Industrial Supply
(Akron, C-1044, account owner Zachary Brown) is a separate legal entity, and nothing gives it a
contract or exception. None applies Acme's 15%, and all name the right approver. They then
choose **REVIEW_REQUIRED** ("special terms do not transfer") and list the missing contract as
missing evidence. The oracle's canonical process says **REQUEST_EVIDENCE**: no evidence
establishes a contract for *this* customer.

The procedure's outcome table scopes REVIEW_REQUIRED to "none covers this product or date",
and REQUEST_EVIDENCE to "a contract term … that no available evidence establishes". It says
nothing about terms that belong to another customer. Six of six readers read that gap the
same way. By the registered rule these stay **fails**. The fix belongs in a new procedure
version, tested on fresh held-out scenarios; re-running S13 with a patched procedure would be
tuning to the test.

### Against the registration

- **Generalizing:** 15 of 18 in the primary condition, and no unsafe miss. Nothing was
  approved that the key says not to approve, and no approval named the wrong approver. The
  registered bar is met.
- **The predicted hard cases:** S09 (a one-day validity boundary) passed 6 of 6, including the
  trap that the request cites an agreement that starts the next day. S13 failed 6 of 6, as
  predicted, but for a reason in the procedure, not in identity resolution.
- **Graph-only generalizes too, given its curation.** The curated graph carried the 2025 and
  2026 bands (including the CRO band) and both exceptions' dates, which is what S09–S12 needed.
  It cost more ($6.30 against $4.74) and took about twice the turns.
