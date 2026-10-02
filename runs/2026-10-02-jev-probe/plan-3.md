# Jev probe, part 3: experiments 1 and 2 from `docs/next-experiments-2026-10-02.md`

Pre-registration, 2026-10-02. The user agreed to run 1 and 2 first. Committed before any run.
The engine is `jev-1.13.0`, recorded through `lab/decision_engine`.

## Experiment 1 (A1): authority from evidence

J1 and E2E held authority at truth: the policy in force, the bands, the requestor's limit, the
required role and the approver. A1 takes all of it from the company's own records.

**How the hybrid engine reads authority** (`authority="evidence"` in `j1/hybrid.py`):

| Step | Done by | Source |
|---|---|---|
| The policy in force on the as-of date | **code** | each pricing policy's front-matter window (`effective_from` / `effective_to`) |
| The bands: role, lower bound, upper bound | **code** | the policy's section 3 sentences ("… may approve discounts up to and including N%", "Discounts greater than N% [and up to and including M%] require ROLE approval") |
| Which HR job title a band's role means ("Enterprise Account Executives" → "Enterprise Account Executive") | **Jev**, Choice over the distinct titles in `employees.csv` | the band's role words |
| The requestor's title, and their manager chain | **code** | `employees.csv` (HR system of record), looked up by the request's `requested_by` email |
| The requestor's limit, whether they are authorized, the required role, the approver (first holder of the required title up the manager chain, else any holder) | **code** | from the above |

- **No policy found** (none in the set covers the date) means authority is unknown, and the outcome
  is `REQUEST_EVIDENCE`.
- **Gating:** an uncertain role mapping (Choice confidence < 0.5) sends the outcome to
  `REQUEST_EVIDENCE`, as in J1.

**Runs:**
- **A1-J1:** the 18 J1 scenarios on gold evidence. Authority documents come from the scenario's
  corpus.
- **A1-E2E:** the 102 T1/T2 transcripts. **Policy documents are limited to the agent's retrieved
  set** ("seen" and "read", as in E2E). `employees.csv` stays a structured system-of-record input,
  like the CRM row.
- **Control:** the perfect judge (`j1/control.py`) with evidence authority. It must reach 18/18
  before any Jev call is trusted.

**Predictions:**
1. The control gets 18/18.
2. A1-J1 gets **18/18**.
3. A1-E2E on "seen" gets at least 100/102, with 0 unsafe. A run that never surfaced the governing
   policy ends in `REQUEST_EVIDENCE`, never in an unsafe approval.
4. Jev maps the three band roles to the right titles with confidence ≥ 0.9.

## Experiment 2 (I2): identity on the whole queue, with a guard and a chosen operating point

J4 measured a 1,445-pair sample. I2 runs on **every labelled pair** in two KBs and picks an
operating point by a rule fixed now.

**Populations:**
- the scale base KB: 21,661 labelled pairs, the J4 population;
- the scale missing-contract KB (`01a0ea56-65d0…`), as an untouched replication.

Both are labelled by `j4/build_pairs.py` (a resolver against the corpus, sha256-checked), with the
same input reconstruction, including the merge-time fix.

**The decision, for each merge threshold τ in {0.5, 0.6, 0.7, 0.8, 0.9}:**
- **Guard (code):** if both names carry an id prefix (`SO-`, `C-`, `CRM-`, `DR-`, `EMP-`, `PROD-`)
  and the kinds differ, keep. An order is never a customer.
- **Otherwise:** merge if Jev says `same` with confidence ≥ τ; keep if it says `different` with
  confidence ≥ 0.5; anything else is routed to a person.

**Operating-point rule, fixed now:**
- On the base KB, take the smallest τ with zero false merges. If there is none, take the τ with the
  fewest false merges, breaking ties by the fewest pairs routed.
- Apply that τ unchanged to the missing-contract KB.

**Measures per τ and KB:** false merges, missed merges, routed (human load), and accuracy when
acting. gpt-4o's own decisions on the same pairs are shown alongside.

**Predictions:**
1. On the base KB, Jev with the guard makes **at most 3 false merges at τ = 0.5**. Zero at the
   chosen τ.
2. Routed load is **at most 10% of pairs** at the chosen τ. The full queue is mostly easy keeps;
   J4's sample was enriched with hard cases.
3. On the replication, at the same τ: false merges at most 0.05% of pairs, and routed at most 10%.
4. gpt-4o's false merges on each full KB are more than 100. J4's sample implies about 160 on the
   base KB.

## Cost

- **Jev:** about 42,000 pair calls at about 490 tokens each, roughly $0.90. A1 needs a handful of
  role calls.
- **Claude:** none.
- **Utopia:** read-only.
- **OpenAI:** none.
