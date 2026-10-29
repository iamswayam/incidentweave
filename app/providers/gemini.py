"""Async HTTP helpers and provider-layer wrappers for Gemini request routing."""

from __future__ import annotations

import asyncio
import os
import random
from collections import deque
from collections.abc import Awaitable, Callable, Mapping
from datetime import timezone
from email.utils import parsedate_to_datetime
from time import monotonic, perf_counter, time
from typing import Any

import httpx

from app.config import settings

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class ProviderError(RuntimeError):
    """Base exception for provider-layer failures."""

    def __init__(
        self,
        message: str,
        *,
        error_class: str,
        status_code: int | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.error_class = error_class
        self.status_code = status_code
        self.retryable = retryable


class ProviderRateLimitedError(ProviderError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(
            message,
            error_class="rate_limited",
            status_code=status_code,
            retryable=True,
        )


class ProviderServerError(ProviderError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(
            message,
            error_class="server_error",
            status_code=status_code,
            retryable=True,
        )


class ProviderTimeoutError(ProviderError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(
            message,
            error_class="timeout",
            status_code=status_code,
            retryable=True,
        )


class ProviderAuthError(ProviderError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(
            message,
            error_class="auth",
            status_code=status_code,
            retryable=False,
        )


class ProviderBadRequestError(ProviderError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(
            message,
            error_class="bad_request",
            status_code=status_code,
            retryable=False,
        )


class ProviderSafetyBlockedError(ProviderError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(
            message,
            error_class="safety_blocked",
            status_code=status_code,
            retryable=False,
        )


class ProviderSchemaInvalidError(ProviderError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(
            message,
            error_class="schema_invalid",
            status_code=status_code,
            retryable=False,
        )


def _redact_secret(value: str) -> str:
    """Remove the provider key from any error text before surfacing it."""

    try:
        api_key = get_gemini_api_key()
    except RuntimeError:
        return value
    if not api_key:
        return value
    return value.replace(api_key, "[REDACTED]")


def get_gemini_api_key() -> str:
    """Read the Gemini API key from the process environment."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def make_client() -> httpx.AsyncClient:
    """Create an async client with no provider-specific default headers."""

    return httpx.AsyncClient(timeout=60.0)


async def send_once(
    client: httpx.AsyncClient,
    url: str,
    payload: Mapping[str, Any],
) -> httpx.Response:
    """Send one POST attempt with the credential confined to its header."""

    return await client.post(
        url,
        json=payload,
        headers={"x-goog-api-key": get_gemini_api_key()},
    )


def _parse_retry_after(value: str | None, *, now: float, remaining_deadline: float) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        delay_seconds = float(value)
    except ValueError:
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        retry_at = dt.timestamp()
        delay_seconds = max(0.0, retry_at - now)
    if remaining_deadline <= 0:
        return 0.0
    return min(max(delay_seconds, 0.0), remaining_deadline)


def _classify_http_error(
    *,
    status_code: int | None,
    detail: str,
    retryable: bool = False,
) -> ProviderError:
    detail = _redact_secret(detail)
    lowered = detail.lower()
    if status_code == 429:
        return ProviderRateLimitedError(
            f"Gemini request failed with HTTP 429: {detail}",
            status_code=status_code,
        )
    if status_code in {500, 502, 503, 504}:
        return ProviderServerError(
            f"Gemini request failed with HTTP {status_code}: {detail}",
            status_code=status_code,
        )
    if status_code == 408 or "timeout" in lowered:
        return ProviderTimeoutError(
            f"Gemini request failed with HTTP {status_code}: {detail}",
            status_code=status_code,
        )
    if status_code in {401, 403}:
        return ProviderAuthError(
            f"Gemini request failed with HTTP {status_code}: {detail}",
            status_code=status_code,
        )
    if status_code in {400, 422}:
        if "safety" in lowered or "blocked" in lowered or "block" in lowered:
            return ProviderSafetyBlockedError(
                f"Gemini request failed with HTTP {status_code}: {detail}",
                status_code=status_code,
            )
        if "schema" in lowered or "response_schema" in lowered or "responseSchema" in lowered:
            return ProviderSchemaInvalidError(
                f"Gemini request failed with HTTP {status_code}: {detail}",
                status_code=status_code,
            )
        return ProviderBadRequestError(
            f"Gemini request failed with HTTP {status_code}: {detail}",
            status_code=status_code,
        )
    if retryable:
        return ProviderServerError(
            "Gemini request failed after the retry budget was exhausted",
            status_code=status_code,
        )
    return ProviderError(
        f"Gemini request failed: {detail}",
        error_class="server_error",
        status_code=status_code,
        retryable=False,
    )


class AsyncRateLimiter:
    """Simple async limiter for provider requests and tokens; no-op when disabled."""

    def __init__(
        self,
        *,
        rpm: float | None = None,
        tpm: float | None = None,
        rpd: float | None = None,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self.rpm = float(rpm) if rpm is not None else None
        self.tpm = float(tpm) if tpm is not None else None
        self.rpd = float(rpd) if rpd is not None else None
        self.clock = clock or monotonic
        self.sleep = sleep or asyncio.sleep
        self._minute_requests: deque[float] = deque()
        self._minute_tokens: deque[tuple[float, float]] = deque()
        self._day_requests: deque[float] = deque()
        self._day_tokens: deque[tuple[float, float]] = deque()

    def _prune(self, now: float) -> None:
        minute_cutoff = now - 60.0
        day_cutoff = now - 86400.0
        while self._minute_requests and self._minute_requests[0] <= minute_cutoff:
            self._minute_requests.popleft()
        while self._minute_tokens and self._minute_tokens[0][0] <= minute_cutoff:
            self._minute_tokens.popleft()
        while self._day_requests and self._day_requests[0] <= day_cutoff:
            self._day_requests.popleft()
        while self._day_tokens and self._day_tokens[0][0] <= day_cutoff:
            self._day_tokens.popleft()

    async def acquire(self, *, tokens: float = 1.0) -> None:
        if self.rpm is None and self.tpm is None and self.rpd is None:
            return
        now = self.clock()
        self._prune(now)
        wait_for = 0.0
        if self.rpm is not None:
            if len(self._minute_requests) >= self.rpm:
                oldest = self._minute_requests[0]
                wait_for = max(wait_for, 60.0 - (now - oldest) + 0.01)
        if self.tpm is not None:
            minute_tokens = sum(weight for _, weight in self._minute_tokens)
            if minute_tokens + tokens > self.tpm:
                if self._minute_tokens:
                    oldest_ts, _ = self._minute_tokens[0]
                    wait_for = max(wait_for, 60.0 - (now - oldest_ts) + 0.01)
                else:
                    wait_for = max(wait_for, 0.01)
        if self.rpd is not None:
            if len(self._day_requests) >= self.rpd:
                oldest = self._day_requests[0]
                wait_for = max(wait_for, 86400.0 - (now - oldest) + 0.01)
        if wait_for > 0:
            await self.sleep(wait_for)
            now = self.clock()
            self._prune(now)
        self._minute_requests.append(now)
        self._minute_tokens.append((now, tokens))
        self._day_requests.append(now)
        self._day_tokens.append((now, tokens))


class CooldownStateMachine:
    """Small circuit-breaker for provider cooldowns."""

    def __init__(
        self,
        *,
        failure_threshold: int | None = None,
        cooldown_seconds: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.failure_threshold = int(failure_threshold) if failure_threshold is not None else None
        self.cooldown_seconds = float(cooldown_seconds) if cooldown_seconds is not None else None
        self.clock = clock or monotonic
        self.state = "closed"
        self.consecutive_failures = 0
        self.cooldown_until = 0.0

    @property
    def enabled(self) -> bool:
        return self.failure_threshold is not None and self.cooldown_seconds is not None

    def allow_request(self) -> bool:
        if not self.enabled:
            return True
        now = self.clock()
        if self.state == "open":
            if now >= self.cooldown_until:
                self.state = "half-open"
                return True
            return False
        if self.state == "half-open":
            return True
        return True

    def record_success(self) -> None:
        if not self.enabled:
            return
        self.state = "closed"
        self.consecutive_failures = 0
        self.cooldown_until = 0.0

    def record_retryable_failure(self) -> None:
        if not self.enabled:
            return
        now = self.clock()
        self.consecutive_failures += 1
        if self.state == "half-open":
            self.state = "open"
            self.cooldown_until = now + self.cooldown_seconds
            self.consecutive_failures = 0
            return
        if self.consecutive_failures >= self.failure_threshold:
            self.state = "open"
            self.cooldown_until = now + self.cooldown_seconds
            self.consecutive_failures = 0


class GeminiProviderAdapter:
    """Thin adapter around the existing direct Gemini helper contract."""

    def __init__(
        self,
        *,
        rate_limiter: AsyncRateLimiter | None = None,
        cooldown: CooldownStateMachine | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        rng: Callable[[], float] = random.random,
        make_client_factory: Callable[[], httpx.AsyncClient] | None = None,
        post_json_fn: Callable[..., Awaitable[dict[str, Any]]] | None = None,
    ) -> None:
        self.rate_limiter = rate_limiter or AsyncRateLimiter(
            rpm=settings.provider_rate_limit_rpm,
            tpm=settings.provider_rate_limit_tpm,
            rpd=settings.provider_rate_limit_rpd,
        )
        self.cooldown = cooldown or CooldownStateMachine(
            failure_threshold=settings.provider_cooldown_failures,
            cooldown_seconds=settings.provider_cooldown_seconds,
        )
        self.sleep = sleep
        self.rng = rng
        self.make_client_factory = make_client_factory or make_client
        self._post_json_fn = post_json_fn

    async def _before_request(self) -> None:
        if not self.cooldown.allow_request():
            raise ProviderRateLimitedError("Gemini provider cooldown is active")
        await self.rate_limiter.acquire(tokens=1)

    def _after_success(self) -> None:
        self.cooldown.record_success()

    def _after_retryable_failure(self) -> None:
        self.cooldown.record_retryable_failure()

    async def generate_investigation(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
    ) -> tuple[dict[str, object], int]:
        """Generate a grounded response while preserving the current contract."""

        from app.investigation.generation import RESPONSE_SCHEMA

        generation_config: dict[str, object] = {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        }
        if temperature is not None:
            generation_config["temperature"] = temperature
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }
        deadline_seconds = float(settings.provider_retry_deadline_seconds)
        max_attempts = int(settings.provider_retry_max_attempts)
        started_at = perf_counter()
        async with make_client() as client:
            await self._before_request()
            fn = self._post_json_fn or post_json
            try:
                response_payload = await fn(
                    client,
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
                    payload,
                    deadline_seconds=deadline_seconds,
                    max_attempts=max_attempts,
                    sleep=self.sleep,
                    rng=self.rng,
                )
            except ProviderError as exc:
                if exc.retryable:
                    self._after_retryable_failure()
                raise
            self._after_success()
        latency_ms = round((perf_counter() - started_at) * 1000)
        return response_payload, latency_ms

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text value using the existing request shape."""

        from scripts.embed_chunks import (
            EMBEDDING_DIMENSION,
            GEMINI_MODEL,
            _single_embedding_url,
        )

        payload = {
            "model": GEMINI_MODEL,
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": EMBEDDING_DIMENSION,
        }
        async with make_client() as client:
            await self._before_request()
            fn = self._post_json_fn or post_json
            try:
                payload_data = await fn(
                    client,
                    _single_embedding_url(),
                    payload,
                    deadline_seconds=float(settings.provider_retry_deadline_seconds),
                    max_attempts=int(settings.provider_retry_max_attempts),
                    sleep=self.sleep,
                    rng=self.rng,
                )
            except ProviderError as exc:
                if exc.retryable:
                    self._after_retryable_failure()
                raise
            self._after_success()
        embedding = payload_data.get("embedding")
        values = embedding.get("values") if isinstance(embedding, dict) else None
        if not isinstance(values, list):
            raise ValueError("Unexpected Gemini embedding response format")
        if len(values) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Unexpected embedding dimension: expected {EMBEDDING_DIMENSION}, got {len(values)}"
            )
        return [float(value) for value in values]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed values using the existing request shape."""

        from scripts.embed_chunks import (
            EMBEDDING_DIMENSION,
            GEMINI_MODEL,
            _batch_embedding_url,
        )

        payload = {
            "requests": [
                {
                    "model": GEMINI_MODEL,
                    "content": {"parts": [{"text": text}]},
                    "outputDimensionality": EMBEDDING_DIMENSION,
                }
                for text in texts
            ]
        }
        async with make_client() as client:
            await self._before_request()
            fn = self._post_json_fn or post_json
            try:
                payload_data = await fn(
                    client,
                    _batch_embedding_url(),
                    payload,
                    deadline_seconds=float(settings.provider_retry_deadline_seconds),
                    max_attempts=int(settings.provider_retry_max_attempts),
                    sleep=self.sleep,
                    rng=self.rng,
                )
            except ProviderError as exc:
                if exc.retryable:
                    self._after_retryable_failure()
                raise
            self._after_success()
        embeddings = payload_data.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise ValueError("Unexpected Gemini batch embedding response count")
        vectors: list[list[float]] = []
        for embedding in embeddings:
            values = embedding.get("values") if isinstance(embedding, dict) else None
            if not isinstance(values, list) or len(values) != EMBEDDING_DIMENSION:
                raise ValueError(
                    f"Unexpected embedding dimension: expected {EMBEDDING_DIMENSION}"
                )
            vectors.append([float(value) for value in values])
        return vectors


DEFAULT_ADAPTER = GeminiProviderAdapter()


async def post_json(
    client: httpx.AsyncClient,
    url: str,
    payload: Mapping[str, Any],
    *,
    deadline_seconds: float,
    max_attempts: int = 3,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    rng: Callable[[], float] = random.random,
) -> dict[str, Any]:
    """POST JSON with bounded retries, jitter, and a whole-operation deadline."""

    async with asyncio.timeout(deadline_seconds):
        remaining_deadline = float(deadline_seconds)
        for attempt in range(max_attempts):
            try:
                response = await send_once(client, url, payload)
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt + 1 == max_attempts:
                    raise ProviderTimeoutError(
                        f"Gemini request failed after {max_attempts} attempts"
                    ) from None
            else:
                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt + 1 == max_attempts:
                        raise ProviderServerError(
                            f"Gemini request failed after {max_attempts} attempts",
                            status_code=response.status_code,
                        )
                    retry_after = _parse_retry_after(
                        response.headers.get("Retry-After"),
                        now=time(),
                        remaining_deadline=remaining_deadline,
                    )
                    delay = (2**attempt) * (0.5 + rng() / 2)
                    if retry_after is not None:
                        delay = max(delay, retry_after)
                    delay = min(delay, remaining_deadline)
                    remaining_deadline -= delay
                    await sleep(delay)
                    continue
                if response.is_error:
                    detail = _redact_secret(response.text[:300])
                    raise _classify_http_error(
                        status_code=response.status_code,
                        detail=detail,
                    )
                result = response.json()
                if not isinstance(result, dict):
                    raise ProviderError(
                        "Gemini request returned an unexpected JSON value",
                        error_class="schema_invalid",
                        status_code=response.status_code,
                        retryable=False,
                    )
                return result

            delay = (2**attempt) * (0.5 + rng() / 2)
            remaining_deadline -= delay
            await sleep(delay)

    raise ProviderTimeoutError(f"Gemini request failed after {max_attempts} attempts")
