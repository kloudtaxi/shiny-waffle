"""Print one reader answer's final text (for G-16's hand reads).

uv run python runs/2026-10-06-rubric-agreement/show.py runs/<...>.jsonl
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
s = importlib.util.spec_from_file_location("detect", HERE / "detect.py")
assert s and s.loader
detect = importlib.util.module_from_spec(s)
s.loader.exec_module(detect)

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(f"===== {arg}\n{detect.result(HERE.parents[1] / arg)}\n")
