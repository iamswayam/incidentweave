from __future__ import annotations

from app.investigation.guard import evaluate_evidence_sufficiency
from evaluation.test_file_variants import (
    control_top_five,
    downweight_test_chunks,
    exclude_test_chunks,
)


def _result(
    index: int,
    *,
    path: str,
    score: float,
    vector_score: float,
    vector_rank: int,
    fulltext_rank: int | None,
) -> dict[str, object]:
    return {
        "id": index,
        "file_path": path,
        "line_start": index,
        "line_end": index + 1,
        "rrf_score": score,
        "vector_score": vector_score,
        "vector_rank": vector_rank,
        "fulltext_rank": fulltext_rank,
    }


def test_v1_reorders_test_chunks_without_dropping_candidates() -> None:
    ranking = [
        _result(
            index,
            path=("tests/test_case.py" if index == 1 else f"src/file_{index}.py"),
            score=(
                1.0 - index / 100
                if index <= 5
                else 0.4 - index / 100
            ),
            vector_score=0.2,
            vector_rank=index,
            fulltext_rank=index,
        )
        for index in range(1, 9)
    ]

    variant = downweight_test_chunks(ranking)

    assert len(variant) == 5
    assert len(ranking) == 8
    assert variant[0]["id"] == 2
    assert {result["id"] for result in variant} == {1, 2, 3, 4, 5}
    assert ranking[0]["rrf_score"] == 0.99


def test_v2_excludes_test_chunks_before_refilling_the_top_five() -> None:
    ranking = [
        _result(
            index,
            path=("tests/test_case.py" if index <= 3 else f"src/file_{index}.py"),
            score=1.0 - index / 100,
            vector_score=0.2,
            vector_rank=index,
            fulltext_rank=index,
        )
        for index in range(1, 9)
    ]

    variant = exclude_test_chunks(ranking)

    assert [result["id"] for result in variant] == [4, 5, 6, 7, 8]
    assert all(not str(result["file_path"]).startswith("tests/") for result in variant)


def test_tie_break_is_deterministic_and_matches_production_path_order() -> None:
    tied = [
        _result(
            2,
            path="src/z.py",
            score=1.0,
            vector_score=0.2,
            vector_rank=1,
            fulltext_rank=1,
        ),
        _result(
            1,
            path="src/a.py",
            score=1.0,
            vector_score=0.2,
            vector_rank=1,
            fulltext_rank=1,
        ),
    ]

    assert [row["file_path"] for row in downweight_test_chunks(tied)] == [
        "src/a.py",
        "src/z.py",
    ]
    assert [row["file_path"] for row in downweight_test_chunks(tied)] == [
        row["file_path"] for row in downweight_test_chunks(tied)
    ]


def test_guard_is_evaluated_on_the_resulting_variant_top_five() -> None:
    ranking = [
        _result(
            index,
            path=("tests/test_case.py" if index == 1 else f"src/file_{index}.py"),
            score=1.0 - index / 100,
            vector_score=(0.2 if index == 6 else 0.8),
            vector_rank=index,
            fulltext_rank=index,
        )
        for index in range(1, 7)
    ]

    control = control_top_five(ranking)
    v1 = downweight_test_chunks(ranking)

    assert control[0]["id"] == 1
    assert v1[0]["id"] == 2
    assert evaluate_evidence_sufficiency(control)["is_sufficient"] is False
    assert evaluate_evidence_sufficiency(v1)["is_sufficient"] is True
