from __future__ import annotations

import pytest

from evaluation.test_files import is_test_path


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_provider.py",
        "src/test/java/example/WidgetTest.java",
        "app/__tests__/widget.tsx",
        "api/specs/user.yaml",
        "pkg/spec/parser.test.ts",
        "pkg/spec/parser.spec.ts",
        "tests/conftest.py",
        "test_cli.py",
        "parser_test.py",
        "apps/accounts/tests.py",
        r"src\test\java\example\WidgetTests.java",
        "src/main/UserTest.java",
        "src/main/UserServiceTests.java",
        "src/test/java/Foo.java",
    ],
)
def test_is_test_path_recognizes_test_conventions(path: str) -> None:
    assert is_test_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "latest_report.py",
        "contest.py",
        "src/testament/readme.md",
        "src/testing/readme.md",
        "src/mytests/readme.md",
        "src/widget.testimony.ts",
        "src/widget.specification.ts",
        "src/Widget.java",
        "src/main/Latest.java",
        "src/main/Contest.java",
        "src/main/Attest.java",
    ],
)
def test_is_test_path_does_not_match_substrings(path: str) -> None:
    assert not is_test_path(path)
