"""Snapshot a settled KB the way runs/2026-09-28-utopia-aad5b06/snapshot/ did. Usage: snapshot.py <kb> <prefix> <outdir>

Writes <prefix>.ttl, .ontology.json, .graph-overview.json, .review-summary.json, .extraction-drops.json,
.documents.tsv, .entity-merges.tsv, .pending-reviews.tsv, and prints the step-4 counts row.
"""
import json
import subprocess
import sys
from pathlib import Path

import utopia as u

kb, prefix, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)


def sql(q: str) -> str:
    return subprocess.run(["docker", "exec", "utopia-db-1", "psql", "-U", "utopia", "-d", "utopia",
                           "-A", "-F", "\t", "-P", "footer=off", "-c", q],
                          check=True, capture_output=True, text=True).stdout


(out / f"{prefix}.ttl").write_bytes(u.call("GET", f"/kbs/{kb}/export?format=turtle", timeout=300).read())
for name, path in (("ontology", "ontology"), ("graph-overview", "graph/overview"),
                   ("review-summary", "review/summary"), ("extraction-drops", "extraction-drops")):
    (out / f"{prefix}.{name}.json").write_text(json.dumps(u.jcall("GET", f"/kbs/{kb}/{path}"), indent=2, ensure_ascii=False) + "\n")
(out / f"{prefix}.documents.tsv").write_text(sql(
    f"select filename, status, graph_status, chunk_count, doc_time, doc_time_source from documents "
    f"where kb_id='{kb}' and deleted_at is null order by filename"))
(out / f"{prefix}.entity-merges.tsv").write_text(sql(
    f"select t.canonical_name as target, s.canonical_name as source, m.reason, m.created_at "
    f"from entity_merges m join entities t on t.id=m.target_id join entities s on s.id=m.source_id "
    f"where m.kb_id='{kb}' and m.reverted_at is null order by m.created_at"))
(out / f"{prefix}.pending-reviews.tsv").write_text(sql(
    f"select l.canonical_name as left_entity, r.canonical_name as right_entity, v.score, v.status, v.reason "
    f"from resolution_reviews v join entities l on l.id=v.left_id join entities r on r.id=v.right_id "
    f"where v.kb_id='{kb}' and v.status='pending' order by v.score desc"))
one = lambda q: sql(q).splitlines()[1]  # noqa: E731
counts = {
    "entities": one(f"select count(*) from entities where kb_id='{kb}' and merged_into is null"),
    "open_facts": one(f"select count(*) from facts where kb_id='{kb}' and invalidated_at is null and layer='open'"),
    "typed_facts": one(f"select count(*) from facts where kb_id='{kb}' and invalidated_at is null and layer='typed'"),
    "merges": one(f"select count(*) from entity_merges where kb_id='{kb}' and reverted_at is null"),
    "reviews_kept_merged_pending": " / ".join(one(
        f"select count(*) filter (where status='{s}') from resolution_reviews where kb_id='{kb}'") for s in ("kept", "merged", "pending")),
    "doc_time_source": sql(f"select doc_time_source, count(*) from documents where kb_id='{kb}' and deleted_at is null group by 1 order by 1").splitlines()[1:],
}
(out / f"{prefix}.counts.json").write_text(json.dumps(counts, indent=2) + "\n")
print(prefix, json.dumps(counts))
