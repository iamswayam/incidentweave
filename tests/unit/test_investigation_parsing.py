from __future__ import annotations

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
    assert evaluate_evidence_sufficiency([
        {"id": 1, "rrf_score": 0.01, "vector_score": 0.1},
        {"id": 2, "rrf_score": 0.005, "vector_score": 0.2},
    ])["is_sufficient"] is False
    assert evaluate_evidence_sufficiency([
        {"id": 3, "rrf_score": 0.021, "vector_score": 0.4},
    ])["is_sufficient"] is True
    assert evaluate_evidence_sufficiency([
        {"id": 4, "rrf_score": 0.021, "vector_score": 0.5001},
    ])["is_sufficient"] is False
    assert evaluate_evidence_sufficiency([
        {"id": 5, "rrf_score": 0.021},
    ])["is_sufficient"] is False
