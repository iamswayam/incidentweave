"""Run registered end-to-end checks or report from saved run-set JSON files."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Sequence

from evaluation.end_to_end_runner import (
    current_repository_commit,
    load_development_questions,
    report_run_sets,
    run_end_to_end,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        help="run three development investigations per question (database and Gemini key required)",
    )
    run.add_argument("--repository", required=True, help="manifest and database repository ID")
    run.add_argument("--questions", type=Path, required=True, help="manifest question JSON file")
    run.add_argument("--out", type=Path, help="run-set JSON output path")
    run.add_argument("--limit", type=int, help="run only the first N development questions")

    report = subparsers.add_parser("report", help="report from saved run-set JSON")
    report.add_argument("records", type=Path, help="one run-set JSON file or a directory of them")
    report.add_argument("--out-md", type=Path, required=True, help="Markdown report path")
    report.add_argument("--out-json", type=Path, required=True, help="JSON summary path")
    report.add_argument(
        "--generated-at",
        help="optional explicit generation timestamp included in both reports",
    )
    return parser


async def _run_command(args: argparse.Namespace) -> int:
    from app.config import settings
    from app.investigation.generation import GEMINI_GENERATION_MODEL
    from app.investigation.service import investigate_repository
    from app.providers.gemini import ProviderError
    from app.retrieval.embeddings import GEMINI_MODEL
    from evaluation.manifest import MANIFEST_PATH, manifest_root

    if not settings.gemini_api_key:
        raise ValueError("the run subcommand requires GEMINI_API_KEY")
    questions = load_development_questions(
        args.questions,
        args.repository,
        manifest_path=MANIFEST_PATH,
    )
    output_path = args.out or Path(
        f"evaluation/experiments/end-to-end/{args.repository}-development.json"
    )
    result = await run_end_to_end(
        questions,
        repository_id=args.repository,
        questions_file=args.questions,
        repository_code_commit=current_repository_commit(manifest_root(MANIFEST_PATH)),
        model_names={
            "generation": GEMINI_GENERATION_MODEL,
            "embedding": GEMINI_MODEL,
            **(
                {"generation_fallback": settings.groq_model}
                if settings.groq_fallback_enabled and settings.groq_model
                else {}
            ),
        },
        generation_parameters={"temperature": 0, "persist": True},
        output_path=output_path,
        investigate=investigate_repository,
        limit=args.limit,
        provider_error_types=(ProviderError, TimeoutError),
    )
    print(f"Recorded {len(result['runs'])} runs to {output_path}")
    print(f"Skipped questions: {len(result['skipped_questions'])}")
    return 0


def _report_command(args: argparse.Namespace) -> int:
    report_data, markdown = report_run_sets(
        args.records,
        generated_at=args.generated_at,
    )
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(markdown + "\n", encoding="utf-8")
    args.out_json.write_text(
        json.dumps(report_data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Markdown report: {args.out_md}")
    print(f"JSON summary: {args.out_json}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "run":
            if args.limit is not None and args.limit < 1:
                raise ValueError("--limit must be positive")
            return asyncio.run(_run_command(args))
        return _report_command(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"end-to-end checks: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
