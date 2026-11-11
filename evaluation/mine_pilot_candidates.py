"""Mine issue-linked source changes for the rq and kopf pilot sets."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.secret_scan import find_secret
from evaluation.source_paths import is_source_python_path, is_test_path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "evaluation" / "manifest.json"
CACHE_ROOT = ROOT / "evaluation" / "cache" / "pilot_candidates"
PILOT_REPOSITORIES = {"rq", "kopf"}
EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)


def _valid_number(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _date_before_pin(value: object, pinned_date: date) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value[:10]) <= pinned_date
    except ValueError:
        return False


def _clean_issue_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return EMAIL_PATTERN.sub("[redacted email]", value)[:2000]


def collect_pilot_candidates(
    repo_id: str,
    repository: str,
    pinned_sha: str,
    pinned_date: date,
    issues: list[dict[str, Any]],
    pull_requests: list[dict[str, Any]],
    pinned_paths: set[str],
) -> list[dict[str, Any]]:
    """Join closed linked issues to merged PRs with only extant non-test changes."""

    issue_by_number = {
        issue["number"]: issue
        for issue in issues
        if _valid_number(issue.get("number"))
        and _date_before_pin(issue.get("closedAt"), pinned_date)
    }
    records: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for pull_request in sorted(
        pull_requests, key=lambda item: item.get("number", 0) if isinstance(item, dict) else 0
    ):
        pr_number = pull_request.get("number")
        if not _valid_number(pr_number) or not _date_before_pin(
            pull_request.get("mergedAt"), pinned_date
        ):
            continue
        files = pull_request.get("files")
        if not isinstance(files, list) or not files:
            continue
        if any(
            not isinstance(item, dict) or not isinstance(item.get("path"), str) for item in files
        ):
            continue
        changed_files = sorted({item["path"] for item in files})
        if (
            not changed_files
            or len(changed_files) != len(files)
            or any(path not in pinned_paths or is_test_path(path) for path in changed_files)
        ):
            continue
        source_files = sorted(path for path in changed_files if is_source_python_path(path))
        if not source_files:
            continue
        issue_refs = pull_request.get("closingIssuesReferences")
        if not isinstance(issue_refs, list):
            continue
        for issue_ref in issue_refs:
            issue_number = issue_ref.get("number") if isinstance(issue_ref, dict) else None
            if not _valid_number(issue_number) or issue_number not in issue_by_number:
                continue
            pair = (issue_number, pr_number)
            if pair in seen:
                continue
            seen.add(pair)
            issue = issue_by_number[issue_number]
            title = _clean_issue_text(issue.get("title"))
            body = _clean_issue_text(issue.get("body"))
            if find_secret(title) or find_secret(body):
                continue
            records.append(
                {
                    "candidate_id": f"M-{len(records) + 1:03d}",
                    "repo_id": repo_id,
                    "repository": repository,
                    "pinned_sha": pinned_sha,
                    "issue_number": issue_number,
                    "issue_title": title,
                    "issue_body": body,
                    "issue_url": issue.get("url", ""),
                    "pr_number": pr_number,
                    "pr_url": pull_request.get("url", ""),
                    "changed_files": changed_files,
                    "changed_source_files": source_files,
                    "diff_command": f"gh pr diff {pr_number} --repo {repository}",
                }
            )
    return records


def _manifest_candidate(repo_id: str, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("manifest candidates must be a list")
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id") == repo_id:
            return candidate
    raise ValueError(f"manifest has no candidate {repo_id!r}")


def _run_git(repository_path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository_path), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed with exit code {result.returncode}")
    return result.stdout.strip()


def _run_gh_json(*args: str) -> Any:
    executable = shutil.which("gh")
    if executable is None:
        raise RuntimeError("GitHub CLI (gh) is not installed or on PATH")
    result = subprocess.run(
        [executable, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])} failed with exit code {result.returncode}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("gh returned invalid JSON") from exc


def _clone_at_pin(candidate: dict[str, Any], clone_path: Path) -> tuple[str, set[str]]:
    repository_url = candidate.get("url")
    pinned_sha = candidate.get("pinned_sha")
    if not isinstance(repository_url, str) or not isinstance(pinned_sha, str):
        raise ValueError("pilot candidate needs a repository URL and pinned SHA")
    slug = urlparse(repository_url).path.strip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", slug):
        raise ValueError("pilot candidate URL must identify a GitHub repository")
    if clone_path.exists():
        if not (clone_path / ".git").exists():
            raise RuntimeError(f"clone path exists but is not a git repository: {clone_path}")
    else:
        clone_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--single-branch",
                "--no-tags",
                "--no-checkout",
                repository_url,
                str(clone_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git clone failed with exit code {result.returncode}")
    _run_git(clone_path, "checkout", "--detach", pinned_sha)
    actual_sha = _run_git(clone_path, "rev-parse", "HEAD")
    if actual_sha != pinned_sha:
        raise RuntimeError(f"clone is at {actual_sha}, expected pinned commit {pinned_sha}")
    paths = set(_run_git(clone_path, "ls-tree", "-r", "--name-only", pinned_sha).splitlines())
    return slug, paths


def mine_pilot_candidates(
    repo_id: str,
    *,
    manifest_path: Path = MANIFEST_PATH,
    cache_root: Path = CACHE_ROOT,
) -> Path:
    """Clone one registered pilot pin and save eligible issue/PR pairs in ignored cache."""

    if repo_id not in PILOT_REPOSITORIES:
        raise ValueError(f"pilot mining is limited to {', '.join(sorted(PILOT_REPOSITORIES))}")
    candidate = _manifest_candidate(repo_id, manifest_path)
    pinned_sha = candidate.get("pinned_sha")
    try:
        pinned_date = date.fromisoformat(candidate["pinned_commit_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("pilot candidate needs an ISO pinned commit date") from exc
    clone_path = cache_root / repo_id / "repo"
    repository, pinned_paths = _clone_at_pin(candidate, clone_path)
    issues = _run_gh_json(
        "issue",
        "list",
        "--repo",
        repository,
        "--state",
        "closed",
        "--search",
        "linked:pr",
        "--limit",
        "1000",
        "--json",
        "body,closedAt,number,title,url",
    )
    pull_requests = _run_gh_json(
        "pr",
        "list",
        "--repo",
        repository,
        "--state",
        "merged",
        "--limit",
        "1000",
        "--json",
        "closingIssuesReferences,files,mergedAt,number,url",
    )
    if not isinstance(issues, list) or not isinstance(pull_requests, list):
        raise RuntimeError("gh returned an unexpected issue or pull request list")
    records = collect_pilot_candidates(
        repo_id,
        repository,
        str(pinned_sha),
        pinned_date,
        issues,
        pull_requests,
        pinned_paths,
    )
    output_path = cache_root / repo_id / "candidates.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(records, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_id", choices=sorted(PILOT_REPOSITORIES))
    args = parser.parse_args()
    output_path = mine_pilot_candidates(args.repo_id)
    records = json.loads(output_path.read_text(encoding="utf-8"))
    print(f"Mined {len(records)} eligible candidates for {args.repo_id}: {output_path}")
    for record in records:
        print(
            f"{record['candidate_id']} issue {record['issue_number']} -> PR {record['pr_number']}"
        )


if __name__ == "__main__":
    main()
