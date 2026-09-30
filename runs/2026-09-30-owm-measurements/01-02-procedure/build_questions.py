"""Build the reader input for items 1 + 2: S01–S05, S09–S14 and S15–S20, each with its CRM record.

    uv run python runs/2026-09-30-owm-measurements/01-02-procedure/build_questions.py

S01–S05 and S09–S14 are copied **verbatim** from the files their earlier runs used, so the only
change between those runs and these is how the procedure reaches the reader. S15–S20 are built by
the same `record()` that built S09–S14 (the scale run's `heldout/heldout.py`).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
SCALE = LAB / "runs/2026-09-28-utopia-aad5b06-scale-large"
KB = {
    "base": "01a0ea56-61e7-79e3-99d1-e82b5d6af79a",
    "missing-contract-evidence": "01a0ea56-65d0-73d2-940d-6f1f9da0d800",
}
FRESH = ("S15", "S16", "S17", "S18", "S19", "S20")


def rows(path: Path) -> list[str]:
    return [r for r in path.read_text().splitlines()[1:] if r.strip()]


def main() -> None:
    spec = importlib.util.spec_from_file_location("heldout", SCALE / "heldout/heldout.py")
    assert spec and spec.loader
    heldout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(heldout)
    from northstar.model import load_truth

    truth = load_truth(LAB / "truth")
    out = ["id\tkb\tquestion"]
    out += rows(SCALE / "request/questions.tsv")  # S01–S05, verbatim
    out += rows(SCALE / "heldout/questions.tsv")  # S09–S14, verbatim
    for sid in FRESH:
        s = next(x for x in truth.scenarios if x.id == sid)
        text = (
            f"{s.question} The request, as recorded in Northstar CRM: "
            f"{json.dumps(heldout.record(sid), ensure_ascii=False)}"
        )
        out.append(f"{sid}\t{KB[s.corpus]}\t{text}")
    (HERE / "questions.tsv").write_text("\n".join(out) + "\n")
    print(f"{len(out) - 1} questions")


if __name__ == "__main__":
    main()
