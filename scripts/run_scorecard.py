"""Compute the registered retrieval and guard scorecard from exported rankings."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation.manifest import MANIFEST_PATH, manifest_root
from evaluation.scorecard import write_scorecard


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="development rankings export JSON")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("evaluation/experiments/scorecard/v1-development.json"),
        help="scorecard JSON output path",
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    root = manifest_root(args.manifest)
    scorecard = write_scorecard(
        args.input,
        args.out,
        manifest_path=args.manifest,
        root=root,
    )
    print(f"Scorecard: {args.out}")
    print(f"Repositories: {', '.join(scorecard['metadata']['repository_ids'])}")
    print(f"Development questions: {scorecard['metadata']['n']}")


if __name__ == "__main__":
    main()
