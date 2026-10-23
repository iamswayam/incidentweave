from __future__ import annotations

import json
from urllib.request import Request

from app.investigation import generation
from scripts import embed_chunks


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def _assert_key_is_in_header(req: Request) -> None:
    assert "key=" not in req.full_url
    assert "test-key" not in req.full_url
    api_key_header = next(
        value
        for name, value in req.headers.items()
        if name.lower() == "x-goog-api-key"
    )
    assert api_key_header == "test-key"


def test_generate_investigation_sends_api_key_in_header(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    captured_requests: list[Request] = []

    def fake_urlopen(req: Request, timeout: float):
        captured_requests.append(req)
        return _FakeResponse({"candidates": []})

    monkeypatch.setattr(generation.request, "urlopen", fake_urlopen)

    generation.generate_investigation("question")

    _assert_key_is_in_header(captured_requests[0])


def test_embed_text_sends_api_key_in_header(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    captured_requests: list[Request] = []

    def fake_urlopen(req: Request, timeout: float):
        captured_requests.append(req)
        return _FakeResponse({"embedding": {"values": [0.0] * 768}})

    monkeypatch.setattr(embed_chunks.request, "urlopen", fake_urlopen)

    embedding = embed_chunks.embed_text("text")

    assert len(embedding) == 768
    _assert_key_is_in_header(captured_requests[0])
