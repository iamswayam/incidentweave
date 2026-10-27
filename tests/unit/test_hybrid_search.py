import importlib

import pytest

hybrid_search_module = importlib.import_module("app.retrieval.hybrid_search")


@pytest.mark.anyio
async def test_hybrid_search_fuses_ranks_with_reciprocal_rank_math(monkeypatch) -> None:
    vector_results = [
        {"id": 10, "file_path": "vector-first.py", "line_start": 1, "line_end": 5,
         "content": "vector only", "distance": 0.1},
        {"id": 20, "file_path": "shared.py", "line_start": 6, "line_end": 10,
         "content": "shared result", "distance": 0.2},
    ]
    fts_results = [
        {"id": 20, "file_path": "shared.py", "line_start": 6, "line_end": 10,
         "content": "shared result", "score": 0.8},
        {"id": 30, "file_path": "fts-only.py", "line_start": 11, "line_end": 15,
         "content": "fts only", "score": 0.7},
    ]

    async def fake_search_vector(session, repository_id, query_embedding, limit=10):
        return vector_results[:limit]

    async def fake_search_fulltext(session, repository_id, query_text, limit=10):
        return fts_results[:limit]

    monkeypatch.setattr(hybrid_search_module, "search_vector", fake_search_vector)
    monkeypatch.setattr(hybrid_search_module, "search_fulltext", fake_search_fulltext)

    results = await hybrid_search_module.hybrid_search(
        session=None,
        repository_id=1,
        query_text="test query",
        query_embedding=[0.0] * 768,
        limit=5,
    )
    results_by_id = {result["id"]: result for result in results}

    shared_expected = 1 / (60 + 2) + 1 / (60 + 1)
    vector_only_expected = 1 / (60 + 1)
    fts_only_expected = 1 / (60 + 2)

    assert results_by_id[20]["rrf_score"] == shared_expected
    assert results_by_id[10]["rrf_score"] == vector_only_expected
    assert results_by_id[30]["rrf_score"] == fts_only_expected
    assert results_by_id[20]["rrf_score"] > results_by_id[10]["rrf_score"]
    assert results[0]["id"] == 20


@pytest.mark.anyio
async def test_hybrid_search_breaks_tied_scores_by_rank_not_chunk_id(monkeypatch) -> None:
    async def retrieve(vector_ids, fts_ids, files):
        vector_results = [
            {
                "id": chunk_id,
                "file_path": files[chunk_id][0],
                "line_start": files[chunk_id][1],
                "line_end": files[chunk_id][1] + 4,
                "content": files[chunk_id][0],
                "distance": 0.1,
            }
            for chunk_id in vector_ids
        ]
        fts_results = [
            {
                "id": chunk_id,
                "file_path": files[chunk_id][0],
                "line_start": files[chunk_id][1],
                "line_end": files[chunk_id][1] + 4,
                "content": files[chunk_id][0],
                "score": 1.0,
            }
            for chunk_id in fts_ids
        ]

        async def fake_search_vector(session, repository_id, query_embedding, limit=10):
            return vector_results[:limit]

        async def fake_search_fulltext(session, repository_id, query_text, limit=10):
            return fts_results[:limit]

        monkeypatch.setattr(hybrid_search_module, "search_vector", fake_search_vector)
        monkeypatch.setattr(hybrid_search_module, "search_fulltext", fake_search_fulltext)
        return await hybrid_search_module.hybrid_search(
            session=None,
            repository_id=1,
            query_text="test",
            query_embedding=[0.0] * 768,
            limit=5,
        )

    first_ids = await retrieve(
        [900, 100],
        [100, 900],
        {900: ("b.py", 20), 100: ("a.py", 10)},
    )
    second_ids = await retrieve(
        [7, 3],
        [3, 7],
        {7: ("b.py", 20), 3: ("a.py", 10)},
    )
    shuffled_fts = await retrieve(
        [900, 100],
        [900, 100],
        {900: ("b.py", 20), 100: ("a.py", 10)},
    )

    assert first_ids[0]["rrf_score"] == first_ids[1]["rrf_score"]
    assert [result["file_path"] for result in first_ids] == ["b.py", "a.py"]
    assert [result["file_path"] for result in second_ids] == ["b.py", "a.py"]
    assert [result["file_path"] for result in shuffled_fts] == ["b.py", "a.py"]
