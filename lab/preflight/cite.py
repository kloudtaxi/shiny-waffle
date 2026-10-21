"""What a paid runner says about the latest pre-flight record: it warns, it never blocks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from preflight.record import latest_record


def _fingerprint(values: dict[str, Any], field: str) -> Any:
    return values.get(field)


def cite_preflight(
    run: Path, *, questions_sha256: str | None, model: str, flags: str, est_usd: float
) -> dict[str, Any]:
    """The latest pass, fail or accepted record, compared with what this run is about to use."""
    found = latest_record(run, frozenset({"pass", "fail", "accepted"}))
    if found is None:
        return {
            "record": None,
            "status": "missing",
            "estimate_usd": est_usd,
            "warnings": ["no pre-flight record in preflight/"],
        }
    path, record = found
    values: dict[str, Any] = {}
    for check in record.checks:
        if check.name == "fingerprint":
            values = {v.field: v.value for v in check.values}
    warnings: list[str] = []
    if record.status == "fail":
        warnings.append("the latest pre-flight record failed")
    if _fingerprint(values, "inputs.questions_sha256") != questions_sha256:
        warnings.append("the pre-flight checked another questions file")
    if _fingerprint(values, "reader.model") != model:
        warnings.append("the pre-flight checked another model")
    if _fingerprint(values, "reader.flags") != flags:
        warnings.append("the pre-flight checked other flags")
    return {
        "record": str(path.relative_to(run)),
        "status": record.status,
        "estimate_usd": est_usd,
        "warnings": warnings,
    }
