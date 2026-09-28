#!/bin/zsh
# status.sh KB_ID... — pipeline state for the given knowledge bases (read-only SQL).
q() { docker exec "${UTOPIA_DB_CONTAINER:-utopia-db-1}" psql -U utopia -d utopia -At -F ' | ' -c "$1"; }
for KB in "$@"; do
  echo "== KB $KB"
  q "select filename, status, graph_status, chunk_count, doc_time::date, doc_time_source,
            left(coalesce(error, graph_error, ''), 80)
       from documents where kb_id='$KB' and deleted_at is null order by filename"
  echo "-- facts (live) by layer"
  q "select layer, count(*) from facts where kb_id='$KB' and invalidated_at is null group by 1"
  echo "-- entities"
  q "select count(*) from entities where kb_id='$KB'" 2>/dev/null
done
echo "== active jobs (whole instance)"
q "select kind, status, count(*) from jobs where status not in ('done','failed') group by 1,2 order by 1"
echo "== failed jobs in the last 2h"
q "select kind, left(coalesce(last_error,''),160), count(*) from jobs
    where status='failed' and updated_at > now() - interval '2 hours' group by 1,2"
