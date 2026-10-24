from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest

from scripts import embed_chunks


class FakeScalars:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class FakeResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def scalars(self) -> FakeScalars:
        return FakeScalars(self.values)


class FakeSession:
    def __init__(self, chunks: list[SimpleNamespace]) -> None:
        self.chunks = chunks
        self.added: list[object] = []
        self.committed = False

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def scalar(self, statement: object) -> SimpleNamespace:
        return SimpleNamespace(id=12)

    async def execute(self, statement: object) -> FakeResult:
        return FakeResult(self.chunks)

    def add(self, value: object) -> None:
        self.added.append(value)

    async def commit(self) -> None:
        self.committed = True


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("embeddings", "message"),
    [
        ([{"values": [0.0] * 768}], "response count"),
        ([{"values": [0.0] * 767}, {"values": [0.0] * 767}], "embedding dimension"),
    ],
)
async def test_embed_texts_rejects_wrong_count_or_dimension(
    monkeypatch: pytest.MonkeyPatch,
    embeddings: list[dict[str, list[float]]],
    message: str,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": embeddings})

    monkeypatch.setattr(
        embed_chunks,
        "make_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ValueError, match=message):
        await embed_chunks.embed_texts(["first", "second"])


@pytest.mark.anyio
async def test_embed_repository_chunks_batches_and_limits_concurrency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    chunks = [
        SimpleNamespace(
            id=index + 1,
            content=f"chunk {index}",
            embedding=None,
            file_path="test.py",
        )
        for index in range(120)
    ]
    session = FakeSession(chunks)
    request_sizes: list[int] = []
    in_flight = 0
    maximum_in_flight = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal in_flight, maximum_in_flight
        body = json.loads(request.content)
        batch_size = len(body["requests"])
        request_sizes.append(batch_size)
        in_flight += 1
        maximum_in_flight = max(maximum_in_flight, in_flight)
        try:
            await asyncio.sleep(0.02)
            return httpx.Response(
                200,
                json={
                    "embeddings": [
                        {"values": [float(index)] * 768}
                        for index in range(batch_size)
                    ]
                },
            )
        finally:
            in_flight -= 1

    monkeypatch.setattr(embed_chunks, "AsyncSessionLocal", lambda: session)
    monkeypatch.setattr(
        embed_chunks,
        "make_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    assert await embed_chunks.embed_repository_chunks("repo") == (120, 0, 0)
    assert sorted(request_sizes) == [20, 50, 50]
    assert maximum_in_flight <= embed_chunks.EMBED_CONCURRENCY
    assert maximum_in_flight > 1
    assert all(len(chunk.embedding) == 768 for chunk in chunks)
    assert session.committed
