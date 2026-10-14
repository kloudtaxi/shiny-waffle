"""`python -m owm_service` (with `lab` on the path): the service on 0.0.0.0, port `OWM_PORT`
(default 8000), configured from the environment (spec §12). Needs the `owm-service` dependency
group."""

from __future__ import annotations

import os

import uvicorn

from .app import create_app
from .config import load_settings


def main() -> None:
    port = int(os.environ.get("OWM_PORT", "8000"))
    uvicorn.run(create_app(load_settings()), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
