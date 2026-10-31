"""Retrieval used only when query embedding is unavailable."""

from __future__ import annotations

from sqlalchemy import text

from app.retrieval.fulltext_variants import build_c1_query, extract_query_tokens

_STOP_WORDS_SQL = text("SELECT lexemes FROM ts_debug('english', :term)")


async def search_degraded_lexical_only(
    session,
    repository_id: int,
    query_text: str,
    limit: int,
) -> list[dict[str, object]]:
    """Run the registered sanitized-OR lexical query without vector retrieval."""

    stop_words: set[str] = set()
    for token in extract_query_tokens(query_text):
        lexemes = (
            await session.execute(_STOP_WORDS_SQL, {"term": token})
        ).scalars().all()
        if not any(lexemes):
            stop_words.add(token)
    built_query = build_c1_query(query_text, stop_words)
    if limit <= 0 or not built_query.query_text:
        return []

    rows = (
        await session.execute(
            text(
                """
                SELECT
                    c.id,
                    c.repository_id,
                    c.file_path,
                    c.line_start,
                    c.line_end,
                    c.content,
                    c.content_hash,
                    ts_rank_cd(
                        to_tsvector('english', c.content),
                        websearch_to_tsquery(:query_text)
                    ) AS score
                FROM chunks AS c
                WHERE c.repository_id = :repository_id
                  AND to_tsvector('english', c.content)
                      @@ websearch_to_tsquery(:query_text)
                ORDER BY
                    score DESC,
                    c.file_path,
                    c.line_start,
                    c.line_end,
                    c.content_hash
                LIMIT :limit
                """
            ),
            {
                "query_text": built_query.query_text,
                "repository_id": repository_id,
                "limit": limit,
            },
        )
    ).mappings().all()
    return [
        {
            "id": row["id"],
            "repository_id": row["repository_id"],
            "file_path": row["file_path"],
            "line_start": row["line_start"],
            "line_end": row["line_end"],
            "content": row["content"],
            "score": float(row["score"]),
            "fts_score": float(row["score"]),
            "rrf_score": None,
            "vector_score": None,
        }
        for row in rows
    ]
