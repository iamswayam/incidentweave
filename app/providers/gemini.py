"""Async HTTP helpers for Gemini provider requests."""

from __future__ import annotations

import asyncio
import os
import random
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

import httpx

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


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
        for attempt in range(max_attempts):
            try:
                response = await send_once(client, url, payload)
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt + 1 == max_attempts:
                    raise RuntimeError(
                        f"Gemini request failed after {max_attempts} attempts"
                    ) from None
            else:
                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt + 1 == max_attempts:
                        raise RuntimeError(
                            f"Gemini request failed after {max_attempts} attempts"
                        )
                elif response.is_error:
                    detail = response.text[:300].replace(get_gemini_api_key(), "[REDACTED]")
                    raise RuntimeError(
                        f"Gemini request failed with HTTP {response.status_code}: {detail}"
                    )
                else:
                    result = response.json()
                    if not isinstance(result, dict):
                        raise RuntimeError("Gemini request returned an unexpected JSON value")
                    return result

            delay = (2**attempt) * (0.5 + rng() / 2)
            await sleep(delay)

    raise RuntimeError(f"Gemini request failed after {max_attempts} attempts")
