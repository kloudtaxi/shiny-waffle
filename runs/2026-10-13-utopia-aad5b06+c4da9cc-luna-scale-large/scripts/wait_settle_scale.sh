#!/bin/bash
# Wait until every document in the given KBs is ready+graphed and no job for them is pending.
# Exits 0 when settled, 2 on any failed job/document, 3 on timeout. Usage: wait_settle.sh <minutes> <kb>...
q() { docker exec utopia-db-1 psql -U utopia -d utopia -At -c "$1"; }
mins=$1; shift; ids=$(printf "'%s'," "$@"); ids=${ids%,}
start=$(date +%s); settled_since=0; sawfail=
while :; do
  bad=$(q "select count(*) from documents where kb_id in ($ids) and deleted_at is null and (status='failed' or graph_status='failed' or error is not null or graph_error is not null)")
  failed=$(q "select count(*) from jobs j left join documents d on d.id=(j.payload->>'document_id')::uuid where j.status='failed' and j.created_at > to_timestamp($start) - interval '1 hour' and coalesce(d.kb_id::text, j.payload->>'kb_id') in ($(printf "'%s'," "$@" | sed 's/,$//'))")
  notdone=$(q "select count(*) from documents where kb_id in ($ids) and deleted_at is null and not ((status='ready' and graph_status in ('done','failed')) or status='failed')")
  pending=$(q "select count(*) from jobs j left join documents d on d.id=(j.payload->>'document_id')::uuid where j.status not in ('done','failed') and coalesce(d.kb_id::text, j.payload->>'kb_id') in ($(printf "'%s'," "$@" | sed 's/,$//'))")
  now=$(date +%s); el=$(( (now-start)/60 ))
  echo "$(date -u +%H:%M:%S) notdone=$notdone pending=$pending failed_jobs=$failed bad_docs=$bad"
  [ "$failed" != "0" ] && sawfail=1
  if [ "$notdone" = "0" ] && [ "$pending" = "0" ]; then
    [ $settled_since = 0 ] && settled_since=$now
    if [ $(( now - settled_since )) -ge 60 ]; then [ -n "$sawfail" ] && { echo "SETTLED_WITH_FAILURES failed_jobs=$failed bad_docs=$bad"; exit 4; }; echo SETTLED; exit 0; fi
  else settled_since=0; fi
  [ $el -ge $mins ] && { echo TIMEOUT; exit 3; }
  sleep 60
done
