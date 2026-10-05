# One register for all three decision types (G-30), 2026-10-05

**STATUS: DONE.** Pre-registered in `plan.md` (`45a4c71`); build `3625d99`.
- Every pre-registered check passed: `results.md`, from `run_all.py`.
- The fresh attack test for discount and SLA is the user's next set (G-31).

## What was built

**One register per company**, as the user decided (it lives in the OWM; the owning function
registers each document; a second person approves; documents carry structured terms; proceeding
is the default). It now covers **all 17 governing documents** of the three decision types:

| Area | Documents |
|---|---|
| Credit | 2 credit policies; the guarantee |
| Discount | 3 pricing policies; the Acme agreement; 2 pricing exceptions |
| SLA | 2 service-level schedules; 3 support-terms documents; the holiday calendar; the severity guide; the escalation procedure |

The missing-contract company registers 14 (no agreement, no exceptions); the missing-guarantee
company registers 16.

**Global kinds:**
- the register names kinds globally (`credit_policy`, `pricing_policy`, `agreement`,
  `exception`, `sla_schedule`, `support_terms`, `holiday_calendar`, `severity_guide`,
  `escalation_procedure`);
- a spec maps its own kind names onto them, in one `registered_kinds` declaration;
- credit was re-pointed to `credit_policy`.

**Explicit relations (G-02):**
- policies and SLA schedules supersede their predecessors;
- EXC-ACME-NS500-15 supersedes EXC-ACME-NS500-10 and is `under` ACME-MFG-2025;
- Schedule C (SUP-ACME-C) is `under` ACME-MFG-2025.

**Structured terms**, from truth, each checked against its document's text by the registrar:
- **pricing policies:** bands and the evidence threshold;
- **the agreement and exceptions:** customer by registered id, products by SKU, maximum discount;
- **SLA schedules:** targets, credits, cap, claim period, notice;
- **support terms:** customer ids, plan, products, coverage start;
- **holidays.**

The severity guide and escalation procedure are registered as **approved text only, with no
structured terms yet.**

**Registered by:**
- **Finance:** Priya Shah, approved by Elena Novak;
- **Customer Support:** Hannah Lindqvist, approved by Marcus Adeyemi;
- **Revenue Operations, Deal Desk, Legal and People Operations:** by function; the HR export has
  none of their staff.

**The approved texts** are all in the content-addressed store. Under the default, every registered
document is read as its approved version, so the existing prose specs need **one declaration and
no other change.**

## Results

**Clean decisions (K3)** are identical to the frozen specs on every decision field, for every
register-backed engine:
- discount 18/18 (experiment 4's scenarios, both corpora);
- SLA 10/10 (S36–S45);
- credit 10/10 (rechecked on the shared register).

**Credit on the shared register (K4):** sets C, D and E, all 555 committed rows (every engine),
**reproduce exactly**.

**Re-saved documents (K5).** Every document was re-saved with CRLF line endings and trailing
spaces, with the same words:

| Engine | Decisions changed |
|---|---|
| discount, discount+R | **18/18** |
| **discount+Ru** | **0/18** |
| sla, sla+R | **10/10**, and the frozen SLA spec *crashed*: with CRLF line endings its severity-guide reader found no severity levels, and the judgment service rejected a question with no choices |
| **sla+Ru** | **0/10** |
| credit v1, v2, v2+R (earlier) | 6/10 |
| **credit v3, v3u, v2+Ru** | **0/10** |

**Experiment 4's attack sets A and B on discount:**

| Engine | Targets unsafe | Targets routed | Unsafe side effects | Side-effect routes |
|---|---|---|---|---|
| discount (frozen v3) | 0 / 16 | 3 (A6, B3, B5) | 0 | 17 |
| discount+R (route) | 0 / 16 | 0 | 0 | 10 (all from A6 and B3, the in-place edits of the real exception) |
| **discount+Ru (default)** | **0 / 16** | **0** | **0** | **0** |

Predictions A-a (0 unsafe) and A-b (no more routing than the frozen spec) both held.

## What it shows

1. **The register generalizes by declaration.** Three decision types, two of them reading prose,
   joined the register with one line each and no code. Clean decisions were unchanged, and every
   attack set held with nothing routed.
2. **Proceeding on the approved version removes the cost of safety.** Experiment 4's guards kept
   discount safe on sets A and B, but sent 20 decisions to a person. With the register (default
   mode), none.
3. **Format fragility is everywhere prose is read,** and the register's store removes it. A CRLF
   re-save changed every discount and SLA decision of the frozen specs, and crashed one, but none
   with the register declared.

## Left open

- **The fresh test for discount and SLA:** no attack set was written against them with the register
  in place. The user's next set (G-31) covers all three decision types.
- **The severity guide and escalation procedure** have no structured terms yet.
- **Discount and SLA still read prose,** so a terms-from-register version (like credit v3) would
  remove the remaining wording fragility and the identity judgments. This is not needed for
  safety now that approved texts are read.

## Files

| File | What it holds |
|---|---|
| `plan.md` | The pre-registration |
| `run_all.py` | K3, K5 and sets A and B |
| `results.md` | All results |
| `set-{a,b}-results.json` | The attack rows |
| `engine-calls.jsonl` | The Jev recording, seeded from experiment 6's; 6 new calls (cents) |
| `lab/owm_register/` | The registrar, the three registers, the store |
