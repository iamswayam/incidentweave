"""Run the Phase 8 retrieval and investigation evaluation."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.runner import EVALUATION_ROOT, run_evaluation  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Phase 8 retrieval and two-pass investigation evaluation "
            "against the incidentweave-eval repository."
        ),
        epilog="Example: .\\.venv\\Scripts\\python.exe scripts\\run_eval.py",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=2,
        help="Number of generation passes to run (default: 2)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    report = await run_evaluation(passes=args.passes)
    run_dir = EVALUATION_ROOT / "results" / "runs" / report["run_id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    snapshot_path = EVALUATION_ROOT / "_snapshot"
    if snapshot_path.exists():
        shutil.rmtree(snapshot_path)
    print("Evaluation complete")
    print(f"Run ID: {report['run_id']}")
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
