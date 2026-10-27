from evaluation.fulltext_diagnostic import (
    build_or_query,
    classify_query_terms,
    extract_query_terms,
)


def test_extract_query_terms_sanitizes_and_deduplicates_in_order() -> None:
    assert extract_query_terms(
        "Does claim_pending_items handle X-Tenant-ID, and claim_pending_items?"
    ) == [
        "Does",
        "claim_pending_items",
        "handle",
        "X",
        "Tenant",
        "ID",
        "and",
    ]


def test_classify_query_terms_reports_stops_stems_and_missing_terms() -> None:
    result = classify_query_terms(
        ["the", "customers", "claim_pending_items", "claim", "missing"],
        {
            "the": [],
            "customers": ["custom"],
            "claim_pending_items": ["claim", "pend", "item"],
            "claim": ["claim"],
            "missing": ["miss"],
        },
        {"customers", "claim_pending_items", "claim"},
    )

    assert result == {
        "dropped_stop_words": ["the"],
        "stemmed": ["customers -> custom", "missing -> miss"],
        "split_into_lexemes": ["claim_pending_items -> claim, pend, item"],
        "absent_from_corpus": ["the", "missing"],
    }


def test_build_or_query_quotes_sanitized_terms() -> None:
    assert build_or_query(["OR", "claim_pending_items"]) == (
        '"OR" OR "claim_pending_items"'
    )
    assert build_or_query([]) == ""
