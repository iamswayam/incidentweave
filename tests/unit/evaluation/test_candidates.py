from __future__ import annotations

from datetime import date

import pytest

from evaluation.candidates import (
    MAX_FIXTURE_BYTES,
    closing_issue_numbers,
    estimate_fixture_bytes,
    fixture_location,
    is_within_twelve_months,
    is_source_python_path,
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
