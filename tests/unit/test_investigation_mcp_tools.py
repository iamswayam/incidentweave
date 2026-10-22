from __future__ import annotations

from pathlib import Path

from app.investigation.mcp_server import grep_search


def test_grep_search_finds_literal_case_insensitively_and_uses_ingest_exclusions(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "fixture.py").write_text(
        "# marker: QuasarLatchOmega\n", encoding="utf-8"
    )
    ignored_dir = tmp_path / ".venv"
    ignored_dir.mkdir()
    (ignored_dir / "ignored.py").write_text(
        "# marker: quasarLatchOmega\n", encoding="utf-8"
    )

    matches = grep_search(tmp_path, "quasarlatchomega", repository_id=4, limit=10)

    assert len(matches) == 1
    assert matches[0]["file_path"] == "src/fixture.py"
    assert matches[0]["line_start"] == matches[0]["line_end"] == 1
    assert matches[0]["content"] == "# marker: QuasarLatchOmega"
    assert matches[0]["vector_score"] is None
    assert matches[0]["fts_score"] is None
    assert matches[0]["rrf_score"] is None
