# G-36 fix, G-35 adoption, and one reader re-baseline (pre-registration, 2026-10-06)

## The user's decisions (2026-10-06)

- **G-36: a per-scenario overlay.** The user first chose "add them to the exports". Claude then
  found that the 24 requests are alternative versions of one situation, so one shared export
  would show each scenario the others' requests as live duplicates (4 pending Acme NS-500
  requests on 2026-09-23; 9 pending credit requests on that day). Asked again, the user chose the
  overlay.
- **G-35: adopt the `conditions` field and the three-sentence rule** with the G-36 fix, then
  re-baseline the readers once, so comparability breaks only once.

This file is committed before the code.

## 1. The overlay (G-36)

`lab/reader_inputs/overlay.py`, `overlay(src_corpus, dst, record, kind)`:
- copies one corpus;
- in its system-of-record export (`discount_requests.csv`, `credit_requests.csv`), drops any row
  with the scenario's request id, or a *pending* request for the same subject on the same day
  (discount: account, product and date; credit: ERP customer and date);
- appends the scenario's request.

So each scenario's system of record holds its own request and no alternative version of it. The
overlay applies only where the question presents the record **"as recorded in Northstar
CRM/ERP"**. Records "as submitted" (S35, and J3's S22–S25) keep the export as it is, because the
conflict is the point there. `truth/`, `dataset/` and the engines are untouched, and no dataset
tag is needed.

## 2. Adoption (G-35)

`owm/procedures/discount-approval.md` and `owm/procedures/credit-limit.md` take the `conditions`
field and the three sentences exactly as tested (`runs/2026-10-06-holds/procedures-v3/`). The SLA
procedure is not changed: it is untested.

## 3. The re-baseline

- **Reader and inputs:** the plain reader (`claude -p`, Opus 5.5, no tools, every document in the
  prompt), with the adopted procedures, on overlay inputs.
- **Scenarios:** experiment 4's 18 discount scenarios plus credit S26–S35, × 3: **84 calls, about
  $26.** The guard stops the run above $0.45 a call.
- **Reads:** one subagent, with `reads-v3`'s definitions, plus "says the request is missing from
  the system of record".

| # | Prediction |
|---|---|
| O1 | **The defect is gone:** no answer says the request is missing from the system of record (0 of 84) |
| O2 | Unsafe by the committed classifiers: **at most 3 of 84** |
| O3 | Every hold in the prose is a blocking condition (at most 1 uncaptured); 0 substituted records; restated approvals at most 2 |
| O4 | With consistent inputs, holds become rare: **at most 15 of 84** answers carry a blocking condition |
