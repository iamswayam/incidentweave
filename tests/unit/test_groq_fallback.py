from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
import pytest

from app.config import settings
from app.investigation import generation, parsing
from app.investigation import graph as graph_module
from app.investigation.confidence import calibrate_confidence
from app.providers import gemini, groq
from app.providers.usage import UsageEntry

VALID_RESPONSE = {
    "outcome": "answered",
    "diagnosis": "connection timeout",
    "self_rating": "medium",
    "uncertainty_note": "",
    "claims": [{"text": "The connection timed out.", "evidence": []}],
}


class RecordingUsageLogger:
    def __init__(self) -> None:
        self.entries: list[UsageEntry] = []

    async def record(self, entry: UsageEntry) -> None:
        self.entries.append(entry)


class FakeSessionContext:
    async def __aenter__(self) -> FakeSessionContext:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


def _groq_payload(content: str | None = None) -> dict[str, Any]:
    return {
        "id": "test-completion",
        "model": "qwen/qwen3.8-27b",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content or json.dumps(VALID_RESPONSE),
                }
            }
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 20},
    }


def _enable_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "groq_fallback_enabled", True)
    monkeypatch.setattr(settings, "groq_api_key", "fake-groq-key")
    monkeypatch.setattr(settings, "groq_model", "qwen/qwen3.8-27b")


def _isolate_groq_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        groq,
        "DEFAULT_ADAPTER",
        _new_groq_adapter(),
    )


def _new_groq_adapter(
    *,
    sleep: Callable[[float], Awaitable[None]] | None = None,
    rng: Callable[[], float] | None = None,
    usage_logger: RecordingUsageLogger | None = None,
) -> groq.GroqProviderAdapter:
    return groq.GroqProviderAdapter(
        rate_limiter=gemini.AsyncRateLimiter(),
        cooldown=gemini.CooldownStateMachine(),
        sleep=sleep,
        rng=rng,
        usage_logger=usage_logger or RecordingUsageLogger(),
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "gemini_error",
    [
        gemini.ProviderRateLimitedError("rate-limited"),
        gemini.ProviderServerError("429 retries exhausted", status_code=429),
        gemini.ProviderServerError("server-error"),
        gemini.ProviderTimeoutError("timeout"),
    ],
)
async def test_generation_falls_back_once_for_retryable_gemini_errors(
    monkeypatch: pytest.MonkeyPatch,
    gemini_error: gemini.ProviderError,
) -> None:
    _enable_fallback(monkeypatch)
    calls: list[str] = []

    async def fail_gemini(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise gemini_error

    async def use_groq(*_args: object, **_kwargs: object) -> dict[str, Any]:
        calls.append("groq")
        return {
            "candidates": [
                {"content": {"parts": [{"text": json.dumps(VALID_RESPONSE)}]}}
            ],
            "_provider": "groq",
            "_model": "qwen/qwen3.8-27b",
        }

    monkeypatch.setattr(generation, "make_client", lambda: httpx.AsyncClient())
    monkeypatch.setattr(generation, "guarded_post_json", fail_gemini)
    monkeypatch.setattr(groq, "generate_with_groq", use_groq)

    payload, _ = await generation.generate_investigation("question")
    assert payload["_provider"] == "groq"
    assert calls == ["groq"]


@pytest.mark.anyio
async def test_generation_falls_back_when_gemini_cooldown_is_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fallback(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    cooldown = gemini.CooldownStateMachine(
        failure_threshold=1,
        cooldown_seconds=60,
        clock=lambda: 0,
    )
    cooldown.state = "open"
    cooldown.cooldown_until = 60
    monkeypatch.setattr(gemini.DEFAULT_ADAPTER, "cooldown", cooldown)
    monkeypatch.setattr(generation, "make_client", lambda: httpx.AsyncClient())
    monkeypatch.setattr(
        groq,
        "generate_with_groq",
        lambda *_args, **_kwargs: asyncio.sleep(
            0,
            result={
                "candidates": [],
                "_provider": "groq",
                "_model": "qwen/qwen3.8-27b",
            },
        ),
    )

    payload, _ = await generation.generate_investigation("question")
    assert payload["_provider"] == "groq"


@pytest.mark.anyio
async def test_generation_falls_back_on_gemini_deadline_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_fallback(monkeypatch)

    async def timeout_gemini(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise TimeoutError("deadline")

    async def use_groq(*_args: object, **_kwargs: object) -> dict[str, Any]:
        return {
            "candidates": [],
            "_provider": "groq",
            "_model": "qwen/qwen3.8-27b",
        }

    monkeypatch.setattr(generation, "make_client", lambda: httpx.AsyncClient())
    monkeypatch.setattr(generation, "guarded_post_json", timeout_gemini)
    monkeypatch.setattr(groq, "generate_with_groq", use_groq)

    payload, _ = await generation.generate_investigation("question")
    assert payload["_provider"] == "groq"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("enabled", "api_key", "model"),
    [
        (False, "fake-groq-key", "qwen/qwen3.8-27b"),
        (True, None, "qwen/qwen3.8-27b"),
        (True, "fake-groq-key", None),
    ],
)
async def test_missing_or_disabled_groq_configuration_does_not_fallback(
    monkeypatch: pytest.MonkeyPatch,
    enabled: bool,
    api_key: str | None,
    model: str | None,
) -> None:
    monkeypatch.setattr(settings, "groq_fallback_enabled", enabled)
    monkeypatch.setattr(settings, "groq_api_key", api_key)
    monkeypatch.setattr(settings, "groq_model", model)
    gemini_error = gemini.ProviderRateLimitedError("rate-limited")

    async def fail_gemini(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise gemini_error

    async def must_not_call_groq(
        *_args: object, **_kwargs: object
    ) -> dict[str, Any]:
        raise AssertionError("Groq must remain disabled")

    monkeypatch.setattr(generation, "make_client", lambda: httpx.AsyncClient())
    monkeypatch.setattr(generation, "guarded_post_json", fail_gemini)
    monkeypatch.setattr(groq, "generate_with_groq", must_not_call_groq)
    with pytest.raises(gemini.ProviderRateLimitedError):
        await generation.generate_investigation("question")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "error",
    [
        gemini.ProviderAuthError("unauthorized"),
        gemini.ProviderBadRequestError("bad request"),
        gemini.ProviderSafetyBlockedError("safety block"),
        gemini.ProviderSchemaInvalidError("invalid output"),
    ],
)
async def test_generation_never_falls_back_for_non_retryable_errors(
    monkeypatch: pytest.MonkeyPatch,
    error: gemini.ProviderError,
) -> None:
    _enable_fallback(monkeypatch)

    async def fail_gemini(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise error

    async def must_not_call_groq(
        *_args: object, **_kwargs: object
    ) -> dict[str, Any]:
        raise AssertionError("Groq must not bypass a non-retryable Gemini error")

    monkeypatch.setattr(generation, "make_client", lambda: httpx.AsyncClient())
    monkeypatch.setattr(generation, "guarded_post_json", fail_gemini)
    monkeypatch.setattr(groq, "generate_with_groq", must_not_call_groq)
    with pytest.raises(type(error)):
        await generation.generate_investigation("question")


@pytest.mark.anyio
async def test_groq_failure_chains_gemini_error_and_does_not_log_secrets(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _enable_fallback(monkeypatch)
    caplog.set_level(logging.WARNING)
    gemini_error = gemini.ProviderServerError("Gemini failed")
    groq_error = groq.ProviderAuthError("Groq credentials were rejected")

    async def fail_gemini(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise gemini_error

    async def fail_groq(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise groq_error

    monkeypatch.setattr(generation, "make_client", lambda: httpx.AsyncClient())
    monkeypatch.setattr(generation, "guarded_post_json", fail_gemini)
    monkeypatch.setattr(groq, "generate_with_groq", fail_groq)

    with pytest.raises(groq.ProviderAuthError) as raised:
        await generation.generate_investigation("question")
    assert raised.value.__cause__ is gemini_error
    assert "fake-groq-key" not in caplog.text
    assert "reason=server_error from_provider=gemini to_provider=groq" in caplog.text


@pytest.mark.anyio
async def test_groq_adapter_honors_retry_after_and_logs_metadata_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "groq_fallback_enabled", True)
    monkeypatch.setattr(settings, "groq_api_key", "fake-groq-key")
    monkeypatch.setattr(settings, "groq_model", "qwen/qwen3.8-27b")
    sleeps: list[float] = []
    responses = iter(
        [
            httpx.Response(429, headers={"Retry-After": "2"}, text="slow down"),
            httpx.Response(200, json=_groq_payload()),
        ]
    )
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return next(responses)

    transport = httpx.MockTransport(handler)
    logger = RecordingUsageLogger()

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    adapter = _new_groq_adapter(
        sleep=fake_sleep,
        rng=lambda: 0,
        usage_logger=logger,
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await adapter.post_json(
            client,
            {"model": "qwen/qwen3.8-27b", "messages": []},
            deadline_seconds=5,
            max_attempts=2,
        )

    assert result["choices"]
    assert sleeps == [2]
    assert requests[0].headers["Authorization"] == "Bearer fake-groq-key"
    assert "fake-groq-key" not in str(requests[0].url)
    assert len(logger.entries) == 1
    entry = logger.entries[0]
    assert (entry.provider, entry.model, entry.operation_tag) == (
        "groq",
        "qwen/qwen3.8-27b",
        "generation",
    )
    assert entry.input_tokens == 12
    assert entry.output_tokens == 20
    assert "fake-groq-key" not in str(entry)


@pytest.mark.anyio
async def test_groq_bad_json_is_schema_invalid_and_redacts_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_key = "private-groq-key"
    monkeypatch.setattr(settings, "groq_api_key", fake_key)
    monkeypatch.setattr(settings, "groq_model", "qwen/qwen3.8-27b")
    monkeypatch.setattr(settings, "groq_fallback_enabled", True)
    _isolate_groq_usage(monkeypatch)
    logger = RecordingUsageLogger()
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            400,
            text=f"invalid payload containing {fake_key}",
        )
    )
    adapter = _new_groq_adapter(usage_logger=logger)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(gemini.ProviderBadRequestError) as raised:
            await adapter.post_json(
                client,
                {"model": "qwen/qwen3.8-27b"},
                deadline_seconds=5,
                max_attempts=1,
            )
    assert fake_key not in str(raised.value)

    monkeypatch.setattr(
        groq,
        "make_client",
        lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _request: httpx.Response(200, json=_groq_payload("not JSON"))
            )
        ),
    )
    with pytest.raises(gemini.ProviderSchemaInvalidError):
        await groq.generate_with_groq("question")


@pytest.mark.anyio
async def test_groq_json_schema_selection_and_same_response_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "groq_api_key", "fake-groq-key")
    monkeypatch.setattr(settings, "groq_model", "qwen/qwen3.8-27b")
    monkeypatch.setattr(settings, "groq_fallback_enabled", True)
    _isolate_groq_usage(monkeypatch)
    captured: list[dict[str, Any]] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(http_request.content))
        return httpx.Response(200, json=_groq_payload())

    monkeypatch.setattr(
        groq,
        "make_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    groq_payload = await groq.generate_with_groq("question")
    gemini_payload = {
        "candidates": [
            {"content": {"parts": [{"text": json.dumps(VALID_RESPONSE)}]}}
        ]
    }

    assert captured[0]["response_format"]["type"] == "json_schema"
    assert groq_payload["candidates"][0]["content"]["parts"][0]["text"] == (
        gemini_payload["candidates"][0]["content"]["parts"][0]["text"]
    )
    assert parsing.parse_investigation_response(groq_payload, [])["diagnosis"] == (
        parsing.parse_investigation_response(gemini_payload, [])["diagnosis"]
    )


def test_groq_adapter_state_is_separate_from_gemini() -> None:
    adapter = _new_groq_adapter()
    assert adapter.rate_limiter is not gemini.DEFAULT_ADAPTER.rate_limiter
    assert adapter.cooldown is not gemini.DEFAULT_ADAPTER.cooldown


def test_json_object_prompt_includes_schema_for_other_models() -> None:
    payload = groq._request_payload(
        "question",
        model="some/unverified-model",
        temperature=None,
    )
    assert payload["response_format"] == {"type": "json_object"}
    assert "Schema:" in payload["messages"][0]["content"]


@pytest.mark.anyio
async def test_graph_reports_the_model_that_generated_the_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_hybrid_search(*_args: object, **_kwargs: object) -> list[dict[str, object]]:
        return [
            {
                "id": 4,
                "file_path": "src/example.py",
                "line_start": 1,
                "line_end": 1,
                "vector_score": 0.1,
                "fts_score": 0.1,
                "rrf_score": 0.04,
                "content": "The example uses a bounded retry.",
            }
        ]

    async def groq_generation(
        _prompt: str,
        *,
        temperature: float | None = None,
    ) -> tuple[dict[str, object], int]:
        del temperature
        return {
            "candidates": [],
            "_provider": "groq",
            "_model": "qwen/qwen3.8-27b",
        }, 12

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "generate_investigation", groq_generation)
    monkeypatch.setattr(
        graph_module,
        "parse_investigation_response",
        lambda *_args, **_kwargs: {
            "diagnosis": "bounded retry",
            "confidence": "medium",
            "raw_self_rating": "medium",
            "raw_text": "{}",
            "cited_chunk_ids": [],
            "claims": [],
            "uncertainty_note": "",
            "submitted_citation_count": 0,
            "valid_citation_count": 0,
            "citation_validity_rate": None,
        },
    )
    initial_state: dict[str, object] = {
        "repository_id": 1,
        "repository_name": "sample",
        "query": "how are retries bounded?",
        "query_embedding": [0.1],
        "search_limit": 5,
        "retry_limit": 10,
        "retry_count": 0,
        "retry_used": False,
        "retrieval_results": [],
        "evidence_check": {},
        "diagnosis": "",
        "confidence": "",
        "cited_chunk_ids": [],
        "model": "gemini-3.5-flash-lite",
        "latency_ms": None,
        "calibration_note": "",
        "confidence_calibrated": False,
        "evidence_source": "hybrid",
        "tool_calls": [],
        "temperature": None,
    }

    result = await graph_module.create_investigation_graph(
        calibrate_confidence
    ).ainvoke(initial_state)
    assert result["model"] == "qwen/qwen3.8-27b"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [
        (429, gemini.ProviderRateLimitedError),
        (500, gemini.ProviderServerError),
        (501, gemini.ProviderServerError),
        (408, gemini.ProviderTimeoutError),
        (401, gemini.ProviderAuthError),
        (403, gemini.ProviderAuthError),
        (400, gemini.ProviderBadRequestError),
    ],
)
async def test_groq_http_statuses_map_to_typed_errors(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    error_type: type[gemini.ProviderError],
) -> None:
    monkeypatch.setattr(settings, "groq_fallback_enabled", True)
    monkeypatch.setattr(settings, "groq_api_key", "fake-groq-key")
    monkeypatch.setattr(settings, "groq_model", "qwen/qwen3.8-27b")
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(status_code, text="provider error")
    )
    adapter = _new_groq_adapter()
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(error_type):
            await adapter.post_json(
                client,
                {"model": "qwen/qwen3.8-27b"},
                deadline_seconds=5,
                max_attempts=1,
            )
