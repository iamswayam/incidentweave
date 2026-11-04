"""CLI wrapper for the registered full-text ablation study."""

from __future__ import annotations

import argparse

from evaluation.studies.fulltext.run_fulltext_ablation import main


def cli() -> None:
    argparse.ArgumentParser(description=__doc__).parse_known_args()
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
