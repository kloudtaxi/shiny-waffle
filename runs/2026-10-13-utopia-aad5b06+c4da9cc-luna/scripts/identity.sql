-- Acme identity in one KB (:kb). Entities whose name or attrs mention the identifiers, their degree,
-- and every live fact between two of them or carrying an identifier as a value.
with ids as (select unnest(array['CRM-2048','C-1001','ACME-MFG-2025','CRM-2091','C-1044']) as v),
acme as (
  select e.id, e.canonical_name from entities e
   where e.kb_id = :'kb' and e.merged_into is null
     and (e.canonical_name ilike '%acme%' or exists (select 1 from ids where e.canonical_name ilike '%'||ids.v||'%')))
select 'entity' as kind, a.canonical_name, (select count(*) from facts f where f.kb_id=:'kb' and f.invalidated_at is null and (f.subject_id=a.id or f.object_id=a.id)) as degree, '' as detail
  from acme a
union all
select 'fact', s.canonical_name, null, coalesce(f.phrase,'') || ' -> ' || coalesce(o.canonical_name, f.object_value::text)
  from facts f join entities s on s.id=f.subject_id left join entities o on o.id=f.object_id
 where f.kb_id=:'kb' and f.invalidated_at is null and f.layer='open'
   and (f.subject_id in (select id from acme) and (f.object_id in (select id from acme)
        or exists (select 1 from ids where f.object_value::text ilike '%'||ids.v||'%')))
order by 1 desc, 2;
