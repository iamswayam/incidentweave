"""Run the offline retrieval evaluation and enforce its committed regression gate."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.gate import evaluate_gate, load_gate  # noqa: E402
from evaluation.retrieval_eval import run_offline_retrieval  # noqa: E402

GATE_PATH = ROOT / "evaluation" / "gate.json"
BASELINE_PATH = ROOT / "evaluation" / "results" / "offline-baseline.json"


def _format_table(result: dict[str, Any]) -> str:
    lines = [
        f"{'Label':<20} {'Metric':<22} {'Baseline':>12} "
        f"{'Observed':>12} {'Allowed min':>12} {'Result':>8}"
    ]
    for check in result["checks"]:
        lines.append(
            f"{check['label_type']:<20} {check['metric']:<22} "
            f"{check['baseline']:>12.6g} {check['observed']:>12.6g} "
            f"{check['allowed_min']:>12.6g} "
            f"{'PASS' if check['passed'] else 'FAIL':>8}"
        )
    return "\n".join(lines)


async def _run(args: argparse.Namespace) -> int:
    gate = load_gate(GATE_PATH)
    report = await run_offline_retrieval()
    result = evaluate_gate(report, gate)
    print(_format_table(result))
    if args.out is not None:
        output_path = args.out.resolve()
        protected_paths = {GATE_PATH.resolve(), BASELINE_PATH.resolve()}
        if output_path in protected_paths:
            raise ValueError("--out cannot overwrite the gate or baseline")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Report: {args.out}")
    return 0 if result["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="optional path for the full JSON report")
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
