from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api as api_module
from app.api_security import rate_limiter
from app.config import settings
from app.db.models import Investigation, Repository
from app.main import app

TEST_SECRET = "phase9-test-secret-not-a-real-credential"
HEADERS = {"X-API-Secret": TEST_SECRET}


class FakeResult:
    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows

    def all(self) -> list[Any]:
        return self.rows

    def scalars(self) -> FakeResult:
        return self


class FakeSession:
    def __init__(
        self,
        entities: dict[tuple[type, int], Any] | None = None,
        rows: list[Any] | None = None,
    ) -> None:
        self.entities = entities or {}
        self.rows = rows or []

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, model: type, identifier: int) -> Any:
        return self.entities.get((model, identifier))

    async def execute(self, statement: object) -> FakeResult:
        return FakeResult(self.rows)


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_protection_secret", TEST_SECRET)
    rate_limiter.reset()
    with TestClient(app) as client:
        yield client
    rate_limiter.reset()


def sufficient_pipeline_result() -> dict[str, object]:
    return {
        "investigation_id": 123,
        "repository": "incidentweave-eval",
        "query": "What chunk size is configured?",
        "diagnosis": "The chunk size is 60 lines.",
        "confidence": "medium",
        "confidence_calibrated": True,
        "cited_chunk_ids": ["7"],
        "evidence_check": {
            "is_sufficient": True,
            "reason": "Evidence strength meets both thresholds.",
            "best_rrf_score": 0.04,
            "best_vector_score": 0.25,
        },
        "retry_used": False,
        "tool_calls": [{"tool": "hybrid_search", "stage": "initial"}],
        "model": "gemini-3.5-flash-lite",
        "latency_ms": 1200,
    }


def test_post_investigation_success_response_shape(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, int, bool]] = []

    async def fake_investigate(
        repository_name: str,
        query: str,
        limit: int,
        persist: bool,
    ) -> dict[str, object]:
        calls.append((repository_name, query, limit, persist))
        return sufficient_pipeline_result()

    monkeypatch.setattr(api_module, "investigate_repository", fake_investigate)

    response = api_client.post(
        "/investigations",
        headers=HEADERS,
        json={"repository_name": "incidentweave-eval", "query": "What chunk size is configured?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["investigation_id"] == 123
    assert body["confidence"] == "medium"
    assert body["raw_confidence"] == "high"
    assert body["evidence_check"]["best_rrf_score"] == 0.04
    assert body["evidence_check"]["best_vector_score"] == 0.25
    assert body["evaluation_note"].startswith("Phase 8 evaluated 24 questions")
    assert calls == [
        ("incidentweave-eval", "What chunk size is configured?", 5, True)
    ]


def test_post_unknown_repository_uses_standard_404(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_investigate(*args: Any, **kwargs: Any) -> dict[str, object]:
        raise ValueError("Repository not found: missing")

    monkeypatch.setattr(api_module, "investigate_repository", fake_investigate)

    response = api_client.post(
        "/investigations",
        headers=HEADERS,
        json={"repository_name": "missing", "query": "test"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "repository_not_found", "message": "Repository not found."}
    }


def test_post_upstream_failure_returns_sanitized_502(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_investigate(*args: Any, **kwargs: Any) -> dict[str, object]:
        raise RuntimeError("provider detail must not be exposed")

    monkeypatch.setattr(api_module, "investigate_repository", fake_investigate)

    response = api_client.post(
        "/investigations",
        headers=HEADERS,
        json={"repository_name": "incidentweave-eval", "query": "test"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "upstream_failure",
            "message": "The investigation provider failed after its retries.",
        }
    }
    assert "provider detail" not in response.text


def test_post_invalid_limit_returns_sanitized_422(api_client: TestClient) -> None:
    response = api_client.post(
        "/investigations",
        headers=HEADERS,
        json={"repository_name": "incidentweave-eval", "query": "test", "limit": 0},
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "validation_error", "message": "Request validation failed."}
    }
    assert "input" not in response.text


def test_health_is_open_and_missing_secret_is_rejected(api_client: TestClient) -> None:
    health = api_client.get("/health")
    missing_secret = api_client.get("/repositories")
    wrong_secret = api_client.get(
        "/repositories", headers={"X-API-Secret": "wrong-test-secret"}
    )

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    expected_error = {
        "error": {
            "code": "unauthorized",
            "message": "A valid X-API-Secret header is required.",
        }
    }
    assert missing_secret.status_code == 401
    assert missing_secret.json() == expected_error
    assert wrong_secret.status_code == 401
    assert wrong_secret.json() == expected_error


def test_rate_limit_returns_429_after_ten_valid_requests(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repositories = [("incidentweave-eval", 70, 70)]
    monkeypatch.setattr(api_module, "AsyncSessionLocal", lambda: FakeSession(rows=repositories))

    responses = [api_client.get("/repositories", headers=HEADERS) for _ in range(11)]

    assert [response.status_code for response in responses[:10]] == [200] * 10
    assert responses[10].status_code == 429
    assert responses[10].json() == {
        "error": {
            "code": "rate_limit_exceeded",
            "message": "Request limit exceeded. Try again later.",
        }
    }


def test_get_investigation_and_missing_id(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    investigation = SimpleNamespace(
        id=19,
        repository_id=34,
        query="What chunk size does repository ingestion use?",
        response="Repository ingestion uses 60 lines.",
        confidence="medium",
        model="gemini-3.5-flash-lite",
        latency_ms=1361,
    )
    repository = SimpleNamespace(id=34, name="incidentweave-eval")
    audit = SimpleNamespace(
        investigation_id=19,
        tool_calls={
            "attempts": [
                {
                    "tool": "hybrid_search",
                    "stage": "initial",
                    "outcome": {
                        "sufficient": True,
                        "reason": "Evidence strength meets both thresholds.",
                        "best_rrf_score": 0.04,
                        "best_vector_score": 0.25,
                    },
                }
            ],
            "cited_chunk_ids": ["7"],
        },
    )
    session = FakeSession(
        entities={(Investigation, 19): investigation, (Repository, 34): repository},
        rows=[audit],
    )
    monkeypatch.setattr(api_module, "AsyncSessionLocal", lambda: session)

    found = api_client.get("/investigations/19", headers=HEADERS)
    missing = api_client.get("/investigations/999999", headers=HEADERS)

    assert found.status_code == 200
    assert found.json()["diagnosis"] == investigation.response
    assert found.json()["cited_chunk_ids"] == ["7"]
    assert found.json()["evidence_check"]["best_rrf_score"] == 0.04
    assert found.json()["evaluation_note"].startswith("Phase 8 evaluated 24 questions")
    assert missing.status_code == 404
    assert missing.json() == {
        "error": {"code": "investigation_not_found", "message": "Investigation not found."}
    }


def test_get_investigation_uses_last_grep_attempt_for_evidence_check(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    investigation = SimpleNamespace(
        id=20,
        repository_id=34,
        query="What does this error indicate?",
        response="The error is handled by the fallback.",
        confidence="medium",
        model="gemini-3.5-flash-lite",
        latency_ms=1200,
    )
    repository = SimpleNamespace(id=34, name="incidentweave-eval")
    audit = SimpleNamespace(
        investigation_id=20,
        tool_calls={
            "attempts": [
                {
                    "tool": "hybrid_search",
                    "stage": "widened_retry",
                    "outcome": {
                        "sufficient": False,
                        "reason": "No vector similarity score was retrieved.",
                        "best_rrf_score": 0.01,
                        "best_vector_score": None,
                    },
                },
                {
                    "tool": "grep_search",
                    "stage": "literal_fallback",
                    "outcome": {
                        "sufficient": True,
                        "reason": "Literal grep found matching evidence.",
                        "match_count": 1,
                    },
                },
            ],
            "cited_chunk_ids": ["7"],
        },
    )
    session = FakeSession(
        entities={(Investigation, 20): investigation, (Repository, 34): repository},
        rows=[audit],
    )
    monkeypatch.setattr(api_module, "AsyncSessionLocal", lambda: session)

    response = api_client.get("/investigations/20", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["evidence_check"] == {
        "is_sufficient": True,
        "reason": "Literal grep found matching evidence.",
        "best_rrf_score": None,
        "best_vector_score": None,
    }


def test_list_repositories_returns_chunk_and_embedding_counts(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [("incidentweave-eval", 70, 70), ("incidentweave-local", 72, 70)]
    monkeypatch.setattr(api_module, "AsyncSessionLocal", lambda: FakeSession(rows=rows))

    response = api_client.get("/repositories", headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == [
        {"name": "incidentweave-eval", "chunk_count": 70, "embedded_chunk_count": 70},
        {"name": "incidentweave-local", "chunk_count": 72, "embedded_chunk_count": 70},
    ]
