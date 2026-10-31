"""Gemini text generation for grounded investigations."""

from __future__ import annotations

import logging
from time import perf_counter

from app.config import settings
from app.providers.gemini import (
    ProviderError,
    ProviderTimeoutError,
    guarded_post_json,
    make_client,
)

GEMINI_GENERATION_MODEL = "gemini-3.5-flash-lite"
GEMINI_GENERATION_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_GENERATION_MODEL}:generateContent"
)
GENERATION_TIMEOUT_SECONDS = 60
GENERATION_DEADLINE_SECONDS = 90
MAX_GENERATION_ATTEMPTS = 3
_logger = logging.getLogger(__name__)
_GROQ_FALLBACK_ERROR_CLASSES = {"rate_limited", "server_error", "timeout"}
GENERATION_UNAVAILABLE_ERROR_CLASSES = frozenset(
    {"rate_limited", "server_error", "timeout"}
)
RESPONSE_SCHEMA: dict[str, object] = {
    "type": "OBJECT",
    "properties": {
        "outcome": {
            "type": "STRING",
            "enum": ["answered", "insufficient_evidence"],
        },
        "diagnosis": {"type": "STRING"},
        "self_rating": {
            "type": "STRING",
            "enum": ["low", "medium", "high"],
        },
        "uncertainty_note": {"type": "STRING"},
        "claims": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "text": {"type": "STRING"},
                    "evidence": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "chunk_id": {"type": "STRING"},
                                "quote": {"type": "STRING"},
                            },
                            "required": ["chunk_id", "quote"],
                        },
                    },
                },
                "required": ["text", "evidence"],
            },
        },
    },
    "required": [
        "outcome",
        "diagnosis",
        "self_rating",
        "uncertainty_note",
        "claims",
    ],
}


def is_generation_unavailable_error(error: Exception) -> bool:
    """Return whether an exhausted typed provider failure is availability-related."""

    if isinstance(error, ProviderError):
        return error.error_class in GENERATION_UNAVAILABLE_ERROR_CLASSES
    return isinstance(error, TimeoutError)


def generation_failure_trace(
    error: Exception,
    *,
    elapsed_ms: int,
) -> dict[str, object]:
    """Build a content-free trace of provider failures for one generation operation."""

    from app.providers.usage import correlation_id_var

    chain: list[Exception] = []
    current: BaseException | None = error
    while isinstance(current, Exception):
        chain.append(current)
        current = current.__cause__
    chain.reverse()
    provider_errors = [item for item in chain if isinstance(item, ProviderError)]
    if not provider_errors:
        provider_errors = [ProviderTimeoutError("Generation timed out")]

    attempts: list[dict[str, object]] = []
    for index, provider_error in enumerate(provider_errors):
        provider = "groq" if index > 0 else "gemini"
        attempt_count = (
            0
            if provider_error.error_class == "rate_limited"
            and provider_error.status_code is None
            else (
                MAX_GENERATION_ATTEMPTS
                if provider_error.retryable
                else 1
            )
        )
        attempts.append(
            {
                "provider": provider,
                "model": (
                    str(settings.groq_model or "")
                    if provider == "groq"
                    else GEMINI_GENERATION_MODEL
                ),
                "error_class": provider_error.error_class,
                "attempt_count": attempt_count,
                "attempt_count_basis": "inferred_from_error_class",
            }
        )
    return {
        "failed_stage": "generation",
        "model": str(attempts[-1]["model"]),
        "provider_attempts": attempts,
        "error_classes": [item["error_class"] for item in attempts],
        "attempt_count": sum(int(item["attempt_count"]) for item in attempts),
        "attempt_count_basis": "inferred_from_error_class",
        "elapsed_ms": elapsed_ms,
        "correlation_id": correlation_id_var.get(),
    }


async def generate_investigation(
    prompt: str,
    *,
    temperature: float | None = None,
) -> tuple[dict[str, object], int]:
    """Try Gemini first and return a response from the permitted generation path."""

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
    started_at = perf_counter()
    fallback_error: ProviderError | None = None
    fallback_reason: str | None = None
    fallback_configured = bool(
        settings.groq_fallback_enabled
        and settings.groq_api_key
        and settings.groq_model
    )
    try:
        async with make_client() as client:
            response_payload = await guarded_post_json(
                client,
                GEMINI_GENERATION_ENDPOINT,
                payload,
                deadline_seconds=GENERATION_DEADLINE_SECONDS,
                max_attempts=MAX_GENERATION_ATTEMPTS,
                operation_tag="generation",
            )
        latency_ms = round((perf_counter() - started_at) * 1000)
        return response_payload, latency_ms
    except ProviderError as gemini_error:
        retryable_reason = gemini_error.error_class
        if gemini_error.status_code == 429:
            retryable_reason = "rate_limited"
        if (
            not fallback_configured
            or retryable_reason not in _GROQ_FALLBACK_ERROR_CLASSES
        ):
            raise
        fallback_error = gemini_error
        fallback_reason = retryable_reason
    except TimeoutError as gemini_timeout:
        if not fallback_configured:
            raise
        fallback_error = ProviderTimeoutError("Gemini generation exceeded its deadline")
        fallback_error.__cause__ = gemini_timeout
        fallback_reason = fallback_error.error_class

    assert fallback_error is not None
    _logger.warning(
        "Generation fallback reason=%s from_provider=gemini to_provider=groq",
        fallback_reason,
    )
    from app.providers.groq import generate_with_groq

    try:
        response_payload = await generate_with_groq(
            prompt,
            temperature=temperature,
            deadline_seconds=GENERATION_DEADLINE_SECONDS,
            max_attempts=MAX_GENERATION_ATTEMPTS,
        )
    except ProviderError as groq_error:
        raise groq_error from fallback_error
    return response_payload, round((perf_counter() - started_at) * 1000)
