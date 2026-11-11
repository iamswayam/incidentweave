"""Repository-relative Python source path rules used by evaluation tooling."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

SOURCE_EXCLUDED_DIRS = {
    "tests",
    "test",
    "testing",
    "docs",
    "doc",
    "examples",
    "example",
}
SOURCE_EXCLUDED_FILES = {"conftest.py"}


def is_source_python_path(path: str | Path) -> bool:
    """Apply protocol 15's source-line exclusions to one repository-relative path."""

    relative = Path(path)
    if relative.suffix.casefold() != ".py":
        return False
    parts = tuple(part.casefold() for part in relative.parts)
    filename = parts[-1]
    return not (
        SOURCE_EXCLUDED_DIRS.intersection(parts[:-1])
        or filename in SOURCE_EXCLUDED_FILES
        or filename.startswith("test_")
        or filename.endswith("_test.py")
    )


def is_test_path(path: str) -> bool:
    """Return whether a repository-relative path identifies test content."""

    relative = PurePosixPath(path)
    parts = tuple(part.casefold() for part in relative.parts)
    filename = parts[-1] if parts else ""
    return (
        bool({"test", "tests", "testing"}.intersection(parts[:-1]))
        or filename == "conftest.py"
        or filename.startswith("test_")
        or filename.endswith("_test.py")
    )
