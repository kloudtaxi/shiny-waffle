# F2: sizing a held-out second org, and how platform-ready the decision path is

2026-10-22 · repo `shiny-waffle` at 00325ce · read-only analysis by a lab subagent. Cost: $0. No model
calls, no network and no services were started. Probes ran only on copies of the code and data in the
session's scratch folder; they aren't committed. The lab spot-checked four blockers against the code
(D1 corpus root, D5 mandate, D7 parser, D10 id prefixes).

**Who reads section 7.** It's written for whoever writes the held-out org. The OWM team gets org B at
acceptance, not before: the kinds of difficulty below are general business rules, but a team that
builds against this list is tuning on the exam.

## 1. Summary

- **Writing the org** (an outsider, after the generator is fixed): the discount slice takes **4.5–7.5 days**,
  including a writer's guide and adjudication. Adding credit takes **2–3.5 more days**.
- **Removing the couplings** takes **10–17 days** if org B's documents come from the generator's
  templates, and **12–21 days** if the outsider writes them. The generator accounts for 4–7 of those
  days and the decision path for 6–14, credit included. Elapsed time to a held-out acceptance run is
  about 2.5–4.5 weeks, with the writing done in parallel.
- **Biggest blocker:** the decision path only knows about one org. The corpus root, the document register
  and the recorded judgments all point at Northstar. On a renamed copy of Northstar, the first judgment
  misses the replay (a 503 in the service). With judgments supplied, the decision **ran on Northstar's
  registered texts** and recorded three incidents. Section 4 has the probe.
- **`--truth DIR` is not a second-company feature.** It only builds variants of Northstar that keep
  Northstar's ids. Of 21 single-change probes, 15 failed and 3 passed but silently changed the dataset.
  After every name in the truth was renamed, 18 of 38 evidence files still said "Northstar".
- **Platform audit headline:** the mechanisms are generic. Each use case, though, is wired in by hand in
  about 20 code sites across the registrar, the service and its contract, the MCP tools and the admission
  gate, plus about 10 more in the generator and oracle. Today a new use case needs code and data.

## 2. What a second `truth/` needs

The schema is the pydantic models in `src/northstar/model/` (`extra="forbid"`). The loader requires
the discount sections of `entities.yaml`, and a missing one raises KeyError (`model/truth.py:175-186`).
The credit sections are optional (`:194-197`), and so is `support.yaml` (`:199`).

| File / section | Northstar today | Org B (discount, then credit) | Kind |
|---|---|---|---|
| `organization.yaml` | 43 lines: 4 systems, 4 departments, 10 roles (6 lab extensions) | ~30 lines, 3 departments, 5–7 roles | From scratch |
| `entities.yaml` customers / accounts | 4 / 1 | 4 / 1–2 | From scratch |
| `entities.yaml` employees | 9 (5 lab extensions) | 6–8; credit adds 2–3 | From scratch |
| `entities.yaml` products / contracts / pricing_exceptions | 3 / 2 / 2 | 3 / 2 / 2 | From scratch |
| `entities.yaml` orders / discount_requests | 2 / 2 | 1–2 / 2 | From scratch |
| `entities.yaml` guarantees / invoices / credit_requests | 1 / 10 / 1 | credit phase: 1 / 8–12 / 1 | From scratch |
| `policies.yaml` policies / principles | 3 / 2 | 2–3 / 2 (must cover the background window, §3 G11) | Adapt the structure, write new values |
| `policies.yaml` credit_policies | 2 | credit phase: 2 | Adapt |
| `relationships.yaml` | 37 rows, 17 predicates; duplicates `entities.yaml` (cross-checked) | ~30 rows | Mechanical, could be generated |
| `facts.yaml` | 39 facts (26 asserted, 13 derived); 46 lines | 15–25 | Lab scaffolding (evaluation sheet), tied to the generator's `asserts` tags |
| `corpora.yaml` | base + 2 variants | base + 1 (+1 for credit) | Adapt; excludes artifact ids that the generator fixes |
| `scenarios/*.yaml` | 45 files, 1,727 lines total: 22 discount, 10 credit, 10 SLA, 3 other | 14–16 discount + 8 credit | From scratch: this is the held-out value |
| `support.yaml` | 289 lines (SLA) | None (SLA is out of the slice) | — |

Scenarios share one base request per decision type and vary it with overrides (`request: {base: …,
<field>: …}`; 24 of 32 decision scenarios override `id`). Org B therefore needs only one pending
request per type in `entities.yaml`. In the service, each variant has to exist as a system-of-record
row (through `/lab/sor`), because the kernel reads rows, not scenarios.

## 3. Couplings in the generator (`src/northstar/`)

A probe applied one change to a copy of `truth/` and ran `northstar check --truth <copy>`. Results: `scratchpad/f2/probes.log` (E01–E21) and the probe
folders (E30–E42).

| # | Where | Coupling | Effect (probe) | To lift it |
|---|---|---|---|---|
| G1 | `generators/emails.py:16,27,31-33,43,57` | Fixed request id; customer name and backstory in the template; fixed artifact id; fixed `mentions` | Renaming the request: KeyError | Narrative artifacts written in truth, or iterate over requests |
| G2 | `generators/documents.py:24-31` | Exactly three pricing policies by id, with hard-coded publication dates and fact ids | Renaming or dropping a policy: KeyError (E06, E20) | Iterate over `truth.policies`; publication date in truth |
| G3 | `documents.py:109,146` | Authority matrix bound to one policy id and date | — | `authority_matrix_document` already exists; use it |
| G4 | `documents.py:207-211,280-286,341` | Fixed contract and exception ids; `holders_of("CRO")[0]` | KeyError (E08, E09, E15); renaming the top role: IndexError (E04) | Iterate over contracts and exceptions; signatory role in truth |
| G5 | `documents.py:426,433-461,484-512` | Account plan for one fixed customer, prose about its history; lookalike ticket for a fixed customer and product | KeyError (E02) | Hand-authored narrative docs in truth |
| G6 | `documents.py:19,180,213-244,304,313,379-388`; `crm.py:83,159`; `erp.py:58,127` | "Northstar" and "Chicago, IL" in template text and source-system names | After renaming every truth name (E42), 18 of 38 files still say Northstar and 14 the old customer | Organization fields (name, short name, systems, HQ) |
| G7 | artifact ids and paths, for example `documents.py:258-259,319-320,464-465` | File names carry Northstar entity names; `corpora.yaml` excludes them | Cosmetic, but they leak into org B | Ids derived from truth ids |
| G8 | `crm.py:86,162-165`; `erp.py:61,150`; `documents.py:155,199,274-276,334-336,477-479`; `finance.py:123,182,203,257,299` | `supports`, `asserts` and `mentions` tags written as literal ids | Renaming one CRM id makes the oracle drop it from evidence, so 25 scenarios fail (E10) | Derive `supports` from what is rendered; `stated_in` in `facts.yaml` |
| G9 | `generators/finance.py:19-24,128,136-137,159,262-264,274-278,91,102` | Role-word plurals per role id; `guarantees[0]`; guarantor city and signatory; fixed credit request and recipient employee; "Northstar CRM/ERP" in the policy text | KeyError (E11, E12); E03 KeyError in `ROLE_WORDS` | A plural field on roles; iterate; organization fields |
| G10 | `generators/support.py:28-29,88-235,400-401,461-466` | Time zone and Northstar text; two fixed executive ids; a branch for one customer id | Renaming an executive id: KeyError (E07) | SLA only. Defer |
| G11 | `factories/_base.py:16,20-21` | `RESERVED_TOKENS` (Northstar names); fixed 2025-01-02..2026-09-20 date window | Dropping a policy (E21) or shifting all dates +3 years (E41): AssertionError | Window and reserved names come from truth |
| G12 | `factories/employee.py:13-21,32,33` | Title list; background managers fixed to two Northstar ids; title-to-role map | Renaming a manager id (E13) passes, but 3 background staff point at a missing manager and drop out of the org chart | Department heads come from truth |
| G13 | `factories/background.py:285` (and `:82,159,177,181-182`) | Lowest band hard-coded as `ENTERPRISE_AE`; AR title; `caps["Standard"]` | Renaming the lowest role (E05) passes, but all 19 background self-approvals go to a truth employee instead | Lowest band read from the policy |
| G14 | `background.py:173-174`; `finance.py:27-35` | Credit is not optional in the background or the generator | Dropping credit (E19): AssertionError. A discount-only org builds after two 2-line gates (E40: 18 artifacts, 25 scenarios coherent) | Gate on `truth.credit_policies` |
| G15 | `background.py:244,251`; `customer.py:23,62-79`; `erp.py:37` | "NS-" SKUs, Midwest cities, segments, "Net 45" | Cosmetic, but every org looks like Northstar | Organization fields |
| G16 | `model/scenarios.py:33-40`; `entities.py:153,255,320`; `build.py:49-60,231`; `oracle.py:88,144,248,417`; `sla.py:21-22,335` | Closed scenario kinds, Literals per use case, `source_ids["erp"]`, the `organization_chart` key, a "northstar" obligation party | Structural: a new kind needs code (§5) | Part of the platform work |
| G17 | `tests/conftest.py:11`; `tests/test_corpus.py:38-47` | Tests hard-code the truth path, artifact ids and a person's name | The corpus invariants are never checked for org B | Parametrize by truth directory |

Probes that passed without harm: renaming a product id (E14), the guarantee id (E16), and dropping SLA
(E18). **Answer to question 2: only Northstar variants.** A truth with new ids or names fails or leaks
Northstar text, and a truth with new dates fails. A truth that keeps Northstar's ids and swaps values
still ships Northstar's prose, file names and trap layout, so it would not be held out.

## 4. Couplings in the decision path (`lab/`)

Severity: **blocks** means it fails, or decides on Northstar's data. **Degrades** means it runs, but is
wrong in some cases or needs per-org setup. **Cosmetic** means labels only.

| # | Where | Coupling | Severity |
|---|---|---|---|
| D1 | `owm_service/_lab.py:135-139` | The corpus root is always `LAB_ROOT/dataset/evidence[-variants]`, so org B would have to live inside `dataset/` | blocks |
| D2 | `owm_register/registrar.py:44-47,107,133`; `_lab.py:164-166` | Fixed `CORPORA` dict; `Staff` defaults to Northstar's base; the register bootstrap is `lab/owm_register/<corpus>.yaml` | blocks |
| D3 | `owm_register/build_register.py:41,44-46,237`; `:50-52,90-101,268-283` | The register is built from `LAB/truth` (Northstar) with fixed corpora, named Northstar approvers, "Northstar CRM/ERP" terms and fixed doc ids | blocks |
| D4 | `_lab.py:63-66,90-95`; `decision_engine/engine.py:89-91` | Judgments replay by a hash of their inputs, from `runs/`. Any new text misses, and the miss is `JevUnavailable` (503) | blocks at $0 (a live Jev run costs cents) |
| D5 | `owm_service/sessions.py:97-104`; `fixtures/mandates.yaml:15` | The agent mandate's accountable person is a Northstar employee id. On org B this raises NotFound, so the agent journey cannot start | blocks |
| D6 | `owm_kernel/specs/discount.yaml:10-14,32,74`; `credit_v3.yaml:14-16,37` | Specs fix the id prefixes, title words and **owning function names** (G1 provenance), plus an "NS-" product regex and an "EXC-" supersedes regex | blocks if org B's documents or function names differ from the templates |
| D7 | `owm_kernel/kernel.py:214-247,336-337,116,121,176,193` | Prose parsers expect the generator's exact grammar ("## 3. Approval authority", "may approve … up to and including N%", "approved by: Name, Title, date"). The discount procedure reads authority from prose (`discount.yaml:121`). Credit v3 reads registered terms | blocks for documents someone writes by hand |
| D8 | `owm_register/registrar.py:48-53,88,54-82` | Fixed kind→function map (Sales, Finance, Customer Support); the no-grant phrase names "northstar's"; per-kind term schemas in code | degrades: register changes are refused for other function names |
| D9 | `owm_register/procedures.yaml:5-30`; `build_procedures.py:41-46`; `owm_kernel/governed.py:19-22,57-59` | One global procedure register naming Northstar approvers, effective from 2025-01-01; an earlier as-of date raises `NoProcedureError` | degrades (dates), cosmetic (names) |
| D10 | `owm_service/decisions.py:85,178` | Request ids must start with `DR-` or `CR-`, else 422 | blocks if org B uses other id formats |
| D11 | `owm_service/clock.py:18`; `clearance.py:382-387`; `assemble.py:222`; `history.py:71`; `config.py:13` | Chicago time zone for the day boundaries of `per_day` limits and for display; the default demo clock | degrades (the env var overrides the clock, not the time zone) |
| D12 | `owm_service/sor.py:29-57`; `prepare.py:42-50`; `owm_kernel/flow.py:374` | Table and column names of Northstar's exports (keys, numeric columns, basis fields, `employees`/`products`) | degrades: fine with the same generator; blocks other system-of-record schemas |
| D13 | `owm_service/clearance.py:107-109` | Incident owner by function name | degrades |
| D14 | `spec_admission/admit.py:40,52-60,100-103` | The gate loads Northstar's truth, answer key and sealed attack sets, so a spec cannot be (re)admitted for org B | blocks for any per-org spec change |
| D15 | `rounds/scenarios.py:15-44,93-108`; `rounds/tools_server.py:6,42-43,264`; `owm_service/smoke.py:19,44-49` | Prompts, the request, the people and the S22 scenario are fixed | blocks the MCP/proof journey; cosmetic for the service |
| D16 | `owm_kernel/specs/sla.yaml:207-228`; `sla_agent.yaml:39-86,499-575` | Role titles, "Northstar" in judgment prompts, America/Chicago | SLA later: blocks for other titles |
| D17 | `owm_service/org.py:59`; `register_view.py:59-60`; `conditions.py:44` | `org_id="northstar"`, labels, system names | cosmetic |

**Probes** (`scratchpad/f2/decide_probe*.py`, recorded answers only):
- **Committed dataset:** the governed discount decision ran fully from recordings.
- **Renamed-customer org:** the first party judgment missed the replay.
- **Same org, with each judgment translated back to Northstar's names before the lookup:** the decision
  completed, but `use_registered` read Northstar's approved contract and exceptions instead of org B's
  files and raised three incidents. With Northstar's register, org B is decided on Northstar's documents.
- **Kernel policy parser:** it reads the templated policy's bands. With the section heading renumbered,
  or the verb reworded, it reads none. Writing "10 percent" drops a band.

The three procedure specs in force are `discount.yaml`, `credit_v3.yaml` and `sla.yaml` (and
`sla_agent.yaml` as SLA v2). `discount.py`, `credit.py` and `sla.py` in the kernel are older code and are
not on the service path (`_lab.py:43-49` imports none of them).

## 5. Platform audit (D2)

**Generic today (the mechanism):**
- **Spec-as-data runner and its expression language:** `flow.py` and `SPEC_FORMAT.md`.
- **Governed procedure register:** by decision-type string (`governed.py:41-77`).
- **Document register:** R1/R3, `entry_in_force`, revocation (`kernel.py:631-748`).
- **Authority:** bands over % or $ (`amount_of`), approver resolution up the chain, separation of duties,
  concurrence (`kernel.py:209-418`). The terms-based variant is `authority_from_terms` (`:749`).
- **Ratchet:** levels over policy bands (`ratchet.py:60-110`).
- **Clearance:** bind, single use, TTL, redeem, report (`clearance.py`).
- **Decision records:** the event log and versions.

**Wired in per use case (code):**

| Layer | Sites |
|---|---|
| Contract and models | `DecisionType`, `ROUTE_TO`, outcome Literals, findings union (`models.py:319-335,353-407`); `owm-decisions.ts:240,255-257,270-312,407` (`ActionName` closed) |
| Service maps | `_lab.py:51-54,353`; `procedures.py:55-57` (`KIND_OF`); `prepare.py:42-50`; `sor.py:29-57`; `decisions.py:85,173`; `ratchet.py:42-57,96`; `clearance.py:107-111`; `assemble.py:130-160,254-277` (findings and actions per type); `conditions.py:44`; `lab_adapter.py:50-53`; `sessions.py:62,68`; `register_view.py:59` |
| Approvals | `owm_kernel/additions.py:123-136` (SLA branch) |
| Register | `registrar.py:48-82` and the per-kind `terms_check` branches (`:286-330`); `serve.py:28-37,59-122` (rendering per kind); `build_register.py` (an entry builder per kind) |
| MCP tools | `rounds/tools_server.py:42-67,184-215`: one hand-written `apply_discount` tool; credit has no tool |
| Admission | `admit.py:40-41` (a reference spec per type, credit kind map) |
| Generator and oracle | `entities.py:221-290`, `truth.py:72-83,194-209`, `scenarios.py:33-40`, `oracle.py:198-347`, `factories/credit.py`, `generators/finance.py`, `build.py:49-60` |

**How credit was added (the worked example).** Credit took new kernel functions (K-1 to K-4 in
`kernel.py:209-247` and `linked` at `:100`), a spec, and every row of the table above. So a new use
case is **both code and data**. Only the procedure (the spec YAML) is data, and even a spec carries
org-specific owners and wording (D6).

**What the spec must require so that a use case is added as registered data, with no kernel or MCP
code change:**
1. **A registered use-case definition**, versioned and approved by two people like a procedure. It
   declares:
   - the decision type id;
   - the subject: system-of-record table, key column, id pattern;
   - the input fields, with type and unit (fraction, USD);
   - the outcome vocabulary, `route_to`, and which outcomes approve;
   - a findings JSON Schema;
   - its actions: name, params mapped from subject and figures, target system, incident owner;
   - its governing kinds, each with a terms JSON Schema, an owning function role, and declarative text
     checks;
   - the ratchet figure and the policy kind.

   This replaces the maps in `_lab`, `prepare`, `sor`, `ratchet`, `clearance`, `assemble`, `procedures`,
   `registrar` and `serve` that section 5 lists.
2. **An org profile as data:** function names and which function owns which kind; the HR, item-master
   and account table mappings; id patterns; time zone and business calendar; system names. This removes
   D6, D8, D10, D11 and D13 for every org.
3. **An open contract:** `DecisionType` is a string checked against registered definitions, and findings
   and actions are typed by the definition's schemas rather than a TypeScript and pydantic union.
4. **Generic MCP tools** (`get_subject`, `decide`, `request_clearance`, `execute(action, params)`)
   whose input schemas come from the registered actions. `apply_discount` becomes data.
5. **Authority and eligibility from registered terms only** (R2, as `credit_v3.yaml` does), so wording
   never matters. The prose readers stay optional. This removes D7 and makes outsider-written documents
   possible.
6. **An admission gate whose inputs are the org, the definition, the scenario set and the attack set**,
   not Northstar's files.
7. **An acceptance check of the rule itself:** on org B, credit is added through definitions, specs and
   register entries, with an empty diff under kernel, service, contract and MCP code (checked in CI).

## 6. Effort

**Assumptions:**
- One developer who knows this repo, working with agents at the lab's usual pace.
- Northstar's committed dataset stays byte-identical, because the `dataset-*` tags are consumed by the
  demo.
- Discount first, then credit; SLA is not sized.
- No model spend except an optional capped Jev recording on org B (cents, going by the lab's recorded
  Jev costs).
- The full platform work in §5 items 1–4 is the OWM team's spec work and is **not** included.

| Work | Days |
|---|---|
| **(a) Writing the org** | |
| Writer's guide and a neutral rule sheet for the outsider (lab) | 1–1.5 |
| Outsider writes and proves the discount org (~550 YAML lines, 14–16 scenarios) | 3–5 |
| Third-party adjudication of author-vs-oracle disagreements | 0.5–1 |
| **Discount subtotal** | **4.5–7.5** |
| Credit addition (~250 lines, ~8 scenarios), including adjudication | 2–3.5 |
| (If the lab writes it instead, which G-39 advises against: discount 2–3, credit 1–1.5) | |
| **(b) Removing the couplings** | |
| Generator G1–G17: data-driven templates (2–3), derived tags (1), factory constants and gates (0.5–1), parametrized tests (0.5–1), Northstar byte-identity regression (0.5–1) | 4–7 |
| Decision path, discount: one org-root setting across D1–D3, D14 (1); a register bootstrap from any truth and corpus (1.5–2); D5, D8–D11, D13 as org config (1–1.5); admission gate per org (1–2); a Jev recording run or a local judge (0.5); end-to-end service run on org B (0.5–1) | 5–8 |
| If org B's governing documents are outsider-written (D7): move discount authority and eligibility to registered terms, as a new admitted procedure version | +2–4 |
| Credit on org B after discount (tier, role words, register terms) | +1–2 |
| **Coupling subtotal** | **10–17 templated; 12–21 outsider-written** |

Critical path: the generator fix (4–7 days), then the outsider's writing (6.5–11 days), while the
decision-path work runs in parallel. That comes to about 11–21 working days, or 2.5–4.5 weeks.

**What an outsider needs, and must not see (G-39):**
- **Uses:**
  - the model schemas (`src/northstar/model/*.py`);
  - a writer's guide covering file formats, scenario kinds and their `expected` fields;
  - section 7 of this report;
  - a neutral rule sheet for each decision type: the outcome vocabulary and the decision rules, in the
    way the SLA rules were written blind (`truth/support.yaml:1-4`);
  - the fixed generator, with `northstar check` as the proof loop.
- **Records** their `expected:` blocks (committed, hashed) **before** the first `check`. On a mismatch
  the oracle prints its own answer, so expectations written after a run are not independent.
- **Must not see:**
  - Northstar's `truth/`, `dataset/answer-key/` and `dataset/evaluation/`;
  - `dataset/evidence/`, if they write documents, so that they don't copy template phrasing;
  - `lab/owm_kernel` (the specs and parsers), `lab/owm_service`, `lab/owm_register` and `runs/`
    (attack sets, recorded judgments);
  - the README's trap and scenario tables, `owm/`, the four design docs, `tracker/` and `knowledge/`.

## 7. A minimal viable held-out org (discount slice)

**Scale:** about 7 people in truth plus generated noise; 2–3 policies; 4 customers; 3 products; 2
agreements and 2 exceptions; 1 pending request and 1 precedent; 2 corpora; 14–16 discount scenarios plus
an identity and a provenance scenario.

**Kinds of difficulty, each at least once:**
- **Authority:** a request within the requestor's band; one above it, so it routes to the nearest
  holder up the chain; one in the top band; a requestor in a middle band.
- **A plausible wrong approver:** someone in another function with a senior-sounding title and no
  discount authority.
- **Eligibility:** within the contractual maximum; above it; on a product the agreement covers but the
  exception does not; a customer with no contract (standard pricing).
- **Time:** a request dated in an earlier policy period with different bands; a policy published
  before its effective date; a superseded exception whose window meets the current one at a boundary
  date.
- **Evidence:** a corpus without the contract documents, where hearsay (an email, an account plan, a
  precedent) remains and must not stand in for the instrument.
- **Identity:** a customer whose ids differ by system and whose legal name differs from its trading
  name; a distinct customer with a lookalike name.
- **Input provenance:** a submitted value that conflicts with the system of record, in three forms
  (amount, date, status).
- **Variation the engines were not tuned on**, within what the oracle can prove:
  - a different number of bands, with non-round thresholds;
  - an approver two levels up;
  - different id formats, once D10 is lifted;
  - different function names and document wording, once D6/D7 are lifted.

**Credit, later:**
- **Scale:** 2 credit policies (bands on the new limit, a tier-scoped concurrence, caps by tier, a
  lateness lookback); 1 guarantee naming one legal entity; invoices for 3 customers, one of them late
  inside the lookback; 1 pending request; about 8 scenarios.
- **Difficulty:** concurrence; guarantee scope; over cap; late payer; earlier policy; a missing-guarantee
  corpus; separation of duties; a submitted conflict.

## 8. Open questions

1. Should org B's governing documents come from templates (cheaper; leaves D7 untested) or be
   outsider-written (+2–4 days; forces registered terms)? I recommend outsider-written for the policy,
   agreement and exception, at least.
2. Who is the outsider: a blind subagent (model spend) or a person (calendar time)?
3. To answer judgments on org B: approve one capped live Jev recording run (cents), or build a local
   deterministic judge?
4. Should org B keep Northstar's function names? Specs would then run unchanged, but that axis would go
   untested.
5. Does acceptance read org B's files directly (the kernel `Evidence`), or through the knowledge
   foundation (F1)?
6. Is byte-identical Northstar after the generator fix a requirement, or can a new `dataset-*` tag be cut?
7. The oracle shares a designer with the engines (G-39). Who adjudicates when the outsider's `expected`
   and the oracle disagree, and is the rule "fix the truth or the oracle, never the engines"?
8. Where does org B live? If it sits in this repo, the never-load rule must extend to it. If it is
   sealed elsewhere until acceptance, the OWM team cannot tune on it.
9. Is the small scale enough, or must acceptance also run at the large scale?
10. Confirm SLA stays out of F2. D16 and G10 are listed but not sized.
