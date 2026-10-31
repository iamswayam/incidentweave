from __future__ import annotations

import json

import pytest

from app.investigation.confidence import calibrate_confidence
from app.investigation.guard import evaluate_evidence_sufficiency
from app.investigation.parsing import ModelOutputError, parse_investigation_response


def structured_payload(
    *,
    chunk_id: str = "105",
    quote: str = "async_sessionmaker",
    outcome: str = "answered",
    diagnosis: str = "Async sessions use async_sessionmaker.",
    self_rating: str = "high",
) -> dict[str, object]:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "outcome": outcome,
                                    "diagnosis": diagnosis,
                                    "self_rating": self_rating,
                                    "claims": [
                                        {
                                            "text": diagnosis,
                                            "evidence": [
                                                {"chunk_id": chunk_id, "quote": quote}
                                            ],
                                        }
                                    ],
                                    "uncertainty_note": "",
                                }
                            )
                        }
                    ]
                }
            }
        ]
    }


def test_parse_structured_response_validates_retrieved_id_and_whitespace_quote() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "outcome": "answered",
                                    "diagnosis": "Async sessions use async_sessionmaker.",
                                    "self_rating": "high",
                                    "claims": [
                                        {
                                            "text": "Async sessions use async_sessionmaker.",
                                            "evidence": [
                                                {
                                                    "chunk_id": "105",
                                                    "quote": "AsyncSessionLocal =  \n "
                                                    "async_sessionmaker(bind=engine, "
                                                    "class_=AsyncSession, "
                                                    "expire_on_commit=False)",
                                                }
                                            ],
                                        }
                                    ],
                                    "uncertainty_note": "",
                                }
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

    assert parsed["diagnosis"] == "Async sessions use async_sessionmaker."
    assert parsed["confidence"] == "high"
    assert parsed["cited_chunk_ids"] == ["105"]
    assert parsed["valid_citation_count"] == 1
    assert parsed["citation_validity_rate"] == 1.0
    assert parsed["claims"][0]["evidence"][0]["chunk_id"] == "105"


def test_parse_structured_response_rejects_hallucinated_chunk_id() -> None:
    retrieved_results = [
        {
            "id": 136,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
        }
    ]

    parsed = parse_investigation_response(
        structured_payload(chunk_id="999"), retrieved_results
    )

    assert parsed["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert parsed["outcome"] == "insufficient_evidence"
    assert parsed["cited_chunk_ids"] == []
    assert parsed["valid_citation_count"] == 0
    assert parsed["submitted_citation_count"] == 1


def test_parse_structured_response_rejects_quote_missing_from_retrieved_chunk() -> None:
    parsed = parse_investigation_response(
        structured_payload(quote="not actually present"),
        [{"id": 105, "content": "AsyncSessionLocal uses async_sessionmaker."}],
    )

    assert parsed["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert parsed["claims"] == []
    assert parsed["citation_validity_rate"] == 0.0


def test_parse_structured_response_drops_invalid_evidence_but_keeps_valid_claim() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "outcome": "answered",
                                    "diagnosis": "Supported claim.",
                                    "self_rating": "medium",
                                    "claims": [
                                        {
                                            "text": "Supported claim.",
                                            "evidence": [
                                                {"chunk_id": "missing", "quote": "text"},
                                                {"chunk_id": "105", "quote": "valid quote"},
                                            ],
                                        }
                                    ],
                                    "uncertainty_note": "Some uncertainty remains.",
                                }
                            )
                        }
                    ]
                }
            }
        ]
    }
    parsed = parse_investigation_response(
        payload,
        [{"id": 105, "content": "A valid quote is present."}],
    )

    assert parsed["diagnosis"] == "Supported claim."
    assert parsed["cited_chunk_ids"] == ["105"]
    assert parsed["submitted_citation_count"] == 2
    assert parsed["valid_citation_count"] == 1
    assert parsed["citation_validity_rate"] == 0.5
    assert parsed["uncertainty_note"] == "Some uncertainty remains."


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


def test_parse_insufficient_evidence_keeps_valid_claims_and_raw_rating() -> None:
    parsed = parse_investigation_response(
        structured_payload(
            outcome="insufficient_evidence",
            diagnosis="insufficient_evidence.",
            self_rating="high",
        ),
        [{"id": 105, "content": "async_sessionmaker configured for app."}],
    )

    assert parsed["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert parsed["confidence"] == "low"
    assert parsed["raw_self_rating"] == "high"
    assert parsed["claims"][0]["text"] == "insufficient_evidence."
    assert parsed["cited_chunk_ids"] == ["105"]


def test_parse_invalid_json_raises_model_output_error() -> None:
    payload = {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]}

    with pytest.raises(ModelOutputError, match="valid JSON"):
        parse_investigation_response(payload, [])


def test_parse_wrong_field_types_raise_model_output_error() -> None:
    payload = structured_payload()
    payload["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(
        {
            "outcome": "answered",
            "diagnosis": "Diagnosis",
            "self_rating": ["high"],
            "uncertainty_note": "",
            "claims": [],
        }
    )

    with pytest.raises(ModelOutputError, match="self_rating"):
        parse_investigation_response(payload, [])


def test_parse_quote_under_ten_characters_is_dropped() -> None:
    parsed = parse_investigation_response(
        structured_payload(quote="short"),
        [{"id": 105, "content": "A short quote is here."}],
    )

    assert parsed["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert parsed["claims"] == []
    assert parsed["valid_citation_count"] == 0


def test_parse_answered_without_valid_claim_is_refused() -> None:
    parsed = parse_investigation_response(
        structured_payload(quote="not present in source"),
        [{"id": 105, "content": "real source content for this result"}],
    )

    assert parsed["outcome"] == "insufficient_evidence"
    assert parsed["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert parsed["claims"] == []
    assert parsed["cited_chunk_ids"] == []


def test_calibrate_confidence_keeps_low_confidence_low() -> None:
    assert calibrate_confidence("low", 0.04, 0.2)[0] == "low"
