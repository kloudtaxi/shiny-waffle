#!/bin/sh
# preflight: the lab's pre-flight checks (lab/preflight/, G-50).
root=$(cd "$(dirname "$0")/.." && pwd)
PYTHONPATH="$root/lab${PYTHONPATH:+:$PYTHONPATH}" exec uv run --project "$root" python -m preflight "$@"
