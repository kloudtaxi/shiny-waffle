"""Post-hoc probe (exploratory, lab-authored, after the labels were unsealed): would the control
the user named have fired, once the problem that a different rule caught first is fixed?

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-08-register-attacks/probe_posthoc.py

Each variant copies one of the user's cases and makes the smallest edit that removes the earlier
refusal, keeping the case's intent. The edits are listed in EDITS and written next to the
results. Nothing here changes the blind results (`results.json`), the scored M1-M3, or the
frozen registrar. The variants run through the same `run_attacks.run`, into `posthoc/`.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
CASES = HERE / "sealed/cases"
OUT = HERE / "posthoc"
SALES = {"acting_as": ["EMP-101", "EMP-200"], "submit_by": "EMP-101", "approve_by": "EMP-200"}
P26 = (LAB / "dataset/evidence/documents/pricing_policy_2026.md").read_text().split("---", 2)[2]
BANDS_26 = next(
    e["terms"]
    for e in yaml.safe_load((LAB / "lab/owm_register/base.yaml").read_text())["entries"]
    if e["doc_id"] == "PRICING-POLICY-2026"
)


def front(doc_id: str, frm: str | None, to: str | None) -> str:
    lines = [
        "---",
        f"doc_id: {doc_id}",
        f"title: {doc_id}",
        "owner: Sales",
        "created: '2026-09-01'",
    ]
    lines += [f"effective_from: '{frm}'"] if frm else []
    lines += [f"effective_to: '{to}'"] if to else []
    return "\n".join([*lines, "---"])


def policy_text(doc_id: str, frm: str | None, to: str | None) -> str:
    """The 2026 policy's body (its bands bind to BANDS_26) under new front matter."""
    return front(doc_id, frm, to) + P26


# case -> (what was edited, function(case, text) -> (case, text))
EDITS: dict[str, tuple[str, Any]] = {
    "C01": ("actors: Sales (EMP-101 submits, EMP-200 approves)", "sales"),
    "C21": ("actors: Sales (EMP-101 submits, EMP-200 approves)", "sales"),
    "C04": ("relation: supersedes HR-HOLIDAYS-2025-26", ("supersedes", "HR-HOLIDAYS-2025-26")),
    "C05": ("relation: supersedes SUP-SEVERITY-GUIDE", ("supersedes", "SUP-SEVERITY-GUIDE")),
    "C06": ("relation: supersedes SOP-SUPPORT-007", ("supersedes", "SOP-SUPPORT-007")),
    "C07": ("relation: supersedes SUP-ACME-C", ("supersedes", "SUP-ACME-C")),
    "C08": ("text: 'grants no' -> 'does not grant' approval authority", "nogrant"),
    "C17": ("terms and text: the 2026 policy's bands and body", "policy"),
    "C18": ("terms and text: the 2026 policy's bands and body", "policy"),
    "C19": ("terms and text: the 2026 policy's bands and body", "policy"),
    "C23": ("terms and text: the 2026 policy's bands and body; front matter without "
            "effective_from, so the window's start isn't in the text", "policy-nofrom"),
}  # fmt: skip


def variant(cid: str, how: Any, dst: Path) -> None:
    case = yaml.safe_load((CASES / f"{cid}.yaml").read_text())
    ch = case["changes"][0]
    text = (CASES / ch["text"]).read_text() if ch.get("text") else None
    if how == "sales":
        case["acting_as"] = SALES["acting_as"]
        ch["submit_by"], ch["approve_by"] = SALES["submit_by"], SALES["approve_by"]
    elif isinstance(how, tuple):
        ch["relations"] = [{"type": how[0], "target": how[1]}]
    elif how == "nogrant":
        assert text and "grants no approval authority" in text
        text = text.replace("grants no approval authority", "does not grant approval authority")
    elif how in ("policy", "policy-nofrom"):
        frm = None if how == "policy-nofrom" else ch["effective_from"]
        text = policy_text(ch["doc_id"], frm, ch["effective_to"])
        ch["terms"] = BANDS_26
    case["case"] = f"{cid}x"
    if text is not None:
        ch["text"] = f"{cid}x/{Path(ch['text']).name}"
        (dst / f"{cid}x").mkdir(exist_ok=True)
        (dst / ch["text"]).write_text(text)
    (dst / f"{cid}x.yaml").write_text(yaml.safe_dump(case, sort_keys=False))


def main() -> None:
    s = importlib.util.spec_from_file_location("run_attacks", HERE / "run_attacks.py")
    assert s and s.loader
    ra = importlib.util.module_from_spec(s)
    s.loader.exec_module(ra)
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ns-posthoc-") as tmp:
        dst = Path(tmp)
        for cid, (_, how) in EDITS.items():
            variant(cid, how, dst)
        ra.run(dst, OUT)
        md = (OUT / "results.md").read_text().split("\n", 1)[1]  # the runner's title says blind
        (OUT / "results.md").write_text("# Post-hoc variants (exploratory; after unsealing)\n" + md)
        for p in sorted(dst.rglob("*")):  # keep the variants with their results
            if p.is_file():
                q = OUT / "cases" / p.relative_to(dst)
                q.parent.mkdir(parents=True, exist_ok=True)
                q.write_text(p.read_text())
    (OUT / "edits.json").write_text(
        json.dumps({f"{k}x": v[0] for k, v in EDITS.items()}, indent=1) + "\n"
    )


if __name__ == "__main__":
    sys.exit(main())
