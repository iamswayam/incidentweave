"""CLI for running a repository investigation."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.investigation.service import investigate_repository  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run retrieval, grounding, generation, parsing, and persistence "
            "for one repository query."
        )
    )
    parser.add_argument("repo_name", help="Repository name stored in the database")
    parser.add_argument("query", help="Natural-language question to investigate")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum hybrid-search results to consider",
    )
    args = parser.parse_args()

    try:
        result = asyncio.run(
            investigate_repository(
                args.repo_name,
                args.query,
                limit=args.limit,
            )
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(f"Repository: {result['repository']}")
    print(f"Query: {result['query']}")
    print(f"Outcome: {result['outcome']}")
    print(f"Diagnosis: {result['diagnosis']}")
    print(f"Model self-rating: {result['confidence']}")
    print(f"Unavailable answer: {bool(result.get('unavailable_answer', False))}")
    print(f"Degraded: {bool(result.get('degraded', False))}")
    print(f"Degraded reason: {result.get('degraded_reason')}")
    print(f"Cited chunks: {result['cited_chunk_ids']}")
    print(f"Model: {result['model']}")
    print(f"Latency ms: {result['latency_ms']}")
    print(
        "Retry used: "
        f"{result['retry_used']}; model self-rating calibrated: "
        f"{result['confidence_calibrated']}"
    )
    print(f"Tool attempts: {len(result['tool_calls'])}")
    generation_trace = result.get("generation_trace")
    if isinstance(generation_trace, dict):
        safe_trace = {key: value for key, value in generation_trace.items() if key != "raw_text"}
    else:
        safe_trace = generation_trace
    print(f"Generation trace: {json.dumps(safe_trace, sort_keys=True)}")
    evidence = result.get("evidence")
    if isinstance(evidence, list) and evidence:
        print(f"Evidence metadata: {json.dumps(evidence, sort_keys=True)}")


if __name__ == "__main__":
    main()
