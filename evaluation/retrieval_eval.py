"""Offline hybrid-retrieval evaluation using committed embeddings."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.models import Chunk, Repository
from app.db.session import AsyncSessionLocal
from app.retrieval.hybrid_search import hybrid_search
from evaluation.build_fixture import FIXTURE_PATH, load_fixture
from evaluation.golden import load_golden_set
from evaluation.metrics import first_relevant_rank, first_relevant_span_rank
from evaluation.stats import paired_comparison, wilson_interval

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "evaluation" / "golden_set.json"
FIXTURE_REPOSITORY = "incidentweave-fixture"


async def _delete_fixture_repository() -> None:
    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == FIXTURE_REPOSITORY)
        )
        if repository is not None:
            await session.delete(repository)
            await session.commit()


def _summary(records: list[dict[str, Any]], rank_key: str) -> dict[str, Any]:
    summary: dict[str, Any] = {"count": len(records)}
    for k in (1, 3, 5):
        successes = sum(
            record[rank_key] is not None and record[rank_key] <= k
            for record in records
        )
        low, high = wilson_interval(successes, len(records))
        summary[f"hit_at_{k}"] = {
            "successes": successes,
            "rate": successes / len(records) if records else 0.0,
            "wilson_95": [low, high],
        }
    summary["mrr"] = (
        sum(
            1 / record[rank_key] if record[rank_key] is not None else 0.0
            for record in records
        )
        / len(records)
        if records
        else 0.0
    )
    return summary


async def run_offline_retrieval(
    fixture_path: Path = FIXTURE_PATH,
    golden_path: Path = GOLDEN_PATH,
    limit: int = 5,
) -> dict[str, Any]:
    """Evaluate vector-plus-FTS retrieval without provider calls."""

    question_records: list[dict[str, Any]] = []
    try:
        if limit < 1:
            raise ValueError("limit must be greater than zero")
        await _delete_fixture_repository()
        fixture = load_fixture(fixture_path)
        golden = load_golden_set(golden_path)
        fixture_chunks = fixture["chunks"]
        fixture_queries = fixture["queries"]

        async with AsyncSessionLocal() as session:
            repository = Repository(name=FIXTURE_REPOSITORY)
            session.add(repository)
            await session.flush()
            repository_id = repository.id
            session.add_all(
                [
                    Chunk(
                        repository_id=repository_id,
                        file_path=chunk["file_path"],
                        line_start=chunk["line_start"],
                        line_end=chunk["line_end"],
                        content=chunk["content"],
                        content_hash=hashlib.sha256(
                            chunk["content"].encode("utf-8")
                        ).hexdigest(),
                        embedding=chunk["embedding"],
                        file_type="python",
                        document_type="code",
                    )
                    for chunk in fixture_chunks
                ]
            )
            await session.commit()

        async with AsyncSessionLocal() as session:
            for question in golden["questions"]:
                question_id = str(question["id"])
                if question_id not in fixture_queries:
                    raise ValueError(
                        f"Fixture lacks cached query embedding for {question_id}"
                    )
                results = await hybrid_search(
                    session,
                    repository_id,
                    question["question"],
                    fixture_queries[question_id],
                    limit=limit,
                )
                answerable = question["category"] in {"direct", "paraphrased"}
                label_rank = (
                    first_relevant_rank(results, question.get("relevant", []))
                    if answerable
                    else None
                )
                span_rank = (
                    first_relevant_span_rank(
                        results, question.get("relevant_spans", [])
                    )
                    if answerable
                    else None
                )
                question_records.append(
                    {
                        "id": question_id,
                        "category": question["category"],
                        "label_rank": label_rank,
                        "span_rank": span_rank,
                        "label_hits": {
                            str(k): label_rank is not None and label_rank <= k
                            for k in (1, 3, 5)
                        },
                        "span_hits": {
                            str(k): span_rank is not None and span_rank <= k
                            for k in (1, 3, 5)
                        },
                    }
                )
    finally:
        await _delete_fixture_repository()

    answerable_records = [
        record
        for record in question_records
        if record["category"] in {"direct", "paraphrased"}
    ]
    breakdown = {}
    for category in ("direct", "paraphrased"):
        category_records = [
            record
            for record in answerable_records
            if record["category"] == category
        ]
        breakdown[category] = {
            "substring_labels": _summary(category_records, "label_rank"),
            "spans": _summary(category_records, "span_rank"),
        }
    return {
        "metadata": {
            "fixture": fixture["meta"],
            "golden_pinned_sha": golden["pinned_sha"],
            "limit": limit,
        },
        "questions": question_records,
        "summary": {
            "substring_labels": _summary(answerable_records, "label_rank"),
            "spans": _summary(answerable_records, "span_rank"),
        },
        "breakdown_by_category": breakdown,
    }


def compare_reports(
    report_a: dict[str, Any],
    report_b: dict[str, Any],
    k: int = 5,
) -> dict[str, int | float]:
    """Compare paired answerable-question substring hit outcomes at K."""

    if k not in {1, 3, 5}:
        raise ValueError("k must be one of 1, 3, or 5")
    records_a = {
        row["id"]: row
        for row in report_a["questions"]
        if row["category"] in {"direct", "paraphrased"}
    }
    records_b = {
        row["id"]: row
        for row in report_b["questions"]
        if row["category"] in {"direct", "paraphrased"}
    }
    if records_a.keys() != records_b.keys():
        raise ValueError("reports must contain the same answerable question ids")
    question_ids = sorted(records_a)
    return paired_comparison(
        [bool(records_a[question_id]["label_hits"][str(k)]) for question_id in question_ids],
        [bool(records_b[question_id]["label_hits"][str(k)]) for question_id in question_ids],
    )
