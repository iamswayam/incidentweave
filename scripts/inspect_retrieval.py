"""Generate deterministic Markdown cards for offline retrieval inspection."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.build_fixture import load_fixture  # noqa: E402
from evaluation.chunk_experiments import (  # noqa: E402
    CANDIDATE_STRATEGIES,
    resolve_split,
)
from evaluation.golden import load_golden_set  # noqa: E402
from evaluation.inspection import (  # noqa: E402
    render_repository_summary,
    render_strategy_report,
)
from evaluation.manifest import load_manifest, repository_entry  # noqa: E402
from evaluation.retrieval_eval import run_offline_retrieval  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "evaluation" / "inspection"
STRATEGY_ALIASES = {
    "s0": "s0_lines_60_10",
    "s1": "s1_lines_100_20",
    "s2": "s2_ast_v1",
    "s3": "s3_ast_v1_embed_text",
}


def _selected_strategies(value: str) -> list[str]:
    if value == "all":
        return list(CANDIDATE_STRATEGIES)
    strategy = STRATEGY_ALIASES.get(value, value)
    if strategy not in CANDIDATE_STRATEGIES:
        raise ValueError(
            f"Unknown strategy {value!r}; choose from all, "
            + ", ".join([*STRATEGY_ALIASES, *CANDIDATE_STRATEGIES])
        )
    return [strategy]


async def _run(args: argparse.Namespace) -> list[Path]:
    if args.limit < 1:
        raise ValueError("--limit must be greater than zero")
    split = resolve_split(
        args.split,
        confirm_frozen_heldout=args.confirm_frozen_heldout,
    )
    manifest = load_manifest()
    if args.repo == "all":
        entries = list(manifest["repositories"])
    else:
        entries = [repository_entry(manifest, args.repo)]
    strategies = _selected_strategies(args.strategy)
    output_dir = args.output_dir
    written_paths: list[Path] = []

    for entry in entries:
        repo_id = str(entry["id"])
        baseline_path = ROOT / entry["fixture"]["path"]
        baseline_fixture = load_fixture(baseline_path)
        golden_path = ROOT / entry["questions"]["path"]
        golden = load_golden_set(golden_path)
        split_questions = [
            question
            for question in golden["questions"]
            if split == "all" or question["id"] in set(entry["splits"][split])
        ]
        reports_by_strategy: dict[str, dict[str, Any]] = {}

        for strategy in strategies:
            if strategy == "s0_lines_60_10":
                fixture_path = baseline_path
            else:
                fixture_path = (
                    ROOT
                    / "evaluation"
                    / "experiments"
                    / "chunking"
                    / "fixtures"
                    / repo_id
                    / f"{strategy}.json.gz"
                )
                if not fixture_path.is_file():
                    raise FileNotFoundError(
                        f"Fixture for repository {repo_id!r} and strategy "
                        f"{strategy!r} is missing: {fixture_path}"
                    )
            report = await run_offline_retrieval(
                fixture_path=fixture_path,
                repo_id=repo_id,
                split=split,
                entry=entry,
                root=ROOT,
                limit=args.limit,
                record_details=True,
            )
            reports_by_strategy[strategy] = report
            fixture = load_fixture(fixture_path)
            fixture_sha = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
            rendered = render_strategy_report(
                report,
                split_questions,
                fixture,
                baseline_fixture,
                strategy=strategy,
                split=split,
                fixture_sha256=fixture_sha,
            )
            strategy_path = (
                output_dir / repo_id / f"{strategy}-{split}.md"
            )
            strategy_path.parent.mkdir(parents=True, exist_ok=True)
            with strategy_path.open("w", encoding="utf-8", newline="\n") as output:
                output.write(rendered)
            written_paths.append(strategy_path)

        summary = render_repository_summary(
            split_questions,
            reports_by_strategy,
            repo_id=repo_id,
            split=split,
        )
        summary_path = output_dir / repo_id / f"summary-{split}.md"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8", newline="\n") as output:
            output.write(summary)
        written_paths.append(summary_path)
    return written_paths


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="all", help="manifest repository ID or all")
    parser.add_argument("--strategy", default="all", help="candidate strategy, alias, or all")
    parser.add_argument(
        "--split",
        choices=("development", "smoke", "held_out", "all"),
        default="development",
    )
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--confirm-frozen-heldout", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        paths = asyncio.run(_run(args))
    except (FileNotFoundError, OSError, ValueError, RuntimeError, SQLAlchemyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
