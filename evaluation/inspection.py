"""Pure Markdown rendering for offline retrieval inspection reports."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.investigation.guard import evaluate_evidence_sufficiency
from evaluation.metrics import is_relevant_span

ANSWERABLE_CATEGORIES = {"direct", "paraphrased"}


def _source_lines(fixture: Mapping[str, Any]) -> dict[str, dict[int, str]]:
    lines_by_file: dict[str, dict[int, str]] = {}
    for chunk in fixture["chunks"]:
        path = str(chunk["file_path"])
        start = int(chunk["line_start"])
        lines = lines_by_file.setdefault(path, {})
        for offset, text in enumerate(str(chunk.get("content", "")).splitlines()):
            lines.setdefault(start + offset, text)
    return lines_by_file


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "..."


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _answerable(question: Mapping[str, Any]) -> bool:
    return str(question.get("category", "")) in ANSWERABLE_CATEGORIES


def _first_hit_rank(record: Mapping[str, Any]) -> int | None:
    rank = record.get("span_rank")
    if rank is None:
        return None
    return int(rank)


def _format_score(value: Any, places: int) -> str:
    if value is None:
        return ""
    return f"{float(value):.{places}f}"


def _retrieved_table(
    retrieved: Sequence[Mapping[str, Any]],
    spans: Sequence[Mapping[str, Any]],
) -> list[str]:
    lines = [
        "**Top 5 retrieved**",
        "",
        "| # | Overlaps evidence | File:lines | Lines | Starts with | "
        "Vector distance | Text score | Fusion score |",
        "|---:|---|---|---:|---|---:|---:|---:|",
    ]
    for result in retrieved[:5]:
        rank = int(result.get("rank", 0))
        overlaps = is_relevant_span(result, spans)
        file_path = str(result.get("file_path") or "")
        line_start = result.get("line_start")
        line_end = result.get("line_end")
        file_lines = (
            f"{file_path}:{line_start}-{line_end}"
            if line_start is not None and line_end is not None
            else file_path
        )
        line_count = (
            int(line_end) - int(line_start) + 1
            if isinstance(line_start, int) and isinstance(line_end, int)
            else ""
        )
        starts_with = next(
            (
                line.strip()
                for line in str(result.get("content") or "").splitlines()
                if line.strip()
            ),
            "",
        )
        starts_with = _markdown_cell(_truncate(starts_with, 60))
        lines.append(
            f"| {rank} | {'yes' if overlaps else 'no'} | "
            f"{_markdown_cell(file_lines)} | {line_count} | {starts_with} | "
            f"{_format_score(result.get('vector_score'), 3)} | "
            f"{_format_score(result.get('fts_score'), 3)} | "
            f"{_format_score(result.get('rrf_score'), 4)} |"
        )
    if not retrieved:
        lines.append("| - | no | - | - | - |  |  |  |")
    return lines


def _guard_line(retrieved: Sequence[Mapping[str, Any]]) -> str:
    decision = evaluate_evidence_sufficiency(retrieved)
    best_distance = decision["best_vector_score"]
    distance_text = (
        f"{float(best_distance):.3f}" if best_distance is not None else "not available"
    )
    behavior = "would answer" if decision["is_sufficient"] else "would refuse"
    return (
        f"**Guard (provisional threshold 0.5):** {behavior}; "
        f"best vector distance: {distance_text}."
    )


def _evidence_block(
    spans: Sequence[Mapping[str, Any]],
    source_lines: Mapping[str, Mapping[int, str]],
) -> list[str]:
    lines = ["**Evidence needed:**"]
    for span in spans:
        path = str(span["file_path"])
        start = int(span["line_start"])
        end = int(span["line_end"])
        count = end - start + 1
        lines.append(f"- `{path}:{start}-{end}` ({count} lines)")
        lines.append("```text")
        for line_number in range(start, min(end, start + 7) + 1):
            text = source_lines.get(path, {}).get(line_number, "(line not available)")
            lines.append(f"{line_number} | {_truncate(text, 100)}")
        lines.append("```")
    if not spans:
        lines.append("- No evidence spans are labelled.")
    return lines


def _question_card(
    question: Mapping[str, Any],
    record: Mapping[str, Any],
    source_lines: Mapping[str, Mapping[int, str]],
) -> list[str]:
    question_id = str(question["id"])
    category = str(question["category"])
    retrieved = record.get("retrieved", [])
    spans = question.get("relevant_spans", [])
    answerable = _answerable(question)
    rank = _first_hit_rank(record) if answerable else None
    if answerable:
        result_label = f"HIT at rank {rank}" if rank is not None else "MISS"
    else:
        result_label = "no answer expected"
    lines = [
        f"### {question_id} | {category} | {result_label}",
        "",
        f"**Question:** {question['question']}",
        "",
    ]
    if answerable:
        lines.extend(_evidence_block(spans, source_lines))
        lines.append("")
    lines.extend(_retrieved_table(retrieved, spans))
    lines.extend(["", _guard_line(retrieved)])
    if not answerable:
        lines.append(
            "Expected: refuse. If the guard would answer here, this is a false-answer risk."
        )
    elif rank is None:
        lines.append("")
        lines.append("**Why it missed (fill in by hand):** ______")
    return lines


def render_strategy_report(
    report: Mapping[str, Any],
    questions: Sequence[Mapping[str, Any]],
    fixture: Mapping[str, Any],
    s0_baseline_fixture: Mapping[str, Any],
    *,
    strategy: str,
    split: str,
    fixture_sha256: str,
) -> str:
    """Render a deterministic per-strategy inspection report."""

    records = {str(record["id"]): record for record in report["questions"]}
    answerable_questions = [question for question in questions if _answerable(question)]
    ranks = [
        _first_hit_rank(records[str(question["id"])])
        for question in answerable_questions
    ]
    hit_counts = {
        cutoff: sum(rank is not None and rank <= cutoff for rank in ranks)
        for cutoff in (1, 3, 5)
    }
    mrr = (
        sum(1 / rank if rank is not None else 0.0 for rank in ranks) / len(ranks)
        if ranks
        else 0.0
    )
    metadata = report["metadata"]
    lines = [
        f"# Retrieval inspection: {metadata['repo_id']} / {strategy} / {split}",
        "",
        f"- Repository: `{metadata['repo_id']}`",
        f"- Strategy: `{strategy}`",
        f"- Split: `{split}`",
        f"- Fixture SHA-256: `{fixture_sha256[:12]}`",
        f"- Chunk count: {len(fixture['chunks'])}",
        f"- Answerable questions: {len(answerable_questions)}",
        f"- Span Hit@1/3/5: {hit_counts[1]}/{hit_counts[3]}/{hit_counts[5]}",
        f"- Span MRR: {mrr:.3f}",
    ]
    if metadata.get("previously_exposed"):
        lines.extend(["", "**IncidentWeave held-out was previously exposed**"])
    if split in {"held_out", "all"}:
        lines.extend(["", "**HELD-OUT: do not use for design decisions**"])
    lines.extend(
        [
            "",
            "## How to read this report",
            "",
            "- HIT = at least one of the top 5 chunks overlaps the evidence lines.",
            "- Vector distance: lower is more similar, 0 = identical.",
            "- Text score: full-text match strength, blank if no match.",
            "- Fusion score decides the ranking.",
            "- Guard = the provisional evidence check at threshold 0.5.",
            "- Unanswerable questions have no evidence and the correct behaviour is to refuse.",
            "",
        ]
    )
    missed = [
        str(question["id"])
        for question, rank in zip(answerable_questions, ranks)
        if rank is None
    ]
    lines.append(f"Missed questions: {', '.join(missed) if missed else 'none'}")
    lines.extend(["", "---", ""])
    source_lines = _source_lines(s0_baseline_fixture)
    for index, question in enumerate(questions):
        question_id = str(question["id"])
        if question_id not in records:
            raise ValueError(f"Retrieval report lacks question {question_id}")
        lines.extend(_question_card(question, records[question_id], source_lines))
        if index < len(questions) - 1:
            lines.extend(["", "---", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_repository_summary(
    questions: Sequence[Mapping[str, Any]],
    reports_by_strategy: Mapping[str, Mapping[str, Any]],
    *,
    repo_id: str,
    split: str,
) -> str:
    """Render per-question ranks and totals across the requested strategies."""

    records_by_strategy = {
        strategy: {
            str(record["id"]): record for record in report["questions"]
        }
        for strategy, report in reports_by_strategy.items()
    }
    strategies = list(reports_by_strategy)
    lines = [
        f"# Retrieval inspection summary: {repo_id} / {split}",
        "",
        "| Question | Category | "
        + " | ".join(strategies)
        + " |",
        "|---|---|"
        + "|".join("---:" for _strategy in strategies)
        + "|",
    ]
    missed_everywhere: list[str] = []
    for question in questions:
        question_id = str(question["id"])
        cells = []
        all_missed = _answerable(question)
        for strategy in strategies:
            record = records_by_strategy[strategy].get(question_id)
            if record is None:
                raise ValueError(
                    f"{strategy} retrieval report lacks question {question_id}"
                )
            rank = _first_hit_rank(record) if _answerable(question) else None
            if rank is not None:
                all_missed = False
            cells.append(
                str(rank) if rank is not None else ("-" if _answerable(question) else "n/a")
            )
        if all_missed:
            missed_everywhere.append(question_id)
        lines.append(
            f"| {question_id} | {question['category']} | "
            + " | ".join(cells)
            + " |"
        )

    total_cells = []
    for strategy in strategies:
        answerable_records = [
            record
            for question in questions
            if _answerable(question)
            for record in [records_by_strategy[strategy][str(question["id"])]]
        ]
        successes = sum(
            _first_hit_rank(record) is not None
            and _first_hit_rank(record) <= 5
            for record in answerable_records
        )
        mrr = (
            sum(
                1 / rank if (rank := _first_hit_rank(record)) is not None else 0.0
                for record in answerable_records
            )
            / len(answerable_records)
            if answerable_records
            else 0.0
        )
        total_cells.append(f"Hit@5 {successes}; MRR {mrr:.3f}")
    lines.extend(
        [
            "| **Totals** | **Answerable** | "
            + " | ".join(total_cells)
            + " |",
            "",
            "Missed under every strategy: "
            + (", ".join(missed_everywhere) if missed_everywhere else "none"),
        ]
    )
    return "\n".join(lines) + "\n"
