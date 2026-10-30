"""Path rules for identifying test-source files in evaluation fixtures."""

from __future__ import annotations

from pathlib import PurePosixPath

TEST_DIRECTORY_NAMES = {"test", "tests", "__tests__", "spec", "specs"}


def is_test_path(path: str) -> bool:
    """Return whether a repository-relative path follows a test-file convention."""

    normalized = path.replace("\\", "/").casefold()
    parts = PurePosixPath(normalized).parts
    if any(part in TEST_DIRECTORY_NAMES for part in parts[:-1]):
        return True

    filename = parts[-1] if parts else ""
    return (
        (filename.startswith("test_") and filename.endswith(".py"))
        or (filename.endswith("_test.py"))
        or filename == "conftest.py"
        or ".test." in filename
        or ".spec." in filename
        or filename == "tests.py"
        or (filename.endswith("test.java"))
        or (filename.endswith("tests.java"))
    )
