from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source_files() -> list[Path]:
    files = list((ROOT / "app").rglob("*.py"))
    files.extend(
        path
        for path in (ROOT / "evaluation").rglob("*.py")
        if not {"cache", "_snapshot"}.intersection(
            path.relative_to(ROOT / "evaluation").parts
        )
    )
    return files


def _scripts_imports(source: str) -> list[int]:
    tree = ast.parse(source)
    imports: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "scripts" or alias.name.startswith("scripts.")
                for alias in node.names
            ):
                imports.append(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "scripts" or module.startswith("scripts."):
                imports.append(node.lineno)
    return imports


def test_app_and_evaluation_do_not_import_scripts() -> None:
    source_files = _source_files()
    assert source_files, "expected the app/evaluation scan to find Python files"

    violations = [
        f"{path.relative_to(ROOT)}:{line}"
        for path in source_files
        for line in _scripts_imports(path.read_text(encoding="utf-8"))
    ]

    assert not violations, (
        "app/ and evaluation/ must not import scripts/: " + ", ".join(violations)
    )
