"""Qualify dataset repository candidates and later mine linked issues."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation.candidates import write_qualification_report
from evaluation.manifest import MANIFEST_PATH

ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / "evaluation" / "cache" / "qualify"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("qualify", help="clone and qualify the registered candidates")
    args = parser.parse_args()
    if args.command == "qualify":
        report = write_qualification_report(
            CACHE_ROOT,
            MANIFEST_PATH,
        )
        for candidate in report["candidates"]:
            print(
                f"QUALIFIED {candidate['id']} ({candidate['role']}): "
                f"{candidate['source_python_lines']} source lines, "
                f"{candidate['qualifying_issue_count']} issues, "
                f"{candidate['fixture_location']} fixture"
            )
        for item in report["pending_verification"]:
            print(f"PENDING {item['id']}: {item['reason']}")
        for item in report["rejected"]:
            print(f"REJECTED {item['id']}: {item['reason']}")
        for swap in report["swaps"]:
            print(f"SWAP {swap['replaced']} -> {swap['replacement']}")
        print(f"Qualification report: {CACHE_ROOT / 'results.json'}")


if __name__ == "__main__":
    main()
