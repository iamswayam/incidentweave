"""Prepare, embed, and evaluate the precommitted chunking comparison."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.build_fixture import load_fixture  # noqa: E402
from evaluation.chunking_experiment import (  # noqa: E402
    CACHE_ROOT,
    EXPERIMENT_ROOT,
    S0_STRATEGY,
    SOURCE_ROOT,
    STRATEGIES,
    _pooled_metrics,
    _read_cache_vector,
    _text_hash,
    build_candidate_fixture,
    build_strategy_chunks_and_count,
    check_s0_reproduces_baseline,
    compute_metrics,
    discover_sources,
    embed_missing,
    load_protocol,
    paired_statistics,
    plan_embeddings,
    select_winner,
)
from evaluation.golden import load_golden_set  # noqa: E402
from evaluation.manifest import (  # noqa: E402
    MANIFEST_PATH,
    load_manifest,
    manifest_root,
)


def _manifest_inputs(manifest_path: Path) -> tuple[dict[str, Any], Path]:
    asset_root = manifest_root(manifest_path)
    return load_manifest(manifest_path, root=asset_root), asset_root


def _load_baselines(
    manifest: dict[str, Any],
    asset_root: Path,
) -> dict[str, dict[str, Any]]:
    return {
        entry["id"]: load_fixture(asset_root / entry["fixture"]["path"])
        for entry in manifest["repositories"]
    }


def _build_plan_inputs(
    manifest: dict[str, Any],
    asset_root: Path,
) -> tuple[
    dict[str, dict[str, list[dict[str, Any]]]],
    dict[str, dict[str, int]],
    dict[str, dict[str, Any]],
]:
    baselines = _load_baselines(manifest, asset_root)
    all_chunks: dict[str, dict[str, list[dict[str, Any]]]] = {}
    skipped: dict[str, dict[str, int]] = {}
    for entry in manifest["repositories"]:
        repo_id = entry["id"]
        source_path = SOURCE_ROOT / repo_id
        exclude_prefixes = ("tests/fixtures/",) if repo_id == "incidentweave" else ()
        sources = discover_sources(source_path, exclude_prefixes=exclude_prefixes)
        all_chunks[repo_id] = {}
        skipped[repo_id] = {}
        for strategy in STRATEGIES:
            chunks, secret_count = build_strategy_chunks_and_count(
                strategy,
                sources,
            )
            all_chunks[repo_id][strategy] = chunks
            skipped[repo_id][strategy] = secret_count
        check_s0_reproduces_baseline(
            all_chunks[repo_id][S0_STRATEGY],
            baselines[repo_id],
        )
    return all_chunks, skipped, baselines


def _texts_to_embed_for(
    chunks: list[dict[str, Any]],
    baseline_fixture: dict[str, Any],
    cache_dir: Path,
) -> int:
    reusable_contents = {
        str(chunk["content"]) for chunk in baseline_fixture["chunks"]
    }
    hashes = {
        _text_hash(str(chunk["embedding_text"]))
        for chunk in chunks
        if str(chunk["embedding_text"]) not in reusable_contents
        and not (cache_dir / f"{_text_hash(str(chunk['embedding_text']))}.json").is_file()
    }
    return len(hashes)


def _prepare_sources(manifest_path: Path) -> int:
    manifest, _asset_root = _manifest_inputs(manifest_path)
    SOURCE_ROOT.mkdir(parents=True, exist_ok=True)
    for entry in manifest["repositories"]:
        repository_root = SOURCE_ROOT / entry["id"]
        if not repository_root.exists():
            try:
                subprocess.run(
                    ["git", "clone", "--no-checkout", entry["url"], str(repository_root)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                raise RuntimeError(
                    f"Could not clone source for {entry['id']}"
                ) from exc
        try:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository_root),
                    "checkout",
                    "--detach",
                    entry["pinned_sha"],
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            completed = subprocess.run(
                ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(
                f"Could not verify pinned source for {entry['id']}"
            ) from exc
        observed_sha = completed.stdout.strip()
        if observed_sha != entry["pinned_sha"]:
            raise RuntimeError(
                f"{entry['id']} checkout mismatch: expected "
                f"{entry['pinned_sha']}, got {observed_sha}"
            )
        print(f"{entry['id']}: {observed_sha}")
    return 0


def _plan(manifest_path: Path) -> int:
    manifest, asset_root = _manifest_inputs(manifest_path)
    protocol = load_protocol()
    try:
        all_chunks, skipped, baselines = _build_plan_inputs(manifest, asset_root)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    texts = plan_embeddings(all_chunks, baselines, CACHE_ROOT)
    total_requests = math.ceil(
        len(texts) / int(protocol["embedding"]["batch_size"])
    )
    print(
        f"{'Repository':<26} {'Strategy':<27} {'Chunks':>8} "
        f"{'Secret skipped':>15} {'Texts to embed':>15}"
    )
    for entry in manifest["repositories"]:
        repo_id = entry["id"]
        for strategy in STRATEGIES:
            chunks = all_chunks[repo_id][strategy]
            print(
                f"{repo_id:<26} {strategy:<27} {len(chunks):>8} "
                f"{skipped[repo_id][strategy]:>15} "
                f"{_texts_to_embed_for(chunks, baselines[repo_id], CACHE_ROOT):>15}"
            )
    print(f"Total unique texts to embed: {len(texts)}")
    print(f"Batch requests needed: {total_requests}")
    print(
        "Caps: "
        f"{protocol['embedding']['max_texts']} texts, "
        f"{protocol['embedding']['max_batch_requests']} batch requests "
        f"of {protocol['embedding']['batch_size']}"
    )
    if len(texts) > int(protocol["embedding"]["max_texts"]) or total_requests > int(
        protocol["embedding"]["max_batch_requests"]
    ):
        print("Embedding plan exceeds the protocol caps.", file=sys.stderr)
        return 2
    return 0


async def _embed(manifest_path: Path) -> int:
    manifest, asset_root = _manifest_inputs(manifest_path)
    all_chunks, _skipped, baselines = _build_plan_inputs(manifest, asset_root)
    texts = plan_embeddings(all_chunks, baselines, CACHE_ROOT)
    if os.environ.get("GEMINI_API_KEY") is None:
        from app.config import settings

        if settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY is required for the confirmed embed command")
    from scripts.embed_chunks import embed_texts

    await embed_missing(texts, CACHE_ROOT, embed_texts)
    print(f"Cached embeddings: {len(texts)}")
    return 0


def _public_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if not key.startswith("_")}


def _markdown_report(
    protocol: dict[str, Any],
    results: dict[str, dict[str, Any]],
    decision: dict[str, Any],
    artifacts: dict[str, dict[str, dict[str, Any]]],
) -> str:
    lines = [
        "# Chunking comparison: development",
        "",
        "| Decision | Winner | Status |",
        "|---|---|---|",
        f"| Strategy | {decision['winner']} | {decision['status']} |",
        "",
        "| Candidate | Repository Hit@5 loss | Repository MRR loss | "
        "Pooled MRR gain | Pooled mean cost | Pooled p95 cost | Qualifies |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for strategy, conditions in decision["conditions"].items():
        lines.append(
            f"| {strategy} | {conditions['repository_hit5_loss']} | "
            f"{conditions['repository_mrr_loss']} | "
            f"{conditions['pooled_mrr_gain']} | "
            f"{conditions['pooled_mean_cost']} | "
            f"{conditions['pooled_p95_cost']} | {conditions['qualifies']} |"
        )
    lines.extend(
        [
            "",
            "| Rule | Value |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| {key} | {value} |" for key, value in decision["rules"].items()
    )
    lines.extend(
        [
            "",
            "| Repository | Strategy | Hit@1 | Hit@3 | Hit@5 | Span MRR | "
            "Mean cost | p95 cost | Coverage@5 | Density@5 | Top1 density | Test share |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for strategy in protocol["strategies"]:
        for repo_id, metrics in results[strategy]["repositories"].items():
            retrieval = metrics["retrieval"]
            lines.append(
                f"| {repo_id} | {strategy} | "
                f"{retrieval['hit_at_1']['successes']}/{retrieval['count']} | "
                f"{retrieval['hit_at_3']['successes']}/{retrieval['count']} | "
                f"{retrieval['hit_at_5']['successes']}/{retrieval['count']} | "
                f"{retrieval['mrr']:.6f} | {metrics['cost']['mean']:.2f} | "
                f"{metrics['cost']['p95']:.0f} | "
                f"{metrics['coverage_at_5']['rate']:.6f} | "
                f"{metrics['density_at_5']['rate']:.6f} | "
                f"{metrics['top1_density']['rate']:.6f} | "
                f"{metrics['test_share']['rate']:.6f} |"
            )
    lines.extend(
        [
            "",
            "| Strategy | Pooled Hit@1 | Pooled Hit@3 | Pooled Hit@5 | "
            "Pooled span MRR | Mean cost | p95 cost |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for strategy in protocol["strategies"]:
        pooled = results[strategy]["pooled"]
        retrieval = pooled["retrieval"]
        lines.append(
            f"| {strategy} | {retrieval['hit_at_1']['successes']}/"
            f"{retrieval['count']} | {retrieval['hit_at_3']['successes']}/"
            f"{retrieval['count']} | {retrieval['hit_at_5']['successes']}/"
            f"{retrieval['count']} | {retrieval['mrr']:.6f} | "
            f"{pooled['cost']['mean']:.2f} | {pooled['cost']['p95']:.0f} |"
        )
    lines.extend(
        [
            "",
            "| Strategy | Wins | Losses | Ties | Exact sign-test p | "
            "Delta MRR | Bootstrap 95% interval |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for strategy in protocol["strategies"]:
        if strategy == S0_STRATEGY:
            continue
        paired = results[strategy]["paired_vs_s0"]
        low, high = paired["bootstrap_interval"]
        lines.append(
            f"| {strategy} | {paired['wins']} | {paired['losses']} | "
            f"{paired['ties']} | {paired['sign_test_p_value']:.6f} | "
            f"{paired['delta_mrr']:.6f} | [{low:.6f}, {high:.6f}] |"
        )
    lines.extend(
        [
            "",
            "| Repository | Strategy | Fixture SHA-256 | Fixture bytes |",
            "|---|---|---|---:|",
        ]
    )
    for repo_id, repo_artifacts in artifacts.items():
        for strategy, artifact in repo_artifacts.items():
            lines.append(
                f"| {repo_id} | {strategy} | {artifact['sha256']} | "
                f"{artifact['bytes']} |"
            )
    return "\n".join(lines) + "\n"


async def _evaluate(manifest_path: Path) -> int:
    from evaluation.retrieval_eval import run_offline_retrieval

    manifest, asset_root = _manifest_inputs(manifest_path)
    protocol = load_protocol()
    baselines = _load_baselines(manifest, asset_root)
    strategy_results: dict[str, dict[str, Any]] = {
        strategy: {"repositories": {}, "paired_vs_s0": None}
        for strategy in STRATEGIES
    }
    artifacts: dict[str, dict[str, dict[str, Any]]] = {}
    baseline_rr: dict[str, dict[str, float]] = {}

    for entry in manifest["repositories"]:
        repo_id = entry["id"]
        baseline_fixture = baselines[repo_id]
        sources = discover_sources(
            SOURCE_ROOT / repo_id,
            exclude_prefixes=("tests/fixtures/",)
            if repo_id == "incidentweave"
            else (),
        )
        baseline_path = asset_root / entry["fixture"]["path"]
        artifacts[repo_id] = {
            S0_STRATEGY: {
                "sha256": entry["fixture"]["sha256"],
                "bytes": baseline_path.stat().st_size,
            }
        }
        all_chunks: dict[str, list[dict[str, Any]]] = {}
        skipped: dict[str, int] = {}
        for strategy in STRATEGIES:
            all_chunks[strategy], skipped[strategy] = (
                build_strategy_chunks_and_count(
                    strategy,
                    sources,
                )
            )
        check_s0_reproduces_baseline(
            all_chunks[S0_STRATEGY],
            baseline_fixture,
        )

        baseline_vectors = {
            str(chunk["content"]): chunk["embedding"]
            for chunk in baseline_fixture["chunks"]
        }
        for strategy in STRATEGIES:
            if strategy == S0_STRATEGY:
                fixture_path = asset_root / entry["fixture"]["path"]
                fixture = baseline_fixture
            else:
                vectors: dict[str, list[float]] = {}
                missing_hashes: set[str] = set()
                for chunk in all_chunks[strategy]:
                    text = str(chunk["embedding_text"])
                    digest = _text_hash(text)
                    if text in baseline_vectors:
                        vectors[digest] = baseline_vectors[text]
                        continue
                    cached_path = CACHE_ROOT / f"{digest}.json"
                    if not cached_path.is_file():
                        missing_hashes.add(digest)
                        continue
                    vectors[digest] = _read_cache_vector(cached_path)
                if missing_hashes:
                    raise RuntimeError(
                        f"{repo_id}/{strategy} is missing "
                        f"{len(missing_hashes)} cached embeddings"
                    )
                fixture_sha, fixture_bytes = build_candidate_fixture(
                    repo_id,
                    strategy,
                    all_chunks[strategy],
                    baseline_fixture,
                    vectors,
                    int(entry["fixture"]["max_bytes"]),
                    output_root=asset_root,
                    secret_skipped_count=skipped[strategy],
                )
                fixture_path = (
                    asset_root
                    / "evaluation"
                    / "experiments"
                    / "chunking"
                    / "fixtures"
                    / repo_id
                    / f"{strategy}.json.gz"
                )
                fixture = load_fixture(fixture_path)
                artifacts.setdefault(repo_id, {})[strategy] = {
                    "sha256": fixture_sha,
                    "bytes": fixture_bytes,
                }

            report = await run_offline_retrieval(
                fixture_path=fixture_path,
                repo_id=repo_id,
                split="development",
                entry=entry,
                manifest_path=manifest_path,
                root=asset_root,
                record_retrieved=True,
            )
            golden = load_golden_set(asset_root / entry["questions"]["path"])
            development_questions = [
                question
                for question in golden["questions"]
                if question["id"] in set(entry["splits"]["development"])
            ]
            fixture_size = fixture_path.stat().st_size
            metrics = compute_metrics(
                report,
                sources,
                development_questions,
                fixture,
                fixture_bytes=fixture_size,
            )
            strategy_results[strategy]["repositories"][repo_id] = metrics
            if strategy == S0_STRATEGY:
                baseline_rr[repo_id] = {
                    item["id"]: float(item["reciprocal_rank"])
                    for item in metrics["question_metrics"]
                    if item["category"] in {"direct", "paraphrased"}
                }

    for strategy in STRATEGIES:
        repository_metrics = strategy_results[strategy]["repositories"]
        strategy_results[strategy]["pooled"] = _pooled_metrics(repository_metrics)
        if strategy != S0_STRATEGY:
            candidate_rr: list[float] = []
            s0_rr: list[float] = []
            for entry in manifest["repositories"]:
                repo_id = entry["id"]
                candidate_by_id = {
                    item["id"]: float(item["reciprocal_rank"])
                    for item in repository_metrics[repo_id]["question_metrics"]
                    if item["category"] in {"direct", "paraphrased"}
                }
                for question_id, baseline_rank in baseline_rr[repo_id].items():
                    candidate_rr.append(candidate_by_id[question_id])
                    s0_rr.append(baseline_rank)
            strategy_results[strategy]["paired_vs_s0"] = paired_statistics(
                candidate_rr,
                s0_rr,
                protocol,
            )

    decision = select_winner(strategy_results, protocol)
    report_data = {
        "protocol": protocol,
        "repositories": [
            entry["id"] for entry in manifest["repositories"]
        ],
        "selection_split": "development",
        "strategies": {
            strategy: {
                "repositories": {
                    repo_id: _public_metrics(metrics)
                    for repo_id, metrics in value["repositories"].items()
                },
                "pooled": _public_metrics(value["pooled"]),
                "paired_vs_s0": value["paired_vs_s0"],
            }
            for strategy, value in strategy_results.items()
        },
        "artifacts": artifacts,
        "decision": decision,
    }
    EXPERIMENT_ROOT.mkdir(parents=True, exist_ok=True)
    json_path = EXPERIMENT_ROOT / "report-development.json"
    json_path.write_text(
        json.dumps(report_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path = EXPERIMENT_ROOT / "report-development.md"
    markdown_path.write_text(
        _markdown_report(
            protocol,
            {
                strategy: {
                    "repositories": {
                        repo_id: _public_metrics(metrics)
                        for repo_id, metrics in value["repositories"].items()
                    },
                    "pooled": _public_metrics(value["pooled"]),
                    "paired_vs_s0": value["paired_vs_s0"],
                }
                for strategy, value in strategy_results.items()
            },
            decision,
            artifacts,
        ),
        encoding="utf-8",
    )
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    print(f"Decision: {decision['status']} ({decision['winner']})")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("prepare-sources", "plan", "embed", "evaluate"),
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument(
        "--confirm-embedding-calls",
        action="store_true",
        help="explicitly authorize the embed command to call the embedding provider",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "embed" and not args.confirm_embedding_calls:
        print(
            "The embed command requires --confirm-embedding-calls.",
            file=sys.stderr,
        )
        return 2
    try:
        if args.command == "prepare-sources":
            return _prepare_sources(args.manifest)
        if args.command == "plan":
            return _plan(args.manifest)
        if args.command == "embed":
            return asyncio.run(_embed(args.manifest))
        return asyncio.run(_evaluate(args.manifest))
    except (OSError, RuntimeError, ValueError, SQLAlchemyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
