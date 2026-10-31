from __future__ import annotations

import json

import pytest

import scripts.run_local_embedding_experiment as runner
from evaluation.local_embedding import (
    MODELS,
    cache_path,
    cache_record,
    fuse_rankings,
    rank_vectors,
    read_cache_record,
    require_development_records,
    retention_rules,
    validate_vector,
)

pytestmark = pytest.mark.evaluation


class FakeEmbedder:
    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions
        self.passage_inputs: list[str] = []
        self.query_inputs: list[str] = []

    def passage_embed(self, values: list[str], *, batch_size: int = 1):
        assert batch_size == runner.EMBED_BATCH_SIZE
        self.passage_inputs.extend(values)
        return ([1.0] * self.dimensions for _ in values)

    def query_embed(self, values: list[str], *, batch_size: int = 1):
        assert batch_size == runner.EMBED_BATCH_SIZE
        self.query_inputs.extend(values)
        return ([1.0] * self.dimensions for _ in values)


def test_cache_identity_labels_model_dimension_version_role_and_text(tmp_path) -> None:
    value = "def exact_source(): pass"
    first = cache_path(tmp_path, MODELS[0], "document", value)
    assert first != cache_path(tmp_path, MODELS[0], "query", value)
    assert first != cache_path(tmp_path, MODELS[0], "document", value + " ")
    assert first != cache_path(tmp_path, MODELS[1], "document", value)

    record = cache_record(MODELS[0], "document", value, [0.0] * MODELS[0].dimensions)
    assert record["embedding_model"] == MODELS[0].model_name
    assert record["dimensions"] == MODELS[0].dimensions
    assert record["library_version"] == "0.9.1"
    assert record["role"] == "document"
    assert value not in json.dumps(record)
    assert read_cache_record(record, MODELS[0], "document", value) == [
        0.0
    ] * MODELS[0].dimensions

    changed_version = dict(record, library_version="0.9.2")
    with pytest.raises(ValueError, match="identity"):
        read_cache_record(changed_version, MODELS[0], "document", value)


def test_vector_validation_rejects_bad_dimensions_nonfinite_and_booleans() -> None:
    with pytest.raises(ValueError, match="dimensions or values"):
        validate_vector([0.0], 2)
    with pytest.raises(ValueError, match="dimensions or values"):
        validate_vector([float("nan")], 1)
    with pytest.raises(ValueError, match="dimensions or values"):
        validate_vector([True], 1)


def test_development_records_reject_held_out_or_incomplete_rows() -> None:
    rows = [{"id": "dev-a"}, {"id": "dev-b"}]
    assert require_development_records(rows, {"dev-a", "dev-b"}, "development") == rows
    with pytest.raises(ValueError, match="development data only"):
        require_development_records(rows, {"dev-a", "dev-b"}, "held_out")
    with pytest.raises(ValueError, match="exactly match"):
        require_development_records([rows[0]], {"dev-a", "dev-b"}, "development")
    with pytest.raises(ValueError, match="exactly match"):
        require_development_records(
            [rows[0], {"id": "held-out"}],
            {"dev-a", "dev-b"},
            "development",
        )


def test_experiment_rejects_an_unregistered_manifest(tmp_path) -> None:
    with pytest.raises(ValueError, match="registered manifest"):
        runner._load_development_inputs(tmp_path / "manifest.json")


def test_fake_embedder_caches_only_requested_raw_development_text(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    model = MODELS[1]
    text = " query with exact case "
    embedder = FakeEmbedder(model.dimensions)
    monkeypatch.setattr(runner, "CACHE_ROOT", tmp_path)

    elapsed, count = runner._embed_missing(
        embedder,
        [text],
        "query",
        model,
        show_progress=True,
    )

    path = cache_path(tmp_path, model, "query", text)
    record = json.loads(path.read_text(encoding="utf-8"))
    progress = capsys.readouterr().out
    assert count == 1
    assert elapsed >= 0
    assert "item 1 of 1" in progress
    assert "seconds/item" in progress
    assert "ETA" in progress
    assert embedder.query_inputs == [text]
    assert embedder.passage_inputs == []
    assert record["text_sha256"]
    assert text not in path.read_text(encoding="utf-8")
    assert read_cache_record(record, model, "query", text) == [1.0] * model.dimensions


def test_embed_cli_defaults_to_all_logical_cpus_and_eight_items() -> None:
    args = runner._parser().parse_args(["embed"])

    assert args.threads == runner.DEFAULT_EMBED_THREADS
    assert args.batch_size == 8


def test_same_candidate_ranking_and_fusion_path_reconciles_control_baseline() -> None:
    chunks = [
        {
            "id": 1,
            "file_path": "src/a.py",
            "line_start": 1,
            "line_end": 2,
            "content": "first",
        },
        {
            "id": 2,
            "file_path": "src/b.py",
            "line_start": 1,
            "line_end": 2,
            "content": "second",
        },
    ]
    vectors = {"first": [1.0, 0.0], "second": [0.0, 1.0]}
    vector_results = rank_vectors(chunks, vectors, [1.0, 0.0])
    assert [row["id"] for row in vector_results] == [1, 2]
    fused = fuse_rankings(
        10,
        vector_results,
        [
            {
                "id": 2,
                "file_path": "src/b.py",
                "line_start": 1,
                "line_end": 2,
                "content": "second",
                "score": 1.0,
            }
        ],
    )
    assert [row["id"] for row in fused] == [2, 1]

    questions = [
        {"id": f"q{index}", "category": "direct"}
        for index in range(33)
    ]
    baseline = [{"id": f"q{index}", "label_rank": 1} for index in range(33)]
    per_question = {
        f"q{index}": {"rank": 1}
        for index in range(33)
    }
    identical, differences = runner._baseline_reconciliation(
        {"repo": questions},
        {"repo": baseline},
        {"repo": per_question},
    )
    assert identical == 33
    assert differences == []
    per_question["q32"]["rank"] = 2
    identical, differences = runner._baseline_reconciliation(
        {"repo": questions},
        {"repo": baseline},
        {"repo": per_question},
    )
    assert identical == 32
    assert differences[0]["development_ordinal"] == 33


def test_retention_rules_distinguish_r4_only_failure() -> None:
    control_repo = {"repo": {"hit_at_5": 0}}
    candidate_repo = {"repo": {"hit_at_5": 33}}
    control_ranks = [None] * 33
    candidate_ranks = [1] * 33
    bootstrap = {"lower": 0.5}

    decision = retention_rules(
        control_repo,
        candidate_repo,
        control_ranks,
        candidate_ranks,
        bootstrap,
        {"repo": [False] * 5},
        {"repo": [True, False, False, False, False]},
    )

    assert decision["rules"] == {
        "R1": True,
        "R2": True,
        "R3": True,
        "R4": False,
    }
    assert decision["outcome"] == (
        "retrieval-promising; guard needs per-model recalibration; control kept"
    )


def test_retention_rules_candidate_requires_all_four_rules() -> None:
    decision = retention_rules(
        {"repo": {"hit_at_5": 0}},
        {"repo": {"hit_at_5": 33}},
        [None] * 33,
        [1] * 33,
        {"lower": 0.5},
        {"repo": [False] * 5},
        {"repo": [False] * 5},
    )
    assert decision["rules"] == {
        "R1": True,
        "R2": True,
        "R3": True,
        "R4": True,
    }
    assert decision["outcome"].startswith("candidate: needs a separately registered")


def test_retention_rules_other_failures_keep_control() -> None:
    decision = retention_rules(
        {"repo": {"hit_at_5": 1}},
        {"repo": {"hit_at_5": 1}},
        [1] * 33,
        [1] * 33,
        {"lower": 0.0},
        {"repo": [False] * 5},
        {"repo": [False] * 5},
    )
    assert decision["rules"]["R1"] is False
    assert decision["outcome"] == "keep control"


def test_retention_rules_requires_paired_guard_decisions() -> None:
    with pytest.raises(ValueError, match="paired guard decisions"):
        retention_rules(
            {"repo": {"hit_at_5": 0}},
            {"repo": {"hit_at_5": 0}},
            [None],
            [None],
            {"lower": 0.0},
            {"repo": [False]},
            {"repo": [True, False]},
        )


def test_retention_r4_fails_when_a_new_unanswerable_is_accepted() -> None:
    decision = retention_rules(
        {"repo": {"hit_at_5": 0}},
        {"repo": {"hit_at_5": 0}},
        [None],
        [None],
        {"lower": 0.0},
        {"repo": [False]},
        {"repo": [True]},
    )
    assert decision["rules"]["R4"] is False
