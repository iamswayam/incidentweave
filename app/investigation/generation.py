"""Gemini text generation for grounded investigations."""

from __future__ import annotations

import json
import os
import time
from time import perf_counter
from urllib import error, request

GEMINI_GENERATION_MODEL = "gemini-3.5-flash-lite"
GEMINI_GENERATION_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_GENERATION_MODEL}:generateContent"
)
GENERATION_TIMEOUT_SECONDS = 60
MAX_GENERATION_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def get_gemini_api_key() -> str:
    """Read the Gemini API key from the process environment."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def generate_investigation(prompt: str) -> tuple[dict[str, object], int]:
    """Send a grounded prompt to Gemini and return its payload and latency."""

    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
        }
    ).encode("utf-8")
    url = f"{GEMINI_GENERATION_ENDPOINT}?key={get_gemini_api_key()}"
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last_error: Exception | None = None
    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            started_at = perf_counter()
            with request.urlopen(req, timeout=GENERATION_TIMEOUT_SECONDS) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            latency_ms = round((perf_counter() - started_at) * 1000)
            if not isinstance(response_payload, dict):
                raise RuntimeError("Unexpected Gemini generation response format")
            return response_payload, latency_ms
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(
                f"Gemini generation failed with HTTP {exc.code}: {detail}"
            )
            if exc.code not in RETRYABLE_STATUS_CODES:
                raise last_error from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            last_error = RuntimeError(f"Gemini generation connection failed: {exc}")

        if attempt < MAX_GENERATION_ATTEMPTS:
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        f"Gemini generation failed after {MAX_GENERATION_ATTEMPTS} attempts: {last_error}"
    ) from last_error
