"""Launch the IncidentWeave API with a psycopg-compatible Windows event loop."""

from __future__ import annotations

import asyncio
import os
import selectors
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import uvicorn  # noqa: E402


def _load_generation_key() -> None:
    from app.config import settings

    if settings.gemini_api_key:
        os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key)


def main() -> None:
    os.chdir(REPO_ROOT)
    _load_generation_key()

    if sys.platform == "win32":
        config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8000)
        server = uvicorn.Server(config)
        asyncio.run(
            server.serve(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
        return

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()