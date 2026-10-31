from __future__ import annotations

import hashlib

from app.investigation.replay import build_chunk_records


def test_build_chunk_records_preserves_rank_and_marks_kept_results() -> None:
    results = [
        {
            "id": 12,
            "content": "first chunk",
            "file_path": "src/first.py",
            "line_start": 1,
            "line_end": 3,
            "vector_score": 0.1,
            "fts_score": 0.2,
            "rrf_score": 0.03,
        },
        {
            "id": 13,
            "content": "second chunk",
            "file_path": "src/second.py",
            "line_start": 4,
            "line_end": 6,
            "vector_score": 0.3,
            "fts_score": None,
            "rrf_score": 0.01,
        },
    ]

    records = build_chunk_records(results, ["12"])

    assert [record["rank"] for record in records] == [1, 2]
    assert [record["chunk_id"] for record in records] == ["12", "13"]
    assert records[0]["content_hash"] == hashlib.sha256(b"first chunk").hexdigest()
    assert records[0]["kept_in_prompt"] is True
    assert records[1]["kept_in_prompt"] is False
    assert records[1]["file_path"] == "src/second.py"
    assert records[1]["fts_score"] is None
