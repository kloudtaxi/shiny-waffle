"""Specs as data: a generic runner for decision specs written as YAML procedure objects.

`runs/2026-10-04-specs-as-data/plan.md` describes it. A spec is data:
- `documents` (provenance settings), `readers`, `questions`, `steps`, `outcome`, `obligations` and
  `record`, which every decision fills in;
- `outcomes` and `route_to`, its outcome vocabulary.

Every value is an **expression** in a small, safe language that this module interprets from the
Python AST. Expressions are never `eval`ed; only whitelisted node types, functions and attributes
are allowed. Expressions can call:
- pure helpers (`min`, `latest`, `days`, `search`, …);
- the kernel's governed primitives (`covering`, `in_force`, `linked`, `judge`, `authority`,
  `concurrences`, `calendar`, `clock`, `holder_of`, `owner_of`, …), bound to the decision being
  made.

Nothing in this module knows a decision type. The format reference for spec authors is
`SPEC_FORMAT.md`.
"""

from __future__ import annotations

import ast
import functools
import re
from collections import ChainMap
from collections.abc import Callable, Mapping
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml
from kernel import (
    Calendar,
    Clock,
    Doc,
    Engine,
    Evidence,
    Guards,
    KindRule,
    Obligation,
    Register,
    authority_from_evidence,
    authority_from_terms,
    concurrences,
    concurrences_from_terms,
    covering,
    entry_in_force,
    gate,
    holder,
    in_force,
    in_window,
    judge,
    lineage_routes,
    linked,
    map_role,
    owner_of,
    products_in,
    referenced_agreement,
    register_screen,
    row,
    screen,
    window,
)


class SpecError(ValueError):
    """The spec is malformed: reported before any decision is made."""


# -- the expression language ------------------------------------------------------------------
METHODS = frozenset({
    # str
    "startswith", "endswith", "split", "strip", "lower", "upper", "replace", "partition",
    "rsplit", "join", "format", "splitlines", "isdigit", "rstrip", "lstrip",
    # dict
    "get", "keys", "values", "items",
    # date and time
    "date", "isoformat", "strftime", "astimezone", "total_seconds",
    # kernel objects (Calendar, Clock)
    "elapsed", "moment", "next_open", "add", "local", "working_days_after",
    "working_days_between", "working_day",
})  # fmt: skip
ATTRIBUTES = frozenset({
    "days", "year", "month", "day", "seconds",  # date and timedelta
    "body", "doc_id", "title", "owner", "front", "filename",  # Doc
    "closes", "opens", "zone", "start",  # Calendar and Clock
})  # fmt: skip


@functools.lru_cache(maxsize=4096)
def _parse(src: str) -> ast.expr:
    try:
        return ast.parse("(" + src.strip() + "\n)", mode="eval").body  # lines join inside ( )
    except SyntaxError as e:
        raise SpecError(f"syntax error in expression {src!r}: {e.msg}") from e


def evaluate(src: str, env: Mapping[str, Any]) -> Any:
    return _Eval(env).ev(_parse(str(src)))


class _Eval:
    BIN: dict[type, Callable[[Any, Any], Any]] = {
        ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b, ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b, ast.FloorDiv: lambda a, b: a // b,
        ast.Mod: lambda a, b: a % b,
    }  # fmt: skip
    CMP: dict[type, Callable[[Any, Any], bool]] = {
        ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b,
        ast.Lt: lambda a, b: a < b, ast.LtE: lambda a, b: a <= b,
        ast.Gt: lambda a, b: a > b, ast.GtE: lambda a, b: a >= b,
        ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b,
        ast.Is: lambda a, b: a is b, ast.IsNot: lambda a, b: a is not b,
    }  # fmt: skip

    def __init__(self, env: Mapping[str, Any]) -> None:
        self.env = env

    def ev(self, n: ast.AST) -> Any:  # noqa: C901 — one case per allowed node type
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            if n.id not in self.env:
                raise SpecError(f"unknown name {n.id!r}")
            return self.env[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in self.BIN:
            return self.BIN[type(n.op)](self.ev(n.left), self.ev(n.right))
        if isinstance(n, ast.UnaryOp):
            v = self.ev(n.operand)
            if isinstance(n.op, ast.Not):
                return not v
            if isinstance(n.op, ast.USub):
                return -v
        if isinstance(n, ast.BoolOp):
            if isinstance(n.op, ast.And):
                out: Any = True
                for x in n.values:
                    out = self.ev(x)
                    if not out:
                        return out
                return out
            for x in n.values:
                out = self.ev(x)
                if out:
                    return out
            return out
        if isinstance(n, ast.Compare):
            left = self.ev(n.left)
            for op, right_n in zip(n.ops, n.comparators, strict=True):
                right = self.ev(right_n)
                if not self.CMP[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(n, ast.IfExp):
            return self.ev(n.body) if self.ev(n.test) else self.ev(n.orelse)
        if isinstance(n, ast.Dict):
            return {self.ev(k): self.ev(v) for k, v in zip(n.keys, n.values, strict=True)
                    if k is not None}  # fmt: skip
        if isinstance(n, ast.List):
            return [self.ev(x) for x in n.elts]
        if isinstance(n, ast.Tuple):
            return tuple(self.ev(x) for x in n.elts)
        if isinstance(n, ast.Set):
            return {self.ev(x) for x in n.elts}
        if isinstance(n, ast.Subscript):
            target = self.ev(n.value)
            if isinstance(n.slice, ast.Slice):
                lo, hi = (self.ev(x) if x else None for x in (n.slice.lower, n.slice.upper))
                return target[lo:hi]
            return target[self.ev(n.slice)]
        if isinstance(n, ast.Attribute):
            if n.attr.startswith("_") or n.attr not in ATTRIBUTES | METHODS:
                raise SpecError(f"attribute {n.attr!r} is not allowed")
            return getattr(self.ev(n.value), n.attr)
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Attribute) and n.func.attr not in METHODS:
                raise SpecError(f"method {n.func.attr!r} is not allowed")
            if not isinstance(n.func, ast.Name | ast.Attribute):
                raise SpecError("only named functions and allowed methods can be called")
            f = self.ev(n.func)
            args = [self.ev(a) for a in n.args]
            kwargs = {k.arg: self.ev(k.value) for k in n.keywords if k.arg}
            return f(*args, **kwargs)
        if isinstance(n, ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp):
            return self.comp(n)
        if isinstance(n, ast.JoinedStr):
            parts = []
            for v in n.values:
                if isinstance(v, ast.FormattedValue):
                    spec = self.ev(v.format_spec) if v.format_spec else ""
                    parts.append(format(self.ev(v.value), spec))
                else:
                    parts.append(str(self.ev(v)))
            return "".join(parts)
        raise SpecError(f"expression element {type(n).__name__} is not allowed")

    def comp(self, n: ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp) -> Any:
        def bind(target: ast.expr, value: Any, scope: dict[str, Any]) -> None:
            if isinstance(target, ast.Name):
                scope[target.id] = value
            elif isinstance(target, ast.Tuple):
                for t, v in zip(target.elts, value, strict=True):
                    bind(t, v, scope)
            else:
                raise SpecError("comprehension targets must be names or tuples")

        def gen(i: int, env: Mapping[str, Any]) -> Any:
            if i == len(n.generators):
                inner = _Eval(env)
                if isinstance(n, ast.DictComp):
                    yield inner.ev(n.key), inner.ev(n.value)
                else:
                    yield inner.ev(n.elt)
                return
            g = n.generators[i]
            for item in _Eval(env).ev(g.iter):
                scope: dict[str, Any] = {}
                bind(g.target, item, scope)
                child = ChainMap(scope, env)  # type: ignore[arg-type]
                if all(_Eval(child).ev(c) for c in g.ifs):
                    yield from gen(i + 1, child)

        if isinstance(n, ast.GeneratorExp):
            return gen(0, self.env)  # lazy: `next(...)` stops at the first match
        if isinstance(n, ast.SetComp):
            return set(gen(0, self.env))
        if isinstance(n, ast.DictComp):
            return dict(gen(0, self.env))
        return list(gen(0, self.env))


# -- pure helpers available to every spec --------------------------------------------------
def _latest(items: list[Any], field: str) -> Any:
    """The item with the greatest `field` (a window counts by its start), or None."""

    def k(x: Any) -> Any:
        v = x[field]
        return v[0] if isinstance(v, tuple) else v

    return max(items, key=k, default=None)


def _unique_by(items: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    seen, out = set(), []
    for x in items:
        if x[field] not in seen:
            seen.add(x[field])
            out.append(x)
    return out


def _intervals(starts: list[datetime], ends: list[datetime]) -> list[tuple[datetime, datetime]]:
    """Pairs each start with the first end after it (an open start with no end is dropped)."""
    out, ends = [], sorted(ends)
    for s in sorted(starts):
        e = next((x for x in ends if x > s), None)
        if e is not None and not (out and s < out[-1][1]):
            out.append((s, e))
    return out


def _search(pattern: str, text: str, group: int = 1) -> str | None:
    m = re.search(pattern, text, re.S)
    return m[group] if m else None


def _flat(text: str) -> str:
    return " ".join(str(text).split())


def _groups(pattern: str, text: str) -> tuple[str, ...] | None:
    m = re.search(pattern, text, re.S)
    return m.groups() if m else None


def _paragraph(text: str, needle: str) -> str | None:
    """The first blank-line-separated paragraph containing `needle`, flattened."""
    return next((_flat(p) for p in re.split(r"\n\s*\n", text) if needle in p), None)


PURE: dict[str, Any] = {
    "min": min, "max": max, "sum": sum, "len": len, "round": round, "abs": abs, "any": any,
    "all": all, "sorted": sorted, "float": float, "int": int, "str": str, "bool": bool,
    "set": set, "list": list, "dict": dict, "tuple": tuple, "zip": zip, "next": next,
    "iter": iter, "None": None, "True": True, "False": False,
    "date": date.fromisoformat, "datetime": datetime.fromisoformat,
    "combine": datetime.combine, "clock_time": time, "zone": ZoneInfo, "max_date": date.max,
    "days": lambda n: timedelta(days=n), "minutes": lambda n: timedelta(minutes=n),
    "latest": _latest, "unique_by": _unique_by, "intervals": _intervals,
    "union": lambda sets: set().union(*sets),
    "first": lambda items: next(iter(items), None),
    "search": _search, "groups": _groups, "paragraph": _paragraph,
    "findall": lambda p, t: re.findall(p, t, re.M | re.S),
    "maybe": lambda f, x: None if x is None else f(x),
    "flat": _flat, "money": lambda s: float(str(s).replace(",", "").lstrip("$")),
    "row": row, "window": window, "products_in": products_in,
    "referenced_agreement": referenced_agreement,
    "paragraphs": lambda t: re.split(r"\n\s*\n", t),
}  # fmt: skip


def entry_routes(
    entries: list[dict[str, Any]], docs_cfg: dict[str, Any], flags: list[str],
    reg_kinds: Mapping[str, str] | None = None,
) -> bool:  # fmt: skip
    """R3: a relied-on register entry whose document on file differs (mismatch) or is gone
    (missing). With `on_mismatch: use_registered`, the default (G-01, decided 2026-10-05), the
    decision stands on the registered terms and an incident is raised to the owning function; with
    `route` it goes to a person. L3 for entries: relying on two entries of a `single_kinds` kind
    routes (a conflict)."""
    routed = False
    mode = docs_cfg.get("on_mismatch", "use_registered")
    for e in {x["doc_id"]: x for x in entries}.values():
        if e["status"] != "verified":
            flags.append(f"{e['doc_id']}: document on file is {e['status']} against registered "
                         f"version {e['version']}")  # fmt: skip
            if mode == "route":
                routed = True
            else:
                kind = {v: k for k, v in (reg_kinds or {}).items()}.get(e["kind"], e["kind"])
                who = ", ".join(docs_cfg.get("owners", {}).get(kind, [])) or "its owner"
                flags.append(f"incident for {who}: {e['doc_id']} v{e['version']} on file is "
                             f"{e['status']}; decided on the registered terms")  # fmt: skip
    for k in docs_cfg.get("single_kinds", ()):
        ids = sorted({x["doc_id"] for x in entries if x["kind"] == k})
        if len(ids) > 1:
            flags.append(f"conflict: registered {k} " + ", ".join(ids))
            routed = True
    return routed


# -- the runner -------------------------------------------------------------------------------
def load(path: Path) -> dict[str, Any]:
    spec = yaml.safe_load(path.read_text())
    for key in ("spec", "outcomes", "route_to", "documents", "steps", "outcome", "record"):
        if key not in spec:
            raise SpecError(f"{path.name}: missing section {key!r}")
    if spec["route_to"] not in spec["outcomes"]:
        raise SpecError(f"{path.name}: route_to {spec['route_to']!r} is not a declared outcome")
    names = set()
    for step in spec["steps"]:
        if not isinstance(step, dict) or len(step) != 1:
            raise SpecError(f"{path.name}: each step is one `name: expression` pair: {step!r}")
        ((name, expr),) = step.items()
        if name in names and not name.startswith("_"):
            raise SpecError(f"{path.name}: step {name!r} is defined twice")
        names.add(name)
        _parse(str(expr if not isinstance(expr, dict) else expr.get("expr", "")))
    for rule in spec["outcome"]:
        if rule["outcome"] not in spec["outcomes"] and not str(rule["outcome"]).startswith("="):
            raise SpecError(f"{path.name}: outcome {rule['outcome']!r} is not declared")
    return spec


def run(
    spec: dict[str, Any], eng: Engine, ev: Evidence, inputs: dict[str, Any],
    register: Register | None = None,
) -> dict[str, Any]:  # fmt: skip
    used: list[dict[str, Any]] = []
    flags: list[str] = []
    relied: list[Doc] = []
    relied_entries: list[dict[str, Any]] = []
    obligations: list[Obligation] = []
    staff, products = ev.table("employees"), ev.table("products")
    docs_cfg = spec["documents"]
    env: dict[str, Any] = dict(PURE)

    def reader(src: str) -> Callable[[Doc], Any]:
        return lambda doc: evaluate(src, {**env, "doc": doc})

    readers = {name: reader(str(src)) for name, src in (spec.get("readers") or {}).items()}

    def helper(src: str) -> Callable[[Any], Any]:
        return lambda x: evaluate(src, {**env, "x": x})

    env.update({name: helper(str(src)) for name, src in (spec.get("helpers") or {}).items()})
    env.update(readers)
    guards = Guards(
        rules=tuple(KindRule(r["kind"], tuple(r.get("id_prefixes", ())),
                             tuple(r.get("title_words", ())), tuple(r.get("owner_hints", ())))
                    for r in docs_cfg["kinds"]),
        owners={k: set(v) for k, v in docs_cfg["owners"].items()},
        value_of=readers.get(docs_cfg.get("value_reader", ""), lambda d: None),
        product_of=readers.get(docs_cfg.get("product_reader", ""), lambda d: ""),
        policy_kind=docs_cfg.get("policy_kind", "policy"),
        graded=tuple(docs_cfg.get("graded", ())),
        approval_kinds=tuple(docs_cfg.get("approval_kinds", ())),
        parent_kind=docs_cfg.get("parent_kind", "agreement"),
        amending_kinds=tuple(docs_cfg.get("amending_kinds", ())),
        schedule_kinds=tuple(docs_cfg.get("schedule_kinds", ())),
        lineage_kinds=tuple(docs_cfg.get("lineage_kinds", ())),
        single_kinds=tuple(docs_cfg.get("single_kinds", ())),
    )  # fmt: skip
    on_file = ev.docs()
    declared = docs_cfg.get("registered_kinds") or {}
    # spec kind -> register kind; a list means the same names (R1, G-30: register kinds are global)
    reg_kinds = dict(declared) if isinstance(declared, dict) else {k: k for k in declared}
    if reg_kinds and register is None:
        raise SpecError(f"{spec['spec']}: registered_kinds is declared, but no register was given")
    status = register.status(on_file) if register else {}
    docs_in = (
        register_screen(
            on_file,
            register,
            reg_kinds,
            guards.rules,
            flags,
            docs_cfg.get("on_mismatch", "use_registered"),
            docs_cfg.get("owners"),
        )
        if register and reg_kinds
        else on_file
    )
    s = screen(eng, docs_in, guards, staff, products, used, flags)

    def registered(kind: str) -> list[dict[str, Any]]:  # R2
        if register is None:
            raise SpecError(f"{spec['spec']}: registered() needs a register, but none was given")
        return [dict(e, status=status[e["doc_id"]]) for e in register.entries if e["kind"] == kind]

    roles: dict[str, str | None] = {}

    def holder_of(words: str) -> str | None:
        if words not in roles:
            who = holder(staff, map_role(eng, words, staff, used))
            roles[words] = who["employee_id"] if who else None
        return roles[words]

    questions = spec.get("questions") or {}
    env.update(inputs)
    env.update({
        "docs": lambda kind: list(s.good.get(kind, [])),
        "policies": lambda: list(s.pols),
        "inconsistent": s.inconsistent,
        "table": ev.table,
        "staff": staff,
        "products": products,
        "judge": lambda name, state: judge(eng, state, name, questions[name]),
        # a question built from governed content (for example criteria read from a guide)
        "ask": lambda name, question, state: judge(eng, state, name, question),
        "use": lambda *js: used.extend(js) or (js[-1] if js else None),
        "uses": lambda js: used.extend(js) or None,
        "flag": lambda msg: flags.append(msg) or None,
        "rely": lambda *ds: relied.extend(
            d for x in ds for d in (x if isinstance(x, list | tuple) else [x]) if d is not None
        ) or None,
        "covering": covering,
        "registered": registered,
        "entry_in_force": lambda entries, on: entry_in_force(entries, on, flags),
        "in_window": lambda entries, on: [e for e in entries if in_window(e, on)],
        "use_entry": lambda *es: relied_entries.extend(
            e for x in es for e in (x if isinstance(x, list | tuple) else [x]) if e is not None
        ) or None,
        "authority_terms": lambda entry, amount, requested_by: authority_from_terms(
            entry, staff, amount, requested_by),
        "concurrences_terms": lambda entry, amount, tier, requested_by: concurrences_from_terms(
            entry, staff, amount, tier, requested_by),
        "in_force": lambda docs, on: in_force(docs, on, flags),
        "linked": linked,
        "authority": lambda pols, on, amount, requested_by: authority_from_evidence(
            eng, pols, staff, on, amount, requested_by, used, flags),
        "concurrences": lambda pol, amount, tier, requested_by: concurrences(
            eng, pol, staff, amount, tier, requested_by, used),
        "map_role": lambda words: map_role(eng, words, staff, used),
        "holder_of": holder_of,
        "owner_of": lambda account: owner_of(account, staff),
        "calendar": lambda zone, opens, closes, holidays=(): Calendar(
            zone, opens, closes, frozenset(holidays)),
        "clock": lambda cal, business, start, excluded=(): Clock(cal, business, start,
                                                                 list(excluded)),
    })  # fmt: skip

    for step in spec["steps"]:
        ((name, expr),) = step.items()
        if isinstance(expr, dict):
            if "when" in expr and not evaluate(expr["when"], env):
                env.setdefault(name, None)
                continue
            expr = expr["expr"]
        env[name] = evaluate(str(expr), env)

    outcome = None
    for rule in spec["outcome"]:
        if evaluate(rule.get("when", "True"), env):
            o = rule["outcome"]
            outcome = evaluate(o[1:], env) if str(o).startswith("=") else o
            break
    if outcome is None:
        raise SpecError(f"{spec['spec']}: no outcome rule matched")
    env["outcome"] = outcome
    for step in spec.get("then") or []:  # steps that depend on the outcome
        ((name, expr),) = step.items()
        env[name] = evaluate(str(expr), env)

    for rule in spec.get("obligations") or []:
        if not evaluate(rule.get("when", "True"), env):
            continue
        fields = {k: evaluate(str(rule[k]), env) for k in ("role", "holder", "due", "status")
                  if k in rule}  # fmt: skip
        due = fields.get("due")
        if isinstance(due, datetime):
            due = env["cal"].local(due).isoformat() if "cal" in env else due.isoformat()
        elif isinstance(due, date):
            due = due.isoformat()
        obligations.append(Obligation(rule["party"], rule["duty"], fields.get("role"),
                                      fields.get("holder"), due, fields.get("status")))  # fmt: skip

    if spec.get("gate", True):
        routed = lineage_routes(relied, s, guards, flags)  # L2, L3
        routed |= entry_routes(relied_entries, docs_cfg, flags, reg_kinds)  # R3
        uncertain, gated = gate(outcome, relied, s.inconsistent, used, flags,
                                route_to=spec["route_to"])  # fmt: skip
        gated = spec["route_to"] if routed else gated
    else:
        uncertain, gated = [j["q"] for j in used if j["uncertain"]], outcome
    env.update({"gated_outcome": gated, "uncertain": uncertain, "judgments": used,
                "flags": flags, "obligations": [o.record() for o in obligations]})  # fmt: skip
    return {field: evaluate(str(src), env) for field, src in spec["record"].items()}
