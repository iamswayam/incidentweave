"""Run the offline retrieval-only evaluation."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.retrieval_eval import run_offline_retrieval  # noqa: E402


def _compact_table(report: dict[str, Any]) -> str:
    lines = [
        "Measure             Hit@1 (95% Wilson)          Hit@3 (95% Wilson)          "
        "Hit@5 (95% Wilson)          MRR"
    ]
    for key, label in (("substring_labels", "Substring labels"), ("spans", "Spans")):
        summary = report["summary"][key]
        cells = []
        for k in (1, 3, 5):
            metric = summary[f"hit_at_{k}"]
            low, high = metric["wilson_95"]
            cells.append(
                f"{metric['successes']}/{summary['count']} "
                f"[{low:.2f}, {high:.2f}]"
            )
        lines.append(
            f"{label:<20} {cells[0]:<27} {cells[1]:<27} "
            f"{cells[2]:<27} {summary['mrr']:.3f}"
        )
    return "\n".join(lines)


async def _run(args: argparse.Namespace) -> None:
    report = await run_offline_retrieval(limit=args.limit)
    print(_compact_table(report))
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Report: {args.out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="optional path for the JSON report")
    parser.add_argument("--limit", type=int, default=5, help="retrieval result limit")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
