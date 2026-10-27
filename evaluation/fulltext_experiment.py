"""Execute and render the item 14c-2 development-only full-text ablation."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import AsyncSessionLocal as SessionFactory
from evaluation.build_fixture import load_fixture
from evaluation.chunking_experiment import discover_sources
from evaluation.fulltext_ablation import (
    ANSWERABLE_CATEGORIES,
    BOOTSTRAP_PROTOCOL,
    DECISION_THRESHOLDS,
    EXPERIMENT_ROOT,
    PROTOCOL_REFERENCE,
    decide_variant,
    paired_comparison,
    run_c3_equivalence,
    summarize_variant,
    unique_source_characters,
)
from evaluation.golden import load_golden_set
from evaluation.manifest import load_manifest, questions_for_split
from evaluation.retrieval_eval import run_offline_retrieval

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "evaluation" / "_snapshot" / "chunking-sources"
VARIANTS = ("control", "c1", "c2")


def _source_line_map(repo_id: str) -> dict[tuple[str, int], str]:
    source_root = SOURCE_ROOT / repo_id
    exclusions = ("tests/fixtures/",) if repo_id == "incidentweave" else ()
    sources = discover_sources(source_root, exclude_prefixes=exclusions)
    return {
        (file_path, line_number): line
        for file_path, content in sources.items()
        for line_number, line in enumerate(content.splitlines(), start=1)
    }


def _dev_answerable_ids(
    entry: dict[str, Any],
    questions: list[dict[str, Any]],
) -> set[str]:
    return {
        str(question["id"])
        for question in questions_for_split(entry, questions, "development")
        if question.get("category") in ANSWERABLE_CATEGORIES
    }


def _assert_control_matches_baseline(
    entry: dict[str, Any],
    report: dict[str, Any],
    root: Path,
) -> None:
    baseline_path = root / entry["full_baseline"]["path"]
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    golden_path = root / entry["questions"]["path"]
    golden = load_golden_set(golden_path)
    development_ids = _dev_answerable_ids(entry, golden["questions"])
    expected = {
        row["id"]: row
        for row in baseline["questions"]
        if row["id"] in development_ids
    }
    actual = {
        row["id"]: row
        for row in report["questions"]
        if row["category"] in ANSWERABLE_CATEGORIES
    }
    fields = ("label_rank", "span_rank", "label_hits", "span_hits")
    differences = [
        {
            "question_id": question_id,
            "fields": {
                field: {
                    "baseline": expected.get(question_id, {}).get(field),
                    "control": actual.get(question_id, {}).get(field),
                }
                for field in fields
                if expected.get(question_id, {}).get(field)
                != actual.get(question_id, {}).get(field)
            },
        }
        for question_id in sorted(development_ids)
    ]
    differences = [row for row in differences if row["fields"]]
    if set(expected) != development_ids or set(actual) != development_ids or differences:
        raise RuntimeError(
            f"Control differs from committed development baseline for "
            f"{entry['id']}: {differences[:5]}"
        )


def _variant_report(
    repo_reports: dict[str, dict[str, Any]],
    source_lines_by_repo: dict[str, dict[tuple[str, int], str]],
) -> dict[str, Any]:
    repositories: dict[str, Any] = {}
    pooled_questions: list[dict[str, Any]] = []
    for repo_id in sorted(repo_reports):
        answerable = [
            dict(row)
            for row in repo_reports[repo_id]["questions"]
            if row["category"] in ANSWERABLE_CATEGORIES
        ]
        for row in answerable:
            row["raw_source_characters"] = unique_source_characters(
                row.get("retrieved", []),
                source_lines_by_repo[repo_id],
            )
        answerable.sort(key=lambda row: row["id"])
        summary = summarize_variant(answerable, source_lines_by_repo[repo_id])
        repositories[repo_id] = {
            "question_ids": [row["id"] for row in answerable],
            "summary": summary,
            "questions": [
                {
                    "id": row["id"],
                    "category": row["category"],
                    "span_rank": row["span_rank"],
                    "text_branch_nonempty": row["text_branch_nonempty"],
                    "query_token_count": row.get("query_token_count"),
                    "query_truncated": row.get("query_truncated", False),
                    "raw_source_characters_top5": row["raw_source_characters"],
                }
                for row in answerable
            ],
        }
        pooled_questions.extend(
            {
                **row,
                "id": f"{repo_id}:{row['id']}",
            }
            for row in answerable
        )
    pooled_questions.sort(key=lambda row: row["id"])
    pooled_summary = summarize_variant(pooled_questions, {})
    return {
        "repositories": repositories,
        "pooled": {
            "question_ids": [row["id"] for row in pooled_questions],
            "summary": pooled_summary,
        },
    }


def _comparison(
    candidate: dict[str, Any],
    comparator: dict[str, Any],
) -> dict[str, Any]:
    per_repository = {}
    for repo_id in sorted(candidate["repositories"]):
        per_repository[repo_id] = paired_comparison(
            candidate["repositories"][repo_id],
            comparator["repositories"][repo_id],
            BOOTSTRAP_PROTOCOL,
        )
    per_repository["pooled"] = paired_comparison(
        candidate["pooled"],
        comparator["pooled"],
        BOOTSTRAP_PROTOCOL,
    )
    return per_repository


def _answerable_report_rows(
    report: dict[str, Any],
    entry: dict[str, Any],
    root: Path,
) -> list[dict[str, Any]]:
    golden = load_golden_set(root / entry["questions"]["path"])
    ids = _dev_answerable_ids(entry, golden["questions"])
    return [
        row
        for row in report["questions"]
        if row["id"] in ids
    ]


def _render_report(results: dict[str, Any]) -> str:
    repository_order = sorted(results["metadata"]["repositories"])
    lines = [
        "# Full-text ablation results (item 14c-2)",
        "",
        "## Method",
        "",
        "The control and c1/c2 runs use the committed S0 fixtures, cached query "
        "embeddings, the local PostgreSQL database, and development questions only. "
        "Before any variant ran, every answerable control question rank and hit outcome "
        "was checked against the committed baseline. No embedding or provider API was "
        "called. c1 stop words came from `ts_debug('english', :term)`; questions and "
        "query text were always passed as bound parameters. c2 appends split identifiers "
        "from chunk content only; file paths are not searchable text.",
        "",
        "The comparison column is read sequentially: c1 versus control, then c2 versus "
        "c1. The registered four-condition decision rule is nevertheless applied to each "
        "quality candidate versus the fixed control, exactly as the protocol's rule says. "
        "The additional c2-versus-control comparison is reported to make that decision "
        "auditable. Bootstrap and exact sign-test results use paired per-question span "
        "reciprocal ranks.",
        "",
        "## Development results",
        "",
        "| Variant | Repository | N | Hit@1 success/rate | Hit@3 success/rate | "
        "Hit@5 success/rate | Span MRR | "
        "Non-empty text branch | Top-5 from tests/ | Mean raw chars | P95 raw chars |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in VARIANTS:
        variant_results = results["variants"][variant]
        for repo_id in [*repository_order, "pooled"]:
            summary = (
                variant_results["pooled"]["summary"]
                if repo_id == "pooled"
                else variant_results["repositories"][repo_id]["summary"]
            )
            hit_cells = [
                f'{summary[f"hit_at_{k}"]["successes"]}/'
                f'{summary["question_count"]} '
                f'({summary[f"hit_at_{k}"]["rate"]:.3f})'
                for k in (1, 3, 5)
            ]
            lines.append(
                f"| {variant} | {repo_id} | {summary['question_count']} | "
                f"{hit_cells[0]} | {hit_cells[1]} | {hit_cells[2]} | "
                f"{summary['span_mrr']:.4f} | "
                f"{summary['nonempty_text_branch']['questions']}/"
                f"{summary['question_count']} "
                f"({summary['nonempty_text_branch']['share']:.3f}) | "
                f"{summary['top5_tests']['results']}/"
                f"{summary['top5_tests']['retrieved_results']} "
                f"({summary['top5_tests']['share']:.3f}) | "
                f"{summary['top5_unique_raw_source_characters']['mean']:.1f} | "
                f"{summary['top5_unique_raw_source_characters']['p95_nearest_rank']} |"
            )
    lines.extend(
        [
            "",
            "Hit@k cells show successes/question count; MRR is span-based. Test-file "
            "share is the number of retrieved top-five chunks under `tests/` divided by "
            "all returned top-five chunks. Context cost unions overlapping file-line "
            "ranges and sums `len(line) + 1` from the pinned local source snapshot.",
            "",
        ]
    )
    lines.extend(
        [
            "## Query-cap truncation",
            "",
            "| Variant | Repository | Truncated development queries |",
            "|---|---|---:|",
        ]
    )
    for variant in ("c1", "c2"):
        variant_repositories = results["variants"][variant]["repositories"]
        for repo_id in repository_order:
            repo_result = variant_repositories[repo_id]
            lines.append(
                f"| {variant} | {repo_id} | "
                f"{repo_result['query_truncation_count']}/16 |"
            )
    lines.extend(
        [
            "",
            "## Paired comparisons",
            "",
            "| Pair | Repository | Delta span MRR | 95% paired bootstrap CI | "
            "Wins / losses / ties | Exact sign-test p (descriptive) |",
            "|---|---|---:|---|---:|---:|",
        ]
    )
    for pair_name, comparisons in results["comparisons"].items():
        for repo_id, comparison in comparisons.items():
            low, high = comparison["bootstrap_interval"]
            lines.append(
                f"| {pair_name} | {repo_id} | {comparison['delta_mrr']:+.4f} | "
                f"[{low:+.4f}, {high:+.4f}] | "
                f"{comparison['wins']} / {comparison['losses']} / "
                f"{comparison['ties']} | {comparison['sign_test_p_value']:.6f} |"
            )
    lines.extend(
        [
            "",
            "## Registered decision rule",
            "",
            "| Candidate | Hit@5 loss <= 1/repo | Span MRR loss <= 0.03/repo | "
            "Pooled delta MRR >= +0.02 | Text branch share increases | "
            "Qualifies to advance? |",
            "|---|---|---|---|---|---|",
        ]
    )
    for variant in ("c1", "c2"):
        decision = results["decisions"][variant]
        conditions = decision["conditions"]
        lines.append(
            f"| {variant} | "
            f"{'pass' if conditions['no_repository_loses_more_than_one_hit_at_5'] else 'fail'} | "
            f"{'pass' if conditions['no_repository_loses_more_than_0_03_span_mrr'] else 'fail'} | "
            f"{'pass' if conditions['pooled_span_mrr_delta_at_least_0_02'] else 'fail'} | "
            f"{'pass' if conditions['nonempty_text_branch_share_larger'] else 'fail'} | "
            f"{'yes' if decision['qualifies'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "The rule is mechanical; a quality variant must pass all four conditions. "
            "No variant is adopted in item 14c-2. Item 14c-3 is the adoption step.",
            "",
            "## c3 generated-vector equivalence and timing",
            "",
            "Each repository was loaded into a temporary PostgreSQL table with a generated "
            "`tsvector` column and a temporary GIN index. Query-time and generated-vector "
            "matching chunk IDs were compared for every development question.",
            "",
            "| Repository | Chunks | Development questions | Equivalent | "
            "Query-time median/p95 ms | Generated-vector median/p95 ms | "
            "Generated index used |",
            "|---|---:|---:|---|---:|---:|---:|",
        ]
    )
    for repo_id in results["metadata"]["repositories"]:
        row = results["c3"]["repositories"][repo_id]
        lines.append(
            f"| {repo_id} | {row['chunk_count']} | {row['question_count']} | "
            f"{row['all_questions_equivalent']} | "
            f"{row['query_time_execution_ms_median']:.4f} / "
            f"{row['query_time_execution_ms_p95_nearest_rank']:.4f} | "
            f"{row['generated_vector_execution_ms_median']:.4f} / "
            f"{row['generated_vector_execution_ms_p95_nearest_rank']:.4f} | "
            f"{row['generated_vector_index_used_questions']}/"
            f"{row['question_count']} |"
        )
    lines.extend(
        [
            "",
            "Timing is descriptive only: these fixtures contain only 38–70 chunks per "
            "repository, so the timings are too small and noise-sensitive to support a "
            "performance claim. c3 has no quality claim and does not qualify as a winner.",
            "",
            "## Honest limits",
            "",
            "The quality sample is 33 development answerable questions across three tiny, "
            "single-author repositories. It does not establish transfer to other repositories "
            "or query distributions. Held-out data was not used. c1 and c2 are opt-in "
            "evaluation variants only; production defaults, baselines, gates, manifest, and "
            "the registered protocol remain unchanged.",
            "",
            "Protocol: [item 14 retrieval ablation](../../../docs/architecture-review/"
            "08-retrieval-ablation-protocol.md).",
            "",
        ]
    )
    return "\n".join(lines)


async def run_fulltext_experiment(
    *,
    root: Path = ROOT,
    output_dir: Path = EXPERIMENT_ROOT,
) -> dict[str, Any]:
    """Run control, c1, c2, then c3 without provider calls."""

    manifest = load_manifest(root / "evaluation" / "manifest.json", root=root)
    entries = manifest["repositories"]
    source_lines_by_repo = {
        str(entry["id"]): _source_line_map(str(entry["id"]))
        for entry in entries
    }
    raw_reports: dict[str, dict[str, dict[str, Any]]] = {
        variant: {} for variant in VARIANTS
    }

    for entry in entries:
        repo_id = str(entry["id"])
        raw_reports["control"][repo_id] = await run_offline_retrieval(
            repo_id=repo_id,
            split="development",
            entry=entry,
            root=root,
            record_details=True,
            record_variant_details=True,
        )
        _assert_control_matches_baseline(entry, raw_reports["control"][repo_id], root)

    for variant in ("c1", "c2"):
        for entry in entries:
            repo_id = str(entry["id"])
            raw_reports[variant][repo_id] = await run_offline_retrieval(
                repo_id=repo_id,
                split="development",
                entry=entry,
                root=root,
                record_details=True,
                record_variant_details=True,
                variant=variant,
            )

    summaries = {
        variant: _variant_report(raw_reports[variant], source_lines_by_repo)
        for variant in VARIANTS
    }
    for variant in VARIANTS:
        for repo_id, report in raw_reports[variant].items():
            answerable_rows = _answerable_report_rows(
                report,
                next(entry for entry in entries if entry["id"] == repo_id),
                root,
            )
            summaries[variant]["repositories"][repo_id]["questions"] = [
                question
                for question in summaries[variant]["repositories"][repo_id]["questions"]
            ]
            truncation_rows = [
                row for row in report["questions"] if row.get("query_truncated")
            ]
            summaries[variant]["repositories"][repo_id][
                "query_truncation_count"
            ] = len(truncation_rows)
            summaries[variant]["repositories"][repo_id][
                "query_truncated_question_ids"
            ] = [row["id"] for row in truncation_rows]
            if variant == "control":
                continue
            if not all(
                "text_branch_nonempty" in row for row in answerable_rows
            ):
                raise RuntimeError(
                    f"Text branch results were not recorded for {variant}/{repo_id}"
                )

    comparisons = {
        "c1_vs_control": _comparison(summaries["c1"], summaries["control"]),
        "c2_vs_c1": _comparison(summaries["c2"], summaries["c1"]),
        "c2_vs_control": _comparison(summaries["c2"], summaries["control"]),
    }
    decisions = {
        variant: decide_variant(summaries[variant], summaries["control"])
        for variant in ("c1", "c2")
    }

    c3_results = {}
    for entry in entries:
        repo_id = str(entry["id"])
        fixture = load_fixture(root / entry["fixture"]["path"])
        golden = load_golden_set(root / entry["questions"]["path"])
        dev_questions = questions_for_split(
            entry, golden["questions"], "development"
        )
        async with SessionFactory() as session:
            c3_results[repo_id] = await run_c3_equivalence(
                session,
                fixture["chunks"],
                dev_questions,
            )

    pooled_control = summaries["control"]["pooled"]["summary"]
    results: dict[str, Any] = {
        "metadata": {
            "protocol": PROTOCOL_REFERENCE,
            "split": "development",
            "repositories": [str(entry["id"]) for entry in entries],
            "answerable_question_count": pooled_control["question_count"],
            "control_baseline_check": "passed per question for all repositories",
            "bootstrap_seed": 20261026,
            "bootstrap_resamples": 10000,
            "bootstrap_interval": 0.95,
            "searchable_text_version": "identifier-split-v1",
            "decision_rule": DECISION_THRESHOLDS,
            "adoption": "none; item 14c-3 adopts only after a separate decision",
        },
        "variants": summaries,
        "comparisons": comparisons,
        "decisions": decisions,
        "c3": {
            "repositories": c3_results,
            "all_questions_equivalent": all(
                row["all_questions_equivalent"] for row in c3_results.values()
            ),
            "quality_claim": False,
        },
    }
    if pooled_control["question_count"] != 33:
        raise RuntimeError(
            f"Expected 33 development answerable questions, got "
            f"{pooled_control['question_count']}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "report.md").write_text(
        _render_report(results),
        encoding="utf-8",
        newline="\n",
    )
    return results


def _report_summary(results: dict[str, Any]) -> list[str]:
    lines = ["Variant Repository Hit@1 Hit@3 Hit@5 Span-MRR Text-branch"]
    for variant in VARIANTS:
        variant_results = results["variants"][variant]
        for repo_id in [*sorted(variant_results["repositories"]), "pooled"]:
            summary = (
                variant_results["pooled"]["summary"]
                if repo_id == "pooled"
                else variant_results["repositories"][repo_id]["summary"]
            )
            lines.append(
                f"{variant} {repo_id} "
                f"{summary['hit_at_1']['successes']}/{summary['question_count']}"
                f"({summary['hit_at_1']['rate']:.3f}) "
                f"{summary['hit_at_3']['successes']}/{summary['question_count']}"
                f"({summary['hit_at_3']['rate']:.3f}) "
                f"{summary['hit_at_5']['successes']}/{summary['question_count']}"
                f"({summary['hit_at_5']['rate']:.3f}) "
                f"{summary['span_mrr']:.4f} "
                f"{summary['nonempty_text_branch']['questions']}/{summary['question_count']}"
            )
    return lines


def main() -> int:
    try:
        results = asyncio.run(run_fulltext_experiment())
    except (OSError, ValueError, RuntimeError, SQLAlchemyError) as exc:
        print(f"Error: {exc}")
        return 2
    print(f"Results: {EXPERIMENT_ROOT / 'results.json'}")
    print(f"Report: {EXPERIMENT_ROOT / 'report.md'}")
    print("\n".join(_report_summary(results)))
    for variant, decision in results["decisions"].items():
        print(f"{variant} decision: {decision['decision']}")
    print(
        "c3 equivalence:",
        "passed" if results["c3"]["all_questions_equivalent"] else "failed",
    )
    return 0
