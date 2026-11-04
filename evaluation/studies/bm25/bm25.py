"""Pure BM25 ranking and decision helpers for the item 14d comparison."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")
K1 = 1.2
B = 0.75
TOP_K = 5


def tokenize(text: str) -> tuple[str, ...]:
    """Return lowercase alphanumeric/identifier tokens without stemming."""
    return tuple(token.casefold() for token in TOKEN_PATTERN.findall(text))


@dataclass(frozen=True)
class BM25Index:
    documents: tuple[Mapping[str, Any], ...]
    frequencies: tuple[Counter[str], ...]
    lengths: tuple[int, ...]
    document_frequencies: Counter[str]
    average_length: float
    k1: float = K1
    b: float = B

    @classmethod
    def build(
        cls,
        documents: Sequence[Mapping[str, Any]],
        *,
        k1: float = K1,
        b: float = B,
    ) -> BM25Index:
        """Build a fixed-parameter index over documents with content and path fields."""
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 parameters require k1 > 0 and b in [0, 1]")
        rows = tuple(documents)
        frequencies = tuple(
            Counter(tokenize(str(document.get("content") or "")))
            for document in rows
        )
        document_frequencies: Counter[str] = Counter()
        for frequency in frequencies:
            document_frequencies.update(frequency.keys())
        lengths = tuple(sum(frequency.values()) for frequency in frequencies)
        average_length = sum(lengths) / len(lengths) if lengths else 0.0
        return cls(
            rows,
            frequencies,
            lengths,
            document_frequencies,
            average_length,
            k1,
            b,
        )

    def rank(self, query: str, *, limit: int = TOP_K) -> list[tuple[int, float]]:
        """Rank OR-matching documents by BM25, breaking ties by path and start line."""
        if limit < 1:
            raise ValueError("limit must be positive")
        query_terms = set(tokenize(query))
        if not query_terms or not self.documents or self.average_length == 0:
            return []

        scores: list[tuple[int, float]] = []
        count = len(self.documents)
        for index, frequency in enumerate(self.frequencies):
            score = 0.0
            for term in query_terms:
                term_frequency = frequency.get(term, 0)
                if not term_frequency:
                    continue
                document_frequency = self.document_frequencies[term]
                inverse_frequency = math.log(
                    1 + (count - document_frequency + 0.5) / (document_frequency + 0.5)
                )
                denominator = term_frequency + self.k1 * (
                    1 - self.b + self.b * self.lengths[index] / self.average_length
                )
                score += inverse_frequency * (
                    term_frequency * (self.k1 + 1) / denominator
                )
            if score > 0:
                scores.append((index, score))

        scores.sort(
            key=lambda row: (
                -row[1],
                str(self.documents[row[0]].get("file_path") or ""),
                int(self.documents[row[0]].get("line_start") or 0),
                row[0],
            )
        )
        return scores[:limit]


def decide_b1(
    control_by_repository: Mapping[str, Mapping[str, Any]],
    candidate_by_repository: Mapping[str, Mapping[str, Any]],
    pooled_mrr_difference: float,
    bootstrap_interval: Sequence[float],
    guard_unchanged: bool,
) -> dict[str, Any]:
    """Apply the four preregistered B1 decision conditions."""
    if sorted(control_by_repository) != sorted(candidate_by_repository):
        raise ValueError("Control and B1 repository sets must match")
    if len(bootstrap_interval) != 2:
        raise ValueError("Bootstrap interval must contain lower and upper bounds")
    conditions = {
        "R1_pooled_mrr_improves_by_at_least_0_030": pooled_mrr_difference >= 0.030,
        "R2_bootstrap_lower_bound_above_zero": float(bootstrap_interval[0]) > 0,
        "R3_no_repository_loses_more_than_one_hit_at_5": all(
            int(candidate_by_repository[repo]["hit_at_5_successes"])
            >= int(control_by_repository[repo]["hit_at_5_successes"]) - 1
            for repo in control_by_repository
        ),
        "R4_unanswerable_guard_outcomes_unchanged": guard_unchanged,
    }
    qualifies = all(conditions.values())
    return {
        "conditions": conditions,
        "qualifies": qualifies,
        "decision": (
            "candidate: a separately registered production comparison (14d-2) is justified"
            if qualifies
            else "keep control"
        ),
    }
