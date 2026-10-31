from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

import scripts.investigate as investigate_module
from app.investigation.replay import ReplayRecord
from app.providers.gemini import (
    ProviderAuthError,
    ProviderBadRequestError,
    ProviderError,
    ProviderSafetyBlockedError,
    ProviderSchemaInvalidError,
    ProviderServerError,
)


class FakeSessionContext:
    async def __aenter__(self) -> FakeSessionContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def scalar(self, statement: object) -> SimpleNamespace:
        return SimpleNamespace(id=1)


async def async_none_cache_miss(key: object) -> tuple[None, bool]:
    return None, True


async def async_noop_cache_write(key: object, vector: list[float]) -> None:
    return None


class FakeGraph:
    def __init__(self) -> None:
        self.state: dict[str, Any] | None = None

    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
        self.state = state
        return {
            "evidence_check": {"is_sufficient": True},
            "response_payload": {"candidates": []},
            "diagnosis": "test diagnosis",
            "confidence": "low",
            "cited_chunk_ids": [],
            "retrieval_results": [],
            "model": "test-model",
            "latency_ms": 1,
            "retry_used": False,
            "confidence_calibrated": False,
            "calibration_note": "",
            "tool_calls": [],
            "prompt": "test prompt",
        }


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("limit", "query", "message"),
    [
        (0, "test", "--limit must be between 1 and 20"),
        (21, "test", "--limit must be between 1 and 20"),
        (1, "q" * 2001, "--query must be at most 2000 characters"),
    ],
)
async def test_investigate_repository_rejects_input_caps_before_database(
    monkeypatch: pytest.MonkeyPatch,
    limit: int,
    query: str,
    message: str,
) -> None:
    def unexpected_database_access() -> None:
        raise AssertionError("Database access should not occur for invalid inputs")

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", unexpected_database_access)

    with pytest.raises(ValueError) as error:
        await investigate_module.investigate_repository("test-repo", query, limit=limit)
    assert str(error.value) == message


@pytest.mark.anyio
@pytest.mark.parametrize("limit", [1, 20])
async def test_investigate_repository_accepts_limit_bounds_without_external_services(
    monkeypatch: pytest.MonkeyPatch,
    limit: int,
) -> None:
    fake_graph = FakeGraph()
    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)

    async def fake_embed_text(query: str) -> list[float]:
        return [0.1, 0.2]

    monkeypatch.setattr(investigate_module, "embed_text", fake_embed_text)
    monkeypatch.setattr(
        investigate_module, "create_investigation_graph", lambda calibrator: fake_graph
    )

    result = await investigate_module.investigate_repository(
        "test-repo", "test query", limit=limit, persist=False, temperature=0
    )

    assert result["diagnosis"] == "test diagnosis"
    assert fake_graph.state is not None
    assert fake_graph.state["search_limit"] == limit
    assert fake_graph.state["temperature"] == 0


@pytest.mark.anyio
@pytest.mark.parametrize("persist", [True, False])
async def test_investigate_repository_persists_guard_refusal_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    persist: bool,
) -> None:
    class InsufficientGraph:
        async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
            return {
                "evidence_check": {
                    "is_sufficient": False,
                    "reason": "No vector similarity score was retrieved.",
                },
                "diagnosis": "INSUFFICIENT_EVIDENCE",
                "confidence": "low",
                "cited_chunk_ids": [],
                "retrieval_results": [{"id": 9, "file_path": "source.py"}],
                "model": "test-model",
                "latency_ms": None,
                "retry_used": True,
                "confidence_calibrated": False,
                "calibration_note": "",
                "tool_calls": [{"stage": "widened_retry"}],
            }

    persisted_calls: list[tuple[object, ...]] = []

    async def fake_persist_refusal(
        session: object,
        repository_id: int,
        query: str,
        retrieval_results: list[dict[str, object]],
        tool_call_trace: list[dict[str, object]],
        ingest_run_id: int | None = None,
        replay: ReplayRecord | None = None,
    ) -> SimpleNamespace:
        persisted_calls.append(
            (repository_id, query, retrieval_results, tool_call_trace, ingest_run_id, replay)
        )
        return SimpleNamespace(id=71)

    async def fake_latest_ingest_run_id(session: object, repository_id: int) -> int:
        del session, repository_id
        return 42

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)

    async def fake_embed_text(query: str) -> list[float]:
        return [0.1, 0.2]

    monkeypatch.setattr(investigate_module, "embed_text", fake_embed_text)
    monkeypatch.setattr(
        investigate_module, "create_investigation_graph", lambda calibrator: InsufficientGraph()
    )
    monkeypatch.setattr(investigate_module, "persist_refusal", fake_persist_refusal)
    monkeypatch.setattr(
        investigate_module, "latest_ingest_run_id", fake_latest_ingest_run_id
    )

    result = await investigate_module.investigate_repository(
        "test-repo",
        "question",
        persist=persist,
    )

    assert result["outcome"] == "refused_guard"
    assert result["investigation_id"] == (71 if persist else None)
    assert len(persisted_calls) == (1 if persist else 0)
    if persist:
        assert persisted_calls[0][-2] == 42
        replay = persisted_calls[0][-1]
        assert isinstance(replay, ReplayRecord)
        assert replay.prompt is None
        assert replay.raw_response is None
        assert replay.chunk_records is not None
        assert replay.chunk_records[0]["kept_in_prompt"] is False
        assert replay.trace is not None
        assert replay.trace["outcome"] == "refused_guard"


@pytest.mark.anyio
async def test_investigation_deadline_persists_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    persisted_errors: list[str] = []

    class SlowGraph:
        async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
            await asyncio.Event().wait()
            return state

    async def fake_embed_text(query: str) -> list[float]:
        return [0.1, 0.2]

    async def fake_persist_error(
        session: object,
        repository_id: int,
        query: str,
        error_class: str,
        **kwargs: object,
    ) -> None:
        persisted_errors.append(error_class)

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(investigate_module, "embed_text", fake_embed_text)
    monkeypatch.setattr(
        investigate_module, "create_investigation_graph", lambda calibrator: SlowGraph()
    )
    monkeypatch.setattr(
        investigate_module, "persist_error", fake_persist_error
    )
    monkeypatch.setattr(investigate_module, "INVESTIGATION_DEADLINE_SECONDS", 0.01)

    with pytest.raises(TimeoutError):
        await investigate_module.investigate_repository(
            "test-repo", "question", persist=True
        )

    assert persisted_errors == ["TimeoutError"]


@pytest.mark.anyio
async def test_embedding_failure_audit_records_query_embedding_stage_and_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: list[tuple[str, ReplayRecord | None]] = []
    provider_error = ProviderServerError("provider unavailable", status_code=503)

    async def fail_embedding(query: str) -> list[float]:
        raise provider_error

    async def fake_persist_error(
        session: object,
        repository_id: int,
        query: str,
        error_class: str,
        **kwargs: object,
    ) -> None:
        recorded.append((error_class, kwargs.get("replay")))

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(investigate_module, "embed_text", fail_embedding)
    monkeypatch.setattr(investigate_module, "persist_error", fake_persist_error)

    with pytest.raises(ProviderServerError):
        await investigate_module.investigate_repository(
            "test-repo", "private question", persist=True
        )

    error_class, replay = recorded[0]
    assert error_class == "ProviderServerError"
    assert isinstance(replay, ReplayRecord)
    assert replay.trace is not None
    assert replay.trace["failed_stage"] == "query_embedding"
    assert replay.trace["model"] == investigate_module.GEMINI_MODEL
    assert replay.trace["error_classes"] == ["server_error"]
    assert replay.trace["provider_attempts"][0]["attempt_count"] == 3
    assert "private question" not in repr(replay.trace)


@pytest.mark.anyio
async def test_generation_failure_audit_records_generation_stage_and_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: list[ReplayRecord | None] = []

    class FailedGraph:
        async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
            raise ProviderAuthError("provider credentials rejected")

    async def fake_embed_text(query: str) -> list[float]:
        return [0.1, 0.2]

    async def fake_persist_error(
        session: object,
        repository_id: int,
        query: str,
        error_class: str,
        **kwargs: object,
    ) -> None:
        recorded.append(kwargs.get("replay"))

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(investigate_module, "embed_text", fake_embed_text)
    monkeypatch.setattr(
        investigate_module, "create_investigation_graph", lambda _calibrator: FailedGraph()
    )
    monkeypatch.setattr(investigate_module, "persist_error", fake_persist_error)

    with pytest.raises(ProviderAuthError):
        await investigate_module.investigate_repository(
            "test-repo", "private question", persist=True
        )

    replay = recorded[0]
    assert isinstance(replay, ReplayRecord)
    assert replay.trace is not None
    assert replay.trace["failed_stage"] == "generation"
    assert replay.trace["model"] == investigate_module.GEMINI_GENERATION_MODEL
    assert replay.trace["error_classes"] == ["auth"]
    assert "private question" not in repr(replay.trace)


@pytest.mark.anyio
async def test_generation_unavailable_result_persists_only_evidence_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    retrieval_results = [
        {
            "id": 9,
            "file_path": "source.py",
            "line_start": 3,
            "line_end": 8,
            "rrf_score": 0.04,
            "vector_score": 0.3,
            "content": "SOURCE TEXT MUST NOT LEAVE THE INVESTIGATION FLOW",
        }
    ]
    trace = {
        "failed_stage": "generation",
        "model": investigate_module.GEMINI_GENERATION_MODEL,
        "provider_attempts": [
            {
                "provider": "gemini",
                "model": investigate_module.GEMINI_GENERATION_MODEL,
                "error_class": "server_error",
                "attempt_count": 3,
                "attempt_count_basis": "inferred_from_error_class",
            }
        ],
        "error_classes": ["server_error"],
        "attempt_count": 3,
        "attempt_count_basis": "inferred_from_error_class",
        "elapsed_ms": 400,
        "correlation_id": "test-correlation",
    }

    class UnavailableGraph:
        async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
            return {
                "outcome": "generation_unavailable",
                "unavailable_answer": True,
                "degraded": True,
                "degraded_reason": "generation_unavailable",
                "diagnosis": "",
                "confidence": "not_applicable",
                "cited_chunk_ids": [],
                "claims": [],
                "uncertainty_note": (
                    "Generation unavailable after configured provider retries."
                ),
                "retrieval_results": retrieval_results,
                "retrieved_before_budget": retrieval_results,
                "evidence_check": {
                    "is_sufficient": True,
                    "reason": "Evidence meets the guard threshold.",
                },
                "retry_used": False,
                "tool_calls": [],
                "generation_trace": trace,
            }

    persisted: list[dict[str, object]] = []

    async def fake_embed_text(query: str) -> list[float]:
        return [0.1, 0.2]

    async def fake_persist_generation_unavailable(**kwargs: object) -> SimpleNamespace:
        persisted.append(kwargs)
        return SimpleNamespace(id=91)

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(investigate_module, "embed_text", fake_embed_text)
    monkeypatch.setattr(
        investigate_module,
        "_lookup_query_embedding_cache",
        async_none_cache_miss,
    )
    monkeypatch.setattr(
        investigate_module,
        "_store_query_embedding_cache",
        async_noop_cache_write,
    )
    monkeypatch.setattr(
        investigate_module,
        "create_investigation_graph",
        lambda _calibrator: UnavailableGraph(),
    )
    monkeypatch.setattr(
        investigate_module,
        "persist_generation_unavailable",
        fake_persist_generation_unavailable,
    )

    result = await investigate_module.investigate_repository(
        "test-repo", "question", persist=True
    )

    assert result["outcome"] == "generation_unavailable"
    assert result["investigation_id"] == 91
    assert result["diagnosis"] == ""
    assert result["confidence"] == "not_applicable"
    assert result["evidence"] == [
        {
            "chunk_id": "9",
            "file_path": "source.py",
            "start_line": 3,
            "end_line": 8,
            "rank": 1,
            "rrf_score": 0.04,
            "vector_score": 0.3,
        }
    ]
    assert "content" not in repr(result["evidence"])
    assert persisted[0]["evidence"] == result["evidence"]
    assert persisted[0]["generation_trace"]["failed_stage"] == "generation"
    assert (
        persisted[0]["generation_trace"]["attempt_count_basis"]
        == "inferred_from_error_class"
    )


def test_cli_prints_generation_trace_and_degraded_state_without_raw_text(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = {
        "repository": "test-repo",
        "query": "question",
        "outcome": "generation_unavailable",
        "diagnosis": "",
        "confidence": "not_applicable",
        "unavailable_answer": True,
        "degraded": True,
        "degraded_reason": "generation_unavailable",
        "cited_chunk_ids": [],
        "model": "",
        "latency_ms": None,
        "retry_used": False,
        "confidence_calibrated": False,
        "tool_calls": [],
        "generation_trace": {
            "failed_stage": "generation",
            "raw_text": "SOURCE RESPONSE TEXT MUST NOT PRINT",
        },
        "evidence": [
            {
                "chunk_id": "9",
                "file_path": "source.py",
                "start_line": 3,
                "end_line": 8,
                "rank": 1,
                "rrf_score": 0.04,
                "vector_score": 0.3,
            }
        ],
    }
    monkeypatch.setattr(
        investigate_module,
        "parse_args",
        lambda: SimpleNamespace(repo_name="test-repo", query="question", limit=5),
    )
    def fake_run(coroutine: Any) -> dict[str, object]:
        coroutine.close()
        return result

    monkeypatch.setattr(asyncio, "run", fake_run)

    investigate_module.main()
    output = capsys.readouterr().out

    assert "Outcome: generation_unavailable" in output
    assert "Unavailable answer: True" in output
    assert "Degraded: True" in output
    assert "Generation trace:" in output
    assert "Evidence metadata:" in output
    assert "SOURCE RESPONSE TEXT MUST NOT PRINT" not in output


@pytest.mark.anyio
async def test_cached_query_vector_skips_embedding_and_uses_normal_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_graph = FakeGraph()

    async def cache_hit(key: object) -> tuple[list[float], bool]:
        return [0.2, 0.4], True

    async def embedding_must_not_run(query: str) -> list[float]:
        raise AssertionError("Cache hit must skip provider embedding")

    async def cache_write_must_not_run(key: object, vector: list[float]) -> None:
        raise AssertionError("Cache hit must not write")

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(investigate_module, "_lookup_query_embedding_cache", cache_hit)
    monkeypatch.setattr(investigate_module, "embed_text", embedding_must_not_run)
    monkeypatch.setattr(
        investigate_module, "_store_query_embedding_cache", cache_write_must_not_run
    )
    monkeypatch.setattr(
        investigate_module,
        "create_investigation_graph",
        lambda _calibrator: fake_graph,
    )

    result = await investigate_module.investigate_repository(
        "test-repo", "question", persist=False
    )

    assert result["outcome"] == "answered"
    assert fake_graph.state is not None
    assert fake_graph.state["query_embedding"] == [0.2, 0.4]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "retrieval_results",
    [
        [
            {
                "id": 9,
                "file_path": "source.py",
                "line_start": 3,
                "line_end": 8,
                "content": "SOURCE TEXT MUST NOT BE RETURNED",
                "score": 0.5,
                "fts_score": 0.5,
                "rrf_score": None,
                "vector_score": None,
            }
        ],
        [],
    ],
)
async def test_embedding_availability_failure_uses_lexical_only_without_guard_or_generation(
    monkeypatch: pytest.MonkeyPatch,
    retrieval_results: list[dict[str, object]],
) -> None:
    provider_error = ProviderServerError("embedding unavailable", status_code=503)
    persisted: list[dict[str, object]] = []
    lexical_calls: list[tuple[int, str, int]] = []

    async def cache_miss(key: object) -> tuple[None, bool]:
        return None, True

    async def fail_embedding(query: str) -> list[float]:
        raise provider_error

    async def fake_lexical_search(
        session: object,
        repository_id: int,
        query: str,
        limit: int,
    ) -> list[dict[str, object]]:
        lexical_calls.append((repository_id, query, limit))
        return retrieval_results

    async def unexpected_cache_write(key: object, vector: list[float]) -> None:
        raise AssertionError("Failed provider embedding must not write cache")

    async def fake_persist(**kwargs: object) -> SimpleNamespace:
        persisted.append(kwargs)
        return SimpleNamespace(id=92)

    def graph_must_not_run(_calibrator: object) -> None:
        raise AssertionError("Degraded lexical-only path must not run graph/guard")

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(investigate_module, "_lookup_query_embedding_cache", cache_miss)
    monkeypatch.setattr(investigate_module, "embed_text", fail_embedding)
    monkeypatch.setattr(
        investigate_module,
        "search_degraded_lexical_only",
        fake_lexical_search,
    )
    monkeypatch.setattr(
        investigate_module,
        "_store_query_embedding_cache",
        unexpected_cache_write,
    )
    monkeypatch.setattr(
        investigate_module,
        "persist_degraded_investigation",
        fake_persist,
    )
    monkeypatch.setattr(
        investigate_module,
        "create_investigation_graph",
        graph_must_not_run,
    )

    result = await investigate_module.investigate_repository(
        "test-repo", "question", limit=4, persist=True
    )

    assert result["outcome"] == "embedding_unavailable"
    assert result["unavailable_answer"] is True
    assert result["degraded"] is True
    assert result["degraded_reason"] == "embedding_unavailable"
    assert result["diagnosis"] == ""
    assert result["confidence"] == "not_applicable"
    assert result["cited_chunk_ids"] == []
    assert result["claims"] == []
    assert result["evidence_check"] == {
        "is_sufficient": None,
        "reason": "not evaluated: no query embedding",
        "best_rrf_score": None,
        "best_vector_score": None,
    }
    expected_evidence = (
        [
            {
                "chunk_id": "9",
                "file_path": "source.py",
                "start_line": 3,
                "end_line": 8,
                "rank": 1,
                "rrf_score": None,
                "vector_score": None,
            }
        ]
        if retrieval_results
        else []
    )
    assert result["evidence"] == expected_evidence
    for evidence_item in result["evidence"]:
        assert set(evidence_item) == {
            "chunk_id",
            "file_path",
            "start_line",
            "end_line",
            "rank",
            "rrf_score",
            "vector_score",
        }
    assert "content" not in repr(result["evidence"])
    assert lexical_calls == [(1, "question", 4)]
    assert persisted[0]["outcome"] == "embedding_unavailable"
    assert persisted[0]["degraded_reason"] == "embedding_unavailable"
    assert persisted[0]["generation_trace"]["failed_stage"] == "query_embedding"
    assert persisted[0]["generation_trace"]["model"] == investigate_module.GEMINI_MODEL
    assert persisted[0]["generation_trace"]["retrieval_mode"] == "lexical_only"
    assert persisted[0]["generation_trace"]["cache"]["miss"] is True
    assert persisted[0]["generation_trace"]["guard_ran"] is False
    assert persisted[0]["generation_trace"]["result_count"] == len(retrieval_results)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "error",
    [
        ProviderAuthError("unauthorized"),
        ProviderBadRequestError("bad request"),
        ProviderSafetyBlockedError("blocked"),
        ProviderSchemaInvalidError("invalid vector"),
    ],
)
async def test_nonavailability_embedding_errors_remain_explicit(
    monkeypatch: pytest.MonkeyPatch,
    error: ProviderError,
) -> None:
    persisted_errors: list[str] = []

    async def cache_miss(key: object) -> tuple[None, bool]:
        return None, True

    async def fail_embedding(query: str) -> list[float]:
        raise error

    async def unexpected_lexical(*args: object, **kwargs: object) -> list[object]:
        raise AssertionError("Non-availability errors must not use lexical fallback")

    async def fake_persist_error(
        session: object,
        repository_id: int,
        query: str,
        error_class: str,
        **kwargs: object,
    ) -> None:
        persisted_errors.append(error_class)

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(investigate_module, "_lookup_query_embedding_cache", cache_miss)
    monkeypatch.setattr(investigate_module, "embed_text", fail_embedding)
    monkeypatch.setattr(
        investigate_module,
        "search_degraded_lexical_only",
        unexpected_lexical,
    )
    monkeypatch.setattr(investigate_module, "persist_error", fake_persist_error)

    with pytest.raises(type(error)):
        await investigate_module.investigate_repository(
            "test-repo", "question", persist=True
        )

    assert persisted_errors == [type(error).__name__]


@pytest.mark.anyio
async def test_embedding_availability_failure_does_not_degrade_when_cache_lookup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_error = ProviderServerError("embedding unavailable", status_code=503)

    async def cache_failure(key: object) -> tuple[None, bool]:
        return None, False

    async def fail_embedding(query: str) -> list[float]:
        raise provider_error

    async def unexpected_lexical(*args: object, **kwargs: object) -> list[object]:
        raise AssertionError("An unreadable cache is not a confirmed cache miss")

    async def fake_persist_error(
        session: object,
        repository_id: int,
        query: str,
        error_class: str,
        **kwargs: object,
    ) -> None:
        return None

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(investigate_module, "_lookup_query_embedding_cache", cache_failure)
    monkeypatch.setattr(investigate_module, "embed_text", fail_embedding)
    monkeypatch.setattr(
        investigate_module,
        "search_degraded_lexical_only",
        unexpected_lexical,
    )
    monkeypatch.setattr(investigate_module, "persist_error", fake_persist_error)

    with pytest.raises(ProviderServerError):
        await investigate_module.investigate_repository(
            "test-repo", "question", persist=True
        )
