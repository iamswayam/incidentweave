from __future__ import annotations

from dataclasses import fields
from typing import Any

import httpx
import pytest

from app.config import settings
from app.providers import gemini, usage


class FakeUsageLogger:
    def __init__(self) -> None:
        self.entries: list[usage.UsageEntry] = []
        self.error: Exception | None = None

    async def record(self, entry: usage.UsageEntry) -> None:
        if self.error is not None:
            raise self.error
        self.entries.append(entry)


def _adapter(
    logger: FakeUsageLogger,
    *,
    post_json_fn: Any = None,
    cooldown: gemini.CooldownStateMachine | None = None,
) -> gemini.GeminiProviderAdapter:
    return gemini.GeminiProviderAdapter(
        rate_limiter=gemini.AsyncRateLimiter(),
        cooldown=cooldown or gemini.CooldownStateMachine(),
        post_json_fn=post_json_fn,
        usage_logger=logger,
    )


def _usage_response(
    *,
    prompt_tokens: object = 12,
    candidate_tokens: object = 7,
) -> dict[str, object]:
    return {
        "usageMetadata": {
            "promptTokenCount": prompt_tokens,
            "candidatesTokenCount": candidate_tokens,
        }
    }


def test_usage_entry_has_exactly_the_approved_fields() -> None:
    assert tuple(field.name for field in fields(usage.UsageEntry)) == (
        "provider",
        "model",
        "operation_tag",
        "status",
        "error_class",
        "attempt_count",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "correlation_id",
    )


@pytest.mark.anyio
async def test_success_records_model_operation_attempt_latency_and_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    logger = FakeUsageLogger()
    adapter = _adapter(logger)

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_usage_response())

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await adapter.post_json(
            client,
            "https://example.test/v1beta/models/gemini-test:generateContent",
            {},
            deadline_seconds=5,
            operation_tag="generation",
        )

    assert result == _usage_response()
    assert len(logger.entries) == 1
    entry = logger.entries[0]
    assert entry.provider == "gemini"
    assert entry.model == "gemini-test"
    assert entry.operation_tag == "generation"
    assert entry.status == "success"
    assert entry.error_class is None
    assert entry.attempt_count == 1
    assert entry.latency_ms is not None
    assert entry.input_tokens == 12
    assert entry.output_tokens == 7
    assert len(entry.correlation_id) == 32


@pytest.mark.anyio
async def test_exhausted_503_retries_are_logged_with_attempt_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    logger = FakeUsageLogger()
    adapter = gemini.GeminiProviderAdapter(
        rate_limiter=gemini.AsyncRateLimiter(),
        cooldown=gemini.CooldownStateMachine(),
        sleep=_no_sleep,
        rng=lambda: 0.0,
        usage_logger=logger,
    )

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(gemini.ProviderServerError):
            await adapter.post_json(
                client,
                "https://example.test/v1beta/models/gemini-test:generateContent",
                {},
                deadline_seconds=10,
                max_attempts=3,
            )

    assert len(logger.entries) == 1
    entry = logger.entries[0]
    assert entry.status == "failure"
    assert entry.error_class == "server_error"
    assert entry.attempt_count == 3


async def _no_sleep(_delay: float) -> None:
    return None


@pytest.mark.anyio
async def test_open_cooldown_logs_rate_limited_without_attempt_or_latency() -> None:
    logger = FakeUsageLogger()
    cooldown = gemini.CooldownStateMachine(
        failure_threshold=1,
        cooldown_seconds=60,
        clock=lambda: 10,
    )
    cooldown.state = "open"
    cooldown.cooldown_until = 100
    adapter = _adapter(logger, cooldown=cooldown)

    with pytest.raises(gemini.ProviderRateLimitedError):
        await adapter.post_json(
            httpx.AsyncClient(),
            "https://example.test/v1beta/models/gemini-test:generateContent",
            {},
            deadline_seconds=5,
        )

    assert len(logger.entries) == 1
    entry = logger.entries[0]
    assert entry.status == "failure"
    assert entry.error_class == "rate_limited"
    assert entry.attempt_count == 0
    assert entry.latency_ms is None


@pytest.mark.anyio
async def test_usage_logger_failure_does_not_change_success_or_provider_exception() -> None:
    logger = FakeUsageLogger()
    logger.error = RuntimeError("logger unavailable")

    async def succeed(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {"ok": True}

    adapter = _adapter(logger, post_json_fn=succeed)
    result = await adapter.post_json(
        httpx.AsyncClient(),
        "https://example.test/models/gemini-test:generateContent",
        {},
        deadline_seconds=5,
    )
    assert result == {"ok": True}

    expected = gemini.ProviderServerError("provider unavailable")

    async def fail(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise expected

    adapter._post_json_fn = fail
    with pytest.raises(gemini.ProviderServerError) as raised:
        await adapter.post_json(
            httpx.AsyncClient(),
            "https://example.test/models/gemini-test:generateContent",
            {},
            deadline_seconds=5,
        )
    assert raised.value is expected


@pytest.mark.anyio
async def test_default_adapter_does_not_access_database_when_logging_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "provider_usage_log_enabled", False)

    def fail_if_db_accessed() -> None:
        raise AssertionError("disabled usage logging must not access the database")

    monkeypatch.setattr(usage, "AsyncSessionLocal", fail_if_db_accessed)
    adapter = gemini.GeminiProviderAdapter()
    assert isinstance(adapter.usage_logger, usage.NullUsageLogger)

    async def succeed(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {"ok": True}

    adapter._post_json_fn = succeed
    result = await adapter.post_json(
        httpx.AsyncClient(),
        "https://example.test/models/gemini-test:generateContent",
        {},
        deadline_seconds=5,
    )
    assert result == {"ok": True}


@pytest.mark.anyio
async def test_usage_operation_overrides_call_tag_and_resets_afterward() -> None:
    logger = FakeUsageLogger()

    async def succeed(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {"ok": True}

    adapter = _adapter(logger, post_json_fn=succeed)
    async with httpx.AsyncClient() as client:
        with usage.usage_operation("evaluation"):
            await adapter.post_json(
                client,
                "https://example.test/models/gemini-test:generateContent",
                {},
                deadline_seconds=5,
                operation_tag="generation",
            )
        await adapter.post_json(
            client,
            "https://example.test/models/gemini-test:generateContent",
            {},
            deadline_seconds=5,
            operation_tag="query_embedding",
        )

    assert [entry.operation_tag for entry in logger.entries] == [
        "evaluation",
        "query_embedding",
    ]
    assert usage.operation_override_var.get() is None


def test_usage_operation_rejects_invalid_tag() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        with usage.usage_operation("invalid"):
            pytest.fail("invalid operation should not enter the context")


@pytest.mark.anyio
async def test_non_integer_usage_metadata_is_logged_as_none() -> None:
    logger = FakeUsageLogger()
    adapter = _adapter(logger)

    async def succeed(*_args: object, **_kwargs: object) -> dict[str, object]:
        return _usage_response(prompt_tokens="12", candidate_tokens=7.0)

    adapter._post_json_fn = succeed
    await adapter.post_json(
        httpx.AsyncClient(),
        "https://example.test/models/gemini-test:generateContent",
        {},
        deadline_seconds=5,
    )

    assert logger.entries[0].input_tokens is None
    assert logger.entries[0].output_tokens is None


@pytest.mark.anyio
async def test_value_error_from_provider_helper_is_not_logged() -> None:
    logger = FakeUsageLogger()

    async def fail(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise ValueError("invalid helper output")

    adapter = _adapter(logger, post_json_fn=fail)
    with pytest.raises(ValueError, match="invalid helper output"):
        await adapter.post_json(
            httpx.AsyncClient(),
            "https://example.test/models/gemini-test:generateContent",
            {},
            deadline_seconds=5,
        )

    assert logger.entries == []
