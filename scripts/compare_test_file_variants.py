"""Run the registered test-file ranking comparison on development fixtures only."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.test_file_comparison import (  # noqa: E402
    compare_development_variants,
    summarize_control_guard,
)
from scripts.diagnose_test_files import collect_diagnostics  # noqa: E402

DEFAULT_OUTPUT = Path("docs/notes/12-test-file-comparison-results.md")
PROTOCOL_COMMIT = "8c411e2fd1ed549dd3c4af393e98ea344cc05169"


def _rate(value: float | None) -> str:
    return "not evaluable" if value is None else f"{value:.6f}"


def _hits(successes: int, total: int) -> str:
    return f"{successes}/{total}"


def _validate_reconciled_control(repositories: list[dict[str, Any]]) -> None:
    total_answerable = 0
    total_questions = 0
    for repository in repositories:
        data = repository["_comparison_data"]
        questions = data["questions"]
        answerable_count = sum(
            question.get("category") in {"direct", "paraphrased"}
            for question in questions
        )
        reconciliation = repository["control_reconciliation"]
        if (
            len(questions) != 16
            or answerable_count != 11
            or reconciliation["questions_compared"] != 11
            or reconciliation["identical_rank_count"] != 11
            or reconciliation["differing_ranks"]
        ):
            raise ValueError("The control failed development baseline reconciliation")
        total_questions += len(questions)
        total_answerable += answerable_count
    if total_questions != 48 or total_answerable != 33:
        raise ValueError("The selected development split has unexpected dimensions")


def render_results(
    repositories: list[dict[str, Any]],
    comparison: dict[str, Any],
) -> str:
    """Render only aggregate metrics and development ordinals, never question IDs."""

    lines = [
        "# Test-file retrieval comparison results",
        "",
        "## Registration and method",
        "",
        "Protocol: [11-test-file-retrieval-protocol.md]"
        "(../architecture-review/11-test-file-retrieval-protocol.md).",
        f"Protocol commit: `{PROTOCOL_COMMIT}`.",
        "Only the 16 development questions per repository were selected through the existing "
        "development split helper. Before any variant ran, the control was checked against "
        "the committed development `label_rank`: all 33 answerable ranks matched.",
        "",
        "The control candidate pool is the full union of the production vector and full-text "
        "branch top fives (up to ten fused candidates). V1 and V2 are applied before the final "
        "top-five cut. The production evidence guard is applied unchanged to each resulting "
        "top five. No provider calls or production retrieval changes were made.",
        "",
        "## Preregistered ambiguity readings",
        "",
        "- Control candidate depth is the union of the two production top-five branch lists; "
        "this preserves the complete fused candidate pool for reranking.",
        "- Guard improvement/regression follows the protocol: sufficient to insufficient is an "
        "improvement; insufficient to sufficient is a regression.",
        "- R5 has a zero test-evidence denominator. It is not evaluable, and therefore is neither "
        "a pass nor a failure; it cannot satisfy the retention rule. V2 additionally requires "
        "R6, for which no separate registered stratum exists.",
        "- Paired bootstrap percentiles use linear interpolation; the exact sign test excludes "
        "tied per-question reciprocal-rank differences.",
        "",
        "## Per-repository and pooled metrics",
        "",
        "Hit@k entries are successes over answerable questions. Test share uses all development "
        "questions' top-five results. Test precision is overlapping labeled test-file spans "
        "over answerable top-five test chunks. Test-source recall is not evaluable when its "
        "development evidence denominator is zero.",
        "",
        "| Scope | Method | Answerable | Hit@1 | Hit@3 | Hit@5 | MRR | Span MRR | "
        "Test top-five share | Test-source recall (hits/denominator) | "
        "Test precision (overlaps/chunks) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    scopes: list[tuple[str, dict[str, dict[str, Any]]]] = [
        (name, metrics)
        for name, metrics in comparison["per_repository"].items()
    ]
    scopes.append(("Pooled", comparison["pooled"]))
    for scope, methods in scopes:
        for method in ("control", "V1", "V2"):
            metrics = methods[method]
            source_hits = metrics["test_source_recall_hits"]
            source_denominator = metrics["test_source_recall_denominator"]
            source_text = (
                "not available"
                if source_denominator is None
                else (
                    "not evaluable (0 denominator)"
                    if source_denominator == 0
                    else f"{source_hits}/{source_denominator} "
                    f"({_rate(metrics['test_source_recall'])})"
                )
            )
            precision_denominator = metrics["answerable_test_top5_chunks"]
            precision_text = (
                "not evaluable (0 chunks)"
                if precision_denominator == 0
                else f"{metrics['test_precision_overlaps']}/{precision_denominator} "
                f"({_rate(metrics['test_precision'])})"
            )
            lines.append(
                f"| {scope} | {method} | {metrics['answerable_questions']} | "
                f"{metrics['hit_at_1_successes']} | {metrics['hit_at_3_successes']} | "
                f"{metrics['hit_at_5_successes']} | {metrics['mrr']:.6f} | "
                f"{_rate(metrics['spans_mrr'])} | "
                f"{metrics['test_top5_chunks']}/{metrics['top5_chunks']} "
                f"({_rate(metrics['test_top5_share'])}) | {source_text} | "
                f"{precision_text} |"
            )

    lines.extend(
        [
            "",
            "## Paired pooled MRR statistics",
            "",
            "The difference is variant MRR minus control MRR. Bootstrap uses 10,000 paired "
            "resamples of the 33 answerable questions, seed `20261031`; sign-test results are "
            "descriptive only.",
            "",
            "| Variant | MRR difference | 95% paired bootstrap percentile interval | "
            "Sign test positive / negative / ties | Exact two-sided p-value |",
            "|---|---:|---|---|---:|",
        ]
    )
    for variant in ("V1", "V2"):
        statistics = comparison["bootstrap"][variant]
        low, high = statistics["bootstrap_95_percentile_interval"]
        sign = statistics["sign_test"]
        lines.append(
            f"| {variant} | {statistics['mrr_difference']:.6f} | "
            f"[{low:.6f}, {high:.6f}] | {sign['positive']} / {sign['negative']} / "
            f"{sign['ties']} | {sign['two_sided_p_value']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Evidence-guard comparison",
            "",
            "The committed baseline stores no guard decision. The guard control below is the "
            "production `evaluate_evidence_sufficiency` function applied to each reconciled "
            "control top five; the same function and threshold are used for both variants. "
            "A top five is sufficient when at least one result has vector cosine distance "
            "at or below the unchanged provisional threshold `0.5`; RRF is not the guard "
            "threshold.",
            "",
            "| Repository | Control sufficient / insufficient | Variant | Unanswerable "
            "questions | Unchanged | Improved | Regressed | Changed development ordinals |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for repository in repositories:
        name = repository["repository"]
        data = repository["_comparison_data"]
        control_counts = summarize_control_guard(
            data["questions"], data["control_rankings"]
        )
        control_text = (
            f"{control_counts['sufficient']} / {control_counts['insufficient']}"
        )
        for variant in ("V1", "V2"):
            guard = comparison["guard_comparisons"][variant][name]
            changed = ", ".join(
                str(ordinal)
                for ordinal in guard["changed_development_ordinals"]
            ) or "none"
            lines.append(
                f"| {name} | {control_text} | {variant} | "
                f"{guard['unanswerable_questions']} | {guard['unchanged']} | "
                f"{guard['improved']} | {guard['regressed']} | {changed} |"
            )

    lines.extend(
        [
            "",
            "## Decision rules",
            "",
            "A rule status of not-evaluable is not treated as a pass or a failure. Since all "
            "required conditions must hold, R5 cannot authorize retention on this development "
            "set when its denominator is zero.",
            "",
            "| Variant | R1 | R2 | R3 | R4 | R5 | R6 | Passes all required rules |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for variant in ("V1", "V2"):
        rules = comparison["rules"][variant]
        lines.append(
            f"| {variant} | "
            + " | ".join(rules["rules"][rule] for rule in ("R1", "R2", "R3", "R4", "R5", "R6"))
            + f" | {'yes' if rules['passes_all_required_rules'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            f"**Mechanical outcome:** {comparison['decision']}",
            "",
            "R5: not evaluable; labeled test-file evidence denominator is "
            f"{comparison['pooled_test_source_recall_denominator']}. "
            "R6: V2 is report-only because no separately registered test-evidence stratum "
            "exists.",
            "",
            "## Limits",
            "",
            "This comparison covers 33 answerable and 15 unanswerable development questions "
            "across three small repositories. The development set contains no answerable "
            "questions with labeled evidence in test files, so test-source recall has a zero "
            "denominator and removal-style policies cannot be penalized by this set. One rank "
            "change is about 0.015 pooled MRR. The guard threshold is provisional. The held-out "
            "split was untouched. Results are not generalizable beyond these repositories.",
            "",
        ]
    )
    return "\n".join(lines)


async def run_comparison(output_path: Path, json_path: Path) -> None:
    repositories = await collect_diagnostics(include_comparison_data=True)
    _validate_reconciled_control(repositories)
    comparison = compare_development_variants(repositories)
    rendered = render_results(repositories, comparison)
    serialized = {
        "protocol_commit": PROTOCOL_COMMIT,
        "development_only": True,
        "pooled": comparison["pooled"],
        "per_repository": comparison["per_repository"],
        "bootstrap": comparison["bootstrap"],
        "guard_comparisons": comparison["guard_comparisons"],
        "pooled_test_source_recall_denominator": (
            comparison["pooled_test_source_recall_denominator"]
        ),
        "pooled_test_source_recall_hits": (
            comparison["pooled_test_source_recall_hits"]
        ),
        "rules": comparison["rules"],
        "decision": comparison["decision"],
    }
    resolved_output = ROOT / output_path
    resolved_json = ROOT / json_path
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_json.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(rendered, encoding="utf-8")
    resolved_json.write_text(
        json.dumps(serialized, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Wrote the development-only comparison note and metrics JSON.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        metavar="PATH",
        help=f"write the results note (default: {DEFAULT_OUTPUT.as_posix()})",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_OUTPUT.with_suffix(".json"),
        metavar="PATH",
        help="write the machine-readable aggregate results JSON",
    )
    args = parser.parse_args()
    try:
        asyncio.run(run_comparison(args.output, args.json_output))
    except (OSError, SQLAlchemyError, ValueError, KeyError, TypeError):
        print(
            "Comparison failed before results were written; no question data was printed.",
            file=sys.stderr,
        )
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
