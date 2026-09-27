"""CSV export (``\\n`` line endings, stable column order)."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Sequence
from typing import Any


def to_csv(header: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(["" if v is None else v for v in row])
    return buf.getvalue()
