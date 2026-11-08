"""Provider interface and Voyage adapter for offline-planned reranker experiments."""

from __future__ import annotations

import asyncio
import json
import math
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Protocol
from uuid import uuid4

import httpx

from app.providers.usage import NullUsageLogger, UsageEntry, UsageLogger

VOYAGE_RERANK_ENDPOINT = "https://api.voyageai.com/v1/rerank"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class RateLimiter(Protocol):
    async def acquire(self, *, tokens: float = 1.0) -> None: ...


class Cooldown(Protocol):
    def allow_request(self) -> bool: ...
    def record_success(self) -> None: ...
    def record_retryable_failure(self) -> None: ...


@dataclass(frozen=True)
class RerankResponse:
    indices: tuple[int, ...]
    response: Mapping[str, Any]
    token_count: int | None
    latency_ms: int
    attempt_count: int
    attempt_records: tuple[Mapping[str, Any], ...] = ()


class RerankProvider(Protocol):
    async def rerank(
        self,
        query: str,
        documents: Sequence[str],
        *,
        top_k: int,
        truncation: bool,
        timeout_seconds: float,
        max_attempts: int,
        retry_policy: Mapping[str, Any],
    ) -> RerankResponse: ...


class VoyageRerankFailure(RuntimeError):
    def __init__(
        self,
        error_class: str,
        *,
        status_code: int | None,
        attempts: int,
        latency_ms: int,
        attempt_records: Sequence[Mapping[str, Any]] = (),
    ) -> None:
        super().__init__(f"Voyage rerank failed ({error_class})")
        self.error_class = error_class
        self.status_code = status_code
        self.attempts = attempts
        self.latency_ms = latency_ms
        self.retryable = error_class in {"rate_limited", "server_error", "timeout"}
        self.attempt_records = tuple(attempt_records)


class VoyageRerankAdapter:
    """Rate-limited, cooldown-aware Voyage reranker with metadata-only usage logging."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        api_version: str,
        client: httpx.AsyncClient,
        rate_limiter: RateLimiter | None = None,
        cooldown: Cooldown | None = None,
        usage_logger: UsageLogger | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if not api_key or not model:
            raise ValueError("Voyage API key and model pin are required")
        if api_version != "v1":
            raise ValueError("Voyage reranker API version must be 'v1'")
        self._api_key = api_key
        self.model = model
        self.client = client
        if rate_limiter is None:
            from app.config import settings
            from app.providers.gemini import AsyncRateLimiter

            rate_limiter = AsyncRateLimiter(
                rpm=settings.provider_rate_limit_rpm,
                tpm=settings.provider_rate_limit_tpm,
                rpd=settings.provider_rate_limit_rpd,
            )
        if cooldown is None:
            from app.config import settings
            from app.providers.gemini import CooldownStateMachine

            cooldown = CooldownStateMachine(
                failure_threshold=settings.provider_cooldown_failures,
                cooldown_seconds=settings.provider_cooldown_seconds,
            )
        self.rate_limiter = rate_limiter
        self.cooldown = cooldown
        self.usage_logger = usage_logger or NullUsageLogger()
        self.sleep = sleep

    async def _record_usage(
        self,
        *,
        status: str,
        error_class: str | None,
        attempts: int,
        latency_ms: int,
        token_count: int | None,
    ) -> None:
        await self.usage_logger.record(
            UsageEntry(
                provider="voyage",
                model=self.model,
                operation_tag="evaluation",
                status=status,
                error_class=error_class,
                attempt_count=attempts,
                latency_ms=latency_ms,
                input_tokens=token_count,
                output_tokens=None,
                correlation_id=uuid4().hex,
            )
        )

    @staticmethod
    def _safe_response(body: Mapping[str, Any]) -> dict[str, Any]:
        data = body.get("data")
        usage = body.get("usage")
        if not isinstance(data, list) or not isinstance(usage, Mapping):
            raise ValueError("Voyage returned an invalid rerank response")
        safe_data = []
        for item in data:
            if (
                not isinstance(item, Mapping)
                or type(item.get("index")) is not int
                or not isinstance(item.get("relevance_score"), (int, float))
                or not math.isfinite(float(item.get("relevance_score")))
            ):
                raise ValueError("Voyage returned an invalid rerank result")
            safe_data.append(
                {"index": item["index"], "relevance_score": float(item["relevance_score"])}
            )
        tokens = usage.get("total_tokens")
        if tokens is not None and (type(tokens) is not int or tokens < 0):
            raise ValueError("Voyage returned invalid usage metadata")
        return {
            "data": safe_data,
            "usage": {"total_tokens": tokens},
            "model": body.get("model"),
        }

    async def rerank(
        self,
        query: str,
        documents: Sequence[str],
        *,
        top_k: int,
        truncation: bool,
        timeout_seconds: float,
        max_attempts: int,
        retry_policy: Mapping[str, Any],
    ) -> RerankResponse:
        if not query.strip() or not documents or any(not item for item in documents):
            raise ValueError("rerank query and documents must be non-empty")
        if (
            type(top_k) is not int
            or top_k < 1
            or top_k > len(documents)
            or type(max_attempts) is not int
            or not 1 <= max_attempts <= 5
            or not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool)
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
            or type(truncation) is not bool
        ):
            raise ValueError("invalid pinned rerank limits")
        initial_delay = retry_policy.get("initial_delay_seconds")
        max_delay = retry_policy.get("max_delay_seconds")
        if (
            retry_policy.get("strategy") != "exponential"
            or type(retry_policy.get("respect_retry_after")) is not bool
            or not isinstance(initial_delay, (int, float))
            or isinstance(initial_delay, bool)
            or not math.isfinite(initial_delay)
            or initial_delay <= 0
            or not isinstance(max_delay, (int, float))
            or isinstance(max_delay, bool)
            or not math.isfinite(max_delay)
            or max_delay < initial_delay
        ):
            raise ValueError("invalid pinned rerank retry policy")
        payload = {
            "model": self.model,
            "query": query,
            "documents": list(documents),
            "top_k": top_k,
            "truncation": truncation,
        }
        estimated_tokens = max(1, len(json.dumps(payload, ensure_ascii=False)) // 4)
        started = perf_counter()
        attempts = 0
        attempt_records: list[dict[str, Any]] = []
        status_code = None
        error_class = None
        try:
            if not self.cooldown.allow_request():
                error_class = "rate_limited"
                raise VoyageRerankFailure(error_class, status_code=None, attempts=0, latency_ms=0)
            async with asyncio.timeout(timeout_seconds):
                for attempt in range(max_attempts):
                    attempts = attempt + 1
                    await self.rate_limiter.acquire(tokens=estimated_tokens)
                    try:
                        response = await self.client.post(
                            VOYAGE_RERANK_ENDPOINT,
                            json=payload,
                            timeout=timeout_seconds,
                            headers={
                                "Authorization": f"Bearer {self._api_key}",
                                "Content-Type": "application/json",
                            },
                        )
                    except (httpx.TimeoutException, httpx.NetworkError):
                        attempt_records.append(
                            {
                                "attempt": attempts,
                                "status_code": None,
                                "error_class": "network_error",
                            }
                        )
                        if attempts == max_attempts:
                            error_class = "timeout"
                            raise VoyageRerankFailure(
                                error_class,
                                status_code=None,
                                attempts=attempts,
                                latency_ms=round((perf_counter() - started) * 1000),
                            ) from None
                        delay = min(
                            retry_policy["initial_delay_seconds"] * 2**attempt,
                            retry_policy["max_delay_seconds"],
                            timeout_seconds,
                        )
                    else:
                        status_code = response.status_code
                        if status_code in RETRYABLE_STATUS_CODES:
                            attempt_records.append(
                                {
                                    "attempt": attempts,
                                    "status_code": status_code,
                                    "error_class": (
                                        "rate_limited" if status_code == 429 else "server_error"
                                    ),
                                }
                            )
                            if attempts == max_attempts:
                                error_class = (
                                    "rate_limited" if status_code == 429 else "server_error"
                                )
                                raise VoyageRerankFailure(
                                    error_class,
                                    status_code=status_code,
                                    attempts=attempts,
                                    latency_ms=round((perf_counter() - started) * 1000),
                                )
                            delay = min(
                                retry_policy["initial_delay_seconds"] * 2**attempt,
                                retry_policy["max_delay_seconds"],
                                timeout_seconds,
                            )
                            from app.providers.gemini import _parse_retry_after

                            if retry_policy["respect_retry_after"]:
                                retry_after = _parse_retry_after(
                                    response.headers.get("Retry-After"),
                                    now=time.time(),
                                    remaining_deadline=timeout_seconds,
                                )
                                if retry_after is not None:
                                    delay = min(
                                        max(delay, retry_after),
                                        retry_policy["max_delay_seconds"],
                                        timeout_seconds,
                                    )
                        elif status_code in {401, 403}:
                            error_class = "auth"
                            attempt_records.append(
                                {
                                    "attempt": attempts,
                                    "status_code": status_code,
                                    "error_class": error_class,
                                }
                            )
                            raise VoyageRerankFailure(
                                error_class,
                                status_code=status_code,
                                attempts=attempts,
                                latency_ms=round((perf_counter() - started) * 1000),
                            )
                        elif response.is_error:
                            error_class = "bad_request"
                            attempt_records.append(
                                {
                                    "attempt": attempts,
                                    "status_code": status_code,
                                    "error_class": error_class,
                                }
                            )
                            raise VoyageRerankFailure(
                                error_class,
                                status_code=status_code,
                                attempts=attempts,
                                latency_ms=round((perf_counter() - started) * 1000),
                            )
                        else:
                            try:
                                body = response.json()
                            except ValueError:
                                error_class = "schema_invalid"
                                attempt_records.append(
                                    {
                                        "attempt": attempts,
                                        "status_code": status_code,
                                        "error_class": error_class,
                                    }
                                )
                                raise VoyageRerankFailure(
                                    error_class,
                                    status_code=status_code,
                                    attempts=attempts,
                                    latency_ms=round((perf_counter() - started) * 1000),
                                ) from None
                            if not isinstance(body, Mapping):
                                error_class = "schema_invalid"
                                attempt_records.append(
                                    {
                                        "attempt": attempts,
                                        "status_code": status_code,
                                        "error_class": error_class,
                                    }
                                )
                                raise VoyageRerankFailure(
                                    error_class,
                                    status_code=status_code,
                                    attempts=attempts,
                                    latency_ms=round((perf_counter() - started) * 1000),
                                )
                            try:
                                safe = self._safe_response(body)
                            except ValueError:
                                error_class = "schema_invalid"
                                attempt_records.append(
                                    {
                                        "attempt": attempts,
                                        "status_code": status_code,
                                        "error_class": error_class,
                                    }
                                )
                                raise VoyageRerankFailure(
                                    error_class,
                                    status_code=status_code,
                                    attempts=attempts,
                                    latency_ms=round((perf_counter() - started) * 1000),
                                ) from None
                            results = safe["data"]
                            indices = [item["index"] for item in results]
                            if len(indices) != len(documents) or set(indices) != set(
                                range(len(documents))
                            ):
                                error_class = "schema_invalid"
                                attempt_records.append(
                                    {
                                        "attempt": attempts,
                                        "status_code": status_code,
                                        "error_class": error_class,
                                    }
                                )
                                raise VoyageRerankFailure(
                                    error_class,
                                    status_code=status_code,
                                    attempts=attempts,
                                    latency_ms=round((perf_counter() - started) * 1000),
                                )
                            ordered = sorted(
                                results,
                                key=lambda item: -item["relevance_score"],
                            )
                            attempt_records.append(
                                {
                                    "attempt": attempts,
                                    "status_code": status_code,
                                    "error_class": None,
                                    "response": safe,
                                }
                            )
                            elapsed = round((perf_counter() - started) * 1000)
                            token_count = safe["usage"]["total_tokens"]
                            self.cooldown.record_success()
                            await self._record_usage(
                                status="success",
                                error_class=None,
                                attempts=attempts,
                                latency_ms=elapsed,
                                token_count=token_count,
                            )
                            return RerankResponse(
                                indices=tuple(item["index"] for item in ordered),
                                response=safe,
                                token_count=token_count,
                                latency_ms=elapsed,
                                attempt_count=attempts,
                                attempt_records=tuple(attempt_records),
                            )
                    await self.sleep(delay)
            error_class = "timeout"
            raise VoyageRerankFailure(
                error_class,
                status_code=status_code,
                attempts=attempts,
                latency_ms=round((perf_counter() - started) * 1000),
            )
        except VoyageRerankFailure as exc:
            exc.attempt_records = tuple(attempt_records)
            if exc.retryable:
                self.cooldown.record_retryable_failure()
            else:
                self.cooldown.record_success()
            elapsed = exc.latency_ms
            await self._record_usage(
                status="failure",
                error_class=exc.error_class,
                attempts=exc.attempts,
                latency_ms=elapsed,
                token_count=None,
            )
            raise
        except TimeoutError:
            self.cooldown.record_retryable_failure()
            elapsed = round((perf_counter() - started) * 1000)
            attempt_records.append(
                {"attempt": attempts, "status_code": status_code, "error_class": "timeout"}
            )
            await self._record_usage(
                status="failure",
                error_class="timeout",
                attempts=attempts,
                latency_ms=elapsed,
                token_count=None,
            )
            raise VoyageRerankFailure(
                "timeout",
                status_code=status_code,
                attempts=attempts,
                latency_ms=elapsed,
                attempt_records=attempt_records,
            ) from None
