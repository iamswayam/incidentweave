from __future__ import annotations

import asyncio
import json

import httpx

from app.providers.reranker import VoyageRerankAdapter, VoyageRerankFailure
from app.providers.usage import UsageEntry


class FakeRateLimiter:
    def __init__(self) -> None:
        self.token_requests: list[float] = []

    async def acquire(self, *, tokens: float = 1.0) -> None:
        self.token_requests.append(tokens)


class FakeCooldown:
    def __init__(self) -> None:
        self.failures = 0
        self.successes = 0

    def allow_request(self) -> bool:
        return True

    def record_success(self) -> None:
        self.successes += 1

    def record_retryable_failure(self) -> None:
        self.failures += 1


class RecordingUsageLogger:
    def __init__(self) -> None:
        self.entries: list[UsageEntry] = []

    async def record(self, entry: UsageEntry) -> None:
        self.entries.append(entry)


def test_voyage_reranker_request_and_response_use_only_safe_metadata() -> None:
    secret = "local-test-key"
    text = "private document text"
    requests: list[httpx.Request] = []
    limiter = FakeRateLimiter()
    cooldown = FakeCooldown()
    logger = RecordingUsageLogger()

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "model": "rerank-test-model",
                "data": [
                    {"index": 1, "relevance_score": 0.9},
                    {"index": 0, "relevance_score": 0.2},
                ],
                "usage": {"total_tokens": 12},
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = VoyageRerankAdapter(
                api_key=secret,
                model="rerank-test-model",
                api_version="v1",
                client=client,
                rate_limiter=limiter,
                cooldown=cooldown,
                usage_logger=logger,
            )
            result = await provider.rerank(
                "where is it?",
                [text, "another document"],
                top_k=2,
                truncation=True,
                timeout_seconds=2,
                max_attempts=1,
                retry_policy={
                    "strategy": "exponential",
                    "initial_delay_seconds": 1,
                    "max_delay_seconds": 8,
                    "respect_retry_after": True,
                },
            )
        assert result.indices == (1, 0)
        assert result.token_count == 12
        assert result.response["data"] == [
            {"index": 1, "relevance_score": 0.9},
            {"index": 0, "relevance_score": 0.2},
        ]
        assert result.attempt_records[0]["status_code"] == 200
        assert secret not in repr(result)
        assert text not in repr(result)

    asyncio.run(run())
    request = requests[0]
    assert request.headers["Authorization"] == f"Bearer {secret}"
    assert str(request.url) == "https://api.voyageai.com/v1/rerank"
    assert json.loads(request.content) == {
        "model": "rerank-test-model",
        "query": "where is it?",
        "documents": [text, "another document"],
        "top_k": 2,
        "truncation": True,
    }
    assert limiter.token_requests and limiter.token_requests[0] > 0
    assert cooldown.successes == 1
    assert logger.entries[0].status == "success"
    assert logger.entries[0].input_tokens == 12
    assert secret not in repr(logger.entries)
    assert text not in repr(logger.entries)


def test_voyage_reranker_failure_does_not_expose_provider_body_or_credentials() -> None:
    secret = "local-test-key"
    text = "private document text"
    logger = RecordingUsageLogger()
    cooldown = FakeCooldown()

    async def handler(_request: httpx.Request) -> httpx.Response:
        del _request
        return httpx.Response(
            401,
            json={"message": f"bad key {secret}; request included {text}"},
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = VoyageRerankAdapter(
                api_key=secret,
                model="rerank-test-model",
                api_version="v1",
                client=client,
                rate_limiter=FakeRateLimiter(),
                cooldown=cooldown,
                usage_logger=logger,
            )
            try:
                await provider.rerank(
                    "question",
                    [text],
                    top_k=1,
                    truncation=True,
                    timeout_seconds=2,
                    max_attempts=1,
                    retry_policy={
                        "strategy": "exponential",
                        "initial_delay_seconds": 1,
                        "max_delay_seconds": 8,
                        "respect_retry_after": True,
                    },
                )
            except VoyageRerankFailure as exc:
                assert exc.error_class == "auth"
                assert exc.status_code == 401
                assert secret not in str(exc)
                assert text not in str(exc)
                assert secret not in repr(exc.attempt_records)
                assert text not in repr(exc.attempt_records)
            else:
                raise AssertionError("expected provider failure")

    asyncio.run(run())
    assert logger.entries[0].status == "failure"
    assert logger.entries[0].error_class == "auth"
    assert secret not in repr(logger.entries)
    assert text not in repr(logger.entries)
