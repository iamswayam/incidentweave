"""Offline hybrid-retrieval evaluation using committed embeddings."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.models import Chunk, Repository
from app.db.session import AsyncSessionLocal
from app.retrieval.fulltext_search import search_fulltext
from app.retrieval.fulltext_variants import SEARCHABLE_TEXT_VERSION
from app.retrieval.hybrid_search import hybrid_search
from evaluation.build_fixture import load_fixture
from evaluation.fulltext_ablation import build_protocol_query
from evaluation.golden import load_golden_set
from evaluation.manifest import (
    MANIFEST_PATH,
    load_manifest,
    questions_for_split,
    repository_entry,
)
from evaluation.metrics import first_relevant_rank, first_relevant_span_rank
from evaluation.stats import paired_comparison, wilson_interval

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "evaluation" / "golden_set.json"
DEFAULT_REPOSITORY_ID = "incidentweave"


def _explicit_development_questions(
    entry: Mapping[str, Any],
    split: str,
    question_records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Accept only rows explicitly selected for the development split."""

    if split != "development":
        raise ValueError(
            "Explicit question records are supported only for development"
        )
    allowed_ids = set(entry["splits"]["development"])
    raw_ids = [question.get("id") for question in question_records]
    if any(not isinstance(question_id, str) or not question_id for question_id in raw_ids):
        raise ValueError("Explicit development records need non-empty question ids")
    selected_ids = [str(question_id) for question_id in raw_ids]
    if (
        len(selected_ids) != len(set(selected_ids))
        or not set(selected_ids) <= allowed_ids
    ):
        raise ValueError("Explicit question records must be unique development rows")
    return [dict(question) for question in question_records]


def fixture_repository_name(repo_id: str) -> str:
    """Return the isolated temporary DB repository name for one manifest ID."""

    safe_id = "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in repo_id
    )
    return f"incidentweave-fixture-{safe_id}"


async def _delete_fixture_repository(repository_name: str) -> None:
    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
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
    fixture_path: Path | None = None,
    golden_path: Path | None = None,
    limit: int = 5,
    *,
    repo_id: str = DEFAULT_REPOSITORY_ID,
    split: str = "all",
    entry: dict[str, Any] | None = None,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
    record_retrieved: bool = False,
    record_details: bool = False,
    variant: str = "control",
    record_variant_details: bool = False,
    development_records: Sequence[Mapping[str, Any]] | None = None,
    golden_pinned_sha: str | None = None,
) -> dict[str, Any]:
    """Evaluate vector-plus-FTS retrieval without provider calls."""

    question_records: list[dict[str, Any]] = []
    if variant not in {"control", "c1", "c2"}:
        raise ValueError(f"Unknown full-text variant: {variant}")
    if entry is None:
        manifest = load_manifest(manifest_path, root=root)
        entry = repository_entry(manifest, repo_id)
    elif entry["id"] != repo_id:
        repo_id = str(entry["id"])
    selected_fixture_path = fixture_path or root / entry["fixture"]["path"]
    selected_golden_path = golden_path or root / entry["questions"]["path"]
    fixture_repository = fixture_repository_name(repo_id)
    try:
        if limit < 1:
            raise ValueError("limit must be greater than zero")
        await _delete_fixture_repository(fixture_repository)
        fixture = load_fixture(selected_fixture_path)
        if development_records is None:
            golden = load_golden_set(selected_golden_path)
            questions = questions_for_split(entry, golden["questions"], split)
            selected_pinned_sha = golden["pinned_sha"]
        else:
            questions = _explicit_development_questions(
                entry,
                split,
                development_records,
            )
            selected_pinned_sha = golden_pinned_sha or str(entry["pinned_sha"])
        fixture_chunks = fixture["chunks"]
        fixture_queries = fixture["queries"]

        async with AsyncSessionLocal() as session:
            repository = Repository(name=fixture_repository)
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
            for question in questions:
                question_id = str(question["id"])
                if question_id not in fixture_queries:
                    raise ValueError(
                        f"Fixture lacks cached query embedding for {question_id}"
                    )
                fulltext_query_text: str | None = None
                searchable_text_version: str | None = None
                query_metadata: dict[str, Any] | None = None
                if variant in {"c1", "c2"}:
                    built_query = await build_protocol_query(
                        session,
                        str(question["question"]),
                    )
                    fulltext_query_text = built_query.query_text
                    query_metadata = {
                        "query_token_count": len(built_query.tokens),
                        "query_truncated": built_query.truncated,
                    }
                    if variant == "c2":
                        searchable_text_version = SEARCHABLE_TEXT_VERSION

                text_branch_nonempty: bool | None = None
                if record_variant_details:
                    branch_results = await search_fulltext(
                        session,
                        repository_id,
                        str(question["question"]),
                        limit=limit,
                        query_text_override=fulltext_query_text,
                        searchable_text_version=searchable_text_version,
                    )
                    text_branch_nonempty = bool(branch_results)

                if fulltext_query_text is None and searchable_text_version is None:
                    results = await hybrid_search(
                        session,
                        repository_id,
                        question["question"],
                        fixture_queries[question_id],
                        limit=limit,
                    )
                else:
                    results = await hybrid_search(
                        session,
                        repository_id,
                        question["question"],
                        fixture_queries[question_id],
                        limit=limit,
                        fulltext_query_text=fulltext_query_text,
                        searchable_text_version=searchable_text_version,
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
                record = {
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
                if record_details:
                    record["retrieved"] = [
                        {
                            "rank": rank,
                            "file_path": result["file_path"],
                            "line_start": result["line_start"],
                            "line_end": result["line_end"],
                            "content": result["content"],
                            "vector_score": result["vector_score"],
                            "fts_score": result["fts_score"],
                            "rrf_score": result["rrf_score"],
                        }
                        for rank, result in enumerate(results[:limit], start=1)
                    ]
                elif record_retrieved:
                    record["retrieved"] = [
                        {
                            "file_path": result["file_path"],
                            "line_start": result["line_start"],
                            "line_end": result["line_end"],
                        }
                        for result in results[:limit]
                    ]
                if query_metadata is not None:
                    record.update(query_metadata)
                if text_branch_nonempty is not None:
                    record["text_branch_nonempty"] = text_branch_nonempty
                question_records.append(record)
    finally:
        await _delete_fixture_repository(fixture_repository)

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
            "repo_id": repo_id,
            "split": split,
            "previously_exposed": bool(entry.get("previously_exposed")),
            "fixture": fixture["meta"],
            "golden_pinned_sha": selected_pinned_sha,
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
