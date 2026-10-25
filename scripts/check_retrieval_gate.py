"""Run manifest-selected offline retrieval gates and report per-repo and pooled metrics."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.gate import (  # noqa: E402
    evaluate_split_gate,
    load_gate,
    pooled_report,
)
from evaluation.manifest import (  # noqa: E402
    MANIFEST_PATH,
    load_manifest,
    manifest_root,
    select_repositories,
)
from evaluation.retrieval_eval import run_offline_retrieval  # noqa: E402
from evaluation.splits import SPLIT_CHOICES  # noqa: E402


def _format_repository_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        f"{'Repository':<20} {'Metric':<22} {'Baseline':>12} "
        f"{'Observed':>12} {'Allowed min':>12} {'Result':>8} {'Seconds':>9}"
    ]
    for row in rows:
        if row.get("error"):
            lines.append(
                f"{row['repo_id']:<20} {'evaluation':<22} {'-':>12} {'-':>12} "
                f"{'-':>12} {'FAIL':>8} {row.get('elapsed_seconds', 0):>8.2f}s"
            )
            lines.append(f"  Error: {row['error']}")
            continue
        for check in row["gate"]["checks"]:
            lines.append(
                f"{row['repo_id']:<20} {check['metric']:<22} "
                f"{check['baseline']:>12.6g} {check['observed']:>12.6g} "
                f"{check['allowed_min']:>12.6g} "
                f"{'PASS' if check['passed'] else 'FAIL':>8} "
                f"{row['elapsed_seconds']:>8.2f}s"
            )
    return "\n".join(lines)


def _format_pooled_table(pooled: dict[str, Any]) -> str:
    lines = [
        f"{'Label':<20} {'N':>5} {'Hit@1 (95% Wilson)':<27} "
        f"{'Hit@3 (95% Wilson)':<27} {'Hit@5 (95% Wilson)':<27} {'MRR':>8}"
    ]
    for label_type, summary in pooled["summary"].items():
        hits = []
        for cutoff in (1, 3, 5):
            metric = summary[f"hit_at_{cutoff}"]
            low, high = metric["wilson_95"]
            hits.append(
                f"{metric['successes']}/{summary['count']} [{low:.2f}, {high:.2f}]"
            )
        lines.append(
            f"{label_type:<20} {summary['count']:>5} {hits[0]:<27} "
            f"{hits[1]:<27} {hits[2]:<27} {summary['mrr']:>8.3f}"
        )
    return "\n".join(lines)


def _resource_path(root: Path, entry: dict[str, Any], resource: str) -> Path:
    return root / entry[resource]["path"]


async def _run(args: argparse.Namespace) -> int:
    asset_root = manifest_root(args.manifest)
    try:
        manifest = load_manifest(args.manifest, root=asset_root)
        repositories = select_repositories(manifest, args.repo)
    except (OSError, ValueError) as exc:
        print(f"Manifest error: {exc}", file=sys.stderr)
        return 1

    rows: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    all_passed = True
    protected_paths: set[Path] = set()
    for entry in repositories:
        for field in (
            "questions",
            "fixture",
            "full_gate",
            "full_baseline",
            "smoke_baseline",
            "smoke_gate",
        ):
            protected_paths.add(_resource_path(asset_root, entry, field).resolve())

        started_at = time.perf_counter()
        row: dict[str, Any] = {"repo_id": entry["id"]}
        try:
            report = await run_offline_retrieval(
                limit=args.limit,
                repo_id=entry["id"],
                split=args.split,
                entry=entry,
                root=asset_root,
            )
            gate_field = "smoke_gate" if args.split == "smoke" else "full_gate"
            gate = load_gate(_resource_path(asset_root, entry, gate_field))
            baseline_report = None
            if args.split in {"development", "held_out"}:
                baseline_report = json.loads(
                    _resource_path(asset_root, entry, "full_baseline").read_text(
                        encoding="utf-8"
                    )
                )
            gate_result = evaluate_split_gate(
                report,
                gate,
                split=args.split,
                full_baseline_report=baseline_report,
            )
            row.update(report=report, gate=gate_result)
            reports.append(report)
            all_passed = all_passed and gate_result["passed"]
        except (OSError, ValueError, RuntimeError, SQLAlchemyError) as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            all_passed = False
        row["elapsed_seconds"] = time.perf_counter() - started_at
        rows.append(row)

    print("Per-repository gate:")
    print(_format_repository_table(rows))
    failed_rows = [row for row in rows if row.get("error")]
    if failed_rows:
        print("\nPooled results: NOT COMPUTED because a selected repository failed.")
        pooled = None
    else:
        pooled = pooled_report(reports)
        print("\nPooled retrieval metrics:")
        print(_format_pooled_table(pooled))

    if args.out is not None:
        output_path = args.out.resolve()
        if output_path in protected_paths:
            raise ValueError("--out cannot overwrite a manifest input")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "split": args.split,
                    "repositories": rows,
                    "pooled": pooled,
                    "passed": all_passed,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"Report: {args.out}")
    return 0 if all_passed and not failed_rows else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--repo", help="run one manifest repository (default: all)")
    parser.add_argument("--split", choices=SPLIT_CHOICES, default="all")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--out", type=Path, help="optional path for the full JSON report")
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
