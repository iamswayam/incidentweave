"""Plan, embed, and evaluate the registered development-only local models."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import Chunk, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.investigation.guard import (  # noqa: E402
    MAX_ACCEPTABLE_VECTOR_DISTANCE,
    evaluate_evidence_sufficiency,
)
from app.retrieval.fulltext_search import search_fulltext  # noqa: E402
from evaluation.local_embedding import (  # noqa: E402
    ANSWERABLE_CATEGORIES,
    CONTROL_DIMENSIONS,
    CONTROL_MODEL,
    EXPERIMENT_VERSION,
    FASTEMBED_VERSION,
    GUARD_DISTANCE_THRESHOLD,
    MODELS,
    TOP_K,
    EmbeddingModel,
    VectorRole,
    cache_path,
    cache_record,
    fuse_rankings,
    label_rank,
    paired_bootstrap,
    rank_vectors,
    read_cache_record,
    require_development_records,
    retention_rules,
    summarize_distances,
    summarize_ranks,
    text_hash,
    validate_vector,
)
from evaluation.manifest import (  # noqa: E402
    MANIFEST_PATH,
    manifest_root,
    questions_for_split,
)
from evaluation.test_files import is_test_path  # noqa: E402
from scripts.diagnose_test_files import _development_question_records  # noqa: E402

CACHE_ROOT = ROOT / "evaluation" / "cache" / EXPERIMENT_VERSION
RESULTS_JSON_PATH = CACHE_ROOT / "results-development.json"
RESULTS_NOTE_PATH = ROOT / "docs" / "notes" / "18-local-embedding-results.md"
DEVELOPMENT_QUESTION_COUNT = 48
DEVELOPMENT_ANSWERABLE_COUNT = 33
DEVELOPMENT_UNANSWERABLE_COUNT = 15
EMBED_BATCH_SIZE = 8
DEFAULT_EMBED_THREADS = os.cpu_count() or 1
CONTROL_CACHE_ROOT = ROOT / "evaluation" / "cache"


def _load_development_inputs(
    manifest_path: Path,
) -> tuple[dict[str, Any], Path, dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    if manifest_path.resolve() != MANIFEST_PATH.resolve():
        raise ValueError("Local embedding comparison requires the registered manifest")
    root = manifest_root(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("repositories"), list):
        raise ValueError("Evaluation manifest must list repositories")
    questions_by_repository: dict[str, list[dict[str, Any]]] = {}
    baseline_by_repository: dict[str, list[dict[str, Any]]] = {}
    total_questions = 0
    total_answerable = 0
    for entry in manifest["repositories"]:
        repository = str(entry["id"])
        development_ids = entry["splits"].get("development")
        if (
            not isinstance(development_ids, list)
            or any(not isinstance(question_id, str) for question_id in development_ids)
        ):
            raise ValueError(f"{repository}: invalid development split")
        allowed_ids = set(development_ids)
        if len(allowed_ids) != len(development_ids):
            raise ValueError(f"{repository}: duplicate development question IDs")

        question_path = root / entry["questions"]["path"]
        selected_questions = questions_for_split(
            entry,
            _development_question_records(question_path, allowed_ids),
            "development",
        )
        questions = require_development_records(
            selected_questions,
            allowed_ids,
            "development",
        )

        baseline_path = root / entry["full_baseline"]["path"]
        selected_baseline = questions_for_split(
            entry,
            _development_question_records(baseline_path, allowed_ids),
            "development",
        )
        baseline = require_development_records(
            selected_baseline,
            allowed_ids,
            "development",
        )
        if len(questions) != 16 or len(baseline) != 16:
            raise ValueError(f"{repository}: unexpected development question count")
        answerable = sum(
            question.get("category") in ANSWERABLE_CATEGORIES
            for question in questions
        )
        if answerable != 11:
            raise ValueError(f"{repository}: unexpected answerable development count")
        questions_by_repository[repository] = questions
        baseline_by_repository[repository] = baseline
        total_questions += len(questions)
        total_answerable += answerable

    if (
        total_questions != DEVELOPMENT_QUESTION_COUNT
        or total_answerable != DEVELOPMENT_ANSWERABLE_COUNT
        or total_questions - total_answerable != DEVELOPMENT_UNANSWERABLE_COUNT
    ):
        raise ValueError("Unexpected pooled development split dimensions")
    return manifest, root, questions_by_repository, baseline_by_repository


async def _load_repository_chunks(
    session: Any,
    entry: dict[str, Any],
    *,
    include_embeddings: bool,
) -> tuple[int, list[dict[str, Any]]]:
    database_repository = entry.get("database_repository")
    if not isinstance(database_repository, str) or not database_repository:
        raise ValueError(f"{entry['id']}: missing evaluation database repository")
    repository = await session.scalar(
        select(Repository).where(Repository.name == database_repository)
    )
    if repository is None:
        raise RuntimeError(f"{entry['id']}: evaluation repository was not found")
    columns = [
        Chunk.id,
        Chunk.file_path,
        Chunk.line_start,
        Chunk.line_end,
        Chunk.content,
    ]
    if include_embeddings:
        columns.append(Chunk.embedding)
    rows = (
        await session.execute(
            select(*columns)
            .where(Chunk.repository_id == repository.id)
            .order_by(Chunk.file_path, Chunk.line_start, Chunk.line_end, Chunk.id)
        )
    ).all()
    chunks: list[dict[str, Any]] = []
    for row in rows:
        record = {
            "id": row[0],
            "file_path": row[1],
            "line_start": row[2],
            "line_end": row[3],
            "content": row[4],
        }
        if include_embeddings:
            if row[5] is None:
                raise ValueError(f"{entry['id']}: evaluation chunk is missing its control vector")
            record["control_embedding"] = validate_vector(row[5], CONTROL_DIMENSIONS)
        chunks.append(record)
    if not chunks:
        raise ValueError(f"{entry['id']}: evaluation repository contains no chunks")
    return int(repository.id), chunks


def _unique_texts(
    questions_by_repository: dict[str, list[dict[str, Any]]],
    chunks_by_repository: dict[str, list[dict[str, Any]]],
) -> tuple[list[str], list[str]]:
    documents = {
        str(chunk["content"])
        for chunks in chunks_by_repository.values()
        for chunk in chunks
    }
    queries = {
        str(question["question"])
        for questions in questions_by_repository.values()
        for question in questions
    }
    return (
        sorted(documents, key=text_hash),
        sorted(queries, key=text_hash),
    )


def _read_candidate_vector(
    model: EmbeddingModel,
    role: VectorRole,
    value: str,
) -> list[float]:
    path = cache_path(CACHE_ROOT, model, role, value)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{model.slug}: missing or invalid vector cache entry") from exc
    if not isinstance(record, dict):
        raise ValueError(f"{model.slug}: invalid vector cache record")
    return read_cache_record(record, model, role, value)


def _read_control_query(value: str) -> list[float]:
    path = CONTROL_CACHE_ROOT / f"{hashlib.sha256(value.encode('utf-8')).hexdigest()}.json"
    try:
        raw_vector = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("A development control query vector is missing or invalid") from exc
    if not isinstance(raw_vector, list):
        raise ValueError("A development control query vector is invalid")
    return [round(value, 6) for value in validate_vector(raw_vector, CONTROL_DIMENSIONS)]


def _read_control_documents(
    chunks: list[dict[str, Any]],
) -> dict[str, list[float]]:
    vectors: dict[str, list[float]] = {}
    for chunk in chunks:
        content = str(chunk["content"])
        vector = [round(value, 6) for value in chunk["control_embedding"]]
        existing = vectors.get(content)
        if existing is not None and existing != vector:
            raise ValueError("Identical control document text has inconsistent vectors")
        vectors[content] = vector
    return vectors


async def _retrieve(
    session: Any,
    repository_id: int,
    question: dict[str, Any],
    chunks: list[dict[str, Any]],
    document_vectors: dict[str, list[float]],
    query_vector: list[float],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    vector_results = rank_vectors(chunks, document_vectors, query_vector, limit=TOP_K)
    fulltext_results = await search_fulltext(
        session,
        repository_id,
        str(question["question"]),
        limit=TOP_K,
    )
    results = fuse_rankings(
        repository_id,
        vector_results,
        fulltext_results,
        limit=TOP_K,
    )
    return results, evaluate_evidence_sufficiency(results)


def _cache_missing_count(
    model: EmbeddingModel,
    role: VectorRole,
    texts: list[str],
) -> int:
    missing = 0
    for value in texts:
        path = cache_path(CACHE_ROOT, model, role, value)
        if not path.is_file():
            missing += 1
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"{model.slug}: invalid existing cache entry") from exc
        if not isinstance(record, dict):
            raise ValueError(f"{model.slug}: invalid existing cache entry")
        read_cache_record(record, model, role, value)
    return missing


async def _plan(manifest_path: Path) -> int:
    manifest, _, questions, _ = _load_development_inputs(manifest_path)
    chunks_by_repository: dict[str, list[dict[str, Any]]] = {}
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(text("SET TRANSACTION READ ONLY"))
            for entry in manifest["repositories"]:
                _repository_id, chunks = await _load_repository_chunks(
                    session,
                    entry,
                    include_embeddings=False,
                )
                chunks_by_repository[str(entry["id"])] = chunks
    document_texts, query_texts = _unique_texts(questions, chunks_by_repository)
    print(
        f"Split: development only; questions={DEVELOPMENT_QUESTION_COUNT} "
        f"(answerable={DEVELOPMENT_ANSWERABLE_COUNT}, "
        f"unanswerable={DEVELOPMENT_UNANSWERABLE_COUNT})"
    )
    print(
        f"Documents: {sum(map(len, chunks_by_repository.values()))} chunk occurrences; "
        f"{len(document_texts)} unique texts"
    )
    print(f"Queries: {len(query_texts)} unique texts")
    for repository, chunks in chunks_by_repository.items():
        print(
            f"{repository}: chunks={len(chunks)}, "
            f"development_questions={len(questions[repository])}"
        )
    missing_control = sum(
        not (
            CONTROL_CACHE_ROOT
            / f"{hashlib.sha256(str(question['question']).encode('utf-8')).hexdigest()}.json"
        ).is_file()
        for rows in questions.values()
        for question in rows
    )
    print(f"Control Gemini development query cache misses: {missing_control}")
    for model in MODELS:
        missing_documents = _cache_missing_count(model, "document", document_texts)
        missing_queries = _cache_missing_count(model, "query", query_texts)
        print(
            f"{model.model_name}: document cache misses={missing_documents}, "
            f"query cache misses={missing_queries}, dimensions={model.dimensions}"
        )
    return 0


def _save_cache_record(
    model: EmbeddingModel,
    role: VectorRole,
    value: str,
    vector: Any,
) -> None:
    path = cache_path(CACHE_ROOT, model, role, value)
    record = cache_record(
        model,
        role,
        value,
        [float(component) for component in vector],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _embed_missing(
    embedder: Any,
    texts: list[str],
    role: VectorRole,
    model: EmbeddingModel,
    *,
    batch_size: int = EMBED_BATCH_SIZE,
    show_progress: bool = False,
) -> tuple[float, int]:
    missing = [
        value
        for value in texts
        if not cache_path(CACHE_ROOT, model, role, value).is_file()
    ]
    for value in texts:
        path = cache_path(CACHE_ROOT, model, role, value)
        if path.is_file():
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"{model.slug}: invalid existing cache entry") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{model.slug}: invalid existing cache entry")
            read_cache_record(record, model, role, value)
    if not missing:
        return 0.0, 0
    start = time.perf_counter()
    method = embedder.passage_embed if role == "document" else embedder.query_embed
    vectors = method(missing, batch_size=batch_size)
    count = 0
    for value, vector in zip(missing, vectors, strict=True):
        _save_cache_record(model, role, value, vector)
        count += 1
        if show_progress:
            elapsed = time.perf_counter() - start
            average_seconds = elapsed / count
            remaining_seconds = average_seconds * (len(missing) - count)
            print(
                f"{model.slug} {role}: item {count} of {len(missing)}; "
                f"{average_seconds:.2f} seconds/item; "
                f"ETA {_format_duration(remaining_seconds)}",
                flush=True,
            )
    elapsed = time.perf_counter() - start
    if count != len(missing):
        raise RuntimeError(f"{model.slug}: embedder returned an incomplete vector batch")
    return elapsed, count


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds_part = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds_part:02}"


async def _embed(manifest_path: Path, threads: int, batch_size: int) -> int:
    installed_version = importlib.metadata.version("fastembed")
    if installed_version != FASTEMBED_VERSION:
        raise RuntimeError(
            f"Protocol requires fastembed=={FASTEMBED_VERSION}; "
            f"found {installed_version}"
        )
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise RuntimeError("Install the local-embeddings optional dependency to embed") from exc

    manifest, _, questions, _ = _load_development_inputs(manifest_path)
    chunks_by_repository: dict[str, list[dict[str, Any]]] = {}
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(text("SET TRANSACTION READ ONLY"))
            for entry in manifest["repositories"]:
                _repository_id, chunks = await _load_repository_chunks(
                    session,
                    entry,
                    include_embeddings=False,
                )
                chunks_by_repository[str(entry["id"])] = chunks
    document_texts, query_texts = _unique_texts(questions, chunks_by_repository)
    for model in MODELS:
        load_start = time.perf_counter()
        embedder = TextEmbedding(
            model_name=model.model_name,
            threads=threads,
            providers=["CPUExecutionProvider"],
        )
        model_load_seconds = time.perf_counter() - load_start
        print(
            f"{model.model_name}: model loaded in {model_load_seconds:.2f}s "
            f"(threads={threads}, batch_size={batch_size}, "
            "provider=CPUExecutionProvider)",
            flush=True,
        )
        document_seconds, document_count = _embed_missing(
            embedder,
            document_texts,
            "document",
            model,
            batch_size=batch_size,
            show_progress=True,
        )
        query_seconds, query_count = _embed_missing(
            embedder,
            query_texts,
            "query",
            model,
            batch_size=batch_size,
            show_progress=True,
        )
        summary = {
            "experiment_version": EXPERIMENT_VERSION,
            "embedding_model": model.model_name,
            "dimensions": model.dimensions,
            "library": "fastembed",
            "library_version": FASTEMBED_VERSION,
            "execution_provider": "CPUExecutionProvider",
            "thread_count": threads,
            "batch_size": batch_size,
            "model_load_seconds": model_load_seconds,
            "cpu": platform.processor() or platform.machine(),
            "logical_cpu_count": os.cpu_count(),
            "unique_document_vectors_embedded": document_count,
            "unique_query_vectors_embedded": query_count,
            "document_elapsed_seconds": document_seconds,
            "query_elapsed_seconds": query_seconds,
            "mean_seconds_per_unique_document": (
                document_seconds / document_count if document_count else None
            ),
            "mean_seconds_per_unique_query": (
                query_seconds / query_count if query_count else None
            ),
        }
        model_directory = CACHE_ROOT / model.slug
        model_directory.mkdir(parents=True, exist_ok=True)
        (model_directory / "embedding-run.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            f"{model.model_name}: embedded {document_count} unique documents and "
            f"{query_count} unique queries; "
            f"threads={threads}, batch_size={batch_size}; "
            f"{summary['mean_seconds_per_unique_document']} s/document, "
            f"{summary['mean_seconds_per_unique_query']} s/query"
        )
    return 0


def _question_rankings(
    questions: list[dict[str, Any]],
    rankings: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]],
) -> tuple[list[int | None], dict[str, dict[str, Any]]]:
    answerable_ranks: list[int | None] = []
    per_question: dict[str, dict[str, Any]] = {}
    for question in questions:
        question_id = str(question["id"])
        results, guard = rankings[question_id]
        rank = (
            label_rank(results, question)
            if question.get("category") in ANSWERABLE_CATEGORIES
            else None
        )
        per_question[question_id] = {
            "rank": rank,
            "guard_accept": bool(guard["is_sufficient"]),
            "distance": guard["best_vector_score"],
            "top5_test_count": sum(
                is_test_path(str(result.get("file_path") or ""))
                for result in results[:TOP_K]
            ),
            "top5_count": len(results[:TOP_K]),
        }
        if question.get("category") in ANSWERABLE_CATEGORIES:
            answerable_ranks.append(rank)
    return answerable_ranks, per_question


def _per_repository_summary(
    questions_by_repository: dict[str, list[dict[str, Any]]],
    per_question: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, list[bool]]]:
    metrics: dict[str, dict[str, Any]] = {}
    unanswerable_guard: dict[str, list[bool]] = {}
    for repository, questions in questions_by_repository.items():
        answerable = [
            per_question[str(question["id"])]["rank"]
            for question in questions
            if question.get("category") in ANSWERABLE_CATEGORIES
        ]
        metrics[repository] = summarize_ranks(answerable)
        unanswerable_guard[repository] = [
            per_question[str(question["id"])]["guard_accept"]
            for question in questions
            if question.get("category") not in ANSWERABLE_CATEGORIES
        ]
    return metrics, unanswerable_guard


def _baseline_reconciliation(
    questions_by_repository: dict[str, list[dict[str, Any]]],
    baseline_by_repository: dict[str, list[dict[str, Any]]],
    per_question_by_repository: dict[str, dict[str, dict[str, Any]]],
) -> tuple[int, list[dict[str, Any]]]:
    identical = 0
    differences: list[dict[str, Any]] = []
    for repository, questions in questions_by_repository.items():
        baseline_by_id = {
            str(row["id"]): row for row in baseline_by_repository[repository]
        }
        ordinal = 0
        for question in questions:
            if question.get("category") not in ANSWERABLE_CATEGORIES:
                continue
            ordinal += 1
            question_id = str(question["id"])
            expected = baseline_by_id[question_id].get("label_rank")
            actual = per_question_by_repository[repository][question_id]["rank"]
            if expected == actual:
                identical += 1
            else:
                differences.append(
                    {
                        "repository": repository,
                        "development_ordinal": ordinal,
                        "baseline_rank": expected,
                        "control_rank": actual,
                    }
                )
    return identical, differences


async def _evaluate(manifest_path: Path) -> int:
    if MAX_ACCEPTABLE_VECTOR_DISTANCE != GUARD_DISTANCE_THRESHOLD:
        raise RuntimeError("The evidence-guard distance threshold differs from protocol")
    manifest, _, questions_by_repository, baseline_by_repository = (
        _load_development_inputs(manifest_path)
    )
    chunks_by_repository: dict[str, list[dict[str, Any]]] = {}
    repository_ids: dict[str, int] = {}
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(text("SET TRANSACTION READ ONLY"))
            for entry in manifest["repositories"]:
                repository_id, chunks = await _load_repository_chunks(
                    session,
                    entry,
                    include_embeddings=True,
                )
                repository = str(entry["id"])
                repository_ids[repository] = repository_id
                chunks_by_repository[repository] = chunks

    document_texts, query_texts = _unique_texts(
        questions_by_repository,
        chunks_by_repository,
    )
    control_per_question_by_repository: dict[str, dict[str, dict[str, Any]]] = {}
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(text("SET TRANSACTION READ ONLY"))
            for repository, questions in questions_by_repository.items():
                chunks = chunks_by_repository[repository]
                document_vectors = _read_control_documents(chunks)
                rankings: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
                for question in questions:
                    question_id = str(question["id"])
                    results, guard = await _retrieve(
                        session,
                        repository_ids[repository],
                        question,
                        chunks,
                        document_vectors,
                        _read_control_query(str(question["question"])),
                    )
                    rankings[question_id] = (results, guard)
                _ranks, per_question = _question_rankings(questions, rankings)
                control_per_question_by_repository[repository] = per_question

    identical, differences = _baseline_reconciliation(
        questions_by_repository,
        baseline_by_repository,
        control_per_question_by_repository,
    )
    if identical != DEVELOPMENT_ANSWERABLE_COUNT:
        failure_report = {
            "experiment_version": EXPERIMENT_VERSION,
            "selection_split": "development",
            "protocol_commit": _protocol_commit_hash(),
            "control_equivalence": {
                "identical_answerable_development_ranks": identical,
                "expected_answerable_development_ranks": DEVELOPMENT_ANSWERABLE_COUNT,
                "differences": differences,
            },
            "candidate_evaluation": "not run because control equivalence failed",
        }
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        RESULTS_JSON_PATH.write_text(
            json.dumps(failure_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        RESULTS_NOTE_PATH.write_text(
            _render_gate_failure(failure_report),
            encoding="utf-8",
        )
        print(
            f"Control evaluator equivalence failed: {identical}/"
            f"{DEVELOPMENT_ANSWERABLE_COUNT}; candidate metrics were not evaluated."
        )
        for difference in differences:
            print(
                f"{difference['repository']} development ordinal "
                f"{difference['development_ordinal']}: baseline rank="
                f"{difference['baseline_rank']}, evaluator rank="
                f"{difference['control_rank']}"
            )
        print(f"Gate failure note: {RESULTS_NOTE_PATH.relative_to(ROOT)}")
        return 3
    print(
        f"Control evaluator equivalence passed: {identical}/"
        f"{DEVELOPMENT_ANSWERABLE_COUNT} development answerable ranks."
    )

    control_by_repository: dict[str, dict[str, Any]] = {}
    control_guard_by_repository: dict[str, list[bool]] = {}
    control_all_ranks: list[int | None] = []
    for repository, questions in questions_by_repository.items():
        qdata = control_per_question_by_repository[repository]
        repository_metrics, repository_guards = _per_repository_summary(
            questions_by_repository={repository: questions},
            per_question=qdata,
        )
        control_by_repository[repository] = repository_metrics[repository]
        control_guard_by_repository[repository] = repository_guards[repository]
        control_all_ranks.extend(
            qdata[str(question["id"])]["rank"]
            for question in questions
            if question.get("category") in ANSWERABLE_CATEGORIES
        )
    control_metrics = summarize_ranks(control_all_ranks)
    control_distance_by_category = _distance_summary(
        questions_by_repository,
        control_per_question_by_repository,
    )
    control_test_share = _test_share(control_per_question_by_repository)

    candidate_reports: dict[str, Any] = {}
    for model in MODELS:
        document_vectors = {
            value: _read_candidate_vector(model, "document", value)
            for value in document_texts
        }
        query_vectors = {
            value: _read_candidate_vector(model, "query", value)
            for value in query_texts
        }
        candidate_per_question_by_repository: dict[str, dict[str, dict[str, Any]]] = {}
        candidate_rank_lists: list[int | None] = []
        async with AsyncSessionLocal() as session:
            async with session.begin():
                await session.execute(text("SET TRANSACTION READ ONLY"))
                for repository, questions in questions_by_repository.items():
                    rankings: dict[str, Any] = {}
                    for question in questions:
                        question_id = str(question["id"])
                        results, guard = await _retrieve(
                            session,
                            repository_ids[repository],
                            question,
                            chunks_by_repository[repository],
                            document_vectors,
                            query_vectors[str(question["question"])],
                        )
                        rankings[question_id] = (results, guard)
                    _ranks, per_question = _question_rankings(questions, rankings)
                    candidate_per_question_by_repository[repository] = per_question
                    candidate_rank_lists.extend(
                        per_question[str(question["id"])]["rank"]
                        for question in questions
                        if question.get("category") in ANSWERABLE_CATEGORIES
                    )

        candidate_by_repository: dict[str, dict[str, Any]] = {}
        candidate_guard_by_repository: dict[str, list[bool]] = {}
        for repository, questions in questions_by_repository.items():
            qdata = candidate_per_question_by_repository[repository]
            repo_metrics, repo_guard = _per_repository_summary(
                questions_by_repository={repository: questions},
                per_question=qdata,
            )
            candidate_by_repository[repository] = repo_metrics[repository]
            candidate_guard_by_repository[repository] = repo_guard[repository]

        bootstrap = paired_bootstrap(control_all_ranks, candidate_rank_lists)
        decision = retention_rules(
            control_by_repository,
            candidate_by_repository,
            control_all_ranks,
            candidate_rank_lists,
            bootstrap,
            control_guard_by_repository,
            candidate_guard_by_repository,
        )
        run_path = CACHE_ROOT / model.slug / "embedding-run.json"
        try:
            embedding_run = json.loads(run_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"{model.slug}: embedding timing metadata is missing") from exc
        candidate_reports[model.model_name] = {
            "model": model.model_name,
            "dimensions": model.dimensions,
            "registry_size": model.registry_size,
            "license": model.license,
            "network_need": "model download only",
            "per_repository": candidate_by_repository,
            "pooled": summarize_ranks(candidate_rank_lists),
            "vector_distances": _distance_summary(
                questions_by_repository,
                candidate_per_question_by_repository,
            ),
            "guard_false_accepts_by_repository": {
                repository: sum(decisions)
                for repository, decisions in candidate_guard_by_repository.items()
            },
            "guard_decisions_by_repository": {
                repository: {
                    "accepted": sum(decisions),
                    "refused": len(decisions) - sum(decisions),
                }
                for repository, decisions in candidate_guard_by_repository.items()
            },
            "guard_decision_changes_by_development_ordinal": (
                _guard_change_ordinals(
                    questions_by_repository,
                    control_per_question_by_repository,
                    candidate_per_question_by_repository,
                )
            ),
            "top5_test_file_share": _test_share(candidate_per_question_by_repository),
            "bootstrap": bootstrap,
            "retention": decision,
            "embedding": embedding_run,
        }

    report = {
        "experiment_version": EXPERIMENT_VERSION,
        "selection_split": "development",
        "protocol_commit": _protocol_commit_hash(),
        "control": {
            "model": CONTROL_MODEL,
            "dimensions": CONTROL_DIMENSIONS,
            "per_repository": control_by_repository,
            "pooled": control_metrics,
            "vector_distances": control_distance_by_category,
            "guard_false_accepts_by_repository": {
                repository: sum(decisions)
                for repository, decisions in control_guard_by_repository.items()
            },
            "guard_decisions_by_repository": {
                repository: {
                    "accepted": sum(decisions),
                    "refused": len(decisions) - sum(decisions),
                }
                for repository, decisions in control_guard_by_repository.items()
            },
            "top5_test_file_share": control_test_share,
        },
        "control_equivalence": {
            "identical_answerable_development_ranks": identical,
            "expected_answerable_development_ranks": DEVELOPMENT_ANSWERABLE_COUNT,
        },
        "candidates": candidate_reports,
        "limits": [
            "33 answerable and 15 unanswerable development questions across "
            "three small repositories.",
            "No held-out questions, labels, retrieval results, or vectors were read or used.",
            "The 0.5 guard threshold is calibrated to Gemini and is not recalibrated "
            "for candidates.",
            "The two comparisons have no multiplicity correction; no adoption is automatic.",
        ],
    }
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    RESULTS_NOTE_PATH.write_text(_render_report(report), encoding="utf-8")
    print(_render_report(report), end="")
    print(f"Aggregate-only JSON: {RESULTS_JSON_PATH.relative_to(ROOT)}")
    print(f"Results note: {RESULTS_NOTE_PATH.relative_to(ROOT)}")
    return 0


def _distance_summary(
    questions_by_repository: dict[str, list[dict[str, Any]]],
    per_question_by_repository: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    grouped: dict[str, list[float]] = {"answerable": [], "unanswerable": []}
    for repository, questions in questions_by_repository.items():
        for question in questions:
            category = (
                "answerable"
                if question.get("category") in ANSWERABLE_CATEGORIES
                else "unanswerable"
            )
            distance = per_question_by_repository[repository][
                str(question["id"])
            ]["distance"]
            if distance is not None:
                grouped[category].append(float(distance))
    return {category: summarize_distances(values) for category, values in grouped.items()}


def _test_share(
    per_question_by_repository: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, int | float]:
    values = [
        value
        for per_question in per_question_by_repository.values()
        for value in per_question.values()
    ]
    test_count = sum(value["top5_test_count"] for value in values)
    result_count = sum(value["top5_count"] for value in values)
    return {
        "test_file_results": test_count,
        "top5_results": result_count,
        "share": test_count / result_count if result_count else 0.0,
    }


def _guard_change_ordinals(
    questions_by_repository: dict[str, list[dict[str, Any]]],
    control_by_repository: dict[str, dict[str, dict[str, Any]]],
    candidate_by_repository: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, list[int]]:
    changes: dict[str, list[int]] = {}
    for repository, questions in questions_by_repository.items():
        ordinal = 0
        changed: list[int] = []
        for question in questions:
            if question.get("category") in ANSWERABLE_CATEGORIES:
                continue
            ordinal += 1
            question_id = str(question["id"])
            if (
                control_by_repository[repository][question_id]["guard_accept"]
                != candidate_by_repository[repository][question_id]["guard_accept"]
            ):
                changed.append(ordinal)
        changes[repository] = changed
    return changes


def _render_report(report: dict[str, Any]) -> str:
    lines = [
        "# Local embedding-model comparison results",
        "",
        "Protocol: [item 18c local embedding comparison]"
        "(../architecture-review/14-local-embedding-protocol.md).",
        "",
        "## Method and limits",
        "",
        "The registered control and candidates were evaluated on development data only. "
        "No held-out question, label, retrieval result, or vector was read or used. The "
        "question and baseline records were selected with the existing development-only "
        "split helper; fixture JSON containing all question vectors was not deserialized. "
        "Only development Gemini query vectors were loaded by text hash, and document "
        "vectors were read from the named evaluation repositories. The control evaluator "
        "matched all 33 answerable development baseline ranks before candidate metrics "
        "were calculated.",
        "",
        "The paired bootstrap uses seed 20261031, 10,000 resamples, and linear-interpolated "
        "95% endpoints. The exact sign test is descriptive only. The guard threshold remains "
        "0.5; its calibration is Gemini-specific. The two candidate comparisons have no "
        "multiplicity correction, and no model is adopted automatically.",
        "",
        "One rank change is approximately 0.015 pooled MRR. Results cover only 33 answerable "
        "and 15 unanswerable questions across three small, single-author repositories. "
        "Local inference makes no provider API calls or provider usage charges; model "
        "downloads are the only network requirement.",
        "",
        "## Retrieval results",
        "",
        "| Model | Dimensions | Pooled MRR | Hit@1 | Hit@3 | Hit@5 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    control = report["control"]["pooled"]
    lines.append(
        f"| Gemini control | 768 | {control['mrr']:.4f} | {control['hit_at_1']} | "
        f"{control['hit_at_3']} | {control['hit_at_5']} |"
    )
    for model in report["candidates"].values():
        metrics = model["pooled"]
        lines.append(
            f"| `{model['model']}` | {model['dimensions']} | {metrics['mrr']:.4f} | "
            f"{metrics['hit_at_1']} | {metrics['hit_at_3']} | {metrics['hit_at_5']} |"
        )
    lines.extend(
        [
            "",
            "### Control per repository",
            "",
            "| Repository | MRR | Hit@1 | Hit@3 | Hit@5 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for repository, metrics in report["control"]["per_repository"].items():
        lines.append(
            f"| {repository} | {metrics['mrr']:.4f} | {metrics['hit_at_1']} | "
            f"{metrics['hit_at_3']} | {metrics['hit_at_5']} |"
        )
    lines.extend(["", "## Candidate retention rules", ""])
    for candidate in report["candidates"].values():
        lines.extend(
            [
                f"### `{candidate['model']}`",
                "",
                "| Rule | Result |",
                "|---|---|",
            ]
        )
        for rule, passed in candidate["retention"]["rules"].items():
            lines.append(f"| {rule} | {'PASS' if passed else 'FAIL'} |")
        lines.extend(
            [
                "",
                f"- Outcome: **{candidate['retention']['outcome']}**",
                f"- MRR delta vs control: {candidate['retention']['mrr_delta']:.4f}",
                f"- Paired bootstrap 95% interval: "
                f"[{candidate['bootstrap']['lower']:.4f}, "
                f"{candidate['bootstrap']['upper']:.4f}]",
                f"- Exact sign test (descriptive): "
                f"p={candidate['bootstrap']['sign_test_p_value']:.4f}",
                f"- Model size: {candidate['registry_size']}; license: "
                f"{candidate['license']}; network need: {candidate['network_need']}",
                f"- Mean CPU embedding time: "
                f"{_format_seconds(candidate['embedding']['mean_seconds_per_unique_document'])} "
                f"per unique development chunk/document and "
                f"{_format_seconds(candidate['embedding']['mean_seconds_per_unique_query'])} "
                "per unique development query (duplicate exact texts reuse a cached vector).",
                f"- CPU runtime: {candidate['embedding']['cpu']} "
                f"({candidate['embedding']['logical_cpu_count']} logical CPUs; "
                f"{candidate['embedding']['execution_provider']}).",
                f"- Top-five test-file share: "
                f"{candidate['top5_test_file_share']['share']:.4%}.",
                "",
                "| Repository | MRR | Hit@1 | Hit@3 | Hit@5 |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for repository, metrics in candidate["per_repository"].items():
            lines.append(
                f"| {repository} | {metrics['mrr']:.4f} | {metrics['hit_at_1']} | "
                f"{metrics['hit_at_3']} | {metrics['hit_at_5']} |"
            )
        lines.extend(["", "Vector distance distributions (model-specific, not comparable):", ""])
        lines.extend(_render_distance_table(candidate["vector_distances"]))
        lines.extend(
            [
                "",
                "Per-repository unanswerable false accepts: "
                + ", ".join(
                    f"{repository}={count}"
                    for repository, count in candidate[
                        "guard_false_accepts_by_repository"
                    ].items()
                )
                + ".",
                "Per-repository unanswerable guard decisions (accepted/refused): "
                + ", ".join(
                    f"{repository}={values['accepted']}/{values['refused']}"
                    for repository, values in candidate[
                        "guard_decisions_by_repository"
                    ].items()
                )
                + ".",
                "Development ordinals whose unanswerable guard decisions changed: "
                + "; ".join(
                    f"{repository}={ordinals or 'none'}"
                    for repository, ordinals in candidate[
                        "guard_decision_changes_by_development_ordinal"
                    ].items()
                )
                + ".",
                "",
            ]
        )
    lines.extend(
        [
            "## Control distances and limitations",
            "",
            "Control vector-distance distributions:",
            "",
        ]
    )
    lines.extend(_render_distance_table(report["control"]["vector_distances"]))
    lines.extend(
        [
            "",
            "Control unanswerable guard decisions (accepted/refused): "
            + ", ".join(
                f"{repository}={values['accepted']}/{values['refused']}"
                for repository, values in report["control"][
                    "guard_decisions_by_repository"
                ].items()
            )
            + ".",
            f"Control top-five test-file share: "
            f"{report['control']['top5_test_file_share']['share']:.4%}.",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "The models and distances have not been evaluated on held-out data. Three small, "
            "single-author repositories and 48 development questions are insufficient to "
            "establish general performance. Candidate guard thresholds remain unvalidated; "
            "the 0.5 threshold was calibrated to Gemini. A passing candidate requires a "
            "separately registered held-out validation, a per-model guard threshold under "
            "item 3b, and a production migration plan before any adoption.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_gate_failure(report: dict[str, Any]) -> str:
    equivalence = report["control_equivalence"]
    lines = [
        "# Local embedding-model comparison results",
        "",
        "Protocol: [item 18c local embedding comparison]"
        "(../architecture-review/14-local-embedding-protocol.md).",
        "",
        "## Evaluator-equivalence gate",
        "",
        f"Control evaluator agreement: "
        f"{equivalence['identical_answerable_development_ranks']}/"
        f"{equivalence['expected_answerable_development_ranks']} development answerable ranks.",
        "",
        "Candidate retrieval metrics were not calculated because the control path did not "
        "match the committed development baseline exactly. Per the preregistered protocol, "
        "both candidate evaluations are stopped; no retention outcome is assigned.",
        "",
        "| Repository | Development ordinal | Baseline label rank | Evaluator label rank |",
        "|---|---:|---:|---:|",
    ]
    for difference in equivalence["differences"]:
        lines.append(
            f"| {difference['repository']} | {difference['development_ordinal']} | "
            f"{difference['baseline_rank']} | {difference['control_rank']} |"
        )
    lines.extend(
        [
            "",
            "No held-out questions, labels, retrieval results, or vectors were used.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_distance_table(summary: dict[str, Any]) -> list[str]:
    lines = [
        "| Question group | Count | Minimum | Median | Maximum |",
        "|---|---:|---:|---:|---:|",
    ]
    for group, values in summary.items():
        lines.append(
            f"| {group} | {values['count']} | {_format_number(values['minimum'])} | "
            f"{_format_number(values['median'])} | {_format_number(values['maximum'])} |"
        )
    return lines


def _format_number(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.6f}"


def _format_seconds(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 1000:.3f} ms"


def _protocol_commit_hash() -> str:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "ea62d34"],
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("plan", "embed", "evaluate"),
        help="count development inputs, embed local models, or evaluate cached vectors",
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument(
        "--threads",
        type=_positive_int,
        default=DEFAULT_EMBED_THREADS,
        help="logical CPU threads per ONNX session (default: os.cpu_count())",
    )
    parser.add_argument(
        "--batch-size",
        type=_positive_int,
        default=EMBED_BATCH_SIZE,
        help="number of texts per embedding batch (default: 8)",
    )
    return parser


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            return asyncio.run(_plan(args.manifest))
        if args.command == "embed":
            return asyncio.run(_embed(args.manifest, args.threads, args.batch_size))
        return asyncio.run(_evaluate(args.manifest))
    except (OSError, RuntimeError, ValueError, SQLAlchemyError) as exc:
        if isinstance(exc, SQLAlchemyError):
            detail = f"database operation failed ({type(exc).__name__})"
        else:
            detail = str(exc)
        print(f"Error: {detail}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
