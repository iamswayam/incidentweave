from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from evaluation.manifest import load_manifest
from evaluation.splits import assign_splits

COUNTS = {
    "questions": 6,
    "development": 4,
    "held_out": 2,
    "smoke": 2,
    "development_answerable": 2,
    "development_unanswerable": 2,
    "held_out_answerable": 1,
    "held_out_unanswerable": 1,
    "smoke_answerable": 1,
    "smoke_unanswerable": 1,
}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_manifest(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    evaluation = tmp_path / "evaluation"
    questions = [
        {"id": "direct-01", "category": "direct"},
        {"id": "direct-02", "category": "direct"},
        {"id": "direct-03", "category": "direct"},
        {"id": "unanswerable_far-01", "category": "unanswerable_far"},
        {"id": "unanswerable_far-02", "category": "unanswerable_far"},
        {"id": "unanswerable_near-01", "category": "unanswerable_near"},
    ]
    resources = {
        "questions": "evaluation/questions.json",
        "fixture": "evaluation/fixture.bin",
        "full_gate": "evaluation/full-gate.json",
        "full_baseline": "evaluation/full-baseline.json",
        "smoke_baseline": "evaluation/smoke-baseline.json",
        "smoke_gate": "evaluation/smoke-gate.json",
    }
    _write_json(
        evaluation / "questions.json",
        {"pinned_sha": "abc123", "questions": questions},
    )
    fixture = {
        "meta": {"pinned_sha": "abc123"},
        "chunks": [],
        "queries": {question["id"]: [0.0] for question in questions},
    }
    (evaluation / "fixture.bin").write_bytes(
        gzip.compress(json.dumps(fixture).encode("utf-8"), mtime=0)
    )
    for field, baseline_field in (
        ("full_gate", "evaluation/full-baseline.json"),
        ("smoke_gate", "evaluation/smoke-baseline.json"),
    ):
        gate = {
            "baseline_report": baseline_field,
            "baselines": {
                label: {"hit_at_5_successes": 1, "mrr": 0.5}
                for label in ("substring_labels", "spans")
            },
            "tolerance": {
                "hit_at_5_successes_max_drop": 0,
                "mrr_max_drop": 0.02,
            },
        }
        _write_json(tmp_path / resources[field], gate)
    for field in ("full_baseline", "smoke_baseline"):
        _write_json(
            tmp_path / resources[field],
            {
                "metadata": {"golden_pinned_sha": "abc123"},
                "summary": {
                    label: {"hit_at_5": {"successes": 1}, "mrr": 0.5}
                    for label in ("substring_labels", "spans")
                },
            },
        )
    entry = {
        "id": "synthetic",
        "url": "https://example.invalid/synthetic",
        "pinned_sha": "abc123",
        "license_note": "Synthetic source; no external files.",
        "owner": "third-party",
        "previously_exposed": False,
        "indexed_python_lines": 10,
        "questions": {
            "path": resources["questions"],
            "sha256": _digest(tmp_path / resources["questions"]),
        },
        "fixture": {
            "path": resources["fixture"],
            "sha256": _digest(tmp_path / resources["fixture"]),
            "max_bytes": 10_000,
        },
        "full_gate": {
            "path": resources["full_gate"],
            "sha256": _digest(tmp_path / resources["full_gate"]),
        },
        "full_baseline": {
            "path": resources["full_baseline"],
            "sha256": _digest(tmp_path / resources["full_baseline"]),
        },
        "smoke_baseline": {
            "path": resources["smoke_baseline"],
            "sha256": _digest(tmp_path / resources["smoke_baseline"]),
        },
        "smoke_gate": {
            "path": resources["smoke_gate"],
            "sha256": _digest(tmp_path / resources["smoke_gate"]),
        },
        "splits": assign_splits(
            questions,
            123,
            development_answerable=2,
            development_unanswerable=2,
            smoke_answerable=1,
            smoke_unanswerable=1,
        ),
    }
    manifest = {
        "schema_version": 1,
        "split_seed": 123,
        "counts": COUNTS,
        "repositories": [entry],
    }
    path = evaluation / "manifest.json"
    _write_json(path, manifest)
    return path, manifest


def assert_manifest_invalid(
    tmp_path: Path,
    mutate: Any,
    message: str,
) -> None:
    path, manifest = valid_manifest(tmp_path)
    mutate(manifest)
    _write_json(path, manifest)
    with pytest.raises(ValueError, match=message):
        load_manifest(path, expected_counts=COUNTS)


def test_manifest_validates_synthetic_assets_and_hashes(tmp_path: Path) -> None:
    path, _ = valid_manifest(tmp_path)

    manifest = load_manifest(path, expected_counts=COUNTS)

    assert manifest["repositories"][0]["id"] == "synthetic"
    assert manifest["repositories"][0]["splits"] == assign_splits(
        json.loads(
            (tmp_path / "evaluation" / "questions.json").read_text(encoding="utf-8")
        )["questions"],
        manifest["split_seed"],
        development_answerable=2,
        development_unanswerable=2,
        smoke_answerable=1,
        smoke_unanswerable=1,
    )


def test_manifest_rejects_unknown_schema_version(tmp_path: Path) -> None:
    assert_manifest_invalid(
        tmp_path,
        lambda data: data.update(schema_version=999),
        "unknown schema_version",
    )


def test_manifest_rejects_duplicate_repository_ids(tmp_path: Path) -> None:
    assert_manifest_invalid(
        tmp_path,
        lambda data: data["repositories"].append(dict(data["repositories"][0])),
        "repository ids must be unique",
    )


@pytest.mark.parametrize(
    "field",
    [
        "questions",
        "fixture",
        "full_gate",
        "full_baseline",
        "smoke_baseline",
        "smoke_gate",
    ],
)
def test_manifest_rejects_missing_inputs(
    tmp_path: Path,
    field: str,
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["repositories"][0][field]["path"] = "evaluation/missing-file"

    assert_manifest_invalid(tmp_path, mutate, f"missing {field} file")


@pytest.mark.parametrize(
    "field",
    [
        "questions",
        "fixture",
        "full_gate",
        "full_baseline",
        "smoke_baseline",
        "smoke_gate",
    ],
)
def test_manifest_rejects_hash_mismatch(
    tmp_path: Path,
    field: str,
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["repositories"][0][field]["sha256"] = "0" * 64

    assert_manifest_invalid(tmp_path, mutate, f"{field} SHA-256 mismatch")


def test_manifest_rejects_oversized_fixture(tmp_path: Path) -> None:
    assert_manifest_invalid(
        tmp_path,
        lambda data: data["repositories"][0]["fixture"].update(max_bytes=1),
        "fixture exceeds max_bytes",
    )


def test_manifest_rejects_non_partitioning_splits(tmp_path: Path) -> None:
    assert_manifest_invalid(
        tmp_path,
        lambda data: data["repositories"][0]["splits"]["development"].pop(),
        "must partition all question ids",
    )


def test_manifest_rejects_held_out_overlap_with_development(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        splits = data["repositories"][0]["splits"]
        splits["held_out"][0] = splits["development"][0]

    assert_manifest_invalid(tmp_path, mutate, "held_out overlaps development")


def test_manifest_rejects_held_out_overlap_with_smoke(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        splits = data["repositories"][0]["splits"]
        splits["held_out"][0] = splits["smoke"][0]

    assert_manifest_invalid(tmp_path, mutate, "held_out overlaps smoke")


def test_manifest_rejects_smoke_outside_development(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        splits = data["repositories"][0]["splits"]
        splits["smoke"][0] = splits["held_out"][0]

    assert_manifest_invalid(tmp_path, mutate, "smoke must be a subset of development")


def test_manifest_rejects_wrong_configured_counts(tmp_path: Path) -> None:
    assert_manifest_invalid(
        tmp_path,
        lambda data: data["counts"].update(development=3),
        "development has 4 ids; expected 3",
    )


def test_manifest_rejects_wrong_split_counts(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        entry = data["repositories"][0]
        smoke = set(entry["splits"]["smoke"])
        extra = next(item for item in entry["splits"]["development"] if item not in smoke)
        entry["splits"]["smoke"].append(extra)

    assert_manifest_invalid(tmp_path, mutate, "smoke has 3 ids; expected 2")
