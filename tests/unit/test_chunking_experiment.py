from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from evaluation import chunking_experiment as experiment
from evaluation.retrieval_eval import run_offline_retrieval
from scripts import run_chunking_experiment


def _chunk(
    text: str,
    *,
    path: str = "src/a.py",
    line_start: int = 1,
    line_end: int = 1,
    content: str = "raw code",
) -> dict[str, Any]:
    return {
        "embedding_text": text,
        "file_path": path,
        "line_start": line_start,
        "line_end": line_end,
        "content": content,
        "symbol": None,
        "kind": "lines",
    }


def test_discover_sources_excludes_requested_prefix(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "fixtures").mkdir(parents=True)
    (tmp_path / "src" / "main.py").write_text("main\n", encoding="utf-8")
    (tmp_path / "tests" / "fixtures" / "sample.py").write_text(
        "fixture\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_sample.py").write_text("test\n", encoding="utf-8")

    assert experiment.discover_sources(
        tmp_path,
        exclude_prefixes=("tests/fixtures/",),
    ) == {
        "src/main.py": "main\n",
        "tests/test_sample.py": "test\n",
    }


def test_build_strategy_chunks_counts_secret_skips() -> None:
    secret_value = "AIza" + "A" * 35
    chunks, skipped = experiment.build_strategy_chunks_and_count(
        "s0_lines_60_10",
        {
            "a.py": f"KEY = '{secret_value}'\n",
            "b.py": "VALUE = 1\n",
        },
    )

    assert skipped == 1
    assert [chunk["file_path"] for chunk in chunks] == ["b.py"]
    assert secret_value not in chunks[0]["content"]


def test_check_s0_reproduces_baseline_and_reports_mismatches() -> None:
    chunk = _chunk("raw")
    fixture = {"chunks": [chunk]}

    assert experiment.check_s0_reproduces_baseline([chunk], fixture) is None
    with pytest.raises(RuntimeError, match="S0 does not reproduce") as error:
        experiment.check_s0_reproduces_baseline(
            [_chunk("different", content="other")],
            fixture,
        )
    assert "src/a.py:1-1" in str(error.value)
    assert "first differences" in str(error.value)


def test_plan_embeddings_reuses_cache_and_baseline_in_hash_order(
    tmp_path: Path,
) -> None:
    baseline_text = "baseline content"
    cached_text = "cached"
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cached_hash = hashlib.sha256(cached_text.encode("utf-8")).hexdigest()
    (cache_dir / f"{cached_hash}.json").write_text("[0.1,0.2]", encoding="utf-8")
    chunks = {
        "repo-a": {
            "s0": [
                _chunk("zebra"),
                _chunk("alpha"),
                _chunk(cached_text),
                _chunk(baseline_text),
            ]
        }
    }
    baseline = {
        "repo-a": {
            "chunks": [
                {
                    "content": baseline_text,
                    "embedding": [1.0],
                }
            ]
        }
    }

    planned = experiment.plan_embeddings(chunks, baseline, cache_dir)

    assert planned == sorted(["zebra", "alpha"], key=lambda text: hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest())


@pytest.mark.parametrize(
    ("texts", "protocol"),
    [
        (
            ["a", "b", "c"],
            {
                "embedding": {
                    "batch_size": 2,
                    "max_texts": 4,
                    "max_batch_requests": 1,
                }
            },
        ),
        (
            ["a", "b", "c"],
            {
                "embedding": {
                    "batch_size": 2,
                    "max_texts": 2,
                    "max_batch_requests": 2,
                }
            },
        ),
    ],
)
def test_embed_missing_enforces_caps_before_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    texts: list[str],
    protocol: dict[str, Any],
) -> None:
    calls: list[list[str]] = []

    async def fake_embed(batch: list[str]) -> list[list[float]]:
        calls.append(batch)
        return [[1.0] for _ in batch]

    monkeypatch.setattr(experiment, "load_protocol", lambda: protocol)
    with pytest.raises(ValueError, match="exceeds protocol caps"):
        asyncio.run(experiment.embed_missing(texts, tmp_path, fake_embed))
    assert calls == []
    assert list(tmp_path.iterdir()) == []


def test_embed_missing_batches_by_fifty_and_keeps_completed_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = {
        "embedding": {
            "batch_size": 50,
            "max_texts": 700,
            "max_batch_requests": 20,
        }
    }
    monkeypatch.setattr(experiment, "load_protocol", lambda: protocol)
    texts = [f"text-{index}" for index in range(105)]
    calls: list[list[str]] = []

    async def interrupted_embed(batch: list[str]) -> list[list[float]]:
        calls.append(batch)
        if len(calls) == 2:
            cached_hash = hashlib.sha256(texts[0].encode("utf-8")).hexdigest()
            assert (tmp_path / f"{cached_hash}.json").is_file()
            raise RuntimeError("interrupted")
        return [[float(len(text))] for text in batch]

    with pytest.raises(RuntimeError, match="interrupted"):
        asyncio.run(
            experiment.embed_missing(texts, tmp_path, interrupted_embed)
        )
    assert [len(batch) for batch in calls] == [50, 50]
    assert len(list(tmp_path.glob("*.json"))) == 50

    resumed_calls: list[int] = []

    async def fake_embed(batch: list[str]) -> list[list[float]]:
        resumed_calls.append(len(batch))
        return [[1.0] for _ in batch]

    asyncio.run(experiment.embed_missing(texts[50:], tmp_path, fake_embed))
    assert resumed_calls == [50, 5]
    assert len(list(tmp_path.glob("*.json"))) == 105


def test_build_candidate_fixture_keeps_raw_content_and_is_deterministic(
    tmp_path: Path,
) -> None:
    baseline = {
        "meta": {"pinned_sha": "pinned"},
        "chunks": [],
        "queries": {"q1": [0.5, 0.5]},
    }
    chunks = [
        _chunk(
            "enriched path and symbol",
            content="RAW CONTENT",
            path="src/module.py",
            line_start=4,
            line_end=5,
        )
    ]
    vectors = {
        hashlib.sha256(b"enriched path and symbol").hexdigest(): [
            0.12345678,
            0.9,
        ]
    }
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"

    first_hash, first_size = experiment.build_candidate_fixture(
        "repo",
        "s3_ast_v1_embed_text",
        chunks,
        baseline,
        vectors,
        10_000,
        output_root=first_root,
    )
    second_hash, second_size = experiment.build_candidate_fixture(
        "repo",
        "s3_ast_v1_embed_text",
        chunks,
        baseline,
        vectors,
        10_000,
        output_root=second_root,
    )
    first_path = (
        first_root
        / "evaluation"
        / "experiments"
        / "chunking"
        / "fixtures"
        / "repo"
        / "s3_ast_v1_embed_text.json.gz"
    )
    second_path = (
        second_root
        / "evaluation"
        / "experiments"
        / "chunking"
        / "fixtures"
        / "repo"
        / "s3_ast_v1_embed_text.json.gz"
    )
    first_data = json.loads(gzip.decompress(first_path.read_bytes()))
    second_data = json.loads(gzip.decompress(second_path.read_bytes()))

    assert first_path.read_bytes() == second_path.read_bytes()
    assert first_hash == second_hash
    assert first_size == second_size
    assert first_data == second_data
    assert first_data["chunks"][0]["content"] == "RAW CONTENT"
    assert first_data["chunks"][0]["embedding"] == [0.123457, 0.9]
    assert first_data["queries"] == baseline["queries"]
    assert "built_at" not in first_data["meta"]


def test_compute_metrics_cost_coverage_density_test_share_and_distance() -> None:
    sources = {
        "src/a.py": "aa\nbbb\nc\ndddd\n",
        "tests/test_sample.py": "xx\nyyy\n",
    }
    report = {
        "metadata": {"repo_id": "repo"},
        "questions": [
            {
                "id": "q1",
                "category": "direct",
                "span_rank": 1,
                "span_hits": {"1": True, "3": True, "5": True},
                "retrieved": [
                    {
                        "file_path": "src/a.py",
                        "line_start": 1,
                        "line_end": 3,
                    },
                    {
                        "file_path": "src/a.py",
                        "line_start": 3,
                        "line_end": 4,
                    },
                    {
                        "file_path": "tests/test_sample.py",
                        "line_start": 1,
                        "line_end": 2,
                    },
                ],
            },
            {
                "id": "q2",
                "category": "unanswerable_far",
                "span_rank": None,
                "span_hits": {"1": False, "3": False, "5": False},
                "retrieved": [
                    {
                        "file_path": "src/a.py",
                        "line_start": 4,
                        "line_end": 4,
                    }
                ],
            },
        ],
    }
    questions = [
        {
            "id": "q1",
            "category": "direct",
            "relevant_spans": [
                {"file_path": "src/a.py", "line_start": 2, "line_end": 3}
            ],
        },
        {
            "id": "q2",
            "category": "unanswerable_far",
            "relevant_spans": [],
        },
    ]
    fixture = {
        "chunks": [
            {
                "file_path": "src/a.py",
                "line_start": 1,
                "line_end": 3,
                "embedding": [1.0, 0.0],
            },
            {
                "file_path": "tests/test_sample.py",
                "line_start": 1,
                "line_end": 2,
                "embedding": [-1.0, 0.0],
            },
        ],
        "queries": {"q1": [1.0, 0.0], "q2": [-1.0, 0.0]},
    }

    metrics = experiment.compute_metrics(
        report,
        sources,
        questions,
        fixture,
        fixture_bytes=123,
    )

    assert metrics["cost"] == {"count": 1, "mean": 21.0, "p95": 21}
    assert metrics["coverage_at_5"]["rate"] == 1.0
    assert metrics["density_at_5"]["rate"] == pytest.approx(2 / 6)
    assert metrics["top1_density"]["rate"] == pytest.approx(2 / 3)
    assert metrics["test_share"]["rate"] == pytest.approx(1 / 3)
    assert metrics["nearest_chunk_cosine_distance"]["answerable"] == {
        "min": 0.0,
        "median": 0.0,
        "max": 0.0,
    }
    assert metrics["nearest_chunk_cosine_distance"]["unanswerable"] == {
        "min": 0.0,
        "median": 0.0,
        "max": 0.0,
    }
    assert metrics["chunk_statistics"]["fixture_bytes"] == 123


def test_paired_statistics_is_seeded_and_uses_exact_sign_test() -> None:
    protocol = {
        "statistics": {
            "bootstrap_seed": 20261026,
            "bootstrap_resamples": 100,
            "bootstrap_interval": 0.95,
        }
    }
    candidate_rr = [1.0, 0.5, 0.0]
    s0_rr = [0.5, 0.5, 1.0]

    first = experiment.paired_statistics(candidate_rr, s0_rr, protocol)
    second = experiment.paired_statistics(candidate_rr, s0_rr, protocol)

    assert first == second
    assert first["wins"] == 1
    assert first["losses"] == 1
    assert first["ties"] == 1
    assert first["sign_test_p_value"] == 1.0
    assert first["delta_mrr"] == pytest.approx(-1 / 6)
    assert len(first["bootstrap_interval"]) == 2


def _selection_results(
    *,
    s1_repo_hit5: int = 8,
    s1_repo_mrr: float = 0.7,
    s1_pooled_mrr: float = 0.7,
    s1_mean_cost: float = 120.0,
    s1_p95_cost: float = 240.0,
    s2_pooled_mrr: float = 0.62,
) -> dict[str, Any]:
    def result(
        repo_hit5: int,
        repo_mrr: float,
        pooled_mrr: float,
        mean_cost: float,
        p95_cost: float,
    ) -> dict[str, Any]:
        repo = {
            "retrieval": {
                "hit_at_5": {"successes": repo_hit5},
                "mrr": repo_mrr,
            }
        }
        pooled = {
            "retrieval": {
                "hit_at_5": {"successes": repo_hit5},
                "mrr": pooled_mrr,
            },
            "cost": {"mean": mean_cost, "p95": p95_cost},
        }
        return {"repositories": {"repo": repo}, "pooled": pooled}

    return {
        "s0_lines_60_10": result(8, 0.6, 0.6, 100.0, 200.0),
        "s1_lines_100_20": result(
            s1_repo_hit5,
            s1_repo_mrr,
            s1_pooled_mrr,
            s1_mean_cost,
            s1_p95_cost,
        ),
        "s2_ast_v1": result(8, 0.7, s2_pooled_mrr, 100.0, 200.0),
        "s3_ast_v1_embed_text": result(8, 0.7, 0.62, 100.0, 200.0),
    }


def _selection_protocol() -> dict[str, Any]:
    return {
        "strategies": [
            "s0_lines_60_10",
            "s1_lines_100_20",
            "s2_ast_v1",
            "s3_ast_v1_embed_text",
        ],
        "repositories": ["repo"],
        "simplicity_order": [
            "s0_lines_60_10",
            "s1_lines_100_20",
            "s2_ast_v1",
            "s3_ast_v1_embed_text",
        ],
        "rule": {
            "max_repo_hit5_loss": 1,
            "max_repo_mrr_loss": 0.03,
            "min_pooled_delta_mrr": 0.03,
            "max_cost_ratio_mean": 1.5,
            "max_cost_ratio_p95": 1.5,
            "tie_epsilon": 1e-9,
        },
    }


def test_select_winner_chooses_clear_candidate() -> None:
    decision = experiment.select_winner(
        _selection_results(),
        _selection_protocol(),
    )
    assert decision["winner"] == "s1_lines_100_20"
    assert decision["conditions"]["s1_lines_100_20"]["qualifies"] is True


@pytest.mark.parametrize(
    ("overrides", "failed_condition"),
    [
        ({"s1_repo_hit5": 6}, "repository_hit5_loss"),
        ({"s1_repo_mrr": 0.55}, "repository_mrr_loss"),
        ({"s1_pooled_mrr": 0.62}, "pooled_mrr_gain"),
        ({"s1_mean_cost": 151.0}, "pooled_mean_cost"),
        ({"s1_p95_cost": 301.0}, "pooled_p95_cost"),
    ],
)
def test_select_winner_rejects_each_rule_condition_independently(
    overrides: dict[str, Any],
    failed_condition: str,
) -> None:
    decision = experiment.select_winner(
        _selection_results(**overrides),
        _selection_protocol(),
    )
    conditions = decision["conditions"]["s1_lines_100_20"]
    assert conditions[failed_condition] is False
    assert sum(value is False for key, value in conditions.items() if key != "qualifies") == 1


def test_select_winner_uses_simplicity_order_for_mrr_ties() -> None:
    results = _selection_results(s1_pooled_mrr=0.7, s2_pooled_mrr=0.7)
    decision = experiment.select_winner(results, _selection_protocol())

    assert decision["qualifiers"] == ["s1_lines_100_20", "s2_ast_v1"]
    assert decision["winner"] == "s1_lines_100_20"


def test_select_winner_retains_s0_when_no_candidate_qualifies() -> None:
    decision = experiment.select_winner(
        _selection_results(s1_pooled_mrr=0.62, s2_pooled_mrr=0.62),
        _selection_protocol(),
    )
    assert decision["winner"] == "s0_lines_60_10"
    assert decision["status"] == "S0 retained"


def test_embed_command_requires_explicit_confirmation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run_chunking_experiment.main(["embed"]) == 2
    assert "--confirm-embedding-calls" in capsys.readouterr().err


def test_run_offline_retrieval_only_records_results_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evaluation.retrieval_eval as retrieval_eval

    fixture = {
        "meta": {"chunk_count": 1, "question_count": 1},
        "chunks": [],
        "queries": {"q1": [0.1]},
    }
    question = {
        "id": "q1",
        "category": "direct",
        "question": "find the function",
        "relevant": [{"file_path": "src/a.py", "substring": "value"}],
        "relevant_spans": [
            {"file_path": "src/a.py", "line_start": 1, "line_end": 1}
        ],
    }

    class FakeSession:
        def __init__(self) -> None:
            self.added: list[Any] = []

        async def __aenter__(self) -> FakeSession:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def add(self, value: Any) -> None:
            self.added.append(value)

        def add_all(self, _values: list[Any]) -> None:
            return None

        async def flush(self) -> None:
            for value in self.added:
                if isinstance(value, retrieval_eval.Repository):
                    value.id = 1

        async def commit(self) -> None:
            return None

    async def fake_delete(_name: str) -> None:
        return None

    async def fake_search(*_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "file_path": "src/a.py",
                "line_start": 1,
                "line_end": 1,
                "content": "value = 1",
            }
        ]

    monkeypatch.setattr(retrieval_eval, "_delete_fixture_repository", fake_delete)
    monkeypatch.setattr(retrieval_eval, "load_fixture", lambda _path: fixture)
    monkeypatch.setattr(
        retrieval_eval,
        "load_golden_set",
        lambda _path: {"pinned_sha": "abc", "questions": [question]},
    )
    monkeypatch.setattr(
        retrieval_eval,
        "questions_for_split",
        lambda *_args, **_kwargs: [question],
    )
    monkeypatch.setattr(retrieval_eval, "AsyncSessionLocal", FakeSession)
    monkeypatch.setattr(retrieval_eval, "hybrid_search", fake_search)
    entry = {
        "id": "repo",
        "fixture": {"path": "fixture.json.gz"},
        "questions": {"path": "questions.json"},
        "splits": {"development": ["q1"]},
    }

    default_report = asyncio.run(
        run_offline_retrieval(
            fixture_path=Path("fixture.json.gz"),
            golden_path=Path("questions.json"),
            repo_id="repo",
            split="development",
            entry=entry,
        )
    )
    recorded_report = asyncio.run(
        run_offline_retrieval(
            fixture_path=Path("fixture.json.gz"),
            golden_path=Path("questions.json"),
            repo_id="repo",
            split="development",
            entry=entry,
            record_retrieved=True,
        )
    )

    assert "retrieved" not in default_report["questions"][0]
    assert recorded_report["questions"][0]["retrieved"] == [
        {
            "file_path": "src/a.py",
            "line_start": 1,
            "line_end": 1,
        }
    ]
