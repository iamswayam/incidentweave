"""Pinned evaluation corpus setup, restricted to incidentweave-eval."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

EVAL_REPOSITORY_NAME = "incidentweave-eval"


def commit_exists(root: Path, sha: str) -> bool:
    """Return True when the commit exists in this clone."""

    try:
        subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=root,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def export_snapshot(root: Path, sha: str, destination: Path) -> Path:
    """Export a pinned commit and remove test fixtures from the snapshot."""

    if not commit_exists(root, sha):
        raise RuntimeError(
            f"The pinned commit {sha} is not in this clone and full history must be fetched."
        )

    destination.mkdir(parents=True, exist_ok=True)
    archive = destination.with_suffix(".tar")
    subprocess.run(
        ["git", "archive", "--format=tar", sha, "-o", str(archive)],
        cwd=root,
        check=True,
    )
    extract_root = destination / "source"
    extract_root.mkdir()
    subprocess.run(["tar", "-xf", str(archive), "-C", str(extract_root)], check=True)
    fixture_root = extract_root / "tests" / "fixtures"
    if fixture_root.exists():
        shutil.rmtree(fixture_root)
    archive.unlink(missing_ok=True)
    return extract_root
