from pathlib import Path

from scripts.export_openapi import generate_openapi_json


def test_committed_openapi_matches_current_application_schema() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    committed_schema = (
        repository_root / "docs" / "reference" / "openapi.json"
    ).read_text(encoding="utf-8")

    assert committed_schema == generate_openapi_json()
