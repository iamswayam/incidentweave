"""Review pack rendering and parsing helpers."""

from __future__ import annotations

import re
from typing import Any

GUIDELINES_LINK = "../../../repos/README.md#labelling-guidelines"

PACK_HEADING = re.compile(
    r"^## (Q-\d{3}) \| (answerable|unanswerable) \| "
    r"(mined|drafted|human)(?: \(issue #(\d+), PR #(\d+)\))?$"
)

GOLD_LINE = re.compile(r"^- (.+?) : (\d+)-(\d+)$")

ABSENCE_LINE = re.compile(r"^(.+?) -> (\d+) hits at ([0-9a-fA-F]{40})$")

SECOND_PASS_HEADING = re.compile(r"^## Item (\d+)$")


def _one_line(value: object) -> str:
    return " ".join(str(value or "").splitlines()).strip()


def render_pack(
    repo_id: str,
    pinned_sha: str,
    items: list[dict[str, Any]],
) -> tuple[str, dict[str, Any], int]:
    """Render a review pack, its original-item metadata, and skipped count."""

    lines = [
        f"# Question review pack: {repo_id}",
        "",
        f"Pinned SHA: `{pinned_sha}`",
        "",
        "Fill Question, Type or Kind, Gold or Absence check, Evidence, Decision, Minutes, "
        "and Notes.",
        "Set Decision to `accept` or `reject`; record whole minutes including review.",
        f"Guidelines: [Labelling guidelines]({GUIDELINES_LINK})",
        "",
    ]
    metadata: dict[str, Any] = {
        "repo_id": repo_id,
        "pinned_sha": pinned_sha,
        "items": {},
    }
    skipped = 0
    number = 0
    for item in items:
        question = _one_line(item.get("question"))
        if not question:
            skipped += 1
            continue
        number += 1
        block_id = f"Q-{number:03d}"
        source = item["source"]
        mined = item.get("mined")
        answerable = bool(item.get("answerable"))
        source_label = source
        if source == "mined":
            if not isinstance(mined, dict):
                raise ValueError(f"{item.get('candidate_id')}: mined record is missing")
            source_label = f"mined (issue #{mined['issue_number']}, PR #{mined['pr_number']})"
        lines.append(
            f"## {block_id} | {'answerable' if answerable else 'unanswerable'} | {source_label}"
        )
        if isinstance(mined, dict):
            lines.extend(
                [
                    f"Issue title: {_one_line(mined.get('issue_title'))}",
                    f"Issue quote: > {_one_line(mined.get('issue_body'))[:280]}",
                ]
            )
        lines.append(f"Question: {question}")
        if answerable:
            lines.append(f"Type: {_one_line(item.get('type'))}")
            lines.append("Gold:")
            for gold in item.get("gold", []):
                lines.append(
                    f"- {_one_line(gold.get('path'))} : {gold.get('start')}-{gold.get('end')}"
                )
        else:
            absence = item.get("absence_check", {})
            lines.extend(
                [
                    f"Kind: {_one_line(item.get('kind'))}",
                    "Absence check: "
                    f"{', '.join(map(str, absence.get('terms', [])))} -> "
                    f"{absence.get('hits')} hits at {pinned_sha}",
                ]
            )
        lines.append(f"Evidence: {_one_line(item.get('evidence'))}")
        if answerable:
            for gold in item.get("gold", []):
                path = _one_line(gold.get("path"))
                start = gold.get("start")
                end = gold.get("end")
                lines.append(
                    f"Link: https://github.com/{item['owner']}/{item['repo']}/blob/"
                    f"{pinned_sha}/{path}#L{start}-L{end}"
                )
        lines.extend(["Decision:", "Minutes:", "Notes:", ""])
        metadata["items"][block_id] = {
            "candidate_id": item.get("candidate_id"),
            "original": item,
            "mined": mined,
        }
    return "\n".join(lines), metadata, skipped


def parse_pack(text: str, *, require_decisions: bool = False) -> list[dict[str, Any]]:
    """Parse review blocks; every malformed field includes its source line."""

    lines = text.splitlines()
    headings = [
        (line_number, PACK_HEADING.fullmatch(line))
        for line_number, line in enumerate(lines, start=1)
        if line.startswith("## ")
    ]
    errors = [
        f"line {line_number}: malformed question block heading"
        for line_number, match in headings
        if match is None
    ]
    if errors:
        raise ValueError("; ".join(errors))
    expected = {
        "answerable": {
            "Question",
            "Type",
            "Gold",
            "Evidence",
            "Decision",
            "Minutes",
            "Notes",
        },
        "unanswerable": {
            "Question",
            "Kind",
            "Absence check",
            "Evidence",
            "Decision",
            "Minutes",
            "Notes",
        },
    }
    known_fields = {
        "Question",
        "Type",
        "Gold",
        "Evidence",
        "Decision",
        "Minutes",
        "Notes",
        "Kind",
        "Absence check",
    }
    blocks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for block_index, (start_line, match) in enumerate(headings):
        assert match is not None
        end_line = (
            headings[block_index + 1][0] - 1 if block_index + 1 < len(headings) else len(lines)
        )
        block_id, status, source, issue, pr = match.groups()
        if block_id in seen_ids:
            errors.append(f"line {start_line}: duplicate question block {block_id}")
        seen_ids.add(block_id)
        fields: dict[str, tuple[str, int]] = {}
        gold: list[dict[str, Any]] = []
        current_field: str | None = None
        for line_number in range(start_line + 1, end_line + 1):
            line = lines[line_number - 1]
            if not line.strip():
                continue
            if line.startswith(("Link: ", "Issue title: ", "Issue quote: ")):
                continue
            if line.startswith("- "):
                if current_field != "Gold":
                    errors.append(f"line {line_number}: gold path outside Gold field")
                    continue
                span_match = GOLD_LINE.fullmatch(line)
                if span_match is None:
                    errors.append(
                        f"line {line_number}: malformed gold span; expected '- path : start-end'"
                    )
                    continue
                path, span_start, span_end = span_match.groups()
                start, end = int(span_start), int(span_end)
                if start < 1 or end < start:
                    errors.append(f"line {line_number}: gold span range is invalid")
                gold.append({"path": path, "start": start, "end": end})
                continue
            field_match = re.match(r"^([A-Za-z ]+):(?:\s*(.*))?$", line)
            if field_match is None:
                errors.append(f"line {line_number}: malformed review field")
                continue
            name, value = field_match.groups()
            name = name.strip()
            if name not in known_fields:
                errors.append(f"line {line_number}: unknown review field {name!r}")
                continue
            if name in fields:
                errors.append(f"line {line_number}: duplicate {name} field")
                continue
            fields[name] = (value or "", line_number)
            current_field = name
        for field, (_, field_line) in fields.items():
            if field not in expected[status]:
                errors.append(f"line {field_line}: {field} field is invalid for {status} questions")
        for field in expected[status]:
            if field not in fields:
                errors.append(f"line {start_line}: missing {field} field in {block_id}")
        question = fields.get("Question", ("", start_line))[0]
        question_type = fields.get("Type", ("", start_line))[0] or None
        kind = fields.get("Kind", ("", start_line))[0] or None
        if not question.strip():
            errors.append(
                f"line {fields.get('Question', ('', start_line))[1]}: Question is required"
            )
        if status == "answerable" and not question_type:
            errors.append(f"line {start_line}: Type is required")
        if status == "answerable" and not gold:
            errors.append(f"line {start_line}: Gold needs a span")
        if status == "unanswerable" and not kind:
            errors.append(f"line {start_line}: Kind is required")
        decision = fields.get("Decision", ("", start_line))[0].casefold()
        minutes_text, minutes_line = fields.get("Minutes", ("", start_line))
        minutes = int(minutes_text) if re.fullmatch(r"\d+", minutes_text) else None
        if require_decisions and decision not in {"accept", "reject"}:
            errors.append(
                f"line {fields.get('Decision', ('', start_line))[1]}: "
                "Decision must be accept or reject"
            )
        if require_decisions and minutes is None:
            errors.append(f"line {minutes_line}: Minutes must be a non-negative integer")
        absence_terms: list[str] = []
        absence_hits: int | None = None
        absence_sha: str | None = None
        if status == "unanswerable" and "Absence check" in fields:
            absence_text, absence_line = fields["Absence check"]
            absence_match = ABSENCE_LINE.fullmatch(absence_text)
            if absence_match is None:
                errors.append(f"line {absence_line}: malformed Absence check")
            else:
                term_text, hits_text, absence_sha = absence_match.groups()
                absence_terms = [term.strip() for term in term_text.split(",") if term.strip()]
                absence_hits = int(hits_text)
        blocks.append(
            {
                "block_id": block_id,
                "answerable": status == "answerable",
                "source": source,
                "issue_number": int(issue) if issue else None,
                "pr_number": int(pr) if pr else None,
                "question": question,
                "type": question_type,
                "kind": kind,
                "gold": gold,
                "evidence": fields.get("Evidence", ("", start_line))[0],
                "absence_terms": absence_terms,
                "absence_hits": absence_hits,
                "absence_sha": absence_sha,
                "decision": decision,
                "minutes": minutes,
                "line": start_line,
            }
        )
    if errors:
        raise ValueError("; ".join(errors))
    return blocks


def render_second_pass(sampled: list[dict[str, Any]]) -> str:
    lines = [
        "# Blind second pass",
        "",
        "Relabel each item independently. Do not consult first-pass labels. "
        "Answer yes or no; list each gold file as `- path`; use whole minutes.",
        "",
    ]
    for index, row in enumerate(sampled, start=1):
        lines.extend(
            [
                f"## Item {index}",
                "",
                _one_line(row["question"].get("question")),
                "",
                "Answerable:",
                "Gold files:",
                "Minutes:",
                "",
            ]
        )
    return "\n".join(lines)


def parse_second_pass(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    headings = [
        (line_number, SECOND_PASS_HEADING.fullmatch(line))
        for line_number, line in enumerate(lines, start=1)
        if line.startswith("## ")
    ]
    errors = [
        f"line {line_number}: malformed second-pass heading"
        for line_number, match in headings
        if match is None
    ]
    if errors:
        raise ValueError("; ".join(errors))
    results: list[dict[str, Any]] = []
    for index, (start_line, match) in enumerate(headings):
        assert match is not None
        end_line = headings[index + 1][0] - 1 if index + 1 < len(headings) else len(lines)
        fields: dict[str, tuple[str, int]] = {}
        question_lines: list[str] = []
        in_gold = False
        for line_number in range(start_line + 1, end_line + 1):
            line = lines[line_number - 1]
            if not line.strip():
                continue
            field_match = re.match(r"^(Answerable|Gold files|Minutes):\s*(.*)$", line)
            if field_match:
                field, value = field_match.groups()
                fields[field] = (value, line_number)
                in_gold = field == "Gold files"
                continue
            if in_gold and line.startswith("- "):
                value, source_line = fields["Gold files"]
                fields["Gold files"] = (f"{value}\n{line[2:]}", source_line)
                continue
            if not fields:
                question_lines.append(line)
        for field in ("Answerable", "Gold files", "Minutes"):
            if field not in fields:
                errors.append(f"line {start_line}: missing {field} in Item {match.group(1)}")
        answer_text, answer_line = fields.get("Answerable", ("", start_line))
        answer_text = answer_text.casefold()
        if answer_text not in {"yes", "no"}:
            errors.append(f"line {answer_line}: Answerable must be yes or no")
        gold_text, gold_line = fields.get("Gold files", ("", start_line))
        gold_files = sorted(
            {
                item.strip().removeprefix("- ").strip()
                for item in gold_text.splitlines()
                if item.strip()
            }
        )
        minutes_text, minutes_line = fields.get("Minutes", ("", start_line))
        valid_minutes = re.fullmatch(r"\d+", minutes_text) is not None
        if not valid_minutes:
            errors.append(f"line {minutes_line}: Minutes must be a non-negative integer")
        if answer_text == "yes" and not gold_files:
            errors.append(f"line {gold_line}: answerable item needs at least one gold file")
        if answer_text == "no" and gold_files:
            errors.append(f"line {gold_line}: unanswerable item must have no gold files")
        results.append(
            {
                "item": int(match.group(1)),
                "question": "\n".join(question_lines),
                "answerable": answer_text == "yes",
                "gold_files": gold_files,
                "minutes": int(minutes_text) if valid_minutes else None,
            }
        )
    if errors:
        raise ValueError("; ".join(errors))
    return results
