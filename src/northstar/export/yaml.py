"""YAML export for the answer key."""

from __future__ import annotations

from datetime import date
from typing import Any

import yaml


class _Dumper(yaml.SafeDumper):
    pass


def _date(dumper: yaml.SafeDumper, value: date) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:timestamp", value.isoformat())


_Dumper.add_representer(date, _date)


def dump(data: Any, header: str = "") -> str:
    body = yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)
    prefix = "".join(f"# {line}\n" if line else "#\n" for line in header.splitlines())
    return prefix + body
