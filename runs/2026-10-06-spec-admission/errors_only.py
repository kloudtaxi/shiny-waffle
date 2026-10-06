"""G-12's fix round (`plan.md`): what the runner rejects in the agent's SLA spec, and nothing else.

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-06-spec-admission/errors_only.py [SPEC]

Prints load errors, or each clean scenario's exception, in its deployed form (the register,
default mode). It never prints an outcome, a field or a score: this is all the author may see.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
spec_ = importlib.util.spec_from_file_location("admit", LAB / "lab/spec_admission/admit.py")
assert spec_ and spec_.loader
admit = importlib.util.module_from_spec(spec_)
sys.modules["admit"] = admit
spec_.loader.exec_module(admit)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else LAB / "lab/owm_kernel/specs/sla_agent.yaml"
    try:
        gate = admit.Gate(admit.Layered(HERE / "jev-calls.jsonl", live=True, cap=2000))
        spec, _ = gate.deployed(path, "sla")
    except Exception as e:  # noqa: BLE001
        print(f"load: {type(e).__name__}: {e}")
        return
    errors = []
    with tempfile.TemporaryDirectory(prefix="ns-g12-") as tmp:
        roots = gate.clean_roots(Path(tmp))
        for i, sid in enumerate(gate.scenarios("sla"), 1):
            d = gate.decide(spec, "sla", sid, roots["base"], admit.ra.REG["base"])
            if d.get("gated_outcome") == "ERROR":
                errors.append(f"case {i}: {d.get('error')}")
    print("\n".join(errors) or "no errors")


if __name__ == "__main__":
    main()
