"""Loading and fail-closed validation for the multi-repository evaluation manifest."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import zlib
import calendar
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from evaluation.gate import load_gate

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "evaluation" / "manifest.json"
SCHEMA_VERSIONS = {1, 2}
SUPPORTED_CANDIDATE_LICENSES = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0"}
FIXTURE_COMMIT_LIMIT_BYTES = 1_572_864
SHA1_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
DEFAULT_COUNTS = {
    "questions": 24,
    "development": 16,
    "held_out": 8,
    "smoke": 8,
    "development_answerable": 11,
    "development_unanswerable": 5,
    "held_out_answerable": 5,
    "held_out_unanswerable": 3,
    "smoke_answerable": 5,
    "smoke_unanswerable": 3,
}
HASHED_PATH_FIELDS = (
    "questions",
    "fixture",
    "full_gate",
    "full_baseline",
    "smoke_baseline",
    "smoke_gate",
)


def sha256_file(path: Path) -> str:
    """Hash file contents, normalizing JSON line endings across operating systems."""

    content = path.read_bytes()
    if path.suffix.lower() == ".json":
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def manifest_root(path: Path) -> Path:
    """Infer the root that relative manifest asset paths are rooted at."""

    resolved = Path(path).resolve()
    if resolved == MANIFEST_PATH.resolve():
        return ROOT
    parent = resolved.parent
    return parent.parent if parent.name == "evaluation" else parent


def _resolve_file(
    entry: dict[str, Any],
    field: str,
    root: Path,
    errors: list[str],
) -> Path | None:
    resource = entry.get(field)
    if not isinstance(resource, dict):
        errors.append(f"{entry.get('id', '<unknown>')}: {field} must be an object")
        return None
    relative_path = resource.get("path")
    digest = resource.get("sha256")
    if not isinstance(relative_path, str) or not relative_path:
        errors.append(f"{entry.get('id', '<unknown>')}: {field}.path is required")
        return None
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        errors.append(f"{entry.get('id', '<unknown>')}: unsafe {field}.path {relative_path!r}")
        return None
    path = (root / candidate).resolve()
    if not path.is_relative_to(root.resolve()):
        errors.append(f"{entry.get('id', '<unknown>')}: unsafe {field}.path {relative_path!r}")
        return None
    if not path.is_file():
        errors.append(f"{entry.get('id', '<unknown>')}: missing {field} file {relative_path!r}")
        return None
    if not isinstance(digest, str) or not digest:
        errors.append(f"{entry.get('id', '<unknown>')}: {field}.sha256 is required")
    elif sha256_file(path) != digest:
        errors.append(f"{entry.get('id', '<unknown>')}: {field} SHA-256 mismatch")
    return path


def _answerable(question: dict[str, Any]) -> bool:
    category = question.get("category")
    return not (
        isinstance(category, str) and category.startswith("unanswerable")
    )


def _validate_splits(
    entry: dict[str, Any],
    questions: list[dict[str, Any]],
    expected: dict[str, int],
    errors: list[str],
) -> None:
    repo_id = entry.get("id", "<unknown>")
    assignments = entry.get("splits")
    if not isinstance(assignments, dict):
        errors.append(f"{repo_id}: splits must be an object")
        return
    question_ids = [str(question.get("id")) for question in questions]
    all_ids = set(question_ids)
    split_ids: dict[str, list[str]] = {}
    for split in ("development", "held_out", "smoke"):
        values = assignments.get(split)
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            errors.append(f"{repo_id}: splits.{split} must be a list of question ids")
            split_ids[split] = []
            continue
        if len(values) != len(set(values)):
            errors.append(f"{repo_id}: splits.{split} contains duplicate ids")
        split_ids[split] = values
        unknown = set(values) - all_ids
        if unknown:
            errors.append(f"{repo_id}: splits.{split} contains unknown ids {sorted(unknown)}")

    development = set(split_ids["development"])
    held_out = set(split_ids["held_out"])
    smoke = set(split_ids["smoke"])
    if development & held_out:
        errors.append(f"{repo_id}: held_out overlaps development")
    if held_out & smoke:
        errors.append(f"{repo_id}: held_out overlaps smoke")
    if not smoke <= development:
        errors.append(f"{repo_id}: smoke must be a subset of development")
    if development | held_out != all_ids or development & held_out:
        errors.append(f"{repo_id}: development and held_out must partition all question ids")

    question_by_id = {str(question.get("id")): question for question in questions}
    for split in ("development", "held_out", "smoke"):
        selected = [
            question_by_id[item]
            for item in split_ids[split]
            if item in question_by_id
        ]
        expected_total = expected[split]
        if len(split_ids[split]) != expected_total:
            errors.append(
                f"{repo_id}: {split} has {len(split_ids[split])} ids; expected {expected_total}"
            )
        answerable_count = sum(_answerable(question) for question in selected)
        unanswerable_count = len(selected) - answerable_count
        if answerable_count != expected[f"{split}_answerable"]:
            errors.append(
                f"{repo_id}: {split} has {answerable_count} answerable; "
                f"expected {expected[f'{split}_answerable']}"
            )
        if unanswerable_count != expected[f"{split}_unanswerable"]:
            errors.append(
                f"{repo_id}: {split} has {unanswerable_count} unanswerable; "
                f"expected {expected[f'{split}_unanswerable']}"
            )


def _iso_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        return date.fromisoformat(value)
    except ValueError:
        return None


def _within_twelve_months(commit_date: date, measured_at: date) -> bool:
    month_days = calendar.monthrange(measured_at.year - 1, measured_at.month)[1]
    cutoff = date(
        measured_at.year - 1,
        measured_at.month,
        min(measured_at.day, month_days),
    )
    return cutoff <= commit_date <= measured_at


def _validate_candidates(
    candidates: object,
    repository_ids: set[str],
    errors: list[str],
) -> set[str]:
    if not isinstance(candidates, list):
        errors.append("candidates must be a list")
        return set()
    candidate_ids: list[str] = []
    required_strings = (
        "id",
        "url",
        "default_branch",
        "pinned_commit_date",
        "license",
        "copyright_holder",
        "role",
        "qualifying_method",
        "measured_at",
    )
    integer_fields = (
        "source_python_lines",
        "all_python_lines",
        "indexed_python_lines",
        "estimated_chunks",
        "estimated_fixture_bytes",
        "qualifying_issue_count",
    )
    for candidate in candidates:
        if not isinstance(candidate, dict):
            errors.append("every candidate entry must be an object")
            continue
        candidate_id = candidate.get("id")
        if isinstance(candidate_id, str) and candidate_id:
            candidate_ids.append(candidate_id)
        else:
            errors.append("every candidate must have a non-empty id")
        for field in required_strings:
            if not isinstance(candidate.get(field), str) or not candidate[field]:
                errors.append(f"{candidate_id or '<unknown>'}: {field} is required")
        pinned_sha = candidate.get("pinned_sha")
        if not isinstance(pinned_sha, str) or SHA1_PATTERN.fullmatch(pinned_sha) is None:
            errors.append(f"{candidate_id or '<unknown>'}: pinned_sha must be 40 hex characters")
        if candidate.get("license") not in SUPPORTED_CANDIDATE_LICENSES:
            errors.append(
                f"{candidate_id or '<unknown>'}: license must be an allowed SPDX identifier"
            )
        if candidate.get("role") not in {"development", "held_out"}:
            errors.append(
                f"{candidate_id or '<unknown>'}: role must be development or held_out"
            )
        for field in integer_fields:
            value = candidate.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"{candidate_id or '<unknown>'}: {field} must be non-negative")
        source_lines = candidate.get("source_python_lines")
        if (
            isinstance(source_lines, int)
            and not isinstance(source_lines, bool)
            and not 5_000 <= source_lines <= 30_000
        ):
            errors.append(
                f"{candidate_id or '<unknown>'}: source_python_lines must be 5,000-30,000"
            )
        issue_count = candidate.get("qualifying_issue_count")
        if (
            isinstance(issue_count, int)
            and not isinstance(issue_count, bool)
            and issue_count < 40
        ):
            errors.append(
                f"{candidate_id or '<unknown>'}: qualifying_issue_count must be at least 40"
            )
        method = candidate.get("qualifying_method")
        if method not in {"git-closing-keywords", "gh"}:
            errors.append(
                f"{candidate_id or '<unknown>'}: qualifying_method is invalid"
            )
        location = candidate.get("fixture_location")
        if location not in {"committed", "release"}:
            errors.append(
                f"{candidate_id or '<unknown>'}: fixture_location is invalid"
            )
        estimated_bytes = candidate.get("estimated_fixture_bytes")
        if (
            isinstance(estimated_bytes, int)
            and not isinstance(estimated_bytes, bool)
            and estimated_bytes >= 0
            and location in {"committed", "release"}
        ):
            expected_location = (
                "committed"
                if estimated_bytes <= FIXTURE_COMMIT_LIMIT_BYTES
                else "release"
            )
            if location != expected_location:
                errors.append(
                    f"{candidate_id or '<unknown>'}: fixture_location does not match "
                    "estimated_fixture_bytes"
                )
        commit_date = _iso_date(candidate.get("pinned_commit_date"))
        measured_at = _iso_date(candidate.get("measured_at"))
        if commit_date is None:
            errors.append(f"{candidate_id or '<unknown>'}: pinned_commit_date must be ISO date")
        if measured_at is None:
            errors.append(f"{candidate_id or '<unknown>'}: measured_at must be ISO date")
        if (
            commit_date is not None
            and measured_at is not None
            and not _within_twelve_months(commit_date, measured_at)
        ):
            errors.append(
                f"{candidate_id or '<unknown>'}: pinned commit must be within 12 months "
                "of measured_at"
            )
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("candidate ids must be unique")
    if repository_ids.intersection(candidate_ids):
        errors.append("repository and candidate ids must be unique")
    return set(candidate_ids)


def validate_manifest(
    data: dict[str, Any],
    *,
    root: Path = ROOT,
    expected_counts: dict[str, int] = DEFAULT_COUNTS,
) -> list[str]:
    """Return all manifest, asset, hash, size, and split validation errors."""

    errors: list[str] = []
    schema_version = data.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version not in SCHEMA_VERSIONS
    ):
        errors.append(f"unknown schema_version {data.get('schema_version')!r}")
    if not isinstance(data.get("split_seed"), int) or isinstance(data.get("split_seed"), bool):
        errors.append("split_seed must be an integer")
    repositories = data.get("repositories")
    if not isinstance(repositories, list):
        return errors + ["repositories must be a list"]
    ids = [
        entry.get("id")
        for entry in repositories
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    ]
    if len(ids) != len(set(ids)):
        errors.append("repository ids must be unique")
    repository_ids = set(ids)
    if "candidates" in data:
        _validate_candidates(data["candidates"], repository_ids, errors)

    configured_counts = data.get("counts", expected_counts)
    if not isinstance(configured_counts, dict):
        errors.append("counts must be an object")
        configured_counts = expected_counts
    counts = {**expected_counts, **configured_counts}

    for entry in repositories:
        if not isinstance(entry, dict):
            errors.append("every repository entry must be an object")
            continue
        repo_id = entry.get("id")
        if not isinstance(repo_id, str) or not repo_id:
            errors.append("every repository must have a non-empty id")
        for required in ("url", "pinned_sha", "license_note", "owner"):
            if not isinstance(entry.get(required), str) or not entry[required]:
                errors.append(f"{repo_id or '<unknown>'}: {required} is required")
        if entry.get("owner") not in {"maintainer-owned", "third-party"}:
            errors.append(
                f"{repo_id or '<unknown>'}: owner must be maintainer-owned or third-party"
            )
        if not isinstance(entry.get("previously_exposed"), bool):
            errors.append(f"{repo_id or '<unknown>'}: previously_exposed must be boolean")
        review_status = entry.get("review_status", "pending maintainer review")
        if not isinstance(review_status, str) or not review_status:
            errors.append(f"{repo_id or '<unknown>'}: review_status must be a non-empty string")
        max_questions_per_file = entry.get("max_questions_per_file", 3)
        if (
            not isinstance(max_questions_per_file, int)
            or isinstance(max_questions_per_file, bool)
            or max_questions_per_file < 1
        ):
            errors.append(
                f"{repo_id or '<unknown>'}: max_questions_per_file must be a positive integer"
            )
        if (
            not isinstance(entry.get("indexed_python_lines"), int)
            or isinstance(entry.get("indexed_python_lines"), bool)
            or entry["indexed_python_lines"] < 0
        ):
            errors.append(f"{repo_id or '<unknown>'}: indexed_python_lines must be non-negative")

        resolved: dict[str, Path] = {}
        for field in HASHED_PATH_FIELDS:
            path = _resolve_file(entry, field, root, errors)
            if path is not None:
                resolved[field] = path
        fixture = entry.get("fixture")
        if isinstance(fixture, dict):
            max_bytes = fixture.get("max_bytes")
            if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
                errors.append(f"{repo_id or '<unknown>'}: fixture.max_bytes must be positive")
            elif "fixture" in resolved and resolved["fixture"].stat().st_size > max_bytes:
                errors.append(
                    f"{repo_id or '<unknown>'}: fixture exceeds max_bytes ({max_bytes})"
                )

        if "questions" in resolved:
            try:
                question_data = json.loads(resolved["questions"].read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{repo_id or '<unknown>'}: invalid questions JSON: {exc}")
            else:
                questions = (
                    question_data.get("questions")
                    if isinstance(question_data, dict)
                    else None
                )
                if not isinstance(questions, list) or any(
                    not isinstance(question, dict) for question in questions
                ):
                    errors.append(f"{repo_id or '<unknown>'}: questions file has invalid questions")
                else:
                    question_ids_set: set[str] = set()
                    if question_data.get("pinned_sha") != entry.get("pinned_sha"):
                        errors.append(
                            f"{repo_id or '<unknown>'}: questions pinned_sha "
                            "does not match manifest"
                        )
                    if len(questions) != counts["questions"]:
                        errors.append(
                            f"{repo_id or '<unknown>'}: questions has {len(questions)} entries; "
                            f"expected {counts['questions']}"
                        )
                    question_ids = [question.get("id") for question in questions]
                    valid_ids = all(
                        isinstance(item, str) and bool(item) for item in question_ids
                    )
                    if not valid_ids:
                        errors.append(f"{repo_id or '<unknown>'}: every question needs an id")
                    elif len(question_ids) != len(set(question_ids)):
                        errors.append(f"{repo_id or '<unknown>'}: question ids must be unique")
                    else:
                        _validate_splits(entry, questions, counts, errors)
                        question_ids_set = set(question_ids)

                    if "fixture" in resolved:
                        try:
                            fixture_data = json.loads(
                                gzip.decompress(resolved["fixture"].read_bytes())
                            )
                        except (
                            OSError,
                            EOFError,
                            gzip.BadGzipFile,
                            json.JSONDecodeError,
                            zlib.error,
                        ) as exc:
                            errors.append(
                                f"{repo_id or '<unknown>'}: invalid fixture data: {exc}"
                            )
                        else:
                            if not isinstance(fixture_data, dict) or not isinstance(
                                fixture_data.get("meta"), dict
                            ):
                                errors.append(
                                    f"{repo_id or '<unknown>'}: fixture needs metadata"
                                )
                            else:
                                if fixture_data["meta"].get("pinned_sha") != entry.get(
                                    "pinned_sha"
                                ):
                                    errors.append(
                                        f"{repo_id or '<unknown>'}: fixture pinned_sha "
                                        "does not match manifest"
                                    )
                                queries = fixture_data.get("queries")
                                if (
                                    not isinstance(queries, dict)
                                    or set(queries) != question_ids_set
                                ):
                                    errors.append(
                                        f"{repo_id or '<unknown>'}: fixture query ids "
                                        "must match question ids"
                                    )
                                if not isinstance(fixture_data.get("chunks"), list):
                                    errors.append(
                                        f"{repo_id or '<unknown>'}: fixture chunks must be a list"
                                    )

        for gate_field, baseline_field in (
            ("full_gate", "full_baseline"),
            ("smoke_gate", "smoke_baseline"),
        ):
            if gate_field in resolved:
                try:
                    gate = load_gate(resolved[gate_field])
                except ValueError as exc:
                    errors.append(f"{repo_id or '<unknown>'}: {exc}")
                else:
                    baseline_resource = entry.get(baseline_field)
                    if (
                        isinstance(baseline_resource, dict)
                        and gate["baseline_report"] != baseline_resource.get("path")
                    ):
                        errors.append(
                            f"{repo_id or '<unknown>'}: {gate_field} baseline_report "
                            f"does not match {baseline_field}.path"
                        )
                    baseline_path = resolved.get(baseline_field)
                    if baseline_path is not None:
                        try:
                            baseline_report = json.loads(
                                baseline_path.read_text(encoding="utf-8")
                            )
                        except (OSError, json.JSONDecodeError) as exc:
                            errors.append(
                                f"{repo_id or '<unknown>'}: invalid "
                                f"{baseline_field} JSON: {exc}"
                            )
                        else:
                            if not isinstance(baseline_report, dict):
                                errors.append(
                                    f"{repo_id or '<unknown>'}: "
                                    f"{baseline_field} must contain an object"
                                )
                            else:
                                metadata = baseline_report.get("metadata")
                                baseline_sha = (
                                    metadata.get("golden_pinned_sha")
                                    if isinstance(metadata, dict)
                                    else None
                                )
                                if baseline_sha != entry.get("pinned_sha"):
                                    errors.append(
                                        f"{repo_id or '<unknown>'}: "
                                        f"{baseline_field} pinned_sha does not match manifest"
                                    )
                                summary = baseline_report.get("summary")
                                for label_type in ("substring_labels", "spans"):
                                    values = (
                                        summary.get(label_type)
                                        if isinstance(summary, dict)
                                        else None
                                    )
                                    hit_at_5 = (
                                        values.get("hit_at_5")
                                        if isinstance(values, dict)
                                        else None
                                    )
                                    successes = (
                                        hit_at_5.get("successes")
                                        if isinstance(hit_at_5, dict)
                                        else None
                                    )
                                    mrr = values.get("mrr") if isinstance(values, dict) else None
                                    if (
                                        not isinstance(successes, int)
                                        or isinstance(successes, bool)
                                        or successes < 0
                                        or not isinstance(mrr, (int, float))
                                        or isinstance(mrr, bool)
                                        or not math.isfinite(mrr)
                                        or not 0 <= mrr <= 1
                                    ):
                                        errors.append(
                                            f"{repo_id or '<unknown>'}: "
                                            f"{baseline_field} has invalid {label_type} metrics"
                                        )
                                        continue
                                    expected_baseline = gate["baselines"][label_type]
                                    if (
                                        successes
                                        != expected_baseline["hit_at_5_successes"]
                                        or mrr != expected_baseline["mrr"]
                                    ):
                                        errors.append(
                                            f"{repo_id or '<unknown>'}: "
                                            f"{gate_field} {label_type} baseline "
                                            f"does not match {baseline_field}"
                                        )

    return errors


def load_manifest(
    path: Path = MANIFEST_PATH,
    *,
    root: Path | None = None,
    expected_counts: dict[str, int] = DEFAULT_COUNTS,
) -> dict[str, Any]:
    """Load a manifest and raise a clear ValueError for invalid or missing inputs."""

    manifest_path = Path(path)
    base = manifest_root(manifest_path) if root is None else root
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot load evaluation manifest {manifest_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Evaluation manifest must contain an object")
    errors = validate_manifest(data, root=base, expected_counts=expected_counts)
    if errors:
        raise ValueError("Evaluation manifest validation failed: " + "; ".join(errors))
    return data


def repository_entry(manifest: dict[str, Any], repo_id: str) -> dict[str, Any]:
    """Return one repository entry or raise rather than silently skipping it."""

    for entry in manifest["repositories"]:
        if entry["id"] == repo_id:
            return entry
    raise ValueError(f"Repository {repo_id!r} is not in the evaluation manifest")


def select_repositories(manifest: dict[str, Any], repo_id: str | None) -> list[dict[str, Any]]:
    """Select all manifest repositories or one explicitly named repository."""

    if repo_id is None:
        return list(manifest["repositories"])
    return [repository_entry(manifest, repo_id)]


def questions_for_split(
    entry: dict[str, Any],
    questions: list[dict[str, Any]],
    split: str,
) -> list[dict[str, Any]]:
    """Select the explicit manifest question assignment for a requested split."""

    if split not in {"development", "held_out", "smoke", "all"}:
        raise ValueError(f"Unknown evaluation split {split!r}")
    if split == "all":
        return list(questions)
    selected_ids = set(entry["splits"][split])
    return [question for question in questions if question["id"] in selected_ids]
