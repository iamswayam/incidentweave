from __future__ import annotations

import pytest

from app.investigation.confidence import calibrate_confidence
from app.investigation.guard import evaluate_evidence_sufficiency
from app.investigation.parsing import parse_investigation_response


def test_parse_investigation_response_handles_nonmatching_header_casing() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "diagnosis: Async sessions use async_sessionmaker\n\n"
                                "confidence: high\n\n"
                                "evidence used:\n"
                                "- app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }
    results = [{
        "id": 105,
        "file_path": "app/db/session.py",
        "line_start": 1,
        "line_end": 46,
        "vector_score": 0.1,
        "fts_score": 0.5,
        "rrf_score": 0.9,
        "content": (
            "AsyncSessionLocal = async_sessionmaker(bind=engine, "
            "class_=AsyncSession, expire_on_commit=False)"
        ),
    }]

    parsed = parse_investigation_response(payload, results)

    assert parsed["diagnosis"] == "Async sessions use async_sessionmaker"
    assert parsed["confidence"] == "high"
    assert parsed["cited_chunk_ids"] == ["105"]


def test_parse_investigation_response_matches_exact_file_path_without_lines() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: AsyncSessionLocal is configured in "
                                "app/db/session.py using async_sessionmaker.\n"
                                "Confidence: high"
                            )
                        }
                    ]
                }
            }
        ]
    }
    retrieved_results = [
        {
            "id": 136,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
        }
    ]

    parsed = parse_investigation_response(payload, retrieved_results)

    assert parsed["cited_chunk_ids"] == ["136"]


def test_evaluate_evidence_sufficiency_rejects_empty_and_weak_results() -> None:
    empty_result = evaluate_evidence_sufficiency([])
    assert empty_result["is_sufficient"] is False
    assert empty_result["best_vector_score"] is None
    # RRF is no longer a gate (checklist item 3a); distance decides.
    assert evaluate_evidence_sufficiency([
        {"id": 1, "rrf_score": 0.01, "vector_score": 0.1},
        {"id": 2, "rrf_score": 0.005, "vector_score": 0.2},
    ])["is_sufficient"] is True
    assert evaluate_evidence_sufficiency([
        {"id": 3, "rrf_score": 0.021, "vector_score": 0.4},
    ])["is_sufficient"] is True
    assert evaluate_evidence_sufficiency([
        {"id": 4, "rrf_score": 0.021, "vector_score": 0.5001},
    ])["is_sufficient"] is False
    assert evaluate_evidence_sufficiency([
        {"id": 5, "rrf_score": 0.021},
    ])["is_sufficient"] is False


def test_evaluate_evidence_sufficiency_uses_each_chunks_vector_distance() -> None:
    different_chunks = evaluate_evidence_sufficiency([
        {"id": 1, "rrf_score": 0.03, "vector_score": 0.9},
        {"id": 2, "rrf_score": 0.017, "vector_score": 0.4},
    ])
    assert different_chunks["is_sufficient"] is True
    assert different_chunks["best_vector_score"] == 0.4

    missing_vector_distance = evaluate_evidence_sufficiency([
        {"id": 1, "rrf_score": 0.03, "vector_score": 0.9},
        {"id": 2, "rrf_score": 0.017},
    ])
    assert missing_vector_distance["is_sufficient"] is False


def test_evaluate_evidence_sufficiency_accepts_rank_one_vector_only_hit() -> None:
    result = evaluate_evidence_sufficiency([
        {"id": 1, "rrf_score": 1 / 61, "vector_score": 0.3, "fts_score": None},
    ])
    assert result["is_sufficient"] is True


def test_evaluate_evidence_sufficiency_rejects_full_text_only_hit() -> None:
    result = evaluate_evidence_sufficiency([
        {"id": 1, "rrf_score": 0.0328, "fts_score": 0.7},
    ])
    assert result["is_sufficient"] is False
    assert result["reason"] == "No vector similarity score was retrieved."


def test_evaluate_evidence_sufficiency_respects_vector_distance_boundary() -> None:
    at_boundary = evaluate_evidence_sufficiency([
        {"id": 1, "vector_score": 0.5},
    ])
    above_boundary = evaluate_evidence_sufficiency([
        {"id": 2, "vector_score": 0.5001},
    ])
    assert at_boundary["is_sufficient"] is True
    assert above_boundary["is_sufficient"] is False


def test_evaluate_evidence_sufficiency_rejects_evidence_source_argument() -> None:
    with pytest.raises(TypeError):
        evaluate_evidence_sufficiency([], evidence_source="literal")


def test_parse_investigation_response_forces_low_confidence_on_abstention() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: INSUFFICIENT_EVIDENCE\n"
                                "Confidence: high\n"
                                "Evidence used: app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }
    retrieved_results = [
        {
            "id": 105,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
        }
    ]

    parsed = parse_investigation_response(payload, retrieved_results)

    assert parsed["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert parsed["confidence"] == "low"
    assert parsed["cited_chunk_ids"] == ["105"]


def test_parse_investigation_response_normalizes_punctuated_abstention() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Diagnosis: insufficient_evidence.\nConfidence: medium"}
                    ]
                }
            }
        ]
    }

    parsed = parse_investigation_response(payload, [])

    assert parsed["confidence"] == "low"


def test_parse_investigation_response_preserves_non_abstention_confidence() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: Sessions use async_sessionmaker.\n"
                                "Confidence: high"
                            )
                        }
                    ]
                }
            }
        ]
    }

    parsed = parse_investigation_response(payload, [])

    assert parsed["confidence"] == "high"


def test_parse_investigation_response_forces_low_confidence_without_diagnosis_header() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Confidence: high"}
                    ]
                }
            }
        ]
    }

    parsed = parse_investigation_response(payload, [])

    assert parsed["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert parsed["confidence"] == "low"


def test_calibrate_confidence_keeps_low_confidence_low() -> None:
    assert calibrate_confidence("low", 0.04, 0.2)[0] == "low"
