"""Build the exam's 47 questions (pre-registration §4), one TSV row each: id, corpus, process,
question.

    uv run python lab/exam/questions.py runs/<exam run>/questions.tsv

- **Discount, S01–S25:** the texts earlier runs asked, byte for byte. S01–S05 and S09–S20 with their
  request records (`01-02-procedure`), S06a–c, S07 and S08 as the luna baseline asked them, S22–S25
  as submitted (`j3`). S21 has no earlier text: it's built the way `01-02-procedure` built S15–S20,
  by the same `record()`.
- **Credit, S26–S35:** experiment 5's message (the question and the request record), less the gold
  evidence that run appended.
- **SLA, S36–S45:** experiment 6's message, the question, less the gold evidence.

No question carries a knowledge base: the corpus column says which of the arm's three bases answers.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

LAB = Path(__file__).resolve().parents[2]
RUNS = LAB / "runs"
PROCEDURE = RUNS / "2026-09-30-owm-measurements/01-02-procedure/questions.tsv"
BASELINE = RUNS / "2026-09-28-utopia-aad5b06/questions.tsv"
SUBMITTED = RUNS / "2026-10-02-jev-probe/j3/questions.tsv"
HELDOUT = RUNS / "2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
EXP5 = RUNS / "2026-10-03-exp5-credit/run_reader.py"
GOLD = "\n\nThe organization's documents and records:"

PROCEDURES = {
    "discount": "owm/procedures/discount-approval.md",
    "credit": "owm/procedures/credit-limit.md",
    "sla": "owm/procedures/sla-response.md",
}


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _texts(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines()[1:]:
        if line.strip():
            sid, _kb, question = line.split("\t", 2)
            out[sid] = question
    return out


def process(sid: str) -> str:
    n = int(sid[1:3])
    return "discount" if n <= 25 else "credit" if n <= 35 else "sla"


def build() -> list[tuple[str, str, str, str]]:
    sys.path.insert(0, str(LAB / "src"))
    from northstar.model import load_truth

    truth = load_truth(LAB / "truth")
    corpus = {s.id: s.corpus for s in truth.scenarios}
    text: dict[str, str] = {}
    procedure, baseline, submitted = _texts(PROCEDURE), _texts(BASELINE), _texts(SUBMITTED)
    for sid in ["S01", "S02", "S03", "S04", "S05", *(f"S{n:02d}" for n in range(9, 21))]:
        text[sid] = procedure[sid]
    for sid in ("S06a", "S06b", "S06c", "S07", "S08"):
        text[sid] = baseline[sid]
    for sid in ("S22", "S23", "S24", "S25"):
        text[sid] = submitted[sid]
    heldout = _module("exam_heldout", HELDOUT)
    s21 = next(s for s in truth.scenarios if s.id == "S21")
    text["S21"] = (
        f"{s21.question} The request, as recorded in Northstar CRM: "
        f"{json.dumps(heldout.record('S21'), ensure_ascii=False)}"
    )
    exp5 = _module("exam_exp5", EXP5)
    for n in range(26, 36):
        sid = f"S{n}"
        full: str = exp5.prompt(truth, sid)
        assert GOLD in full, sid
        text[sid] = full.split(GOLD, 1)[0]
    for n in range(36, 46):
        sid = f"S{n}"
        text[sid] = next(s for s in truth.scenarios if s.id == sid).question

    def order(sid: str) -> tuple[int, str]:
        return int(sid[1:3]), sid

    rows = []
    for sid in sorted(text, key=order):
        rows.append((sid, corpus[sid[:3]], process(sid), text[sid]))
    return rows


def main() -> None:
    out = Path(sys.argv[1])
    rows = build()
    assert len(rows) == 47, len(rows)
    for sid, _, _, q in rows:
        assert "\t" not in q and "\n" not in q, sid
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("id\tcorpus\tprocess\tquestion\n" + "".join("\t".join(r) + "\n" for r in rows))
    print(f"{len(rows)} questions -> {out}")


if __name__ == "__main__":
    main()
