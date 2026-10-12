"""Procedures (spec §7.3; contract §4.5): a procedure version as a register change, and the
procedure reads (#18, in v1.1's shape).

A procedure is a spec the kernel runs as a decision, used only in a registered, admitted version.
A new version is a register change of kind `procedure` (`changes.py`) through the register queue's
two steps. `check` is its rules, in the registrar's order:

1. RR-5: a decision type with an owner (`KIND_OF`: discount, credit, sla), and a `proc_id` of
   the form `PROC-` then capitals, digits and hyphens (it names the version's file);
2. the people rules (`registrar.people`, RR-1 to RR-4), the owner taken from the decision type as
   the representative kind of its owning function: discount `pricing_policy` (Sales), credit
   `credit_policy` (Finance), sla `sla_schedule` (Customer Support);
3. RR-5: a text; a procedure that is the decision type's own (one procedure per decision type, so
   the governed runner's highest-version rule picks among one procedure's versions); the next
   version number, which is also a procedure's stale check, since a procedure approval never
   moves the register's version (ruling R50); RR-7: a window that doesn't end before it starts;
   RR-9: no backdating, an `effective_from` on or after the register's clock (the service
   clock's date; ruling R52), so a new version never changes what a past decision ran;
4. ADM: the lab's procedure registrar (`build_procedures.register`), given the change's report as
   a temp file, refuses no report, a report for another text, or a verdict that isn't admitted,
   in its own words. Then the service refuses a report admitted for another decision type
   (`report.type`), and a text that declares no `registered_kinds`: the gate admits such a spec
   with its standard mapping applied, which the lab registers as the version's deployment, and a
   change carries no deployment, so the version would run unlike admitted.

The queue runs `check` as a dry run at draft and submit, and for real at approval, where the
entry the registrar wrote is stored with the service's fields (`approved`). The service never runs
the admission gate. A version registered here is named `<proc_id>-v<n>.yaml`, unique per version.

**Known limit (ruling R55):** the admission report is self-attested JSON supplied with the change.
The service checks that it is for this exact text, for this decision type and admitted, but it
can't tell a report the gate wrote from one written by hand to look like it; only the two-person
rule (a person in the owning function submits, another person approves) stands behind it.
"""

from __future__ import annotations

import copy
import json
import re
import tempfile
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any, Final

import yaml

from . import _lab
from .changes import Change, version_name
from .errors import NotFound
from .org import Org
from .register_view import LABEL

KIND_OF: Final[Mapping[str, str]] = {
    "discount": "pricing_policy", "credit": "credit_policy", "sla": "sla_schedule",
}  # fmt: skip
PROC_ID: Final = re.compile(r"^PROC-[A-Z0-9-]+$")
_PERSON = re.compile(r"^(?P<name>.+) \((?P<id>EMP-\d+), (?P<title>.+)\)$")
_AGENT_AUTHOR = "proposed by an agent"  # how the procedure register's author text names one


def owner(decision_type: Any) -> str | None:
    """The function owning a decision type's procedure, or None for an unknown decision type."""
    kind = KIND_OF.get(decision_type) if isinstance(decision_type, str) else None
    return _lab.OWNER.get(kind) if kind else None


def file_name(proc_id: str, version: int) -> str:
    return f"{proc_id}-v{version}.yaml"


def _no(rule: str, message: str) -> _lab.RefusedError:
    return _lab.RefusedError(rule, message)


# -- the rules ----------------------------------------------------------------------------------
def check(
    entries: Sequence[Mapping[str, Any]], staff: _lab.Staff, fields: Mapping[str, Any],
    text: str | None, submit_by: str | None, approve_by: str | None, today: date,
) -> dict[str, Any]:  # fmt: skip
    """One procedure version through its rules (module docstring), against the procedure
    register's `entries`: the entry the lab's procedure registrar writes for it, with the
    service's fields still empty, or `RefusedError` (the registrar's own class)."""
    dt, pid, n = fields["decision_type"], str(fields["proc_id"]), fields["version"]
    kind = KIND_OF.get(dt) if isinstance(dt, str) else None
    if kind is None:
        raise _no("RR-5", f"no decision type {dt!r}: a procedure is for "
                          f"{', '.join(KIND_OF)} decisions")  # fmt: skip
    if not PROC_ID.fullmatch(pid):
        raise _no("RR-5", f"{pid!r} isn't a procedure id: PROC- then capital letters, digits and "
                          "hyphens")  # fmt: skip
    acting = {p for p in (submit_by, approve_by) if p is not None}
    submit, approve = _lab.people(kind, submit_by, approve_by, acting, staff)
    if not text:
        raise _no("RR-5", "no procedure text")
    mine = [e for e in entries if e["proc_id"] == pid]
    if mine and mine[0]["decision_type"] != dt:
        raise _no("RR-5", f"{pid} is a {mine[0]['decision_type']} procedure, not {dt}")
    other = next((e["proc_id"] for e in entries
                  if e["decision_type"] == dt and e["proc_id"] != pid), None)  # fmt: skip
    if other is not None:
        raise _no("RR-5", f"{dt} decisions follow {other}: register its next version, not a new "
                          f"procedure {pid}")  # fmt: skip
    latest = max((int(e["version"]) for e in mine), default=0)
    if any(e["version"] == n for e in mine):
        raise _no("RR-5", f"{version_name(pid, n)} is registered already; the next version is "
                          f"{latest + 1}")  # fmt: skip
    if n != latest + 1:
        raise _no("RR-5", f"{pid}'s next version is {latest + 1}, not {n}")
    start, end = fields["effective_from"], fields["effective_to"]
    if end is not None and date.fromisoformat(end) < date.fromisoformat(start):
        raise _no("RR-7", "the window ends before it starts")
    if date.fromisoformat(start) < today:  # ruling R52
        raise _no("RR-9", f"effective {start}, before the register's clock {today}")
    file = file_name(pid, n)
    report = fields.get("report")
    if report is None:
        raise _no("ADM", f"{file}: no admission report")
    version: dict[str, Any] = {
        "proc_id": pid, "decision_type": dt, "version": n, "file": file,
        "effective_from": start, "effective_to": end, "author": "", "admission": None,
        "deployment": None, "who": (staff.label(submit), staff.label(approve)),
        "on": today.isoformat(),
    }  # fmt: skip
    if n > 1:
        version["supersedes"] = version_name(pid, n - 1)
    with tempfile.TemporaryDirectory(prefix="owm-admission-") as tmp:
        path = Path(tmp) / "report.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        try:
            entry, _ = _lab.register_procedure(version, set(staff.rows), text, path)
        except _lab.ProcedureRefusedError as e:
            raise _no("ADM", str(e)) from e
        except (KeyError, TypeError, AttributeError) as e:
            raise _no("ADM", f"{file}: the admission report can't be read "
                             f"({type(e).__name__}: {e})") from e  # fmt: skip
    admitted_as = (report.get("report") or {}).get("type")
    if admitted_as != dt:
        raise _no("ADM", f"{file}: admitted as a {admitted_as} procedure, not {dt}")
    if not _declares_kinds(text):
        raise _no("ADM", f"{file}: declares no registered_kinds. The gate admitted it with its "
                         "standard mapping applied, which a version registered here doesn't "
                         "carry; declare registered_kinds in the text and have it admitted "
                         "again.")  # fmt: skip
    entry["admission"] = {**entry["admission"], "report": None, "detail": _details(report)}
    return entry | {"change": None, "proposed_by": None}


def _declares_kinds(text: str) -> bool:
    spec = yaml.safe_load(text)
    docs = spec.get("documents") if isinstance(spec, dict) else None
    return isinstance(docs, dict) and bool(docs.get("registered_kinds"))


def _details(report: Mapping[str, Any]) -> dict[str, str]:
    """Each gate's result in a few words, from the admission report."""
    r = report.get("report")
    gates = {g: r.get(g) for g in "ABC"} if isinstance(r, dict) else {}
    a, b, c = (g if isinstance(g, dict) else None for g in (gates.get(k) for k in "ABC"))
    out: dict[str, str] = {}
    if a:
        out["A"] = f"{a.get('held')} of {a.get('of')} held"
    if b:
        out["B"] = f"{b.get('attacks')} attacks, {len(b.get('unsafe_or_error') or [])} unsafe"
    if c:
        out["C"] = f"{c.get('relied')} relied on, {len(c.get('idle') or [])} idle"
    return out


def approved(entry: Mapping[str, Any], c: Change, on: date) -> dict[str, Any]:
    """The entry an approval stores (`procedure.approved`): the registrar's, with the change that
    registered it, who proposed it, its author, the day it was submitted (registered) and the
    day it was approved. The admission report on file is the change's."""
    out = copy.deepcopy(dict(entry))
    out |= {"change": c.change_id, "proposed_by": c.proposed_by, "author": _author_text(c),
            "registered_on": str(c.submitted_at)[:10], "approved_on": on.isoformat()}  # fmt: skip
    out["admission"] = {**out["admission"], "report": c.change_id}
    return out


def _author_text(c: Change) -> str:
    p = c.proposed_by
    if p is not None and p["kind"] == "agent":
        whom = p.get("on_behalf_of")
        return f"{_AGENT_AUTHOR} ({p['name']}, {p['id']})" + (
            f" for {whom['name']}" if whom else "")  # fmt: skip
    if p is not None:
        return f"drafted by {p['person']['name']} ({p['person']['id']})"
    s = c.submitted_by or {}
    return f"submitted by {s.get('name')} ({s.get('id')})"


def diff(
    fields: Mapping[str, Any], sha256: str | None, entries: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Against the version it supersedes, for the reviewer (G-33): the window and the text's
    fingerprint, where they differ."""
    pid, n = fields["proc_id"], fields["version"]
    was = next((e for e in entries if e["proc_id"] == pid and e["version"] == n - 1), None)
    if was is None:
        return []
    rows = [("effective_from", "Effective from", was["effective_from"], fields["effective_from"]),
            ("effective_to", "Effective to", was["effective_to"], fields["effective_to"]),
            ("sha256", "Text (sha256)", was["sha256"], sha256)]  # fmt: skip
    shown = [(k, label, _str(a), _str(b)) for k, label, a, b in rows]
    return [{"key": k, "label": label, "was": a, "now": b} for k, label, a, b in shown if a != b]


def _str(v: Any) -> str | None:
    return None if v is None else str(v)


# -- reads (#18) --------------------------------------------------------------------------------
def list_procedures(org: Org) -> list[dict[str, Any]]:
    """Every procedure, in the order the register first names it, as `get_procedure` reads it."""
    entries, _ = org.procedures()
    today = org.clock.today()
    ids = list(dict.fromkeys(str(e["proc_id"]) for e in entries))
    return [_procedure(pid, entries, today) for pid in ids]


def get_procedure(org: Org, proc_id: str) -> dict[str, Any]:
    """One procedure with its versions, in v1.1's #18 shape (`ProcedureEntry`): `proc_id` (and
    `id`, the same), `title`, `decision_type`, `owning_function`, `in_force` (the version a
    decision today runs) and `versions`, each with its `status` today, `sha256`, window, `author`
    (`{kind, name}`), `registered_by` and `approved_by` (`{id, name, title, on}`), `admission`
    (`{verdict, gates: {A, B, C: {passed, detail}}, report}`) and `change` (the change that
    registered it; null for the bootstrap's). v1.1's BlueLeaf fields (`kb_id`, `kb_name`,
    `steps`, `outcomes`, `principles`, `reads`, `decisions_7d`) and `admission.attempts` and `at`
    aren't the OWM's to give."""
    entries, _ = org.procedures()
    if not any(e["proc_id"] == proc_id for e in entries):
        raise NotFound(f"procedure {proc_id}")
    return _procedure(proc_id, entries, org.clock.today())


def _procedure(pid: str, entries: Sequence[Mapping[str, Any]], today: date) -> dict[str, Any]:
    versions = sorted((e for e in entries if e["proc_id"] == pid), key=lambda e: int(e["version"]))
    dt = str(versions[0]["decision_type"])
    current = _lab.procedure_in_force(entries, dt, today)
    mine = current if current is not None and current["proc_id"] == pid else None
    return {
        "id": pid, "proc_id": pid, "title": LABEL.get(dt, dt), "decision_type": dt,
        "owning_function": owner(dt), "in_force": None if mine is None else mine["version"],
        "versions": [_version(e, mine, today) for e in versions],
    }  # fmt: skip


def _status(e: Mapping[str, Any], current: Mapping[str, Any] | None, today: date) -> str:
    """`in_force` (what a decision today runs), `scheduled` (not started), `superseded` (a later
    version runs instead) or `expired` (its window ended and no later version runs)."""
    if current is not None and current["version"] == e["version"]:
        return "in_force"
    if date.fromisoformat(str(e["effective_from"])) > today:
        return "scheduled"
    if current is not None and current["version"] > e["version"]:
        return "superseded"
    return "expired"


def _version(
    e: Mapping[str, Any], current: Mapping[str, Any] | None, today: date
) -> dict[str, Any]:
    adm = e.get("admission") or {}
    gates, detail = adm.get("gates") or {}, adm.get("detail") or {}
    return {
        "version": e["version"], "status": _status(e, current, today), "sha256": e["sha256"],
        "effective_from": _str(e["effective_from"]), "effective_to": _str(e["effective_to"]),
        "author": _author(e),
        "registered_by": _signoff(e.get("registered_by"), e.get("registered_on")),
        "approved_by": _signoff(e.get("approved_by"), e.get("approved_on")),
        "admission": {"verdict": adm.get("verdict"),
                      "gates": {g: {"passed": bool(gates.get(g)), "detail": detail.get(g)}
                                for g in "ABC"},
                      "report": adm.get("report")},
        "change": e.get("change"),
    }  # fmt: skip


def _signoff(label: Any, on: Any) -> dict[str, Any] | None:
    """The procedure registrar's label for who acted ("Name (EMP-1, Title)"), with the day."""
    if not label:
        return None
    m = _PERSON.match(str(label))
    if m is None:
        return {"id": None, "name": str(label), "title": "", "on": _str(on)}
    return {"id": m["id"], "name": m["name"], "title": m["title"], "on": _str(on)}


def _author(e: Mapping[str, Any]) -> dict[str, str]:
    """A version registered here: who proposed it (an agent, or the person who drafted it), else
    its submitter. A bootstrap version: the procedure register's author text, an agent when it
    says it was proposed by one."""
    if e.get("change"):
        p = e.get("proposed_by")
        if p and p.get("kind") == "agent":
            return {"kind": "agent", "name": str(p["name"])}
        if p:
            return {"kind": "person", "name": str(p["person"]["name"])}
        signed = _signoff(e.get("registered_by"), e.get("registered_on")) or {}
        return {"kind": "person", "name": str(signed.get("name"))}
    text = str(e.get("author") or "")
    return {"kind": "agent" if text.startswith(_AGENT_AUTHOR) else "person", "name": text}
