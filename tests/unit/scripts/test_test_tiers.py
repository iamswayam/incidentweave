import socket
import sys
from pathlib import Path
from subprocess import CompletedProcess

import pytest
from pytest_socket import SocketBlockedError

from scripts import test_tiers


def test_unit_tier_disables_network_sockets() -> None:
    with pytest.warns(UserWarning, match="A test tried to use socket.socket"):
        with pytest.raises(SocketBlockedError):
            socket.socket()


def test_fast_area_runs_only_the_selected_unit_area(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool) -> CompletedProcess[str]:
        assert check is False
        captured.append(command)
        return CompletedProcess(command, 0)

    monkeypatch.setattr(sys, "argv", ["test_tiers", "fast", "--area", "providers"])
    monkeypatch.setattr(test_tiers.subprocess, "run", fake_run)

    assert test_tiers.main() == 0
    assert len(captured) == 1
    assert Path(captured[0][-2]).parts[-3:] == ("tests", "unit", "providers")
    assert captured[0][-1] == "-q"
