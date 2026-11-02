from __future__ import annotations

import io
import json
import subprocess
from datetime import date
from pathlib import Path
from zipfile import ZipFile

import pytest

import evaluation.candidates as candidates
from evaluation.candidates import (
    MAX_FIXTURE_BYTES,
    bsd_clause_count,
    closing_issue_numbers,
    copyright_holder_line,
    estimate_fixture_bytes,
    fixture_location,
    is_source_python_path,
    is_within_twelve_months,
    qualifying_issues_from_git_log,
    spdx_from_license_text,
)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("src/app.py", True),
        ("tests/app.py", False),
        ("src/test/app.py", False),
        ("testing/helper.py", False),
        ("doc/api.py", False),
        ("examples/demo.py", False),
        ("src/test_parser.py", False),
        ("src/parser_test.py", False),
        ("src/conftest.py", False),
        ("src/contest.py", True),
        ("src/app.pyx", False),
    ],
)
def test_source_python_path_exclusions(path: str, expected: bool) -> None:
    assert is_source_python_path(path) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Permission is hereby granted, free of charge, to any person obtaining a copy.",
            "MIT",
        ),
        (
            "Apache License\nVersion 2.0, January 2004",
            "Apache-2.0",
        ),
        (
            "Redistribution and use in source and binary forms, with or without "
            "modification, are permitted provided that the following conditions are met.",
            "BSD-2-Clause",
        ),
        (
            "Redistribution and use in source and binary forms are permitted provided "
            "that the following conditions are met. Neither the name of the project "
            "may be used to endorse or promote products derived from this software.",
            "BSD-3-Clause",
        ),
        ("All rights reserved.", None),
    ],
)
def test_spdx_license_matcher(text: str, expected: str | None) -> None:
    assert spdx_from_license_text(text) == expected


def test_bsd_clause_count_reads_numbered_conditions() -> None:
    assert bsd_clause_count("1. First condition\n2. Second condition\n3. Third condition") == 3
    assert bsd_clause_count("1. First condition\n2. Second condition") == 2
    assert bsd_clause_count("License terms without numbered clauses") is None


def test_bsd_clause_count_reads_bulleted_conditions() -> None:
    text = (
        "Redistribution and use are permitted provided that the following conditions "
        "are met:\n"
        "* First condition.\n"
        "* Second condition.\n"
        "* Third condition.\n"
        "\n"
        "THIS SOFTWARE IS PROVIDED AS IS."
    )
    assert bsd_clause_count(text) == 3


def test_copyright_holder_skips_generic_legal_definitions() -> None:
    text = (
        "Copyright notice that is included in or attached to the work.\n"
        "Copyright (c) 2017 Example Foundation."
    )
    assert copyright_holder_line(text) == "Copyright (c) 2017 Example Foundation."
    assert copyright_holder_line(
        "Copyright notice that is included in or attached to the work."
    ) is None


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Fixes #12", {12}),
        ("closes #12 and resolves #34", {12, 34}),
        ("prefix #12", set()),
        ("fixture #3", set()),
        ("fixed #8\n\nClose #8", {8}),
    ],
)
def test_closing_keyword_issue_parser(message: str, expected: set[int]) -> None:
    assert closing_issue_numbers(message) == expected


def test_git_history_issue_count_requires_source_python_changes() -> None:
    log_output = (
        "\x1e"
        + "a" * 40
        + "\x00Fixes #12\n\x00src/service.py\n"
        + "\x1e"
        + "b" * 40
        + "\x00Closes #13\n\x00tests/test_service.py\n"
        + "\x1e"
        + "c" * 40
        + "\x00Fixes #14\n\x00README.md\n"
    )

    assert qualifying_issues_from_git_log(log_output) == {12}


def test_fixture_size_uses_median_and_adds_twenty_percent() -> None:
    assert estimate_fixture_bytes(100, [100.0, 200.0, 900.0]) == 24_000


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (MAX_FIXTURE_BYTES, "committed"),
        (MAX_FIXTURE_BYTES + 1, "release"),
    ],
)
def test_fixture_location_boundary(size: int, expected: str) -> None:
    assert fixture_location(size) == expected


def test_commit_recency_uses_twelve_calendar_months() -> None:
    assert is_within_twelve_months(date(2025, 11, 2), date(2026, 11, 2))
    assert not is_within_twelve_months(date(2025, 11, 1), date(2026, 11, 2))
    assert not is_within_twelve_months(date(2026, 11, 3), date(2026, 11, 2))


def test_python_tree_reads_only_pinned_archive_members(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_buffer = io.BytesIO()
    with ZipFile(archive_buffer, "w") as archive:
        archive.writestr("project-sha/pkg/module.py", "value = 1\n")
    archive_bytes = archive_buffer.getvalue()
    requests: list[str] = []

    def fake_urlopen(url: str, *, timeout: int) -> io.BytesIO:
        requests.append(url)
        assert timeout == 1200
        return io.BytesIO(archive_bytes)

    monkeypatch.setattr(candidates, "_python_tree", lambda *_: [("blob", "pkg/module.py")])
    monkeypatch.setattr(candidates, "urlopen", fake_urlopen)

    result = candidates._read_python_tree(
        tmp_path / "repo",
        "owner/project",
        "a" * 40,
        tmp_path / "snapshot",
    )

    assert requests == [
        f"https://codeload.github.com/owner/project/zip/{'a' * 40}"
    ]
    assert result == [("blob", "pkg/module.py")]
    assert (tmp_path / "snapshot" / "pkg" / "module.py").read_text() == "value = 1\n"


def test_github_issue_count_filters_merged_date_and_source_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    pull_requests = [
        {
            "mergedAt": "2026-10-30T12:00:00Z",
            "files": [{"path": "src/app.py"}],
            "closingIssuesReferences": [{"number": 12}, {"number": 15}],
        },
        {
            "mergedAt": "2026-11-02T12:00:00Z",
            "files": [{"path": "src/new.py"}],
            "closingIssuesReferences": [{"number": 20}],
        },
        {
            "mergedAt": "2026-10-20T12:00:00Z",
            "files": [{"path": "docs/readme.py"}],
            "closingIssuesReferences": [{"number": 25}],
        },
        {
            "mergedAt": "2026-10-20T12:00:00Z",
            "files": [{"path": "tests/test_app.py"}],
            "closingIssuesReferences": [{"number": 30}],
        },
    ]

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[1:3] == ["auth", "status"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(
            command, 0, json.dumps(pull_requests), ""
        )

    monkeypatch.setattr(candidates.shutil, "which", lambda _name: "gh")
    monkeypatch.setattr(candidates.subprocess, "run", fake_run)

    assert candidates._gh_qualifying_issue_numbers(
        "owner/repo", date(2026, 11, 1)
    ) == {12, 15}
    pr_command = calls[1]
    assert pr_command[pr_command.index("--limit") + 1] == "1000"
    assert "closingIssuesReferences,files,mergedAt" in pr_command


def test_github_issue_query_retries_once_without_proxy_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[1:3] == ["auth", "status"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if len([item for item in calls if item[1:3] == ["pr", "list"]]) == 1:
            return subprocess.CompletedProcess(command, 1, "", "rate limit")
        return subprocess.CompletedProcess(command, 0, "[]", "")

    monkeypatch.setattr(candidates.shutil, "which", lambda _name: "gh")
    monkeypatch.setattr(candidates.subprocess, "run", fake_run)

    assert candidates._gh_qualifying_issue_numbers("owner/repo", date(2026, 11, 1)) == set()
    assert len([item for item in calls if item[1:3] == ["pr", "list"]]) == 2


def test_github_auth_status_retries_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[1:3] == ["auth", "status"] and len(calls) == 1:
            return subprocess.CompletedProcess(command, 1, "", "temporary auth error")
        if command[1:3] == ["auth", "status"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 0, "[]", "")

    monkeypatch.setattr(candidates.shutil, "which", lambda _name: "gh")
    monkeypatch.setattr(candidates.subprocess, "run", fake_run)

    assert candidates._gh_qualifying_issue_numbers("owner/repo", date(2026, 11, 1)) == set()
    assert len([item for item in calls if item[1:3] == ["auth", "status"]]) == 2


def test_github_issue_query_surfaces_failure_after_one_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[1:3] == ["auth", "status"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 1, "", "API error")

    monkeypatch.setattr(candidates.shutil, "which", lambda _name: "gh")
    monkeypatch.setattr(candidates.subprocess, "run", fake_run)

    with pytest.raises(candidates.CandidateQualificationError, match="after one retry"):
        candidates._gh_qualifying_issue_numbers("owner/repo", date(2026, 11, 1))
    assert len([item for item in calls if item[1:3] == ["pr", "list"]]) == 2


def test_qualification_skips_unqualified_backups(monkeypatch: pytest.MonkeyPatch) -> None:
    issue_counts = {
        "rq": 109,
        "kopf": 59,
        "apscheduler": 17,
        "client_python": 45,
        "locust": 119,
        "docker_py": 82,
        "uvicorn": 116,
        "huey": 4,
        "luigi": 43,
    }

    def fake_qualify(
        repository_name: str,
        repository_url: str,
        role: str,
        **_kwargs,
    ) -> dict[str, object]:
        return {
            "id": repository_name,
            "url": f"https://github.com/{repository_url}",
            "default_branch": "main",
            "pinned_sha": "a" * 40,
            "pinned_commit_date": "2026-11-01",
            "license": "MIT",
            "copyright_holder": "Copyright 2026 Example",
            "role": role,
            "source_python_lines": 8_000,
            "all_python_lines": 10_000,
            "indexed_python_lines": 10_000,
            "estimated_chunks": 100,
            "estimated_fixture_bytes": 100_000,
            "fixture_location": "committed",
            "qualifying_issue_count": issue_counts[repository_name],
            "qualifying_method": "gh",
            "measured_at": "2026-11-02",
            "license_path": "LICENSE",
            "bsd_clause_count": None,
        }

    monkeypatch.setattr(candidates, "fixture_bytes_per_chunk", lambda _path: [1.0])
    monkeypatch.setattr(candidates, "qualify_repository", fake_qualify)

    report = candidates.run_qualification(
        cache_root=Path("cache"),
        manifest_path=Path("manifest.json"),
        measured_at=date(2026, 11, 2),
    )

    assert [candidate["id"] for candidate in report["candidates"]] == [
        "rq",
        "kopf",
        "luigi",
        "client_python",
        "locust",
        "docker_py",
        "uvicorn",
    ]
    assert report["swaps"] == [
        {
            "replaced": "apscheduler",
            "replacement": "luigi",
            "role": "development",
            "reason": "only 17 qualifying issues; at least 40 required",
        }
    ]
    assert report["qualified_backups"] == []
