#!/bin/bash
# The rest of the pre-registered baseline, one run at a time (so each run's tokens are its own),
# in the pre-registration's order: arm A (and the bench setup sets), then arms B and C.
# Guard: before each run, the spend since the first calibration run is priced at gpt-6-luna's
# list price ($0.10 / M input, $0.50 / M output); above $30 the queue stops.
B=$SCRATCH
SINCE=$(cat $B/out/temporal-armA-r1.start)
# Wait for identity run 1 (calibration) to finish.
while [ ! -f $B/out/identity-bench-r1.end ]; do sleep 20; done
spent() {
  python3 -I $B/tools/usage.py $B/bench-utopia.log "$SINCE" | python3 -I -c "
import json, sys; d = json.load(sys.stdin)
p = sum(v['prompt'] for v in d.values()); c = sum(v['completion'] for v in d.values())
print(f'{p * 0.10 / 1e6 + c * 0.50 / 1e6:.4f} {p} {c}')"
}
for job in "temporal-A r2" "identity-bench r2" "recall-A r1" "recall-A r2" \
           "contracts-bench r1" "contracts-bench r2" \
           "temporal-B r1" "temporal-B r2" "identity-C r1" "identity-C r2"; do
  read usd p c <<< "$(spent)"
  echo "$(date -u +%T) before $job: \$$usd (prompt $p, completion $c)"
  if python3 -I -c "import sys; sys.exit(0 if float('$usd') > 30 else 1)"; then
    echo "STOP: spend guard (\$30) reached before $job"; exit 3
  fi
  $B/tools/run-set.sh $job
done
read usd p c <<< "$(spent)"
echo "$(date -u +%T) queue done: \$$usd (prompt $p, completion $c)"
