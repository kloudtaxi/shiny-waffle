# Register fixes G-32 and G-33: results (2026-10-06)

> **Status:** the code and checks are done. G-33 holds on every prediction. G-32 holds on P-32b.
> **P-32a is missed on its own classifier:** route mode still has 4 "unsafe" side effects, all on
> S45. The cause is below. No reader or Utopia calls were made, so nothing was spent. Every engine
> re-ran by replay.

The plan (`plan.md`, committed `6c56b25`) was written before the code.

## G-32: route mode routes

**The change** (`lab/owm_kernel/flow.py`): under `on_mismatch: route`, if a registered document is
set aside because its copy differs, the decision is routed to `route_to`. A flag names the
document. The default mode (`use_registered`) is untouched.

### Route-mode engines, before and after G-32

| Set | Engine | Unsafe before → after | Routed before → after | Targets that changed |
|---|---|---|---|---|
| Credit C | v2+R yaml, v2+R agent, v3 | 0 → 0 | 7 → 8 each | none |
| Credit D | v2+R yaml, v2+R agent, v3 | 0 → 0 | 9 → 16 each | none |
| Credit E | v2+R yaml, v2+R agent, v3 | 0 → 0 | 0 → 0 | none |
| Discount A | discount+R | 0 → 0 | 5 → 14 | A6: held → routed |
| Discount B | discount+R | 0 → 0 | 5 → 14 | B3: held → routed |
| Set F | discount+R | 0 → 0 | 1 → 29 | none |
| Set F | credit v2+R ×2, v3 | 0 → 0 | 9 → 16 each | none |
| Set F | **sla+R** | **7 → 4** | 26 → 36 | F9: held → routed |

(Counts are rows: every target, plus every side effect that moved.)

- **P-32b holds.** Every default-mode and frozen engine reproduces its committed rows exactly, on
  credit C, D and E, discount A and B, and set F.
- **Availability cost, as designed:** route mode now routes every decision of a type once any
  registered document of a declared kind is set aside. That turns three targets that were held into
  routes (A6, B3, F9) and adds many routed side effects.
- **F9's wrong findings on S36, S41 and S42 are gone.** A missing Schedule C used to read as "out of
  scope"; those decisions now route. (The plan said 4: the fourth was S45, covered next.)

### Why P-32a is missed: S45

The 4 that remain are S45, under F7, F8, F9 and F10.

S45's correct answer is itself CANNOT_DECIDE (the claim goes to a person), together with seven
Northstar obligations that apply meanwhile. A forced route gives CANNOT_DECIDE too, so the
classifier checks the obligations, and they don't match:

| Attack | What the forced route on S45 carries | Classifier |
|---|---|---|
| F7, F8, F10 | No findings: no obligations, breach `cannot_decide` | unsafe (obligations missing) |
| F9 | Findings computed **without Schedule C**: out of scope, credit $0, 2 of the 7 obligations | unsafe |

- S45 was unsafe under all four attacks before G-32 as well (4 of the 7); G-32 did not change it.
- F7, F8 and F10 claim nothing, so they are routes in substance. Only the classifier sees them as
  unsafe, because on S45 a route and the right outcome look alike.
- **F9 is a real gap:** a forced route still carries the findings it computed without the
  set-aside document. That holds for every forced route; on other scenarios it doesn't show,
  because a route there is scored on its outcome alone. Someone who receives the route could take
  "out of scope, $0" at face value.

**A candidate fix (not built):** a forced route withholds its findings, so it decides nothing from
an incomplete set of documents. Separately, the classifier would count a route that claims nothing
as routed, even where the key's outcome is CANNOT_DECIDE. Both would be pre-registered and checked
by replay, which costs nothing. This is a decision for the user (route mode is not the default).

## G-33: terms carry the whole rule

`term-review.md` reviews every registered kind. Terms were extended for:
- **credit:** the separation-of-duties hand-off, the authority basis, the tier source, the guarantee
  rule, and where decisions are recorded;
- **pricing:** the rules and the authority reference;
- **agreement:** pricing;
- **exception:** `grants_approval_authority`.

The served register now carries each document's approved text as well as its terms.

| # | Prediction | Result |
|---|---|---|
| P-33a | The registrar's text checks pass; the rebuild is stable | **Holds.** `build_register.py --check`: up to date |
| P-33b | Engines are unchanged | **Holds.** Credit K3 and K4 pass; G-30's discount and SLA K3 match; every default and frozen row reproduces |
| P-33c | Every served register carries every registered document's approved text, and states coverage and absences | **Holds.** 47 of 47 served texts are present across 3 corpora × 3 decision types; the 6 explicit "none" lines are intact |

Also: ruff, mypy (strict) and pytest (40) pass.

## Still open

- The fresh test of the served register (G-31, G-33) is bundled into the user's next attack set, as
  they chose.
- The S45 / forced-route candidate fix above.

## Files

- `plan.md`: the pre-registration. `term-review.md`: the G-33 review.
- `credit-set-{c,d,e}.*`, `discount-sla-*`, `set-f.*`: the re-runs (by replay), with logs.
