"""Fixtures for the rounds harness: a live OWM service on a free port, in a background thread."""

from __future__ import annotations

import socket
import threading
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn

from owm_service.app import create_app
from owm_service.config import load_settings


@pytest.fixture
def live_service(tmp_path: Path) -> Iterator[str]:
    """Serve the service (jev replay, fresh state) and yield its base URL."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    app = create_app(load_settings({"OWM_STATE_DIR": str(tmp_path / "state"), "OWM_JEV": "replay"}))
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(base + "/lab/clock", timeout=1):
                break
        except OSError:
            time.sleep(0.1)
    else:
        server.should_exit = True
        raise RuntimeError("live_service did not start")
    try:
        yield base
    finally:
        server.should_exit = True
        thread.join(timeout=10)
