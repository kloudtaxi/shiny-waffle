"""One-time migration: `docs/gap-tracker.md` (as of `7678903`) into the ledger's `gaps` collection.

    python3 tracker/seed_gaps.py

Writes `seed/gaps.json` and one file per gap under `seed/docs/gaps/`. Claude then writes them into
the artifact's database with an `ArtifactData` batch. After that the ledger is the source of truth:
status changes, updates and decisions are made on the page (or by Claude with `ArtifactData`
`update`, pinned to the version it read). **Never re-run this over a live ledger:** it would
overwrite the user's changes.

Each gap document holds:
- `order`, `id`, `title`, `area`, `owner`, `priority`;
- `status` (open, pending decision, partial, finding, decided, closed) and `status_note`;
- `body` (the detail section as markdown);
- `decisions` (G-01 only);
- `log` ([{at, by, text}]) and `updated_at`.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = "7678903:docs/gap-tracker.md"  # the tracker as written; the file is now a pointer
OUT = HERE / "seed"
CREATED = "2026-10-05T00:00:00Z"

STATUS = [  # (prefix in the summary table, status)
    ("open", "open"), ("decision pending", "pending decision"), ("partial", "partial"),
    ("closed", "closed"), ("decided", "decided"), ("finding", "finding"),
]  # fmt: skip

DECISIONS = [
    {
        "key": "where",
        "question": "Where does the register live in the product?",
        "needed_by": "Before the BlueLeaf product spec or amendment is written. Not needed for the "
        "lab build, which models the register as a trusted input either way.",
        "options": [
            {"key": "A", "label": "In the OWM", "text": "BlueLeaf keeps its own governed store of "
             "registered documents: the thing decisions trust sits with the engine that decides. "
             "The knowledge foundation keeps documents for search and retrieval. It fits the rule "
             "that the OWM must not depend on the foundation, and procedure objects (G-13) can be "
             "registered in the same place. Cost: BlueLeaf owns a registration workflow."},
            {"key": "B", "label": "In the knowledge foundation", "text": "Utopia, or whatever "
             "document system feeds it, stores versions and hashes; the OWM asks it. One place for "
             "documents. Cost: the decision's safety would rest on a replaceable component, one "
             "whose own governance made 161 false merges (J4)."},
            {"key": "C", "label": "In the customer's systems of record", "text": "E-signature, "
             "contract-lifecycle and policy-management tools, read through an adapter the way the "
             "CRM and ERP exports are read today. It uses where executed documents already live. "
             "Cost: coverage varies by customer, many policies have no such system, and each "
             "vendor needs an adapter."},
        ],
        "recommended": "A",
        "recommendation": "A, fed by C where it exists: the OWM holds the register, and imports "
        "registrations from a customer's e-signature or contract system when there is one. Not B.",
        "choice": None,
    },
    {
        "key": "who",
        "question": "Who may register a governing document?",
        "needed_by": "Before the product spec. The lab build models the recommended option "
        "(registered by the owning function, approved by a second person).",
        "options": [
            {"key": "A", "label": "The owning function, plus a second approver", "text": "Finance "
             "registers policies, Legal registers guarantees: the owners the guards already check. "
             "A second person in that function approves (two-person rule). The requestor of any "
             "decision that relies on the document can never register or approve it (separation "
             "of duties, as for approvals)."},
            {"key": "B", "label": "A central registrar", "text": "Legal operations or Compliance "
             "registers everything after checking where it came from. One point of control and "
             "audit. Cost: a bottleneck, and the registrar may not understand the content."},
            {"key": "C", "label": "Automatically, from trusted executions", "text": "A document "
             "registers itself when the e-signature or contract system reports it executed; people "
             "register only what has no such source. Fast. Cost: it inherits the upstream "
             "system's controls, good or bad."},
        ],
        "recommended": "A",
        "recommendation": "A, with C as the fast path where a trusted execution source exists. "
        "Agents may propose a registration (agents-first) but never approve one. B only where a "
        "customer already runs a registrar function.",
        "choice": None,
    },
    {
        "key": "terms",
        "question": "Do registered documents also carry structured terms?",
        "needed_by": "Decided.",
        "options": [
            {"key": "yes", "label": "Yes", "text": "Amount, the party by registered id, the term "
             "and relations are stored with the registered version. Engines read the terms, not "
             "the prose (closes most of G-08)."},
            {"key": "no", "label": "No", "text": "Engines keep reading terms from the text."},
        ],
        "recommended": "yes",
        "recommendation": "Yes.",
        "choice": "yes",
    },
]  # fmt: skip


def status_of(cell: str) -> tuple[str, str]:
    plain = re.sub(r"[*`]", "", cell).strip()
    for prefix, status in STATUS:
        if plain.lower().startswith(prefix):
            note = plain[len(prefix) :].strip(" :")
            if note.startswith("(") and note.endswith(")"):
                note = note[1:-1]
            return status, note
    raise ValueError(f"unknown status: {cell!r}")


def main() -> None:
    text = subprocess.run(["git", "show", SRC], cwd=HERE, check=True, capture_output=True,
                          text=True).stdout  # fmt: skip
    rows = re.findall(r"^\| (G-\d\d) \| (.+?) \| (.+?) \| (.+?) \| (P\d) \| (.+?) \|$", text, re.M)
    sections = dict(
        re.findall(r"^### (G-\d\d): .+?\n\n(.*?)(?=\n### |\n## |\Z)", text, re.M | re.S)
    )
    docs = {}
    for order, (gid, title, area, owner, prio, cell) in enumerate(rows, start=1):
        status, note = status_of(cell)
        body = sections[gid].strip()
        doc = {"order": order, "id": gid, "title": re.sub(r"\*\*", "", title).strip(),
               "area": area.strip(), "owner": owner.strip(), "priority": prio, "status": status,
               "status_note": note, "body": body, "updated_at": CREATED,
               "log": [{"at": CREATED, "by": "Claude",
                        "text": "Created from docs/gap-tracker.md (7678903)."}]}  # fmt: skip
        if gid == "G-01":
            doc["body"] = re.sub(
                r"\n- \*\*Open questions for the user:\*\*.*\Z", "", body, flags=re.S
            )
            doc["decisions"] = DECISIONS
            decided = "Decided: registered documents carry structured terms (amount, party, term)."
            doc["log"].append({"at": CREATED, "by": "you", "text": decided})
        if gid == "G-08":
            decided = "Direction decided under G-01: registered documents carry structured terms."
            doc["log"].append({"at": CREATED, "by": "you", "text": decided})
        docs[gid] = doc
    assert len(docs) == 29, len(docs)
    (OUT / "gaps.json").write_text(json.dumps(docs, ensure_ascii=False, indent=1) + "\n")
    (OUT / "docs/gaps").mkdir(parents=True, exist_ok=True)
    for gid, doc in docs.items():
        (OUT / "docs/gaps" / f"{gid}.json").write_text(json.dumps(doc, ensure_ascii=False) + "\n")
    print(f"{len(docs)} gaps; statuses:", {d["status"] for d in docs.values()})


if __name__ == "__main__":
    main()
