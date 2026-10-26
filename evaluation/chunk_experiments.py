"""Chunking strategies supported by the evaluation harness only."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from app.retrieval.chunking import (
    ChunkSpec,
    ast_chunk_specs,
    embedding_text,
    line_window_specs,
)

DEFAULT_STRATEGY = "baseline"


@dataclass(frozen=True)
class ChunkingStrategy:
    name: str
    chunk_size: int
    overlap: int
    evaluation_repository: str


STRATEGIES = {
    "baseline": ChunkingStrategy(
        name="baseline",
        chunk_size=60,
        overlap=10,
        evaluation_repository="incidentweave-eval",
    ),
    "w100_o20": ChunkingStrategy(
        name="w100_o20",
        chunk_size=100,
        overlap=20,
        evaluation_repository="incidentweave-eval-w100_20",
    ),
}
STRATEGY_CHOICES = tuple(STRATEGIES)
SPLIT_CHOICES = ("development", "held_out", "smoke", "all")
EVALUATION_REPOSITORIES = frozenset(
    strategy.evaluation_repository for strategy in STRATEGIES.values()
)


@dataclass(frozen=True)
class CandidateStrategy:
    name: str
    chunker: str
    line_size: int | None
    line_overlap: int | None
    embedding_text: str


CANDIDATE_STRATEGIES = {
    "s0_lines_60_10": CandidateStrategy(
        "s0_lines_60_10", "lines", 60, 10, "raw"
    ),
    "s1_lines_100_20": CandidateStrategy(
        "s1_lines_100_20", "lines", 100, 20, "raw"
    ),
    "s2_ast_v1": CandidateStrategy("s2_ast_v1", "ast", None, None, "raw"),
    "s3_ast_v1_embed_text": CandidateStrategy(
        "s3_ast_v1_embed_text",
        "ast",
        None,
        None,
        "embed-path-symbol-v1",
    ),
}


def get_candidate_strategy(name: str) -> CandidateStrategy:
    try:
        return CANDIDATE_STRATEGIES[name]
    except KeyError as exc:
        choices = ", ".join(CANDIDATE_STRATEGIES)
        raise ValueError(
            f"Unsupported candidate strategy {name!r}; choose from: {choices}"
        ) from exc


def candidate_chunk_specs(name: str, source: str) -> list[ChunkSpec]:
    strategy = get_candidate_strategy(name)
    if strategy.chunker == "lines":
        return line_window_specs(
            source,
            size=strategy.line_size or 60,
            overlap=strategy.line_overlap or 10,
        )
    return ast_chunk_specs(source)


def candidate_embedding_text(
    name: str,
    spec: ChunkSpec,
    file_path: str,
) -> str:
    strategy = get_candidate_strategy(name)
    if strategy.embedding_text == "raw":
        return spec.content
    return embedding_text(spec, file_path)


def get_strategy(name: str = DEFAULT_STRATEGY) -> ChunkingStrategy:
    """Return a supported strategy or raise a clear validation error."""

    if not isinstance(name, str) or name not in STRATEGIES:
        choices = ", ".join(STRATEGY_CHOICES)
        raise ValueError(f"Unsupported chunking strategy {name!r}; choose from: {choices}")
    return STRATEGIES[name]


def resolve_evaluation_repository(
    repository_name: str | None = None,
    strategy: str = DEFAULT_STRATEGY,
) -> str:
    """Return the one allowlisted evaluation repository for a strategy."""

    selected = get_strategy(strategy)
    repository = (
        selected.evaluation_repository
        if repository_name is None
        else repository_name
    )
    if not isinstance(repository, str) or repository not in EVALUATION_REPOSITORIES:
        choices = ", ".join(sorted(EVALUATION_REPOSITORIES))
        raise ValueError(
            f"Evaluation repository {repository!r} is not allowed; choose from: {choices}"
        )
    if repository != selected.evaluation_repository:
        raise ValueError(
            f"Strategy {selected.name!r} requires evaluation repository "
            f"{selected.evaluation_repository!r}"
        )
    return repository


def resolve_split(
    split: str = "development",
    *,
    confirm_frozen_heldout: bool = False,
) -> str:
    """Validate split access and require explicit confirmation for frozen data."""

    if split not in SPLIT_CHOICES:
        choices = ", ".join(SPLIT_CHOICES)
        raise ValueError(f"Unsupported evaluation split {split!r}; choose from: {choices}")
    if split in {"held_out", "all"}:
        if not confirm_frozen_heldout:
            raise ValueError(
                f"Split {split!r} includes frozen held-out questions; "
                "pass --confirm-frozen-heldout to proceed"
            )
        print(
            f"WARNING: evaluating split {split!r} includes frozen held-out questions; "
            "do not use these results for design or threshold selection."
        )
    return split


def expected_chunk_ranges(
    lines: list[str],
    strategy: str = DEFAULT_STRATEGY,
) -> Iterator[tuple[int, int]]:
    """Yield ingestion-compatible half-open ranges for the selected strategy."""

    selected = get_strategy(strategy)
    if not lines:
        return

    step = selected.chunk_size - selected.overlap
    if step <= 0:
        raise ValueError("chunk size must be greater than overlap")

    previous_end = 0
    for start_index in range(0, len(lines), step):
        end_index = min(start_index + selected.chunk_size, len(lines))
        if end_index <= previous_end:
            continue
        yield start_index, end_index
        previous_end = end_index
