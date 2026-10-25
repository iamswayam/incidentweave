from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from app.db.models import Repository
from app.investigation.parsing import extract_generation_trace
from evaluation.chunk_experiments import (
    DEFAULT_STRATEGY,
    EVALUATION_REPOSITORIES,
    STRATEGY_CHOICES,
    expected_chunk_ranges,
    get_strategy,
    resolve_evaluation_repository,
)
from evaluation.corpus import export_snapshot
from evaluation.golden import load_golden_set, validate_golden_set, validate_index_labels
from evaluation.metrics import (
    abstention_kind,
    answer_screen,
    best_score_distribution,
    citation_summary,
    classify_outcome_v2,
    distance_sweep,
    guard_confusion,
    guard_diagnostics,
    hit_at_k,
    is_refused,
    is_relevant,
    mean_reciprocal_rank,
    retrieval_summary,
    value_distribution,
)
from evaluation.runner import (
    MAX_GENERATION_HTTP_CALLS,
    build_run_id,
    classify_outcome_v2_for_records,
    classify_outcomes,
    ensure_non_eval_inventory_unchanged,
    resolve_corpus_sha,
    run_pipeline_once,
    summarize_run,
)
from scripts import ingest_repo
from scripts.ingest_repo import chunk_lines, iter_python_files


def result(file_path: str, content: str) -> dict[str, object]:
    return {"file_path": file_path, "content": content}


class FakeRows:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self.rows = rows

    def all(self) -> list[tuple[object, ...]]:
        return self.rows


class FakeEvaluationSession:
    def __init__(
        self,
        repository: Repository | None = None,
        rows: list[tuple[object, ...]] | None = None,
    ) -> None:
        self.repository = repository
        self.rows = rows or []
        self.added: list[object] = []
        self.added_chunks: list[object] = []
        self.commit_count = 0
        self.null_embedding_count = 0
        self.scalar_call_count = 0

    async def __aenter__(self) -> FakeEvaluationSession:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def scalar(self, statement: object) -> Repository | None:
        del statement
        self.scalar_call_count += 1
        if self.scalar_call_count == 1:
            return self.repository
        return self.null_embedding_count

    async def execute(self, statement: object) -> FakeRows:
        del statement
        return FakeRows(self.rows)

    def add(self, value: object) -> None:
        self.added.append(value)
        if isinstance(value, Repository):
            self.repository = value

    def add_all(self, values: list[object]) -> None:
        self.added_chunks.extend(values)

    async def flush(self) -> None:
        if self.repository is not None and self.repository.id is None:
            self.repository.id = 17

    async def commit(self) -> None:
        self.commit_count += 1


def test_chunk_strategies_preserve_baseline_and_define_experimental_ranges() -> None:
    assert STRATEGY_CHOICES == ("baseline", "w100_o20")
    assert get_strategy(DEFAULT_STRATEGY).chunk_size == 60
    assert get_strategy(DEFAULT_STRATEGY).overlap == 10
    assert get_strategy("w100_o20").chunk_size == 100
    assert get_strategy("w100_o20").overlap == 20

    for line_count in (0, 1, 60, 61, 110, 111, 200, 201):
        lines = ["line"] * line_count
        assert list(expected_chunk_ranges(lines)) == list(chunk_lines(lines))

    assert list(expected_chunk_ranges(["line"] * 181, "w100_o20")) == [
        (0, 100),
        (80, 180),
        (160, 181),
    ]
    with pytest.raises(ValueError, match="Unsupported chunking strategy"):
        get_strategy("ast")


@pytest.mark.parametrize(
    ("strategy", "chunk_size", "overlap"),
    [("baseline", 60, 10), ("w100_o20", 100, 20)],
)
def test_chunk_ranges_cover_boundaries_overlap_and_final_line(
    strategy: str,
    chunk_size: int,
    overlap: int,
) -> None:
    step = chunk_size - overlap
    second_boundary = chunk_size + step
    third_boundary = chunk_size + 2 * step
    line_counts = {
        0,
        1,
        chunk_size - 1,
        chunk_size,
        chunk_size + 1,
        second_boundary - 1,
        second_boundary,
        second_boundary + 1,
        third_boundary - 1,
        third_boundary,
        third_boundary + 1,
    }

    for line_count in sorted(line_counts):
        lines = [f"line-{line_number}" for line_number in range(1, line_count + 1)]
        ranges = list(expected_chunk_ranges(lines, strategy))

        if strategy == DEFAULT_STRATEGY:
            assert ranges == list(chunk_lines(lines))
        if not line_count:
            assert ranges == []
            continue

        assert ranges[0][0] == 0
        assert ranges[-1][1] == line_count
        assert lines[ranges[-1][1] - 1] == f"line-{line_count}"
        assert all(end - start <= chunk_size for start, end in ranges)
        assert all(
            next_start == end - overlap
            for (_, end), (next_start, _) in zip(ranges, ranges[1:])
        )


def test_evaluation_repository_allowlist_and_inventory_guard() -> None:
    assert EVALUATION_REPOSITORIES == {
        "incidentweave-eval",
        "incidentweave-eval-w100_20",
    }
    assert resolve_evaluation_repository() == "incidentweave-eval"
    assert resolve_evaluation_repository(strategy="w100_o20") == (
        "incidentweave-eval-w100_20"
    )
    with pytest.raises(ValueError, match="not allowed"):
        resolve_evaluation_repository("incidentweave")
    with pytest.raises(ValueError, match="not allowed"):
        resolve_evaluation_repository("")
    with pytest.raises(ValueError, match="requires evaluation repository"):
        resolve_evaluation_repository("incidentweave-eval", "w100_o20")

    for strategy, repository_name in (
        ("baseline", "incidentweave-eval"),
        ("w100_o20", "incidentweave-eval-w100_20"),
    ):
        ensure_non_eval_inventory_unchanged(
            {"incidentweave": 48},
            {"incidentweave": 48, repository_name: 52},
            selected_repository=repository_name,
        )

        other_eval_repository = (
            "incidentweave-eval-w100_20"
            if strategy == "baseline"
            else "incidentweave-eval"
        )
        with pytest.raises(RuntimeError, match=other_eval_repository):
            ensure_non_eval_inventory_unchanged(
                {other_eval_repository: 70},
                {other_eval_repository: 71},
                selected_repository=repository_name,
            )

    with pytest.raises(RuntimeError, match="incidentweave"):
        ensure_non_eval_inventory_unchanged(
            {"incidentweave": 48},
            {"incidentweave": 49},
            selected_repository="incidentweave-eval",
        )
    with pytest.raises(RuntimeError, match="created"):
        ensure_non_eval_inventory_unchanged(
            {},
            {"unapproved-repository": 1},
            selected_repository="incidentweave-eval",
        )
    with pytest.raises(RuntimeError, match="disappeared"):
        ensure_non_eval_inventory_unchanged(
            {"dexterai": 1},
            {},
            selected_repository="incidentweave-eval-w100_20",
        )
    ensure_non_eval_inventory_unchanged(
        {"incidentweave": 48, "incidentweave-eval": 70},
        {"incidentweave": 48, "incidentweave-eval": 70},
        selected_repository="incidentweave-eval",
    )


@pytest.mark.parametrize("strategy", ["baseline", "w100_o20"])
def test_setup_eval_corpus_inserts_strategy_chunks_without_global_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    strategy: str,
) -> None:
    from evaluation import runner

    repository_name = resolve_evaluation_repository(strategy=strategy)
    session = FakeEvaluationSession()
    monkeypatch.setattr(runner, "AsyncSessionLocal", lambda: session)
    source_file = tmp_path / "source.py"
    source_lines = [f"line {line_number}" for line_number in range(1, 182)]
    source_file.write_text("\n".join(source_lines), encoding="utf-8")
    original_chunk_lines = ingest_repo.chunk_lines

    async def fake_embed_repository_chunks(repo_name: str) -> tuple[int, int, int]:
        assert repo_name == repository_name
        return len(session.added_chunks), 0, 0

    monkeypatch.setattr(
        runner.embed_chunks,
        "embed_repository_chunks",
        fake_embed_repository_chunks,
    )

    files, chunks = asyncio.run(
        runner.setup_eval_corpus(tmp_path, strategy=strategy)
    )
    expected_ranges = list(expected_chunk_ranges(source_lines, strategy))

    assert (files, chunks) == (1, len(expected_ranges))
    assert session.repository is not None
    assert session.repository.name == repository_name
    assert session.commit_count == 1
    assert ingest_repo.chunk_lines is original_chunk_lines
    assert [chunk.line_start for chunk in session.added_chunks] == [
        start + 1 for start, _ in expected_ranges
    ]
    assert [chunk.line_end for chunk in session.added_chunks] == [
        end for _, end in expected_ranges
    ]
    assert session.added_chunks[-1].content.endswith("line 181")


@pytest.mark.parametrize("missing_embedding", [False, True])
def test_setup_eval_corpus_reuses_exact_chunks_and_only_retries_missing_embeddings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    missing_embedding: bool,
) -> None:
    from evaluation import runner

    strategy = "w100_o20"
    repository_name = resolve_evaluation_repository(strategy=strategy)
    source_file = tmp_path / "source.py"
    source_lines = [f"line {line_number}" for line_number in range(1, 182)]
    source_file.write_text("\n".join(source_lines), encoding="utf-8")
    expected_ranges = list(expected_chunk_ranges(source_lines, strategy))
    rows = [
        (
            "source.py",
            start + 1,
            end,
            "\n".join(source_lines[start:end]),
            None if missing_embedding and index == 0 else [0.1],
        )
        for index, (start, end) in enumerate(expected_ranges)
    ]
    session = FakeEvaluationSession(Repository(name=repository_name), rows)
    session.repository.id = 91
    monkeypatch.setattr(runner, "AsyncSessionLocal", lambda: session)
    embed_calls: list[str] = []

    async def fake_embed_repository_chunks(name: str) -> tuple[int, int, int]:
        embed_calls.append(name)
        return 1, 0, len(expected_ranges) - 1

    if missing_embedding:
        monkeypatch.setattr(
            runner.embed_chunks,
            "embed_repository_chunks",
            fake_embed_repository_chunks,
        )
    else:
        monkeypatch.setattr(
            runner.embed_chunks,
            "embed_repository_chunks",
            lambda *_args: pytest.fail("matching embedded chunks must be reused"),
        )

    assert asyncio.run(
        runner.setup_eval_corpus(tmp_path, strategy=strategy)
    ) == (1, len(expected_ranges))
    assert session.added == []
    assert session.added_chunks == []
    assert session.commit_count == 0
    assert embed_calls == ([repository_name] if missing_embedding else [])


def test_setup_eval_corpus_checks_for_null_embeddings_after_embedding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from evaluation import runner

    repository_name = "incidentweave-eval-w100_20"
    (tmp_path / "source.py").write_text("expected chunk\n", encoding="utf-8")
    session = FakeEvaluationSession()
    session.null_embedding_count = 1
    monkeypatch.setattr(runner, "AsyncSessionLocal", lambda: session)

    async def successful_embedding_call(name: str) -> tuple[int, int, int]:
        assert name == repository_name
        return 1, 0, 0

    monkeypatch.setattr(
        runner.embed_chunks,
        "embed_repository_chunks",
        successful_embedding_call,
    )

    with pytest.raises(RuntimeError, match="still has 1 chunks without embeddings"):
        asyncio.run(
            runner.setup_eval_corpus(tmp_path, strategy="w100_o20")
        )


def test_setup_eval_corpus_refuses_stale_chunks_without_deleting_or_replacing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from evaluation import runner

    strategy = "w100_o20"
    repository_name = resolve_evaluation_repository(strategy=strategy)
    (tmp_path / "source.py").write_text("new source\n", encoding="utf-8")
    session = FakeEvaluationSession(
        Repository(name=repository_name),
        [("source.py", 1, 1, "stale source", [0.1])],
    )
    session.repository.id = 92
    monkeypatch.setattr(runner, "AsyncSessionLocal", lambda: session)
    monkeypatch.setattr(
        runner.embed_chunks,
        "embed_repository_chunks",
        lambda *_args: pytest.fail("stale chunks must not be embedded"),
    )

    with pytest.raises(RuntimeError, match="refusing to replace existing chunks"):
        asyncio.run(runner.setup_eval_corpus(tmp_path, strategy=strategy))

    assert session.added == []
    assert session.added_chunks == []
    assert session.commit_count == 0


@pytest.mark.parametrize("strategy", ["baseline", "w100_o20"])
def test_setup_eval_corpus_skips_empty_and_whitespace_only_chunks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    strategy: str,
) -> None:
    from evaluation import runner

    repository_name = resolve_evaluation_repository(strategy=strategy)
    (tmp_path / "empty.py").write_text("", encoding="utf-8")
    (tmp_path / "whitespace.py").write_text(" \n\t\n", encoding="utf-8")
    session = FakeEvaluationSession()
    monkeypatch.setattr(runner, "AsyncSessionLocal", lambda: session)

    async def fake_embed_repository_chunks(name: str) -> tuple[int, int, int]:
        assert name == repository_name
        return 0, 0, 0

    monkeypatch.setattr(
        runner.embed_chunks,
        "embed_repository_chunks",
        fake_embed_repository_chunks,
    )

    assert asyncio.run(
        runner.setup_eval_corpus(tmp_path, strategy=strategy)
    ) == (2, 0)
    assert session.added_chunks == []


def test_run_pipeline_once_routes_selected_evaluation_repository(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from evaluation import runner

    observed = {}
    question = {
        "id": "strategy-route",
        "category": "direct",
        "question": "Question for strategy routing",
        "relevant": [],
        "must_mention": [],
    }

    async def fake_investigate_repository(
        repository_name: str,
        query: str,
        **kwargs: object,
    ) -> dict[str, object]:
        observed.update(repository_name=repository_name, query=query, **kwargs)
        return {
            "diagnosis": "INSUFFICIENT_EVIDENCE",
            "latency_ms": None,
            "generation_trace": None,
            "retrieval_results": [],
            "cited_chunk_ids": [],
            "evidence_check": {"is_sufficient": False},
            "tool_calls": [],
        }

    monkeypatch.setattr(
        runner.investigate,
        "investigate_repository",
        fake_investigate_repository,
    )
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)

    asyncio.run(
        run_pipeline_once(
            [question],
            tmp_path,
            "test",
            {"http_calls": 0, "http_429_responses": 0},
            repository_name="incidentweave-eval-w100_20",
            strategy="w100_o20",
        )
    )

    assert observed["repository_name"] == "incidentweave-eval-w100_20"
    assert observed["persist"] is False
    assert observed["temperature"] == 0


def test_run_evaluation_threads_strategy_and_repository_without_live_services(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    from evaluation import runner

    source_root = Path(__file__).resolve().parents[2]
    evaluation_root = tmp_path / "evaluation"
    evaluation_root.mkdir()
    (evaluation_root / "golden_set.json").write_text(
        (source_root / "evaluation" / "golden_set.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    results_root = tmp_path / "results"
    pipeline_calls: list[tuple[str, str]] = []
    observed: dict[str, object] = {}

    async def fake_inventory() -> dict[str, int]:
        return {"incidentweave": 48}

    async def fake_setup_eval_corpus(
        snapshot_root: Path,
        *,
        repository_name: str,
        strategy: str,
    ) -> tuple[int, int]:
        observed["setup"] = (repository_name, strategy)
        return 40, 52

    async def fake_validate_eval_index(
        questions: list[dict[str, object]],
        *,
        repository_name: str,
        strategy: str,
    ) -> list[str]:
        observed["validate"] = (repository_name, strategy)
        return []

    async def fake_retrieval_records(
        questions: list[dict[str, object]],
        *,
        repository_name: str,
        strategy: str,
    ) -> list[dict[str, object]]:
        observed["retrieval"] = (repository_name, strategy)
        return [
            {
                "id": question["id"],
                "category": question["category"],
                "relevant": question.get("relevant", []),
                "vector": [],
                "fulltext": [],
                "hybrid": [],
                "evidence_check": {
                    "is_sufficient": False,
                    "reason": "stubbed test evidence",
                },
            }
            for question in questions
        ]

    async def fake_run_pipeline_once(
        questions: list[dict[str, object]],
        snapshot_root: Path,
        run_name: str,
        generation_budget: dict[str, int],
        *,
        repository_name: str,
        strategy: str,
    ) -> tuple[list[dict[str, object]], dict[str, int]]:
        pipeline_calls.append((repository_name, strategy))
        records = [
            {
                "id": question["id"],
                "category": question["category"],
                "diagnosis": "",
                "error": "stubbed test pipeline",
                "outcome": "error",
                "generation_ran": False,
                "generation_trace": None,
                "wall_ms": 0,
                "generation_ms": None,
                "cited_chunk_ids": [],
                "tool_calls": [],
                "confidence_raw": None,
                "confidence": None,
            }
            for question in questions
        ]
        return records, {"http_calls": 0, "http_429_responses": 0}

    monkeypatch.setattr(runner, "EVALUATION_ROOT", evaluation_root)
    monkeypatch.setattr(runner, "RESULTS_ROOT", results_root)
    monkeypatch.setattr(runner, "load_key_without_logging", lambda: None)
    monkeypatch.setattr(runner, "snapshot_sha", lambda: "abcdef0123456789")
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout=""),
    )
    monkeypatch.setattr(runner, "export_snapshot", lambda *args: tmp_path / "snapshot")
    monkeypatch.setattr(runner, "validate_golden_set", lambda *args: [])
    monkeypatch.setattr(runner, "inventory", fake_inventory)
    monkeypatch.setattr(runner, "setup_eval_corpus", fake_setup_eval_corpus)
    monkeypatch.setattr(runner, "validate_eval_index", fake_validate_eval_index)
    monkeypatch.setattr(runner, "retrieval_records", fake_retrieval_records)
    monkeypatch.setattr(runner, "run_pipeline_once", fake_run_pipeline_once)

    report = asyncio.run(runner.run_evaluation(strategy="w100_o20"))

    expected_route = ("incidentweave-eval-w100_20", "w100_o20")
    assert observed["setup"] == expected_route
    assert observed["validate"] == expected_route
    assert observed["retrieval"] == expected_route
    assert pipeline_calls == [expected_route, expected_route]
    assert report["strategy"] == "w100_o20"
    assert report["evaluation_repository"] == "incidentweave-eval-w100_20"
    assert report["chunk_size"] == 100
    assert report["overlap"] == 20
    assert report["generation_config"] == (
        "temperature=0; responseMimeType=application/json; "
        "response schema + prompt version grounded-v3"
    )
    assert report["run_id"].endswith("-w100_o20")
    assert (results_root / "runs" / report["run_id"] / "report.json").is_file()


def test_resolve_corpus_sha_returns_pinned_value_and_raises_on_invalid_input() -> None:
    assert resolve_corpus_sha({"pinned_sha": "abc123"}) == "abc123"

    with pytest.raises(ValueError, match="pinned_sha"):
        resolve_corpus_sha({})

    with pytest.raises(ValueError, match="pinned_sha"):
        resolve_corpus_sha({"pinned_sha": ""})


def test_pinned_snapshot_exports_and_validates_with_expected_counts(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    data = load_golden_set(root / "evaluation" / "golden_set.json")
    sha = resolve_corpus_sha(data)
    snapshot_parent = tmp_path / "snapshot"
    try:
        snapshot_root = export_snapshot(root, sha, snapshot_parent)
    except RuntimeError as exc:
        pytest.skip(f"pinned commit not present in this clone: {exc}")

    errors = validate_golden_set(data, snapshot_root, sha)
    assert errors == []
    files = sorted(iter_python_files(snapshot_root))
    assert len(files) == 40

    chunks = 0
    for file_path in files:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for start_index, end_index in chunk_lines(lines):
            content = "\n".join(lines[start_index:end_index])
            if content.strip():
                chunks += 1
    assert chunks == 70

    experimental_chunks = 0
    for file_path in files:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for start_index, end_index in expected_chunk_ranges(lines, "w100_o20"):
            content = "\n".join(lines[start_index:end_index])
            if content.strip():
                experimental_chunks += 1
    assert experimental_chunks == 52


def test_extract_generation_trace_handles_payload_and_missing_usage() -> None:
    payload = {
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [{"text": "diagnosis: INSUFFICIENT_EVIDENCE"}]},
        }],
        "usageMetadata": {"totalTokenCount": 42, "promptTokenCount": 10, "candidateTokenCount": 32},
    }
    trace = extract_generation_trace("sample prompt", payload)
    assert trace is not None
    assert trace["prompt_sha256"] == hashlib.sha256(b"sample prompt").hexdigest()
    assert trace["prompt_chars"] == len("sample prompt")
    assert trace["finish_reason"] == "STOP"
    assert trace["usage"] == payload["usageMetadata"]
    assert trace["total_tokens"] == 42

    empty_usage = {
        "candidates": [
            {"content": {"parts": [{"text": "diagnosis: insufficient evidence"}]}}
        ]
    }
    trace2 = extract_generation_trace("sample prompt", empty_usage)
    assert trace2 is not None
    assert trace2["usage"] == {}
    assert trace2["total_tokens"] is None

    assert extract_generation_trace(None, None) is None


def test_abstention_kind_and_outcome_v2_and_value_distribution() -> None:
    assert (
        abstention_kind("INSUFFICIENT_EVIDENCE", True, "INSUFFICIENT_EVIDENCE")
        == "explicit"
    )
    assert (
        abstention_kind(
            "INSUFFICIENT_EVIDENCE",
            True,
            "diagnosis: insufficient evidence",
        )
        == "parse_fallback"
    )
    assert abstention_kind("INSUFFICIENT_EVIDENCE", False, "INSUFFICIENT_EVIDENCE") is None

    cases = [
        ("answerable", None, False, False, True, True, "correct_labeled_context"),
        ("answerable", None, False, False, False, True, "correct_unlabeled_context"),
        ("answerable", None, False, False, True, False, "incomplete_or_wrong"),
        ("answerable", None, False, True, False, None, "retrieval_miss_abstained"),
        ("answerable", None, False, True, True, None, "model_false_abstention"),
        ("answerable", None, True, False, None, None, "guard_false_refusal"),
        ("unanswerable", None, True, False, None, None, "guard_true_refusal"),
        ("unanswerable", None, False, True, None, None, "model_abstained"),
        ("unanswerable", None, False, False, None, None, "answered_unanswerable"),
        ("answerable", "error", False, False, True, True, "error"),
    ]
    for (
        category,
        error,
        guard_refused,
        abstained,
        labeled_in_context,
        screen_pass,
        expected,
    ) in cases:
        assert classify_outcome_v2(
            category,
            error,
            guard_refused,
            abstained,
            labeled_in_context,
            screen_pass,
        ) == expected

    assert value_distribution([3, 5, 1, None, 9]) == {
        "min": 1,
        "median": 4.0,
        "max": 9,
        "count": 4,
    }
    assert value_distribution([None, None]) == {
        "min": None,
        "median": None,
        "max": None,
        "count": 0,
    }
    assert value_distribution([]) == {
        "min": None,
        "median": None,
        "max": None,
        "count": 0,
    }

def test_exact_abstention_does_not_pass_answer_screen(monkeypatch, tmp_path: Path) -> None:
    from evaluation import runner

    question = {
        "id": "exact-abstention",
        "category": "direct",
        "question": "What answer is supported?",
        "relevant": [],
        "must_mention": [["supported answer"]],
    }

    async def fake_investigate_repository(*args, **kwargs):
        return {
            "diagnosis": "INSUFFICIENT_EVIDENCE",
            "latency_ms": 75,
            "generation_trace": {"raw_text": "INSUFFICIENT_EVIDENCE"},
            "retrieval_results": [],
            "cited_chunk_ids": [],
        }

    monkeypatch.setattr(
        runner.investigate, "investigate_repository", fake_investigate_repository
    )
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)

    records, _ = asyncio.run(
        run_pipeline_once(
            [question], tmp_path, "test", {"http_calls": 0, "http_429_responses": 0}
        )
    )
    record = records[0]
    classify_outcomes(records, [question])
    classify_outcome_v2_for_records(records)

    assert record["abstention_kind"] == "explicit"
    assert record["screen_pass"] is None
    assert record["outcome_v2"] == "retrieval_miss_abstained"


def test_baseline_answer_mentioning_marker_is_screened_as_answer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from evaluation import runner

    root = Path(__file__).resolve().parents[2]
    baseline = json.loads((root / "evaluation" / "results" / "baseline.json").read_text(
        encoding="utf-8"
    ))
    question = next(item for item in baseline if item["id"] == "paraphrased-05")
    diagnosis = question["diagnosis"]

    async def fake_investigate_repository(*args, **kwargs):
        return {
            "diagnosis": diagnosis,
            "latency_ms": 75,
            "generation_trace": {"raw_text": diagnosis},
            "retrieval_results": [],
            "cited_chunk_ids": [],
        }

    monkeypatch.setattr(
        runner.investigate, "investigate_repository", fake_investigate_repository
    )
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)

    records, _ = asyncio.run(
        run_pipeline_once(
            [question], tmp_path, "test", {"http_calls": 0, "http_429_responses": 0}
        )
    )
    record = records[0]
    classify_outcomes(records, [question])
    classify_outcome_v2_for_records(records)

    assert "INSUFFICIENT_EVIDENCE" in diagnosis
    assert record["abstention_kind"] is None
    assert record["screen_pass"] is True
    assert record["outcome"] == "correct"
    assert record["outcome_v2"] == "correct_unlabeled_context"


def test_unanswerable_answer_mentioning_marker_is_answered(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from evaluation import runner

    root = Path(__file__).resolve().parents[2]
    baseline = json.loads((root / "evaluation" / "results" / "baseline.json").read_text(
        encoding="utf-8"
    ))
    diagnosis = next(
        item["diagnosis"] for item in baseline if item["id"] == "paraphrased-05"
    )
    question = {
        "id": "unanswerable-marker-answer",
        "category": "unanswerable_near",
        "question": "An unanswerable test question",
        "relevant": [],
        "must_mention": [],
    }

    async def fake_investigate_repository(*args, **kwargs):
        return {
            "diagnosis": diagnosis,
            "latency_ms": 75,
            "generation_trace": {"raw_text": diagnosis},
            "retrieval_results": [],
            "cited_chunk_ids": [],
        }

    monkeypatch.setattr(
        runner.investigate, "investigate_repository", fake_investigate_repository
    )
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)

    records, _ = asyncio.run(
        run_pipeline_once(
            [question], tmp_path, "test", {"http_calls": 0, "http_429_responses": 0}
        )
    )
    record = records[0]
    classify_outcomes(records, [question])
    classify_outcome_v2_for_records(records)

    assert record["abstention_kind"] is None
    assert record["outcome"] == "falsely answered"
    assert record["outcome_v2"] == "answered_unanswerable"


def test_legacy_and_v2_outcome_count_invariants() -> None:
    questions = [
        {"id": "labeled", "category": "direct", "must_mention": [["answer"]]},
        {"id": "unlabeled", "category": "paraphrased", "must_mention": [["answer"]]},
        {"id": "false-refusal", "category": "direct", "must_mention": []},
        {"id": "true-refusal", "category": "unanswerable_far", "must_mention": []},
        {"id": "model-abstention", "category": "unanswerable_near", "must_mention": []},
        {"id": "answered-unanswerable", "category": "unanswerable_near", "must_mention": []},
    ]
    records = [
        {
            "id": "labeled", "category": "direct", "diagnosis": "answer", "error": None,
            "refused": False, "abstention_kind": None, "labeled_chunk_in_context": True,
            "screen_pass": True,
        },
        {
            "id": "unlabeled", "category": "paraphrased", "diagnosis": "answer",
            "error": None, "refused": False, "abstention_kind": None,
            "labeled_chunk_in_context": False, "screen_pass": True,
        },
        {
            "id": "false-refusal", "category": "direct",
            "diagnosis": "INSUFFICIENT_EVIDENCE", "error": None, "refused": True,
            "abstention_kind": None, "labeled_chunk_in_context": False,
            "screen_pass": None,
        },
        {
            "id": "true-refusal", "category": "unanswerable_far",
            "diagnosis": "INSUFFICIENT_EVIDENCE", "error": None, "refused": True,
            "abstention_kind": None, "labeled_chunk_in_context": None, "screen_pass": None,
        },
        {
            "id": "model-abstention", "category": "unanswerable_near",
            "diagnosis": "INSUFFICIENT_EVIDENCE", "error": None, "refused": False,
            "abstention_kind": "explicit", "labeled_chunk_in_context": None,
            "screen_pass": None,
        },
        {
            "id": "answered-unanswerable", "category": "unanswerable_near",
            "diagnosis": "an answer", "error": None, "refused": False,
            "abstention_kind": None, "labeled_chunk_in_context": None, "screen_pass": None,
        },
    ]

    classify_outcomes(records, questions)
    classify_outcome_v2_for_records(records)
    answerable = [
        record for record in records if not record["category"].startswith("unanswerable")
    ]

    assert sum(record["outcome"] == "correct" for record in answerable) == sum(
        record["outcome_v2"] in {"correct_labeled_context", "correct_unlabeled_context"}
        for record in answerable
    )
    assert sum(record["outcome"] == "refused" for record in records) == sum(
        record["outcome_v2"] == "guard_true_refusal" for record in records
    )
    assert sum(record["outcome"] == "falsely answered" for record in records) == sum(
        record["outcome_v2"] in {"model_abstained", "answered_unanswerable"}
        for record in records
    )


def test_guard_diagnostics_and_citation_summary_arithmetic() -> None:
    checks = [
        {
            "is_sufficient": False,
            "reason": "Best retrieved evidence score is below the minimum threshold.",
        },
        {
            "is_sufficient": False,
            "reason": "Best vector cosine distance is above the maximum threshold.",
        },
        {
            "is_sufficient": False,
            "reason": "No repository evidence was retrieved.",
        },
        {
            "is_sufficient": True,
            "reason": "Evidence strength meets the RRF and vector-distance requirements.",
        },
        {
            "is_sufficient": True,
            "reason": "Best retrieved evidence score is below the minimum threshold.",
        },
        {
            "is_sufficient": True,
            "reason": "Best vector cosine distance is above the maximum threshold.",
        },
    ]
    diagnostics = guard_diagnostics(checks, 0.016)
    assert diagnostics == {
        "rrf_threshold": 0.016,
        "rrf_rank1_floor": 1 / 61,
        "rrf_gate_can_reject_nonempty_vector_results": False,
        "rrf_rejections": 1,
        "vector_rejections": 1,
        "other_rejections": 1,
    }
    assert "can_reject" not in diagnostics
    assert (
        guard_diagnostics(checks, 0.02)[
            "rrf_gate_can_reject_nonempty_vector_results"
        ]
        is True
    )
    assert best_score_distribution(
        [{"score": 0.3}, {"score": 0.4}], "score"
    ) == {"min": 0.3, "median": 0.35, "max": 0.4}

    records = [{
        "category": "direct",
        "diagnosis": "answer",
        "cited_chunk_ids": ["a", "b"],
        "cited_chunk_relevance": [{"relevant": True}, {"relevant": False}],
        "submitted_citation_count": 2,
        "valid_citation_count": 2,
    }, {
        "category": "direct",
        "diagnosis": "answer",
        "cited_chunk_ids": ["c"],
        "cited_chunk_relevance": [{"relevant": False}],
        "submitted_citation_count": 3,
        "valid_citation_count": 1,
    }, {
        "category": "unanswerable_far",
        "diagnosis": "INSUFFICIENT_EVIDENCE",
        "cited_chunk_ids": [],
        "cited_chunk_relevance": [],
    }, {
        "category": "direct",
        "diagnosis": "INSUFFICIENT_EVIDENCE",
        "cited_chunk_ids": [],
        "cited_chunk_relevance": [],
    }]
    summary = citation_summary(records)
    assert summary == {
        "cited_total": 3,
        "cited_relevant": 1,
        "answers_with_zero_citations": 0,
        "submitted_citations": 5,
        "valid_citations": 3,
        "citation_validity_rate": 0.6,
    }


def test_retrieval_metrics_handle_hits_ties_and_no_hit() -> None:
    results = [
        [result("a.py", "alpha"), result("b.py", "beta")],
        [result("b.py", "beta"), result("a.py", "alpha")],
        [result("c.py", "gamma")],
    ]
    labels = [
        [{"file_path": "a.py", "substring": "alpha"}],
        [{"file_path": "a.py", "substring": "alpha"}],
        [{"file_path": "z.py", "substring": "zeta"}],
    ]

    assert hit_at_k(results, labels, 1) == 1
    assert hit_at_k(results, labels, 3) == 2
    assert mean_reciprocal_rank(results, labels) == (1 + 0.5) / 3
    assert retrieval_summary(results, labels)["hit_at_5"] == 2


def test_run_summary_reports_answered_citation_validity_rate() -> None:
    records = [
        {
            "outcome": "correct",
            "diagnosis": "A supported answer.",
            "generation_ran": True,
            "error": None,
            "submitted_citation_count": 4,
            "valid_citation_count": 3,
        },
        {
            "outcome": "refused",
            "diagnosis": "INSUFFICIENT_EVIDENCE",
            "generation_ran": False,
            "error": None,
            "submitted_citation_count": 9,
            "valid_citation_count": 9,
        },
    ]

    assert summarize_run(records)["citation_validity_rate"] == 0.75
    assert summarize_run(
        [{**records[0], "submitted_citation_count": 0, "valid_citation_count": 0}]
    )["citation_validity_rate"] is None


@pytest.mark.anyio
async def test_counted_send_once_counts_and_throttles_generation_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evaluation import runner

    delays: list[float] = []
    state = {"last_call_at": 1.0, "question_throttle_wait_ms": 0.0}
    budget = {"http_calls": 0, "http_429_responses": 0}
    stats = {"http_calls": 0, "http_429_responses": 0}

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    async def original_send_once(client: object, url: str, payload: object):
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(runner.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(runner.time, "monotonic", lambda: 2.0)
    response = await runner._counted_send_once(
        object(),
        "https://provider.test:generateContent",
        {},
        original_send_once=original_send_once,
        generation_budget=budget,
        call_stats=stats,
        state=state,
    )

    assert response.status_code == 200
    assert delays == [0.5]
    assert state["question_throttle_wait_ms"] == 500
    assert budget["http_calls"] == stats["http_calls"] == 1


@pytest.mark.anyio
async def test_counted_send_once_counts_429_and_returns_response() -> None:
    from evaluation import runner

    budget = {"http_calls": 0, "http_429_responses": 0}
    stats = {"http_calls": 0, "http_429_responses": 0}

    async def original_send_once(client: object, url: str, payload: object):
        return httpx.Response(429)

    response = await runner._counted_send_once(
        object(),
        "https://provider.test:generateContent",
        {},
        original_send_once=original_send_once,
        generation_budget=budget,
        call_stats=stats,
        state={},
    )

    assert response.status_code == 429
    assert budget == stats == {"http_calls": 1, "http_429_responses": 1}


@pytest.mark.anyio
async def test_counted_send_once_enforces_generation_budget() -> None:
    from evaluation import runner

    budget = {"http_calls": MAX_GENERATION_HTTP_CALLS, "http_429_responses": 0}
    stats = {"http_calls": 0, "http_429_responses": 0}
    called = False

    async def original_send_once(client: object, url: str, payload: object):
        nonlocal called
        called = True
        return httpx.Response(200)

    with pytest.raises(RuntimeError, match="generation HTTP call budget reached"):
        await runner._counted_send_once(
            object(),
            "https://provider.test:generateContent",
            {},
            original_send_once=original_send_once,
            generation_budget=budget,
            call_stats=stats,
            state={},
        )

    assert called is False
    assert stats["http_calls"] == 0


@pytest.mark.anyio
async def test_counted_send_once_passes_embeddings_without_counting() -> None:
    from evaluation import runner

    budget = {"http_calls": 0, "http_429_responses": 0}
    stats = {"http_calls": 0, "http_429_responses": 0}
    calls: list[str] = []

    async def original_send_once(client: object, url: str, payload: object):
        calls.append(url)
        return httpx.Response(200)

    response = await runner._counted_send_once(
        object(),
        "https://provider.test:batchEmbedContents",
        {},
        original_send_once=original_send_once,
        generation_budget=budget,
        call_stats=stats,
        state={},
    )

    assert response.status_code == 200
    assert calls == ["https://provider.test:batchEmbedContents"]
    assert budget["http_calls"] == stats["http_calls"] == 0


def test_mrr_averages_equal_ranks_and_counts_no_hit_as_zero() -> None:
    results = [
        [result("other.py", "no"), result("target.py", "yes")],
        [result("elsewhere.py", "no"), result("target.py", "yes")],
        [result("other.py", "no")],
    ]
    labels = [[{"file_path": "target.py", "substring": "yes"}]] * 3

    assert mean_reciprocal_rank(results, labels) == pytest.approx(1 / 3)


def test_relevance_rule_is_case_insensitive_and_requires_same_file() -> None:
    labels = [{"file_path": "src/store.py", "substring": "PersistResult"}]

    assert is_relevant(result("src/store.py", "class persistresult:"), labels)
    assert not is_relevant(result("src/other.py", "class PersistResult:"), labels)


def test_guard_confusion_and_distance_sweep() -> None:
    answerable = [True, True, False, False]
    sufficient = [True, False, False, True]
    assert guard_confusion(answerable, sufficient) == {
        "true_accept": 1,
        "false_refusal": 1,
        "true_refusal": 1,
        "false_accept": 1,
    }

    checks = [
        {"best_rrf_score": 0.02, "best_vector_score": 0.31},
        {"best_rrf_score": 0.02, "best_vector_score": 0.51},
    ]
    sweep = distance_sweep(checks, [True, False], 0.016)
    assert sweep[0] == {
        "vector_cutoff": 0.3,
        "false_refusals": 1,
        "false_accepts": 0,
    }
    assert len(sweep) == 16
    assert sweep[-1]["vector_cutoff"] == 0.6


def test_distance_sweep_counts_false_refusals_and_false_accepts() -> None:
    checks = [
        {"best_rrf_score": 0.02, "best_vector_score": 0.31},
        {"best_rrf_score": 0.02, "best_vector_score": 0.5},
        {"best_rrf_score": 0.02, "best_vector_score": 0.35},
        {"best_rrf_score": 0.01, "best_vector_score": 0.2},
    ]
    sweep = distance_sweep(checks, [True, True, False, False], 0.016)

    assert sweep[0] == {
        "vector_cutoff": 0.3,
        "false_refusals": 2,
        "false_accepts": 0,
    }
    assert sweep[3] == {
        "vector_cutoff": 0.36,
        "false_refusals": 1,
        "false_accepts": 1,
    }
    assert sweep[10] == {
        "vector_cutoff": 0.5,
        "false_refusals": 0,
        "false_accepts": 1,
    }


def test_answer_screen_and_refusal() -> None:
    assert answer_screen("AsyncSessionLocal uses async_sessionmaker", [["sessionmaker"], ["async"]])
    assert not answer_screen("Only a database engine is described", [["sessionmaker"]])
    assert is_refused("INSUFFICIENT_EVIDENCE")
    assert is_refused(" INSUFFICIENT_EVIDENCE ")
    assert not is_refused("INSUFFICIENT_EVIDENCE", generation_latency_ms=75)
    assert not is_refused("Diagnosis: insufficient evidence")


def _valid_golden_data(snapshot_root: Path) -> dict[str, object]:
    questions = []
    for index, category in enumerate(["direct"] * 8 + ["paraphrased"] * 8):
        relative_path = f"area{index}.py"
        content = f"label phrase {index}"
        (snapshot_root / relative_path).write_text(
            f"value = {content!r}\n", encoding="utf-8"
        )
        questions.append(
            {
                "id": f"{category}-{index}",
                "category": category,
                "question": "How does this behavior work?",
                "seen_before": False,
                "relevant": [{"file_path": relative_path, "substring": content}],
                "relevant_spans": [
                    {"file_path": relative_path, "line_start": 1, "line_end": 1}
                ],
                "must_mention": [["label"]],
            }
        )
    questions.extend(
        {
            "id": f"unanswerable-{index}",
            "category": "unanswerable_far" if index < 4 else "unanswerable_near",
            "question": "How is this absent feature handled?",
            "seen_before": False,
            "relevant": [],
            "relevant_spans": [],
            "absent_terms": ["feature-not-present"],
        }
        for index in range(8)
    )
    return {
        "pinned_sha": "snapshot-sha",
        "review_status": "pending maintainer review",
        "counts": {
            "direct": 8,
            "paraphrased": 8,
            "unanswerable_far": 4,
            "unanswerable_near": 4,
        },
        "questions": questions,
    }


def test_golden_validation_accepts_valid_schema_and_snapshot(tmp_path: Path) -> None:
    data = _valid_golden_data(tmp_path)

    assert validate_golden_set(data, tmp_path, "snapshot-sha") == []


def test_golden_validation_rejects_duplicate_ids_invalid_category_and_counts(
    tmp_path: Path,
) -> None:
    data = _valid_golden_data(tmp_path)
    questions = data["questions"]
    questions[1]["id"] = questions[0]["id"]
    questions[0]["category"] = "invalid"
    data["counts"]["direct"] = 7

    errors = validate_golden_set(data, tmp_path, "other-sha")

    assert "question ids are not unique" in errors
    assert any("invalid categories" in error for error in errors)
    assert any("category counts differ" in error for error in errors)
    assert "header counts do not match the required category counts" in errors
    assert "pinned_sha does not match the exported snapshot" in errors


def test_golden_validation_rejects_missing_labels_absent_terms_and_answer_labels(
    tmp_path: Path,
) -> None:
    data = _valid_golden_data(tmp_path)
    questions = data["questions"]
    questions[0]["relevant"] = [{"file_path": "missing.py", "substring": "absent"}]
    questions[-1]["absent_terms"] = ["LABEL PHRASE 1"]
    questions[-2]["absent_terms"] = []
    questions[-3]["relevant"] = [{"file_path": "area0.py", "substring": "label phrase 0"}]

    errors = validate_golden_set(data, tmp_path, "snapshot-sha")

    assert any("missing label file" in error for error in errors)
    assert any("absent term appears" in error for error in errors)
    assert any("unanswerable_near requires absent_terms" in error for error in errors)
    assert any("unanswerable question has answer labels" in error for error in errors)


def test_golden_validation_checks_relevant_span_shape_and_matching_paths(
    tmp_path: Path,
) -> None:
    data = _valid_golden_data(tmp_path)
    data["questions"][0]["relevant_spans"] = [
        {"file_path": "wrong.py", "line_start": 0, "line_end": 2}
    ]
    data["questions"][1]["relevant_spans"] = []

    errors = validate_golden_set(data, tmp_path, "snapshot-sha")

    assert any("file_path does not match label" in error for error in errors)
    assert any("line range is invalid" in error for error in errors)
    assert any("must match relevant labels" in error for error in errors)


def test_index_validation_requires_a_reachable_chunk() -> None:
    questions = [
        {
            "id": "direct-1",
            "category": "direct",
            "relevant": [{"file_path": "source.py", "substring": "target phrase"}],
        }
    ]

    assert validate_index_labels(
        questions, [result("source.py", "contains target phrase")]
    ) == []
    assert validate_index_labels(questions, [result("source.py", "no target")]) == [
        "direct-1: no indexed chunk matches a relevance label"
    ]


def test_build_run_metadata_stable_hash_and_compare_reports_detect_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evaluation import runner
    from evaluation.compare import compare_reports

    def build_metadata(
        *,
        code_sha: str = "code123",
        code_dirty: bool = False,
        code_untracked_files: int = 1,
        strategy: str = DEFAULT_STRATEGY,
    ) -> dict[str, object]:
        return runner.build_run_metadata(
            run_id=build_run_id(
                datetime(2026, 1, 1, tzinfo=UTC),
                code_sha,
                strategy,
            ),
            started_at="2026-01-01T00:00:00+00:00",
            finished_at="2026-01-01T00:01:00+00:00",
            corpus_sha="deadbeef",
            code_sha=code_sha,
            code_dirty=code_dirty,
            code_untracked_files=code_untracked_files,
            models={"embedding": "m1", "generation": "g1"},
            limit=5,
            passes=2,
            strategy=strategy,
        )

    a = build_metadata()
    b = build_metadata()
    assert a["config_sha256"] == b["config_sha256"]
    assert a["code_untracked_files"] == 1
    assert a["strategy"] == "baseline"
    assert a["chunk_size"] == 60
    assert a["overlap"] == 10
    assert a["evaluation_repository"] == "incidentweave-eval"
    assert a["run_id"].endswith("-baseline")
    code_metadata_changed = build_metadata(
        code_sha="other-code",
        code_dirty=True,
        code_untracked_files=9,
    )
    assert code_metadata_changed["code_sha"] == "other-code"
    assert code_metadata_changed["code_dirty"] is True
    assert code_metadata_changed["code_untracked_files"] == 9
    assert code_metadata_changed["config_sha256"] == a["config_sha256"]

    experimental_metadata = build_metadata(strategy="w100_o20")
    assert experimental_metadata["strategy"] == "w100_o20"
    assert experimental_metadata["chunk_size"] == 100
    assert experimental_metadata["overlap"] == 20
    assert experimental_metadata["evaluation_repository"] == (
        "incidentweave-eval-w100_20"
    )
    assert experimental_metadata["run_id"].endswith("-w100_o20")
    assert experimental_metadata["run_id"] != a["run_id"]
    assert experimental_metadata["config_sha256"] != a["config_sha256"]

    with monkeypatch.context() as patch:
        patch.setattr(
            runner,
            "MIN_ACCEPTABLE_RRF_SCORE",
            runner.MIN_ACCEPTABLE_RRF_SCORE + 0.001,
        )
        assert build_metadata()["config_sha256"] != a["config_sha256"]

    with monkeypatch.context() as patch:
        patch.setattr(runner, "SYSTEM_INSTRUCTION", runner.SYSTEM_INSTRUCTION + " changed")
        assert build_metadata()["config_sha256"] != a["config_sha256"]

    report_a = {
        "pinned_sha": "deadbeef",
        "run_id": "a",
        "code_sha": "old-code",
        "config_sha256": a["config_sha256"],
        "guard_counts": {"true_accept": 2, "false_refusal": 1},
        "retrieval_tables": {"vector": {"hit_at_1": 2, "hit_at_3": 3}},
        "latency_summary": {"pass_1": {"generation_ms": {"median": 100}}},
        "token_summary": {"pass_1": {"total_tokens": {"median": 120}}},
        "run_summaries": [
            {
                "outcome_counts": {"correct": 2, "falsely answered": 1},
                "outcome_v2_counts": {
                    "correct_labeled_context": 2,
                    "model_abstained": 1,
                },
            },
            {
                "outcome_counts": {"correct": 2, "falsely answered": 1},
                "outcome_v2_counts": {
                    "correct_labeled_context": 2,
                    "model_abstained": 1,
                },
            },
        ],
        "records": [[
            {"id": "q1", "outcome_v2": "correct_labeled_context", "labeled_rank": 1},
            {"id": "q2", "outcome_v2": "model_abstained", "labeled_rank": None},
        ], [
            {"id": "q1", "outcome_v2": "correct_labeled_context", "labeled_rank": 1},
            {"id": "q2", "outcome_v2": "model_abstained", "labeled_rank": None},
        ]],
    }
    report_b = {
        "pinned_sha": "deadbeef",
        "run_id": "b",
        "code_sha": "new-code",
        "config_sha256": a["config_sha256"],
        "guard_counts": {"true_accept": 1, "false_refusal": 2},
        "retrieval_tables": {"vector": {"hit_at_1": 1, "hit_at_3": 2}},
        "latency_summary": {"pass_1": {"generation_ms": {"median": 200}}},
        "token_summary": {"pass_1": {"total_tokens": {"median": 180}}},
        "run_summaries": [
            {
                "outcome_counts": {"correct": 1, "falsely answered": 2},
                "outcome_v2_counts": {
                    "correct_labeled_context": 1,
                    "model_abstained": 2,
                },
            },
            {
                "outcome_counts": {"correct": 1, "falsely answered": 2},
                "outcome_v2_counts": {
                    "correct_labeled_context": 1,
                    "model_abstained": 2,
                },
            },
        ],
        "records": [[
            {"id": "q1", "outcome_v2": "incomplete_or_wrong", "labeled_rank": 3},
            {"id": "q2", "outcome_v2": "model_abstained", "labeled_rank": None},
        ], [
            {"id": "q1", "outcome_v2": "incomplete_or_wrong", "labeled_rank": 3},
            {"id": "q2", "outcome_v2": "model_abstained", "labeled_rank": None},
        ]],
    }

    diff = compare_reports(report_a, report_b)
    assert diff["config_differences"]["code_sha"] == {
        "from": "old-code",
        "to": "new-code",
    }
    assert diff["outcome_v2_counts_delta"]["correct_labeled_context"] == -1
    assert diff["outcome_v2_counts_delta"]["model_abstained"] == 1
    assert diff["outcome_v2_counts_delta_pass_2"] == {
        "correct_labeled_context": -1,
        "model_abstained": 1,
    }
    assert diff["question_flips"]["q1"]["outcome_v2"] == {
        "from": "correct_labeled_context",
        "to": "incomplete_or_wrong",
    }
    assert diff["question_flips"]["q1"]["labeled_rank"] == {"from": 1, "to": 3}
    assert diff["generation_latency_delta"]["median_generation_ms"] == 100
    assert diff["total_token_delta"]["median_total_tokens"] == 60

    legacy_records = [
        {"id": "q1", "outcome": "correct", "labeled_rank": None},
        {"id": "q2", "outcome": "refused", "labeled_rank": None},
    ]
    legacy_diff = compare_reports(legacy_records, report_a)
    assert legacy_diff["legacy_report"] is True
    assert legacy_diff["question_flips"]["q1"]["outcome_v2"] == {
        "from": None,
        "to": "correct_labeled_context",
    }
    assert legacy_diff["question_flips"]["q2"]["outcome_v2"] == {
        "from": None,
        "to": "model_abstained",
    }
    assert "outcome_v2_counts_delta_pass_2" not in legacy_diff


def test_compare_reports_uses_top_level_counts_only_without_run_summaries() -> None:
    from evaluation.compare import compare_reports

    report_a = {"outcome_v2_counts": {"correct_labeled_context": 3}}
    report_b = {"outcome_v2_counts": {"correct_labeled_context": 5}}

    assert compare_reports(report_a, report_b)["outcome_v2_counts_delta"] == {
        "correct_labeled_context": 2
    }


def test_run_eval_accepts_only_two_passes_and_supported_strategies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.run_eval import parse_args

    monkeypatch.setattr("sys.argv", ["run_eval.py"])
    default_args = parse_args()
    assert default_args.passes == 2
    assert default_args.strategy == "baseline"

    monkeypatch.setattr(
        "sys.argv",
        ["run_eval.py", "--strategy", "w100_o20", "--passes", "2"],
    )
    assert parse_args().strategy == "w100_o20"

    for pass_count in ("1", "3"):
        monkeypatch.setattr("sys.argv", ["run_eval.py", "--passes", pass_count])
        with pytest.raises(SystemExit):
            parse_args()

    monkeypatch.setattr("sys.argv", ["run_eval.py", "--strategy", "ast"])
    with pytest.raises(SystemExit):
        parse_args()
