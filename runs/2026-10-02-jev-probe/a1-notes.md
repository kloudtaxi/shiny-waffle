# A1: authority from evidence (2026-10-02)

Pre-registered in `plan-3.md` (commit `01f16c8`). This closes J1's and E2E's last assumption: the
hybrid engine now reads authority from the company's own records, and truth is used nowhere.

**Code:** `j1/hybrid.py --authority evidence` (`authority_from_evidence`):
- the policy in force, by its front-matter window (code);
- its bands, from the section 3 sentences (code);
- which HR job title each band's role means (Jev, a Choice over the 10 titles in `employees.csv`);
- the requestor, their limit, and the approver up the manager chain (code, from `employees.csv`).

**Outputs:** `j1/decisions-a1.json`, `j1/scores-a1.json`, `e2e/results-a1.{md,jsonl}`.

## Results

| Run | Result | Prediction |
|---|---|---|
| Control: perfect judge with evidence authority | **18/18** | 18/18 ✓ |
| **A1-J1:** 18 scenarios, gold evidence | **18/18**, raw and gated | 18/18 ✓ |
| Role → title mapping | 50 judgments (3 roles per policy, 2 in 2025), **all correct at confidence 1.0** | ≥ 0.9 ✓ |
| **A1-E2E, "seen":** policy only if the agent surfaced it | **102/102**, 0 unsafe. The governing policy was in the set 102/102 times (2026 ×78, 2025 ×24). | ≥ 100/102, 0 unsafe ✓ |
| A1-E2E, "read": policy only if the agent opened it in full | **21/102**, 0 unsafe. The policy was opened in only 21 runs; every other run ends in `REQUEST_EVIDENCE` (authority unknown). | — |

- **Jev cost:** 3 new calls. Each role phrasing is asked once and answered from the recording after
  that.
- J1 (truth authority) replays unchanged at 18/18 after the change.

## What it shows

- **The whole decision runs from evidence.** The policy, the bands, the job titles, the manager
  chain, the agreement and the exception all came from the company's records. On gold evidence,
  and on what agents surfaced, it is 18/18 and 102/102. Nothing in the result depends on the answer
  key any more.
- **Agents read policies from snippets, not documents.** Readers saw the governing policy in search
  results every time, but opened it in full only 21 times in 102. Limited to opened documents, the
  engine says "need the policy" (`REQUEST_EVIDENCE`) instead of guessing, with 0 unsafe answers.
  That is the right behaviour, and it says what the agent-facing tool should be: **"fetch the
  governing documents for this request" should return whole documents**, the policy included.
  This is experiment 3's design.
- **Jev's role in authority is small and exact.** Its only job was mapping "Enterprise Account
  Executives" to the HR title "Enterprise Account Executive", and so on. Code did every number,
  date and chain walk, which is where Jev 1.13 is documented to be weak.

## Limits

- The policy parser reads this corpus's section 3 sentence pattern. A differently worded policy
  needs either the parser extended or a Jev question per band. The bounds themselves stay in code.
- `employees.csv` is the small corpus's HR file, while the E2E transcripts came from the scale KBs.
  The truth employees and titles are the same; the scale file adds background staff only.
- n = 18 scenarios on one company's titles. The role mapping was easy here: the titles nearly match
  the policy wording.
