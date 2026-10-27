"""Diagnose full-text query behavior against committed development fixtures."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import Chunk, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from evaluation.build_fixture import load_fixture  # noqa: E402
from evaluation.fulltext_diagnostic import (  # noqa: E402
    build_or_query,
    classify_query_terms,
    extract_query_terms,
)
from evaluation.golden import load_golden_set  # noqa: E402
from evaluation.manifest import (  # noqa: E402
    load_manifest,
    questions_for_split,
)
from evaluation.metrics import is_relevant_span  # noqa: E402

DEFAULT_OUTPUT = ROOT / "docs" / "notes" / "08-fulltext-diagnostic.md"
TEXT_SEARCH_CONFIG_SQL = text(
    "SELECT current_setting('default_text_search_config')"
)
LEXEMES_SQL = text(
    "SELECT lexemes FROM ts_debug(CAST(:config AS regconfig), :term)"
)
TSQUERY_SQL = text(
    "SELECT websearch_to_tsquery(:query_text)::text AS tsquery"
)
MATCHING_CHUNKS_SQL = text(
    """
    SELECT c.file_path, c.line_start, c.line_end, c.content
    FROM chunks AS c
    WHERE c.repository_id = :repository_id
      AND to_tsvector('english', c.content)
          @@ websearch_to_tsquery(:query_text)
    ORDER BY c.file_path, c.line_start, c.line_end
    """
)


def _answerable(question: dict[str, Any]) -> bool:
    return question.get("category") in {"direct", "paraphrased"}


def _corpus_terms(chunks: list[dict[str, Any]]) -> set[str]:
    terms: set[str] = set()
    for chunk in chunks:
        terms.update(
            term.casefold()
            for term in extract_query_terms(str(chunk.get("content", "")))
        )
    return terms


async def _delete_repository(name: str) -> None:
    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == name)
        )
        if repository is not None:
            await session.delete(repository)
            await session.commit()


async def _insert_fixture_repository(
    repo_id: str,
    chunks: list[dict[str, Any]],
) -> tuple[str, int]:
    name = f"incidentweave-fulltext-diagnostic-{repo_id}-{uuid4().hex}"
    async with AsyncSessionLocal() as session:
        repository = Repository(name=name)
        session.add(repository)
        await session.flush()
        repository_id = repository.id
        session.add_all(
            [
                Chunk(
                    repository_id=repository_id,
                    file_path=str(chunk["file_path"]),
                    line_start=chunk["line_start"],
                    line_end=chunk["line_end"],
                    content=str(chunk["content"]),
                    content_hash=hashlib.sha256(
                        str(chunk["content"]).encode("utf-8")
                    ).hexdigest(),
                )
                for chunk in chunks
            ]
        )
        await session.commit()
    return name, repository_id


async def _query_term_lexemes(
    terms: list[str],
    text_search_config: str,
) -> dict[str, list[str]]:
    lexemes_by_term: dict[str, list[str]] = {}
    async with AsyncSessionLocal() as session:
        for term in terms:
            rows = (
                await session.execute(
                    LEXEMES_SQL,
                    {"config": text_search_config, "term": term},
                )
            ).mappings().all()
            lexemes_by_term[term] = [
                str(lexeme)
                for row in rows
                for lexeme in (row["lexemes"] or [])
            ]
    return lexemes_by_term


async def _diagnose_question(
    repository_id: int,
    question: dict[str, Any],
    corpus_terms: set[str],
    lexeme_cache: dict[str, list[str]],
    text_search_config: str,
) -> dict[str, Any]:
    query = str(question["question"])
    terms = extract_query_terms(query)
    missing_lexemes = [term for term in terms if term not in lexeme_cache]
    lexeme_cache.update(
        await _query_term_lexemes(missing_lexemes, text_search_config)
    )
    term_analysis = classify_query_terms(terms, lexeme_cache, corpus_terms)
    or_query = build_or_query(terms)

    async with AsyncSessionLocal() as session:
        tsquery = str(
            (
                await session.execute(TSQUERY_SQL, {"query_text": query})
            ).scalar_one()
        )
        and_matches = (
            await session.execute(
                MATCHING_CHUNKS_SQL,
                {"repository_id": repository_id, "query_text": query},
            )
        ).mappings().all()
        or_matches = (
            await session.execute(
                MATCHING_CHUNKS_SQL,
                {"repository_id": repository_id, "query_text": or_query},
            )
        ).mappings().all()

    spans = question.get("relevant_spans", [])
    return {
        "question_id": str(question["id"]),
        "category": str(question["category"]),
        "query": query,
        "tsquery": tsquery,
        "and_match_count": len(and_matches),
        "or_query": or_query,
        "or_match_count": len(or_matches),
        "or_evidence_match": any(
            is_relevant_span(match, spans) for match in or_matches
        ),
        **term_analysis,
    }


async def collect_diagnostics() -> list[dict[str, Any]]:
    """Run fixture-backed FTS diagnostics for answerable development questions."""

    manifest = load_manifest()
    async with AsyncSessionLocal() as session:
        text_search_config = str(
            (await session.execute(TEXT_SEARCH_CONFIG_SQL)).scalar_one()
        )
    output: list[dict[str, Any]] = []
    for entry in manifest["repositories"]:
        repo_id = str(entry["id"])
        fixture_path = ROOT / entry["fixture"]["path"]
        question_path = ROOT / entry["questions"]["path"]
        fixture = load_fixture(fixture_path)
        golden = load_golden_set(question_path)
        questions = [
            question
            for question in questions_for_split(
                entry, golden["questions"], "development"
            )
            if _answerable(question)
        ]
        chunks = fixture["chunks"]
        corpus_terms = _corpus_terms(chunks)
        repository_name, repository_id = await _insert_fixture_repository(
            repo_id, chunks
        )
        lexeme_cache: dict[str, list[str]] = {}
        try:
            question_rows = [
                await _diagnose_question(
                    repository_id,
                    question,
                    corpus_terms,
                    lexeme_cache,
                    text_search_config,
                )
                for question in questions
            ]
        finally:
            await _delete_repository(repository_name)
        output.append(
            {
                "repo_id": repo_id,
                "text_search_config": text_search_config,
                "answerable_questions": len(question_rows),
                "questions": question_rows,
            }
        )
    return output


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _list_cell(values: list[str]) -> str:
    return ", ".join(_cell(value) for value in values) if values else "—"


def render_diagnostic(results: list[dict[str, Any]]) -> str:
    """Render a deterministic method, summary, question table, and conclusion."""

    total_questions = sum(repo["answerable_questions"] for repo in results)
    total_and_empty = sum(
        row["and_match_count"] == 0
        for repo in results
        for row in repo["questions"]
    )
    total_or_nonempty = sum(
        row["or_match_count"] > 0
        for repo in results
        for row in repo["questions"]
    )
    lines = [
        "# Full-text diagnostic (item 14c-1)",
        "",
        "## Method",
        "",
        "The diagnostic loads each manifest repository's committed S0 fixture and questions, "
        "then uses the local PostgreSQL database to evaluate full-text expressions. It "
        "temporarily inserts fixture chunks under an isolated repository name and deletes that "
        "temporary repository after the report is collected. Query strings and diagnostics use "
        "bound parameters; no retrieval code, fixtures, baselines, or gates are changed.",
        "",
        "For each answerable development question, the current query is the question text passed "
        "to `websearch_to_tsquery(:query_text)` in `app/retrieval/fulltext_search.py`. Its parsed "
        "tsquery is reported directly from PostgreSQL. Stop-word and stemming inspection uses "
        f"the database's `{results[0]['text_search_config']}` configuration. The diagnostic OR "
        "probe is the unique, "
        "case-preserving `[A-Za-z0-9_]` tokens from that question, including stop words, each "
        "quoted and joined with `OR`; it is broader than protocol variant c1. OR evidence "
        "overlap uses the question's labeled source spans. Terms absent from "
        "the repository are determined by exact, case-insensitive token presence in fixture "
        "chunk text. Stop-word removal, stemming, and identifier splitting are reported from "
        "`ts_debug` under that configuration. Stemming means PostgreSQL emitted one lexeme "
        "different "
        "from the input token; multi-lexeme decomposition is reported separately.",
        "",
        "## Per-repository summary",
        "",
        "| Repository | Answerable development questions | "
        "Current query has no matches | OR query has matches | "
        "OR matches labeled evidence |",
        "|---|---:|---:|---:|---:|",
    ]
    for repo in results:
        questions = repo["questions"]
        lines.append(
            f"| {repo['repo_id']} | {len(questions)} | "
            f"{sum(row['and_match_count'] == 0 for row in questions)} | "
            f"{sum(row['or_match_count'] > 0 for row in questions)} | "
            f"{sum(row['or_evidence_match'] for row in questions)} |"
        )
    lines.extend(
        [
            "",
            "## Per-question results",
            "",
            "| Repository | Question | Current query (exact) | PostgreSQL tsquery | "
            "Current matches | OR query | OR matches | OR evidence overlap | "
            "Dropped stop words | Stemmed terms | Split into lexemes | "
            "Terms absent from repo chunks |",
            "|---|---|---|---|---:|---|---:|---|---|---|---|---|",
        ]
    )
    for repo in results:
        for row in repo["questions"]:
            lines.append(
                f"| {repo['repo_id']} | {row['question_id']} | "
                f"`{_cell(row['query'])}` | `{_cell(row['tsquery'])}` | "
                f"{row['and_match_count']} | `{_cell(row['or_query'])}` | "
                f"{row['or_match_count']} | "
                f"{'yes' if row['or_evidence_match'] else 'no'} | "
                f"{_list_cell(row['dropped_stop_words'])} | "
                f"{_list_cell(row['stemmed'])} | "
                f"{_list_cell(row['split_into_lexemes'])} | "
                f"{_list_cell(row['absent_from_corpus'])} |"
            )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"Confirmed in these fixtures: the current query returned no matching chunks for "
            f"{total_and_empty} of {total_questions} answerable development questions; the "
            f"sanitized OR query returned at least one chunk for {total_or_nonempty}. The "
            "per-question table distinguishes empty current-query results, stop words, "
            "stemming, absent exact tokens, and OR evidence overlap.",
            "",
            "The results are consistent with restrictive current-query matching as a contributor, "
            "but do not establish that AND semantics alone caused empty results. In particular, "
            "the batch-processing-service `direct-02` query contains an explicit PostgreSQL OR "
            "branch (`done | fail`) and returns 12 chunks, so a universal claim that every "
            "current query is a conjunction is not supported. The broader OR probe and protocol "
            "c1 are not proven to improve retrieval quality. Terms absent from chunk text, "
            "English dictionary behavior, query phrasing, and the small pinned corpus remain "
            "possible contributors. The OR probe is diagnostic only; run the registered protocol "
            "before adopting any variant. No held-out questions or provider APIs were used.",
            "",
        ]
    )
    return "\n".join(lines)


async def _run(output_path: Path) -> None:
    report = render_diagnostic(await collect_diagnostics())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8", newline="\n")
    print(output_path)
    for repo in collect_summary_counts(report):
        print(repo)


def collect_summary_counts(report: str) -> list[str]:
    """Extract the rendered per-repository summary lines for concise CLI output."""

    start = report.index("| Repository |")
    end = report.index("\n\n## Per-question results", start)
    return report[start:end].splitlines()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        asyncio.run(_run(args.output))
    except (OSError, ValueError, RuntimeError, SQLAlchemyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
