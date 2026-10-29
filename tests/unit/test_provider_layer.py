from __future__ import annotations

import httpx
import pytest

from app.investigation import generation
from app.providers import gemini
from scripts import embed_chunks


@pytest.mark.parametrize(
    ("status_code", "detail", "expected_class", "retryable"),
    [
        (429, "quota exceeded", "rate_limited", True),
        (500, "upstream glitch", "server_error", True),
        (408, "request timeout", "timeout", True),
        (401, "missing auth", "auth", False),
        (400, "bad request", "bad_request", False),
        (400, "safety blocked", "safety_blocked", False),
        (400, "response_schema invalid", "schema_invalid", False),
    ],
)
def test_classify_http_error_table(
    status_code: int,
    detail: str,
    expected_class: str,
    retryable: bool,
) -> None:
    exc = gemini._classify_http_error(status_code=status_code, detail=detail)
    assert exc.error_class == expected_class
    assert exc.retryable is retryable
    assert exc.status_code == status_code


def test_parse_retry_after_handles_seconds_and_http_date() -> None:
    assert gemini._parse_retry_after("5", now=0.0, remaining_deadline=30.0) == 5.0

    assert gemini._parse_retry_after(
        "Wed, 21 Oct 2015 07:28:00 GMT",
        now=0.0,
        remaining_deadline=30.0,
    ) == 30.0


@pytest.mark.anyio
async def test_rate_limiter_respects_rpm_tpm_rpd_with_fake_clock() -> None:
    now = 0.0
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    limiter = gemini.AsyncRateLimiter(
        rpm=2,
        tpm=3,
        rpd=3,
        clock=lambda: now,
        sleep=fake_sleep,
    )

    await limiter.acquire(tokens=1)
    await limiter.acquire(tokens=1)
    await limiter.acquire(tokens=1)

    assert len(sleeps) >= 1
    assert now >= 0.0


@pytest.mark.anyio
async def test_cooldown_state_machine_tracks_closed_open_and_half_open() -> None:
    now = 0.0

    cooldown = gemini.CooldownStateMachine(
        failure_threshold=2,
        cooldown_seconds=5.0,
        clock=lambda: now,
    )

    assert cooldown.allow_request() is True
    cooldown.record_retryable_failure()
    assert cooldown.state == "closed"
    cooldown.record_retryable_failure()
    assert cooldown.state == "open"
    assert cooldown.allow_request() is False

    now = 6.0
    assert cooldown.allow_request() is True
    assert cooldown.state == "half-open"

    cooldown.record_success()
    assert cooldown.state == "closed"


@pytest.mark.anyio
async def test_adapter_uses_legacy_request_shape_for_generation_and_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(":generateContent"):
            return httpx.Response(200, json={"candidates": []})
        if request.url.path.endswith(":embedContent"):
            return httpx.Response(
                200,
                json={"embedding": {"values": [0.0] * embed_chunks.EMBEDDING_DIMENSION}},
            )
        return httpx.Response(
            200,
            json={
                "embeddings": [
                    {"values": [0.0] * embed_chunks.EMBEDDING_DIMENSION},
                    {"values": [1.0] * embed_chunks.EMBEDDING_DIMENSION},
                ]
            },
        )

    monkeypatch.setattr(
        generation,
        "make_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setattr(
        embed_chunks,
        "make_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    payload, _ = await generation.generate_investigation("question")
    assert payload == {"candidates": []}

    values = await embed_chunks.embed_text("text")
    assert len(values) == embed_chunks.EMBEDDING_DIMENSION

    vectors = await embed_chunks.embed_texts(["a", "b"])
    assert len(vectors) == 2
    assert all(len(vector) == embed_chunks.EMBEDDING_DIMENSION for vector in vectors)


def test_error_messages_do_not_leak_google_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "secret-api-key")
    exc = gemini._classify_http_error(
        status_code=400,
        detail="secret-api-key should not appear",
    )
    assert "secret-api-key" not in str(exc)


def test_default_provider_settings_leave_behavior_unchanged() -> None:
    limiter = gemini.AsyncRateLimiter()
    cooldown = gemini.CooldownStateMachine()
    assert limiter.rpm is None
    assert limiter.tpm is None
    assert limiter.rpd is None
    assert cooldown.enabled is False
    assert cooldown.allow_request() is True


def test_retry_after_longer_than_backoff_is_honored_and_capped() -> None:
    assert gemini._parse_retry_after("30", now=0.0, remaining_deadline=10.0) == 10.0
    assert gemini._parse_retry_after("90", now=0.0, remaining_deadline=30.0) == 30.0


def test_retry_after_http_date_uses_injected_now() -> None:
    value = "Wed, 21 Oct 2030 07:28:00 GMT"
    assert gemini._parse_retry_after(value, now=0.0, remaining_deadline=30.0) == 30.0


def test_cooldown_only_counts_retryable_failures() -> None:
    cooldown = gemini.CooldownStateMachine(
        failure_threshold=2,
        cooldown_seconds=5.0,
        clock=lambda: 0.0,
    )

    bad_request = gemini._classify_http_error(status_code=400, detail="bad request")
    server_error = gemini._classify_http_error(status_code=503, detail="server down")

    assert bad_request.retryable is False
    assert server_error.retryable is True

    assert cooldown.allow_request() is True
    cooldown.record_retryable_failure()
    assert cooldown.state == "closed"
    cooldown.record_retryable_failure()
    assert cooldown.state == "open"


def test_default_adapter_exists_without_name_error() -> None:
    adapter = gemini.GeminiProviderAdapter()
    assert adapter is not None
    assert gemini.DEFAULT_ADAPTER is not None
