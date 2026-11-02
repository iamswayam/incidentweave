from __future__ import annotations

import io
from datetime import date
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
