# Requires: uv sync --extra eval-frameworks
"""Exploration-grade DeepEval report for saved development end-to-end runs."""

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
JUDGE_MODEL = "gemini-2.5-flash"


def _finite_score(value: Any) -> float | None:
    if value is None:
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if math.isfinite(score) else None


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
        / f"deepeval_report_{datetime.now(UTC).date().isoformat()}.json"
    )
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {output_path}")

    from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
    from deepeval.models import DeepEvalBaseLLM
    from deepeval.test_case import LLMTestCase
    from langchain_google_genai import ChatGoogleGenerativeAI

    from app.config import settings

    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY must be configured to run the DeepEval report")

    class GeminiJudge(DeepEvalBaseLLM):
        def __init__(self) -> None:
            self._model = ChatGoogleGenerativeAI(
                model=JUDGE_MODEL,
                google_api_key=settings.gemini_api_key,
                temperature=0,
            )

        def load_model(self) -> Any:
            return self._model

        @staticmethod
        def _text(response: Any) -> str:
            content = response.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "".join(
                    block["text"]
                    for block in content
                    if isinstance(block, dict) and isinstance(block.get("text"), str)
                )
            raise TypeError("Gemini judge returned non-text content")

        def generate(self, prompt: str) -> str:
            return self._text(self._model.invoke(prompt))

        async def a_generate(self, prompt: str) -> str:
            return self._text(await self._model.ainvoke(prompt))

        def get_model_name(self) -> str:
            return JUDGE_MODEL

    judge = GeminiJudge()
    metrics = {
        "answer_relevancy": AnswerRelevancyMetric(model=judge, include_reason=True),
        "faithfulness": FaithfulnessMetric(model=judge, include_reason=True),
    }
    test_cases = [
        LLMTestCase(
            input=sample["question"],
            actual_output=sample["answer"],
            retrieval_context=sample["contexts"],
        )
        for sample in samples
    ]
    record_scores = []
    metric_values = {name: [] for name in metrics}
    for record_index, test_case in enumerate(test_cases):
        record_result: dict[str, Any] = {"record_index": record_index}
        for name, metric in metrics.items():
            metric.measure(test_case)
            score = _finite_score(metric.score)
            if score is not None:
                metric_values[name].append(score)
            record_result[name] = {
                "score": score,
                "reason": metric.reason,
            }
        record_scores.append(record_result)

    metric_summary = {
        name: {
            "mean": sum(scores) / len(scores) if scores else None,
            "scored_count": len(scores),
        }
        for name, scores in metric_values.items()
    }
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "framework": "deepeval",
        "judge": {"provider": "Gemini", "model": JUDGE_MODEL},
        "source_files": [path.name for path in run_files],
        "summary": summary,
        "metrics": metric_summary,
        "record_scores": record_scores,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"DeepEval report: {output_path}")
    print(f"Records: {summary['success_count']} successful / {summary['total_records']} total")
    for name, result in metric_summary.items():
        mean = result["mean"]
        print(f"{name}: mean={mean if mean is not None else 'n/a'}, n={result['scored_count']}")


if __name__ == "__main__":
    main()
