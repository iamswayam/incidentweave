"""Qualify pinned repository candidates without embedding or building fixtures."""

from __future__ import annotations

import ast
import calendar
import io
import json
import math
import re
import shutil
import subprocess
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse
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
    ("huey", "coleifer/huey"),
    ("luigi", "spotify/luigi"),
    ("gunicorn", "benoitc/gunicorn"),
    ("alembic", "sqlalchemy/alembic"),
)
QUALIFICATION_REPOSITORIES = INITIAL_CANDIDATES + (
    ("huey", "coleifer/huey", "development"),
    ("luigi", "spotify/luigi", "development"),
)


class CandidateQualificationError(RuntimeError):
    """A candidate cannot be qualified against the registered criteria."""


def _gh_executable() -> str:
    executable = shutil.which("gh")
    if executable:
        return executable
    windows_path = Path(r"C:\Program Files\GitHub CLI\gh.exe")
    if windows_path.is_file():
        return str(windows_path)
    raise CandidateQualificationError("GitHub CLI (gh) is not installed or on PATH")


def _gh_json(command: list[str], description: str) -> Any:
    errors: list[str] = []
    for _attempt in range(2):
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=300,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(type(exc).__name__)
            continue
        if completed.returncode != 0:
            errors.append(f"exit code {completed.returncode}")
            continue
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError:
            errors.append("invalid JSON")
    raise CandidateQualificationError(
        f"{description} failed after one retry ({'; '.join(errors)})"
    )


def _gh_text(command: list[str], description: str) -> str:
    errors: list[str] = []
    for _attempt in range(2):
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=300,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(type(exc).__name__)
            continue
        if completed.returncode == 0:
            return completed.stdout
        errors.append(f"exit code {completed.returncode}")
    raise CandidateQualificationError(
        f"{description} failed after one retry ({'; '.join(errors)})"
    )


def _cached_clone(cache_root: Path, repository_id: str, pinned_sha: str) -> Path:
    clones = sorted(
        cache_root.glob(f"{repository_id}-*/repo"),
        key=lambda path: path.parent.name,
        reverse=True,
    )
    for clone in clones:
        if not (clone / ".git").exists():
            continue
        try:
            _run_git(clone, "cat-file", "-e", f"{pinned_sha}^{{commit}}")
        except (OSError, subprocess.SubprocessError):
            continue
        return clone
    raise CandidateQualificationError(
        f"no cached clone for {repository_id} contains pinned commit {pinned_sha}; "
        "run qualify first"
    )


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
) -> set[int]:
    gh = _gh_executable()
    auth_errors: list[str] = []
    authenticated = False
    for _attempt in range(2):
        try:
            auth = subprocess.run(
                [gh, "auth", "status"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            auth_errors.append(str(exc))
            continue
        if auth.returncode == 0:
            authenticated = True
            break
        auth_errors.append(auth.stderr.strip() or "not authenticated")
    if not authenticated:
        raise CandidateQualificationError(
            f"gh auth status failed for {repository_url} after one retry: "
            + "; ".join(auth_errors)
        )

    command = [
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
    ]
    errors: list[str] = []
    pull_requests: list[dict[str, Any]] | None = None
    for _attempt in range(2):
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=300,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(str(exc))
            continue
        if completed.returncode != 0:
            errors.append(completed.stderr.strip() or "gh pr list failed")
            continue
        try:
            response = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            errors.append(f"gh returned invalid JSON: {exc}")
            continue
        if not isinstance(response, list) or any(
            not isinstance(item, dict) for item in response
        ):
            errors.append("gh returned an invalid pull-request list")
            continue
        pull_requests = response
        break
    if pull_requests is None:
        raise CandidateQualificationError(
            f"GitHub PR query failed for {repository_url} after one retry: "
            + "; ".join(errors)
        )

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
            if isinstance(issue, dict)
            and isinstance(issue.get("number"), int)
            and not isinstance(issue.get("number"), bool)
        )
    return issue_numbers


def proposed_spans_from_diff(
    diff_text: str,
    source_root: Path,
    pinned_python_paths: set[str],
) -> dict[str, list[dict[str, int | str]]]:
    """Map PR hunk headers to enclosing pinned-snapshot definitions or files."""

    file_patch = re.compile(r"^\+\+\+ b/(.+)$")
    hunk_header = re.compile(
        r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@(?:\s*(.*))?$"
    )
    context_symbol = re.compile(r"\b(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)")
    output: dict[str, list[dict[str, int | str]]] = {}
    current_path: str | None = None
    for line in diff_text.splitlines():
        file_match = file_patch.match(line)
        if file_match:
            path = file_match.group(1)
            current_path = path if path in pinned_python_paths else None
            continue
        hunk_match = hunk_header.match(line)
        if not hunk_match or current_path is None:
            continue
        root = source_root.resolve()
        source = (root / Path(*PurePosixPath(current_path).parts)).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            continue
        source_lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
        if not source_lines:
            continue
        changed_start = int(hunk_match.group(1))
        changed_count = int(hunk_match.group(2) or "1")
        changed_end = max(changed_start, changed_start + changed_count - 1)
        context_match = context_symbol.search(hunk_match.group(3) or "")
        context_name = context_match.group(1) if context_match else None
        try:
            tree = ast.parse("\n".join(source_lines))
        except SyntaxError:
            tree = None
        definitions: list[
            ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ] = []
        if tree is not None:
            definitions = [
                node
                for node in ast.walk(tree)
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                )
            ]
        containing = [
            node
            for node in definitions
            if node.lineno <= changed_start <= getattr(node, "end_lineno", node.lineno)
            or (
                node.lineno <= changed_end
                and changed_start <= getattr(node, "end_lineno", node.lineno)
            )
        ]
        matching_context = [
            node for node in definitions if context_name and node.name == context_name
        ]
        candidates = containing or matching_context
        if candidates:
            node = min(
                candidates,
                key=lambda item: (
                    getattr(item, "end_lineno", item.lineno) - item.lineno,
                    -item.lineno,
                ),
            )
            proposed: dict[str, int | str] = {
                "start": node.lineno,
                "end": getattr(node, "end_lineno", node.lineno),
                "symbol": node.name,
            }
        else:
            proposed = {"start": 1, "end": len(source_lines), "symbol": "<file>"}
        output.setdefault(current_path, [])
        if proposed not in output[current_path]:
            output[current_path].append(proposed)
    return output


def collect_mined_issues(
    pinned_commit_date: date,
    pull_requests: list[dict[str, Any]],
    issue_details: dict[int, dict[str, str]],
    pull_request_diffs: dict[int, str],
    source_root: Path,
    pinned_python_paths: set[str],
) -> list[dict[str, Any]]:
    """Build deterministic mined-issue records from synthetic or live GH data."""

    linked: list[tuple[int, int, list[str]]] = []
    for pull_request in pull_requests:
        merged_at = pull_request.get("mergedAt")
        number = pull_request.get("number")
        if (
            not isinstance(merged_at, str)
            or not isinstance(number, int)
            or isinstance(number, bool)
            or date.fromisoformat(merged_at[:10]) > pinned_commit_date
        ):
            continue
        files = pull_request.get("files", [])
        source_files = (
            sorted(
                {
                    item["path"]
                    for item in files
                    if isinstance(item, dict)
                    and isinstance(item.get("path"), str)
                    and is_source_python_path(item["path"])
                    and item["path"] in pinned_python_paths
                }
            )
            if isinstance(files, list)
            else []
        )
        if not 1 <= len(source_files) <= 4:
            continue
        issues = pull_request.get("closingIssuesReferences", [])
        for issue in issues if isinstance(issues, list) else []:
            issue_number = issue.get("number") if isinstance(issue, dict) else None
            if (
                isinstance(issue_number, int)
                and not isinstance(issue_number, bool)
                and issue_number > 0
            ):
                linked.append((issue_number, number, source_files))

    linked.sort(key=lambda item: (item[0], item[1]))
    records: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for issue_number, pr_number, files in linked:
        pair = (issue_number, pr_number)
        if pair in seen:
            continue
        seen.add(pair)
        details = issue_details.get(issue_number, {})
        proposed = proposed_spans_from_diff(
            pull_request_diffs.get(pr_number, ""),
            source_root,
            pinned_python_paths,
        )
        file_records = [
            {
                "path": path,
                "proposed_spans": proposed.get(
                    path,
                    [
                        {
                            "start": 1,
                            "end": max(
                                1,
                                len(
                                    (source_root / Path(*PurePosixPath(path).parts))
                                    .read_text(encoding="utf-8", errors="replace")
                                    .splitlines()
                                ),
                            ),
                            "symbol": "<file>",
                        }
                    ],
                ),
            }
            for path in files
        ]
        records.append(
            {
                "candidate_id": f"M-{len(records) + 1:03d}",
                "issue_number": issue_number,
                "issue_title": details.get("title", ""),
                "issue_body": details.get("body", "")[:2000],
                "pr_number": pr_number,
                "files": file_records,
            }
        )
    return records


def mine_candidate_issues(
    candidate: dict[str, Any],
    *,
    cache_root: Path,
    question_cache_root: Path,
) -> Path:
    """Query GitHub for qualifying merged PRs and write ignored mined.json."""

    repository_url = candidate.get("url")
    repository_id = candidate.get("id")
    if not isinstance(repository_url, str) or not isinstance(repository_id, str):
        raise CandidateQualificationError("candidate needs id and GitHub URL")
    slug = urlparse(repository_url).path.strip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", slug):
        raise CandidateQualificationError("candidate URL must identify a GitHub repository")
    pinned_sha = candidate.get("pinned_sha")
    if not isinstance(pinned_sha, str):
        raise CandidateQualificationError("candidate needs a pinned SHA")
    try:
        pinned_date = date.fromisoformat(candidate["pinned_commit_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CandidateQualificationError("candidate needs an ISO pinned commit date") from exc

    repository = _cached_clone(cache_root, repository_id, pinned_sha)
    source_root = repository.parent / "python-snapshot"
    if not source_root.is_dir():
        raise CandidateQualificationError(
            f"pinned Python snapshot missing for {repository_id}; run qualify first"
        )
    python_paths = {path for _, path in _python_tree(repository, pinned_sha)}
    gh = _gh_executable()
    auth = subprocess.run(
        [gh, "auth", "status"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
    )
    if auth.returncode != 0:
        raise CandidateQualificationError("gh auth status failed; authenticate with gh")
    pull_requests_raw = _gh_json(
        [
            gh,
            "pr",
            "list",
            "--repo",
            slug,
            "--state",
            "merged",
            "--limit",
            "1000",
            "--json",
            "closingIssuesReferences,files,mergedAt,number",
        ],
        f"merged PR query for {slug}",
    )
    if not isinstance(pull_requests_raw, list) or any(
        not isinstance(item, dict) for item in pull_requests_raw
    ):
        raise CandidateQualificationError(f"gh returned invalid PR data for {slug}")

    selected_prs: dict[int, dict[str, Any]] = {}
    issue_numbers: set[int] = set()
    for pr in pull_requests_raw:
        merged_at = pr.get("mergedAt")
        pr_number = pr.get("number")
        if (
            not isinstance(merged_at, str)
            or not isinstance(pr_number, int)
            or isinstance(pr_number, bool)
            or date.fromisoformat(merged_at[:10]) > pinned_date
        ):
            continue
        files = pr.get("files")
        source_files = (
            [
                item.get("path")
                for item in files
                if isinstance(item, dict)
                and isinstance(item.get("path"), str)
                and is_source_python_path(item["path"])
                and item["path"] in python_paths
            ]
            if isinstance(files, list)
            else []
        )
        source_files = sorted(set(source_files))
        if not 1 <= len(source_files) <= 4:
            continue
        issues = pr.get("closingIssuesReferences", [])
        valid_issues = (
            [
                issue["number"]
                for issue in issues
                if isinstance(issue, dict)
                and isinstance(issue.get("number"), int)
                and not isinstance(issue.get("number"), bool)
                and issue["number"] > 0
            ]
            if isinstance(issues, list)
            else []
        )
        if not valid_issues:
            continue
        selected_prs[pr_number] = pr
        issue_numbers.update(valid_issues)

    issue_details: dict[int, dict[str, str]] = {}
    for issue_number in sorted(issue_numbers):
        raw_issue = _gh_json(
            [
                gh,
                "issue",
                "view",
                str(issue_number),
                "--repo",
                slug,
                "--json",
                "title,body",
            ],
            f"issue #{issue_number} query for {slug}",
        )
        if not isinstance(raw_issue, dict):
            raise CandidateQualificationError(
                f"gh returned invalid issue #{issue_number} data"
            )
        issue_details[issue_number] = {
            "title": str(raw_issue.get("title") or ""),
            "body": str(raw_issue.get("body") or "")[:2000],
        }

    diffs = {
        number: _gh_text(
            [gh, "pr", "diff", str(number), "--repo", slug],
            f"PR #{number} diff query for {slug}",
        )
        for number in sorted(selected_prs)
    }
    records = collect_mined_issues(
        pinned_date,
        pull_requests_raw,
        issue_details,
        diffs,
        source_root,
        python_paths,
    )
    output = question_cache_root / repository_id / "mined.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


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
    issue_numbers = _gh_qualifying_issue_numbers(repository_url, commit_date)

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
        "qualifying_method": "gh",
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
    """Qualify registered repositories and select replacements when required."""

    measured_at = measured_at or date.today()
    fixture_rates = fixture_bytes_per_chunk(manifest_path)
    selected: list[dict[str, Any]] = []
    qualified: dict[str, dict[str, Any]] = {}
    measured: dict[str, dict[str, Any] | None] = {}
    rejected: list[dict[str, Any]] = []
    verification_errors: list[dict[str, str]] = []
    swaps: list[dict[str, str]] = []

    inputs = list(QUALIFICATION_REPOSITORIES)

    def measure(
        repository_id: str,
        repository_url: str,
        role: str,
    ) -> dict[str, Any] | None:
        if repository_id in measured:
            return measured[repository_id]
        try:
            candidate = qualify_repository(
                repository_id,
                repository_url,
                role,
                cache_root=cache_root,
                measured_at=measured_at,
                fixture_rates=fixture_rates,
            )
        except CandidateQualificationError as exc:
            measured[repository_id] = None
            verification_errors.append(
                {
                    "id": repository_id,
                    "role": role,
                    "reason": str(exc),
                }
            )
            return None
        measured[repository_id] = candidate
        failures = _candidate_failures(candidate)
        if failures:
            rejected.append(
                {
                    **{
                        key: value
                        for key, value in candidate.items()
                        if key not in {"license_path", "bsd_clause_count"}
                    },
                    "status": "failed",
                    "reason": "; ".join(failures),
                }
            )
        else:
            qualified[repository_id] = candidate
        return candidate

    for repository_id, repository_url, role in inputs:
        measure(repository_id, repository_url, role)

    def get_backup(
        backup_id: str,
        role: str,
    ) -> dict[str, Any] | None:
        repository_url = next(
            url for candidate_id, url in BACKUP_REPOSITORIES if candidate_id == backup_id
        )
        return measure(backup_id, repository_url, role)

    for original_id, _original_url, role in INITIAL_CANDIDATES:
        original = qualified.get(original_id)
        if original is not None:
            selected.append(original)
            continue
        if measured.get(original_id) is None:
            continue

        backup_ids = (
            ("huey", "luigi", "gunicorn", "alembic")
            if role == "development"
            else ("gunicorn", "alembic")
        )
        replacement: dict[str, Any] | None = None
        for backup_id in backup_ids:
            replacement = qualified.get(backup_id)
            if replacement is None:
                if backup_id not in measured:
                    get_backup(backup_id, role)
                replacement = qualified.get(backup_id)
            if replacement is not None:
                break
        if replacement is None:
            continue
        selected.append(replacement)
        original_failures = next(
            (
                item["reason"]
                for item in rejected
                if item["id"] == original_id
            ),
            "candidate did not qualify",
        )
        swaps.append(
            {
                "replaced": original_id,
                "replacement": replacement["id"],
                "role": role,
                "reason": original_failures,
            }
        )

    selected_ids = {candidate["id"] for candidate in selected}
    qualified_backups = [
        candidate
        for candidate_id, candidate in qualified.items()
        if candidate_id not in selected_ids
    ]

    return {
        "measured_at": measured_at.isoformat(),
        "fixture_gzip_bytes_per_chunk": fixture_rates,
        "candidates": [
            {
                key: value
                for key, value in candidate.items()
                if key not in {"license_path", "bsd_clause_count"}
            }
            for candidate in selected
        ],
        "qualified_backups": [
            {
                key: value
                for key, value in candidate.items()
                if key not in {"license_path", "bsd_clause_count"}
            }
            for candidate in qualified_backups
        ],
        "rejected": rejected,
        "verification_errors": verification_errors,
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
