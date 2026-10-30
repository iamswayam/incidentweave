"""Report test-file representation and control retrieval in development fixtures."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import AsyncSessionLocal  # noqa: E402
from evaluation.build_fixture import load_fixture  # noqa: E402
from evaluation.manifest import (  # noqa: E402
    MANIFEST_PATH,
    questions_for_split,
    sha256_file,
)
from evaluation.test_file_diagnostic import (  # noqa: E402
    build_repository_diagnostic,
    reconcile_control,
)

DEFAULT_OUTPUT = Path("docs/notes/11-test-file-diagnostic.md")
TOP_FIVE = 5
CONTROL_SQL = text(
    """
    WITH fixture_chunks AS (
        SELECT *
        FROM jsonb_to_recordset(CAST(:fixture_chunks AS jsonb)) AS chunk(
            id integer,
            file_path text,
            line_start integer,
            line_end integer,
            content text,
            embedding text
        )
    ),
    vector_ranked AS (
        SELECT
            chunk.*,
            CAST(chunk.embedding AS vector)
                <=> CAST(:query_embedding AS vector) AS distance,
            row_number() OVER (
                ORDER BY
                    CAST(chunk.embedding AS vector)
                        <=> CAST(:query_embedding AS vector),
                    chunk.file_path,
                    chunk.line_start,
                    chunk.line_end
            ) AS vector_rank
        FROM fixture_chunks AS chunk
        WHERE chunk.embedding IS NOT NULL
    ),
    vector_top AS (
        SELECT * FROM vector_ranked WHERE vector_rank <= :limit
    ),
    fulltext_ranked AS (
        SELECT
            chunk.*,
            ts_rank_cd(
                to_tsvector('english', chunk.content),
                websearch_to_tsquery(:query_text)
            ) AS score,
            row_number() OVER (
                ORDER BY
                    ts_rank_cd(
                        to_tsvector('english', chunk.content),
                        websearch_to_tsquery(:query_text)
                    ) DESC,
                    chunk.file_path,
                    chunk.line_start,
                    chunk.line_end
            ) AS fulltext_rank
        FROM fixture_chunks AS chunk
        WHERE to_tsvector('english', chunk.content)
              @@ websearch_to_tsquery(:query_text)
    ),
    fulltext_top AS (
        SELECT * FROM fulltext_ranked WHERE fulltext_rank <= :limit
    ),
    candidates AS (
        SELECT id FROM vector_top
        UNION
        SELECT id FROM fulltext_top
    )
    SELECT
        COALESCE(vector.file_path, fulltext.file_path) AS file_path,
        COALESCE(vector.line_start, fulltext.line_start) AS line_start,
        COALESCE(vector.line_end, fulltext.line_end) AS line_end,
        COALESCE(vector.content, fulltext.content) AS content,
        vector.distance AS vector_score,
        fulltext.score AS fts_score,
        (
            CASE
                WHEN vector.vector_rank IS NULL THEN 0.0
                ELSE 1.0 / (60 + vector.vector_rank)
            END
            +
            CASE
                WHEN fulltext.fulltext_rank IS NULL THEN 0.0
                ELSE 1.0 / (60 + fulltext.fulltext_rank)
            END
        ) AS rrf_score,
        vector.vector_rank,
        fulltext.fulltext_rank
    FROM candidates
    LEFT JOIN vector_top AS vector USING (id)
    LEFT JOIN fulltext_top AS fulltext USING (id)
    ORDER BY
        rrf_score DESC,
        COALESCE(vector.vector_rank, 2147483647),
        COALESCE(fulltext.fulltext_rank, 2147483647),
        COALESCE(vector.file_path, fulltext.file_path),
        COALESCE(vector.line_start, fulltext.line_start),
        COALESCE(vector.line_end, fulltext.line_end)
    LIMIT :limit
    """
)


def _skip_space(value: str, position: int) -> int:
    while position < len(value) and value[position].isspace():
        position += 1
    return position


def _json_value_end(value: str, position: int) -> int:
    """Find a JSON value's end without decoding its strings or nested fields."""

    if position >= len(value):
        raise ValueError("Unexpected end of question-set JSON")
    if value[position] == '"':
        escaped = False
        for index in range(position + 1, len(value)):
            character = value[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                return index + 1
        raise ValueError("Unterminated JSON string in question set")

    if value[position] in "[{":
        closers = {"[": "]", "{": "}"}
        stack = [closers[value[position]]]
        in_string = False
        escaped = False
        for index in range(position + 1, len(value)):
            character = value[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
            elif character in closers:
                stack.append(closers[character])
            elif character in "]}":
                if not stack or character != stack.pop():
                    raise ValueError("Mismatched JSON structure in question set")
                if not stack:
                    return index + 1
        raise ValueError("Unterminated JSON structure in question set")

    end = position
    while end < len(value) and value[end] not in ",]} \t\r\n":
        end += 1
    if end == position:
        raise ValueError("Invalid JSON value in question set")
    return end


def _question_id(raw_question: str) -> str:
    decoder = json.JSONDecoder()
    position = _skip_space(raw_question, 0)
    if raw_question[position] != "{":
        raise ValueError("Every question record must be a JSON object")
    position += 1
    while True:
        position = _skip_space(raw_question, position)
        if raw_question[position] == "}":
            break
        key, key_end = decoder.raw_decode(raw_question, position)
        if not isinstance(key, str):
            raise ValueError("Question object keys must be strings")
        position = _skip_space(raw_question, key_end)
        if raw_question[position] != ":":
            raise ValueError("Invalid question object")
        value_start = _skip_space(raw_question, position + 1)
        value_end = _json_value_end(raw_question, value_start)
        if key == "id":
            question_id = json.loads(raw_question[value_start:value_end])
            if not isinstance(question_id, str) or not question_id:
                raise ValueError("Every question needs a non-empty id")
            return question_id
        position = _skip_space(raw_question, value_end)
        if raw_question[position] == ",":
            position += 1
        elif raw_question[position] != "}":
            raise ValueError("Invalid question object separator")
    raise ValueError("Every question needs an id")


def _development_question_records(
    question_path: Path,
    development_ids: set[str],
) -> list[dict[str, Any]]:
    """Decode only development question records; skip all other record values."""

    raw = question_path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    position = _skip_space(raw, 0)
    if raw[position] != "{":
        raise ValueError("Question set must be a JSON object")
    position += 1

    while True:
        position = _skip_space(raw, position)
        if raw[position] == "}":
            break
        key, key_end = decoder.raw_decode(raw, position)
        if not isinstance(key, str):
            raise ValueError("Question-set keys must be strings")
        position = _skip_space(raw, key_end)
        if raw[position] != ":":
            raise ValueError("Invalid question-set object")
        value_start = _skip_space(raw, position + 1)
        if key != "questions":
            value_end = _json_value_end(raw, value_start)
            position = _skip_space(raw, value_end)
            if raw[position] == ",":
                position += 1
                continue
            if raw[position] == "}":
                break
            raise ValueError("Invalid question-set separator")
        if raw[value_start] != "[":
            raise ValueError("Question-set questions must be an array")

        selected: list[dict[str, Any]] = []
        position = value_start + 1
        while True:
            position = _skip_space(raw, position)
            if raw[position] == "]":
                return selected
            record_end = _json_value_end(raw, position)
            record = raw[position:record_end]
            if _question_id(record) in development_ids:
                question = json.loads(record)
                if not isinstance(question, dict):
                    raise ValueError("Every selected question must be an object")
                selected.append(question)
            position = _skip_space(raw, record_end)
            if raw[position] == ",":
                position += 1
            elif raw[position] == "]":
                return selected
            else:
                raise ValueError("Invalid question array separator")

    raise ValueError("Question set has no questions array")


def _vector_literal(values: list[float]) -> str:
    if not values:
        raise ValueError("Embedding vectors must not be empty")
    return "[" + ",".join(str(float(value)) for value in values) + "]"


async def _control_top_five(
    chunks: list[dict[str, Any]],
    question_text: str,
    query_embedding: list[float],
) -> list[dict[str, Any]]:
    fixture_chunks = []
    for index, chunk in enumerate(chunks, start=1):
        embedding = chunk.get("embedding")
        if not isinstance(embedding, list):
            raise ValueError("Every fixture chunk needs an embedding vector")
        fixture_chunks.append(
            {
                "id": index,
                "file_path": chunk["file_path"],
                "line_start": chunk["line_start"],
                "line_end": chunk["line_end"],
                "content": chunk["content"],
                "embedding": _vector_literal(embedding),
            }
        )

    async with AsyncSessionLocal() as session:
        await session.execute(text("SET TRANSACTION READ ONLY"))
        rows = (
            await session.execute(
                CONTROL_SQL,
                {
                    "fixture_chunks": json.dumps(fixture_chunks),
                    "query_embedding": _vector_literal(query_embedding),
                    "query_text": question_text,
                    "limit": TOP_FIVE,
                },
            )
        ).mappings().all()
    return [
        {
            "file_path": row["file_path"],
            "line_start": row["line_start"],
            "line_end": row["line_end"],
            "content": row["content"],
            "vector_score": (
                float(row["vector_score"])
                if row["vector_score"] is not None
                else None
            ),
            "fts_score": float(row["fts_score"]) if row["fts_score"] is not None else None,
            "rrf_score": float(row["rrf_score"]),
        }
        for row in rows
    ]


async def collect_diagnostics(manifest_path: Path = MANIFEST_PATH) -> list[dict[str, Any]]:
    """Run control retrieval against fixture CTEs for development questions only."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("repositories"), list):
        raise ValueError("Evaluation manifest must contain a repositories list")

    output: list[dict[str, Any]] = []
    for entry in manifest["repositories"]:
        repository_id = entry["id"]
        question_resource = entry["questions"]
        question_path = manifest_path.resolve().parent.parent / question_resource["path"]
        if sha256_file(question_path) != question_resource["sha256"]:
            raise ValueError(f"{repository_id}: question-set SHA-256 mismatch")
        development_ids = set(entry["splits"]["development"])
        questions = questions_for_split(
            entry,
            _development_question_records(question_path, development_ids),
            "development",
        )
        if len(questions) != len(development_ids):
            raise ValueError(
                f"{repository_id}: development question records do not match manifest"
            )

        fixture_path = manifest_path.resolve().parent.parent / entry["fixture"]["path"]
        baseline_path = manifest_path.resolve().parent.parent / entry["full_baseline"]["path"]
        baseline_questions = questions_for_split(
            entry,
            _development_question_records(baseline_path, development_ids),
            "development",
        )

        fixture = load_fixture(fixture_path)
        chunks = fixture["chunks"]
        fixture_queries = fixture["queries"]
        results_by_question: dict[str, list[dict[str, Any]]] = {}
        for question in questions:
            question_id = str(question["id"])
            if question_id not in fixture_queries:
                raise ValueError(
                    f"{repository_id}: fixture is missing a development query embedding"
                )
            results_by_question[question_id] = await _control_top_five(
                chunks,
                str(question["question"]),
                fixture_queries[question_id],
            )
        repository_diagnostic = build_repository_diagnostic(
            chunks, questions, results_by_question
        )
        repository_diagnostic["control_reconciliation"] = reconcile_control(
            questions,
            results_by_question,
            baseline_questions,
        )
        output.append({"repository": repository_id, **repository_diagnostic})
    return output


def render_diagnostic(repositories: list[dict[str, Any]]) -> str:
    """Render a diagnostic note without question IDs or question text."""

    lines = [
        "# Test-file retrieval diagnostic",
        "",
        "## Method",
        "",
        "The classifier applies the path rules in `evaluation/test_files.py` to fixture chunk "
        "paths. Only development question records are decoded and selected through the manifest "
        "split helper. The control is the production hybrid retrieval: exact pgvector cosine "
        "ranking and PostgreSQL English full-text ranking, fused with RRF (constant 60) and the "
        "production deterministic tie-break. Fixture chunks are supplied through a query-local "
        "JSONB CTE; the query runs in a read-only PostgreSQL transaction and does not insert or "
        "modify rows. Cached fixture query embeddings are used; no provider is called.",
        "",
        "## Held-out handling disclosure",
        "",
        "During the review of item 14b-1, an assistant opened the first lines of the committed "
        "baseline files directly instead of through the development split helper. This exposed "
        "baseline row metadata for a small number of held-out rows and an all-split summary in a "
        "tool output. No held-out question text was opened, no held-out retrieval or provider "
        "call was run, and nothing exposed was used for any decision in this item. It is recorded "
        "here so the single registered held-out run in item 3b can take it into account. All "
        "later access to baseline and question files goes through the development split helper "
        "only.",
        "",
        "## Control reconciliation",
        "",
        "Baseline label ranks were compared only for the 11 answerable development questions "
        "per repository. Rank `—` means no substring match in the top five. Hit@5 and MRR use "
        "these 11 questions as the denominator, counting misses as zero for MRR. Unanswerable "
        "questions were not compared because the baseline rows expose no evidence-guard decision. "
        "The earlier aggregate comparison used all-split totals and is replaced by this "
        "development-only comparison.",
        "",
        "| Repository | Answerable questions compared | Identical ranks | "
        "Baseline label_rank present | Differing ranks (ordinal: baseline → diagnostic) | "
        "Baseline hit@5; MRR | "
        "Diagnostic hit@5; MRR | Unanswerable guard | Verdict |",
        "|---:|---:|---:|---:|---|---|---|---|---|",
    ]
    for repository in repositories:
        reconciliation = repository["control_reconciliation"]
        differing = ", ".join(
            f"{row['ordinal']}: {row['baseline_rank'] or '—'} → "
            f"{row['diagnostic_rank'] or '—'}"
            for row in reconciliation["differing_ranks"]
        ) or "none"
        baseline_metrics = reconciliation["baseline_metrics"]
        diagnostic_metrics = reconciliation["diagnostic_metrics"]
        lines.append(
            f"| {repository['repository']} | "
            f"{reconciliation['questions_compared']} | "
            f"{reconciliation['identical_rank_count']} | "
            f"{reconciliation['baseline_label_rank_count']} | {differing} | "
            f"{baseline_metrics['hit_at_5_successes']}; "
            f"{baseline_metrics['mrr']:.6f} | "
            f"{diagnostic_metrics['hit_at_5_successes']}; "
            f"{diagnostic_metrics['mrr']:.6f} | "
            f"{reconciliation['unanswerable_guard_comparison']} | "
            f"{reconciliation['verdict']} |"
        )
    lines.extend(
        [
            "",
        ]
    )
    lines.extend(
        [
            "## Per-repository results",
            "",
            "| Repository | Chunks | Tagged test chunks | Tagged share | "
            "Top-5 tagged test results | Top-5 results | Top-5 test share | "
            "Answerable questions with test-file evidence | Hit at rank <=5 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for repository in repositories:
        lines.append(
            f"| {repository['repository']} | {repository['total_chunks']} | "
            f"{repository['tagged_chunk_count']} | "
            f"{repository['tagged_chunk_share']:.1%} | "
            f"{repository['top5_test_chunk_count']} | "
            f"{repository['top5_result_count']} | "
            f"{repository['top5_test_share']:.1%} | "
            f"{repository['answerable_test_evidence_question_count']} | "
            f"{repository['answerable_test_evidence_hit_at_5']} |"
        )

    pooled_tagged = sum(repo["top5_test_chunk_count"] for repo in repositories)
    pooled_results = sum(repo["top5_result_count"] for repo in repositories)
    lines.extend(
        [
            f"| **Pooled** | {sum(repo['total_chunks'] for repo in repositories)} | "
            f"{sum(repo['tagged_chunk_count'] for repo in repositories)} | — | "
            f"{pooled_tagged} | {pooled_results} | "
            f"{pooled_tagged / pooled_results:.1%} | "
            f"{sum(repo['answerable_test_evidence_question_count'] for repo in repositories)} | "
            f"{sum(repo['answerable_test_evidence_hit_at_5'] for repo in repositories)} |",
            "",
            "### Tagged paths",
            "",
        ]
    )
    for repository in repositories:
        lines.extend([f"#### `{repository['repository']}`", ""])
        paths = repository["tagged_paths"]
        lines.extend([f"- `{path}`" for path in paths] if paths else ["- (none)"])
        lines.append("")

    lines.extend(["### Untagged paths containing `test` (manual review)", ""])
    for repository in repositories:
        lines.extend([f"#### `{repository['repository']}`", ""])
        paths = repository["untagged_test_paths"]
        lines.extend([f"- `{path}`" for path in paths] if paths else ["- (none)"])
        lines.append("")

    lines.extend(
        [
            "### Tagged test chunks in each development question's top five",
            "",
            "| Repository | Development question ordinal | Tagged test chunks in top five |",
            "|---|---:|---:|",
        ]
    )
    for repository in repositories:
        for ordinal, count in enumerate(repository["question_top5_test_counts"], start=1):
            lines.append(f"| {repository['repository']} | {ordinal} | {count} |")

    lines.extend(
        [
            "",
            "## What this does not show",
            "",
            "This is a descriptive control inventory, not a comparison of ranking variants and "
            "not evidence that test files should be downweighted or excluded. It does not measure "
            "answer quality, guard outcomes, or whether test-file evidence is preferable for a "
            "particular query. The small development fixtures do not establish generalization "
            "beyond these repositories.",
            "",
        ]
    )
    return "\n".join(lines)


async def _run(output_path: Path | None) -> None:
    repositories = await collect_diagnostics()
    rendered = render_diagnostic(repositories)
    if output_path is None:
        print(rendered, end="")
        return
    resolved_output = ROOT / output_path
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(rendered, encoding="utf-8")
    print(f"Wrote diagnostic to {resolved_output.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        nargs="?",
        const=DEFAULT_OUTPUT,
        default=None,
        type=Path,
        metavar="PATH",
        help=(
            "write the report to PATH (default when specified: "
            f"{DEFAULT_OUTPUT.as_posix()}); without this option, write no file"
        ),
    )
    args = parser.parse_args()
    try:
        asyncio.run(_run(args.output))
    except (OSError, SQLAlchemyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
