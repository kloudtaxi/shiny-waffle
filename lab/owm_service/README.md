# OWM service (contract v1.2)

The lab's Organizational World Model service: decisions, the ratchet, clearances, the register
and procedures, and approvals, over HTTP. The design is
`docs/superpowers/specs/2026-10-10-owm-service-design.md`. The contract is in `contract/`.

## Run it locally

```bash
PYTHONPATH=lab uv run --group owm-service python -m owm_service
```

The service listens on `0.0.0.0:8000`. `GET /healthz` reports health. State (the event log, the
stores and the recorded Jev calls) lives in `OWM_STATE_DIR`.

## Checks

```bash
uv run --group owm-service pytest
uv run --group owm-service mypy
bash scripts/owm-gate.sh        # the full regression gate, replay only
```

Both commands need the `owm-service` group, because the code and the HTTP tests type-check
against FastAPI (R38). Plain `uv run mypy` fails without it.

## Docker

```bash
docker build -f lab/owm_service/Dockerfile -t owm-service:dev .
docker run --rm owm-service:dev sh -c 'for p in truth dataset/answer-key dataset/evaluation site \
  lab/utopia lab/spec_admission src README.md; do test ! -e "/app/$p" || exit 1; done; echo isolated'
docker run -d --name owm-smoke -p 8000:8000 -e OWM_LAB_ROUTES=1 owm-service:dev
uv run --group owm-service python lab/owm_service/smoke.py --base http://localhost:8000
docker rm -f owm-smoke
```

The smoke script runs S22's main branch over HTTP (ask DR-9001 at 8%, Sarah confirms the record,
Michael approves, the agent clears 15%, the adapter executes) and prints `S22: spent`. It needs
the lab routes, so the run sets `OWM_LAB_ROUTES=1` explicitly.

The build context is the repo root. The image copies only what the service runs:
- the four lab packages it imports: `lab/owm_service`, `lab/owm_kernel`, `lab/owm_register` and
  `lab/decision_engine`;
- `dataset/evidence/` and `dataset/evidence-variants/`;
- from `runs/`, only the 13 recorded Jev exchange files and the procedure admission reports.

The dependencies are installed with `uv sync --no-install-project`, so neither `src/` (the
`northstar` package) nor the repo README is in the image. `.dockerignore` also keeps `truth/`,
`dataset/answer-key/`, `dataset/evaluation/`, `site/`, `_owm-local/`, `.vault/`, `.owm-service/`,
`.superpowers/`, `.claude/`, `.git/` and the rest of `runs/` out of the build context, so the
image enforces the lab's isolation itself. The image holds no key. It runs as a non-root user,
with `/data` as its volume.

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `OWM_STATE_DIR` | `.owm-service` locally; `/data` in the image | The event log, stores and recorded Jev calls |
| `OWM_CORPUS` | `base` | The org's corpus (`base`, or a name under `dataset/evidence-variants/`) |
| `OWM_JEV` | `replay` | `replay` or `live` |
| `OWM_JEV_CAP` | `100` | Live calls allowed per state directory |
| `OWM_CLOCK` | `2026-09-23T09:00:00-05:00` | The demo's start time |
| `OWM_CLEARANCE_TTL_SECONDS` | `300` | Clearance lifetime |
| `OWM_SUSPENDED` | empty | Comma-separated agents, or `agent@sha` versions, that are suspended |
| `OWM_LAB_ROUTES` | `1` locally; `0` in the image | `0` removes every `/lab/*` route |

`OWM_LAB_ROUTES` accepts `1/true/yes/on` and `0/false/no/off`. Anything else is refused at
startup, so a typo never leaves the routes switched on.

## Warning: the lab routes

`/lab/*` lets anyone sign in as anyone, edit the discount and credit requests and the service
tickets, add ticket events and service credits, move the clock and reset the org. Every other
system of record (HR, accounts, customers, products, invoices) is read-only, and a write to it is
422 RR-5 (R60): those tables decide who approves and at what tier. It is demo scaffolding outside
the contract, with no real authentication. The image defaults it off. A demo deployment that
turns it on must stay reachable only from web-next's server, never from the open network.

## Live Jev

The default is replay: every kernel call is answered from recorded exchanges, and a miss is a
503, never a silent live call. Going live spends money. Pre-register the run and spend only after
the user agrees a cap (`OWM_JEV_CAP`).

The service's own settings never read the key. In live mode, on the first call that misses the
replay, the lab engine reads it (`lab/decision_engine/engine.py`, `_key_from_env`):
1. from `TYPESAFE_API_KEY`, the key itself, if that variable is set;
2. otherwise from the file whose path `TYPESAFE_API_KEY_FILE` holds.

Neither belongs in an image: no `ENV` and no key file baked in. Prefer the file: mount it at run
time and set `TYPESAFE_API_KEY_FILE` to its path when the container starts. The key is never
logged or recorded.

## Known limits

- Approving a new register entry of a kind that decisions read can make the next such decision
  miss the replay and return 503 in replay mode.
- `self_sourced_basis` sees only edits made through the service.
- Live calls that fail do not count toward the cap, and a missing key surfaces as 503
  `cannot_decide`.
- Sign-in is demo sign-in only.
- A new request id is a new subject: DR-9002 is not linked to DR-9001.

## What this service is not

From spec §3:

- Real authentication or an identity provider, and hosting.
- Mandate changes, Manage and Agents screens, and trust records. Suspension is configuration, not
  an endpoint.
- G-43's outcome change (emitting `possible_duplicate`), meaning-flip protection (G-44), and
  linking re-entered requests (DR-9002).
- The admission gate. The service accepts a report the lab's `admit.py` produced.
- Reversals and adjustments, external agents acting, a "what if" endpoint, and `as_known_at`
  (G-38).
- web-next changes: the `OWM_API_URL` route and a Northstar demo org.
- Reporting every finding on a draft register change at once.

It is also not the system under test's knowledge base: it holds no `truth/`, answer key or
evaluation sheets.
