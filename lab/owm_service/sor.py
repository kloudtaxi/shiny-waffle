"""The org's structured exports (systems of record): read-only files plus an overlay of logged
inserts and edits (spec §5). The kernel reads the overlay, so an edit changes a later decision.

Events (stream `sor`): `sor.inserted` `{table, row}` and `sor.edited` `{table, key, field, was,
now}`, one per field. The overlay is the base rows, then inserts, then edits, in event order.
"""

from __future__ import annotations

import csv
import math
import sqlite3
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any, Final

from .errors import NotFound, Refused
from .events import Event, EventLog
from .models import Refusal
from .people import People

STREAM: Final = "sor"
KEYS: Final = {
    "discount_requests": "request_id",
    "credit_requests": "request_id",
    "service_tickets": "ticket_id",
    "crm_accounts": "account_id",
    "customers": "erp_customer_id",
}
NUMERIC: Final = frozenset({
    "requested_discount_pct", "list_value_usd", "discount_value_usd", "net_value_usd",
    "current_limit_usd", "requested_limit_usd", "amount_usd",
})  # fmt: skip
DATES: Final = frozenset({"request_date", "approved_on"})
COLUMN_TYPES: Final[dict[str, str]] = {
    **dict.fromkeys(NUMERIC, "number"),
    **dict.fromkeys(DATES, "date"),
}
OPTIONAL: Final = frozenset({"approved_on"})  # blank until approved

ALL_COLUMNS: Final = "*"  # in a basis list: every column of the row
BASIS_FIELDS: Final[dict[str, tuple[str, ...]]] = {
    "discount": ("account_id", "product_sku", "requested_discount_pct", "request_date",
                 "requested_by"),
    "credit": ("erp_customer_id", "current_limit_usd", "requested_limit_usd", "request_date",
               "requested_by"),
    "sla": (ALL_COLUMNS, "events"),  # every column of the ticket row, then its event ids
}  # fmt: skip


def _refuse(status: int, detail: str) -> Refused:
    return Refused(status, [Refusal(rule="RR-5", detail=detail)])


def _check(column: str, value: object, *, insert: bool = False) -> str:
    """The value as a string if it fits the column's type, else a 422 refusal."""
    if not isinstance(value, str):
        raise _refuse(422, f"{column}: {value!r} is not a string")
    kind = COLUMN_TYPES.get(column)
    if value == "" and (column in OPTIONAL or insert):
        return value
    if kind == "number":
        try:
            ok = math.isfinite(float(value))
        except ValueError:
            ok = False
        if not ok:
            raise _refuse(422, f"{column}: {value!r} is not a number")
    elif kind == "date":
        try:
            ok = len(value) == 10 and date.fromisoformat(value).isoformat() == value
        except ValueError:
            ok = False
        if not ok:
            raise _refuse(422, f"{column}: {value!r} is not an ISO date (YYYY-MM-DD)")
    return value


class SystemsOfRecord:
    def __init__(self, log: EventLog, org: str, root: Path) -> None:
        self.log, self.org, self.root = log, org, root
        self._base: dict[str, list[dict[str, str]]] = {}
        self._cols: dict[str, list[str]] = {}
        self._cache: tuple[int, list[Event]] | None = None
        self._lock = threading.Lock()

    # -- reading --------------------------------------------------------------------------
    def _base_rows(self, name: str) -> list[dict[str, str]]:
        if name not in self._base:
            path = self.root / "structured" / f"{name}.csv"
            if "/" in name or "\\" in name or not path.is_file():
                raise NotFound(f"table {name}")
            with path.open(newline="") as f:
                reader = csv.DictReader(f)
                self._base[name] = list(reader)
                self._cols[name] = list(reader.fieldnames or [])
        return self._base[name]

    def _columns(self, name: str) -> list[str]:
        self._base_rows(name)
        return self._cols[name]

    def _events(self) -> list[Event]:
        with self._lock:
            last = self.log.last_seq(self.org, STREAM)
            if self._cache is None or self._cache[0] != last:
                evs = self.log.read(self.org, stream=STREAM, kinds=("sor.inserted", "sor.edited"))
                self._cache = (last, evs)
            return self._cache[1]

    def table(self, name: str) -> list[dict[str, str]]:
        """The table now: base rows, then inserts, then edits (event order). Fresh copies."""
        rows = [dict(r) for r in self._base_rows(name)]
        key = KEYS.get(name)
        for ev in self._events():
            if ev.payload["table"] != name:
                continue
            if ev.kind == "sor.inserted":
                rows.append(dict(ev.payload["row"]))
            elif key:
                for r in rows:
                    if r.get(key) == ev.payload["key"]:
                        r[ev.payload["field"]] = ev.payload["now"]
        return rows

    def row(self, table: str, key: str) -> dict[str, str] | None:
        col = KEYS.get(table)
        if col is None:
            raise NotFound(f"table {table} has no key")
        return next((r for r in self.table(table) if r.get(col) == key), None)

    def edits(self, table: str, key: str, *, after: datetime | None = None) -> list[Event]:
        return [
            e for e in self._events()
            if e.kind == "sor.edited" and e.payload["table"] == table
            and e.payload["key"] == key and (after is None or e.at > after)
        ]  # fmt: skip

    # -- writing --------------------------------------------------------------------------
    def _in_tx(self, tx: sqlite3.Connection, table: str) -> list[dict[str, str]]:
        """The table as the open transaction sees it (so two writes in one transaction agree)."""
        key = KEYS.get(table)
        rows = [dict(r) for r in self._base_rows(table)]
        for ev in self.log.read(self.org, stream=STREAM, tx=tx):
            if ev.payload["table"] != table:
                continue
            if ev.kind == "sor.inserted":
                rows.append(dict(ev.payload["row"]))
            elif ev.kind == "sor.edited" and key:
                for r in rows:
                    if r.get(key) == ev.payload["key"]:
                        r[ev.payload["field"]] = ev.payload["now"]
        return rows

    def insert(
        self, tx: sqlite3.Connection, table: str, row: dict[str, str], *,
        actor: dict[str, Any] | None, at: datetime,
    ) -> None:  # fmt: skip
        cols = self._columns(table)
        extra = sorted(set(row) - set(cols))
        if extra:
            raise _refuse(422, f"{table}: unknown column {extra[0]!r}")
        full = {c: _check(c, row.get(c, ""), insert=True) for c in cols}
        col = KEYS.get(table)
        if col:
            if not full[col]:
                raise _refuse(422, f"{col}: a key is required")
            if any(r.get(col) == full[col] for r in self._in_tx(tx, table)):
                raise _refuse(409, f"{table}: {col} {full[col]!r} already exists")
        self.log.append(tx, at=at, org=self.org, stream=STREAM, kind="sor.inserted",
                        actor=actor, payload={"table": table, "row": full})  # fmt: skip

    def edit(
        self, tx: sqlite3.Connection, table: str, key: str, fields: dict[str, str], *,
        actor: dict[str, Any] | None, at: datetime,
    ) -> None:  # fmt: skip
        col = KEYS.get(table)
        if col is None:
            raise NotFound(f"table {table} takes inserts only")
        cols = self._columns(table)
        current = next((r for r in self._in_tx(tx, table) if r.get(col) == key), None)
        if current is None:
            raise NotFound(f"{table} {key}")
        for field in fields:
            if field not in cols:
                raise _refuse(422, f"{table}: unknown column {field!r}")
            if field == col:
                raise _refuse(422, f"{col}: the key can't be edited")
        checked = {f: _check(f, v) for f, v in fields.items()}
        for field, now in checked.items():
            self.log.append(
                tx, at=at, org=self.org, stream=STREAM, kind="sor.edited", actor=actor,
                payload={"table": table, "key": key, "field": field, "was": current[field],
                         "now": now},
            )  # fmt: skip


def contract_view(kind: str, row: dict[str, str], people: People) -> dict[str, Any]:
    """The §3.5 field names for a request or ticket row, in the contract's units."""
    out: dict[str, Any] = {}
    if kind == "discount":
        out["customer"] = row["account_id"]
        out["product"] = row["product_sku"]
        out["requested_discount"] = float(row["requested_discount_pct"]) / 100
    elif kind == "credit":
        out["customer"] = row["erp_customer_id"]
        out["requested_limit_usd"] = float(row["requested_limit_usd"])
        out["current_limit_usd"] = float(row["current_limit_usd"])
    else:
        out["customer"] = row["account_id"]
        out["product"] = row["product_sku"]
    if "request_date" in row:
        out["request_date"] = row["request_date"]
    out["status"] = row["status"]
    who = people.by_email(row["requested_by"]) if row.get("requested_by") else None
    if who:
        out["requestor"] = who.id
    return out


def basis_columns(kind: str, row: dict[str, str]) -> list[str]:
    """The basis fields for `kind`, with `*` replaced by the row's own columns."""
    out: list[str] = []
    for f in BASIS_FIELDS[kind]:
        out += list(row) if f == ALL_COLUMNS else [f]
    return out
