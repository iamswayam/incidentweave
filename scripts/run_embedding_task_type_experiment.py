"""Plan, run, and compare the registered development embedding task-type experiment."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.providers.gemini import ProviderError  # noqa: E402
from evaluation.build_fixture import load_fixture, write_fixture  # noqa: E402
from evaluation.embedding_task_type import (  # noqa: E402
    DOCUMENT_TASK_TYPE,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    EXPERIMENT_VERSION,
    QUERY_TASK_TYPE,
    EmbeddingInputs,
    collect_embedding_inputs,
    compare_guard_decisions,
    embedding_cache_key,
    evaluate_task_type_rules,
    paired_mrr_statistics,
    read_cached_vector,
    render_results,
    summarize_method,
    write_results_note,
)
from evaluation.manifest import (  # noqa: E402
    MANIFEST_PATH,
    manifest_root,
)
from scripts.diagnose_test_files import _development_question_records  # noqa: E402

CACHE_ROOT = ROOT / "evaluation" / "cache" / "embedding_task_type_v1"
RESULTS_NOTE_PATH = ROOT / "docs" / "notes" / "15-embedding-task-type-results.md"
RESULT_LIMITS = (
    "This comparison covers 33 answerable and 15 unanswerable development questions "
    "across three small repositories; results may not generalize to other repositories "
    "or query distributions.",
    "A successful retrieval metric does not establish answer quality; the held-out "
    "split remains untouched.",
    "The evidence-guard threshold of 0.5 is provisional and was set on the control "
    "embeddings. A candidate may shift distances and change guard decisions; an R4 "
    "failure for that reason is valid, and threshold recalibration is out of scope "
    "for this comparison (item 3b).",
)
MAX_DOCUMENT_TEXTS = 200
MAX_QUERY_TEXTS = 48
DOCUMENT_BATCH_SIZE = 50
MAX_DOCUMENT_BATCHES = math.ceil(MAX_DOCUMENT_TEXTS / DOCUMENT_BATCH_SIZE)
DOCUMENT_BATCH_DELAY_SECONDS = 70.0
QUERY_REQUEST_DELAY_SECONDS = 1.5


def _load_development_inputs(
    manifest_path: Path,
) -> tuple[
    dict[str, Any],
    Path,
    dict[str, dict[str, Any]],
    dict[str, list[dict[str, Any]]],
]:
    asset_root = manifest_root(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(
        manifest.get("repositories"), list
    ):
        raise ValueError("Evaluation manifest must list repositories")
    fixtures: dict[str, dict[str, Any]] = {}
    development_questions: dict[str, list[dict[str, Any]]] = {}
    total_questions = 0
    total_answerable = 0
    for entry in manifest["repositories"]:
        repository = str(entry["id"])
        fixture = load_fixture(asset_root / entry["fixture"]["path"])
        development_ids = entry["splits"]["development"]
        if not isinstance(development_ids, list) or any(
            not isinstance(question_id, str) for question_id in development_ids
        ):
            raise ValueError(
                f"{repository}: development split must contain question ids"
            )
        selected = _development_question_records(
            asset_root / entry["questions"]["path"],
            set(development_ids),
        )
        selected_ids = {str(question["id"]) for question in selected}
        fixture_queries = fixture.get("queries")
        if not isinstance(fixture_queries, dict) or not selected_ids <= set(
            fixture_queries
        ):
            raise ValueError(
                f"{repository}: fixture is missing a development query embedding"
            )
        fixture["queries"] = {
            question_id: fixture_queries[question_id]
            for question_id in selected_ids
        }
        fixtures[repository] = fixture
        answerable = sum(
            question.get("category") in {"direct", "paraphrased"}
            for question in selected
        )
        if len(selected) != 16 or answerable != 11:
            raise ValueError(
                f"{repository}: unexpected development split dimensions"
            )
        development_questions[repository] = selected
        total_questions += len(selected)
        total_answerable += answerable
    if total_questions != 48 or total_answerable != 33:
        raise ValueError("Unexpected pooled development split dimensions")
    return manifest, asset_root, fixtures, development_questions


def _cache_path(text: str, task_type: str) -> Path:
    return CACHE_ROOT / f"{embedding_cache_key(text, task_type)}.json"


def _missing_texts(
    texts: tuple[str, ...],
    task_type: str,
) -> list[str]:
    return [text for text in texts if not _cache_path(text, task_type).is_file()]


def _require_cached_vectors(inputs: EmbeddingInputs) -> None:
    missing_documents = _missing_texts(inputs.document_texts, DOCUMENT_TASK_TYPE)
    missing_queries = _missing_texts(inputs.query_texts, QUERY_TASK_TYPE)
    if missing_documents or missing_queries:
        raise ValueError(
            "Embedding cache is incomplete: "
            f"missing document vectors={len(missing_documents)}, "
            f"missing development query vectors={len(missing_queries)}"
        )
    for text in inputs.document_texts:
        read_cached_vector(_cache_path(text, DOCUMENT_TASK_TYPE))
    for text in inputs.query_texts:
        read_cached_vector(_cache_path(text, QUERY_TASK_TYPE))


def _protocol_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Cannot identify the registered protocol commit") from exc
    commit = result.stdout.strip()
    if not commit:
        raise RuntimeError("Git returned an empty protocol commit")
    return commit


def _request_plan(
    document_texts: tuple[str, ...],
    query_texts: tuple[str, ...],
) -> dict[str, int]:
    document_batches = math.ceil(len(document_texts) / DOCUMENT_BATCH_SIZE)
    return {
        "document_texts": len(document_texts),
        "document_requests": document_batches,
        "query_texts": len(query_texts),
        "query_requests": len(query_texts),
        "provider_requests": document_batches + len(query_texts),
        "maximum_attempts_per_request": 1,
    }


def _check_request_caps(plan: dict[str, int]) -> None:
    if plan["document_texts"] > MAX_DOCUMENT_TEXTS:
        raise ValueError(
            f"Document embedding plan exceeds {MAX_DOCUMENT_TEXTS} unique texts"
        )
    if plan["query_texts"] > MAX_QUERY_TEXTS:
        raise ValueError(
            f"Query embedding plan exceeds {MAX_QUERY_TEXTS} development questions"
        )
    if plan["document_requests"] > MAX_DOCUMENT_BATCHES:
        raise ValueError(
            f"Document embedding plan exceeds {MAX_DOCUMENT_BATCHES} batch requests"
        )


def _plan(manifest_path: Path) -> int:
    manifest, _, fixtures, questions = _load_development_inputs(
        manifest_path
    )
    inputs = collect_embedding_inputs(fixtures, questions)
    missing_documents = _missing_texts(inputs.document_texts, DOCUMENT_TASK_TYPE)
    missing_queries = _missing_texts(inputs.query_texts, QUERY_TASK_TYPE)
    plan = _request_plan(
        tuple(missing_documents),
        tuple(missing_queries),
    )
    _check_request_caps(plan)

    for entry in manifest["repositories"]:
        repository = str(entry["id"])
        print(
            f"{repository}: development ordinals 1-16; "
            f"development questions={len(questions[repository])}; "
            f"fixture chunks={len(fixtures[repository]['chunks'])}"
        )
    print(
        f"Unique uncached document texts={plan['document_texts']}; "
        f"document batch requests={plan['document_requests']}"
    )
    print(
        f"Unique uncached development query texts={plan['query_texts']}; "
        f"query requests={plan['query_requests']}"
    )
    print(
        f"Provider requests={plan['provider_requests']}; "
        f"maximum attempts per request={plan['maximum_attempts_per_request']}"
    )
    print(
        "Usage operation tags: document_embedding for document batches; "
        "query_embedding for query requests."
    )
    print(
        f"Caps: {MAX_DOCUMENT_TEXTS} document texts, "
        f"{MAX_QUERY_TEXTS} query texts, "
        f"{MAX_DOCUMENT_BATCHES} document batches."
    )
    return 0


def _write_vector(text: str, task_type: str, vector: list[float]) -> None:
    if len(vector) != EMBEDDING_DIMENSION:
        raise ValueError("Provider returned an embedding with the wrong dimension")
    if any(not math.isfinite(value) for value in vector):
        raise ValueError("Provider returned a non-finite embedding value")
    path = _cache_path(text, task_type)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(vector, separators=(",", ":")),
        encoding="utf-8",
    )


async def _embed(manifest_path: Path, document_delay: float, query_delay: float) -> int:
    if not (settings.gemini_api_key or "").strip():
        raise ValueError("GEMINI_API_KEY is missing.")
    _, _, fixtures, questions = _load_development_inputs(
        manifest_path
    )
    inputs = collect_embedding_inputs(fixtures, questions)
    documents = _missing_texts(inputs.document_texts, DOCUMENT_TASK_TYPE)
    queries = _missing_texts(inputs.query_texts, QUERY_TASK_TYPE)
    plan = _request_plan(tuple(documents), tuple(queries))
    _check_request_caps(plan)
    if not plan["provider_requests"]:
        print("All development task-type embeddings are cached; no provider call made.")
        return 0

    from scripts.embed_chunks import embed_text, embed_texts

    batches = [
        documents[offset : offset + DOCUMENT_BATCH_SIZE]
        for offset in range(0, len(documents), DOCUMENT_BATCH_SIZE)
    ]
    for index, batch in enumerate(batches):
        vectors = await embed_texts(
            batch,
            task_type=DOCUMENT_TASK_TYPE,
            max_attempts=1,
        )
        if len(vectors) != len(batch):
            raise ValueError("Provider returned the wrong number of document vectors")
        for text, vector in zip(batch, vectors):
            _write_vector(text, DOCUMENT_TASK_TYPE, vector)
        if index + 1 < len(batches):
            await asyncio.sleep(document_delay)

    if batches and queries:
        await asyncio.sleep(query_delay)
    for index, text in enumerate(queries):
        vector = await embed_text(
            text,
            task_type=QUERY_TASK_TYPE,
            max_attempts=1,
        )
        _write_vector(text, QUERY_TASK_TYPE, vector)
        if index + 1 < len(queries):
            await asyncio.sleep(query_delay)

    print(
        f"Cached document vectors={len(documents)}; "
        f"cached development query vectors={len(queries)}."
    )
    return 0


def _candidate_fixture(
    fixture: dict[str, Any],
    questions: list[dict[str, Any]],
    output_path: Path,
    max_bytes: int,
) -> Path:
    candidate = {
        "meta": {
            **fixture["meta"],
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "embedding_task_type_version": EXPERIMENT_VERSION,
            "document_task_type": DOCUMENT_TASK_TYPE,
            "query_task_type": QUERY_TASK_TYPE,
            "question_count": len(questions),
            "selection_split": "development",
        },
        "chunks": [],
        "queries": {},
    }
    for chunk in fixture["chunks"]:
        vector = read_cached_vector(
            _cache_path(str(chunk["content"]), DOCUMENT_TASK_TYPE)
        )
        candidate["chunks"].append({**chunk, "embedding": vector})
    for question in questions:
        question_id = str(question["id"])
        candidate["queries"][question_id] = read_cached_vector(
            _cache_path(str(question["question"]), QUERY_TASK_TYPE)
        )
    write_fixture(candidate, output_path, max_bytes)
    return output_path


def _rankings(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        str(row["id"]): list(row["retrieved"])
        for row in report["questions"]
    }


def _public_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metrics.items()
        if key != "reciprocal_ranks"
    }


async def _evaluate(manifest_path: Path) -> int:
    from evaluation.retrieval_eval import run_offline_retrieval

    manifest, asset_root, fixtures, questions = _load_development_inputs(
        manifest_path
    )
    inputs = collect_embedding_inputs(fixtures, questions)
    _require_cached_vectors(inputs)
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    per_repository: dict[str, dict[str, dict[str, Any]]] = {}
    guard_by_repository: dict[str, dict[str, Any]] = {}
    pooled_control_ranks: list[float] = []
    pooled_candidate_ranks: list[float] = []
    pooled_question_results: dict[str, list[tuple[Any, Any]]] = {
        "control": [],
        "candidate": [],
    }

    for entry in manifest["repositories"]:
        repository = str(entry["id"])
        control_path = CACHE_ROOT / "controls" / f"{repository}.json.gz"
        candidate_path = CACHE_ROOT / "fixtures" / f"{repository}.json.gz"
        write_fixture(
            fixtures[repository],
            control_path,
            int(entry["fixture"]["max_bytes"]),
        )
        _candidate_fixture(
            fixtures[repository],
            questions[repository],
            candidate_path,
            int(entry["fixture"]["max_bytes"]),
        )
        control_report = await run_offline_retrieval(
            fixture_path=control_path,
            repo_id=repository,
            split="development",
            entry=entry,
            manifest_path=manifest_path,
            root=asset_root,
            record_details=True,
            development_records=questions[repository],
            golden_pinned_sha=str(entry["pinned_sha"]),
        )
        candidate_report = await run_offline_retrieval(
            fixture_path=candidate_path,
            repo_id=repository,
            split="development",
            entry=entry,
            manifest_path=manifest_path,
            root=asset_root,
            record_details=True,
            development_records=questions[repository],
            golden_pinned_sha=str(entry["pinned_sha"]),
        )
        control_rankings = _rankings(control_report)
        candidate_rankings = _rankings(candidate_report)
        control_rows = {
            str(row["id"]): row for row in control_report["questions"]
        }
        candidate_rows = {
            str(row["id"]): row for row in candidate_report["questions"]
        }
        control_pairs = [
            (question, control_rankings[str(question["id"])])
            for question in questions[repository]
        ]
        candidate_pairs = [
            (question, candidate_rankings[str(question["id"])])
            for question in questions[repository]
        ]
        control_metrics = summarize_method(control_pairs)
        candidate_metrics = summarize_method(candidate_pairs)
        per_repository[repository] = {
            "control": _public_metrics(control_metrics),
            "candidate": _public_metrics(candidate_metrics),
        }
        pooled_control_ranks.extend(control_metrics["reciprocal_ranks"])
        pooled_candidate_ranks.extend(candidate_metrics["reciprocal_ranks"])
        pooled_question_results["control"].extend(control_pairs)
        pooled_question_results["candidate"].extend(candidate_pairs)

        guard_by_repository[repository] = _compare_guards(
            questions[repository],
            control_rankings,
            candidate_rankings,
        )
        if len(control_rows) != 16 or len(candidate_rows) != 16:
            raise ValueError(f"{repository}: retrieval report did not cover development")

    pooled_metrics = {
        method: _public_metrics(summarize_method(pooled_question_results[method]))
        for method in ("control", "candidate")
    }
    bootstrap = paired_mrr_statistics(
        pooled_control_ranks,
        pooled_candidate_ranks,
    )
    decision = evaluate_task_type_rules(
        pooled_metrics["control"],
        pooled_metrics["candidate"],
        {
            name: values["control"]
            for name, values in per_repository.items()
        },
        {
            name: values["candidate"]
            for name, values in per_repository.items()
        },
        guard_by_repository,
        bootstrap,
    )
    report = {
        "experiment_version": EXPERIMENT_VERSION,
        "selection_split": "development",
        "protocol_commit": _protocol_commit_hash(),
        "limits": RESULT_LIMITS,
        "bootstrap": bootstrap,
        "per_repository": per_repository,
        "pooled": pooled_metrics,
        "guard_by_repository": guard_by_repository,
        "decision": decision,
    }
    markdown_path = CACHE_ROOT / "report-development.md"
    json_path = CACHE_ROOT / "report-development.json"
    markdown_path.write_text(render_results(report), encoding="utf-8")
    write_results_note(report, RESULTS_NOTE_PATH)
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(render_results(report), end="")
    print(f"Development-only report: {markdown_path}")
    print(f"Aggregate-only results note: {RESULTS_NOTE_PATH}")
    return 0


def _compare_guards(
    questions: list[dict[str, Any]],
    control_rankings: dict[str, list[dict[str, Any]]],
    candidate_rankings: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    return compare_guard_decisions(
        questions,
        control_rankings,
        candidate_rankings,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("plan", "embed", "evaluate"),
        help="plan counts only, embed development inputs, or evaluate cached vectors",
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument(
        "--confirm-provider-calls",
        action="store_true",
        help="explicitly authorize bounded Gemini embedding requests",
    )
    parser.add_argument(
        "--document-batch-delay-seconds",
        type=float,
        default=DOCUMENT_BATCH_DELAY_SECONDS,
    )
    parser.add_argument(
        "--query-delay-seconds",
        type=float,
        default=QUERY_REQUEST_DELAY_SECONDS,
    )
    return parser


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, ProviderError):
        return f"Gemini provider request failed ({exc.error_class})."

    message = str(exc)
    for api_key in (settings.gemini_api_key, os.environ.get("GEMINI_API_KEY")):
        if api_key:
            message = message.replace(api_key, "[REDACTED]")
    return message


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "embed" and not args.confirm_provider_calls:
        print("embed requires --confirm-provider-calls.", file=sys.stderr)
        return 2
    if args.document_batch_delay_seconds < 0 or args.query_delay_seconds < 0:
        print("Pacing delays must be non-negative.", file=sys.stderr)
        return 2
    try:
        if args.command == "plan":
            return _plan(args.manifest)
        if args.command == "embed":
            return asyncio.run(
                _embed(
                    args.manifest,
                    args.document_batch_delay_seconds,
                    args.query_delay_seconds,
                )
            )
        return asyncio.run(_evaluate(args.manifest))
    except (OSError, RuntimeError, ValueError, SQLAlchemyError) as exc:
        print(f"Error: {_safe_error_message(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
