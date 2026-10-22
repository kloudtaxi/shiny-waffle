# F1: can Knowledge Foundation contract v0.2 serve the OWM's evidence reads?

Read-only check, 2026-10-22, by a lab subagent. The lab spot-checked the verdict's claims against
the code: the matching fingerprint functions, contract §13.6, the double corpus read, and
clearance's register-only staleness check. Cost $0: no services were started and no models were
called.
Sources: shiny-waffle `main` at 00325ce; blueleaf-knowledge-foundation (B-20) at 9912391, whose
`src/` and `contract/` are unchanged since the freeze commit 02e9cc9 (`git diff --stat` shows only
`README.md` and `tracker/` changed); the contract text is glowing-garbanzo
`owm/docs/foundation-contract-v0.2.md` (read only).

## 1. Verdict

**`EvidenceProvider` can be an adapter over v0.2. No v0.3 is needed to match what the service does today.**
The kernel needs only four things from a foundation: the list of documents, each current version's
whole canonical text, its file name, and its text hash, plus a lookup by hash. v0.2 serves all four
(K2, K7, K5/K9). Of 31 reads, 5 are served as they are, 7 need a thin adapter, 9 belong to the Data
Foundation and 10 are the OWM's own. None needs v0.3. The adapter is small (about one module), but it
must get three behaviours right: one snapshot per decision, failing closed on a document it can't
read, and leaving out record exports. v0.3 candidates come up only for future needs (gaps 7 and 11).

The contract already planned this split. Its §13.6 says the kernel's `docs()` is "K2 plus K7 for each
current version" and `table(name)` stays with the systems of record
(`foundation-contract-v0.2.md:599-606`).

## 2. Contract v0.2 in brief

Base path `/api/knowledge/v1`. Each caller is a service with a bearer token, and a token can be
limited to named bases and to reading only (`auth.py:17-25`). Ids are opaque (`doc_id`). A version is
an integer and never changes once received (§4.2). Each version carries `file.sha256` (its bytes) and
`text.sha256`. The second is the register's fingerprint, the same function as the kernel's:
compare `canonical.py:50-62` with `kernel.py:621-627`. B-20 computes it when it receives the file
(`ingest.py:84,156`). Spans are half-open ranges of UTF-8 bytes in the canonical text. Errors come as
`{error, detail}`.

| K | Operation | Returns | B-20 at 02e9cc9 | Does the OWM need it? |
|---|---|---|---|---|
| K0 | `GET /about` | `contract`, `serves[]`, `partial[]` | served (`app.py:177-184`) | yes: check before reading |
| K1 | `GET /kbs` | `Page<KnowledgeBase>` | served | yes: corpus to base |
| K2 | `GET /kbs/{kb}/documents?state=&q=&cursor=` | `Page<Document>`: `doc_id, filename, media_type, title, current_version, state, problem, doc_time, created_at, deleted_at` | served; 500 per page at most (`app.py:62,195-215`) | yes: the document list |
| K3, K4 | upload; get, delete, restore | `Document` | served | K4 get only (the writes are BlueLeaf's) |
| K5 | `GET /documents/{id}/versions` | `DocumentVersion[]`: `version, received_at, file.sha256, text.sha256, rendition, superseded_at` | served | yes: text hash, history |
| K6 | `…/versions/{v}/file` | the bytes, with `ETag` set to `file.sha256` | served | no |
| K7 | `…/versions/{v}/text` | the canonical text, with `ETag` set to `text.sha256`; 404 `no_text` | served for text formats and HTML (`app.py:283-296`) | yes: the text |
| K8 | `…/versions/{v}/passages` | `Page<Passage>` with byte spans | served | not today (spans, gap 12) |
| K9 | `GET /kbs/{kb}/versions?text_sha256=` or `file_sha256=` | `DocumentVersion[]` | served (`app.py:307-323`) | yes: finding the copy on file by hash |
| K10 | search | hits and coverage | served | no |
| K11, K12 | asking, answers | | not served | no |
| K13–K17 | facts, entities, identifiers, graph | | served (K13, K15, K16 in part) | no |
| K18–K21 | pipeline, health, changes, review | | not served (`app.py:27-44`) | K20 would help staleness (gap 5) |

## 3. The reads

The classes are: **as-is** (a v0.2 operation serves it directly), **adapter** (v0.2 has the data in a
different shape), **v0.3** (none), **DF** (the Data Foundation, through `RecordReadProvider`) and
**OWM** (the OWM governs the data itself). Paths are relative to `lab/`.

| # | file:line | What it reads | Why | Class | Note |
|---|---|---|---|---|---|
| 1 | `owm_kernel/kernel.py:73-81` | A document's whole text: its YAML front matter (stated id, title, owner, every field) and its body | Every guard and every spec reads these | as-is (K7) | The canonical text keeps the front matter (§4.3). Parsing stays in the kernel |
| 2 | `owm_kernel/kernel.py:108-128, 143-160, 174-182, 214-247, 533-542` | Front-matter fields, then pattern reads over the body: dates, ids it names, one row of a field table, a named section's lines, a paragraph, marker words | Document kinds, windows, authority, cross-document checks | as-is (K7) | Relies on Markdown structure (headings, pipe tables, blank-line paragraphs). See gap 7 |
| 3 | `owm_kernel/flow.py:86-90, 285-303, 378-387` | Spec readers: `doc.body/front/title/owner/doc_id/filename` with regex helpers. The registered specs `discount.yaml`, `sla.yaml` and `sla_agent.yaml` read bodies; `credit_v3.yaml` reads register terms only | Each decision type's findings | as-is (K7) | Specs can't read `raw` (`flow.py:86-90`) |
| 4 | `owm_kernel/kernel.py:621-627, 664-671, 687-712` | The fingerprint of each copy on file. Register status (verified, mismatch or missing); a copy matched to its entry by hash, else by its stated id | Registered versions (R1, R3) | as-is (K5 or K7's `ETag`) | Same function as `text.sha256`. Falling back to the stated id needs row 1's parse |
| 5 | `owm_service/assemble.py:286-301` | The sha256 of an unregistered document the decision relied on: its copy's fingerprint | The decision's basis | as-is | The `text.sha256` of the version read |
| 6 | `owm_service/org.py:71,80`; `_lab.py:123-125, 135-139` | Which corpus to read: the evidence folder or a variant folder | One org reads one corpus | adapter (K1, K0) | Map the corpus name to one base each (CLAUDE.md: one knowledge base per corpus). Check K0 `serves` first |
| 7 | `owm_kernel/kernel.py:90-93` | `Evidence.docs()`: every `documents/*.md`, sorted by file name, as whole text | The decision's set of documents. A missing document means something to the kernel | adapter (K2 + K7) | Read K2's pages and leave out deleted documents. Keep Markdown and drop the CSV record exports. Require text (`state` ready or partial), then K7 each current version. Sort by `filename`. An unreadable document fails closed and never counts as absent (gap 1) |
| 8 | `owm_kernel/flow.py:410-430`; `owm_service/prepare.py:226-232`; `decisions.py:217` | The corpus is read twice per decision: inside the kernel, then again for its fingerprints | Basis and `register_used` | adapter | Serve both reads from one snapshot per decision. Cache texts by (doc_id, version), since versions never change (gap 2) |
| 9 | `owm_service/_lab.py:128-132` | `doc_prints`: (file name, stated id, fingerprint) for every document | Basis sha256, `register_used`, the ids a flag may name (`decisions.py:229`) | adapter | Built from the snapshot: file name from K2, stated id parsed from K7, hash from K5 |
| 10 | `owm_service/register_view.py:121-127, 230` | The copy on file for a register entry, found by the entry's **file name**: its sha256, whether it matches, "differs" or "missing", and `source_id` set to the corpus path | The register view | adapter (K9) | K9 with `text_sha256=<registered>`; keep a version that is current and whose document isn't deleted (K9 checks neither, `app.py:317-322`). Otherwise find the stated id in the snapshot, which gives "differs". `source_id` becomes the foundation's `doc_id`, as the OWM contract already says (`owm_service/contract/owm-decisions.ts:139-143`) |
| 11 | `owm_service/assemble.py:304-323` | `register_used.file_matches`: does a copy with the stated id carry the registered sha256? | The decision record | adapter | Same as row 10 |
| 12 | `owm_kernel/flow.py:548-549` → `owm_service/_lab.py:379-381` | `trace.relied`: (file name, stated id) of each document relied on | Basis documents | adapter | Map each one to the foundation's (doc_id, version, text_sha256), so the basis names the exact version read. Nothing records this today: "the lab has no knowledge-foundation id" (`register_view.py:17-18`) |
| 13 | `owm_kernel/kernel.py:95-97`; `owm_service/_lab.py:112-120`; `org.py:88-90`; `sor.py:99-103` | `Evidence.table(name)`: system-of-record exports plus the logged edits overlaid on them | Every record a decision reads | DF | The overlay of edits belongs on the record side |
| 14 | `owm_kernel/flow.py:374, 459` | The specs' `staff`, `products` and `table()`: HR, products, CRM accounts, ERP customers and invoices, tickets, ticket events, maintenance notices, service credits | Findings and approvers | DF | |
| 15 | `owm_service/_lab.py:142-145`; `org.py:73` | The HR export's base rows, without the overlay | People | DF | |
| 16 | `owm_service/_lab.py:148-154` | An ERP customer, then the CRM account linked to it by a registered identifier | Account tier | DF | Identity by identifier, never by name (K-4) |
| 17 | `owm_service/decisions.py:203`; `prepare.py:98-103`; `ratchet.py:255, 373` | HR rows, account tier | Approvers, the requester, the ratchet | DF | |
| 18 | `owm_service/prepare.py:194-197`; `clearance.py:292-308`; `app.py:254, 285` | Basis rows read again; a digest of ticket events; the record API | Staleness at clearance | DF | |
| 19 | `owm_register/registrar.py:103-109`; `owm_service/register_queue.py:155` | `Staff.load`: the HR file | The registrar's people rules | DF | |
| 20 | `owm_register/registrar.py:252-268` | Customers and CRM accounts | The registrar's customer check | DF | |
| 21 | `owm_register/build_procedures.py:41` | The HR file | The procedure registrar | DF | |
| 22 | `owm_register/registrar.py:131-143`; `owm_kernel/kernel.py:640-648` | The bootstrap's entries and approved texts, addressed by sha256; `Register.approved` reads the approved version | Decisions run on the registered version | OWM | |
| 23 | `owm_service/org.py:92-124`; `_lab.py:283-306` | The register replayed from the log; the register store's texts, by sha256 | The register's state | OWM | |
| 24 | `owm_register/registrar.py:390-414`; `owm_service/register_queue.py:252-253, 538` | A change's text: parsed, fingerprinted (RR-5), its window (RR-7) and terms (RR-6) checked | Registering a document | OWM | The text arrives in the request. Optional: the change names a foundation version and the OWM reads K7 itself (§13.2 has BlueLeaf send the text) |
| 25 | `owm_service/register_view.py:110-119, 248-255` | A title taken from the approved text's heading; the approved text, served | The register view | OWM | |
| 26 | `owm_register/serve.py:126-160` | The register as served to an agent, with its approved texts | Agent prompts | OWM | |
| 27 | `owm_kernel/governed.py:56-68`; `owm_service/org.py:127-171` | Procedure texts from the procedure store; the spec file on disk checked against them | Which procedure runs | OWM | |
| 28 | `owm_service/clearance.py:310-327` | Basis documents checked against the register (and nothing else) | Staleness | OWM | Copies on file are never checked again (gap 5) |
| 29 | `owm_service/sessions.py:97`; `register_view.py:159-170` | The mandate fixture | Agent mandates | OWM | |
| 30 | `owm_service/_lab.py:63-104` | Recorded Jev exchanges under `runs/` | Replaying the engine | OWM | Not evidence |
| 31 | `owm_register/build_register.py:236-240` | The corpus files, read to build the bootstrap | A one-time import | OWM | A lab tool that also reads the lab's ground truth, so it is not a prototype runtime read |

**Counts:** as-is 5, adapter 7, v0.3 0, DF 9, OWM 10. The older Python specs
(`owm_kernel/discount.py:114-116`, `credit.py:130-148`, `sla.py:205-363`) make the same two reads as
rows 7 and 13. The service doesn't load them (`_lab.py:43-49`), so they aren't counted.

## 4. Formats

| Corpus | `.md` documents | `.csv` record exports (DF) |
|---|---|---|
| base (`dataset/evidence`) | 25 | 13 |
| variant 1 | 22 | 13 |
| variant 2 | 24 | 13 |

All 25 base documents:
- have YAML front matter;
- are UTF-8, NFC and LF, with no byte-order mark and no duplicate bytes;
- differ from their canonical text only by the final newline (checked one by one), so the kernel's
  `body` (`kernel.py:81`, which strips it) is identical either way.

12 of the 25 contain pipe tables.

What B-20 reads:
- **Text formats, read as the file itself** (`canonical.py:16-42`): Markdown, plain text, CSV, TSV,
  JSON, YAML and email.
- **HTML**, through Docling as a reading-order layout rendering (`layout.py:29`).
- **PDF, Word, PowerPoint and Excel** are received and kept, but not read: their `state` is `failed`
  and K7 answers `no_text` (`ingest.py:73-87`; `app.py:49`). That's F2b, "later".

**So the current corpus is covered completely.** A layout format would reach the kernel without front
matter or Markdown syntax, which is a kernel-side gap as much as B-20's (gap 7).

## 5. EvidenceProvider sketch

```
kernel (unchanged) ── docs() ──▶ FoundationEvidence ── EvidenceProvider ──▶ Knowledge Foundation (K0,K1,K2,K4,K5,K7,K9)
                    └─ table() ─▶   (facade)        └─ RecordReadProvider ─▶ Data Foundation (stub in v1)
```

```python
@dataclass(frozen=True)
class VersionRef:                 # one immutable version of one document
    source_id: str                # the foundation's document id
    version: int
    filename: str
    media_type: str
    text_sha256: str | None       # the register's fingerprint of its text; None: no text

@dataclass(frozen=True)
class Unread:                     # held by the foundation, but no text to give
    source_id: str
    filename: str
    state: str
    problem: str | None

@dataclass(frozen=True)
class Snapshot:                   # one corpus at one read: everything a decision sees
    corpus: str
    read_at: str
    documents: tuple[VersionRef, ...]    # current versions with text, sorted by filename
    unread: tuple[Unread, ...]           # non-empty: an absence proves nothing

class EvidenceProvider(Protocol):
    def snapshot(self, corpus: str, *, media_types: frozenset[str]) -> Snapshot: ...
    #   K1 (corpus to base), every page of K2; text_sha256 from K5 or K7's ETag
    def text(self, ref: VersionRef) -> str: ...
    #   K7; checked against ref.text_sha256; cacheable for good
    def find_text(self, corpus: str, text_sha256: str) -> list[VersionRef]: ...
    #   K9, keeping only current versions of documents not deleted; the copy on file
    def current(self, source_id: str) -> VersionRef | None: ...
    #   K4 + K5; None when deleted; for staleness checks
```

- **The facade.** `FoundationEvidence(snapshot, provider, records)` keeps the kernel's own interface
  (`kernel.py:84-97`):
  - `docs()` returns `parse_doc(ref.filename, provider.text(ref))` for each document in the
    snapshot;
  - `table()` hands over to `RecordReadProvider`.

  The facade also keeps a map from (file name, stated id) to `VersionRef`, which rows 9–12 need.
- **No change to the kernel.** Parsing stays in the kernel, and the port has no decision-type
  vocabulary in it.
- **Failure.** A transport, auth or 5xx error raises `EvidenceUnavailable`. The service turns it into
  `CannotDecide`, as it already does with kernel failures (`_lab.py:375-378`).
- **Reserved for later:** `snapshot(..., known_at=)` (gap 11) and a `changes(since)` feed (gap 5).

## 6. Gaps and open questions

1. **Unreadable documents.** K2 lists documents that are still processing or have failed, and K7
   answers 404 for them. The kernel has never met one, and it treats a missing document as meaning
   something (v0.2 principle 9 says the same). Proposal: fail closed (`CannotDecide`) whenever
   `unread` isn't empty. Decide this in the spec.
2. **One snapshot per decision.** The service reads the corpus twice per decision (`flow.py:410`,
   `prepare.py:230`) and again on every register view (`register_view.py:230`). A live foundation
   could show different sets to those reads. Fix: one K2 read per decision, with texts cached by
   (doc_id, version).
3. **Record exports in the same base.** `load-lab` loads `structured/*.csv` into the base alongside
   the documents (`cli.py:48-61`). The OWM must read records only through `RecordReadProvider`, and
   the two copies can drift apart, since only the DF side carries the overlay of edits (`sor.py`).
   Either give the OWM a base that holds documents only, or have the adapter filter by media type.
   K2 has no media-type filter, so the filtering happens on the client.
4. **Basis provenance.** A basis document records only its stated id and sha256
   (`owm-decisions.ts:428`). Proposal: also record the foundation's (doc_id, version). That's a
   candidate for an OWM contract amendment, not for the KF.
5. **Staleness of unregistered basis documents.** Clearance checks only the register
   (`clearance.py:310-327`). Static files made that safe, but under a live foundation a new version
   of an unregistered document that a decision relied on goes unnoticed. Two options:
   - poll K4 or K5 at clearance (an adapter over v0.2);
   - read K20, which v0.2 defines but B-20 doesn't serve (`app.py:27-44`): a B-20 build item, not an
     amendment.

   Decide whether clearance should check this at all.
6. **K9's scope.** K9 returns superseded versions and versions of deleted documents
   (`app.py:307-323`), so the adapter checks for a current version and a live document. That's
   allowed by the contract's "every version". Ask B-20 whether it's intended.
7. **Formats beyond Markdown.** The kernel reads front matter and Markdown structure, so a layout
   rendering (HTML now, PDF and Word after F2b) loses its stated id, owner and window, and the
   pattern reads miss. Before any non-Markdown evidence arrives, choose one:
   - (a) the register supplies the metadata for governing documents (it already holds kind and
     window);
   - (b) a v0.3 adds a document's stated properties as a generic read shape: stated id, issuer,
     effective window and status, each with an evidence span.
8. **Duplicate bytes.** K3 skips a file whose bytes are already in the base (`ingest.py:56-62`), but
   today the kernel would see both copies. The corpus has no duplicates. Check the held-out org (F2).
9. **Byte-order mark.** B-20 strips a UTF-8 BOM (`canonical.py:65-70`); the kernel's fingerprint
   doesn't (`kernel.py:625`). Every current file hashes the same either way, but a register text
   submitted with a BOM would never match. Make the kernel's fingerprint strip it too, or have the
   registrar strip it.
10. **Engine replay.** Recorded Jev requests are hashed over the state (`_lab.py:91`). K7 differs
    from the files only by the final newline, and `body` strips it, so the hashes should still match.
    Prove it with an offline test before switching: decide every recorded case over a snapshot
    served by B-20, and diff the records.
11. **Which base, and as known when.**
    - BlueLeaf's base carries demo revisions, version 2 of some documents (`load-lab --revisions`).
      A parity run needs one base per corpus, loaded at a lab commit without revisions.
    - The reserved `as_known_at` (G-38) has no document-side `known_at` in v0.2: K13 has one, but K2
      and K5 don't. The adapter can rebuild it from `created_at`, `deleted_at`, `received_at` and
      `superseded_at`, except across a delete followed by a restore, because a restore clears
      `deleted_at` (`app.py:255-264`). That's a v0.3 candidate, and only if the feature is wanted.
12. **Spans and extracted facts.**
    - Today the kernel cites no words. To cite them, the OWM can compute UTF-8 spans over K7's text
      itself, with no amendment needed.
    - The kernel reads none of the facts B-20 extracts (K13–K17). Open: should a prototype decision
      ever rest on them? I'd advise not, because the guards are deterministic.
