"""THROWAWAY (G-52 spike): register terms → ZEN JDM graphs, a node validator and a band coverage
check. See plan.md. Nothing here is imported by the lab's kernel."""

from __future__ import annotations

import json
import re
from typing import Any

ALLOWED_NODES = {"inputNode", "outputNode", "decisionTableNode", "expressionNode"}
HANDOFFS = {"requestor's manager"}  # the hand-offs the kernel's people walk can resolve


def num(x: Any) -> str:
    f = float(x)
    return str(int(f)) if f.is_integer() else repr(f)


def lit(v: Any) -> str:
    """A ZEN literal for an output cell."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int | float):
        return num(v)
    return json.dumps(v)


def band_cell(lo: Any, hi: Any) -> str:
    """The kernel's `in_band`: a null (or 0) lower bound is open below, so `d <= hi`."""
    low = float(lo or 0.0)
    if low == 0.0:
        return "" if hi is None else f"<= {num(hi)}"
    return f"> {num(low)}" if hi is None else f"({num(low)}..{num(hi)}]"


def list_cell(values: list[Any] | None) -> str:
    return "" if not values else ", ".join(json.dumps(v) for v in values)


class Graph:
    def __init__(self, name: str) -> None:
        self.name = name
        self.nodes: list[dict[str, Any]] = [
            {"id": "in", "type": "inputNode", "name": "Request", "position": {"x": 0, "y": 0}}
        ]
        self.edges: list[dict[str, Any]] = []

    def table(self, nid: str, name: str, path: str, hit: str,
              inputs: list[tuple[str, str]], outputs: list[tuple[str, str]],
              rows: list[tuple[str, list[str], list[str]]]) -> None:  # fmt: skip
        ins = [{"id": f"i{k}", "name": n, "field": f} for k, (n, f) in enumerate(inputs)]
        outs = [{"id": f"o{k}", "name": n, "field": f} for k, (n, f) in enumerate(outputs)]
        rules = []
        for rid, icells, ocells in rows:
            r: dict[str, str] = {"_id": rid}
            r.update({f"i{k}": c for k, c in enumerate(icells)})
            r.update({f"o{k}": c for k, c in enumerate(ocells)})
            rules.append(r)
        self._add(nid, "decisionTableNode", name, {"hitPolicy": hit, "outputPath": path,
                  "inputs": ins, "outputs": outs, "rules": rules})  # fmt: skip

    def constants(self, nid: str, name: str, path: str, values: dict[str, Any]) -> None:
        exprs = [{"id": f"x{k}", "key": key, "value": lit(v)} for k, (key, v) in
                 enumerate(values.items())]  # fmt: skip
        self._add(nid, "expressionNode", name, {"expressions": exprs, "outputPath": path})

    def _add(self, nid: str, kind: str, name: str, content: dict[str, Any]) -> None:
        y = 120 * (len(self.nodes) - 1)
        self.nodes.append({"id": nid, "type": kind, "name": name, "position": {"x": 260, "y": y},
                           "content": content})  # fmt: skip
        self.edges.append({"id": f"e-in-{nid}", "sourceId": "in", "targetId": nid, "type": "edge"})

    def jdm(self) -> dict[str, Any]:
        out = {"id": "out", "type": "outputNode", "name": "Decision", "position": {"x": 560, "y": 0}}
        edges = self.edges + [{"id": f"e-{n['id']}-out", "sourceId": n["id"], "targetId": "out",
                               "type": "edge"} for n in self.nodes[1:]]  # fmt: skip
        return {"name": self.name, "nodes": [*self.nodes, out], "edges": edges}


def bands_and_limits(g: Graph, bands: list[dict[str, Any]], field: str, unit: str) -> None:
    g.table("bands", f"Who must approve ({unit})", "band", "first", [(unit, field)],
            [("Required title", "required_title")],
            [(f"b{k + 1}", [band_cell(b["min_exclusive"], b["max_inclusive"])], [lit(b["title"])])
             for k, b in enumerate(bands)])  # fmt: skip
    titles: list[str] = []
    for b in bands:
        if b["title"] not in titles:
            titles.append(b["title"])
    rows = []
    for k, t in enumerate(titles):
        mine = [b["max_inclusive"] for b in bands if b["title"] == t]
        unlimited = None in mine
        limit = None if unlimited else max(float(h) for h in mine)
        rows.append((f"l{k + 1}", [lit(t)], [lit(limit), lit(unlimited)]))
    rows.append(("l-other", [""], ["0", "false"]))  # a title with no band can approve nothing
    g.table("limits", "The requestor's own limit", "limit", "first", [("Requestor's title", "title")],
            [("Limit", "limit"), ("Unlimited", "unlimited")], rows)  # fmt: skip


def credit_graph(entry: dict[str, Any]) -> dict[str, Any]:
    t = entry["terms"]
    g = Graph(f"{entry['doc_id']} v{entry['version']}: credit authority")
    bands_and_limits(g, t["bands"], "amount", "New credit limit ($)")
    g.table("concurrence", "Who must also concur", "concurrence", "collect",
            [("New credit limit ($)", "amount"), ("Account tier", "tier")],
            [("Concurring title", "title")],
            [(f"c{k + 1}", [f"> {num(c['min_exclusive'])}", list_cell(c.get("tiers"))],
              [lit(c["title"])]) for k, c in enumerate(t.get("concurrence", []))])  # fmt: skip
    g.constants("policy", "Separation of duties", "policy", {
        "separation_of_duties": bool(t.get("separation_of_duties")),
        "passes_to": t.get("separation_of_duties_passes_to"),
    })
    return g.jdm()


def pricing_graph(entry: dict[str, Any]) -> dict[str, Any]:
    t = entry["terms"]
    g = Graph(f"{entry['doc_id']} v{entry['version']}: discount authority")
    bands_and_limits(g, t["bands"], "discount", "Discount (fraction of list)")
    above = t.get("approval_evidence_required_above")
    rows = [("v1", [f"> {num(above)}"], ["true"])] if above is not None else []
    rows.append(("v-other", [""], ["false"]))
    g.table("evidence", "Recorded approval evidence required", "evidence", "first",
            [("Discount (fraction of list)", "discount")], [("Required", "required")], rows)
    return g.jdm()


def sla_graph(entry: dict[str, Any]) -> dict[str, Any]:
    t = entry["terms"]
    g = Graph(f"{entry['doc_id']} v{entry['version']}: SLA targets and credits")
    g.table("targets", "Targets", "target", "first", [("Severity", "severity"), ("Plan", "plan")],
            [("Response (min)", "response_minutes"), ("Restoration (min)", "restoration_minutes"),
             ("Clock", "clock")],
            [(f"t{k + 1}", [num(x["severity"]), "" if x["plan"] is None else lit(x["plan"])],
              [lit(x["response_minutes"]), lit(x["restoration_minutes"]), lit(x["clock"])])
             for k, x in enumerate(t["targets"])])  # fmt: skip
    g.table("credits", "Service credits", "credit", "first",
            [("Severity", "severity"), ("Missed target", "target"), ("Band", "band")],
            [("Credit (fraction of monthly fee)", "pct")],
            [(f"k{k + 1}", [num(c["severity"]), lit(c["target"]),
                            "" if c["band"] is None else num(c["band"])], [lit(c["pct"])])
             for k, c in enumerate(t["credits"])])  # fmt: skip
    g.constants("terms", "Other terms", "terms", {
        "cap_pct": t["cap_pct"], "claim_days": t["claim_days"],
        "notice_business_days": t["notice_business_days"],
    })
    return g.jdm()


BUILDERS = {"credit_policy": credit_graph, "pricing_policy": pricing_graph,
            "sla_schedule": sla_graph}  # fmt: skip


# -- registration checks (P3) ------------------------------------------------------------------
def validate(jdm: dict[str, Any]) -> list[str]:
    """Only input, output, decision-table and expression nodes may be registered."""
    return [f"node {n.get('id')!r} has type {n.get('type')!r}, which isn't allowed in a "
            "registered table" for n in jdm.get("nodes", []) if n.get("type") not in ALLOWED_NODES]


_CELL = re.compile(r"^\s*(?:<=\s*(?P<le>[-\d.]+)|>\s*(?P<gt>[-\d.]+)|"
                   r"\((?P<lo>[-\d.]+)\.\.(?P<hi>[-\d.]+)\]|(?P<any>))\s*$")  # fmt: skip


def interval(cell: str) -> tuple[float | None, float | None]:
    m = _CELL.match(cell)
    if not m:
        raise ValueError(f"not a band cell: {cell!r}")
    if m["le"] is not None:
        return None, float(m["le"])
    if m["gt"] is not None:
        return float(m["gt"]), None
    if m["lo"] is not None:
        return float(m["lo"]), float(m["hi"])
    return None, None


def coverage(jdm: dict[str, Any], node_id: str = "bands") -> list[str]:
    """A band table must cover every value once: open below, contiguous, open above, in order."""
    node = next(n for n in jdm["nodes"] if n["id"] == node_id)
    rules = node["content"]["rules"]
    spans = [(r["_id"], *interval(r["i0"])) for r in rules]
    problems = []
    if spans and spans[0][1] is not None:
        problems.append(f"{spans[0][0]}: nothing covers values up to {spans[0][1]}")
    for (a, _, ahi), (b, blo, _) in zip(spans, spans[1:], strict=False):
        if ahi is None:
            problems.append(f"{a} is open above, so {b} can never match (shadowed)")
        elif blo is None or blo < ahi:
            problems.append(f"{b} overlaps {a} (starts at {blo}, {a} ends at {ahi})")
        elif blo > ahi:
            problems.append(f"gap between {a} and {b}: ({ahi}..{blo}] matches nothing")
    if spans and spans[-1][2] is not None:
        problems.append(f"{spans[-1][0]}: nothing covers values above {spans[-1][2]}")
    return problems
