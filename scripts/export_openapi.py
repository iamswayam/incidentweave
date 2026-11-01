"""Export the application's OpenAPI schema without loading repository secrets."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "docs" / "reference" / "openapi.json"


def generate_openapi_json() -> str:
    """Return a stable OpenAPI document while isolating import-time .env loading."""

    original_directory = Path.cwd()
    original_path = sys.path.copy()
    with tempfile.TemporaryDirectory(prefix="incidentweave-openapi-") as temp_dir:
        os.chdir(temp_dir)
        sys.path.insert(0, str(REPOSITORY_ROOT))
        try:
            from app.main import app

            return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
        finally:
            os.chdir(original_directory)
            sys.path[:] = original_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="destination path (default: docs/reference/openapi.json)",
    )
    arguments = parser.parse_args()

    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generate_openapi_json(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
