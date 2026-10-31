from __future__ import annotations

import json

import httpx
import pytest

from app.investigation import generation
from scripts import embed_chunks


def mock_client(monkeypatch, handler) -> list[httpx.Request]:
    requests: list[httpx.Request] = []

    async def capture(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return await handler(request)

    monkeypatch.setattr(
        generation,
        "make_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(capture)),
    )
    monkeypatch.setattr(
        embed_chunks,
        "make_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(capture)),
    )
    return requests


def assert_key_header_and_url(request: httpx.Request) -> None:
    assert request.headers["x-goog-api-key"] == "test-key"
    assert "test-key" not in str(request.url)
    assert "key=" not in str(request.url)


@pytest.mark.anyio
async def test_generate_investigation_sends_key_in_header_and_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"candidates": []})

    requests = mock_client(monkeypatch, handler)
    payload, _ = await generation.generate_investigation("question")

    assert payload == {"candidates": []}
    assert_key_header_and_url(requests[0])
    body = json.loads(requests[0].content)
    assert body["generationConfig"] == {
        "responseMimeType": "application/json",
        "responseSchema": generation.RESPONSE_SCHEMA,
    }


@pytest.mark.anyio
async def test_generate_investigation_adds_temperature_only_when_given(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"candidates": []})

    requests = mock_client(monkeypatch, handler)
    await generation.generate_investigation("question", temperature=0)

    body = json.loads(requests[0].content)
    assert body["generationConfig"]["temperature"] == 0


@pytest.mark.anyio
async def test_embed_text_sends_key_in_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"embedding": {"values": [0.0] * embed_chunks.EMBEDDING_DIMENSION}},
        )

    requests = mock_client(monkeypatch, handler)
    values = await embed_chunks.embed_text("text")

    assert len(values) == 768
    assert_key_header_and_url(requests[0])
    assert str(requests[0].url).endswith(":embedContent")


@pytest.mark.anyio
async def test_embed_texts_sends_key_in_header_and_batch_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "embeddings": [
                    {"values": [float(i)] * embed_chunks.EMBEDDING_DIMENSION}
                    for i, _ in enumerate(json.loads(request.content)["requests"])
                ]
            },
        )

    requests = mock_client(monkeypatch, handler)
    vectors = await embed_chunks.embed_texts(["one", "two"])

    assert len(vectors) == 2
    assert_key_header_and_url(requests[0])
    assert str(requests[0].url).endswith(":batchEmbedContents")
    assert json.loads(requests[0].content)["requests"] == [
        {
            "model": embed_chunks.GEMINI_MODEL,
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": 768,
        }
        for text in ("one", "two")
    ]
