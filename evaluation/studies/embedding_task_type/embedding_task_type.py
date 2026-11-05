"""Pure helpers for the registered Gemini embedding task-type experiment."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.investigation.guard import evaluate_evidence_sufficiency
from evaluation.metrics import (
    first_relevant_rank,
    first_relevant_span_rank,
    is_relevant_span,
)
from evaluation.stats import exact_sign_test
from evaluation.test_files import is_test_path

EmbeddingTaskType = Literal["RETRIEVAL_DOCUMENT", "CODE_RETRIEVAL_QUERY"]
DOCUMENT_TASK_TYPE: EmbeddingTaskType = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE: EmbeddingTaskType = "CODE_RETRIEVAL_QUERY"
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 768
EXPERIMENT_VERSION = "gemini-embedding-001-768-task-type-v1"
BOOTSTRAP_SEED = 20261031
BOOTSTRAP_RESAMPLES = 10_000
TOP_K = 5
ANSWERABLE_CATEGORIES = {"direct", "paraphrased"}


@dataclass(frozen=True)
class EmbeddingInputs:
    """Unique text inputs, split by their distinct Gemini task semantics."""

    document_texts: tuple[str, ...]
    query_texts: tuple[str, ...]


def embedding_cache_key(text: str, task_type: EmbeddingTaskType) -> str:
    """Keep control vectors and task-specific candidate vectors in separate caches."""

    identity = json.dumps(
        {
            "version": EXPERIMENT_VERSION,
            "model": EMBEDDING_MODEL,
            "dimension": EMBEDDING_DIMENSION,
            "task_type": task_type,
            "text": text,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def collect_embedding_inputs(
    fixtures_by_repository: Mapping[str, Mapping[str, Any]],
    development_questions_by_repository: Mapping[
        str, Sequence[Mapping[str, Any]]
    ],
) -> EmbeddingInputs:
    """Collect distinct source text and only the questions selected for development."""

    if fixtures_by_repository.keys() != development_questions_by_repository.keys():
        raise ValueError("Fixture and development repository selections differ")
    document_texts: set[str] = set()
    query_texts: set[str] = set()
    for repository, fixture in fixtures_by_repository.items():
        chunks = fixture.get("chunks")
        if not isinstance(chunks, list):
            raise ValueError(f"{repository}: fixture chunks must be a list")
        for chunk in chunks:
            text = chunk.get("content") if isinstance(chunk, Mapping) else None
            if not isinstance(text, str) or not text:
                raise ValueError(f"{repository}: every chunk needs content text")
            document_texts.add(text)
        for question in development_questions_by_repository[repository]:
            text = question.get("question")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(
                    f"{repository}: every selected development question needs text"
                )
            query_texts.add(text)
    return EmbeddingInputs(
        document_texts=tuple(
            sorted(document_texts, key=lambda text: embedding_cache_key(
                text, DOCUMENT_TASK_TYPE
            ))
        ),
        query_texts=tuple(
            sorted(query_texts, key=lambda text: embedding_cache_key(
                text, QUERY_TASK_TYPE
            ))
        ),
    )


def read_cached_vector(path: Path) -> list[float]:
    """Reject malformed or wrong-dimension vectors before they enter a fixture."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read embedding cache entry {path.name}") from exc
    if (
        not isinstance(value, list)
        or len(value) != EMBEDDING_DIMENSION
        or any(
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(item)
            for item in value
        )
    ):
        raise ValueError(f"Invalid cached embedding vector: {path.name}")
    return [float(item) for item in value]


def summarize_method(
    question_results: Sequence[
        tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]
    ],
) -> dict[str, Any]:
    """Summarize development retrieval quality and the test-source safeguard."""

    answerable_ranks: list[int | None] = []
    span_ranks: list[int | None] = []
    span_labels_available = True
    test_source_denominator = 0
    test_source_hits = 0
    test_chunks = 0
    test_span_overlaps = 0
    top5_test_chunks = 0
    top5_results = 0

    for question, ranking in question_results:
        results = ranking[:TOP_K]
        tagged_results = [
            result
            for result in results
            if is_test_path(str(result.get("file_path") or ""))
        ]
        top5_test_chunks += len(tagged_results)
        top5_results += len(results)
        if question.get("category") not in ANSWERABLE_CATEGORIES:
            continue

        labels = question.get("relevant", [])
        if not isinstance(labels, list):
            raise ValueError("Answerable development questions need relevance labels")
        answerable_ranks.append(first_relevant_rank(results, labels))
        spans = question.get("relevant_spans")
        if not isinstance(spans, list):
            span_labels_available = False
            spans = []
        span_ranks.append(first_relevant_span_rank(results, spans))
        test_spans = [
            span
            for span in spans
            if isinstance(span, Mapping)
            and isinstance(span.get("file_path"), str)
            and is_test_path(span["file_path"])
        ]
        if test_spans:
            test_source_denominator += 1
            if first_relevant_span_rank(results, test_spans) is not None:
                test_source_hits += 1
        test_chunks += len(tagged_results)
        test_span_overlaps += sum(
            is_relevant_span(result, test_spans) for result in tagged_results
        )

    count = len(answerable_ranks)
    reciprocal_ranks = [
        1 / rank if rank is not None else 0.0 for rank in answerable_ranks
    ]
    span_reciprocal_ranks = [
        1 / rank if rank is not None else 0.0 for rank in span_ranks
    ]
    return {
        "answerable_questions": count,
        "hit_at_1_successes": sum(
            rank is not None and rank <= 1 for rank in answerable_ranks
        ),
        "hit_at_3_successes": sum(
            rank is not None and rank <= 3 for rank in answerable_ranks
        ),
        "hit_at_5_successes": sum(
            rank is not None and rank <= 5 for rank in answerable_ranks
        ),
        "mrr": sum(reciprocal_ranks) / count if count else 0.0,
        "span_mrr": (
            sum(span_reciprocal_ranks) / count
            if span_labels_available and count
            else None
        ),
        "test_top5_chunks": top5_test_chunks,
        "top5_chunks": top5_results,
        "test_top5_share": (
            top5_test_chunks / top5_results if top5_results else 0.0
        ),
        "test_source_recall_denominator": (
            test_source_denominator if span_labels_available else None
        ),
        "test_source_recall_hits": (
            test_source_hits if span_labels_available else None
        ),
        "test_source_recall": (
            test_source_hits / test_source_denominator
            if span_labels_available and test_source_denominator
            else None
        ),
        "test_precision_overlaps": test_span_overlaps,
        "answerable_test_top5_chunks": test_chunks,
        "test_precision": (
            test_span_overlaps / test_chunks if test_chunks else None
        ),
        "reciprocal_ranks": reciprocal_ranks,
    }


def paired_mrr_statistics(
    control_reciprocal_ranks: Sequence[float],
    candidate_reciprocal_ranks: Sequence[float],
    *,
    seed: int = BOOTSTRAP_SEED,
    resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict[str, Any]:
    """Estimate paired MRR change and its registered descriptive statistics."""

    if len(control_reciprocal_ranks) != len(candidate_reciprocal_ranks):
        raise ValueError("Paired MRR samples must have equal lengths")
    if not control_reciprocal_ranks:
        raise ValueError("Paired MRR statistics need at least one question")
    if resamples < 1:
        raise ValueError("Bootstrap resamples must be positive")

    differences = [
        candidate - control
        for control, candidate in zip(
            control_reciprocal_ranks, candidate_reciprocal_ranks
        )
    ]
    observed = sum(differences) / len(differences)
    rng = random.Random(seed)
    means = sorted(
        sum(rng.choices(differences, k=len(differences))) / len(differences)
        for _ in range(resamples)
    )

    def percentile(q: float) -> float:
        position = (len(means) - 1) * q
        lower = int(position)
        upper = min(lower + 1, len(means) - 1)
        fraction = position - lower
        return means[lower] * (1 - fraction) + means[upper] * fraction

    positive = sum(value > 0 for value in differences)
    negative = sum(value < 0 for value in differences)
    return {
        "mrr_difference": observed,
        "bootstrap_seed": seed,
        "bootstrap_resamples": resamples,
        "bootstrap_95_percentile_interval": [
            percentile(0.025),
            percentile(0.975),
        ],
        "sign_test": {
            "positive": positive,
            "negative": negative,
            "ties": len(differences) - positive - negative,
            "two_sided_p_value": exact_sign_test(positive, negative),
        },
    }


def compare_guard_decisions(
    questions: Sequence[Mapping[str, Any]],
    control_rankings: Mapping[str, Sequence[Mapping[str, Any]]],
    candidate_rankings: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, int | list[int]]:
    """Compare production guard decisions and expose changed ordinals only."""

    unchanged = improved = regressed = 0
    changed_ordinals: list[int] = []
    unanswerable_count = 0
    for ordinal, question in enumerate(questions, start=1):
        if question.get("category") in ANSWERABLE_CATEGORIES:
            continue
        question_id = question.get("id")
        if (
            not isinstance(question_id, str)
            or question_id not in control_rankings
            or question_id not in candidate_rankings
        ):
            raise ValueError("Every development question needs both rankings")
        control = evaluate_evidence_sufficiency(
            control_rankings[question_id][:TOP_K]
        )["is_sufficient"]
        candidate = evaluate_evidence_sufficiency(
            candidate_rankings[question_id][:TOP_K]
        )["is_sufficient"]
        if not isinstance(control, bool) or not isinstance(candidate, bool):
            raise ValueError("Production guard must return boolean decisions")
        unanswerable_count += 1
        if control == candidate:
            unchanged += 1
        else:
            changed_ordinals.append(ordinal)
            if control and not candidate:
                improved += 1
            else:
                regressed += 1
    return {
        "unanswerable_questions": unanswerable_count,
        "unchanged": unchanged,
        "improved": improved,
        "regressed": regressed,
        "changed_development_ordinals": changed_ordinals,
    }


def evaluate_task_type_rules(
    control_pooled: Mapping[str, Any],
    candidate_pooled: Mapping[str, Any],
    control_by_repository: Mapping[str, Mapping[str, Any]],
    candidate_by_repository: Mapping[str, Mapping[str, Any]],
    guard_by_repository: Mapping[str, Mapping[str, Any]],
    bootstrap: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply the four-condition 14a retention rule without hidden defaults."""

    difference = float(candidate_pooled["mrr"]) - float(control_pooled["mrr"])
    interval = bootstrap["bootstrap_95_percentile_interval"]

    rules = {
        "R1": "pass" if difference >= 0.03 else "fail",
        "R2": "pass" if float(interval[0]) > 0 else "fail",
        "R3": (
            "pass"
            if all(
                int(candidate_by_repository[name]["hit_at_5_successes"])
                >= int(control_by_repository[name]["hit_at_5_successes"])
                for name in control_by_repository
            )
            else "fail"
        ),
        "R4": (
            "pass"
            if all(
                int(guard["regressed"]) == 0
                for guard in guard_by_repository.values()
            )
            else "fail"
        ),
    }
    qualifies = all(rules[rule] == "pass" for rule in ("R1", "R2", "R3", "R4"))
    return {
        "rules": rules,
        "qualifies_for_retention": qualifies,
        "mrr_difference": difference,
        "outcome": (
            "The task-type candidate qualifies under the registered rules; "
            "production remains unchanged pending a separate adoption decision."
            if qualifies
            else "Keep the current control; the candidate does not qualify under "
            "the registered rules."
        ),
    }


def render_results(report: Mapping[str, Any]) -> str:
    """Render a commit-ready aggregate note without question IDs or text."""

    lines = [
        "# Embedding task-type comparison: development",
        "",
        "## Protocol metadata",
        "",
        "- Protocol: [14-embedding-task-type-experiment.md](14-embedding-task-type-experiment.md)",
        f"- Protocol commit: `{report['protocol_commit']}`",
        f"- Cache version: `{report['experiment_version']}`",
        "- Selection split: development only.",
        "",
        "| Scope | Method | Answerable | Hit@1 | Hit@3 | Hit@5 | MRR | Span MRR | "
        "Test top-five share | Test-source recall | Test precision |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    scopes = [
        (name, methods)
        for name, methods in report["per_repository"].items()
    ]
    scopes.append(("Pooled", report["pooled"]))
    for scope, methods in scopes:
        for method in ("control", "candidate"):
            metrics = methods[method]
            denominator = metrics["test_source_recall_denominator"]
            recall = (
                "not evaluable (0 denominator)"
                if denominator == 0
                else (
                    "not available"
                    if denominator is None
                    else f"{metrics['test_source_recall_hits']}/{denominator} "
                    f"({metrics['test_source_recall']:.6f})"
                )
            )
            precision_denominator = metrics["answerable_test_top5_chunks"]
            precision = (
                "not evaluable (0 chunks)"
                if precision_denominator == 0
                else f"{metrics['test_precision_overlaps']}/"
                f"{precision_denominator} ({metrics['test_precision']:.6f})"
            )
            span_mrr = (
                "not available"
                if metrics["span_mrr"] is None
                else f"{metrics['span_mrr']:.6f}"
            )
            lines.append(
                f"| {scope} | {method} | {metrics['answerable_questions']} | "
                f"{metrics['hit_at_1_successes']} | {metrics['hit_at_3_successes']} | "
                f"{metrics['hit_at_5_successes']} | {metrics['mrr']:.6f} | "
                f"{span_mrr} | {metrics['test_top5_chunks']}/"
                f"{metrics['top5_chunks']} ({metrics['test_top5_share']:.6f}) | "
                f"{recall} | {precision} |"
            )
    bootstrap = report["bootstrap"]
    low, high = bootstrap["bootstrap_95_percentile_interval"]
    sign = bootstrap["sign_test"]
    lines.extend(
        [
            "",
            "## Paired pooled MRR",
            "",
            f"Difference: {bootstrap['mrr_difference']:.6f}; 95% paired bootstrap "
            f"interval: [{low:.6f}, {high:.6f}] (seed "
            f"{bootstrap['bootstrap_seed']}, {bootstrap['bootstrap_resamples']} "
            "resamples). The exact sign test is descriptive only: "
            f"{sign['positive']} positive, {sign['negative']} negative, "
            f"{sign['ties']} tied; p={sign['two_sided_p_value']:.6f}.",
            "",
            "## Evidence-guard changes",
            "",
            "| Repository | Unanswerable | Unchanged | Improved | Regressed | "
            "Changed development ordinals |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for repository, guard in report["guard_by_repository"].items():
        ordinals = ", ".join(map(str, guard["changed_development_ordinals"])) or "none"
        lines.append(
            f"| {repository} | {guard['unanswerable_questions']} | "
            f"{guard['unchanged']} | {guard['improved']} | {guard['regressed']} | "
            f"{ordinals} |"
        )
    lines.extend(
        [
            "",
            "## Registered decision",
            "",
            "| Rule | Retention condition | Result |",
            "|---|---|---|",
        ]
    )
    conditions = {
        "R1": (
            "Pooled development MRR over 33 answerable questions improves "
            "by at least 0.03 versus control."
        ),
        "R2": "The 95% paired-bootstrap lower bound of the pooled MRR difference is above 0.",
        "R3": "Per-repository answerable Hit@5 successes do not decrease.",
        "R4": (
            "Per-repository guard decisions on every unanswerable development "
            "question are unchanged or improved."
        ),
    }
    lines.extend(
        f"| {rule} | {conditions[rule]} | {status} |"
        for rule, status in report["decision"]["rules"].items()
    )
    lines.extend(
        [
            "",
            f"**Mechanical decision:** {report['decision']['outcome']}",
            "",
            "## Limits",
            "",
            *[f"- {limit}" for limit in report["limits"]],
            "",
        ]
    )
    return "\n".join(lines)


def write_results_note(report: Mapping[str, Any], path: Path) -> None:
    """Write the aggregate development result to its repository documentation path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_results(report), encoding="utf-8")
