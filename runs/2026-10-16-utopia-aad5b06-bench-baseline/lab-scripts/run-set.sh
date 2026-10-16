#!/bin/bash
# One baseline run on the throwaway bench instance. Usage: run-set.sh <set> <run-label>
#   sets: temporal-A  temporal-B  temporal-bench  recall-A  identity-bench  identity-C  contracts-bench
# Writes out/<set>-<label>.{start,end,json,log}. Runs only against :1526 and utopia_bench.
set -u
B=$SCRATCH
W=$B/work/bench
export BENCH_BASE=http://127.0.0.1:1526
export BENCH_PSQL="$B/tools/bench-psql -tAc"
case "$BENCH_BASE" in *:1526) ;; *) echo "refusing: not the bench instance" >&2; exit 2 ;; esac
set_name=$1; label=$2; out=$B/out/$set_name-$label
date -u +%Y-%m-%dT%H:%M:%S > $out.start
cd $W
case "$set_name" in
  temporal-A)     BENCH_ARM=A node temporal.mjs --label "A-$label" --no-declare > $out.json 2> $out.log ;;
  temporal-B)     BENCH_ARM=A node temporal.mjs --label "B-$label" > $out.json 2> $out.log ;;
  temporal-bench) node temporal.mjs --label "bench-$label" > $out.json 2> $out.log ;;
  recall-A)       node recall-armA.mjs --label "A-$label" > $out.json 2> $out.log ;;
  identity-bench) node identity.mjs --label "bench-$label" > $out.json 2> $out.log ;;
  identity-C)     BENCH_GOVERNANCE=on node identity.mjs --label "C-$label" > $out.json 2> $out.log ;;
  contracts-bench)
    cd corpora/contracts
    python3 -I lease_bench.py setup --label "bench-$label" > $out.log 2>&1 || { echo "setup failed" >> $out.log; exit 1; }
    kb=$(python3 -I -c "import json;print(json.load(open('lease-kb-bench-$label.json'))['kb'])")
    # Wait for this base's documents and jobs: progress, not total time (stall = 15 min).
    last=""; stall=0
    while :; do
      s=$($B/tools/bench-psql -tAc "SELECT (SELECT count(*) FROM jobs WHERE status IN ('queued','running') AND (payload->>'kb_id'='$kb' OR payload->>'document_id' IN (SELECT id::text FROM documents WHERE kb_id='$kb')))||'/'||(SELECT count(*) FROM documents WHERE kb_id='$kb' AND status<>'failed' AND (status<>'ready' OR graph_status IN ('none','queued','extracting')))||'/'||(SELECT count(c.extracted_at) FROM chunks c JOIN documents d ON d.id=c.document_id WHERE d.kb_id='$kb')")
      case "$s" in 0/0/*) break ;; esac
      if [ "$s" = "$last" ]; then stall=$((stall+1)); else stall=0; last=$s; echo "$(date -u +%T) jobs/open/chunks $s" >> $out.log; fi
      [ $stall -gt 90 ] && { echo "stalled at $s" >> $out.log; break; }
      sleep 10
    done
    $B/tools/bench-psql -tAc "SELECT string_agg(filename||' '||status||'/'||graph_status, '; ') FROM documents WHERE kb_id='$kb'" >> $out.log
    python3 -I lease_bench.py score "$kb" > $out.json 2>> $out.log ;;
  *) echo "unknown set $set_name" >&2; exit 2 ;;
esac
rc=$?
date -u +%Y-%m-%dT%H:%M:%S > $out.end
python3 -I $B/tools/usage.py $B/bench-utopia.log "$(cat $out.start)" "$(cat $out.end)" > $out.usage.json
echo "$set_name $label exit $rc"
exit $rc
