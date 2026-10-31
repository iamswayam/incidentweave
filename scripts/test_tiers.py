"""Run one of the documented test tiers with its required pytest settings."""

from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> int:
    """Run the selected test tier and return its exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tier",
        choices=("fast", "integration", "evaluation", "full"),
        help="test tier to run",
    )
    tier = parser.parse_args().tier

    commands = {
        "fast": [[sys.executable, "-m", "pytest", "tests/unit", "-q"]],
        "integration": [[sys.executable, "-m", "pytest", "tests/integration", "-q"]],
        "evaluation": [
            [sys.executable, "-m", "pytest", "tests/evaluation", "-q"],
            [sys.executable, "-m", "scripts.check_retrieval_gate", "--split", "smoke"],
        ],
        "full": [[sys.executable, "-m", "pytest", "-q"]],
    }

    for command in commands[tier]:
        result = subprocess.run(command, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
