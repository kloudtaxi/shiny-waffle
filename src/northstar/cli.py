"""``northstar build`` / ``northstar check``."""

from __future__ import annotations

import argparse
from pathlib import Path

from northstar.build import assemble, build
from northstar.factories import SCALES

LAB_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED = 20260923  # the as-of date of Scenario 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="northstar", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("build", "generate the dataset"),
        ("check", "verify truth coherence without writing anything"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--seed", type=int, default=DEFAULT_SEED)
        p.add_argument("--scale", choices=sorted(SCALES), default="small")
        p.add_argument("--truth", type=Path, default=LAB_ROOT / "truth")
        if name == "build":
            p.add_argument("--out", type=Path, default=LAB_ROOT / "dataset")
    args = parser.parse_args(argv)

    if args.command == "check":
        ds = assemble(args.truth, args.seed, args.scale)
    else:
        ds = build(args.truth, args.out, args.seed, args.scale)
    for sid, result in ds.results.items():
        outcome = result.get("decision", {}).get("outcome", result["type"])
        print(f"{sid}  {outcome}")
    print(f"{len(ds.artifacts)} artifacts · {len(ds.truth.scenarios)} scenarios coherent")
    return 0
