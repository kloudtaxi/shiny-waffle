"""The fingerprint check: what this run will use, against the baseline record."""

from __future__ import annotations

from preflight.baseline import Baseline, baseline_values, compared_groups
from preflight.record import CheckResult, Value


def check_fingerprint(values: list[Value], baseline: Baseline | None) -> CheckResult:
    """Any compared field that differs fails; `ok is False` marks the drift."""
    groups = compared_groups(baseline)
    then = baseline_values(baseline.record) if baseline is not None else {}
    out: list[Value] = []
    compared = 0
    for v in values:
        if v.compare == "true":
            out.append(v.model_copy(update={"ok": v.value is True}))
        elif v.compare == "equal" and v.group in groups and baseline is not None:
            compared += 1
            old = then.get(v.field)
            ok = v.state != "unread" and old is not None and old.value == v.value
            out.append(
                v.model_copy(update={"baseline": None if old is None else old.value, "ok": ok})
            )
        else:
            out.append(v.model_copy(update={"ok": None}))
    now = {v.field for v in values}
    for field, old in then.items():
        if old.compare == "equal" and old.group in groups and field not in now:
            compared += 1
            out.append(
                old.model_copy(
                    update={"state": "unread", "value": None, "baseline": old.value, "ok": False}
                )
            )
    drift = sum(1 for v in out if v.ok is False)
    status = "fail" if drift else "pass"
    if baseline is None:
        summary = "baseline set by this record" if not drift else "lab code tree is not clean"
    elif drift:
        summary = f"{drift} of {compared} compared fields differ from the baseline"
    else:
        summary = "every compared field matches the baseline"
    return CheckResult(name="fingerprint", status=status, summary=summary, values=out)
