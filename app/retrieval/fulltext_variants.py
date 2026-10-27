"""Versioned, opt-in helpers for full-text ablation variants."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Collection

QUERY_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")
ACRONYM_BOUNDARY_PATTERN = re.compile(r"([A-Z]+)([A-Z][a-z])")
CAMEL_BOUNDARY_PATTERN = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
MAX_QUERY_TOKENS = 32
SEARCHABLE_TEXT_VERSION = "identifier-split-v1"


@dataclass(frozen=True)
class BuiltFulltextQuery:
    query_text: str
    tokens: tuple[str, ...]
    truncated: bool


def extract_query_tokens(query: str) -> list[str]:
    """Return unique sanitized query tokens in first-occurrence order."""

    tokens: list[str] = []
    seen: set[str] = set()
    for token in QUERY_TOKEN_PATTERN.findall(query):
        normalized = token.casefold()
        if normalized not in seen:
            tokens.append(token)
            seen.add(normalized)
    return tokens


def build_c1_query(
    question: str,
    stop_words: Collection[str],
    *,
    token_cap: int = MAX_QUERY_TOKENS,
) -> BuiltFulltextQuery:
    """Build the protocol's quoted OR query from non-stop sanitized tokens."""

    if token_cap < 1:
        raise ValueError("token_cap must be greater than zero")
    stop_words_normalized = {word.casefold() for word in stop_words}
    filtered = [
        token
        for token in extract_query_tokens(question)
        if token.casefold() not in stop_words_normalized
    ]
    truncated = len(filtered) > token_cap
    tokens = tuple(filtered[:token_cap])
    query_text = " OR ".join(f'"{token}"' for token in tokens)
    return BuiltFulltextQuery(query_text, tokens, truncated)


def split_identifier_text(content: str) -> str:
    """Append split snake_case and camelCase identifiers to chunk text."""

    additions: list[str] = []
    for identifier in QUERY_TOKEN_PATTERN.findall(content):
        if (
            "_" not in identifier
            and not ACRONYM_BOUNDARY_PATTERN.search(identifier)
            and not CAMEL_BOUNDARY_PATTERN.search(identifier)
        ):
            continue
        camel_spaced = ACRONYM_BOUNDARY_PATTERN.sub(r"\1 \2", identifier)
        camel_spaced = CAMEL_BOUNDARY_PATTERN.sub(" ", camel_spaced)
        pieces = [
            part
            for segment in camel_spaced.split("_")
            for part in segment.split()
            if part
        ]
        if len(pieces) > 1:
            additions.append(" ".join(pieces))
    if not additions:
        return content
    return f"{content}\n{' '.join(additions)}"
