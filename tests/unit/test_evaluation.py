from __future__ import annotations

import asyncio
import hashlib
import shutil
from pathlib import Path

import pytest

from app.investigation.parsing import extract_generation_trace
from evaluation.corpus import export_snapshot
from evaluation.golden import load_golden_set, validate_golden_set, validate_index_labels
from evaluation.metrics import (
    abstention_kind,
    answer_screen,
    citation_summary,
    classify_outcome_v2,
    distance_sweep,
    guard_confusion,
    guard_diagnostics,
    hit_at_k,
    is_refused,
    is_relevant,
    mean_reciprocal_rank,
    retrieval_summary,
    value_distribution,
)
from evaluation.runner import (
    classify_outcome_v2_for_records,
    classify_outcomes,
    resolve_corpus_sha,
    run_pipeline_once,
)
from scripts.ingest_repo import chunk_lines, iter_python_files


def result(file_path: str, content: str) -> dict[str, object]:
    return {"file_path": file_path, "content": content}


def test_resolve_corpus_sha_returns_pinned_value_and_raises_on_invalid_input() -> None:
    assert resolve_corpus_sha({"pinned_sha": "abc123"}) == "abc123"

    with pytest.raises(ValueError, match="pinned_sha"):
        resolve_corpus_sha({})

    with pytest.raises(ValueError, match="pinned_sha"):
        resolve_corpus_sha({"pinned_sha": ""})


def test_pinned_snapshot_exports_and_validates_with_expected_counts() -> None:
    root = Path(__file__).resolve().parents[2]
    data = load_golden_set(root / "evaluation" / "golden_set.json")
    sha = resolve_corpus_sha(data)
    snapshot_parent = root / "evaluation" / "_snapshot"
    if snapshot_parent.exists():
        shutil.rmtree(snapshot_parent)
    try:
        snapshot_root = export_snapshot(root, sha, snapshot_parent)
    except RuntimeError as exc:
        pytest.skip(f"pinned commit not present in this clone: {exc}")

    errors = validate_golden_set(data, snapshot_root, sha)
    assert errors == []
    files = sorted(iter_python_files(snapshot_root))
    assert len(files) == 40

    chunks = 0
    for file_path in files:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for start_index, end_index in chunk_lines(lines):
            content = "\n".join(lines[start_index:end_index])
            if content.strip():
                chunks += 1
    assert chunks == 70


def test_extract_generation_trace_handles_payload_and_missing_usage() -> None:
    payload = {
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [{"text": "diagnosis: INSUFFICIENT_EVIDENCE"}]},
        }],
        "usageMetadata": {"totalTokenCount": 42, "promptTokenCount": 10, "candidateTokenCount": 32},
    }
    trace = extract_generation_trace("sample prompt", payload)
    assert trace is not None
    assert trace["prompt_sha256"] == hashlib.sha256(b"sample prompt").hexdigest()
    assert trace["prompt_chars"] == len("sample prompt")
    assert trace["finish_reason"] == "STOP"
    assert trace["usage"] == payload["usageMetadata"]
    assert trace["total_tokens"] == 42

    empty_usage = {
        "candidates": [
            {"content": {"parts": [{"text": "diagnosis: insufficient evidence"}]}}
        ]
    }
    trace2 = extract_generation_trace("sample prompt", empty_usage)
    assert trace2 is not None
    assert trace2["usage"] == {}
    assert trace2["total_tokens"] is None

    assert extract_generation_trace(None, None) is None


def test_abstention_kind_and_outcome_v2_and_value_distribution() -> None:
    assert (
        abstention_kind("INSUFFICIENT_EVIDENCE", True, "INSUFFICIENT_EVIDENCE")
        == "explicit"
    )
    assert (
        abstention_kind(
            "INSUFFICIENT_EVIDENCE",
            True,
            "diagnosis: insufficient evidence",
        )
        == "parse_fallback"
    )
    assert abstention_kind("INSUFFICIENT_EVIDENCE", False, "INSUFFICIENT_EVIDENCE") is None

    cases = [
        ("answerable", None, False, False, True, True, "correct_labeled_context"),
        ("answerable", None, False, False, False, True, "correct_unlabeled_context"),
        ("answerable", None, False, False, True, False, "incomplete_or_wrong"),
        ("answerable", None, False, True, False, None, "retrieval_miss_abstained"),
        ("answerable", None, False, True, True, None, "model_false_abstention"),
        ("answerable", None, True, False, None, None, "guard_false_refusal"),
        ("unanswerable", None, True, False, None, None, "guard_true_refusal"),
        ("unanswerable", None, False, True, None, None, "model_abstained"),
        ("unanswerable", None, False, False, None, None, "answered_unanswerable"),
        ("answerable", "error", False, False, True, True, "error"),
    ]
    for (
        category,
        error,
        guard_refused,
        abstained,
        labeled_in_context,
        screen_pass,
        expected,
    ) in cases:
        assert classify_outcome_v2(
            category,
            error,
            guard_refused,
            abstained,
            labeled_in_context,
            screen_pass,
        ) == expected

    assert value_distribution([3, 5, 1, None, 9]) == {
        "min": 1,
        "median": 5,
        "max": 9,
        "count": 4,
    }
    assert value_distribution([None, None]) == {
        "min": None,
        "median": None,
        "max": None,
        "count": 0,
    }
    assert value_distribution([]) == {
        "min": None,
        "median": None,
        "max": None,
        "count": 0,
    }

    answerable_legacy = [
        {"legacy": "correct", "v2": "correct_labeled_context"},
        {"legacy": "correct", "v2": "correct_unlabeled_context"},
    ]
    assert sum(1 for row in answerable_legacy if row["legacy"] == "correct") == sum(
        1
        for row in answerable_legacy
        if row["v2"]
        in {"correct_labeled_context", "correct_unlabeled_context"}
    )
    refused_legacy = [{"legacy": "refused", "v2": "guard_true_refusal"}]
    assert sum(1 for row in refused_legacy if row["legacy"] == "refused") == sum(
        1 for row in refused_legacy if row["v2"] == "guard_true_refusal"
    )
    false_answer_legacy = [
        {"legacy": "falsely answered", "v2": "model_abstained"},
        {"legacy": "falsely answered", "v2": "answered_unanswerable"},
    ]
    assert sum(1 for row in false_answer_legacy if row["legacy"] == "falsely answered") == sum(
        1
        for row in false_answer_legacy
        if row["v2"] in {"model_abstained", "answered_unanswerable"}
    )


def test_explicit_abstention_cannot_pass_answer_screen(monkeypatch, tmp_path: Path) -> None:
    from evaluation import runner

    question = {
        "id": "paraphrased-05",
        "category": "paraphrased",
        "question": "What is the answer?",
        "relevant": [{"file_path": "missing.py", "substring": "target"}],
        "must_mention": [["INSUFFICIENT_EVIDENCE"]],
    }

    async def fake_investigate_repository(*args, **kwargs):
        return {
            "diagnosis": "INSUFFICIENT_EVIDENCE",
            "latency_ms": 75,
            "generation_trace": {"raw_text": "INSUFFICIENT_EVIDENCE"},
            "retrieval_results": [],
            "cited_chunk_ids": [],
        }

    monkeypatch.setattr(
        runner.investigate, "investigate_repository", fake_investigate_repository
    )
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)

    records, _ = asyncio.run(
        run_pipeline_once(
            [question], tmp_path, "test", {"http_calls": 0, "http_429_responses": 0}
        )
    )
    record = records[0]
    classify_outcomes(records, [question])
    classify_outcome_v2_for_records(records)

    assert record["screen_pass"] is None
    assert record["outcome"] == "correct"
    assert record["outcome_v2"] == "retrieval_miss_abstained"


def test_guard_diagnostics_and_citation_summary_arithmetic() -> None:
    checks = [
        {"reason": "RRF threshold below minimum"},
        {"reason": "vector distance too large"},
    ]
    assert guard_diagnostics(checks, 0.016)["rrf_gate_can_reject_nonempty_vector_results"] is False
    assert guard_diagnostics(checks, 0.02)["rrf_gate_can_reject_nonempty_vector_results"] is True

    records = [{
        "category": "direct",
        "diagnosis": "answer",
        "cited_chunk_ids": ["a", "b"],
        "cited_chunk_relevance": [{"relevant": True}, {"relevant": False}],
    }, {
        "category": "direct",
        "diagnosis": "answer",
        "cited_chunk_ids": ["c"],
        "cited_chunk_relevance": [{"relevant": False}],
    }, {
        "category": "unanswerable_far",
        "diagnosis": "INSUFFICIENT_EVIDENCE",
        "cited_chunk_ids": [],
        "cited_chunk_relevance": [],
    }]
    summary = citation_summary(records)
    assert summary == {"cited_total": 3, "cited_relevant": 1, "answers_with_zero_citations": 0}


def test_retrieval_metrics_handle_hits_ties_and_no_hit() -> None:
    results = [
        [result("a.py", "alpha"), result("b.py", "beta")],
        [result("b.py", "beta"), result("a.py", "alpha")],
        [result("c.py", "gamma")],
    ]
    labels = [
        [{"file_path": "a.py", "substring": "alpha"}],
        [{"file_path": "a.py", "substring": "alpha"}],
        [{"file_path": "z.py", "substring": "zeta"}],
    ]

    assert hit_at_k(results, labels, 1) == 1
    assert hit_at_k(results, labels, 3) == 2
    assert mean_reciprocal_rank(results, labels) == (1 + 0.5) / 3
    assert retrieval_summary(results, labels)["hit_at_5"] == 2


def test_mrr_averages_equal_ranks_and_counts_no_hit_as_zero() -> None:
    results = [
        [result("other.py", "no"), result("target.py", "yes")],
        [result("elsewhere.py", "no"), result("target.py", "yes")],
        [result("other.py", "no")],
    ]
    labels = [[{"file_path": "target.py", "substring": "yes"}]] * 3

    assert mean_reciprocal_rank(results, labels) == pytest.approx(1 / 3)


def test_relevance_rule_is_case_insensitive_and_requires_same_file() -> None:
    labels = [{"file_path": "src/store.py", "substring": "PersistResult"}]

    assert is_relevant(result("src/store.py", "class persistresult:"), labels)
    assert not is_relevant(result("src/other.py", "class PersistResult:"), labels)


def test_guard_confusion_and_distance_sweep() -> None:
    answerable = [True, True, False, False]
    sufficient = [True, False, False, True]
    assert guard_confusion(answerable, sufficient) == {
        "true_accept": 1,
        "false_refusal": 1,
        "true_refusal": 1,
        "false_accept": 1,
    }

    checks = [
        {"best_rrf_score": 0.02, "best_vector_score": 0.31},
        {"best_rrf_score": 0.02, "best_vector_score": 0.51},
    ]
    sweep = distance_sweep(checks, [True, False], 0.016)
    assert sweep[0] == {
        "vector_cutoff": 0.3,
        "false_refusals": 1,
        "false_accepts": 0,
    }
    assert len(sweep) == 16
    assert sweep[-1]["vector_cutoff"] == 0.6


def test_distance_sweep_counts_false_refusals_and_false_accepts() -> None:
    checks = [
        {"best_rrf_score": 0.02, "best_vector_score": 0.31},
        {"best_rrf_score": 0.02, "best_vector_score": 0.5},
        {"best_rrf_score": 0.02, "best_vector_score": 0.35},
        {"best_rrf_score": 0.01, "best_vector_score": 0.2},
    ]
    sweep = distance_sweep(checks, [True, True, False, False], 0.016)

    assert sweep[0] == {
        "vector_cutoff": 0.3,
        "false_refusals": 2,
        "false_accepts": 0,
    }
    assert sweep[3] == {
        "vector_cutoff": 0.36,
        "false_refusals": 1,
        "false_accepts": 1,
    }
    assert sweep[10] == {
        "vector_cutoff": 0.5,
        "false_refusals": 0,
        "false_accepts": 1,
    }


def test_answer_screen_and_refusal() -> None:
    assert answer_screen("AsyncSessionLocal uses async_sessionmaker", [["sessionmaker"], ["async"]])
    assert not answer_screen("Only a database engine is described", [["sessionmaker"]])
    assert is_refused("INSUFFICIENT_EVIDENCE")
    assert is_refused(" INSUFFICIENT_EVIDENCE ")
    assert not is_refused("INSUFFICIENT_EVIDENCE", generation_latency_ms=75)
    assert not is_refused("Diagnosis: insufficient evidence")


def _valid_golden_data(snapshot_root: Path) -> dict[str, object]:
    questions = []
    for index, category in enumerate(["direct"] * 8 + ["paraphrased"] * 8):
        relative_path = f"area{index}.py"
        content = f"label phrase {index}"
        (snapshot_root / relative_path).write_text(
            f"value = {content!r}\n", encoding="utf-8"
        )
        questions.append(
            {
                "id": f"{category}-{index}",
                "category": category,
                "question": "How does this behavior work?",
                "seen_before": False,
                "relevant": [{"file_path": relative_path, "substring": content}],
                "must_mention": [["label"]],
            }
        )
    questions.extend(
        {
            "id": f"unanswerable-{index}",
            "category": "unanswerable_far" if index < 4 else "unanswerable_near",
            "question": "How is this absent feature handled?",
            "seen_before": False,
            "absent_terms": ["feature-not-present"],
        }
        for index in range(8)
    )
    return {
        "pinned_sha": "snapshot-sha",
        "review_status": "pending maintainer review",
        "counts": {
            "direct": 8,
            "paraphrased": 8,
            "unanswerable_far": 4,
            "unanswerable_near": 4,
        },
        "questions": questions,
    }


def test_golden_validation_accepts_valid_schema_and_snapshot(tmp_path: Path) -> None:
    data = _valid_golden_data(tmp_path)

    assert validate_golden_set(data, tmp_path, "snapshot-sha") == []


def test_golden_validation_rejects_duplicate_ids_invalid_category_and_counts(
    tmp_path: Path,
) -> None:
    data = _valid_golden_data(tmp_path)
    questions = data["questions"]
    questions[1]["id"] = questions[0]["id"]
    questions[0]["category"] = "invalid"
    data["counts"]["direct"] = 7

    errors = validate_golden_set(data, tmp_path, "other-sha")

    assert "question ids are not unique" in errors
    assert any("invalid categories" in error for error in errors)
    assert any("category counts differ" in error for error in errors)
    assert "header counts do not match the required category counts" in errors
    assert "pinned_sha does not match the exported snapshot" in errors


def test_golden_validation_rejects_missing_labels_absent_terms_and_answer_labels(
    tmp_path: Path,
) -> None:
    data = _valid_golden_data(tmp_path)
    questions = data["questions"]
    questions[0]["relevant"] = [{"file_path": "missing.py", "substring": "absent"}]
    questions[-1]["absent_terms"] = ["LABEL PHRASE 1"]
    questions[-2]["absent_terms"] = []
    questions[-3]["relevant"] = [{"file_path": "area0.py", "substring": "label phrase 0"}]

    errors = validate_golden_set(data, tmp_path, "snapshot-sha")

    assert any("missing label file" in error for error in errors)
    assert any("absent term appears" in error for error in errors)
    assert any("unanswerable_near requires absent_terms" in error for error in errors)
    assert any("unanswerable question has answer labels" in error for error in errors)


def test_index_validation_requires_a_reachable_chunk() -> None:
    questions = [
        {
            "id": "direct-1",
            "category": "direct",
            "relevant": [{"file_path": "source.py", "substring": "target phrase"}],
        }
    ]

    assert validate_index_labels(
        questions, [result("source.py", "contains target phrase")]
    ) == []
    assert validate_index_labels(questions, [result("source.py", "no target")]) == [
        "direct-1: no indexed chunk matches a relevance label"
    ]


def test_build_run_metadata_stable_hash_and_compare_reports_detect_changes() -> None:
    from evaluation.compare import compare_reports
    from evaluation.runner import build_run_metadata

    a = build_run_metadata(
        run_id="20260101T000000Z-abc1234",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:01:00+00:00",
        corpus_sha="deadbeef",
        code_sha="code123",
        code_dirty=False,
        models={"embedding": "m1", "generation": "g1"},
        limit=5,
        passes=2,
    )
    b = build_run_metadata(
        run_id="20260101T000001Z-abc1234",
        started_at="2026-01-01T00:00:01+00:00",
        finished_at="2026-01-01T00:01:01+00:00",
        corpus_sha="deadbeef",
        code_sha="code123",
        code_dirty=False,
        models={"embedding": "m1", "generation": "g1"},
        limit=5,
        passes=2,
    )
    assert a["config_sha256"] == b["config_sha256"]

    report_a = {
        "pinned_sha": "deadbeef",
        "run_id": "a",
        "config_sha256": a["config_sha256"],
        "outcome_v2_counts": {"correct_labeled_context": 2, "model_abstained": 1},
        "guard_counts": {"true_accept": 2, "false_refusal": 1},
        "retrieval_tables": {"vector": {"hit_at_1": 2, "hit_at_3": 3}},
        "latency_summary": {"pass_1": {"generation_ms": {"median": 100}}},
        "token_summary": {"pass_1": {"total_tokens": {"median": 120}}},
        "records": [[
            {"id": "q1", "outcome_v2": "correct_labeled_context", "labeled_rank": 1},
            {"id": "q2", "outcome_v2": "model_abstained", "labeled_rank": None},
        ]],
    }
    report_b = {
        "pinned_sha": "deadbeef",
        "run_id": "b",
        "config_sha256": a["config_sha256"],
        "outcome_v2_counts": {"correct_labeled_context": 1, "model_abstained": 2},
        "guard_counts": {"true_accept": 1, "false_refusal": 2},
        "retrieval_tables": {"vector": {"hit_at_1": 1, "hit_at_3": 2}},
        "latency_summary": {"pass_1": {"generation_ms": {"median": 200}}},
        "token_summary": {"pass_1": {"total_tokens": {"median": 180}}},
        "records": [[
            {"id": "q1", "outcome_v2": "incomplete_or_wrong", "labeled_rank": 3},
            {"id": "q2", "outcome_v2": "model_abstained", "labeled_rank": None},
        ]],
    }

    diff = compare_reports(report_a, report_b)
    assert diff["outcome_v2_counts_delta"]["correct_labeled_context"] == -1
    assert diff["question_flips"]["q1"]["outcome_v2"] == {
        "from": "correct_labeled_context",
        "to": "incomplete_or_wrong",
    }
    assert diff["question_flips"]["q1"]["labeled_rank"] == {"from": 1, "to": 3}
    assert diff["generation_latency_delta"]["median_generation_ms"] == 100
    assert diff["total_token_delta"]["median_total_tokens"] == 60

    legacy = {
        "run_id": "legacy",
        "records": [{"id": "q1", "outcome_v2": "correct_labeled_context"}],
    }
    assert compare_reports(legacy, report_a)["legacy_report"] is True
