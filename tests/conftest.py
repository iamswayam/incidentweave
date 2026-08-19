import asyncio
import sys

import pytest


@pytest.fixture
def anyio_backend() -> str:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return "asyncio"