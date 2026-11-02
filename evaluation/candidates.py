"""Qualify pinned repository candidates without embedding or building fixtures."""

from __future__ import annotations

import calendar
import io
import json
import math
import re
import shutil
import subprocess
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.request import urlopen
from zipfile import ZipFile

from evaluation.chunk_strategies import candidate_chunk_specs
from scripts.ingest_repo import iter_python_files

MAX_FIXTURE_BYTES = 1_572_864
LICENSE_IDS = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0"}
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
SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".m",
    ".mm",
    ".php",
    ".pl",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sh",
    ".swift",
    ".ts",
    ".tsx",
}
CLOSING_ISSUE = re.compile(
    r"\b(?:fix|fixes|fixed|close|closes|closed|resolve|resolves|resolved)\s+#(\d+)\b",
    re.IGNORECASE,
)

INITIAL_CANDIDATES = (
    ("rq", "rq/rq", "development"),
    ("kopf", "nolar/kopf", "development"),
    ("apscheduler", "agronholm/apscheduler", "development"),
    ("client_python", "prometheus/client_python", "development"),
    ("locust", "locustio/locust", "held_out"),
    ("docker_py", "docker/docker-py", "held_out"),
    ("uvicorn", "encode/uvicorn", "held_out"),
)
BACKUP_REPOSITORIES = (
    ("structlog", "hynek/structlog"),
    ("huey", "coleifer/huey"),
    ("flower", "mher/flower"),
    ("luigi", "spotify/luigi"),
)


class CandidateQualificationError(RuntimeError):
    """A candidate cannot be qualified against the registered criteria."""


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


def spdx_from_license_text(text: str) -> str | None:
    """Recognize the candidate license identifiers allowed by protocol 15."""

    normalized = text.casefold()
    if "apache license" in normalized and "version 2.0" in normalized:
        return "Apache-2.0"
    if "permission is hereby granted, free of charge" in normalized:
        return "MIT"
    if (
        "redistribution and use in source and binary forms" in normalized
        and "are permitted provided that" in normalized
    ):
        if (
            "neither the name of" in normalized
            or "may be used to endorse or promote" in normalized
        ):
            return "BSD-3-Clause"
        return "BSD-2-Clause"
    return None


def copyright_holder_line(text: str) -> str | None:
    """Return the first copyright attribution line without altering its wording."""

    attribution = re.compile(
        r"^(?:copyright(?:\s*\(c\))?\s+|©\s*|\(c\)\s*)"
        r"(?:©\s*)?\d{4}(?:-\d{4}|-present)?\b",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        stripped = line.strip()
        if attribution.match(stripped):
            return stripped
    return None


def bsd_clause_count(text: str) -> int | None:
    """Count numbered or bulleted conditions in a BSD license text."""

    clauses = re.findall(r"(?m)^\s*(\d+)\.\s+", text)
    numbers = {int(number) for number in clauses if 1 <= int(number) <= 3}
    if numbers:
        return len(numbers)
    conditions = re.search(
        r"following conditions are met\s*:?(.*?)(?:\n\s*\n|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if conditions is None:
        return None
    bullets = re.findall(r"(?m)^\s*[*-]\s+\S", conditions.group(1))
    return len(bullets) if bullets else None


def closing_issue_numbers(commit_message: str) -> set[int]:
    """Extract issue numbers explicitly named by GitHub closing keywords."""

    return {int(number) for number in CLOSING_ISSUE.findall(commit_message)}


def qualifying_issues_from_git_log(log_output: str) -> set[int]:
    """Count distinct closing-keyword issues from commits changing source Python."""

    issues: set[int] = set()
    for record in log_output.split("\x1e"):
        record = record.strip("\r\n")
        if not record:
            continue
        _commit, separator, after_commit = record.partition("\x00")
        if not separator:
            continue
        message, separator, changed_files = after_commit.partition("\x00")
        if separator and any(
            is_source_python_path(path) for path in changed_files.splitlines()
        ):
            issues.update(closing_issue_numbers(message))
    return issues


def estimate_fixture_bytes(chunk_count: int, gzip_bytes_per_chunk: Iterable[float]) -> int:
    """Estimate compressed chunks plus 20% for question vectors, rounded up."""

    if chunk_count < 0:
        raise ValueError("chunk_count must be non-negative")
    rates = list(gzip_bytes_per_chunk)
    if not rates or any(not math.isfinite(rate) or rate < 0 for rate in rates):
        raise ValueError("gzip_bytes_per_chunk must contain finite non-negative values")
    from statistics import median

    return math.ceil(chunk_count * median(rates) * 1.2)


def fixture_location(estimated_bytes: int) -> str:
    """Choose committed storage at or below the protocol's 1.5 MiB cap."""

    if estimated_bytes < 0:
        raise ValueError("estimated_bytes must be non-negative")
    return "committed" if estimated_bytes <= MAX_FIXTURE_BYTES else "release"


def is_within_twelve_months(commit_date: date, measured_at: date) -> bool:
    """Return whether a commit is no older than twelve calendar months."""

    month_days = calendar.monthrange(measured_at.year - 1, measured_at.month)[1]
    cutoff = date(
        measured_at.year - 1,
        measured_at.month,
        min(measured_at.day, month_days),
    )
    return cutoff <= commit_date <= measured_at


def fixture_bytes_per_chunk(manifest_path: Path) -> list[float]:
    """Measure the three committed v1 fixtures through the registered loader."""

    from evaluation.build_fixture import load_fixture
    from evaluation.manifest import manifest_root

    root = manifest_root(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    repositories = manifest.get("repositories")
    if not isinstance(repositories, list):
        raise CandidateQualificationError("manifest repositories must be a list")
    rates: list[float] = []
    for entry in repositories:
        fixture_path = root / entry["fixture"]["path"]
        fixture = load_fixture(fixture_path)
        chunks = fixture.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            raise CandidateQualificationError(
                f"{entry['id']}: cannot estimate fixture size without chunks"
            )
        rates.append(fixture_path.stat().st_size / len(chunks))
    if len(rates) != 3:
        raise CandidateQualificationError(
            f"expected three v1 fixtures for sizing; found {len(rates)}"
        )
    return rates


def _run_git(repository: Path, *arguments: str, input_text: str | None = None) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        timeout=3600,
    )
    return completed.stdout


def _clone_repository(
    repository_name: str,
    repository_url: str,
    cache_root: Path,
    run_id: str,
) -> Path:
    existing_clones = sorted(
        cache_root.glob(f"{repository_name}-*/repo"),
        key=lambda path: path.parent.name,
        reverse=True,
    )
    for existing in existing_clones:
        if not (existing / ".git").exists():
            continue
        try:
            is_shallow = _run_git(
                existing, "rev-parse", "--is-shallow-repository"
            ).strip()
            branch_ref = _run_git(
                existing, "symbolic-ref", "refs/remotes/origin/HEAD"
            ).strip()
            _run_git(existing, "rev-parse", branch_ref)
        except (OSError, subprocess.SubprocessError):
            continue
        if is_shallow == "false":
            return existing

    repository = cache_root / f"{repository_name}-{run_id}" / "repo"
    repository.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--single-branch",
            "--no-tags",
            "--no-checkout",
            f"https://github.com/{repository_url}.git",
            str(repository),
        ],
        check=True,
        timeout=7200,
    )
    if _run_git(repository, "rev-parse", "--is-shallow-repository").strip() != "false":
        raise CandidateQualificationError("candidate clone is not full-history")
    return repository


def _default_branch(repository: Path) -> str:
    symbolic_ref = _run_git(repository, "symbolic-ref", "refs/remotes/origin/HEAD").strip()
    prefix = "refs/remotes/origin/"
    if not symbolic_ref.startswith(prefix):
        raise CandidateQualificationError(
            f"unexpected origin/HEAD reference {symbolic_ref!r}"
        )
    return symbolic_ref.removeprefix(prefix)


def _python_tree(repository: Path, pinned_sha: str) -> list[tuple[str, str]]:
    raw_tree = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--full-tree", pinned_sha],
        cwd=repository,
        capture_output=True,
        check=True,
        timeout=1800,
    ).stdout
    entries: list[tuple[str, str]] = []
    for raw_entry in raw_tree.split(b"\0"):
        if not raw_entry:
            continue
        metadata, raw_path = raw_entry.split(b"\t", maxsplit=1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if object_type == "blob" and mode != "120000" and path.casefold().endswith(".py"):
            entries.append((object_id, path))
    return entries


def _read_python_tree(
    repository: Path,
    repository_url: str,
    pinned_sha: str,
    snapshot_root: Path,
) -> list[tuple[str, str]]:
    entries = _python_tree(repository, pinned_sha)
    archive_url = f"https://codeload.github.com/{repository_url}/zip/{pinned_sha}"
    with urlopen(archive_url, timeout=1200) as response:
        archive_bytes = response.read()
    snapshot_root.mkdir(parents=True, exist_ok=True)
    with ZipFile(io.BytesIO(archive_bytes)) as archive:
        archive_root = archive.namelist()[0].split("/", maxsplit=1)[0]
        archive_names = set(archive.namelist())
        for _, relative_path in entries:
            member = f"{archive_root}/{relative_path}"
            if member not in archive_names:
                raise CandidateQualificationError(
                    f"pinned source archive is missing Python file {relative_path!r}"
                )
            destination = snapshot_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            resolved_destination = destination.resolve()
            if not resolved_destination.is_relative_to(snapshot_root.resolve()):
                raise CandidateQualificationError(
                    f"unsafe Python file path in candidate tree: {relative_path!r}"
                )
            destination.write_bytes(archive.read(member))
    return entries


def _license_blob(repository: Path, pinned_sha: str) -> tuple[str | None, str | None]:
    names = _run_git(
        repository, "ls-tree", "--name-only", pinned_sha
    ).splitlines()
    license_path = next(
        (
            name
            for name in names
            if Path(name).name.casefold() in {"license", "license.txt", "license.md"}
        ),
        None,
    )
    if license_path is None:
        return None, None
    content = subprocess.run(
        ["git", "show", f"{pinned_sha}:{license_path}"],
        cwd=repository,
        capture_output=True,
        check=True,
        timeout=1800,
    ).stdout.decode("utf-8", errors="replace")
    return content, license_path


def _qualifying_issue_numbers(repository: Path, pinned_sha: str) -> set[int]:
    output = _run_git(
        repository,
        "log",
        "--diff-merges=first-parent",
        "--format=%x1e%H%x00%B%x00",
        "--name-only",
        "--no-renames",
        pinned_sha,
        "--",
        ":(glob)**/*.py",
    )
    return qualifying_issues_from_git_log(output)


def _gh_qualifying_issue_numbers(
    repository_url: str,
    pinned_commit_date: date,
) -> set[int] | None:
    gh = shutil.which("gh")
    if gh is None:
        return None
    auth = subprocess.run(
        [gh, "auth", "status"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if auth.returncode != 0:
        return None
    completed = subprocess.run(
        [
            gh,
            "pr",
            "list",
            "--repo",
            repository_url,
            "--state",
            "merged",
            "--limit",
            "1000",
            "--json",
            "closingIssuesReferences,files,mergedAt",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    if completed.returncode != 0:
        return None
    pull_requests = json.loads(completed.stdout)
    issue_numbers: set[int] = set()
    for pull_request in pull_requests:
        merged_at = pull_request.get("mergedAt")
        if (
            not isinstance(merged_at, str)
            or date.fromisoformat(merged_at[:10]) > pinned_commit_date
        ):
            continue
        files = pull_request.get("files", [])
        if not any(
            is_source_python_path(item.get("path", ""))
            for item in files
            if isinstance(item, dict)
        ):
            continue
        issue_numbers.update(
            int(issue["number"])
            for issue in pull_request.get("closingIssuesReferences", [])
            if isinstance(issue, dict) and isinstance(issue.get("number"), int)
        )
    return issue_numbers


def _candidate_failures(candidate: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not 5_000 <= candidate["source_python_lines"] <= 30_000:
        failures.append("source Python lines outside 5,000-30,000")
    if candidate["license"] not in LICENSE_IDS:
        failures.append(f"unrecognized or unsupported license {candidate['license']!r}")
    if candidate["qualifying_issue_count"] < 40:
        failures.append(
            f"only {candidate['qualifying_issue_count']} qualifying issues; at least 40 required"
        )
    commit_date = date.fromisoformat(candidate["pinned_commit_date"])
    measured_at = date.fromisoformat(candidate["measured_at"])
    if not is_within_twelve_months(commit_date, measured_at):
        failures.append("default-branch commit is older than twelve months")
    return failures


def qualify_repository(
    repository_name: str,
    repository_url: str,
    role: str,
    *,
    cache_root: Path,
    measured_at: date,
    fixture_rates: Iterable[float],
) -> dict[str, Any]:
    """Clone and measure one repository at its default branch's pinned commit."""

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    repository = _clone_repository(repository_name, repository_url, cache_root, run_id)
    branch = _default_branch(repository)
    pinned_sha = _run_git(repository, "rev-parse", f"refs/remotes/origin/{branch}").strip()
    commit_date = date.fromisoformat(
        _run_git(repository, "show", "-s", "--format=%cs", pinned_sha).strip()
    )
    py_tree = _read_python_tree(
        repository,
        repository_url,
        pinned_sha,
        repository.parent / "python-snapshot",
    )
    all_python_lines = 0
    source_python_lines = 0
    for _object_id, relative_path in py_tree:
        content = (repository.parent / "python-snapshot" / relative_path).read_text(
            encoding="utf-8", errors="replace"
        )
        lines = len(content.splitlines())
        all_python_lines += lines
        if is_source_python_path(relative_path):
            source_python_lines += lines

    indexed_python_lines = 0
    estimated_chunks = 0
    snapshot_root = repository.parent / "python-snapshot"
    for file_path in sorted(iter_python_files(snapshot_root)):
        content = file_path.read_text(encoding="utf-8", errors="replace")
        indexed_python_lines += len(content.splitlines())
        estimated_chunks += len(candidate_chunk_specs("s0_lines_60_10", content))

    license_text, license_path = _license_blob(repository, pinned_sha)
    license_id = spdx_from_license_text(license_text or "")
    holder = copyright_holder_line(license_text or "")
    clause_count = bsd_clause_count(license_text or "")
    issue_numbers = _qualifying_issue_numbers(repository, pinned_sha)
    method = "git-closing-keywords"
    if len(issue_numbers) < 40:
        verified_issues = _gh_qualifying_issue_numbers(repository_url, commit_date)
        if verified_issues is not None:
            issue_numbers = verified_issues
            method = "gh"

    estimate = estimate_fixture_bytes(estimated_chunks, fixture_rates)
    candidate = {
        "id": repository_name,
        "url": f"https://github.com/{repository_url}",
        "default_branch": branch,
        "pinned_sha": pinned_sha,
        "pinned_commit_date": commit_date.isoformat(),
        "license": license_id,
        "copyright_holder": holder or "Not stated in LICENSE",
        "role": role,
        "source_python_lines": source_python_lines,
        "all_python_lines": all_python_lines,
        "indexed_python_lines": indexed_python_lines,
        "estimated_chunks": estimated_chunks,
        "estimated_fixture_bytes": estimate,
        "fixture_location": fixture_location(estimate),
        "qualifying_issue_count": len(issue_numbers),
        "qualifying_method": method,
        "measured_at": measured_at.isoformat(),
        "license_path": license_path,
        "bsd_clause_count": clause_count,
    }
    return candidate


def run_qualification(
    *,
    cache_root: Path,
    manifest_path: Path,
    measured_at: date | None = None,
) -> dict[str, Any]:
    """Qualify the registered candidates, substituting backups when needed."""

    measured_at = measured_at or date.today()
    fixture_rates = fixture_bytes_per_chunk(manifest_path)
    candidates: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    swaps: list[dict[str, str]] = []
    backup_index = 0

    for original_id, original_url, role in INITIAL_CANDIDATES:
        current_id, current_url = original_id, original_url
        while True:
            candidate = qualify_repository(
                current_id,
                current_url,
                role,
                cache_root=cache_root,
                measured_at=measured_at,
                fixture_rates=fixture_rates,
            )
            failures = _candidate_failures(candidate)
            if not failures:
                candidates.append(
                    {
                        key: value
                        for key, value in candidate.items()
                        if key not in {"license_path", "bsd_clause_count"}
                    }
                )
                if current_id != original_id:
                    swaps.append(
                        {
                            "replaced": original_id,
                            "replacement": current_id,
                            "role": role,
                            "reason": "; ".join(
                                item["reason"]
                                for item in pending + rejected
                                if item["id"] == original_id
                            ),
                        }
                    )
                break

            issue_only_unverified = (
                candidate["qualifying_issue_count"] < 40
                and candidate["qualifying_method"] == "git-closing-keywords"
                and len(failures) == 1
            )
            result = {
                **{
                    key: value
                    for key, value in candidate.items()
                    if key not in {"license_path", "bsd_clause_count"}
                },
                "id": current_id,
                "role": role,
                "status": "pending verification" if issue_only_unverified else "failed",
                "reason": "; ".join(failures),
                "qualifying_issue_count": candidate["qualifying_issue_count"],
                "qualifying_method": candidate["qualifying_method"],
            }
            (pending if issue_only_unverified else rejected).append(result)
            if backup_index >= len(BACKUP_REPOSITORIES):
                break
            current_id, current_url = BACKUP_REPOSITORIES[backup_index]
            backup_index += 1

    return {
        "measured_at": measured_at.isoformat(),
        "fixture_gzip_bytes_per_chunk": fixture_rates,
        "candidates": candidates,
        "pending_verification": pending,
        "rejected": rejected,
        "swaps": swaps,
    }


def write_qualification_report(
    cache_root: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    """Run qualification and write machine-readable output under the ignored cache."""

    report = run_qualification(cache_root=cache_root, manifest_path=manifest_path)
    output = cache_root / "results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
