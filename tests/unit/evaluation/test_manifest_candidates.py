from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from evaluation.manifest import select_repositories, validate_manifest

MEASURED_AT = "2026-11-02"
VALID_CANDIDATE = {
    "id": "candidate",
    "url": "https://github.com/example/candidate",
    "default_branch": "main",
    "pinned_sha": "a" * 40,
    "pinned_commit_date": MEASURED_AT,
    "license": "MIT",
    "copyright_holder": "Copyright Example",
    "role": "development",
    "source_python_lines": 5_000,
    "all_python_lines": 6_000,
    "indexed_python_lines": 5_500,
    "estimated_chunks": 100,
    "estimated_fixture_bytes": 1_000_000,
    "fixture_location": "committed",
    "qualifying_issue_count": 40,
    "qualifying_method": "git-closing-keywords",
    "measured_at": MEASURED_AT,
}


def _manifest(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "split_seed": 1,
        "repositories": [],
        "candidates": [candidate],
    }


def _errors(candidate: dict[str, Any]) -> list[str]:
    return validate_manifest(_manifest(candidate))


def test_manifest_accepts_valid_v2_candidate() -> None:
    assert _errors(deepcopy(VALID_CANDIDATE)) == []


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("url", "", "url is required"),
        ("default_branch", "", "default_branch is required"),
        ("pinned_sha", "not-a-sha", "pinned_sha must be 40 hex characters"),
        ("pinned_commit_date", "not-a-date", "pinned_commit_date must be ISO date"),
        ("license", "GPL-3.0", "license must be an allowed SPDX identifier"),
        ("license", [], "license must be an allowed SPDX identifier"),
        ("copyright_holder", "", "copyright_holder is required"),
        ("role", "test", "role must be development or held_out"),
        ("role", [], "role must be development or held_out"),
        ("source_python_lines", 4_999, "source_python_lines must be 5,000-30,000"),
        ("source_python_lines", 30_001, "source_python_lines must be 5,000-30,000"),
        ("all_python_lines", -1, "all_python_lines must be non-negative"),
        ("indexed_python_lines", -1, "indexed_python_lines must be non-negative"),
        ("estimated_chunks", -1, "estimated_chunks must be non-negative"),
        ("estimated_fixture_bytes", -1, "estimated_fixture_bytes must be non-negative"),
        ("estimated_fixture_bytes", 1_572_865, "fixture_location does not match"),
        ("fixture_location", "cache", "fixture_location is invalid"),
        ("qualifying_issue_count", 39, "qualifying_issue_count must be at least 40"),
        ("qualifying_method", "manual", "qualifying_method is invalid"),
        ("qualifying_method", [], "qualifying_method is invalid"),
        ("fixture_location", [], "fixture_location is invalid"),
        ("measured_at", "not-a-date", "measured_at must be ISO date"),
        ("pinned_commit_date", "2025-11-01", "pinned commit must be within 12 months"),
        ("pinned_commit_date", "2026-11-03", "pinned commit must be within 12 months"),
    ],
)
def test_manifest_rejects_invalid_candidate_fields(
    field: str,
    value: object,
    message: str,
) -> None:
    candidate = deepcopy(VALID_CANDIDATE)
    candidate[field] = value
    assert any(message in error for error in _errors(candidate))


def test_manifest_rejects_duplicate_candidate_ids() -> None:
    manifest = _manifest(deepcopy(VALID_CANDIDATE))
    duplicate = deepcopy(VALID_CANDIDATE)
    duplicate["role"] = "held_out"
    manifest["candidates"].append(duplicate)

    assert "candidate ids must be unique" in validate_manifest(manifest)


def test_manifest_rejects_candidate_id_also_used_by_repository() -> None:
    manifest = _manifest(deepcopy(VALID_CANDIDATE))
    manifest["repositories"] = [{"id": "candidate"}]

    assert "repository and candidate ids must be unique" in validate_manifest(manifest)


def test_v1_manifest_without_candidate_fields_remains_valid() -> None:
    assert validate_manifest(
        {
            "schema_version": 1,
            "split_seed": 1,
            "repositories": [],
        }
    ) == []


def test_repository_selection_ignores_candidates() -> None:
    repositories = [{"id": "v1"}]
    manifest = {
        "repositories": repositories,
        "candidates": [{"id": "not-yet-evaluation-data"}],
    }

    assert select_repositories(manifest, None) == repositories
