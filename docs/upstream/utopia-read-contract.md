# Utopia: issues surfaced by the Northstar experiment (drafts, not filed)

These are drafts for the Utopia maintainers (`deeplethe/utopia`, `dev` @ `aad5b06`). Each one
is backed by a run in `runs/2026-09-28-utopia-aad5b06/`. File them, edit them, or drop them;
nothing has been posted.

They all concern the seam an application builds on. Utopia's own record (ADR 0046) says "MCP
is where an application on this knowledge gets built … against the read contract". An
Organizational World Model sits exactly there.

---

## 1. `entity_facts` should carry each fact's supporting quote (or chunk id)

**What happens.** `entity_facts` returns `document_ids`, but not the sentence a fact came from.
Values that only live in that sentence are invisible to a graph-only reader. In our corpus
those were the discount percentages and the approval bands.

**The only graph-side route is `changes`,** used per entity with `since` = ingestion day. That
is a record-time audit feed repurposed as a quote retriever. Whether a reader finds this
path decides its answers:

- A blind Opus reader limited to the graph tools found it in 8 of 9 runs on one graph state
  and 0 of 9 after an identity correction.
- S04 was right exactly when it did.

(`repeats/notes.md`)

**Ask.** Add `quote` (and a stable chunk id) to each `facts[]` entry in `entity_facts`
`structuredContent`. `chat-and-mcp.md` already lists "the chunk identity behind a quote" as a
read-contract gap.

## 2. Record-time replay isn't uniform on MCP

**What happens.** We tried to replay a pre-merge graph by stamping `as_of` on every MCP read.
Two gaps made that impossible:

- **`find_entities` has no `as_of`,** although `utopia_store::graph::search_entities` takes
  one ("merged sources before the merge are still visible"). Merged-away entities can't be
  *found*, only reached by id.
- **`changes` windows are whole days** (`since` / `until` as dates), so events within a day
  can't be excluded.

(`repeats/notes.md`, "Why a revert, not a replay")

**Ask.** Expose `as_of` on `find_entities`, and accept RFC 3339 instants for `changes`
`since` / `until`.

## 3. A manual merge can drop the merged entity's identifier

**What happens.** `POST /kbs/{id}/entities/merge` with source = an ID entity created from a
CSV row (`C-1001`, `CRM-2048`) and target = the customer. The facts moved correctly, but the
ID stopped being findable: the source had a `canonical_name` and no name fact, so nothing
carried over. `C-1044`, which *had* a document-attested name fact, survived. This appears to
diverge from ADR 0041 decision 1: "`entities.canonical_name` … is also one of the entity's
name facts".

**Effect.** After a correct human merge, `find_entities "C-1001"` returned nothing. It had
returned the ID entity before (`correction/comparison.md`, finding 2).

**Ask.** When merging, record the source's `canonical_name` as a name fact on the target
(attributed to the merge), or ensure every entity carries its canonical name as a name fact.

## 4. The Statements push has no way to reference an existing entity

**What happens.** Statements take names only (`e: [name, kind word, named]`), and any other key
is refused. Pushing "Sarah Chen reports to Michael Torres" (exact existing names, untyped
entities, no kind bindings) created **new** Sarah Chen and Michael Torres entities, queued
for a human at 0.52 and 0.54. In a larger push most names attached directly, but not all.
The push also raised new candidate pairs (Acme Mfg. Holdings ≟ Acme Industrial Supply Co.,
0.77). (`curation/notes.md`)

**Effect.** Every write-back from an external system is an identity review.

**Ask.** An optional entity reference in `e` (for example a fourth slot, or `{id}`), honoured
only for a token with write scope and the editor role. Or document the attachment rule so
integrators can predict it.

## 5. Dense CSV chunks lose rows to truncated extraction replies

**What happens.** All six CSVs in a 17-file corpus had a `truncated_reply` drop ("the open reply
was cut off; kept up to the last complete item"). Rows after the cut produced no facts. One
lost row was the discount request DR-9001, including its justification "Contract pricing per
Acme MSA". Without it, a reader following the organization's procedure can't tell that the
request relies on a contract (`procedure/notes.md`).

**Ask.** Chunk tables by row count rather than characters, or re-ask for the remainder when
a reply is truncated, so structured sources extract completely.
