# Requires: uv sync --extra eval-frameworks
"""Exploration-grade RAGAS report for saved development end-to-end runs."""

from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evaluation.offline_eval_adapter import load_offline_eval_data

ROOT = Path(__file__).resolve().parents[1]
RUN_FILES = tuple(
    ROOT / "evaluation" / "results" / "runs" / f"end_to_end_dev_run_{repo}_2026-11-23.json"
    for repo in ("rq", "kopf", "luigi", "client_python")
)
METRIC_NAMES = ("faithfulness", "answer_relevancy")
JUDGE_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-001"


def _finite_score(value: Any) -> float | None:
    if value is None:
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if math.isfinite(score) else None


def _format_table(metric_summary: dict[str, dict[str, Any]]) -> str:
    lines = ["Metric           Mean     Scored", "---------------- -------  ------"]
    lines.extend(
        f"{name:<16} {summary['mean'] if summary['mean'] is not None else 'n/a':>7}  "
        f"{summary['scored_count']:>6}"
        for name, summary in metric_summary.items()
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-files", nargs="+", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    run_files = args.run_files if args.run_files is not None else RUN_FILES
    samples, summary = load_offline_eval_data(run_files)
    if not samples:
        raise ValueError("no successful development answers with text were found")

    output_path = args.output or (
        ROOT
        / "evaluation"
        / "results"
        / f"ragas_report_{datetime.now(UTC).date().isoformat()}.json"
    )
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {output_path}")

    from datasets import Dataset
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from ragas import evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, faithfulness

    from app.config import settings

    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY must be configured to run the RAGAS report")

    judge = ChatGoogleGenerativeAI(
        model=JUDGE_MODEL,
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=settings.gemini_api_key,
    )
    result = evaluate(
        dataset=Dataset.from_list(samples),
        metrics=[faithfulness, answer_relevancy],
        llm=LangchainLLMWrapper(judge),
        embeddings=LangchainEmbeddingsWrapper(embeddings),
    )

    score_rows = [
        {name: _finite_score(row.get(name)) for name in METRIC_NAMES} for row in result.scores
    ]
    metric_summary = {
        name: {
            "mean": (
                sum(values) / len(values)
                if (values := [row[name] for row in score_rows if row[name] is not None])
                else None
            ),
            "scored_count": sum(row[name] is not None for row in score_rows),
        }
        for name in METRIC_NAMES
    }
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "framework": "ragas",
        "judge": {"provider": "Gemini", "model": JUDGE_MODEL},
        "source_files": [path.name for path in run_files],
        "summary": summary,
        "metrics": metric_summary,
        "record_scores": [
            {"record_index": index, **scores} for index, scores in enumerate(score_rows)
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"RAGAS report: {output_path}")
    print(f"Records: {summary['success_count']} successful / {summary['total_records']} total")
    print(_format_table(metric_summary))


if __name__ == "__main__":
    main()
