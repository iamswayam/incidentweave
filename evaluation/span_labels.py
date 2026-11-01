"""Derive stable, chunk-independent relevance spans from golden substring labels."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "evaluation" / "repos" / "incidentweave" / "questions.json"


def find_span(file_text: str, substring: str) -> tuple[int, int] | None:
    """Find the first case-insensitive occurrence and return inclusive line bounds."""

    if not substring:
        return None
    folded_parts: list[str] = []
    source_offsets: list[int] = []
    for source_offset, character in enumerate(file_text):
        folded = character.casefold()
        folded_parts.append(folded)
        source_offsets.extend([source_offset] * len(folded))
    folded_text = "".join(folded_parts)
    folded_substring = substring.casefold()
    folded_start = folded_text.find(folded_substring)
    if folded_start < 0:
        return None
    source_start = source_offsets[folded_start]
    source_end = source_offsets[folded_start + len(folded_substring) - 1]
    return (
        file_text.count("\n", 0, source_start) + 1,
        file_text.count("\n", 0, source_end) + 1,
    )


def derive_spans(
    golden: Mapping[str, Any],
    read_file: Callable[[str, str], str],
) -> dict[str, list[dict[str, int | str]]]:
    """Resolve every question's relevant labels to source line ranges."""

    pinned_sha = golden.get("pinned_sha")
    if not isinstance(pinned_sha, str) or not pinned_sha:
        raise ValueError("golden set must contain a pinned_sha")
    spans_by_question: dict[str, list[dict[str, int | str]]] = {}
    for question in golden.get("questions", []):
        question_id = str(question.get("id") or "<missing>")
        spans: list[dict[str, int | str]] = []
        for label in question.get("relevant", []):
            path = str(label["file_path"])
            span = find_span(read_file(pinned_sha, path), str(label["substring"]))
            if span is None:
                raise ValueError(
                    f"{question_id}: substring not found in {path}: "
                    f"{label['substring']!r}"
                )
            spans.append(
                {"file_path": path, "line_start": span[0], "line_end": span[1]}
            )
        spans_by_question[question_id] = spans
    return spans_by_question


def _read_pinned_file(sha: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{sha}:{path}"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write spans into the IncidentWeave questions file",
    )
    args = parser.parse_args()
    if not args.write:
        parser.error("--write is required")

    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    derived = derive_spans(golden, _read_pinned_file)
    for question in golden["questions"]:
        question["relevant_spans"] = derived[str(question["id"])]
    GOLDEN_PATH.write_text(
        json.dumps(golden, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
