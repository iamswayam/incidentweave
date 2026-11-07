from __future__ import annotations

from app.text import normalize_whitespace
from evaluation.end_to_end_checks import (
    Citation,
    RecordedRun,
    _jaccard,
    format_end_to_end_markdown,
    recorded_run_from_replay,
    summarize_end_to_end,
)
from evaluation.stats import wilson_interval


def _run(
    question_id: str,
    *,
    answerable: bool = True,
    outcome: str = "answered",
    citations: tuple[Citation, ...] = (),
    retrieved_ids: frozenset[str] = frozenset(),
    retrieved_texts: dict[str, str] | None = None,
    repeat_index: int = 1,
) -> RecordedRun:
    return RecordedRun(
        question_id=question_id,
        answerable=answerable,
        outcome=outcome,
        citations=citations,
        retrieved_chunk_ids=retrieved_ids,
        retrieved_chunk_texts=retrieved_texts or {},
        repeat_index=repeat_index,
    )


def test_quote_validity_uses_runtime_whitespace_and_minimum_length_rule() -> None:
    assert normalize_whitespace("alpha\t beta\n gamma") == "alpha beta gamma"
    record = _run(
        "quote-check",
        citations=(
            Citation("present", "alpha   beta\ngamma"),
            Citation("present", "missing phrase here"),
            Citation("present", "too short"),
            Citation("absent", "alpha beta gamma"),
        ),
        retrieved_ids=frozenset({"present"}),
        retrieved_texts={"present": "alpha beta gamma; other chunk text"},
    )

    summary = summarize_end_to_end([record])

    assert summary["check_a"]["submitted_citations"] == 4
    assert summary["check_a"]["valid_citations"] == 1
    assert summary["check_a"]["citation_quote_validity"] == {
        "successes": 1,
        "denominator": 4,
        "rate": 0.25,
        "wilson_95": list(wilson_interval(1, 4)),
    }
    assert summary["check_b"]["retrieved_citations"] == 3


def test_no_citations_have_undefined_rates() -> None:
    summary = summarize_end_to_end([_run("empty")])

    assert summary["check_a"]["citation_quote_validity"]["rate"] is None
    assert summary["check_b"]["retrieval_grounded_citation_rate"]["rate"] is None
    assert summary["check_a"]["answered_with_citations"]["rate"] == 0


def test_correctness_rates_exclude_only_degraded_outcomes() -> None:
    records = [
        _run("a-answer", outcome="answered"),
        _run("a-refused", outcome="refused_guard"),
        _run("u-answer", answerable=False, outcome="answered"),
        _run("u-refused", answerable=False, outcome="abstained_model"),
        _run("u-error", answerable=False, outcome="error"),
        _run("a-generation-down", outcome="generation_unavailable"),
        _run("u-embedding-down", answerable=False, outcome="embedding_unavailable"),
    ]

    check = summarize_end_to_end(records)["check_c"]

    assert check["degraded_outcome_counts"] == {
        "embedding_unavailable": 1,
        "generation_unavailable": 1,
    }
    assert check["false_answer_rate"]["successes"] == 1
    assert check["false_answer_rate"]["denominator"] == 3
    assert check["false_refusal_rate"]["successes"] == 1
    assert check["false_refusal_rate"]["denominator"] == 2
    assert check["overall_correctness"]["successes"] == 2
    assert check["overall_correctness"]["denominator"] == 5
    assert check["provider_error_count"] == 1
    assert check["false_answer_rate"]["wilson_95"] is not None


def test_zero_correctness_denominators_are_undefined() -> None:
    check = summarize_end_to_end(
        [_run("degraded", answerable=False, outcome="generation_unavailable")]
    )["check_c"]

    assert check["false_answer_rate"]["rate"] is None
    assert check["false_refusal_rate"]["rate"] is None
    assert check["overall_correctness"]["wilson_95"] is None


def test_stability_covers_identical_flip_empty_and_incomplete_runs() -> None:
    records = [
        *[
            _run(
                "stable",
                citations=(Citation("same", "quote text here"),),
                retrieved_ids=frozenset({"same"}),
                repeat_index=repeat,
            )
            for repeat in (1, 2, 3)
        ],
        _run("flip", outcome="answered", citations=(Citation("a", "quote text here"),)),
        _run(
            "flip",
            outcome="refused_guard",
            citations=(Citation("b", "quote text here"),),
            repeat_index=2,
        ),
        _run("flip", outcome="answered", repeat_index=3),
        *[
            _run(
                "empty",
                outcome="refused_guard",
                answerable=False,
                repeat_index=repeat,
            )
            for repeat in (1, 2, 3)
        ],
        _run("single", repeat_index=2),
    ]

    check = summarize_end_to_end(records)["check_d"]

    assert check["question_set_count"] == 4
    assert check["complete_question_set_count"] == 3
    assert check["incomplete_question_set_count"] == 1
    assert check["stable_outcome_questions"]["successes"] == 2
    assert check["stable_outcome_questions"]["denominator"] == 3
    assert check["flip_questions"] == {"count": 1, "denominator": 3}
    assert check["mean_cited_chunk_jaccard"] == {"mean": 0.5, "question_count": 2}


def test_both_empty_citation_sets_have_jaccard_one() -> None:
    assert _jaccard(frozenset(), frozenset()) == 1.0


def test_persisted_replay_converter_uses_raw_citations_and_prompt_chunks() -> None:
    audit = {
        "outcome": "answered",
        "raw_response": (
            '{"claims":[{"text":"claim","evidence":'
            '[{"chunk_id":"12","quote":"a sufficiently long quote"}]}]}'
        ),
        "trace": {"outcome": "answered"},
        "chunk_records": [
            {"chunk_id": "12", "kept_in_prompt": True},
            {"chunk_id": "13", "kept_in_prompt": False},
        ],
    }

    record = recorded_run_from_replay(
        audit,
        question_id="persisted",
        answerable=True,
        repeat_index=1,
        retrieved_chunk_texts={
            "12": "a sufficiently long quote appears here",
            "13": "not supplied to the prompt",
        },
    )

    assert record.citations == (Citation("12", "a sufficiently long quote"),)
    assert record.retrieved_chunk_ids == frozenset({"12"})
    assert set(record.retrieved_chunk_texts) == {"12"}


def test_report_is_deterministic_and_contains_registered_denominators() -> None:
    records = [
        _run(
            "q",
            citations=(Citation("c", "a sufficiently long quote"),),
            retrieved_ids=frozenset({"c"}),
            retrieved_texts={"c": "a sufficiently long quote in the chunk"},
            repeat_index=repeat,
        )
        for repeat in (1, 2, 3)
    ]
    summary = summarize_end_to_end(records)

    first = format_end_to_end_markdown(summary)
    second = format_end_to_end_markdown(summary)

    assert first.encode("utf-8") == second.encode("utf-8")
    assert "Citation quote validity: 1.000 (3/3)" in first
    assert "Retrieval-grounded citation rate: 1.000 (3/3)" in first
    assert "False-answer rate:" in first and "Wilson 95%" in first
    assert "False-refusal rate:" in first
    assert "Overall correctness:" in first
    assert "Stable outcomes:" in first
    assert "Mean cited-chunk-set pairwise Jaccard:" in first
    assert "Answered/refused flips:" in first
