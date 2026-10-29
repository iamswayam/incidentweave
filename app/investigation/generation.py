"""Gemini text generation for grounded investigations."""

from __future__ import annotations

from time import perf_counter

from app.providers.gemini import make_client, post_json

GEMINI_GENERATION_MODEL = "gemini-3.5-flash-lite"
GEMINI_GENERATION_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_GENERATION_MODEL}:generateContent"
)
GENERATION_TIMEOUT_SECONDS = 60
GENERATION_DEADLINE_SECONDS = 90
MAX_GENERATION_ATTEMPTS = 3
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


async def generate_investigation(
    prompt: str,
    *,
    temperature: float | None = None,
) -> tuple[dict[str, object], int]:
    """Send a grounded prompt to Gemini and return its payload and latency."""

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
    async with make_client() as client:
        response_payload = await post_json(
            client,
            GEMINI_GENERATION_ENDPOINT,
            payload,
            deadline_seconds=GENERATION_DEADLINE_SECONDS,
            max_attempts=MAX_GENERATION_ATTEMPTS,
        )
    latency_ms = round((perf_counter() - started_at) * 1000)
    return response_payload, latency_ms
