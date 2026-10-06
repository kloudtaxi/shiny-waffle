"""Exploratory, NOT pre-registered (`notes.md`): the mirror of gate C. For each clean SLA scenario,
remove each governing document the decision did NOT rely on (from the corpus and the register), and
see whether the decision changes. A change means the document fed the decision unwatched.

    uv run python runs/2026-10-06-spec-admission/explore_unrelied.py SPEC
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
s = importlib.util.spec_from_file_location("admit", LAB / "lab/spec_admission/admit.py")
assert s and s.loader
admit = importlib.util.module_from_spec(s)
sys.modules["admit"] = admit
s.loader.exec_module(admit)


def main() -> None:
    path = Path(sys.argv[1]).resolve()
    gate = admit.Gate(admit.Layered(HERE / "jev-calls.jsonl", live=False, cap=0))
    spec, _ = gate.deployed(path, "sla")
    reg = admit.ra.REG["base"]
    governing = {e["doc_id"]: e["file"] for e in reg.entries
                 if e["kind"] in set(admit.ra.SLA.values())}  # fmt: skip
    found = []
    with tempfile.TemporaryDirectory(prefix="ns-unrelied-") as tmp:
        root = gate.clean_roots(Path(tmp) / "clean")["base"]
        for sid in gate.scenarios("sla"):
            trace: dict[str, object] = {}
            d0 = gate.decide(spec, "sla", sid, root, reg, trace)
            relied = {doc_id for _, doc_id in trace.get("relied", [])}  # type: ignore[union-attr]
            for doc_id, filename in governing.items():
                if doc_id in relied:
                    continue
                ab = Path(tmp) / f"{sid}-{doc_id}"
                shutil.copytree(root, ab)
                (ab / "documents" / filename).unlink(missing_ok=True)
                r = admit.Register([e for e in reg.entries if e["doc_id"] != doc_id], reg.store)
                d = gate.decide(spec, "sla", sid, ab, r)
                if "not recorded" in str(d.get("error", "")):
                    found.append(f"{sid} {doc_id}: unknown (Jev)")
                elif gate.ckey("sla", d) != gate.ckey("sla", d0):
                    found.append(f"{sid} {doc_id}: decision changed, but it wasn't relied on")
                shutil.rmtree(ab, ignore_errors=True)
    print(f"{path.name}: " + ("; ".join(found) or "every unrelied governing document is idle"))


if __name__ == "__main__":
    main()
