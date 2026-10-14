from __future__ import annotations

from rounds import foundation


def test_import_is_offline_and_mcp_url_shape() -> None:
    assert foundation.mcp_url("x").endswith("/kbs/x/mcp")
