"""Path rules for identifying test-source files in evaluation fixtures."""

from __future__ import annotations

from pathlib import PurePosixPath

TEST_DIRECTORY_NAMES = {"test", "tests", "__tests__", "spec", "specs"}


def is_test_path(path: str) -> bool:
    """Return whether a repository-relative path follows a test-file convention."""

    normalized_path = path.replace("\\", "/")
    original_filename = normalized_path.rsplit("/", 1)[-1]
    normalized = normalized_path.casefold()
    parts = PurePosixPath(normalized).parts
    if any(part in TEST_DIRECTORY_NAMES for part in parts[:-1]):
        return True

    filename = parts[-1] if parts else ""
    java_test_class = (
        original_filename.endswith("Test.java")
        and len(original_filename) > len("Test.java")
    ) or (
        original_filename.endswith("Tests.java")
        and len(original_filename) > len("Tests.java")
    )
    return (
        (filename.startswith("test_") and filename.endswith(".py"))
        or (filename.endswith("_test.py"))
        or filename == "conftest.py"
        or ".test." in filename
        or ".spec." in filename
        or filename == "tests.py"
        or java_test_class
    )
