import asyncio
import sys

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Assign one test tier from each test's location."""
    for item in items:
        path_parts = item.path.parts
        if "tests" not in path_parts:
            continue
        tests_index = path_parts.index("tests")
        if tests_index + 1 >= len(path_parts):
            continue
        tier = path_parts[tests_index + 1]
        if tier in {"unit", "integration", "evaluation"}:
            item.add_marker(getattr(pytest.mark, tier))


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return "asyncio"