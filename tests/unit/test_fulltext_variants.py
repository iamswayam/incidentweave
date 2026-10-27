from __future__ import annotations

import pytest

from app.retrieval.fulltext_variants import (
    MAX_QUERY_TOKENS,
    build_c1_query,
    extract_query_tokens,
    split_identifier_text,
)


def test_extract_query_tokens_sanitizes_and_deduplicates_case_insensitively() -> None:
    assert extract_query_tokens("Foo foo_bar; FOO, x-y") == [
        "Foo",
        "foo_bar",
        "x",
        "y",
    ]


def test_build_c1_query_drops_stop_words_quotes_and_ors_tokens() -> None:
    query = build_c1_query(
        'How "OR" configured configured? AsyncSessionLocal',
        {"how"},
    )

    assert query.query_text == (
        '"OR" OR "configured" OR "AsyncSessionLocal"'
    )
    assert query.tokens == ("OR", "configured", "AsyncSessionLocal")
    assert query.truncated is False


def test_build_c1_query_truncates_after_stop_word_removal() -> None:
    question = " ".join(
        ["the", *(f"term{index}" for index in range(MAX_QUERY_TOKENS + 2))]
    )
    query = build_c1_query(question, {"the"})

    assert len(query.tokens) == MAX_QUERY_TOKENS
    assert query.truncated is True
    assert query.query_text.split(" OR ") == [
        f'"term{index}"' for index in range(MAX_QUERY_TOKENS)
    ]


def test_build_c1_query_requires_positive_token_cap() -> None:
    with pytest.raises(ValueError, match="token_cap"):
        build_c1_query("query", set(), token_cap=0)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (
            "claim_pending_items()",
            "claim_pending_items()\nclaim pending items",
        ),
        (
            "client = AsyncSessionLocal()",
            "client = AsyncSessionLocal()\nAsync Session Local",
        ),
        (
            "value = HTTPServer",
            "value = HTTPServer\nHTTP Server",
        ),
        ("plain words", "plain words"),
    ],
)
def test_split_identifier_text_appends_only_identifier_splits(
    content: str,
    expected: str,
) -> None:
    assert split_identifier_text(content) == expected

