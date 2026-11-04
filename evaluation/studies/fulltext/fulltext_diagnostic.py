"""Pure helpers for diagnosing PostgreSQL full-text query terms."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

QUERY_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def extract_query_terms(query: str) -> list[str]:
    """Return unique sanitized alphanumeric/underscore terms in source order."""

    terms: list[str] = []
    seen: set[str] = set()
    for term in QUERY_TOKEN_PATTERN.findall(query):
        normalized = term.casefold()
        if normalized not in seen:
            terms.append(term)
            seen.add(normalized)
    return terms


def classify_query_terms(
    terms: Sequence[str],
    lexemes_by_term: Mapping[str, Sequence[str]],
    corpus_terms: set[str],
) -> dict[str, list[str]]:
    """Classify query terms using PostgreSQL lexemes and exact corpus tokens."""

    dropped_stop_words: list[str] = []
    stemmed: list[str] = []
    split_into_lexemes: list[str] = []
    absent_from_corpus: list[str] = []
    normalized_corpus_terms = {term.casefold() for term in corpus_terms}

    for term in terms:
        lexemes = list(lexemes_by_term.get(term, ()))
        if not lexemes:
            dropped_stop_words.append(term)
        elif len(lexemes) > 1:
            split_into_lexemes.append(f"{term} -> {', '.join(lexemes)}")
        elif any(lexeme.casefold() != term.casefold() for lexeme in lexemes):
            stemmed.append(f"{term} -> {', '.join(lexemes)}")
        if term.casefold() not in normalized_corpus_terms:
            absent_from_corpus.append(term)

    return {
        "dropped_stop_words": dropped_stop_words,
        "stemmed": stemmed,
        "split_into_lexemes": split_into_lexemes,
        "absent_from_corpus": absent_from_corpus,
    }


def build_or_query(terms: Sequence[str]) -> str:
    """Build a websearch query that ORs only sanitized tokens."""

    if not terms:
        return ""
    # Quoting tokens keeps a literal term such as "OR" from becoming an operator.
    return " OR ".join(f'"{term}"' for term in terms)
