import math

import pytest

from evaluation.bm25 import BM25Index, decide_b1, tokenize


def test_tokenize_keeps_identifiers_and_lowercases() -> None:
    assert tokenize("HTTPServer snake_case CamelCase 42") == (
        "httpserver",
        "snake_case",
        "camelcase",
        "42",
    )


def test_bm25_uses_fixed_score_and_or_matching() -> None:
    documents = [
        {"content": "alpha alpha beta", "file_path": "a.py", "line_start": 1},
        {"content": "alpha gamma", "file_path": "b.py", "line_start": 1},
        {"content": "delta epsilon", "file_path": "c.py", "line_start": 1},
    ]
    index = BM25Index.build(documents)

    ranked = index.rank("alpha")

    assert [row[0] for row in ranked] == [0, 1]
    expected_idf = math.log(1 + (3 - 2 + 0.5) / (2 + 0.5))
    expected_first = expected_idf * (
        2 * (1.2 + 1)
        / (2 + 1.2 * (1 - 0.75 + 0.75 * 3 / (7 / 3)))
    )
    assert ranked[0][1] == pytest.approx(expected_first)
    expected_second = expected_idf * (
        1.2 + 1
    ) / (1 + 1.2 * (1 - 0.75 + 0.75 * 2 / (7 / 3)))
    assert ranked[1][1] == pytest.approx(expected_second)
    assert [row[0] for row in index.rank("alpha epsilon")] == [2, 0, 1]


def test_bm25_ties_use_path_then_start_line() -> None:
    index = BM25Index.build(
        [
            {"content": "alpha", "file_path": "z.py", "line_start": 1},
            {"content": "alpha", "file_path": "a.py", "line_start": 5},
            {"content": "alpha", "file_path": "a.py", "line_start": 2},
        ]
    )

    assert [index.documents[i]["line_start"] for i, _ in index.rank("alpha")] == [
        2,
        5,
        1,
    ]


def test_bm25_empty_query_and_empty_corpus_return_no_results() -> None:
    assert BM25Index.build([{"content": "some text"}]).rank("___") == []
    assert BM25Index.build([]).rank("some text") == []


@pytest.mark.parametrize(
    ("delta", "interval", "hit5", "guard", "expected"),
    [
        (0.03, [0.001, 0.1], 9, True, True),
        (0.0299, [0.001, 0.1], 9, True, False),
        (0.03, [0.0, 0.1], 9, True, False),
        (0.03, [0.001, 0.1], 8, True, False),
        (0.03, [0.001, 0.1], 9, False, False),
    ],
)
def test_decide_b1_requires_every_registered_condition(
    delta: float,
    interval: list[float],
    hit5: int,
    guard: bool,
    expected: bool,
) -> None:
    control = {"repo": {"hit_at_5_successes": 10}}
    candidate = {"repo": {"hit_at_5_successes": hit5}}

    assert decide_b1(control, candidate, delta, interval, guard)["qualifies"] is expected
