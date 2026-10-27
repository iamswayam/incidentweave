"""Full-text search over repository chunks."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.fulltext_variants import SEARCHABLE_TEXT_VERSION


async def search_fulltext(
    session: AsyncSession,
    repository_id: int,
    query_text: str,
    limit: int = 10,
    *,
    query_text_override: str | None = None,
    searchable_text_version: str | None = None,
) -> list[dict[str, object]]:
    """Return top-N chunks matching a text query using PostgreSQL FTS."""

    if limit <= 0:
        return []

    if searchable_text_version not in {None, SEARCHABLE_TEXT_VERSION}:
        raise ValueError(
            f"Unsupported searchable-text version: {searchable_text_version}"
        )
    bound_query_text = (
        query_text if query_text_override is None else query_text_override
    )
    if searchable_text_version == SEARCHABLE_TEXT_VERSION:
        query = text(
            """
            WITH searchable_chunks AS (
                SELECT
                    c.*,
                    c.content || E'\\n' || COALESCE(identifiers.split_text, '')
                        AS searchable_text
                FROM chunks AS c
                LEFT JOIN LATERAL (
                    SELECT string_agg(
                        regexp_replace(
                            regexp_replace(
                                regexp_replace(
                                    matches.token_parts[1],
                                    '([A-Z]+)([A-Z][a-z])',
                                    '\\1 \\2',
                                    'g'
                                ),
                                '([a-z0-9])([A-Z])',
                                '\\1 \\2',
                                'g'
                            ),
                            '_+',
                            ' ',
                            'g'
                        ),
                        ' ' ORDER BY matches.position
                    ) AS split_text
                    FROM regexp_matches(
                        c.content,
                        '[A-Za-z0-9_]+',
                        'g'
                    ) WITH ORDINALITY AS matches(token_parts, position)
                    WHERE matches.token_parts[1] ~ '_'
                       OR matches.token_parts[1] ~ '[a-z0-9][A-Z]'
                       OR matches.token_parts[1] ~ '[A-Z]{2}[a-z]'
                ) AS identifiers ON true
                WHERE c.repository_id = :repository_id
            )
            SELECT
                c.id,
                c.repository_id,
                c.file_path,
                c.line_start,
                c.line_end,
                c.content,
                ts_rank_cd(
                    to_tsvector('english', c.searchable_text),
                    websearch_to_tsquery(:query_text)
                ) AS score
            FROM searchable_chunks AS c
            WHERE to_tsvector('english', c.searchable_text)
                  @@ websearch_to_tsquery(:query_text)
            ORDER BY score DESC, c.file_path, c.line_start, c.line_end
            LIMIT :limit
            """
        )
    else:
        query = text(
            """
            SELECT
                c.id,
                c.repository_id,
                c.file_path,
                c.line_start,
                c.line_end,
                c.content,
                ts_rank_cd(
                    to_tsvector('english', c.content),
                    websearch_to_tsquery(:query_text)
                ) AS score
            FROM chunks AS c
            WHERE c.repository_id = :repository_id
              AND to_tsvector('english', c.content) @@ websearch_to_tsquery(:query_text)
            ORDER BY score DESC, c.file_path, c.line_start, c.line_end
            LIMIT :limit
            """
        )

    rows = (
        await session.execute(
            query,
            {
                "query_text": bound_query_text,
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
        }
        for row in rows
    ]
