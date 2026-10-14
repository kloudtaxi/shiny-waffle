"""The proof rounds' own OWM service, run as a child process with fixed settings (spec §3).

Replay-only Jev, lab routes on, its own state directory and port. Any `OWM_*` variable in the
runner's environment is dropped, so a mis-configured instance can't happen. The runner restarts
the child at the start of every round: the demo clock only moves forward.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]


class ServiceChild:
    def __init__(self, port: int, state_dir: Path, start_timeout_s: float = 20) -> None:
        self.port = port
        self.state_dir = state_dir
        self.start_timeout_s = start_timeout_s
        self._proc: subprocess.Popen[bytes] | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> None:
        """Start the child and wait for it to answer; RuntimeError within `start_timeout_s`."""
        self.stop()
        deadline = time.monotonic() + self.start_timeout_s

        def left() -> float:
            return max(0.05, min(1.0, deadline - time.monotonic()))

        with socket.socket() as s:
            s.settimeout(left())
            if s.connect_ex(("127.0.0.1", self.port)) == 0:
                raise RuntimeError("the service port is in use")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if not k.startswith("OWM_")}
        env.update(PYTHONPATH=str(LAB), OWM_PORT=str(self.port), OWM_JEV="replay",
                   OWM_STATE_DIR=str(self.state_dir.resolve()), OWM_LAB_ROUTES="1")  # fmt: skip
        self._proc = proc = subprocess.Popen(
            [sys.executable, "-m", "owm_service"],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        while time.monotonic() < deadline and proc.poll() is None:
            try:
                with urllib.request.urlopen(self.url + "/lab/clock", timeout=left()):
                    pass
            except OSError:
                time.sleep(0.1)
                continue
            if proc.poll() is None:
                return
        self.stop()
        raise RuntimeError("the service did not start")

    def stop(self) -> None:
        proc, self._proc = self._proc, None
        if proc is None:
            return
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    def restart(self) -> None:
        self.stop()
        self.start()
