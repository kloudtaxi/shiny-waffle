"""`python -m owm_service` (with `lab` on the path): the service on 0.0.0.0:8000, configured from
the environment (spec §12). Needs the `owm-service` dependency group."""

from __future__ import annotations

import uvicorn

from .app import create_app
from .config import load_settings


def main() -> None:
    uvicorn.run(create_app(load_settings()), host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
