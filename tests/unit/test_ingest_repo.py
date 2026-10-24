from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.ingest_repo as ingest_repo
from scripts.ingest_repo import chunk_lines


@pytest.mark.parametrize(
    ("line_count", "expected_windows"),
    [
        (0, []),
        (5, [(0, 5)]),
        (201, [(0, 60), (50, 110), (100, 160), (150, 201)]),
    ],
)
def test_chunk_lines_uses_non_redundant_overlapping_windows(
    line_count: int,
    expected_windows: list[tuple[int, int]],
) -> None:
    lines = [f"line {index}" for index in range(line_count)]

    assert list(chunk_lines(lines)) == expected_windows


class FakeSession:
    def __init__(self) -> None:
        self.chunks = []

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def scalar(self, statement: object) -> SimpleNamespace:
        del statement
        return SimpleNamespace(id=1)

    async def execute(self, statement: object) -> None:
        del statement

    def add_all(self, chunks: list[object]) -> None:
        self.chunks.extend(chunks)

    async def commit(self) -> None:
        return None


@pytest.mark.anyio
async def test_ingest_skips_secret_chunk_without_printing_or_storing_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret = "AIza" + "A" * 35
    (tmp_path / "secret.py").write_text(f"KEY = '{secret}'\n", encoding="utf-8")
    (tmp_path / "safe.py").write_text("VALUE = 42\n", encoding="utf-8")
    session = FakeSession()
    monkeypatch.setattr(ingest_repo, "AsyncSessionLocal", lambda: session)

    files_processed, chunks_created = await ingest_repo.ingest_repository(
        str(tmp_path), "secret-scan-test"
    )
    output = capsys.readouterr().out

    assert files_processed == 2
    assert chunks_created == 1
    assert len(session.chunks) == 1
    assert all(secret not in chunk.content for chunk in session.chunks)
    assert "Skipped chunk with possible secret (google_api_key): secret.py:1-1" in output
    assert secret not in output
