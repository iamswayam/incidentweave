import asyncio
import ipaddress
import socket
import sys

import pytest
from pytest_socket import SocketBlockedError

_SOCKET = socket.socket
_SOCKETPAIR = socket.socketpair


class _LoopbackOnlySocket(_SOCKET):
    def connect(self, address: object) -> None:
        host = address[0] if isinstance(address, tuple) and address else None
        try:
            is_loopback = host == "localhost" or ipaddress.ip_address(host).is_loopback
        except (TypeError, ValueError):
            is_loopback = False
        if not is_loopback:
            raise SocketBlockedError("Only the Windows event-loop socket pair is allowed.")
        super().connect(address)

    def connect_ex(self, address: object) -> int:
        host = address[0] if isinstance(address, tuple) and address else None
        try:
            is_loopback = host == "localhost" or ipaddress.ip_address(host).is_loopback
        except (TypeError, ValueError):
            is_loopback = False
        if not is_loopback:
            raise SocketBlockedError("Only the Windows event-loop socket pair is allowed.")
        return super().connect_ex(address)


def _windows_loopback_socketpair(
    *args: object,
    **kwargs: object,
) -> tuple[socket.socket, socket.socket]:
    """Permit asyncio's private loopback pair without enabling application networking."""
    previous_socket = socket.socket
    socket.socket = _LoopbackOnlySocket
    try:
        return _SOCKETPAIR(*args, **kwargs)
    finally:
        socket.socket = previous_socket


if sys.platform == "win32":
    socket.socketpair = _windows_loopback_socketpair


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Choose a Windows loop policy matching each tier before fixture setup."""
    if sys.platform != "win32":
        return

    if item.get_closest_marker("integration") is not None:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


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
        if tier == "integration":
            item.add_marker(pytest.mark.allow_hosts(["localhost", "127.0.0.1", "::1"]))


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"