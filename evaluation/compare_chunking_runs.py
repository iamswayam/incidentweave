"""Compare two saved chunking-evaluation runs without database or API access."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "evaluation" / "results" / "runs"
PASS_NAMES = ("pass-1", "pass-2")
HIT_CUTOFFS = (1, 3, 5)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_run(run_dir: Path) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Load saved report metadata and pass records from one run folder."""

    metadata = _read_json(run_dir / "report.json")
    if not isinstance(metadata, dict):
        raise ValueError(f"{run_dir / 'report.json'} must contain a JSON object")
    passes: dict[str, list[dict[str, Any]]] = {}
    for pass_name in PASS_NAMES:
        path = run_dir / f"{pass_name}.json"
        if not path.is_file():
            continue
        records = _read_json(path)
        if not isinstance(records, list) or not all(
            isinstance(record, dict) for record in records
        ):
            raise ValueError(f"{path} must contain a list of JSON objects")
        passes[pass_name] = records
    if not passes:
        raise ValueError(f"No pass-1.json or pass-2.json found in {run_dir}")
    return metadata, passes


def read_pinned_source(pinned_sha: str, file_path: str) -> str:
    """Read one source file from the pinned commit using read-only git show."""

    path = Path(file_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe pinned source path: {file_path!r}")
    result = subprocess.run(
        ["git", "show", f"{pinned_sha}:{file_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _function_or_class_span(source: str, label: str) -> tuple[int, int] | None:
    """Return the tightest enclosing function/class line span for a label."""

    positions = []
    position = source.find(label)
    while position >= 0:
        positions.append(position)
        position = source.find(label, position + 1)
    if not positions:
        raise ValueError(f"Label substring is absent from pinned source: {label!r}")
    tree = ast.parse(source)
    scopes = [
        node
        for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        )
    ]
    for position in positions:
        label_line = source.count("\n", 0, position) + 1
        enclosing = [
            node
            for node in scopes
            if node.lineno <= label_line <= (node.end_lineno or node.lineno)
        ]
        if enclosing:
            node = min(
                enclosing,
                key=lambda item: (item.end_lineno or item.lineno) - item.lineno,
            )
            return node.lineno, node.end_lineno or node.lineno
    return None


def _rank(record: dict[str, Any]) -> int | None:
    if "labeled_rank" in record:
        value = record.get("labeled_rank")
        return value if isinstance(value, int) and not isinstance(value, bool) else None
    labels = record.get("relevant") or []
    for index, result in enumerate(record.get("retrieval_results") or [], start=1):
        if not isinstance(result, dict):
            continue
        file_path = result.get("file_path")
        content = str(result.get("content") or "").casefold()
        if any(
            isinstance(label, dict)
            and file_path == label.get("file_path")
            and str(label.get("substring") or "").casefold() in content
            for label in labels
        ):
            return index
    return None


def _answerable(record: dict[str, Any]) -> bool:
    return not str(record.get("category") or "").startswith("unanswerable")


def _hit(rank: int | None, cutoff: int) -> bool:
    return rank is not None and rank <= cutoff


def _question_function_hit(
    record: dict[str, Any],
    sources: dict[str, str],
) -> bool | None:
    labels = [label for label in record.get("relevant") or [] if isinstance(label, dict)]
    top_five = [
        item
        for item in (record.get("retrieval_results") or [])[:5]
        if isinstance(item, dict)
    ]
    applicable_spans: list[tuple[str, int, int]] = []
    for label in labels:
        file_path = str(label.get("file_path") or "")
        source = sources.get(file_path)
        if source is None:
            raise ValueError(f"No pinned source loaded for {file_path!r}")
        span = _function_or_class_span(
            source, str(label.get("substring") or "")
        )
        if span is not None:
            applicable_spans.append((file_path, span[0], span[1]))
    if not applicable_spans:
        return None
    return any(
        item.get("file_path") == file_path
        and isinstance(item.get("line_start"), int)
        and isinstance(item.get("line_end"), int)
        and item["line_start"] <= start_line
        and item["line_end"] >= end_line
        for item in top_five
        for file_path, start_line, end_line in applicable_spans
    )


def _summary(
    records: list[dict[str, Any]],
    sources: dict[str, str],
) -> dict[str, Any]:
    answerable = [record for record in records if _answerable(record)]

    def summarize_group(group: list[dict[str, Any]]) -> dict[str, int | float]:
        group_ranks = [_rank(record) for record in group]
        count = len(group)
        return {
            "questions": count,
            "hit_at_1": sum(_hit(rank, 1) for rank in group_ranks),
            "hit_at_3": sum(_hit(rank, 3) for rank in group_ranks),
            "hit_at_5": sum(_hit(rank, 5) for rank in group_ranks),
            "mrr": (
                sum(1 / rank if rank is not None else 0 for rank in group_ranks)
                / count
                if count
                else 0.0
            ),
        }

    by_category = {
        category: summarize_group(
            [record for record in answerable if record.get("category") == category]
        )
        for category in ("direct", "paraphrased")
    }
    by_label_file_type: dict[str, dict[str, int | float]] = {}
    for file_type in ("test_file", "non_test_file"):
        group = [
            record
            for record in answerable
            if any(
                _is_test_path(str(label.get("file_path") or "")) == (file_type == "test_file")
                for label in record.get("relevant") or []
                if isinstance(label, dict)
            )
        ]
        by_label_file_type[file_type] = summarize_group(group)

    file_hits = 0
    function_hits = 0
    function_applicable = 0
    function_not_applicable = 0
    for record in answerable:
        labels = [label for label in record.get("relevant") or [] if isinstance(label, dict)]
        top_five = [
            item
            for item in (record.get("retrieval_results") or [])[:5]
            if isinstance(item, dict)
        ]
        if any(
            item.get("file_path") == label.get("file_path")
            for item in top_five
            for label in labels
        ):
            file_hits += 1

        function_hit = _question_function_hit(record, sources)
        if function_hit is None:
            function_not_applicable += 1
            continue
        function_applicable += 1
        if function_hit:
            function_hits += 1

    question_usage = []
    for record in records:
        context_chars = sum(
            len(str(item.get("content") or ""))
            for item in (record.get("retrieval_results") or [])[:5]
            if isinstance(item, dict)
        )
        trace = record.get("generation_trace")
        total_tokens = (
            trace.get("total_tokens")
            if isinstance(trace, dict)
            and isinstance(trace.get("total_tokens"), (int, float))
            and not isinstance(trace.get("total_tokens"), bool)
            else None
        )
        question_usage.append(
            {
                "id": record.get("id"),
                "top5_context_characters": context_chars,
                "total_tokens": total_tokens,
            }
        )
    contexts = [item["top5_context_characters"] for item in question_usage]
    token_values = [
        item["total_tokens"] for item in question_usage if item["total_tokens"] is not None
    ]
    false_accepts = sum(
        not _answerable(record)
        and isinstance(record.get("evidence_check"), dict)
        and record["evidence_check"].get("is_sufficient") is True
        for record in records
    )
    outcomes = Counter(
        record.get("outcome_v2", "missing") for record in records
    )
    return {
        "overall": summarize_group(answerable),
        "by_category": by_category,
        "by_label_file_type": by_label_file_type,
        "hit_by_file": {
            "hit_at_5": file_hits,
            "questions": len(answerable),
        },
        "hit_by_function": {
            "hit_at_5": function_hits,
            "applicable_questions": function_applicable,
            "not_applicable_module_level": function_not_applicable,
        },
        "top5_context_characters": {
            "median": median(contexts) if contexts else None,
            "per_question": [
                {"id": item["id"], "characters": item["top5_context_characters"]}
                for item in question_usage
            ],
        },
        "total_tokens": {
            "median": median(token_values) if token_values else None,
            "questions": len(token_values),
            "per_question": [
                {"id": item["id"], "total_tokens": item["total_tokens"]}
                for item in question_usage
            ],
        },
        "guard_false_accepts": false_accepts,
        "outcome_v2_counts": dict(sorted(outcomes.items(), key=lambda item: str(item[0]))),
    }


def _is_test_path(file_path: str) -> bool:
    normalized = file_path.replace("\\", "/")
    return normalized.startswith("tests/") or "/tests/" in normalized


def _prepare_sources(
    pinned_sha: str,
    passes: dict[str, list[dict[str, Any]]],
    source_reader: Callable[[str, str], str],
) -> dict[str, str]:
    paths = {
        str(label.get("file_path") or "")
        for records in passes.values()
        for record in records
        if _answerable(record)
        for label in record.get("relevant") or []
        if isinstance(label, dict)
    }
    return {path: source_reader(pinned_sha, path) for path in sorted(paths)}


def _paired_questions(
    baseline: list[dict[str, Any]],
    experiment: list[dict[str, Any]],
    sources: dict[str, str],
) -> list[dict[str, Any]]:
    baseline_by_id = {str(record.get("id")): record for record in baseline}
    experiment_by_id = {str(record.get("id")): record for record in experiment}
    answerable_ids = sorted(
        {
            identifier
            for identifier, record in baseline_by_id.items()
            if _answerable(record)
        }
        | {
            identifier
            for identifier, record in experiment_by_id.items()
            if _answerable(record)
        }
    )
    rows = []
    for identifier in answerable_ids:
        baseline_record = baseline_by_id.get(identifier, {})
        experiment_record = experiment_by_id.get(identifier, {})
        baseline_rank = _rank(baseline_record)
        experiment_rank = _rank(experiment_record)
        gained = [
            f"@{cutoff}"
            for cutoff in HIT_CUTOFFS
            if not _hit(baseline_rank, cutoff) and _hit(experiment_rank, cutoff)
        ]
        lost = [
            f"@{cutoff}"
            for cutoff in HIT_CUTOFFS
            if _hit(baseline_rank, cutoff) and not _hit(experiment_rank, cutoff)
        ]
        rows.append(
            {
                "id": identifier,
                "category": experiment_record.get(
                    "category", baseline_record.get("category")
                ),
                "baseline_labeled_rank": baseline_rank,
                "experiment_labeled_rank": experiment_rank,
                "baseline_hits": {
                    f"hit_at_{cutoff}": _hit(baseline_rank, cutoff)
                    for cutoff in HIT_CUTOFFS
                },
                "experiment_hits": {
                    f"hit_at_{cutoff}": _hit(experiment_rank, cutoff)
                    for cutoff in HIT_CUTOFFS
                },
                "baseline_hit_by_file": _hit_by_file(baseline_record),
                "experiment_hit_by_file": _hit_by_file(experiment_record),
                "baseline_hit_by_function": _question_function_hit(
                    baseline_record, sources
                ),
                "experiment_hit_by_function": _question_function_hit(
                    experiment_record, sources
                ),
                "gained_hits": gained,
                "lost_hits": lost,
            }
        )
    return rows


def _hit_by_file(record: dict[str, Any]) -> bool:
    labels = [label for label in record.get("relevant") or [] if isinstance(label, dict)]
    return any(
        item.get("file_path") == label.get("file_path")
        for item in (record.get("retrieval_results") or [])[:5]
        if isinstance(item, dict)
        for label in labels
    )


def _display_hit(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def _outcome_changes(
    baseline_passes: dict[str, list[dict[str, Any]]],
    experiment_passes: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    changes = []
    for pass_name in PASS_NAMES:
        if pass_name not in baseline_passes or pass_name not in experiment_passes:
            continue
        baseline_by_id = {
            str(record.get("id")): record for record in baseline_passes[pass_name]
        }
        experiment_by_id = {
            str(record.get("id")): record for record in experiment_passes[pass_name]
        }
        for identifier in sorted(set(baseline_by_id) | set(experiment_by_id)):
            before = baseline_by_id.get(identifier, {}).get("outcome_v2")
            after = experiment_by_id.get(identifier, {}).get("outcome_v2")
            if before != after:
                changes.append(
                    {
                        "pass": pass_name,
                        "id": identifier,
                        "baseline": before,
                        "experiment": after,
                    }
                )
    return changes


def _gates(
    paired: list[dict[str, Any]],
    baseline_metrics: dict[str, dict[str, Any]],
    experiment_metrics: dict[str, dict[str, Any]],
    baseline_records: list[dict[str, Any]],
    experiment_records: list[dict[str, Any]],
) -> list[dict[str, str]]:
    primary = "pass-1" if "pass-1" in baseline_metrics else next(iter(baseline_metrics))
    base = baseline_metrics[primary]
    candidate = experiment_metrics.get(primary, {})
    hit5_delta = (
        candidate.get("overall", {}).get("hit_at_5", 0)
        - base.get("overall", {}).get("hit_at_5", 0)
    )
    hit3_deltas = {
        pass_name: metrics.get("overall", {}).get("hit_at_3", 0)
        - baseline_metrics[pass_name].get("overall", {}).get("hit_at_3", 0)
        for pass_name, metrics in experiment_metrics.items()
        if pass_name in baseline_metrics
    }
    hit5_deltas = {
        pass_name: metrics.get("overall", {}).get("hit_at_5", 0)
        - baseline_metrics[pass_name].get("overall", {}).get("hit_at_5", 0)
        for pass_name, metrics in experiment_metrics.items()
        if pass_name in baseline_metrics
    }
    lost_questions = [
        row["id"]
        for row in paired
        if row["baseline_hits"]["hit_at_5"]
        and not row["experiment_hits"]["hit_at_5"]
    ]
    baseline_false_accepts = base.get("guard_false_accepts", 0)
    experiment_false_accepts = candidate.get("guard_false_accepts", 0)
    baseline_answered = base.get("outcome_v2_counts", {}).get(
        "answered_unanswerable", 0
    )
    experiment_answered = candidate.get("outcome_v2_counts", {}).get(
        "answered_unanswerable", 0
    )
    baseline_answered_ids = {
        str(record.get("id"))
        for record in baseline_records
        if str(record.get("category") or "").startswith("unanswerable")
        and record.get("outcome_v2") == "answered_unanswerable"
    }
    experiment_answered_ids = {
        str(record.get("id"))
        for record in experiment_records
        if str(record.get("category") or "").startswith("unanswerable")
        and record.get("outcome_v2") == "answered_unanswerable"
    }
    new_answered_ids = experiment_answered_ids - baseline_answered_ids
    baseline_tokens = base.get("total_tokens", {}).get("median")
    experiment_tokens = candidate.get("total_tokens", {}).get("median")
    token_ok = (
        isinstance(baseline_tokens, (int, float))
        and isinstance(experiment_tokens, (int, float))
        and experiment_tokens <= baseline_tokens * 1.5
    )
    file_base = base.get("hit_by_file", {}).get("hit_at_5", 0)
    file_candidate = candidate.get("hit_by_file", {}).get("hit_at_5", 0)
    function_base = base.get("hit_by_function", {})
    function_candidate = candidate.get("hit_by_function", {})
    function_applicable = function_base.get("applicable_questions", 0)
    candidate_function_applicable = function_candidate.get("applicable_questions", 0)
    function_ok = (
        candidate_function_applicable == function_applicable
        and (
            function_applicable == 0
            or function_candidate.get("hit_at_5", 0)
            > function_base.get("hit_at_5", 0)
        )
    )
    mrr_delta = (
        candidate.get("overall", {}).get("mrr", 0)
        - base.get("overall", {}).get("mrr", 0)
    )
    return [
        {
            "gate": "1",
            "status": "PASS" if hit5_delta >= 2 else "FAIL",
            "evidence": f"pass-1 net Hit@5={hit5_delta}; required >= 2",
        },
        {
            "gate": "2",
            "status": (
                "PASS"
                if hit3_deltas
                and all(delta >= 0 for delta in hit3_deltas.values())
                and all(delta >= 0 for delta in hit5_deltas.values())
                else "FAIL"
            ),
            "evidence": f"Hit@3 deltas={hit3_deltas}; Hit@5 deltas={hit5_deltas}",
        },
        {
            "gate": "3",
            "status": "PASS" if not lost_questions else "FAIL",
            "evidence": (
                f"previously hit@5 questions lost={lost_questions}; "
                "each loss requires an explanation"
            ),
        },
        {
            "gate": "4",
            "status": (
                "PASS"
                if experiment_false_accepts <= 4
                and not new_answered_ids
                else "FAIL"
            ),
            "evidence": (
                f"false accepts baseline={baseline_false_accepts}, "
                f"experiment={experiment_false_accepts} (limit 4); "
                f"answered-unanswerable baseline={baseline_answered}, "
                f"experiment={experiment_answered}; "
                f"new answered-unanswerable questions={sorted(new_answered_ids)}"
            ),
        },
        {
            "gate": "5",
            "status": "MANUAL",
            "evidence": "human-reviewed end-to-end correctness is not computed",
        },
        {
            "gate": "6",
            "status": "PASS" if token_ok else "FAIL",
            "evidence": (
                f"median total tokens baseline={baseline_tokens}, "
                f"experiment={experiment_tokens}; limit=1.5x baseline"
            ),
        },
        {
            "gate": "7",
            "status": (
                "PASS"
                if file_candidate > file_base and function_ok
                else "FAIL"
            ),
            "evidence": (
                f"hit-by-file@5 baseline={file_base}, experiment={file_candidate}; "
                f"hit-by-function@5 baseline={function_base.get('hit_at_5', 0)}, "
                f"experiment={function_candidate.get('hit_at_5', 0)} "
                f"({function_applicable} applicable, "
                f"{function_base.get('not_applicable_module_level', 0)} module-level n/a)"
            ),
        },
        {
            "gate": "8",
            "status": "FAIL" if hit5_delta == 1 else "PASS",
            "evidence": (
                "net gain is exactly +1 Hit@5: INCONCLUSIVE; retain baseline"
                if hit5_delta == 1
                else f"net Hit@5={hit5_delta}; only exactly +1 is inconclusive"
            ),
        },
        {
            "gate": "9",
            "status": "PASS",
            "evidence": f"MRR delta={mrr_delta:.6f}; supporting only, not an adoption route",
        },
    ]


def compare_run_data(
    baseline_metadata: dict[str, Any],
    baseline_passes: dict[str, list[dict[str, Any]]],
    experiment_metadata: dict[str, Any],
    experiment_passes: dict[str, list[dict[str, Any]]],
    source_reader: Callable[[str, str], str] | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable comparison from two saved run datasets."""

    baseline_sha = baseline_metadata.get("pinned_sha")
    experiment_sha = experiment_metadata.get("pinned_sha")
    if not isinstance(baseline_sha, str) or not baseline_sha:
        raise ValueError("Baseline report is missing pinned_sha")
    if baseline_sha != experiment_sha:
        raise ValueError("Cannot compare runs with different pinned_sha values")
    combined_passes = {
        pass_name: baseline_passes.get(pass_name, [])
        + experiment_passes.get(pass_name, [])
        for pass_name in set(baseline_passes) | set(experiment_passes)
    }
    sources = _prepare_sources(
        baseline_sha,
        combined_passes,
        source_reader or read_pinned_source,
    )
    baseline_metrics = {
        name: _summary(records, sources) for name, records in baseline_passes.items()
    }
    experiment_metrics = {
        name: _summary(records, sources)
        for name, records in experiment_passes.items()
    }
    first_pass = "pass-1" if "pass-1" in baseline_passes else next(iter(baseline_passes))
    paired = _paired_questions(
        baseline_passes[first_pass],
        experiment_passes.get(first_pass, []),
        sources,
    )
    return {
        "baseline_run_id": baseline_metadata.get("run_id"),
        "experiment_run_id": experiment_metadata.get("run_id"),
        "pinned_sha": baseline_sha,
        "paired_questions_pass_1": paired,
        "metrics_by_pass": {
            "baseline": baseline_metrics,
            "experiment": experiment_metrics,
        },
        "outcome_v2_changes": _outcome_changes(baseline_passes, experiment_passes),
        "gates": _gates(
            paired,
            baseline_metrics,
            experiment_metrics,
            baseline_passes[first_pass],
            experiment_passes.get(first_pass, []),
        ),
    }


def compare_runs(
    baseline_dir: Path,
    experiment_dir: Path,
    source_reader: Callable[[str, str], str] | None = None,
) -> dict[str, Any]:
    baseline_metadata, baseline_passes = load_run(baseline_dir)
    experiment_metadata, experiment_passes = load_run(experiment_dir)
    return compare_run_data(
        baseline_metadata,
        baseline_passes,
        experiment_metadata,
        experiment_passes,
        source_reader=source_reader,
    )


def _under_runs_root(path: Path) -> Path:
    resolved = path.resolve()
    root = RUNS_ROOT.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"Run folder must be under {root}: {path}")
    if not resolved.is_dir():
        raise ValueError(f"Run folder does not exist: {resolved}")
    return resolved


def format_report(report: dict[str, Any]) -> str:
    """Render the paired table, summaries, changes, and gate evidence."""

    lines = [
        f"Baseline: {report['baseline_run_id']}",
        f"Experiment: {report['experiment_run_id']}",
        f"Pinned SHA: {report['pinned_sha']}",
        "",
        "Pass-1 answerable paired retrieval (rank and hit indicators):",
        "id | baseline rank | experiment rank | baseline @1/@3/@5 | "
        "experiment @1/@3/@5 | file baseline/experiment | "
        "function baseline/experiment | gained | lost",
    ]
    for row in report["paired_questions_pass_1"]:
        base_hits = row["baseline_hits"]
        exp_hits = row["experiment_hits"]
        lines.append(
            f"{row['id']} | {row['baseline_labeled_rank']} | "
            f"{row['experiment_labeled_rank']} | "
            f"{int(base_hits['hit_at_1'])}/{int(base_hits['hit_at_3'])}/"
            f"{int(base_hits['hit_at_5'])} | "
            f"{int(exp_hits['hit_at_1'])}/{int(exp_hits['hit_at_3'])}/"
            f"{int(exp_hits['hit_at_5'])} | "
            f"{_display_hit(row['baseline_hit_by_file'])}/"
            f"{_display_hit(row['experiment_hit_by_file'])} | "
            f"{_display_hit(row['baseline_hit_by_function'])}/"
            f"{_display_hit(row['experiment_hit_by_function'])} | "
            f"{','.join(row['gained_hits']) or '-'} | "
            f"{','.join(row['lost_hits']) or '-'}"
        )
    lines.append("")
    for pass_name in PASS_NAMES:
        lines.append(f"{pass_name} metrics:")
        for arm in ("baseline", "experiment"):
            metrics = report["metrics_by_pass"][arm].get(pass_name)
            if metrics is None:
                continue
            lines.append(
                f"  {arm}: overall={metrics['overall']}; "
                f"by_category={metrics['by_category']}; "
                f"by_label_file_type={metrics['by_label_file_type']}; "
                f"hit_by_file={metrics['hit_by_file']}; "
                f"hit_by_function={metrics['hit_by_function']}; "
                f"top5_median_chars={metrics['top5_context_characters']['median']}; "
                f"top5_chars_per_question={metrics['top5_context_characters']['per_question']}; "
                f"median_tokens={metrics['total_tokens']['median']}; "
                f"tokens_per_question={metrics['total_tokens']['per_question']}; "
                f"guard_false_accepts={metrics['guard_false_accepts']}; "
                f"outcome_v2_counts={metrics['outcome_v2_counts']}"
            )
    lines.append("")
    lines.append("Questions with changed outcome_v2:")
    for change in report["outcome_v2_changes"]:
        lines.append(
            f"  {change['pass']} {change['id']}: "
            f"{change['baseline']} -> {change['experiment']}"
        )
    if not report["outcome_v2_changes"]:
        lines.append("  none")
    lines.append("")
    lines.append("Gate checklist:")
    for gate in report["gates"]:
        lines.append(f"  Gate {gate['gate']}: {gate['status']} — {gate['evidence']}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two saved chunking evaluation runs offline."
    )
    parser.add_argument("baseline_run", type=Path)
    parser.add_argument("experiment_run", type=Path)
    args = parser.parse_args()
    baseline_dir = _under_runs_root(args.baseline_run)
    experiment_dir = _under_runs_root(args.experiment_run)
    report = compare_runs(baseline_dir, experiment_dir)
    output_path = experiment_dir / "chunking-comparison.json"
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(format_report(report))
    print(f"\nJSON report: {output_path}")


if __name__ == "__main__":
    main()
