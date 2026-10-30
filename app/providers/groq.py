"""Groq chat-completion adapter for the optional generation fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from collections.abc import Awaitable, Callable, Mapping
from time import perf_counter
from typing import Any
from uuid import uuid4

import httpx

from app.config import settings
from app.investigation.generation import RESPONSE_SCHEMA
from app.investigation.parsing import (
    ModelOutputError,
    validate_generation_response_text,
)
from app.providers.gemini import (
    AsyncRateLimiter,
    CooldownStateMachine,
    ProviderAuthError,
    ProviderBadRequestError,
    ProviderError,
    ProviderRateLimitedError,
    ProviderSafetyBlockedError,
    ProviderSchemaInvalidError,
    ProviderServerError,
    ProviderTimeoutError,
    _parse_retry_after,
)
from app.providers.usage import (
    DbUsageLogger,
    NullUsageLogger,
    UsageEntry,
    UsageLogger,
    correlation_id_var,
    operation_override_var,
    validate_operation_tag,
)

GROQ_CHAT_COMPLETIONS_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
JSON_SCHEMA_MODELS = {
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-safeguard-20b",
    "qwen/qwen3.8-27b",
    "meta-models/muse-spark-open",
}
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_logger = logging.getLogger(__name__)


def _json_schema(value: Mapping[str, Any]) -> dict[str, Any]:
    """Translate Gemini's response schema types to JSON Schema spelling."""

    translated: dict[str, Any] = {}
    for key, item in value.items():
        if key == "type" and isinstance(item, str):
            translated[key] = item.lower()
        elif key == "properties" and isinstance(item, Mapping):
            translated[key] = {
                str(name): _json_schema(definition)
                for name, definition in item.items()
                if isinstance(definition, Mapping)
            }
        elif key == "items" and isinstance(item, Mapping):
            translated[key] = _json_schema(item)
        elif key == "required" and isinstance(item, list):
            translated[key] = list(item)
        else:
            translated[key] = item
    return translated


def _request_payload(
    prompt: str,
    *,
    model: str,
    temperature: float | None,
) -> dict[str, Any]:
    schema = _json_schema(RESPONSE_SCHEMA)
    if model in JSON_SCHEMA_MODELS:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "grounded_investigation",
                "strict": False,
                "schema": schema,
            },
        }
        messages = [{"role": "user", "content": prompt}]
    else:
        response_format = {"type": "json_object"}
        messages = [
            {
                "role": "system",
                "content": (
                    "Return one JSON object matching this schema. Do not include "
                    f"Markdown fences or text outside the JSON object. Schema: "
                    f"{json.dumps(schema, separators=(',', ':'))}"
                ),
            },
            {"role": "user", "content": prompt},
        ]
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "response_format": response_format,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    return payload


class GroqProviderAdapter:
    """Provider-scoped limiter, cooldown, retries, classification, and usage logging."""

    def __init__(
        self,
        *,
        rate_limiter: AsyncRateLimiter | None = None,
        cooldown: CooldownStateMachine | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
        rng: Callable[[], float] | None = None,
        usage_logger: UsageLogger | None = None,
    ) -> None:
        self.rate_limiter = rate_limiter or AsyncRateLimiter(
            rpm=settings.groq_rate_limit_rpm,
            tpm=settings.groq_rate_limit_tpm,
            rpd=settings.groq_rate_limit_rpd,
        )
        self.cooldown = cooldown or CooldownStateMachine(
            failure_threshold=settings.groq_cooldown_failures,
            cooldown_seconds=settings.groq_cooldown_seconds,
        )
        self.sleep = sleep or asyncio.sleep
        self.rng = rng or random.random
        self.usage_logger = (
            usage_logger
            if usage_logger is not None
            else (
                DbUsageLogger()
                if settings.provider_usage_log_enabled
                else NullUsageLogger()
            )
        )

    async def _record_usage(
        self,
        *,
        status: str,
        error_class: str | None,
        attempt_count: int,
        latency_ms: int | None,
        result: Mapping[str, Any] | None = None,
    ) -> None:
        usage = result.get("usage") if result is not None else None
        input_tokens = usage.get("prompt_tokens") if isinstance(usage, Mapping) else None
        output_tokens = (
            usage.get("completion_tokens") if isinstance(usage, Mapping) else None
        )
        try:
            await asyncio.wait_for(
                self.usage_logger.record(
                    UsageEntry(
                        provider="groq",
                        model=str(settings.groq_model or "unconfigured"),
                        operation_tag=operation_override_var.get() or "generation",
                        status=status,
                        error_class=error_class,
                        attempt_count=attempt_count,
                        latency_ms=latency_ms,
                        input_tokens=(
                            input_tokens if type(input_tokens) is int else None
                        ),
                        output_tokens=(
                            output_tokens if type(output_tokens) is int else None
                        ),
                        correlation_id=correlation_id_var.get() or uuid4().hex,
                    )
                ),
                timeout=settings.provider_usage_log_timeout_seconds,
            )
        except Exception as exc:
            _logger.warning(
                "Provider usage logger failed (%s)",
                type(exc).__name__,
            )

    async def post_json(
        self,
        client: httpx.AsyncClient,
        payload: Mapping[str, Any],
        *,
        deadline_seconds: float,
        max_attempts: int,
        operation_tag: str = "generation",
    ) -> dict[str, Any]:
        """Send a bounded, authenticated Groq request and classify failures safely."""

        validate_operation_tag(operation_tag)
        if not settings.groq_fallback_enabled:
            raise ProviderAuthError("Groq fallback is disabled")
        api_key = settings.groq_api_key
        model = settings.groq_model
        if not api_key or not model:
            raise ProviderAuthError("Groq fallback is not fully configured")
        if payload.get("model") != model:
            raise ProviderBadRequestError(
                "Groq request model does not match the configured model"
            )
        stats: dict[str, int] = {}
        if not self.cooldown.allow_request():
            await self._record_usage(
                status="failure",
                error_class="rate_limited",
                attempt_count=0,
                latency_ms=None,
            )
            raise ProviderRateLimitedError("Groq provider cooldown is active")

        estimated_tokens = max(1, len(json.dumps(payload)) // 4)
        started_at = perf_counter()
        try:
            await self.rate_limiter.acquire(tokens=estimated_tokens)
            result = await self._post_json(
                client,
                payload,
                api_key=api_key,
                deadline_seconds=deadline_seconds,
                max_attempts=max_attempts,
                estimated_tokens=estimated_tokens,
                stats=stats,
            )
        except ProviderError as exc:
            if exc.retryable:
                self.cooldown.record_retryable_failure()
            else:
                self.cooldown.record_success()
            await self._record_usage(
                status="failure",
                error_class=exc.error_class,
                attempt_count=stats.get("attempts", 0),
                latency_ms=round((perf_counter() - started_at) * 1000),
            )
            raise
        except TimeoutError:
            self.cooldown.record_retryable_failure()
            await self._record_usage(
                status="failure",
                error_class="timeout",
                attempt_count=stats.get("attempts", 0),
                latency_ms=round((perf_counter() - started_at) * 1000),
            )
            raise ProviderTimeoutError("Groq request exceeded its deadline") from None
        except BaseException:
            self.cooldown.release_probe()
            raise

        self.cooldown.record_success()
        await self._record_usage(
            status="success",
            error_class=None,
            attempt_count=stats.get("attempts", 0),
            latency_ms=round((perf_counter() - started_at) * 1000),
            result=result,
        )
        if result.get("model") != model:
            _logger.debug("Groq response model differed from configured model")
        return result

    async def _post_json(
        self,
        client: httpx.AsyncClient,
        payload: Mapping[str, Any],
        *,
        api_key: str,
        deadline_seconds: float,
        max_attempts: int,
        estimated_tokens: int,
        stats: dict[str, int],
    ) -> dict[str, Any]:
        async with asyncio.timeout(deadline_seconds):
            remaining_deadline = float(deadline_seconds)
            for attempt in range(max_attempts):
                stats["attempts"] = attempt + 1
                try:
                    response = await client.post(
                        GROQ_CHAT_COMPLETIONS_ENDPOINT,
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                    )
                except (httpx.TimeoutException, httpx.NetworkError):
                    if attempt + 1 == max_attempts:
                        raise ProviderTimeoutError(
                            f"Groq request failed after {max_attempts} attempts"
                        ) from None
                    delay = (2**attempt) * (0.5 + self.rng() / 2)
                else:
                    if (
                        response.status_code in _RETRYABLE_STATUS_CODES
                        or 500 <= response.status_code < 600
                    ):
                        if attempt + 1 == max_attempts:
                            if response.status_code == 429:
                                raise ProviderRateLimitedError(
                                    "Groq rate limit remained after retries",
                                    status_code=429,
                                )
                            raise ProviderServerError(
                                f"Groq server error after retries "
                                f"(HTTP {response.status_code})",
                                status_code=response.status_code,
                            )
                        retry_after = _parse_retry_after(
                            response.headers.get("Retry-After"),
                            now=time.time(),
                            remaining_deadline=remaining_deadline,
                        )
                        delay = (2**attempt) * (0.5 + self.rng() / 2)
                        if retry_after is not None:
                            delay = max(delay, retry_after)
                        delay = min(delay, remaining_deadline)
                    elif response.status_code == 408:
                        raise ProviderTimeoutError(
                            "Groq request timed out (HTTP 408)",
                            status_code=408,
                        )
                    elif response.status_code in {401, 403}:
                        raise ProviderAuthError(
                            f"Groq authentication failed (HTTP {response.status_code})",
                            status_code=response.status_code,
                        )
                    elif response.status_code == 400:
                        lowered = response.text[:300].casefold()
                        if "safety" in lowered or "blocked" in lowered:
                            raise ProviderSafetyBlockedError(
                                "Groq request was safety-blocked (HTTP 400)",
                                status_code=400,
                            )
                        raise ProviderBadRequestError(
                            "Groq request was rejected (HTTP 400)",
                            status_code=400,
                        )
                    elif response.is_error:
                        raise ProviderBadRequestError(
                            f"Groq request failed (HTTP {response.status_code})",
                            status_code=response.status_code,
                        )
                    else:
                        try:
                            result = response.json()
                        except ValueError:
                            raise ProviderSchemaInvalidError(
                                "Groq returned invalid JSON in its HTTP response",
                                status_code=response.status_code,
                            ) from None
                        if not isinstance(result, dict):
                            raise ProviderSchemaInvalidError(
                                "Groq returned an unexpected response shape",
                                status_code=response.status_code,
                            )
                        return result

                remaining_deadline -= delay
                if remaining_deadline < 0:
                    raise ProviderTimeoutError("Groq request exceeded its deadline")
                await self.sleep(delay)
                await self.rate_limiter.acquire(tokens=estimated_tokens)

        raise ProviderTimeoutError("Groq request exceeded its deadline")


DEFAULT_ADAPTER = GroqProviderAdapter()


def make_client() -> httpx.AsyncClient:
    """Create an HTTP client using the configured Groq request timeout."""

    return httpx.AsyncClient(timeout=settings.groq_timeout_seconds)


async def generate_with_groq(
    prompt: str,
    *,
    temperature: float | None = None,
    deadline_seconds: float = 90,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Generate and validate the same response contract used by Gemini."""

    model = settings.groq_model
    if not settings.groq_fallback_enabled or not settings.groq_api_key or not model:
        raise ProviderAuthError("Groq fallback is disabled or not fully configured")
    request_payload = _request_payload(
        prompt,
        model=model,
        temperature=temperature,
    )
    async with make_client() as client:
        raw_response = await DEFAULT_ADAPTER.post_json(
            client,
            request_payload,
            deadline_seconds=deadline_seconds,
            max_attempts=max_attempts,
        )

    choices = raw_response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], Mapping):
        raise ProviderSchemaInvalidError("Groq response contained no completion choice")
    message = choices[0].get("message")
    if not isinstance(message, Mapping):
        raise ProviderSchemaInvalidError("Groq response contained no completion message")
    refusal = message.get("refusal")
    if isinstance(refusal, str) and refusal:
        raise ProviderSafetyBlockedError("Groq blocked the generation request")
    if choices[0].get("finish_reason") in {"content_filter", "safety"}:
        raise ProviderSafetyBlockedError("Groq blocked the generation request")
    content = message.get("content")
    if not isinstance(content, str):
        raise ProviderSchemaInvalidError("Groq response content was not text")
    try:
        validate_generation_response_text(content)
    except ModelOutputError:
        raise ProviderSchemaInvalidError(
            "Groq response did not match the investigation response schema"
        ) from None

    usage = raw_response.get("usage")
    input_tokens = usage.get("prompt_tokens") if isinstance(usage, Mapping) else None
    output_tokens = (
        usage.get("completion_tokens") if isinstance(usage, Mapping) else None
    )
    normalized_usage: dict[str, int] = {}
    if type(input_tokens) is int:
        normalized_usage["promptTokenCount"] = input_tokens
    if type(output_tokens) is int:
        normalized_usage["candidatesTokenCount"] = output_tokens
    if type(input_tokens) is int and type(output_tokens) is int:
        normalized_usage["totalTokenCount"] = input_tokens + output_tokens
    return {
        "candidates": [
            {"content": {"parts": [{"text": content}]}}
        ],
        "usageMetadata": normalized_usage,
        "_provider": "groq",
        "_model": model,
    }
