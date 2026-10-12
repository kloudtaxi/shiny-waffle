"""The acceptance suite's rebuild check (spec §5 and §10): after every acceptance test, state
rebuilt from the log equals the live state.

Every `Org` a test builds is recorded, including the one an HTTP app builds. After the test, for
each, the live state is read (every decision's current version, the `clearances` and `executions`
projections); then a fresh `Org` over the same state dir rebuilds the projections from the events
and must read back the same. A test that builds no org has nothing to check."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from owm_service.decisions import Decisions
from owm_service.org import Org


def live_state(org: Org) -> tuple[list[dict[str, Any]], list[Any], list[Any]]:
    """Every decision's current version as served, and the two projections."""
    decisions = [r.model_dump(mode="json", exclude_unset=True) for r in Decisions(org).list()]
    return decisions, org.log.clearances(), org.log.executions()


@pytest.fixture(autouse=True)
def rebuilt_equals_live() -> Iterator[None]:
    built: list[Org] = []
    real = Org.__init__

    def recording(self: Org, *args: Any, **kwargs: Any) -> None:
        real(self, *args, **kwargs)
        built.append(self)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Org, "__init__", recording)
        yield
    seen: set[tuple[str, str]] = set()
    for org in built:
        key = (str(org.dir.resolve()), org.corpus)
        if key in seen:
            continue
        seen.add(key)
        live = live_state(org)
        again = Org(org.settings, org_id=org.org_id, corpus=org.corpus)
        again.log.rebuild_projections()
        assert live_state(again) == live, f"rebuilt state differs from the live state: {org.dir}"
