from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from app.investigation import generation
from app.providers import gemini


def client_for(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.anyio
async def test_post_json_retries_503_with_exponential_jitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    statuses = iter([503, 503, 200])
    delays: list[float] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(next(statuses), json={"ok": True})

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    async with client_for(handler) as client:
        response = await gemini.post_json(
            client,
            "https://provider.test/generate",
            {},
            deadline_seconds=10,
            sleep=fake_sleep,
            rng=lambda: 0.5,
        )

    assert response == {"ok": True}
    assert delays == [0.75, 1.5]


@pytest.mark.anyio
async def test_post_json_does_not_retry_http_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(400, text="bad request")

    async with client_for(handler) as client:
        with pytest.raises(RuntimeError, match="HTTP 400: bad request"):
            await gemini.post_json(
                client,
                "https://provider.test/generate",
                {},
                deadline_seconds=10,
            )

    assert calls == 1


@pytest.mark.anyio
async def test_post_json_exhausted_retries_do_not_include_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "secret-api-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="secret-api-key")

    async def no_sleep(delay: float) -> None:
        return None

    async with client_for(handler) as client:
        with pytest.raises(RuntimeError, match="failed after 3 attempts") as error:
            await gemini.post_json(
                client,
                "https://provider.test/generate",
                {},
                deadline_seconds=10,
                sleep=no_sleep,
                rng=lambda: 0.0,
            )

    assert "secret-api-key" not in str(error.value)


@pytest.mark.anyio
async def test_post_json_deadline_raises_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.2)
        return httpx.Response(200, json={"ok": True})

    async with client_for(handler) as client:
        with pytest.raises(TimeoutError):
            await gemini.post_json(
                client,
                "https://provider.test/generate",
                {},
                deadline_seconds=0.01,
            )


@pytest.mark.anyio
async def test_generation_is_responsive_during_slow_provider_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        prompt = body["contents"][0]["parts"][0]["text"]
        if prompt == "slow":
            await asyncio.sleep(0.5)
        return httpx.Response(200, json={"candidates": []})

    monkeypatch.setattr(
        generation,
        "make_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    slow_task = asyncio.create_task(generation.generate_investigation("slow"))
    tick_times: list[float] = []

    async def ticker() -> None:
        while not slow_task.done():
            tick_times.append(asyncio.get_running_loop().time())
            await asyncio.sleep(0.01)

    ticker_task = asyncio.create_task(ticker())
    await asyncio.sleep(0.01)
    fast_started = asyncio.get_running_loop().time()
    await generation.generate_investigation("fast")
    fast_elapsed = asyncio.get_running_loop().time() - fast_started

    assert not slow_task.done()
    assert fast_elapsed < 0.2
    await slow_task
    await ticker_task
    assert max(
        second - first for first, second in zip(tick_times, tick_times[1:])
    ) < 0.2
