"""Utilities to compare evaluation runs in a stable, legacy-tolerant way."""

from __future__ import annotations

from typing import Any


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _extract_pass_records(report: dict[str, Any]) -> list[dict[str, Any]]:
    records = report.get("records")
    if isinstance(records, list) and records and isinstance(records[0], list):
        return [item for group in records[:1] for item in group]
    if isinstance(records, list):
        return [item for item in records if isinstance(item, dict)]
    return []


def _value_or_none(value: object) -> object:
    return value if value is not None else None


def _diff_counts(left: object, right: object) -> dict[str, int]:
    left_map = left if isinstance(left, dict) else {}
    right_map = right if isinstance(right, dict) else {}
    keys = sorted(set(left_map) | set(right_map))
    return {
        key: int(right_map.get(key, 0) - left_map.get(key, 0))
        for key in keys
    }


def _numeric_delta(left: object, right: object) -> dict[str, float | int | None]:
    left_value = None if left is None else float(left)
    right_value = None if right is None else float(right)
    if left_value is None and right_value is None:
        return {"delta": None}
    if left_value is None:
        return {"delta": right_value}
    if right_value is None:
        return {"delta": -left_value}
    return {"delta": right_value - left_value}


def compare_reports(report_a: dict[str, Any], report_b: dict[str, Any]) -> dict[str, Any]:
    """Return a stable difference summary between two evaluation reports.

    Missing fields are treated as None; legacy reports without the Phase 8b metadata
    are still compared without crashing.
    """

    a = report_a if isinstance(report_a, dict) else {}
    b = report_b if isinstance(report_b, dict) else {}
    legacy_report = bool(
        not (
            ("outcome_v2_counts" in a or "guard_counts" in a or "retrieval_tables" in a)
            and ("outcome_v2_counts" in b or "guard_counts" in b or "retrieval_tables" in b)
        )
    )

    config_keys = [
        "run_id",
        "pinned_sha",
        "code_sha",
        "code_dirty",
        "golden_set_sha256",
        "golden_review_status",
        "models",
        "limit",
        "thresholds",
        "prompt_sha256",
        "generation_config",
        "passes",
        "config_sha256",
    ]
    config_differences = {}
    for key in config_keys:
        left = a.get(key)
        right = b.get(key)
        if left != right:
            config_differences[key] = {
                "from": _value_or_none(left),
                "to": _value_or_none(right),
            }

    records_a = {
        str(item.get("id")): item
        for item in _extract_pass_records(a)
        if isinstance(item, dict) and item.get("id") is not None
    }
    records_b = {
        str(item.get("id")): item
        for item in _extract_pass_records(b)
        if isinstance(item, dict) and item.get("id") is not None
    }

    question_flips: dict[str, Any] = {}
    for question_id in sorted(set(records_a) | set(records_b)):
        left_record = records_a.get(question_id)
        right_record = records_b.get(question_id)
        if left_record is None or right_record is None:
            continue
        left_outcome = left_record.get("outcome_v2")
        right_outcome = right_record.get("outcome_v2")
        left_rank = left_record.get("labeled_rank")
        right_rank = right_record.get("labeled_rank")
        if left_outcome != right_outcome or left_rank != right_rank:
            question_flips[question_id] = {}
            if left_outcome != right_outcome:
                question_flips[question_id]["outcome_v2"] = {
                    "from": left_outcome,
                    "to": right_outcome,
                }
            if left_rank != right_rank:
                question_flips[question_id]["labeled_rank"] = {
                    "from": left_rank,
                    "to": right_rank,
                }

    latency_a = _as_dict(_as_dict(a.get("latency_summary") or {}).get("pass_1"))
    latency_b = _as_dict(_as_dict(b.get("latency_summary") or {}).get("pass_1"))
    generation_ms_a = _as_dict(latency_a.get("generation_ms"))
    generation_ms_b = _as_dict(latency_b.get("generation_ms"))
    median_generation_ms_a = generation_ms_a.get("median")
    median_generation_ms_b = generation_ms_b.get("median")

    token_a = _as_dict(_as_dict(a.get("token_summary") or {}).get("pass_1"))
    token_b = _as_dict(_as_dict(b.get("token_summary") or {}).get("pass_1"))
    total_tokens_a = _as_dict(token_a.get("total_tokens"))
    total_tokens_b = _as_dict(token_b.get("total_tokens"))
    median_total_tokens_a = total_tokens_a.get("median")
    median_total_tokens_b = total_tokens_b.get("median")

    return {
        "legacy_report": legacy_report,
        "config_differences": config_differences,
        "outcome_v2_counts_delta": _diff_counts(
            a.get("outcome_v2_counts"),
            b.get("outcome_v2_counts"),
        ),
        "guard_counts_delta": _diff_counts(a.get("guard_counts"), b.get("guard_counts")),
        "retrieval_tables_delta": {
            method: {
                metric: float((right or 0) - (left or 0))
                if isinstance(left, (int, float)) and isinstance(right, (int, float))
                else {"from": left, "to": right}
                for metric, left in (dict(left_map or {}).items())
                for right in [dict(right_map or {}).get(metric)]
            }
            for method, left_map in _as_dict(a.get("retrieval_tables")).items()
            for right_map in [_as_dict(_as_dict(b.get("retrieval_tables")).get(method))]
        },
        "question_flips": question_flips,
        "generation_latency_delta": {
            "median_generation_ms": (
                (float(median_generation_ms_b) - float(median_generation_ms_a))
                if median_generation_ms_a is not None and median_generation_ms_b is not None
                else None
            )
        },
        "total_token_delta": {
            "median_total_tokens": (
                (float(median_total_tokens_b) - float(median_total_tokens_a))
                if median_total_tokens_a is not None and median_total_tokens_b is not None
                else None
            )
        },
    }
