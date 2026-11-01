"""Run the Phase 8 evaluation without changing production pipeline behavior."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.db.session import AsyncSessionLocal
from app.investigation.confidence import MAX_CLEAR_VECTOR_DISTANCE, MIN_CLEAR_RRF_SCORE
from app.investigation.generation import GEMINI_GENERATION_MODEL
from app.investigation.guard import (
    MAX_ACCEPTABLE_VECTOR_DISTANCE,
    MIN_ACCEPTABLE_RRF_SCORE,
    evaluate_evidence_sufficiency,
)
from app.investigation.prompt import SYSTEM_INSTRUCTION
from app.providers import gemini as gemini_provider
from app.providers.usage import usage_operation
from app.retrieval.fulltext_search import search_fulltext
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.vector_search import search_vector
from scripts import embed_chunks, investigate
from scripts.ingest_repo import iter_python_files

from .chunk_strategies import (
    DEFAULT_STRATEGY,
    EVALUATION_REPOSITORIES,
    expected_chunk_ranges,
    get_strategy,
    resolve_evaluation_repository,
    resolve_split,
)
from .corpus import export_snapshot
from .golden import load_golden_set, validate_golden_set, validate_index_labels
from .manifest import (
    MANIFEST_PATH,
    load_manifest,
    questions_for_split,
    repository_entry,
)
from .metrics import (
    abstention_kind,
    answer_screen,
    best_score_distribution,
    citation_summary,
    classify_outcome_v2,
    distance_sweep,
    first_relevant_rank,
    guard_confusion,
    guard_diagnostics,
    is_refused,
    is_relevant,
    latency_summary,
    retrieval_summary,
    token_summary,
)

ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ROOT = ROOT / "evaluation"
CACHE_ROOT = EVALUATION_ROOT / "cache"
RESULTS_ROOT = EVALUATION_ROOT / "results"
LIMIT = 5
MIN_API_DELAY_SECONDS = 1.5
MAX_GENERATION_HTTP_CALLS = 119


def build_run_metadata(
    *,
    run_id: str,
    started_at: str,
    finished_at: str,
    corpus_sha: str,
    code_sha: str,
    code_dirty: bool,
    code_untracked_files: int,
    golden_set_path: Path | str = (
        EVALUATION_ROOT / "repos" / "incidentweave" / "questions.json"
    ),
    models: dict[str, str] | None = None,
    limit: int = LIMIT,
    passes: int = 2,
    generation_config: str = "provider default (none set)",
    strategy: str = DEFAULT_STRATEGY,
    evaluation_repository: str | None = None,
    repo_id: str = "incidentweave",
    split: str = "development",
    confirm_frozen_heldout: bool = False,
) -> dict[str, Any]:
    """Build the stable metadata block used to identify a report run."""

    selected_strategy = get_strategy(strategy)
    evaluation_repository = resolve_evaluation_repository(
        evaluation_repository,
        selected_strategy.name,
    )
    golden_path = Path(golden_set_path)
    golden_data = load_golden_set(golden_path)
    prompt_sha256 = hashlib.sha256(SYSTEM_INSTRUCTION.encode("utf-8")).hexdigest()
    golden_set_sha256 = hashlib.sha256(golden_path.read_bytes()).hexdigest()
    payload = {
        "pinned_sha": corpus_sha,
        "golden_set_sha256": golden_set_sha256,
        "golden_review_status": golden_data.get("review_status"),
        "models": models or {
            "embedding": embed_chunks.GEMINI_MODEL,
            "generation": GEMINI_GENERATION_MODEL,
        },
        "limit": limit,
        "thresholds": {
            "guard_rrf": MIN_ACCEPTABLE_RRF_SCORE,
            "guard_vector": MAX_ACCEPTABLE_VECTOR_DISTANCE,
            "calibration_rrf": MIN_CLEAR_RRF_SCORE,
            "calibration_vector": MAX_CLEAR_VECTOR_DISTANCE,
        },
        "prompt_sha256": prompt_sha256,
        "generation_config": generation_config,
        "passes": passes,
        "strategy": selected_strategy.name,
        "chunk_size": selected_strategy.chunk_size,
        "overlap": selected_strategy.overlap,
        "evaluation_repository": evaluation_repository,
        "repo_id": repo_id,
        "split": split,
        "confirm_frozen_heldout": confirm_frozen_heldout,
    }
    return {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "date": started_at,
        "pinned_sha": corpus_sha,
        "code_sha": code_sha,
        "code_dirty": code_dirty,
        "code_untracked_files": code_untracked_files,
        "golden_set_sha256": golden_set_sha256,
        "golden_review_status": golden_data.get("review_status"),
        "models": payload["models"],
        "limit": limit,
        "thresholds": payload["thresholds"],
        "prompt_sha256": prompt_sha256,
        "generation_config": generation_config,
        "passes": passes,
        "strategy": selected_strategy.name,
        "chunk_size": selected_strategy.chunk_size,
        "overlap": selected_strategy.overlap,
        "evaluation_repository": evaluation_repository,
        "repo_id": repo_id,
        "split": split,
        "confirm_frozen_heldout": confirm_frozen_heldout,
        "config_sha256": hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def load_key_without_logging() -> None:
    """Load only the Gemini key into the process environment, never print it."""

    if os.getenv("GEMINI_API_KEY"):
        return
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = raw_line.partition("=")
        if separator and key.strip() == "GEMINI_API_KEY":
            os.environ["GEMINI_API_KEY"] = value.strip().strip('"').strip("'")
            return


async def cached_embedding(question: str) -> list[float]:
    """Load or create one query embedding cache entry without logging secrets."""

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(question.encode("utf-8")).hexdigest()
    cache_path = CACHE_ROOT / f"{cache_key}.json"
    if cache_path.is_file():
        return [float(value) for value in json.loads(cache_path.read_text())]
    load_key_without_logging()
    values = await embed_chunks.embed_text(question)
    cache_path.write_text(json.dumps(values), encoding="utf-8")
    await asyncio.sleep(MIN_API_DELAY_SECONDS)
    return values


async def _counted_send_once(
    client: Any,
    url: str,
    payload: Any,
    *,
    original_send_once: Any,
    generation_budget: dict[str, int],
    call_stats: dict[str, int],
    state: dict[str, float],
) -> Any:
    """Count, budget, and throttle generation attempts without counting embeddings."""

    if ":generateContent" not in url:
        return await original_send_once(client, url, payload)

    try:
        now = time.monotonic()
        last_call_at = state.get("last_call_at")
        if last_call_at is not None:
            delay = MIN_API_DELAY_SECONDS - (now - last_call_at)
            if delay > 0:
                await asyncio.sleep(delay)
                state["question_throttle_wait_ms"] = (
                    state.get("question_throttle_wait_ms", 0.0) + round(delay * 1000)
                )
        if generation_budget["http_calls"] >= MAX_GENERATION_HTTP_CALLS:
            raise RuntimeError("Phase 8 generation HTTP call budget reached")
        generation_budget["http_calls"] += 1
        call_stats["http_calls"] += 1
        response = await original_send_once(client, url, payload)
        if response.status_code == 429:
            generation_budget["http_429_responses"] += 1
            call_stats["http_429_responses"] += 1
        return response
    finally:
        state["last_call_at"] = time.monotonic()


def _json_safe(value: object) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return str(value)


def safe_error_text(exc: Exception) -> str:
    """Format evaluation errors without ever persisting the API-key value."""

    message = f"{type(exc).__name__}: {exc}"
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        message = message.replace(api_key, "[REDACTED]")
    return message


def snapshot_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def build_run_id(
    started_at: datetime,
    code_sha: str,
    strategy: str = DEFAULT_STRATEGY,
    split: str = "development",
) -> str:
    """Build a run identifier that distinguishes chunking strategies."""

    selected_strategy = get_strategy(strategy)
    run_id = (
        f"{started_at.strftime('%Y%m%dT%H%M%SZ')}-"
        f"{code_sha[:7]}-{selected_strategy.name}"
    )
    return run_id if split == "development" else f"{run_id}-{split}"


def resolve_corpus_sha(data: dict[str, Any]) -> str:
    """Return the golden-set pinned corpus SHA, rejecting missing or empty values."""

    pinned_sha = data.get("pinned_sha")
    if not isinstance(pinned_sha, str) or not pinned_sha:
        raise ValueError("pinned_sha must be a non-empty string")
    return pinned_sha


async def inventory() -> dict[str, int]:
    from sqlalchemy import func, select

    from app.db.models import Chunk, Repository

    async with AsyncSessionLocal() as session:
        rows = (
            await session.execute(
                select(Repository.name, func.count(Chunk.id))
                .outerjoin(Chunk)
                .group_by(Repository.id, Repository.name)
                .order_by(Repository.name)
            )
        ).all()
    return {name: int(count) for name, count in rows}


def ensure_non_eval_inventory_unchanged(
    before: dict[str, int],
    after: dict[str, int],
    *,
    selected_repository: str,
) -> None:
    """Reject inventory changes outside the selected evaluation repository."""

    if selected_repository not in EVALUATION_REPOSITORIES:
        raise ValueError(f"Evaluation repository {selected_repository!r} is not allowed")

    for name in sorted(set(before) | set(after)):
        if name == selected_repository:
            continue
        before_count = before.get(name, 0)
        after_count = after.get(name, 0)
        if before_count != after_count and before_count == 0:
            raise RuntimeError(
                f"Unexpected repository created: {name!r} "
                f"(chunks={after_count})"
            )
        if before_count != after_count and after_count == 0:
            raise RuntimeError(
                f"Unexpected repository disappeared: {name!r} "
                f"(chunks before={before_count})"
            )
        if before_count != after_count:
            raise RuntimeError(
                f"Unexpected inventory change for repository {name!r}: "
                f"before={before_count}, after={after_count}"
            )


async def setup_eval_corpus(
    snapshot_root: Path,
    *,
    repository_name: str | None = None,
    strategy: str = DEFAULT_STRATEGY,
) -> tuple[int, int]:
    selected_strategy = get_strategy(strategy)
    repository_name = resolve_evaluation_repository(
        repository_name,
        selected_strategy.name,
    )

    snapshot_chunks = []
    snapshot_files = sorted(iter_python_files(snapshot_root))
    for file_path in snapshot_files:
        relative_path = file_path.relative_to(snapshot_root).as_posix()
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for start_index, end_index in expected_chunk_ranges(
            lines,
            selected_strategy.name,
        ):
            content = "\n".join(lines[start_index:end_index])
            if content.strip():
                snapshot_chunks.append(
                    (relative_path, start_index + 1, end_index, content)
                )

    from sqlalchemy import select

    from app.db.models import Chunk, Repository

    created_repository = False
    should_embed = False
    expected_to_embed = 0
    selected_repository_id: int | None = None
    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
        if repository is None:
            repository = Repository(name=repository_name)
            session.add(repository)
            await session.flush()
            selected_repository_id = repository.id
            session.add_all(
                [
                    Chunk(
                        repository_id=repository.id,
                        content=content,
                        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                        file_path=relative_path,
                        file_type="python",
                        document_type="code",
                        line_start=line_start,
                        line_end=line_end,
                        function_name=None,
                        class_name=None,
                        symbol=None,
                    )
                    for relative_path, line_start, line_end, content in snapshot_chunks
                ]
            )
            await session.commit()
            created_repository = True
            should_embed = True
        else:
            selected_repository_id = repository.id
            rows = (
                await session.execute(
                    select(
                        Chunk.file_path,
                        Chunk.line_start,
                        Chunk.line_end,
                        Chunk.content,
                        Chunk.embedding,
                    )
                    .where(Chunk.repository_id == repository.id)
                    .order_by(Chunk.file_path, Chunk.line_start, Chunk.id)
                )
            ).all()
            current_chunks = [tuple(row[:4]) for row in rows]
            if sorted(current_chunks) != sorted(snapshot_chunks):
                raise RuntimeError(
                    f"Existing evaluation repository {repository_name!r} does not "
                    "match the selected snapshot and chunking strategy; refusing "
                    "to replace existing chunks."
                )
            missing_embeddings = sum(row[4] is None for row in rows)
            if not missing_embeddings:
                return len(snapshot_files), len(snapshot_chunks)
            expected_to_embed = missing_embeddings
            should_embed = True

    if should_embed:
        embedded, failed, skipped = await embed_chunks.embed_repository_chunks(
            repository_name
        )
        expected_to_embed = len(snapshot_chunks) if created_repository else expected_to_embed
        expected_skipped = len(snapshot_chunks) - expected_to_embed

        from sqlalchemy import func, select

        async with AsyncSessionLocal() as session:
            remaining_null_embeddings = await session.scalar(
                select(func.count(Chunk.id)).where(
                    Chunk.repository_id == selected_repository_id,
                    Chunk.embedding.is_(None),
                )
            )
        if remaining_null_embeddings:
            raise RuntimeError(
                f"Evaluation repository {repository_name!r} still has "
                f"{remaining_null_embeddings} chunks without embeddings."
            )
        if failed or skipped != expected_skipped or embedded != expected_to_embed:
            raise RuntimeError(
                "Evaluation embedding counts do not match the selected corpus: "
                f"expected_embedded={expected_to_embed}, embedded={embedded}, "
                f"expected_skipped={expected_skipped}, skipped={skipped}, "
                f"failed={failed}"
            )
    return len(snapshot_files), len(snapshot_chunks)


async def validate_eval_index(
    questions: list[dict[str, Any]],
    *,
    repository_name: str | None = None,
    strategy: str = DEFAULT_STRATEGY,
) -> list[str]:
    repository_name = resolve_evaluation_repository(repository_name, strategy)
    from sqlalchemy import select

    from app.db.models import Chunk, Repository

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
        if repository is None:
            return [f"{repository_name} repository is missing"]
        rows = (
            await session.execute(
                select(Chunk.file_path, Chunk.content).where(
                    Chunk.repository_id == repository.id
                )
            )
        ).all()
    indexed_chunks = [
        {"file_path": file_path, "content": content}
        for file_path, content in rows
    ]
    return validate_index_labels(questions, indexed_chunks)


async def retrieval_records(
    questions: list[dict[str, Any]],
    *,
    repository_name: str | None = None,
    strategy: str = DEFAULT_STRATEGY,
) -> list[dict[str, Any]]:
    repository_name = resolve_evaluation_repository(repository_name, strategy)
    from sqlalchemy import select

    from app.db.models import Repository

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
        if repository is None:
            raise RuntimeError(f"Evaluation repository was not created: {repository_name}")
        records = []
        for question in questions:
            embedding = await cached_embedding(question["question"])
            vector = await search_vector(session, repository.id, embedding, limit=LIMIT)
            fulltext = await search_fulltext(
                session, repository.id, question["question"], limit=LIMIT
            )
            hybrid = await hybrid_search(
                session,
                repository.id,
                question["question"],
                embedding,
                limit=LIMIT,
            )
            records.append(
                {
                    "id": question["id"],
                    "category": question["category"],
                    "question": question["question"],
                    "relevant": question.get("relevant", []),
                    "vector": vector,
                    "fulltext": fulltext,
                    "hybrid": hybrid,
                    "evidence_check": evaluate_evidence_sufficiency(hybrid),
                }
            )
    return records


async def run_pipeline_once(
    questions: list[dict[str, Any]],
    snapshot_root: Path,
    run_name: str,
    generation_budget: dict[str, int],
    *,
    repository_name: str | None = None,
    strategy: str = DEFAULT_STRATEGY,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Run the shipped CLI pipeline function with persistence disabled."""

    repository_name = resolve_evaluation_repository(repository_name, strategy)
    original_embed = investigate.embed_text
    original_calibrator = investigate.calibrate_confidence
    original_send_once = gemini_provider.send_once
    calibration: dict[str, str] = {}
    call_stats = {"http_calls": 0, "http_429_responses": 0}
    request_state = {"question_throttle_wait_ms": 0.0}

    def capture_calibration(
        raw_confidence: str,
        best_rrf_score: float | None,
        best_vector_score: float | None,
    ) -> tuple[str, str]:
        calibrated, note = original_calibrator(
            raw_confidence, best_rrf_score, best_vector_score
        )
        calibration.update(
            raw_confidence=raw_confidence,
            calibrated_confidence=calibrated,
        )
        return calibrated, note

    async def counted_send_once(client: Any, url: str, payload: Any) -> Any:
        return await _counted_send_once(
            client,
            url,
            payload,
            original_send_once=original_send_once,
            generation_budget=generation_budget,
            call_stats=call_stats,
            state=request_state,
        )

    investigate.embed_text = cached_embedding
    investigate.calibrate_confidence = capture_calibration
    gemini_provider.send_once = counted_send_once
    try:
        records = []
        request_state["question_throttle_wait_ms"] = 0
        for question in questions:
            calibration.clear()
            start_http_calls = call_stats["http_calls"]
            request_state["question_throttle_wait_ms"] = 0
            start_wall = time.perf_counter()
            try:
                with usage_operation("evaluation"):
                    result = await investigate.investigate_repository(
                        repository_name,
                        question["question"],
                        limit=LIMIT,
                        persist=False,
                        temperature=0,
                    )
                diagnosis = str(result.get("diagnosis") or "")
                cited_chunk_ids = result.get("cited_chunk_ids", [])
                retrieval_results = result.get("retrieval_results", [])
                retrieval_by_id = {
                    str(item.get("id")): item
                    for item in retrieval_results
                    if isinstance(item, dict) and item.get("id") is not None
                }
                labels = question.get("relevant", [])
                cited_relevance = []
                for cited_id in cited_chunk_ids:
                    cited_chunk = retrieval_by_id.get(str(cited_id))
                    cited_relevance.append(
                        {
                            "id": str(cited_id),
                            "found_in_retrieval_results": cited_chunk is not None,
                            "relevant": bool(
                                cited_chunk is not None
                                and is_relevant(cited_chunk, labels)
                            ),
                        }
                    )
                generation_latency_ms = result.get("latency_ms")
                generation_trace = result.get("generation_trace")
                generation_ran = generation_latency_ms is not None
                abstained = abstention_kind(
                    diagnosis,
                    generation_ran,
                    (
                        generation_trace.get("raw_text")
                        if isinstance(generation_trace, dict)
                        else None
                    ),
                )
                labeled_rank = (
                    first_relevant_rank(retrieval_results, labels)
                    if not question["category"].startswith("unanswerable")
                    else None
                )
                labeled_chunk_in_context = labeled_rank is not None
                screen_pass = None
                if not question["category"].startswith("unanswerable") and not abstained:
                    screen_pass = answer_screen(diagnosis, question.get("must_mention", []))
                records.append(
                    {
                        "id": question["id"],
                        "category": question["category"],
                        "question": question["question"],
                        "relevant": question.get("relevant", []),
                        "must_mention": question.get("must_mention", []),
                        "diagnosis": diagnosis,
                        "confidence_raw": calibration.get("raw_confidence"),
                        "confidence": result.get("confidence"),
                        "confidence_calibrated_value": calibration.get(
                            "calibrated_confidence"
                        ),
                        "confidence_calibrated": result.get("confidence_calibrated", False),
                        "calibration_note": result.get("calibration_note", ""),
                        "cited_chunk_ids": cited_chunk_ids,
                        "cited_chunk_relevance": cited_relevance,
                        "submitted_citation_count": result.get(
                            "submitted_citation_count", 0
                        ),
                        "valid_citation_count": result.get("valid_citation_count", 0),
                        "claims": result.get("claims", []),
                        "uncertainty_note": result.get("uncertainty_note", ""),
                        "retrieval_results": retrieval_results,
                        "evidence_check": result.get("evidence_check", {}),
                        "retry_used": result.get("retry_used", False),
                        "evidence_source": result.get("evidence_source", "hybrid"),
                        "tool_calls": result.get("tool_calls", []),
                        "refused": is_refused(diagnosis, generation_latency_ms),
                        "generation_ran": generation_ran,
                        "generation_trace": generation_trace,
                        "wall_ms": round((time.perf_counter() - start_wall) * 1000),
                        "throttle_wait_ms": request_state["question_throttle_wait_ms"],
                        "generation_ms": (
                            None
                            if generation_latency_ms is None
                            else max(
                                0,
                                int(generation_latency_ms)
                                - int(request_state["question_throttle_wait_ms"]),
                            )
                        ),
                        "generation_http_calls": call_stats["http_calls"] - start_http_calls,
                        "guard_refused": is_refused(diagnosis, generation_latency_ms),
                        "abstention_kind": abstained,
                        "labeled_rank": labeled_rank,
                        "labeled_chunk_in_context": labeled_chunk_in_context,
                        "screen_pass": screen_pass,
                        "error": None,
                        "outcome": "pending",
                    }
                )
            except Exception as exc:
                records.append(
                    {
                        "id": question["id"],
                        "category": question["category"],
                        "question": question["question"],
                        "relevant": question.get("relevant", []),
                        "must_mention": question.get("must_mention", []),
                        "diagnosis": "",
                        "confidence_raw": None,
                        "confidence": None,
                        "confidence_calibrated_value": None,
                        "confidence_calibrated": False,
                        "calibration_note": "",
                        "cited_chunk_ids": [],
                        "cited_chunk_relevance": [],
                        "submitted_citation_count": 0,
                        "valid_citation_count": 0,
                        "claims": [],
                        "uncertainty_note": "",
                        "retrieval_results": [],
                        "evidence_check": {},
                        "retry_used": False,
                        "evidence_source": "hybrid",
                        "tool_calls": [],
                        "refused": False,
                        "generation_ran": False,
                        "generation_trace": None,
                        "wall_ms": round((time.perf_counter() - start_wall) * 1000),
                        "throttle_wait_ms": request_state["question_throttle_wait_ms"],
                        "generation_ms": None,
                        "generation_http_calls": call_stats["http_calls"] - start_http_calls,
                        "guard_refused": False,
                        "abstention_kind": None,
                        "labeled_rank": None,
                        "labeled_chunk_in_context": None,
                        "screen_pass": None,
                        "error": safe_error_text(exc),
                        "outcome": "error",
                    }
                )
            time.sleep(MIN_API_DELAY_SECONDS)
        return records, call_stats
    finally:
        investigate.embed_text = original_embed
        investigate.calibrate_confidence = original_calibrator
        gemini_provider.send_once = original_send_once


def classify_outcomes(records: list[dict[str, Any]], questions: list[dict[str, Any]]) -> None:
    questions_by_id = {question["id"]: question for question in questions}
    for record in records:
        if record["error"]:
            continue
        question = questions_by_id[record["id"]]
        if question["category"].startswith("unanswerable"):
            record["outcome"] = "refused" if record["refused"] else "falsely answered"
        elif record["refused"]:
            record["outcome"] = "false refusal"
        else:
            record["outcome"] = (
                "correct"
                if answer_screen(record["diagnosis"], question.get("must_mention", []))
                else "wrong-or-incomplete"
            )


def classify_outcome_v2_for_records(records: list[dict[str, Any]]) -> None:
    """Set the additive outcome_v2 field while preserving the legacy outcome values."""

    for record in records:
        if record.get("error"):
            record["outcome_v2"] = "error"
            continue
        category = str(record.get("category") or "")
        guard_refused = bool(record.get("refused"))
        abstained = record.get("abstention_kind") is not None
        screen_pass = record.get("screen_pass")
        labeled_in_context = record.get("labeled_chunk_in_context")
        record["outcome_v2"] = classify_outcome_v2(
            category,
            record.get("error"),
            guard_refused,
            abstained,
            labeled_in_context,
            screen_pass,
        )


def summarize_run(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    outcome_v2_counts: dict[str, int] = {}
    for record in records:
        counts[record["outcome"]] = counts.get(record["outcome"], 0) + 1
        outcome_v2 = record.get("outcome_v2")
        if outcome_v2 is not None:
            outcome_v2_counts[outcome_v2] = outcome_v2_counts.get(outcome_v2, 0) + 1
    answered = [
        record
        for record in records
        if record.get("generation_ran")
        and not record.get("error")
        and record.get("diagnosis") != "INSUFFICIENT_EVIDENCE"
    ]
    submitted = sum(
        int(record.get("submitted_citation_count") or 0) for record in answered
    )
    valid = sum(int(record.get("valid_citation_count") or 0) for record in answered)
    return {
        "outcome_counts": counts,
        "outcome_v2_counts": outcome_v2_counts,
        "total_records": len(records),
        "citation_validity_rate": valid / submitted if submitted else None,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_safe(value), indent=2), encoding="utf-8")


async def run_evaluation(
    passes: int = 2,
    *,
    strategy: str = DEFAULT_STRATEGY,
    repository_name: str | None = None,
    repo_id: str = "incidentweave",
    split: str = "development",
    confirm_frozen_heldout: bool = False,
) -> dict[str, Any]:
    split = resolve_split(split, confirm_frozen_heldout=confirm_frozen_heldout)
    manifest = load_manifest(MANIFEST_PATH)
    manifest_entry = repository_entry(manifest, repo_id)
    selected_strategy = get_strategy(strategy)
    repository_name = resolve_evaluation_repository(
        repository_name,
        selected_strategy.name,
    )
    load_key_without_logging()
    started = datetime.now(UTC)
    golden_set_path = ROOT / manifest_entry["questions"]["path"]
    data = load_golden_set(golden_set_path)
    corpus_sha = resolve_corpus_sha(data)
    code_sha = snapshot_sha()
    code_dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
    )
    untracked_output = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    code_untracked_files = sum(bool(path) for path in untracked_output.split("\0"))
    snapshot_parent = EVALUATION_ROOT / "_snapshot"
    if snapshot_parent.exists():
        shutil.rmtree(snapshot_parent)
    snapshot_root = export_snapshot(ROOT, corpus_sha, snapshot_parent)
    errors = validate_golden_set(
        data,
        snapshot_root,
        corpus_sha,
        required_review_status=manifest_entry.get(
            "review_status", "pending maintainer review"
        ),
        max_questions_per_file=manifest_entry.get("max_questions_per_file", 3),
    )
    if errors:
        raise ValueError("Golden set validation failed: " + "; ".join(errors))

    before = await inventory()
    files, chunks = await setup_eval_corpus(
        snapshot_root,
        repository_name=repository_name,
        strategy=selected_strategy.name,
    )
    after = await inventory()
    ensure_non_eval_inventory_unchanged(
        before,
        after,
        selected_repository=repository_name,
    )

    questions = questions_for_split(manifest_entry, data["questions"], split)
    index_errors = await validate_eval_index(
        questions,
        repository_name=repository_name,
        strategy=selected_strategy.name,
    )
    if index_errors:
        raise ValueError("Golden-set index validation failed: " + "; ".join(index_errors))
    retrieval = await retrieval_records(
        questions,
        repository_name=repository_name,
        strategy=selected_strategy.name,
    )
    answerable = [not question["category"].startswith("unanswerable") for question in questions]
    answerable_retrieval = [record for record, expected in zip(retrieval, answerable) if expected]
    labels = [record["relevant"] for record in answerable_retrieval]
    retrieval_tables = {}
    for method in ("vector", "fulltext", "hybrid"):
        method_results = [record[method] for record in answerable_retrieval]
        retrieval_tables[method] = retrieval_summary(method_results, labels)
    fulltext_empty = sum(not record["fulltext"] for record in answerable_retrieval)
    direct_records = [record for record in answerable_retrieval if record["category"] == "direct"]
    paraphrased_records = [
        record for record in answerable_retrieval if record["category"] == "paraphrased"
    ]
    split_tables = {}
    for split_name, split_records in {
        "direct": direct_records,
        "paraphrased": paraphrased_records,
    }.items():
        split_labels = [record["relevant"] for record in split_records]
        split_tables[split_name] = {
            method: retrieval_summary(
                [record[method] for record in split_records], split_labels
            )
            for method in ("vector", "fulltext", "hybrid")
        }
    hybrid_checks = [record["evidence_check"] for record in retrieval]
    guard_counts = guard_confusion(
        answerable,
        [bool(check.get("is_sufficient")) for check in hybrid_checks],
    )
    distributions = {
        "answerable_vector": best_score_distribution(
            [check for check, expected in zip(hybrid_checks, answerable) if expected],
            "best_vector_score",
        ),
        "unanswerable_vector": best_score_distribution(
            [check for check, expected in zip(hybrid_checks, answerable) if not expected],
            "best_vector_score",
        ),
        "answerable_rrf": best_score_distribution(
            [check for check, expected in zip(hybrid_checks, answerable) if expected],
            "best_rrf_score",
        ),
        "unanswerable_rrf": best_score_distribution(
            [check for check, expected in zip(hybrid_checks, answerable) if not expected],
            "best_rrf_score",
        ),
    }

    run_results = []
    generation_budget = {"http_calls": 0, "http_429_responses": 0}
    generation_calls_by_run = []
    run_id = build_run_id(started, code_sha, selected_strategy.name, split)
    for index in range(1, passes + 1):
        records, call_stats = await run_pipeline_once(
            questions,
            snapshot_root,
            f"run-{index}",
            generation_budget,
            repository_name=repository_name,
            strategy=selected_strategy.name,
        )
        classify_outcomes(records, questions)
        classify_outcome_v2_for_records(records)
        output_path = RESULTS_ROOT / "runs" / run_id / f"pass-{index}.json"
        write_json(output_path, records)
        run_results.append(records)
        generation_calls_by_run.append(call_stats)

    changed = [
        question["id"]
        for question, first, second in zip(questions, run_results[0], run_results[1])
        if first["outcome"] != second["outcome"]
    ]
    metadata = build_run_metadata(
        run_id=run_id,
        started_at=started.isoformat(),
        finished_at=datetime.now(UTC).isoformat(),
        corpus_sha=corpus_sha,
        code_sha=code_sha,
        code_dirty=code_dirty,
        code_untracked_files=code_untracked_files,
        models={
            "embedding": embed_chunks.GEMINI_MODEL,
            "generation": GEMINI_GENERATION_MODEL,
        },
        limit=LIMIT,
        passes=passes,
        strategy=selected_strategy.name,
        evaluation_repository=repository_name,
        golden_set_path=golden_set_path,
        repo_id=repo_id,
        split=split,
        confirm_frozen_heldout=confirm_frozen_heldout,
        generation_config=(
            "temperature=0; responseMimeType=application/json; "
            "response schema + prompt version grounded-v3"
        ),
    )
    report = {
        **metadata,
        "repository": repository_name,
        "snapshot_files": files,
        "snapshot_chunks": chunks,
        "retrieval_tables": retrieval_tables,
        "retrieval_split_tables": split_tables,
        "fulltext_empty_answerable": fulltext_empty,
        "guard_counts": guard_counts,
        "guard_distributions": distributions,
        "guard_diagnostics": guard_diagnostics(
            [check for check in hybrid_checks if isinstance(check, dict)],
            float(MIN_ACCEPTABLE_RRF_SCORE),
        ),
        "citation_summary": {
            "pass_1": citation_summary(run_results[0]),
            "pass_2": citation_summary(run_results[1]) if len(run_results) > 1 else None,
        },
        "latency_summary": {
            "pass_1": latency_summary(run_results[0]),
            "pass_2": latency_summary(run_results[1]) if len(run_results) > 1 else None,
        },
        "token_summary": {
            "pass_1": token_summary(run_results[0]),
            "pass_2": token_summary(run_results[1]) if len(run_results) > 1 else None,
        },
        "distance_sweep": distance_sweep(
            hybrid_checks,
            answerable,
            float(MIN_ACCEPTABLE_RRF_SCORE),
        ),
        "run_summaries": [summarize_run(records) for records in run_results],
        "outcome_changes": changed,
        "generation_error_count": sum(
            1 for records in run_results for record in records if record["error"]
        ),
        "generation_http_calls": generation_budget["http_calls"],
        "generation_http_429_responses": generation_budget["http_429_responses"],
        "generation_calls_by_run": generation_calls_by_run,
        "calibration_downgrade_count": sum(
            1
            for records in run_results
            for record in records
            if record.get("confidence_raw") == "high"
            and record.get("confidence") != "high"
        ),
        "escalation_counts": {
            "initial_insufficient": sum(
                1
                for records in run_results
                for record in records
                if len(record["tool_calls"]) >= 1
                and record["tool_calls"][0]["outcome"].get("sufficient") is False
            ),
            "retry_recovered": sum(
                1
                for records in run_results
                for record in records
                if any(
                    attempt.get("stage") == "widened_retry"
                    and attempt.get("outcome", {}).get("sufficient") is True
                    for attempt in record["tool_calls"]
                )
            ),
            "grep_attempted": sum(
                1
                for records in run_results
                for record in records
                if any(attempt.get("tool") == "grep_search" for attempt in record["tool_calls"])
            ),
            "grep_recovered": sum(
                1
                for records in run_results
                for record in records
                if any(
                    attempt.get("tool") == "grep_search"
                    and attempt.get("outcome", {}).get("sufficient") is True
                    for attempt in record["tool_calls"]
                )
            ),
        },
        "records": run_results,
        "repository_inventory_before": before,
        "repository_inventory_after": after,
    }
    report_path = RESULTS_ROOT / "runs" / run_id / "report.json"
    write_json(report_path, report)
    return report
