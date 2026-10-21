"""The plain front end: `check`, `spend`; `tui` and `serve` arrive with the app (Task 12).

Exit codes: 0 pass or accepted, 1 fail, 2 a config error, an empty reason or a bad command line.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from preflight.config import ConfigError, load_config
from preflight.engine import Deps, repo_relative, run_preflight
from preflight.record import CheckResult
from preflight.spend import spend_view

MARK = {"pass": "✔", "fail": "✖", "n/a": "·"}
LABEL = {
    "inputs": "Inputs",
    "fingerprint": "Fingerprint",
    "settled": "Settled",
    "agent_context": "Agent context",
}
NO_APP = "the app isn't built yet"


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="preflight", description="Pre-flight checks for a lab run.")
    p.add_argument("--run", dest="bare_run", type=Path, help="run folder (no subcommand)")
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("check", help="run the checks and write a record")
    c.add_argument("--run", type=Path, required=True)
    c.add_argument("--accept-drift", metavar="REASON", help="accept fingerprint drift, with why")
    s = sub.add_parser("spend", help="print the run folder's spend")
    s.add_argument("--run", type=Path, required=True)
    t = sub.add_parser("tui", help="the operator app")
    t.add_argument("--run", type=Path, required=True)
    v = sub.add_parser("serve", help="the operator app in a browser tab")
    v.add_argument("--run", type=Path, required=True)
    v.add_argument("--port", type=int, default=8765)
    return p


def _config_error(exc: ConfigError) -> int:
    print(f"preflight.yaml: {str(exc).removeprefix('preflight.yaml: ')}", file=sys.stderr)
    return 2


def _print_check(c: CheckResult) -> None:
    print(f"{MARK[c.status]} {LABEL[c.name]:<14} {c.summary}")
    for problem in c.problems:
        print(f"    - {problem}")


def _check(run: Path, repo: Path, reason: str | None, deps: Deps | None) -> int:
    if reason is not None and not reason.split():
        print("a reason is required", file=sys.stderr)
        return 2
    try:
        cfg = load_config(run, repo)
        outcome = run_preflight(run, repo, cfg, accept_reason=reason, deps=deps)
    except ConfigError as exc:  # a broken config, or a baseline path naming no record (T7)
        return _config_error(exc)
    for c in outcome.record.checks:
        _print_check(c)
    print(f"record: {repo_relative(outcome.path, repo)}")
    print(f"status: {outcome.record.status}")
    if outcome.note:
        print(outcome.note)
    return 0 if outcome.record.status in ("pass", "accepted") else 1


def _app(run: Path, repo: Path, deps: Deps | None) -> int | None:
    """Run the Textual app on a terminal; None when it isn't installed (behave as `check`)."""
    try:
        from preflight.tui.app import run_app  # type: ignore[import-not-found, unused-ignore]
    except ImportError:
        return None
    try:
        cfg = load_config(run, repo)
    except ConfigError as exc:
        return _config_error(exc)
    return int(run_app(run, repo, cfg, deps))


def main(argv: list[str] | None = None, deps: Deps | None = None) -> int:
    parser = _parser()
    try:
        a = parser.parse_args(argv)
    except SystemExit as exc:  # --help, or a bad command line (argparse prints why)
        return exc.code if isinstance(exc.code, int) else 2
    repo = Path(__file__).resolve().parents[2]
    if a.cmd is None:
        if a.bare_run is None:
            parser.print_usage(sys.stderr)
            print("preflight: --run is required", file=sys.stderr)
            return 2
        if sys.stdout.isatty():
            code = _app(a.bare_run, repo, deps)
            if code is not None:
                return code
        return _check(a.bare_run, repo, None, deps)
    if a.cmd == "check":
        return _check(a.run, repo, a.accept_drift, deps)
    if a.cmd == "spend":
        if not a.run.is_dir():
            print(f"no run folder at {a.run}", file=sys.stderr)
            return 2
        print(spend_view(a.run))
        return 0
    print(NO_APP, file=sys.stderr)  # tui and serve: Task 12
    return 2
