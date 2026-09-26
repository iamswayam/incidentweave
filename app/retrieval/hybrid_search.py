"""Hybrid vector + full-text retrieval using reciprocal rank fusion."""

from __future__ import annotations

from app.retrieval.fulltext_search import search_fulltext
from app.retrieval.vector_search import search_vector


async def hybrid_search(
    session,
    repository_id: int,
    query_text: str,
    query_embedding: list[float],
    limit: int = 10,
) -> list[dict[str, object]]:
    """Fuse vector and FTS results using reciprocal rank fusion (RRF)."""

    if limit <= 0:
        return []

    vector_results = await search_vector(session, repository_id, query_embedding, limit=limit)
    fts_results = await search_fulltext(session, repository_id, query_text, limit=limit)

    vector_rank_by_id = {result["id"]: index + 1 for index, result in enumerate(vector_results)}
    fts_rank_by_id = {result["id"]: index + 1 for index, result in enumerate(fts_results)}

    vector_result_by_id = {result["id"]: result for result in vector_results}
    fts_result_by_id = {result["id"]: result for result in fts_results}

    candidate_ids = set(vector_rank_by_id) | set(fts_rank_by_id)
    fused: list[dict[str, object]] = []

    for chunk_id in candidate_ids:
        vector_rank = vector_rank_by_id.get(chunk_id)
        fts_rank = fts_rank_by_id.get(chunk_id)

        rrf_score = 0.0
        if vector_rank is not None:
            rrf_score += 1 / (60 + vector_rank)
        if fts_rank is not None:
            rrf_score += 1 / (60 + fts_rank)

        fused.append(
            {
                "id": chunk_id,
                "repository_id": repository_id,
                "file_path": (
                    vector_result_by_id.get(chunk_id, {}).get("file_path")
                    or fts_result_by_id.get(chunk_id, {}).get("file_path")
                ),
                "line_start": (
                    vector_result_by_id.get(chunk_id, {}).get("line_start")
                    or fts_result_by_id.get(chunk_id, {}).get("line_start")
                ),
                "line_end": (
                    vector_result_by_id.get(chunk_id, {}).get("line_end")
                    or fts_result_by_id.get(chunk_id, {}).get("line_end")
                ),
                "content": (
                    vector_result_by_id.get(chunk_id, {}).get("content")
                    or fts_result_by_id.get(chunk_id, {}).get("content")
                ),
                "vector_score": vector_result_by_id.get(chunk_id, {}).get("distance"),
                "fts_score": fts_result_by_id.get(chunk_id, {}).get("score"),
                "rrf_score": rrf_score,
            }
        )

    fused.sort(key=lambda item: item["rrf_score"], reverse=True)
    return fused[:limit]
