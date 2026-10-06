# Register fixes G-32 and G-33: pre-registration, 2026-10-06

The user decided on 2026-10-06:
- **G-32:** fix route mode;
- **G-33:** review every term schema now;
- **the fresh test:** later, bundled into the next attack set.

This file is committed before the code.

## G-32: route mode must route, not set aside

**Today:** under `on_mismatch: route`, a registered document whose copy differs is set aside, and
the decision continues without it. Set F showed what follows: SLA read a missing Schedule C as "out
of scope", giving 4 wrong findings, and dropped S45's obligations.

**The fix:** in route mode, if any registered document of a kind the spec declares is set aside, the
decision is **explicitly routed** to `route_to`, with a flag naming the document. This is coarse on
purpose, because prose specs don't say which document each decision reads. Route mode trades
availability for caution; the default mode (`use_registered`) is unchanged.

**Predictions** (route-mode engines re-run on sets C, D, E and F: v2+R ×2, v3, discount+R,
sla+R):
- **P-32a:** 0 unsafe, on targets and side effects; sla+R's 7 unsafe side effects become routed;
- **P-32b:** default-mode and frozen engines reproduce their committed rows exactly.

## G-33: structured terms must carry the whole rule

**The review** (`term-review.md`) covers every registered kind. For each rule in the approved
document it records whether it is captured in the terms, lives only in engine code, or lives only
in prose. Then:
1. **Terms are extended** where a decision-relevant rule is simple:
   - credit: the guarantee rule and the tier source;
   - pricing: the policy's rules;
   - exceptions: `grants_approval_authority`;
   - each new term is checked against the text by the registrar.
2. **The served register also carries each registered document's approved text** (served form
   v3), not just terms. Terms alone can't hold SLA clock rules, exclusions or procedures. With the
   approved text served, nothing in the approved document is lost to an agent, however complete
   the schema is.

**Predictions:**
- **P-33a:** the registrar's checks pass, and the rebuild is stable;
- **P-33b:** engines are unchanged (credit K3 and K4; G-30's discount and SLA K3);
- **P-33c:** every served register contains every registered document's approved text, and states
  coverage and absences as before.

**No reader calls now.** The fresh test of the served register is bundled into the next attack set,
as the user chose.
