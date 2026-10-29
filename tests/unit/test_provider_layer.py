from __future__ import annotations

import asyncio
import json

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
        (400, "request timeout while validating", "bad_request", False),
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
async def test_rate_limiter_uses_rpm_window_and_concurrency() -> None:
    now = 0.0
    admitted_at: list[float] = []

    async def fake_sleep(delay: float) -> None:
        nonlocal now
        now += delay

    limiter = gemini.AsyncRateLimiter(
        rpm=2,
        clock=lambda: now,
        sleep=fake_sleep,
    )

    async def acquire_and_record() -> None:
        await limiter.acquire(tokens=1)
        admitted_at.append(now)

    await asyncio.gather(*(acquire_and_record() for _ in range(5)))

    assert len(admitted_at) == 5
    for window_start in admitted_at:
        requests_in_window = sum(
            window_start <= timestamp < window_start + 60
            for timestamp in admitted_at
        )
        assert requests_in_window <= 2


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
async def test_half_open_allows_one_probe_only() -> None:
    now = 0.0
    cooldown = gemini.CooldownStateMachine(
        failure_threshold=1,
        cooldown_seconds=10.0,
        clock=lambda: now,
    )

    cooldown.state = "open"
    cooldown.cooldown_until = 0.0
    now = 10.0

    assert cooldown.allow_request() is True
    assert cooldown._probe_in_flight is True
    assert cooldown.allow_request() is False

    cooldown.record_success()
    assert cooldown.state == "closed"
    assert cooldown._probe_in_flight is False


@pytest.mark.anyio
async def test_failed_half_open_probe_reopens_cooldown() -> None:
    now = 0.0
    cooldown = gemini.CooldownStateMachine(
        failure_threshold=1,
        cooldown_seconds=10.0,
        clock=lambda: now,
    )
    cooldown.state = "open"
    cooldown.cooldown_until = 0.0
    now = 10.0

    assert cooldown.allow_request() is True
    assert cooldown.allow_request() is False
    cooldown.record_retryable_failure()
    assert cooldown.state == "open"
    assert cooldown._probe_in_flight is False
    assert cooldown.allow_request() is False

    now = 20.0
    assert cooldown.allow_request() is True
    assert cooldown.state == "half-open"


@pytest.mark.anyio
async def test_guarded_post_json_uses_default_adapter_and_blocks_open_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, str]] = []
    transport = httpx.MockTransport(
        lambda request: calls.append(
            (request.method, request.url.raw_path.decode(), request.content.decode())
        )
        or httpx.Response(200, json={"ok": True})
    )

    cooldown = gemini.CooldownStateMachine(
        failure_threshold=1,
        cooldown_seconds=10.0,
        clock=lambda: 0.0,
    )
    cooldown.state = "open"
    cooldown.cooldown_until = 10.0
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini.DEFAULT_ADAPTER, "cooldown", cooldown)
    monkeypatch.setattr(
        generation,
        "make_client",
        lambda: httpx.AsyncClient(transport=transport),
    )
    monkeypatch.setattr(
        embed_chunks,
        "make_client",
        lambda: httpx.AsyncClient(transport=transport),
    )

    with pytest.raises(gemini.ProviderRateLimitedError):
        await generation.generate_investigation("question")
    with pytest.raises(gemini.ProviderRateLimitedError):
        await embed_chunks.embed_text("text")
    with pytest.raises(gemini.ProviderRateLimitedError):
        await embed_chunks.embed_texts(["a", "b"])

    assert calls == []


@pytest.mark.anyio
async def test_adapter_uses_legacy_request_shape_for_generation_and_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
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

    assert [str(request.url) for request in requests] == [
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-3.5-flash-lite:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-embedding-001:embedContent",
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-embedding-001:batchEmbedContents",
    ]
    assert all(request.headers["x-goog-api-key"] == "test-key" for request in requests)
    assert [json.loads(request.content) for request in requests] == [
        {
            "contents": [{"parts": [{"text": "question"}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": generation.RESPONSE_SCHEMA,
            },
        },
        {
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": "text"}]},
            "outputDimensionality": 768,
        },
        {
            "requests": [
                {
                    "model": "models/gemini-embedding-001",
                    "content": {"parts": [{"text": text}]},
                    "outputDimensionality": 768,
                }
                for text in ("a", "b")
            ]
        },
    ]


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


@pytest.mark.anyio
async def test_estimated_tokens_are_passed_to_limiter_and_tpm_is_enforced() -> None:
    seen: dict[str, float] = {}
    async def fake_sleep(delay: float) -> None:
        return None

    async def fake_acquire(*, tokens: float) -> None:
        seen["tokens"] = tokens

    async def fake_post_json(*args: object, **kwargs: object) -> dict[str, object]:
        return {"ok": True}

    adapter = gemini.GeminiProviderAdapter(
        rate_limiter=gemini.AsyncRateLimiter(
            tpm=5,
            clock=lambda: 0.0,
            sleep=fake_sleep,
        ),
        cooldown=gemini.CooldownStateMachine(
            failure_threshold=2,
            cooldown_seconds=5.0,
            clock=lambda: 0.0,
        ),
        post_json_fn=fake_post_json,
    )
    adapter.rate_limiter.acquire = fake_acquire

    await adapter.post_json(
        httpx.AsyncClient(),
        "https://example.test",
        {"message": "hello world!"},
        deadline_seconds=10,
    )

    assert seen["tokens"] == max(1, len('{"message": "hello world!"}') // 4)


@pytest.mark.anyio
async def test_estimated_tokens_trigger_tpm_wait() -> None:
    now = 0.0
    request_times: list[float] = []
    payload = {"message": "hello world!"}
    estimated_tokens = max(1, len(json.dumps(payload)) // 4)

    async def fake_sleep(delay: float) -> None:
        nonlocal now
        now += delay

    async def fake_post_json(*args: object, **kwargs: object) -> dict[str, object]:
        request_times.append(now)
        return {"ok": True}

    adapter = gemini.GeminiProviderAdapter(
        rate_limiter=gemini.AsyncRateLimiter(
            tpm=estimated_tokens + 1,
            clock=lambda: now,
            sleep=fake_sleep,
        ),
        cooldown=gemini.CooldownStateMachine(),
        post_json_fn=fake_post_json,
    )

    for _ in range(2):
        await adapter.post_json(
            httpx.AsyncClient(),
            "https://example.test",
            payload,
            deadline_seconds=10,
        )

    assert len(request_times) == 2
    assert request_times[1] - request_times[0] >= 60


@pytest.mark.anyio
async def test_non_retryable_error_closes_cooldown_and_timeout_counts_as_retryable() -> None:
    cooldown = gemini.CooldownStateMachine(
        failure_threshold=2,
        cooldown_seconds=5.0,
        clock=lambda: 0.0,
    )
    adapter = gemini.GeminiProviderAdapter(
        cooldown=cooldown,
        rate_limiter=gemini.AsyncRateLimiter(),
    )

    async def fail_400(*args: object, **kwargs: object) -> dict[str, object]:
        raise gemini.ProviderBadRequestError("bad request")

    async def fail_timeout(*args: object, **kwargs: object) -> dict[str, object]:
        raise TimeoutError("deadline")

    adapter._post_json_fn = fail_400
    with pytest.raises(gemini.ProviderBadRequestError):
        await adapter.post_json(
            httpx.AsyncClient(),
            "https://example.test",
            {"a": 1},
            deadline_seconds=10,
        )
    assert cooldown.state == "closed"

    adapter._post_json_fn = fail_timeout
    with pytest.raises(TimeoutError):
        await adapter.post_json(
            httpx.AsyncClient(),
            "https://example.test",
            {"a": 1},
            deadline_seconds=10,
        )
    assert cooldown.state == "closed"
    assert cooldown.consecutive_failures == 1


def test_default_adapter_exists_without_name_error() -> None:
    adapter = gemini.GeminiProviderAdapter()
    assert adapter is not None
    assert gemini.DEFAULT_ADAPTER is not None
