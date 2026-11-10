"""Export, rerank, import notebook scores, or analyse the development-only reranker study.

Usage: export, export-requests, notebook scoring, import-results, analyze.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from evaluation.manifest import MANIFEST_PATH, manifest_root
from evaluation.studies.reranker.reranker_experiment import (
    PIN_PATH,
    RANKINGS_PATH,
    REPORT_JSON_PATH,
    REPORT_MARKDOWN_PATH,
    RERANKER_REQUESTS_PATH,
    export_development_candidates,
    export_reranker_requests,
    import_reranker_results,
    run_analysis_stage,
    run_rerank_stage,
)


def _non_negative_seconds(value: str) -> float:
    import math

    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative number") from exc
    if not math.isfinite(seconds) or seconds < 0:
        raise argparse.ArgumentTypeError("must be a finite non-negative number")
    return seconds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    export = commands.add_parser("export", help="freeze the development top-20 candidates")
    export.add_argument("--out", type=Path, default=RANKINGS_PATH)
    export.add_argument("--manifest", type=Path, default=MANIFEST_PATH)

    export_requests = commands.add_parser(
        "export-requests", help="write the frozen development candidates for notebook scoring"
    )
    export_requests.add_argument("--input", type=Path, default=RANKINGS_PATH)
    export_requests.add_argument("--out", type=Path, default=RERANKER_REQUESTS_PATH)
    export_requests.add_argument("--manifest", type=Path, default=MANIFEST_PATH)

    import_results = commands.add_parser(
        "import-results", help="import offline notebook scores into frozen rankings"
    )
    import_results.add_argument("--input", type=Path, default=RANKINGS_PATH)
    import_results.add_argument("--requests", type=Path, required=True)
    import_results.add_argument("--results", type=Path, required=True)
    import_results.add_argument("--pin", type=Path, default=PIN_PATH)
    import_results.add_argument("--out", type=Path)
    import_results.add_argument("--manifest", type=Path, default=MANIFEST_PATH)

    rerank = commands.add_parser("rerank", help="rerank frozen candidates with the pinned model")
    rerank.add_argument("--input", type=Path, default=RANKINGS_PATH)
    rerank.add_argument("--out", type=Path)
    rerank.add_argument("--pin", type=Path, default=PIN_PATH)
    rerank.add_argument(
        "--min-interval-seconds",
        type=_non_negative_seconds,
        default=0.0,
        help="minimum time between rerank request start times",
    )
    rerank.add_argument("--manifest", type=Path, default=MANIFEST_PATH)

    analyze = commands.add_parser("analyze", help="analyse frozen baseline and treatment offline")
    analyze.add_argument("--input", type=Path, default=RANKINGS_PATH)
    analyze.add_argument("--json-out", type=Path, default=REPORT_JSON_PATH)
    analyze.add_argument("--markdown-out", type=Path, default=REPORT_MARKDOWN_PATH)
    analyze.add_argument("--manifest", type=Path, default=MANIFEST_PATH)

    args = parser.parse_args()
    root = manifest_root(args.manifest)
    if args.command == "export":
        data = asyncio.run(
            export_development_candidates(args.out, manifest_path=args.manifest, root=root)
        )
        question_count = sum(len(repo["questions"]) for repo in data["repositories"])
        print(f"Frozen {question_count} development questions.")
    elif args.command == "export-requests":
        requests = export_reranker_requests(
            args.input, args.out, manifest_path=args.manifest, root=root
        )
        print(f"Exported requests for {len(requests['items'])} development questions.")
    elif args.command == "import-results":
        data = import_reranker_results(
            args.input,
            args.requests,
            args.results,
            pin_path=args.pin,
            output_path=args.out,
            manifest_path=args.manifest,
            root=root,
        )
        question_count = sum(len(repo["questions"]) for repo in data["repositories"])
        print(f"Imported local reranker scores for {question_count} development questions.")
    elif args.command == "rerank":
        data = asyncio.run(
            run_rerank_stage(
                args.input,
                pin_path=args.pin,
                output_path=args.out,
                min_interval_seconds=args.min_interval_seconds,
                manifest_path=args.manifest,
                root=root,
            )
        )
        question_count = sum(len(repo["questions"]) for repo in data["repositories"])
        print(f"Reranked {question_count} development questions.")
        print(f"Rerank failures with baseline fallback: {data['metadata']['rerank_failure_count']}")
    else:
        report = run_analysis_stage(
            args.input,
            json_output=args.json_out,
            markdown_output=args.markdown_out,
            manifest_path=args.manifest,
            root=root,
        )
        print(f"Decision: {report['decision']['decision']}")
        for failure in report["decision"]["failing_conditions"]:
            print(f"Failing condition: {failure}")


if __name__ == "__main__":
    main()
