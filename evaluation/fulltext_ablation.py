"""Fixture-backed runners and metrics for the registered full-text ablation."""

from __future__ import annotations

import json
import math
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.fulltext_variants import (
    BuiltFulltextQuery,
    build_c1_query,
    extract_query_tokens,
)
from evaluation.chunking_experiment import paired_statistics

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ROOT = ROOT / "evaluation" / "experiments" / "fulltext"
PROTOCOL_REFERENCE = (
    "docs/architecture-review/08-retrieval-ablation-protocol.md"
)
STOP_WORDS_SQL = text(
    "SELECT lexemes FROM ts_debug('english', :term)"
)
ANSWERABLE_CATEGORIES = {"direct", "paraphrased"}
TESTS_PREFIX = "tests/"
BOOTSTRAP_PROTOCOL = {
    "statistics": {
        "bootstrap_seed": 20261026,
        "bootstrap_resamples": 10000,
        "bootstrap_interval": 0.95,
    }
}
DECISION_THRESHOLDS = {
    "maximum_repository_hit_at_5_loss": 1,
    "maximum_repository_span_mrr_loss": 0.03,
    "minimum_pooled_span_mrr_delta": 0.02,
    "nonempty_text_branch_share_must_increase": True,
}


async def build_protocol_query(
    session: AsyncSession,
    question: str,
) -> BuiltFulltextQuery:
    """Build c1 using stop words reported by PostgreSQL's English config."""

    stop_words: set[str] = set()
    for token in extract_query_tokens(question):
        rows = (
            await session.execute(STOP_WORDS_SQL, {"term": token})
        ).scalars().all()
        if not any(row for row in rows):
            stop_words.add(token)
    return build_c1_query(question, stop_words)


def reciprocal_rank(rank: int | None) -> float:
    return 1.0 / rank if rank is not None else 0.0


def unique_source_characters(
    retrieved: Sequence[Mapping[str, Any]],
    source_lines: Mapping[tuple[str, int], str],
) -> int:
    """Count raw characters over the union of retrieved file-line ranges."""

    line_ids: set[tuple[str, int]] = set()
    for result in retrieved[:5]:
        file_path = str(result["file_path"])
        start = int(result["line_start"])
        end = int(result["line_end"])
        if start > end:
            raise ValueError(f"Invalid source range for {file_path}: {start}-{end}")
        line_ids.update((file_path, line) for line in range(start, end + 1))
    missing = sorted(line_id for line_id in line_ids if line_id not in source_lines)
    if missing:
        raise ValueError(f"Missing source text for retrieved lines: {missing[:5]}")
    return sum(len(source_lines[line_id]) + 1 for line_id in line_ids)


def _nearest_rank(values: Sequence[int], quantile: float) -> int:
    if not values:
        return 0
    if not 0 < quantile <= 1:
        raise ValueError("quantile must be in (0, 1]")
    return sorted(values)[math.ceil(quantile * len(values)) - 1]


def _nearest_rank_float(values: Sequence[float], quantile: float) -> float:
    if not values:
        return 0.0
    if not 0 < quantile <= 1:
        raise ValueError("quantile must be in (0, 1]")
    return sorted(values)[math.ceil(quantile * len(values)) - 1]


def summarize_variant(
    questions: Sequence[Mapping[str, Any]],
    source_lines: Mapping[tuple[str, int], str],
) -> dict[str, Any]:
    """Summarize span quality, text-branch coverage, test share, and raw cost."""

    answerable = [
        row
        for row in questions
        if row["category"] in ANSWERABLE_CATEGORIES
    ]
    count = len(answerable)
    if not count:
        raise ValueError("Cannot summarize an empty answerable question set")

    hit_counts = {
        str(k): sum(
            row["span_rank"] is not None and row["span_rank"] <= k
            for row in answerable
        )
        for k in (1, 3, 5)
    }
    reciprocal_ranks = [
        reciprocal_rank(row["span_rank"]) for row in answerable
    ]
    costs = [
        int(row["raw_source_characters"])
        if "raw_source_characters" in row
        else unique_source_characters(row.get("retrieved", []), source_lines)
        for row in answerable
    ]
    retrieved = [
        result
        for row in answerable
        for result in row.get("retrieved", [])[:5]
    ]
    test_count = sum(
        str(result["file_path"]).startswith(TESTS_PREFIX) for result in retrieved
    )
    text_nonempty = sum(bool(row.get("text_branch_nonempty")) for row in answerable)
    return {
        "question_count": count,
        "hit_at_1": {
            "successes": hit_counts["1"],
            "rate": hit_counts["1"] / count,
        },
        "hit_at_3": {
            "successes": hit_counts["3"],
            "rate": hit_counts["3"] / count,
        },
        "hit_at_5": {
            "successes": hit_counts["5"],
            "rate": hit_counts["5"] / count,
        },
        "span_mrr": sum(reciprocal_ranks) / count,
        "nonempty_text_branch": {
            "questions": text_nonempty,
            "share": text_nonempty / count,
        },
        "top5_tests": {
            "results": test_count,
            "retrieved_results": len(retrieved),
            "share": test_count / len(retrieved) if retrieved else 0.0,
        },
        "top5_unique_raw_source_characters": {
            "mean": sum(costs) / len(costs),
            "p95_nearest_rank": _nearest_rank(costs, 0.95),
        },
        "top5_unique_raw_source_characters_by_question": costs,
        "question_reciprocal_ranks": reciprocal_ranks,
    }


def paired_comparison(
    candidate: Mapping[str, Any],
    comparator: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    """Pair ranks by report order and reuse the chunking bootstrap method."""

    if candidate["question_ids"] != comparator["question_ids"]:
        raise ValueError("Paired reports must have the same question IDs")
    candidate_rr = candidate["summary"]["question_reciprocal_ranks"]
    comparator_rr = comparator["summary"]["question_reciprocal_ranks"]
    return paired_statistics(candidate_rr, comparator_rr, protocol)


def decide_variant(
    candidate: Mapping[str, Any],
    control: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply the four registered quality conditions against fixed control."""

    repo_ids = sorted(control["repositories"])
    if repo_ids != sorted(candidate["repositories"]):
        raise ValueError("Candidate and control repositories do not match")
    conditions = {
        "no_repository_loses_more_than_one_hit_at_5": all(
            control["repositories"][repo]["summary"]["hit_at_5"]["successes"]
            - candidate["repositories"][repo]["summary"]["hit_at_5"]["successes"]
            <= DECISION_THRESHOLDS["maximum_repository_hit_at_5_loss"]
            for repo in repo_ids
        ),
        "no_repository_loses_more_than_0_03_span_mrr": all(
            control["repositories"][repo]["summary"]["span_mrr"]
            - candidate["repositories"][repo]["summary"]["span_mrr"]
            <= DECISION_THRESHOLDS["maximum_repository_span_mrr_loss"]
            for repo in repo_ids
        ),
        "pooled_span_mrr_delta_at_least_0_02": (
            candidate["pooled"]["summary"]["span_mrr"]
            - control["pooled"]["summary"]["span_mrr"]
            >= DECISION_THRESHOLDS["minimum_pooled_span_mrr_delta"]
        ),
        "nonempty_text_branch_share_larger": (
            candidate["pooled"]["summary"]["nonempty_text_branch"]["share"]
            > control["pooled"]["summary"]["nonempty_text_branch"]["share"]
        ),
    }
    return {
        "qualifies": all(conditions.values()),
        "conditions": conditions,
        "decision": (
            "advance to item 14c-3"
            if all(conditions.values())
            else "retain current behavior"
        ),
        "thresholds": DECISION_THRESHOLDS,
        "rule_source": PROTOCOL_REFERENCE,
    }


def _execution_ms(explain_result: Any) -> float:
    if not isinstance(explain_result, list) or not explain_result:
        raise ValueError("PostgreSQL EXPLAIN returned an unexpected result")
    plan = explain_result[0]
    if not isinstance(plan, dict) or "Execution Time" not in plan:
        raise ValueError("PostgreSQL EXPLAIN omitted Execution Time")
    return float(plan["Execution Time"])


def _plan_uses_index(explain_result: Any) -> bool:
    text_value = json.dumps(explain_result, sort_keys=True)
    return "fulltext_c3_search_vector_idx" in text_value


async def run_c3_equivalence(
    session: AsyncSession,
    chunks: Sequence[Mapping[str, Any]],
    questions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Check query-time/generated-vector equivalence and collect EXPLAIN timings."""

    await session.execute(
        text(
            """
            CREATE TEMP TABLE fulltext_c3_chunks (
                id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                file_path text NOT NULL,
                line_start integer NOT NULL,
                line_end integer NOT NULL,
                content text NOT NULL,
                search_vector tsvector GENERATED ALWAYS AS (
                    to_tsvector('english', content)
                ) STORED
            ) ON COMMIT DROP
            """
        )
    )
    try:
        if chunks:
            await session.execute(
                text(
                    """
                    INSERT INTO fulltext_c3_chunks
                        (file_path, line_start, line_end, content)
                    VALUES
                        (:file_path, :line_start, :line_end, :content)
                    """
                ),
                [
                    {
                        "file_path": chunk["file_path"],
                        "line_start": chunk["line_start"],
                        "line_end": chunk["line_end"],
                        "content": chunk["content"],
                    }
                    for chunk in chunks
                ],
            )
        await session.execute(
            text(
                "CREATE INDEX fulltext_c3_search_vector_idx "
                "ON fulltext_c3_chunks USING GIN (search_vector)"
            )
        )
        await session.execute(text("ANALYZE fulltext_c3_chunks"))
        query_time_sql = text(
            """
            SELECT id FROM fulltext_c3_chunks
            WHERE to_tsvector('english', content)
                  @@ websearch_to_tsquery(:query_text)
            ORDER BY file_path, line_start, line_end
            """
        )
        generated_sql = text(
            """
            SELECT id FROM fulltext_c3_chunks
            WHERE search_vector @@ websearch_to_tsquery(:query_text)
            ORDER BY file_path, line_start, line_end
            """
        )
        explain_query_time = text(
            """
            EXPLAIN (ANALYZE, FORMAT JSON)
            SELECT id FROM fulltext_c3_chunks
            WHERE to_tsvector('english', content)
                  @@ websearch_to_tsquery(:query_text)
            ORDER BY file_path, line_start, line_end
            """
        )
        explain_generated = text(
            """
            EXPLAIN (ANALYZE, FORMAT JSON)
            SELECT id FROM fulltext_c3_chunks
            WHERE search_vector @@ websearch_to_tsquery(:query_text)
            ORDER BY file_path, line_start, line_end
            """
        )
        question_results: list[dict[str, Any]] = []
        for question in questions:
            parameters = {"query_text": str(question["question"])}
            query_time_ids = list(
                (
                    await session.execute(query_time_sql, parameters)
                ).scalars().all()
            )
            generated_ids = list(
                (
                    await session.execute(generated_sql, parameters)
                ).scalars().all()
            )
            query_explain = (
                await session.execute(explain_query_time, parameters)
            ).scalar_one()
            generated_explain = (
                await session.execute(explain_generated, parameters)
            ).scalar_one()
            question_results.append(
                {
                    "question_id": str(question["id"]),
                    "equivalent": query_time_ids == generated_ids,
                    "query_time_match_count": len(query_time_ids),
                    "generated_vector_match_count": len(generated_ids),
                    "query_time_execution_ms": _execution_ms(query_explain),
                    "generated_vector_execution_ms": _execution_ms(generated_explain),
                    "generated_vector_index_used": _plan_uses_index(generated_explain),
                }
            )
        if any(not result["equivalent"] for result in question_results):
            raise RuntimeError("c3 generated-vector results differ from query-time FTS")
        query_times = [
            row["query_time_execution_ms"] for row in question_results
        ]
        generated_times = [
            row["generated_vector_execution_ms"] for row in question_results
        ]
        return {
            "chunk_count": len(chunks),
            "question_count": len(question_results),
            "all_questions_equivalent": True,
            "query_time_execution_ms_median": statistics.median(query_times),
            "query_time_execution_ms_p95_nearest_rank": _nearest_rank_float(
                query_times, 0.95
            ),
            "generated_vector_execution_ms_median": statistics.median(
                generated_times
            ),
            "generated_vector_execution_ms_p95_nearest_rank": _nearest_rank_float(
                generated_times, 0.95
            ),
            "generated_vector_index_used_questions": sum(
                row["generated_vector_index_used"] for row in question_results
            ),
            "questions": question_results,
        }
    finally:
        await session.execute(text("DROP TABLE IF EXISTS fulltext_c3_chunks"))
