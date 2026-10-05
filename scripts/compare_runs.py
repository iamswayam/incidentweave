"""Compare two saved evaluation reports and print the deltas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.compare import compare_reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two evaluation report JSON files.",
    )
    parser.add_argument("report_a", type=Path, help="Path to the first report JSON file")
    parser.add_argument("report_b", type=Path, help="Path to the second report JSON file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.report_a.open("r", encoding="utf-8") as handle:
        report_a = json.load(handle)
    with args.report_b.open("r", encoding="utf-8") as handle:
        report_b = json.load(handle)

    diff = compare_reports(report_a, report_b)
    print(json.dumps(diff, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
