from __future__ import annotations

import json

import httpx
import pytest

from scripts import embed_chunks
from tests.unit.httpx_client import make_test_client


@pytest.mark.anyio
async def test_single_embedding_can_send_query_task_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "embedding": {
                    "values": [0.0] * embed_chunks.EMBEDDING_DIMENSION,
                }
            },
        )

    monkeypatch.setattr(
        embed_chunks,
        "make_client",
        lambda: make_test_client(transport=httpx.MockTransport(handler)),
    )

    vector = await embed_chunks.embed_text(
        "query text",
        task_type="CODE_RETRIEVAL_QUERY",
        max_attempts=1,
    )

    assert len(vector) == 768
    body = json.loads(requests[0].content)
    assert body["taskType"] == "CODE_RETRIEVAL_QUERY"
    assert body["outputDimensionality"] == 768


@pytest.mark.anyio
async def test_batched_embedding_applies_document_task_type_per_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "embeddings": [
                    {"values": [float(index)] * embed_chunks.EMBEDDING_DIMENSION}
                    for index, _ in enumerate(body["requests"])
                ]
            },
        )

    monkeypatch.setattr(
        embed_chunks,
        "make_client",
        lambda: make_test_client(transport=httpx.MockTransport(handler)),
    )

    vectors = await embed_chunks.embed_texts(
        ["document one", "document two"],
        task_type="RETRIEVAL_DOCUMENT",
        max_attempts=1,
    )

    assert len(vectors) == 2
    body = json.loads(requests[0].content)
    assert [item["taskType"] for item in body["requests"]] == [
        "RETRIEVAL_DOCUMENT",
        "RETRIEVAL_DOCUMENT",
    ]
    assert all(item["outputDimensionality"] == 768 for item in body["requests"])


@pytest.mark.anyio
async def test_default_embedding_payload_omits_task_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "embedding": {
                    "values": [0.0] * embed_chunks.EMBEDDING_DIMENSION,
                }
            },
        )

    monkeypatch.setattr(
        embed_chunks,
        "make_client",
        lambda: make_test_client(transport=httpx.MockTransport(handler)),
    )

    await embed_chunks.embed_text("legacy query")

    assert "taskType" not in json.loads(requests[0].content)


@pytest.mark.anyio
async def test_invalid_embedding_retry_budget_fails_before_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unexpected_client() -> httpx.AsyncClient:
        raise AssertionError("an invalid retry budget must not create a client")

    monkeypatch.setattr(embed_chunks, "make_client", unexpected_client)

    with pytest.raises(ValueError, match="max_attempts must be positive"):
        await embed_chunks.embed_text("query", max_attempts=0)
