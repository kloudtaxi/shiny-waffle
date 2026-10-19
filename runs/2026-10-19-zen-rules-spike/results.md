# ZEN rules spike: results (G-52)

**2026-10-19. All five pre-registered checks passed, at $0.** The register's business tables can
live as ZEN decision tables behind a port, and every decision stays the same. Plan: `plan.md`
(e54e72f); notes and one amendment to the test: `notes.md`.

## The checks

| | Check | Result |
|---|---|---|
| **P1** | Admission gate on `credit_v3.yaml`, baseline against ZEN-backed (A clean, B sealed attack sets, C reliance) | **Identical reports.** Both arms: A 10/10, B 0 unsafe or error in 24 attacks, C 0 idle. Live Jev 0 in both. The ZEN arm made 400 table calls |
| **P2** | Boundary grid over all 7 tables | **1,445 points, 0 differences.** 77 points are the pre-declared exception (below) |
| **P3** | Registration checks | All 7 real tables pass the node check and the coverage check. A planted function node is **refused** (`'functionNode' isn't allowed in a registered table`). A planted gap is **flagged** (`(100000..150000] matches nothing`), and so is a planted overlap (`b2 starts at 90000, b1 ends at 100000`) |
| **P4** | The G-33 hand-off lives in the table | **Yes.** As registered, an AR Specialist's $1,000 request isn't self-authorized and passes to his manager (Elena Novak), exactly as the kernel decides. With separation of duties switched off **in the table only**, he's authorized and approves it himself; the YAML terms didn't change. A hand-off the kernel can't resolve ("the CFO") is **refused**, not guessed |
| **P5** | Trace | Every call yields the table file, the entry's version and the matched row ids. Example: `CREDIT-POLICY-2026.v1.json`, $400,000 → band row `b2`, limit row `l-other` (the requestor holds no band), no concurrence. A decision record can cite exactly that |

## The finding: the kernel's limit for an unlimited band

`limit_for` returns **1.0** for a title whose band has no upper limit. That is the discount
convention (1.0 = 100%) applied to dollar amounts. So a Director of Finance's own credit limit
reads as $1.

Separation of duties is on in every credit policy, and it makes the requestor never self-authorized.
So this changes no decision today. P1 confirms that. With separation of duties off, a Director's
request above $1 would be recorded as needing authorization, not as within their own limit.

The table states the band as unlimited. This is the "a table makes the whole rule explicit" benefit
in practice: writing the rule out exposed the quirk. It's logged on G-52; the kernel hasn't been
changed.

## Measures

| | |
|---|---|
| **Size** | JDM is verbose: 3.0–4.1 KB per table pretty-printed (2.0–2.6 KB compact), against 0.3–0.9 KB of YAML terms. It's a machine format; people read it in the editor as tables |
| **Speed** | Median **0.26 ms** per call with tracing on (Python binding), worst 0.5 ms. The first call per table also compiles it (about 5 ms). Negligible against a Jev call |
| **Rows** | 7–11 rules per table |
| **Variants** | The same terms appear in all three committed registers (21 entries checked), so one table per entry version serves every corpus |

**What still lives in code or the specs:**
- **People:** the manager-chain walk (who holds the title up the requestor's chain). Tables say
  *which role*; the OWM resolves *which person*. That's the right split.
- **Constants the spec reads directly:** the credit `caps`. Moving them into the table means
  changing the spec to ask the table, which this spike didn't do.
- **SLA targets and credits:** the SLA specs read them from the schedule's prose, not the terms. The
  SLA tables pass P2 but aren't on an engine path yet.
- **Pricing:** no engine reads the pricing terms (the discount spec reads policy prose; agents get
  the served register). Its tables pass P2 only.
- **Definitions and bindings,** such as "discounts are calculated against the current list price",
  "the tier comes from the CRM" and "the authority basis is the new total limit". These aren't table
  rules: they say where an input comes from and what it means. They belong to the semantic layer
  (G-51), not to a rules engine.

## What this settles, and what it doesn't

- **Settled:** ZEN can hold the register's business tables, evaluated through a port. It changes no
  decision, gives a row-level trace, and supports registration checks that refuse code and catch
  gaps and overlaps.
- **Not settled:**
  - whether approvers can read and edit a table (G-11). That's your step: open
    `tables/CREDIT-POLICY-2026.v1.json` in GoRules' editor. It runs as a free browser playground
    (https://docs.gorules.io/learn/getting-started/playground) or self-hosted
    (Docker image `gorules/editor`). The tables hold only Northstar's synthetic terms, already
    public in this repo;
  - whether to move the SLA and pricing engine paths onto the tables;
  - whether to adopt ZEN at all (G-52's first decision).

## Files

- `tables/*.json`: the seven JDM tables.
- `outputs/gate-base.json`, `outputs/gate-zen.json`: the two gate reports.
- `outputs/traces.jsonl`: every ZEN call in the gate's ZEN arm.
- `outputs/results.json`; `outputs/results-first-pass.json` (see `notes.md`).
- `spike.py`, `tables.py`: throwaway code.
