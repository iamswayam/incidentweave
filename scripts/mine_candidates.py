"""Qualify dataset repository candidates and later mine linked issues."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation.candidates import write_qualification_report
from evaluation.manifest import MANIFEST_PATH
from evaluation.question_review import (
    create_review_pack,
    create_second_pass,
    ingest_review_pack,
    mine_issues,
    run_agreement,
)

ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / "evaluation" / "cache" / "qualify"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("qualify", help="clone and qualify the registered candidates")
    issues_parser = subparsers.add_parser(
        "issues", help="mine linked issues and pinned source spans for one candidate"
    )
    issues_parser.add_argument("repo_id")
    pack_parser = subparsers.add_parser("pack", help="render a maintainer review pack")
    pack_parser.add_argument("repo_id")
    ingest_parser = subparsers.add_parser("ingest", help="validate and ingest a reviewed pack")
    ingest_parser.add_argument("repo_id")
    ingest_parser.add_argument(
        "--targets",
        choices=("full", "reduced"),
        default="full",
    )
    second_pass_parser = subparsers.add_parser(
        "second-pass", help="create a stratified blind second-pass sample"
    )
    second_pass_parser.add_argument("repo_ids", nargs="+")
    agreement_parser = subparsers.add_parser(
        "agreement", help="measure filled second-pass agreement and effort"
    )
    agreement_parser.add_argument("repo_ids", nargs="+")
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
                f"{candidate['qualifying_issue_count']} gh issues, "
                f"{candidate['fixture_location']} fixture"
            )
        for candidate in report["qualified_backups"]:
            print(
                f"QUALIFIED BACKUP {candidate['id']}: "
                f"{candidate['qualifying_issue_count']} gh issues"
            )
        for item in report["rejected"]:
            print(f"REJECTED {item['id']}: {item['reason']}")
        for item in report["verification_errors"]:
            print(f"VERIFICATION ERROR {item['id']}: {item['reason']}")
        for swap in report["swaps"]:
            print(f"SWAP {swap['replaced']} -> {swap['replacement']}")
        print(f"Qualification report: {CACHE_ROOT / 'results.json'}")
    elif args.command == "issues":
        path = mine_issues(args.repo_id)
        print(f"Mined issues: {path}")
    elif args.command == "pack":
        path, skipped = create_review_pack(args.repo_id)
        print(f"Review pack: {path}")
        if skipped:
            print(f"WARNING: skipped {skipped} draft items without a question")
    elif args.command == "ingest":
        report = ingest_review_pack(args.repo_id, targets=args.targets)
        print(
            f"INGESTED {args.repo_id}: accepted {report['accepted']}, "
            f"rejected {report['rejected']}, edited {report['edited']}, "
            f"median {report['median_minutes']} minutes"
        )
    elif args.command == "second-pass":
        path, sample_size = create_second_pass(args.repo_ids)
        print(f"Second-pass pack: {path} ({sample_size} questions)")
    elif args.command == "agreement":
        result = run_agreement(args.repo_ids)
        for label in ("answerability", "gold_files"):
            metric = result[label]
            print(
                f"{label}: {metric['agreement']}/{metric['total']} "
                f"({metric['rate']:.1%}), 95% Wilson "
                f"{metric['wilson_95'][0]:.1%}-{metric['wilson_95'][1]:.1%} "
                f"{'PASS' if metric['passed'] else 'FAIL'}"
            )
        print(
            f"First-pass median: {result['median_first_pass_minutes']} minutes "
            f"{'PASS' if result['median_effort_passed'] else 'FAIL'}"
        )


if __name__ == "__main__":
    main()
