from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from app.providers.reranker import RerankResponse, VoyageRerankFailure
from evaluation.studies.reranker.reranker_experiment import (
    PIN_PATH,
    V1_REPOSITORIES,
    analyze_experiment,
    apply_reranked_ids,
    canonical_sha256,
    decide_reranker,
    load_pin,
    require_development,
    rerank_candidates,
    write_json_atomic,
    write_text_atomic,
)

PIN = {
    "model_identifier": "rerank-test-model",
    "api_version": "v1",
    "model_settings": {},
    "request_limits": {
        "max_candidates": 20,
        "top_k": 20,
        "truncation": True,
        "timeout_seconds": 10,
        "max_attempts": 2,
    },
    "retry_policy": {
        "strategy": "exponential",
        "initial_delay_seconds": 1,
        "max_delay_seconds": 8,
        "respect_retry_after": True,
    },
    "pricing": {
        "usd_per_million_tokens": 1.0,
        "source_url": "https://example.invalid/pricing",
    },
}


def _candidate_data() -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    repositories = []
    fixture_chunks_by_repo = {}
    hashes = {}
    for repo_id in V1_REPOSITORIES:
        question_id = f"{repo_id}-question"
        candidates = [
            {
                "chunk_id": f"{repo_id}/src/file-{index}.py:{index}-{index}",
                "file_path": f"src/file-{index}.py",
                "line_start": index,
                "line_end": index,
                "text": f"candidate {repo_id} {index}",
            }
            for index in range(1, 6)
        ]
        span = {"file_path": "src/file-3.py", "line_start": 3, "line_end": 3}
        digest = canonical_sha256(candidates)
        hashes[f"{repo_id}:{question_id}"] = digest
        repositories.append(
            {
                "id": repo_id,
                "questions": [
                    {
                        "id": question_id,
                        "question": "Where is the target?",
                        "category": "direct",
                        "relevant_spans": [span],
                        "guard_refused": False,
                        "best_vector_distance": 0.1,
                        "candidate_set_sha256": digest,
                        "baseline_candidates": candidates,
                    }
                ],
            }
        )
        fixture_chunks_by_repo[repo_id] = [
            {
                "file_path": candidate["file_path"],
                "line_start": candidate["line_start"],
                "line_end": candidate["line_end"],
                "content": candidate["text"],
            }
            for candidate in candidates
        ]
    return (
        {
            "metadata": {
                "dataset_version": "v1",
                "split": "development",
                "repository_ids": list(V1_REPOSITORIES),
                "guard_threshold": 0.5,
                "candidate_set_sha256": hashes,
                "reranker_pin": PIN,
            },
            "repositories": repositories,
        },
        fixture_chunks_by_repo,
    )


class FailingProvider:
    async def rerank(self, *_args: Any, **_kwargs: Any) -> RerankResponse:
        del _args, _kwargs
        raise VoyageRerankFailure(
            "server_error",
            status_code=503,
            attempts=2,
            latency_ms=20,
            attempt_records=({"attempt": 1, "status_code": 503},),
        )


class TimedProvider:
    def __init__(self, clock: Any) -> None:
        self.clock = clock
        self.starts: list[float] = []

    async def rerank(self, *_args: Any, **_kwargs: Any) -> RerankResponse:
        del _args, _kwargs
        self.starts.append(self.clock.now)
        self.clock.now += 0.125
        return RerankResponse(
            indices=(0, 1, 2, 3, 4),
            response={"data": []},
            token_count=100,
            latency_ms=125,
            attempt_count=1,
        )


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def time(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += seconds


class ReplacingProvider:
    async def rerank(self, *_args: Any, **_kwargs: Any) -> RerankResponse:
        del _args, _kwargs
        return RerankResponse(
            indices=(0,),
            response={"data": []},
            token_count=4,
            latency_ms=10,
            attempt_count=1,
        )


def _good_decision_inputs() -> dict[str, Any]:
    return {
        "mrr": {"treatment_minus_baseline": 0.02, "bootstrap_95": [0.001, 0.04]},
        "guard_baseline": {
            "guard.false_accept_rate": 0.1,
            "guard.false_refusal_rate": 0.2,
            "guard.correct_refusal_rate": 0.8,
        },
        "guard_treatment": {
            "guard.false_accept_rate": 0.1,
            "guard.false_refusal_rate": 0.22,
            "guard.correct_refusal_rate": 0.78,
        },
        "latency": {"p50_ms": 500, "p95_ms": 1500},
        "cost": {"cost_per_1000_queries_usd": 0.0},
    }


def test_decision_rule_accepts_inclusive_registered_boundaries() -> None:
    result = decide_reranker(**_good_decision_inputs())
    assert result == {"decision": "KEEP", "failing_conditions": []}


@pytest.mark.parametrize(
    ("field", "replacement", "expected"),
    [
        ("mrr", {"treatment_minus_baseline": 0.019}, "MRR@5 improvement"),
        ("mrr", {"bootstrap_95": [0.0, 0.04]}, "interval lower bound"),
        (
            "guard_treatment",
            {"guard.false_accept_rate": 0.100001},
            "guard.false_accept_rate",
        ),
        (
            "guard_treatment",
            {"guard.false_refusal_rate": 0.220001},
            "guard.false_refusal_rate",
        ),
        (
            "guard_treatment",
            {"guard.correct_refusal_rate": 0.779999},
            "guard.correct_refusal_rate",
        ),
        ("latency", {"p50_ms": 500.001}, "median latency"),
        ("latency", {"p95_ms": 1500.001}, "p95 latency"),
        ("cost", {"cost_per_1000_queries_usd": None}, "cost per 1,000"),
    ],
)
def test_decision_rule_rejects_each_failed_gate(
    field: str,
    replacement: dict[str, Any],
    expected: str,
) -> None:
    inputs = _good_decision_inputs()
    inputs[field].update(replacement)
    result = decide_reranker(**inputs)
    assert result["decision"] == "REJECT"
    assert any(expected in failure for failure in result["failing_conditions"])


def test_analysis_reports_hand_calculated_mrr_and_paired_differences() -> None:
    data, corpora = _candidate_data()
    for repository in data["repositories"]:
        question = repository["questions"][0]
        baseline = question["baseline_candidates"]
        question["treatment_candidates"] = [baseline[2], baseline[0], baseline[1], *baseline[3:]]
        question["rerank"] = {
            "response": {"data": []},
            "attempts": [],
            "latency_ms": 100,
            "attempt_count": 1,
            "token_count": 100,
            "estimated_cost_usd": 0.0001,
            "fallback_used": False,
            "error": None,
        }

    report = analyze_experiment(data, corpora)
    mrr = report["pooled"]["mrr_at_5"]
    assert mrr["baseline"] == pytest.approx(1 / 3)
    assert mrr["treatment"] == pytest.approx(1.0)
    assert mrr["treatment_minus_baseline"] == pytest.approx(2 / 3)
    assert mrr["bootstrap_95"] == pytest.approx([2 / 3, 2 / 3])
    assert all(
        row["differences"]["mrr_at_5"] == pytest.approx(2 / 3) for row in report["per_question"]
    )
    assert report["pooled"]["hit_at_5"]["paired_comparison"] == {
        "wins": 0,
        "losses": 0,
        "ties": 3,
        "p_value": 1.0,
    }


def test_rerank_interval_defaults_to_zero_without_sleep() -> None:
    data, _ = _candidate_data()
    clock = FakeClock()
    provider = TimedProvider(clock)
    sleeps: list[float] = []

    async def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        await clock.sleep(seconds)

    result = asyncio.run(
        rerank_candidates(data, PIN, provider, sleep=record_sleep, clock=clock.time)
    )

    assert sleeps == []
    assert result["metadata"]["min_interval_seconds"] == 0
    assert len(provider.starts) == 3


def test_positive_rerank_interval_sleeps_between_requests_outside_latency() -> None:
    data, _ = _candidate_data()
    clock = FakeClock()
    provider = TimedProvider(clock)
    sleeps: list[float] = []

    async def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        await clock.sleep(seconds)

    result = asyncio.run(
        rerank_candidates(
            data,
            PIN,
            provider,
            min_interval_seconds=45,
            sleep=record_sleep,
            clock=clock.time,
        )
    )

    assert len(sleeps) == 2
    assert sleeps == pytest.approx([44.875, 44.875])
    assert provider.starts[0] == 0
    assert all(
        later - earlier >= 45 for earlier, later in zip(provider.starts, provider.starts[1:])
    )
    assert result["metadata"]["min_interval_seconds"] == 45
    assert all(
        question["rerank"]["latency_ms"] == 125
        for repository in result["repositories"]
        for question in repository["questions"]
    )


def test_negative_rerank_interval_is_rejected() -> None:
    data, _ = _candidate_data()
    with pytest.raises(ValueError, match="finite non-negative"):
        asyncio.run(rerank_candidates(data, PIN, FailingProvider(), min_interval_seconds=-1))


def test_rerank_failure_uses_baseline_order_and_is_counted() -> None:
    data, _ = _candidate_data()
    result = asyncio.run(rerank_candidates(data, PIN, FailingProvider()))
    assert result["metadata"]["rerank_failure_count"] == 3
    for source_repo, result_repo in zip(data["repositories"], result["repositories"]):
        source_question = source_repo["questions"][0]
        result_question = result_repo["questions"][0]
        assert result_question["treatment_candidates"] == source_question["baseline_candidates"]
        assert result_question["rerank"]["fallback_used"] is True
        assert result_question["rerank"]["error"]["status_code"] == 503
        assert result_question["rerank"]["attempts"] == [{"attempt": 1, "status_code": 503}]


def test_reranker_cannot_change_candidate_set() -> None:
    data, _ = _candidate_data()
    with pytest.raises(AssertionError, match="different candidate set"):
        asyncio.run(rerank_candidates(data, PIN, ReplacingProvider()))


def test_candidate_set_helper_rejects_text_or_identifier_changes() -> None:
    candidates = [{"chunk_id": "one", "text": "unchanged"}]
    with pytest.raises(AssertionError, match="different candidate set"):
        apply_reranked_ids(candidates, ["missing"])


def test_held_out_split_is_refused() -> None:
    with pytest.raises(ValueError, match="other than development"):
        require_development("held_out")

    data, _ = _candidate_data()
    data["metadata"]["split"] = "held_out"
    with pytest.raises(ValueError, match="other than development"):
        asyncio.run(rerank_candidates(data, PIN, FailingProvider()))


def test_missing_pin_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pin is missing"):
        load_pin(tmp_path / "missing-pin.json")
    assert PIN_PATH.name == "pin.json"


def test_json_output_is_idempotent(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    report = {"metadata": {"split": "development"}, "value": [1, 2, 3]}
    write_json_atomic(output, report)
    first = output.read_bytes()
    write_json_atomic(output, report)
    assert output.read_bytes() == first
    assert not output.with_name(output.name + ".tmp").exists()
    markdown = tmp_path / "report.md"
    write_text_atomic(markdown, "# Report\n")
    first_markdown = markdown.read_bytes()
    write_text_atomic(markdown, "# Report\n")
    assert markdown.read_bytes() == first_markdown
    assert first_markdown == b"# Report\n"
