"""Run the registered BM25 comparison against development fixtures only."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.investigation.guard import evaluate_evidence_sufficiency  # noqa: E402
from evaluation.bm25 import TOP_K, BM25Index, decide_b1  # noqa: E402
from evaluation.build_fixture import load_fixture  # noqa: E402
from evaluation.fulltext_ablation import build_protocol_query  # noqa: E402
from evaluation.fulltext_experiment import _assert_control_matches_baseline  # noqa: E402
from evaluation.manifest import load_manifest  # noqa: E402
from evaluation.metrics import first_relevant_rank, first_relevant_span_rank  # noqa: E402
from evaluation.test_file_comparison import (  # noqa: E402
    paired_mrr_statistics,
    summarize_control_guard,
    summarize_method,
)
from evaluation.test_file_variants import control_top_five  # noqa: E402
from scripts.diagnose_test_files import collect_diagnostics  # noqa: E402

PROTOCOL_PATH = "docs/architecture-review/12-bm25-comparison-protocol.md"
PROTOCOL_COMMIT = "a47e6fc0c981f28530a89c710bda12371f9d30e1"
NOTE_PATH = ROOT / "docs" / "notes" / "17-bm25-comparison-results.md"
REPORT_PATH = ROOT / "evaluation" / "experiments" / "bm25" / "results.json"
LEXICAL_SQL = text(
    """
    WITH fixture_chunks AS (
        SELECT *
        FROM jsonb_to_recordset(CAST(:fixture_chunks AS jsonb)) AS chunk(
            id integer,
            file_path text,
            line_start integer,
            line_end integer,
            content text
        )
    )
    SELECT
        id, file_path, line_start, line_end, content,
        ts_rank_cd(
            to_tsvector('english', content),
            websearch_to_tsquery(:query_text)
        ) AS score
    FROM fixture_chunks
    WHERE to_tsvector('english', content)
          @@ websearch_to_tsquery(:query_text)
    ORDER BY score DESC, file_path, line_start, line_end
    LIMIT :limit
    """
)


def _chunk_keys(chunks: list[dict[str, Any]]) -> dict[tuple[str, int, int, str], int]:
    keys: dict[tuple[str, int, int, str], int] = {}
    for index, chunk in enumerate(chunks, start=1):
        key = (
            str(chunk["file_path"]),
            int(chunk["line_start"]),
            int(chunk["line_end"]),
            str(chunk["content"]),
        )
        if key in keys:
            raise ValueError("Fixture chunk coordinates and content must be unique")
        keys[key] = index
    return keys


def _attach_ids(
    results: list[dict[str, Any]],
    chunk_ids: dict[tuple[str, int, int, str], int],
) -> list[dict[str, Any]]:
    attached = []
    for result in results:
        key = (
            str(result["file_path"]),
            int(result["line_start"]),
            int(result["line_end"]),
            str(result["content"]),
        )
        attached.append({**result, "id": chunk_ids[key]})
    return attached


def _fuse(
    vector_results: list[dict[str, Any]],
    lexical_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    vector = {int(row["id"]): (rank, row) for rank, row in enumerate(vector_results, 1)}
    lexical = {
        int(row["id"]): (rank, row) for rank, row in enumerate(lexical_results, 1)
    }
    fused = []
    for chunk_id in vector.keys() | lexical.keys():
        vector_pair = vector.get(chunk_id)
        lexical_pair = lexical.get(chunk_id)
        row = (vector_pair or lexical_pair)[1]
        vector_rank = vector_pair[0] if vector_pair else None
        lexical_rank = lexical_pair[0] if lexical_pair else None
        fused.append(
            {
                **row,
                "id": chunk_id,
                "vector_score": (
                    vector_pair[1].get("vector_score") if vector_pair else None
                ),
                "fts_score": lexical_pair[1].get("score") if lexical_pair else None,
                "vector_rank": vector_rank,
                "fulltext_rank": lexical_rank,
                "rrf_score": (
                    (1 / (60 + vector_rank) if vector_rank else 0.0)
                    + (1 / (60 + lexical_rank) if lexical_rank else 0.0)
                ),
            }
        )
    fused.sort(
        key=lambda row: (
            -float(row["rrf_score"]),
            int(row["vector_rank"]) if row["vector_rank"] is not None else float("inf"),
            (
                int(row["fulltext_rank"])
                if row["fulltext_rank"] is not None
                else float("inf")
            ),
            str(row["file_path"]),
            int(row["line_start"]),
            int(row["line_end"]),
        )
    )
    return fused[:TOP_K]


def _baseline_rows(
    questions: list[dict[str, Any]],
    rankings: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    for question in questions:
        question_id = str(question["id"])
        results = rankings[question_id][:TOP_K]
        label_rank = first_relevant_rank(results, question.get("relevant", []))
        span_rank = first_relevant_span_rank(
            results, question.get("relevant_spans", [])
        )
        rows.append(
            {
                "id": question_id,
                "category": question["category"],
                "label_rank": label_rank,
                "span_rank": span_rank,
                "label_hits": {
                    str(k): label_rank is not None and label_rank <= k
                    for k in (1, 3, 5)
                },
                "span_hits": {
                    str(k): span_rank is not None and span_rank <= k
                    for k in (1, 3, 5)
                },
            }
        )
    return rows


async def _c1_rankings(
    chunks: list[dict[str, Any]],
    questions: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[float]]:
    fixture_chunks = json.dumps(
        [
            {
                "id": index,
                "file_path": chunk["file_path"],
                "line_start": chunk["line_start"],
                "line_end": chunk["line_end"],
                "content": chunk["content"],
            }
            for index, chunk in enumerate(chunks, start=1)
        ]
    )
    rankings: dict[str, list[dict[str, Any]]] = {}
    query_times: list[float] = []
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET TRANSACTION READ ONLY"))
        for question in questions:
            built = await build_protocol_query(session, str(question["question"]))
            started = time.perf_counter()
            rows = (
                await session.execute(
                    LEXICAL_SQL,
                    {
                        "fixture_chunks": fixture_chunks,
                        "query_text": built.query_text,
                        "limit": TOP_K,
                    },
                )
            ).mappings().all()
            query_times.append((time.perf_counter() - started) * 1000)
            rankings[str(question["id"])] = [
                dict(row) for row in rows
            ]
    return rankings, query_times


def _lexical_summary(
    questions: list[dict[str, Any]],
    rankings: dict[str, list[dict[str, Any]]],
) -> dict[str, int | float]:
    answerable = [
        row
        for row in questions
        if row.get("category") in {"direct", "paraphrased"}
    ]
    ranks = [
        first_relevant_rank(
            rankings[str(question["id"])][:TOP_K],
            question.get("relevant", []),
        )
        for question in answerable
    ]
    return {
        f"hit_at_{k}_successes": sum(rank is not None and rank <= k for rank in ranks)
        for k in (1, 3, 5)
    } | {"answerable_questions": len(answerable)}


def _guard_comparison(
    questions: list[dict[str, Any]],
    control: dict[str, list[dict[str, Any]]],
    candidate: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    unchanged = 0
    changed_ordinals: list[int] = []
    ordinal = 0
    for question in questions:
        if question.get("category") in {"direct", "paraphrased"}:
            continue
        ordinal += 1
        question_id = str(question["id"])
        control_answer = evaluate_evidence_sufficiency(
            control[question_id]
        )["is_sufficient"]
        candidate_answer = evaluate_evidence_sufficiency(
            candidate[question_id]
        )["is_sufficient"]
        if not isinstance(control_answer, bool) or not isinstance(candidate_answer, bool):
            raise ValueError("Evidence guard must return boolean decisions")
        if control_answer == candidate_answer:
            unchanged += 1
        else:
            changed_ordinals.append(ordinal)
    return {
        "unanswerable_questions": ordinal,
        "unchanged": unchanged,
        "changed": len(changed_ordinals),
        "changed_development_ordinals": changed_ordinals,
    }


def _public_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "answerable_questions": summary["answerable_questions"],
        "hit_at_1_successes": summary["hit_at_1_successes"],
        "hit_at_3_successes": summary["hit_at_3_successes"],
        "hit_at_5_successes": summary["hit_at_5_successes"],
        "mrr": summary["mrr"],
    }


def _render_note(results: dict[str, Any]) -> str:
    lines = [
        "# BM25 comparison results (item 14d)",
        "",
        "## Protocol and method",
        "",
        f"Protocol: [{PROTOCOL_PATH.rsplit('/', 1)[1]}]"
        "(../architecture-review/12-bm25-comparison-protocol.md).",
        f"Protocol commit: `{PROTOCOL_COMMIT}`.",
        "The comparison used committed S0 fixture chunks and cached query vectors through the "
        "development split helper. Before either lexical variant was evaluated, current hybrid "
        "control retrieval matched the committed baseline for all 33 answerable development "
        "questions, including label and span ranks and hit outcomes. No provider calls or "
        "held-out data were used.",
        "",
        "B1 replaces only the lexical branch with the fixed Python BM25 index (`k1=1.2`, "
        "`b=0.75`), OR token matching, and path/start-line tie breaks. C1 is the sanitized-OR "
        "`ts_rank` reference arm and is descriptive only. Both retain top-k 5 and RRF constant 60.",
        "",
        "## Per-repository and pooled hybrid metrics",
        "",
        "| Scope | Arm | N | Hit@1 | Hit@3 | Hit@5 | MRR |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for scope in [*sorted(results["per_repository"]), "pooled"]:
        methods = (
            results["pooled"]["methods"]
            if scope == "pooled"
            else results["per_repository"][scope]["methods"]
        )
        for arm in ("control", "B1", "C1"):
            metrics = methods[arm]
            count = metrics["answerable_questions"]
            lines.append(
                f"| {scope} | {arm} | {count} | "
                f"{metrics['hit_at_1_successes']}/{count} | "
                f"{metrics['hit_at_3_successes']}/{count} | "
                f"{metrics['hit_at_5_successes']}/{count} | {metrics['mrr']:.6f} |"
            )
    lines.extend(
        [
            "",
            "## Lexical-branch-only hit rates (descriptive)",
            "",
            "| Scope | Arm | N | Hit@1 | Hit@3 | Hit@5 |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for scope in [*sorted(results["per_repository"]), "pooled"]:
        branches = (
            results["pooled"]["lexical_branch"]
            if scope == "pooled"
            else results["per_repository"][scope]["lexical_branch"]
        )
        for arm in ("control", "B1", "C1"):
            metrics = branches[arm]
            count = metrics["answerable_questions"]
            lines.append(
                f"| {scope} | {arm} | {count} | "
                f"{metrics['hit_at_1_successes']}/{count} | "
                f"{metrics['hit_at_3_successes']}/{count} | "
                f"{metrics['hit_at_5_successes']}/{count} |"
            )
    interval = results["pooled"]["statistics"]["bootstrap_95_percentile_interval"]
    sign = results["pooled"]["statistics"]["sign_test"]
    lines.extend(
        [
            "",
            "## Paired pooled statistics and cost",
            "",
            f"B1 minus control MRR: `{results['pooled']['statistics']['mrr_difference']:.6f}`; "
            f"95% paired bootstrap interval: `[{interval[0]:.6f}, {interval[1]:.6f}]` "
            "(seed 20261031, 10,000 resamples).",
            f"Exact sign test (descriptive): {sign['positive']} positive, "
            f"{sign['negative']} negative, {sign['ties']} tied; two-sided "
            f"`p={sign['two_sided_p_value']:.6f}`.",
            "",
            "| Repository | BM25 build ms | BM25 query mean ms | SQL C1 query mean ms |",
            "|---|---:|---:|---:|",
        ]
    )
    for repo_id in sorted(results["per_repository"]):
        cost = results["per_repository"][repo_id]["cost"]
        lines.append(
            f"| {repo_id} | {cost['bm25_index_build_ms']:.3f} | "
            f"{cost['bm25_query_mean_ms']:.3f} | {cost['sql_c1_query_mean_ms']:.3f} |"
        )
    lines.extend(
        [
            "",
            "The exact sign test and timing are descriptive, not decision conditions. SQL timing "
            "covers the C1 `ts_rank` statement after its sanitized query has been constructed; "
            "BM25 query timing excludes index construction.",
            "",
            "## Guard outcomes and registered decision",
            "",
            "| Repository | Unanswerable N | Control sufficient/insufficient | "
            "B1 unchanged | Changed ordinals |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for repo_id in sorted(results["per_repository"]):
        guard = results["per_repository"][repo_id]["guard"]
        changed = ", ".join(map(str, guard["changed_development_ordinals"])) or "none"
        lines.append(
            f"| {repo_id} | {guard['unanswerable_questions']} | "
            f"{guard['control']['sufficient']}/{guard['control']['insufficient']} | "
            f"{guard['unchanged']} | {changed} |"
        )
    lines.extend(
        [
            "",
            "R4 compares every unanswerable development question returned by the registered split "
            "helper. The manifest currently supplies five per repository; this conservatively "
            "checks all of them against the protocol's three-ordinal safety condition.",
            "",
            "| Rule | Condition | Result |",
            "|---|---|---|",
        ]
    )
    descriptions = {
        "R1_pooled_mrr_improves_by_at_least_0_030": (
            "Pooled MRR improves by at least 0.030."
        ),
        "R2_bootstrap_lower_bound_above_zero": (
            "Paired bootstrap 95% interval lower bound is above zero."
        ),
        "R3_no_repository_loses_more_than_one_hit_at_5": (
            "No repository loses more than one Hit@5 success."
        ),
        "R4_unanswerable_guard_outcomes_unchanged": (
            "All unanswerable development guard outcomes are unchanged."
        ),
    }
    for rule, condition in results["decision"]["conditions"].items():
        lines.append(
            f"| {rule.split('_', 1)[0]} | {descriptions[rule]} | "
            f"{'pass' if condition else 'fail'} |"
        )
    lines.extend(
        [
            "",
            f"**Mechanical decision:** {results['decision']['decision']}.",
            "",
            "BM25 is not adopted in this comparison. Production use would require either an "
            "in-app index or a PostgreSQL extension; neither is built here.",
            "",
            "## Honest limits",
            "",
            "The comparison covers 33 answerable development questions from three small "
            "repositories by a single author. It is not evidence of general performance on "
            "other codebases or query distributions. Results are development-only; the "
            "held-out split was untouched.",
            "",
            "Machine-readable aggregate report: "
            "[evaluation/experiments/bm25/results.json]"
            "(../../evaluation/experiments/bm25/results.json).",
            "",
        ]
    )
    return "\n".join(lines)


async def run_comparison() -> dict[str, Any]:
    manifest = load_manifest()
    diagnostics = await collect_diagnostics(include_comparison_data=True)
    entries = {str(entry["id"]): entry for entry in manifest["repositories"]}
    diagnostic_by_repo = {str(row["repository"]): row for row in diagnostics}
    if set(entries) != set(diagnostic_by_repo):
        raise ValueError("Development control did not cover every manifest repository")

    controls: dict[str, dict[str, Any]] = {}
    questions_by_repo: dict[str, list[dict[str, Any]]] = {}
    for repo_id in sorted(entries):
        diagnostic = diagnostic_by_repo[repo_id]
        data = diagnostic["_comparison_data"]
        questions = data["questions"]
        full_rankings = data["control_rankings"]
        reconciliation = diagnostic["control_reconciliation"]
        if (
            reconciliation["questions_compared"] != 11
            or reconciliation["identical_rank_count"] != 11
            or reconciliation["differing_ranks"]
        ):
            raise RuntimeError("Control did not match committed development baseline 33/33")
        controls[repo_id] = {
            question_id: control_top_five(rows)
            for question_id, rows in full_rankings.items()
        }
        questions_by_repo[repo_id] = questions
        _assert_control_matches_baseline(
            entries[repo_id],
            {"questions": _baseline_rows(questions, controls[repo_id])},
            ROOT,
        )
    answerable_total = sum(
        question.get("category") in {"direct", "paraphrased"}
        for questions in questions_by_repo.values()
        for question in questions
    )
    if answerable_total != 33:
        raise RuntimeError("Expected 33 answerable development questions")

    per_repository: dict[str, Any] = {}
    all_questions: list[dict[str, Any]] = []
    all_control: dict[str, list[dict[str, Any]]] = {}
    all_b1: dict[str, list[dict[str, Any]]] = {}
    all_c1: dict[str, list[dict[str, Any]]] = {}
    pooled_control_lexical: dict[str, list[dict[str, Any]]] = {}
    pooled_b1_lexical: dict[str, list[dict[str, Any]]] = {}
    pooled_c1_lexical: dict[str, list[dict[str, Any]]] = {}

    for repo_id in sorted(entries):
        diagnostic = diagnostic_by_repo[repo_id]
        questions = questions_by_repo[repo_id]
        fixture = load_fixture(ROOT / entries[repo_id]["fixture"]["path"])
        chunks = fixture["chunks"]
        chunk_ids = _chunk_keys(chunks)
        bm25_started = time.perf_counter()
        index = BM25Index.build(chunks)
        build_ms = (time.perf_counter() - bm25_started) * 1000
        data = diagnostic["_comparison_data"]
        control_full = data["control_rankings"]
        b1_rankings: dict[str, list[dict[str, Any]]] = {}
        b1_lexical: dict[str, list[dict[str, Any]]] = {}
        bm25_query_times: list[float] = []
        for question in questions:
            question_id = str(question["id"])
            vector_rows = [
                row
                for row in control_full[question_id]
                if row.get("vector_rank") is not None
            ]
            vector_rows.sort(key=lambda row: int(row["vector_rank"]))
            vector_results = _attach_ids(vector_rows[:TOP_K], chunk_ids)
            started = time.perf_counter()
            scored = index.rank(str(question["question"]), limit=TOP_K)
            bm25_query_times.append((time.perf_counter() - started) * 1000)
            lexical_results = [
                {
                    **dict(chunks[index_number]),
                    "id": index_number + 1,
                    "score": score,
                }
                for index_number, score in scored
            ]
            question_key = question_id
            b1_lexical[question_key] = lexical_results
            b1_rankings[question_key] = _fuse(vector_results, lexical_results)

        c1_lexical, sql_query_times = await _c1_rankings(chunks, questions)
        c1_lexical = {
            question_id: _attach_ids(rows, chunk_ids)
            for question_id, rows in c1_lexical.items()
        }
        c1_rankings = {}
        for question in questions:
            question_id = str(question["id"])
            vector_rows = [
                row
                for row in control_full[question_id]
                if row.get("vector_rank") is not None
            ]
            vector_rows.sort(key=lambda row: int(row["vector_rank"]))
            vector_results = _attach_ids(vector_rows[:TOP_K], chunk_ids)
            c1_rankings[question_id] = _fuse(
                vector_results,
                c1_lexical[question_id],
            )

        control_lexical = {
            str(question["id"]): sorted(
                [
                    row
                    for row in control_full[str(question["id"])]
                    if row.get("fulltext_rank") is not None
                ],
                key=lambda row: int(row["fulltext_rank"]),
            )[:TOP_K]
            for question in questions
        }
        methods = {
            "control": summarize_method(questions, controls[repo_id]),
            "B1": summarize_method(questions, b1_rankings),
            "C1": summarize_method(questions, c1_rankings),
        }
        lexical = {
            "control": _lexical_summary(questions, control_lexical),
            "B1": _lexical_summary(questions, b1_lexical),
            "C1": _lexical_summary(questions, c1_lexical),
        }
        guard = _guard_comparison(
            questions,
            controls[repo_id],
            b1_rankings,
        )
        guard["control"] = summarize_control_guard(questions, controls[repo_id])
        per_repository[repo_id] = {
            "methods": {arm: _public_summary(row) for arm, row in methods.items()},
            "lexical_branch": lexical,
            "guard": guard,
            "cost": {
                "bm25_index_build_ms": build_ms,
                "bm25_query_mean_ms": (
                    sum(bm25_query_times) / len(bm25_query_times)
                    if bm25_query_times
                    else 0.0
                ),
                "sql_c1_query_mean_ms": (
                    sum(sql_query_times) / len(sql_query_times)
                    if sql_query_times
                    else 0.0
                ),
            },
        }

        for question in questions:
            question_id = str(question["id"])
            namespaced = {**question, "id": f"{repo_id}:{question_id}"}
            all_questions.append(namespaced)
            all_control[f"{repo_id}:{question_id}"] = controls[repo_id][question_id]
            all_b1[f"{repo_id}:{question_id}"] = b1_rankings[question_id]
            all_c1[f"{repo_id}:{question_id}"] = c1_rankings[question_id]
            pooled_control_lexical[f"{repo_id}:{question_id}"] = control_lexical[
                question_id
            ]
            pooled_b1_lexical[f"{repo_id}:{question_id}"] = b1_lexical[question_id]
            pooled_c1_lexical[f"{repo_id}:{question_id}"] = c1_lexical[question_id]

    pooled_methods_raw = {
        "control": summarize_method(all_questions, all_control),
        "B1": summarize_method(all_questions, all_b1),
        "C1": summarize_method(all_questions, all_c1),
    }
    pooled_lexical = {
        "control": _lexical_summary(all_questions, pooled_control_lexical),
        "B1": _lexical_summary(all_questions, pooled_b1_lexical),
        "C1": _lexical_summary(all_questions, pooled_c1_lexical),
    }
    statistics = paired_mrr_statistics(
        pooled_methods_raw["control"]["mrr_reciprocal_values"],
        pooled_methods_raw["B1"]["mrr_reciprocal_values"],
        seed=20261031,
        resamples=10_000,
    )
    guards_unchanged = all(
        not result["guard"]["changed_development_ordinals"]
        for result in per_repository.values()
    )
    decision = decide_b1(
        {
            repo: {
                "hit_at_5_successes": row["methods"]["control"]["hit_at_5_successes"]
            }
            for repo, row in per_repository.items()
        },
        {
            repo: {
                "hit_at_5_successes": row["methods"]["B1"]["hit_at_5_successes"]
            }
            for repo, row in per_repository.items()
        },
        float(statistics["mrr_difference"]),
        statistics["bootstrap_95_percentile_interval"],
        guards_unchanged,
    )
    return {
        "metadata": {
            "protocol": PROTOCOL_PATH,
            "protocol_commit": PROTOCOL_COMMIT,
            "split": "development",
            "answerable_questions": answerable_total,
            "repositories": sorted(per_repository),
            "bm25_k1": 1.2,
            "bm25_b": 0.75,
            "top_k": TOP_K,
            "rrf_constant": 60,
            "control_reconciliation": "passed 33/33 per-question label and span ranks",
            "provider_calls": False,
            "held_out_used": False,
        },
        "per_repository": per_repository,
        "pooled": {
            "methods": {
                arm: _public_summary(row)
                for arm, row in pooled_methods_raw.items()
            },
            "lexical_branch": pooled_lexical,
            "statistics": statistics,
        },
        "decision": decision,
    }


def _render_results(results: dict[str, Any]) -> str:
    return _render_note(results)


async def run_and_write() -> dict[str, Any]:
    results = await run_comparison()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    NOTE_PATH.write_text(_render_results(results), encoding="utf-8", newline="\n")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        results = asyncio.run(run_and_write())
    except (OSError, SQLAlchemyError, ValueError, RuntimeError, KeyError, TypeError):
        print(
            "BM25 comparison failed before a result was written; no question data was printed.",
            file=sys.stderr,
        )
        return 2
    print("Scope=development; control baseline reconciliation=33/33")
    for repo_id in [*sorted(results["per_repository"]), "pooled"]:
        methods = (
            results["pooled"]["methods"]
            if repo_id == "pooled"
            else results["per_repository"][repo_id]["methods"]
        )
        for arm in ("control", "B1", "C1"):
            metrics = methods[arm]
            print(
                f"{repo_id} {arm}: "
                f"Hit@1={metrics['hit_at_1_successes']}/"
                f"{metrics['answerable_questions']} "
                f"Hit@3={metrics['hit_at_3_successes']}/"
                f"{metrics['answerable_questions']} "
                f"Hit@5={metrics['hit_at_5_successes']}/"
                f"{metrics['answerable_questions']} MRR={metrics['mrr']:.6f}"
            )
    statistics = results["pooled"]["statistics"]
    low, high = statistics["bootstrap_95_percentile_interval"]
    print(
        f"B1 pooled delta MRR={statistics['mrr_difference']:.6f}; "
        f"95% CI=[{low:.6f}, {high:.6f}]; "
        f"sign={statistics['sign_test']['positive']}/"
        f"{statistics['sign_test']['negative']}/"
        f"{statistics['sign_test']['ties']} "
        f"p={statistics['sign_test']['two_sided_p_value']:.6f}"
    )
    for rule, condition in results["decision"]["conditions"].items():
        print(f"{rule.split('_', 1)[0]}={'PASS' if condition else 'FAIL'}")
    print(f"BM25 comparison decision: {results['decision']['decision']}")
    print(f"Results: {REPORT_PATH}")
    print(f"Note: {NOTE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
