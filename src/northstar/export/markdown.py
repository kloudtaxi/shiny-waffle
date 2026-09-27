"""Markdown documents with a YAML front-matter header, as Northstar Drive exports them."""

from __future__ import annotations

from typing import Any

import yaml


def document(front_matter: dict[str, Any], body: str) -> str:
    header = yaml.safe_dump(front_matter, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{header}\n---\n\n{body.strip()}\n"


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def pct(value: float) -> str:
    return f"{value * 100:g}%"


def usd(value: int) -> str:
    return f"${value:,}"
