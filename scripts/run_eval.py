"""Run the Phase 8 retrieval and investigation evaluation."""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.chunk_strategies import (  # noqa: E402
    DEFAULT_STRATEGY,
    SPLIT_CHOICES,
    STRATEGY_CHOICES,
)
from evaluation.runner import EVALUATION_ROOT, run_evaluation  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Phase 8 retrieval and two-pass investigation evaluation "
            "against an allowlisted evaluation repository."
        ),
        epilog="Example: .\\.venv\\Scripts\\python.exe scripts\\run_eval.py",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=2,
        choices=[2],
        help="Number of generation passes to run (default: 2)",
    )
    parser.add_argument(
        "--strategy",
        choices=STRATEGY_CHOICES,
        default=DEFAULT_STRATEGY,
        help="Evaluation-only chunking strategy (default: baseline)",
    )
    parser.add_argument(
        "--repo",
        default="incidentweave",
        help="manifest repository ID (default: incidentweave)",
    )
    parser.add_argument(
        "--split",
        choices=SPLIT_CHOICES,
        default="development",
        help="question split (default: development)",
    )
    parser.add_argument(
        "--confirm-frozen-heldout",
        action="store_true",
        help="confirm intentional evaluation of held-out questions",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    report = await run_evaluation(
        passes=args.passes,
        strategy=args.strategy,
        repo_id=args.repo,
        split=args.split,
        confirm_frozen_heldout=args.confirm_frozen_heldout,
    )
    run_dir = EVALUATION_ROOT / "results" / "runs" / report["run_id"]
    report_path = run_dir / "report.json"
    snapshot_path = EVALUATION_ROOT / "_snapshot"
    if snapshot_path.exists():
        shutil.rmtree(snapshot_path)
    print("Evaluation complete")
    print(f"Run ID: {report['run_id']}")
    print(f"Strategy: {report['strategy']}")
    print(f"Evaluation repository: {report['evaluation_repository']}")
    print(f"Report path: {report_path}")
    print(f"Questions: {len(report['records'][0])}")
    print(f"Snapshot chunks: {report['snapshot_chunks']}")
    print(f"Run summaries: {report['run_summaries']}")
    print(f"Outcome changes: {report['outcome_changes']}")
    print(f"Generation HTTP calls: {report['generation_http_calls']}")
    print(f"HTTP 429 responses: {report['generation_http_429_responses']}")
    print(f"Generation errors: {report['generation_error_count']}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
