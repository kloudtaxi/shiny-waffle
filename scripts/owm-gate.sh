#!/usr/bin/env bash
# B-06 regression gate: replay-only proof that kernel/registrar changes moved no committed lab result.
# Never goes live: TYPESAFE_API_KEY_FILE is unset and run_attacks.py is never run.
set -euo pipefail
unset TYPESAFE_API_KEY_FILE
cd "$(git rev-parse --show-toplevel)"

if [ -n "$(git status --porcelain runs/)" ]; then
  echo "gate: refusing to start, runs/ is not clean (a dirty runs/ would mask a regression):" >&2
  git status --porcelain runs/ >&2
  exit 2
fi

tmp="$(mktemp)"
finish() {
  rc=$?
  rm -f "$tmp"
  if [ -n "$(git status --porcelain runs/)" ]; then
    echo "gate: FAIL, files under runs/ differ from the committed ones:" >&2
    git diff --stat -- runs/ >&2 || true
    git diff -- runs/ >&2 || true
    git checkout -- runs/
    [ "$rc" -eq 0 ] && rc=1
  fi
  if [ "$rc" -eq 0 ]; then echo "gate: GREEN"; else echo "gate: FAILED (exit $rc)" >&2; fi
  exit "$rc"
}
trap finish EXIT

step() { echo; echo "== $*"; }

step "register-fixes withhold check"
uv run python runs/2026-10-06-register-fixes/check_withhold.py
step "specs-as-data equivalence"
uv run python runs/2026-10-04-specs-as-data/check_equivalence.py
step "procedures-governed (expect 5 HOLDS)"
uv run python runs/2026-10-06-procedures-governed/run_governed.py >"$tmp"
cat "$tmp"
holds="$(grep -c HOLDS "$tmp" || true)"
if [ "$holds" -ne 5 ]; then echo "gate: expected 5 HOLDS, got $holds" >&2; exit 1; fi
step "register build check"
uv run python lab/owm_register/build_register.py --check
step "procedures build check"
uv run python lab/owm_register/build_procedures.py --check
step "registrar replay (register-attacks)"
uv run python runs/2026-10-08-register-attacks/check_registrar.py
step "registrar steps vs results.json (24 cases)"
uv run --group owm-service pytest tests/owm_service/test_gate_registrar_steps.py -q
step "full test suite (owm-service group: the HTTP tests run, never skip)"
uv run --group owm-service pytest -q
step "ruff (code paths)"
uv run ruff check src tests lab scripts
uv run ruff format --check src tests lab scripts
step "mypy (owm-service group: app.py and the HTTP tests type-check against FastAPI)"
uv run --group owm-service mypy
