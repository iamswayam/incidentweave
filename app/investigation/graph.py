"""LangGraph orchestration for evidence-grounded investigations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from app.db.session import AsyncSessionLocal
from app.investigation.generation import GEMINI_GENERATION_MODEL, generate_investigation
from app.investigation.guard import evaluate_evidence_sufficiency
from app.investigation.parsing import parse_investigation_response
from app.investigation.prompt import build_grounded_prompt
from app.retrieval.hybrid_search import hybrid_search


class InvestigationState(TypedDict):
    repository_id: int
    query: str
    query_embedding: list[float]
    search_limit: int
    retry_limit: int
    retry_count: int
    retry_used: bool
    retrieval_results: list[dict[str, object]]
    evidence_check: dict[str, object]
    diagnosis: str
    confidence: str
    cited_chunk_ids: list[str]
    model: str
    latency_ms: int | None
    calibration_note: str
    confidence_calibrated: bool
    prompt: NotRequired[str]
    response_payload: NotRequired[Mapping[str, object]]


ConfidenceCalibrator = Callable[
    [str, float | None, float | None], tuple[str, str]
]


def create_investigation_graph(calibrate_confidence: ConfidenceCalibrator):
    """Build the one-retry investigation graph around existing Phase 5 logic."""

    async def retrieve(state: InvestigationState) -> dict[str, object]:
        async with AsyncSessionLocal() as session:
            results = await hybrid_search(
                session,
                state["repository_id"],
                state["query"],
                state["query_embedding"],
                limit=state["search_limit"],
            )
        return {"retrieval_results": results}

    def guard(state: InvestigationState) -> dict[str, object]:
        return {
            "evidence_check": evaluate_evidence_sufficiency(
                state["retrieval_results"]
            )
        }

    def route_after_guard(state: InvestigationState) -> str:
        if state["evidence_check"]["is_sufficient"]:
            return "continue"
        if state["retry_count"] == 0:
            return "retry"
        return "stop"

    def widen_search(state: InvestigationState) -> dict[str, object]:
        return {
            "search_limit": state["retry_limit"],
            "retry_count": state["retry_count"] + 1,
            "retry_used": True,
        }

    def return_insufficient(state: InvestigationState) -> dict[str, object]:
        return {
            "diagnosis": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "cited_chunk_ids": [],
            "model": GEMINI_GENERATION_MODEL,
            "latency_ms": None,
            "calibration_note": "Not calibrated because evidence remained insufficient.",
            "confidence_calibrated": False,
        }

    def build_prompt(state: InvestigationState) -> dict[str, object]:
        return {
            "prompt": build_grounded_prompt(
                state["query"], state["retrieval_results"]
            )
        }

    def generate(state: InvestigationState) -> dict[str, object]:
        response_payload, latency_ms = generate_investigation(state["prompt"])
        return {
            "response_payload": response_payload,
            "latency_ms": latency_ms,
            "model": GEMINI_GENERATION_MODEL,
        }

    def parse(state: InvestigationState) -> dict[str, object]:
        parsed = parse_investigation_response(
            state["response_payload"], state["retrieval_results"]
        )
        return {
            "diagnosis": str(parsed["diagnosis"]),
            "confidence": str(parsed["confidence"]),
            "cited_chunk_ids": list(parsed["cited_chunk_ids"]),
        }

    def calibrate(state: InvestigationState) -> dict[str, object]:
        evidence_check = state["evidence_check"]
        confidence, note = calibrate_confidence(
            state["confidence"],
            evidence_check.get("best_rrf_score"),
            evidence_check.get("best_vector_score"),
        )
        return {
            "confidence": confidence,
            "calibration_note": note,
            "confidence_calibrated": confidence != state["confidence"],
        }

    graph = StateGraph(InvestigationState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("guard", guard)
    graph.add_node("widen_search", widen_search)
    graph.add_node("insufficient", return_insufficient)
    graph.add_node("build_prompt", build_prompt)
    graph.add_node("generate", generate)
    graph.add_node("parse", parse)
    graph.add_node("calibrate", calibrate)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "guard")
    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {"continue": "build_prompt", "retry": "widen_search", "stop": "insufficient"},
    )
    graph.add_edge("widen_search", "retrieve")
    graph.add_edge("insufficient", END)
    graph.add_edge("build_prompt", "generate")
    graph.add_edge("generate", "parse")
    graph.add_edge("parse", "calibrate")
    graph.add_edge("calibrate", END)
    return graph.compile()
