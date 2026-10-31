"""Run one of the documented test tiers with its required pytest settings."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run the selected test tier and return its exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tier",
        choices=("fast", "integration", "evaluation", "full"),
        help="test tier to run",
    )
    parser.add_argument(
        "--area",
        help="run only this area inside tests/unit (fast tier only)",
    )
    arguments = parser.parse_args()
    tier = arguments.tier
    if arguments.area is not None and tier != "fast":
        parser.error("--area is only supported with the fast tier")

    unit_root = Path("tests/unit")
    if arguments.area is not None:
        area_path = (unit_root / arguments.area).resolve()
        try:
            area_path.relative_to(unit_root.resolve())
        except ValueError:
            parser.error("--area must name a folder inside tests/unit")
        if not area_path.is_dir():
            parser.error(f"unknown unit area: {arguments.area}")
        fast_path = str(area_path)
    else:
        fast_path = "tests/unit"

    commands = {
        "fast": [[sys.executable, "-m", "pytest", fast_path, "-q"]],
        "integration": [[sys.executable, "-m", "pytest", "tests/integration", "-q"]],
        "evaluation": [
            [sys.executable, "-m", "pytest", "tests/evaluation", "-q"],
            [sys.executable, "-m", "scripts.check_retrieval_gate", "--split", "smoke"],
        ],
        "full": [
            [sys.executable, "-m", "pytest", "tests/unit", "-q"],
            [sys.executable, "-m", "pytest", "tests/integration", "-q"],
            [sys.executable, "-m", "pytest", "tests/evaluation", "-q"],
            [sys.executable, "-m", "scripts.check_retrieval_gate", "--split", "smoke"],
        ],
    }

    for command in commands[tier]:
        result = subprocess.run(command, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
