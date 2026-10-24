"""LangGraph orchestration for evidence-grounded investigations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from app.db.session import AsyncSessionLocal
from app.investigation.generation import GEMINI_GENERATION_MODEL, generate_investigation
from app.investigation.guard import evaluate_evidence_sufficiency
from app.investigation.limits import MAX_EVIDENCE_CHARS
from app.investigation.parsing import parse_investigation_response
from app.investigation.prompt import build_grounded_prompt, select_evidence_within_budget
from app.retrieval.hybrid_search import hybrid_search


class InvestigationState(TypedDict):
    repository_id: int
    repository_name: str
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
    evidence_source: str
    tool_calls: list[dict[str, object]]
    prompt: NotRequired[str]
    raw_response: NotRequired[str]
    response_payload: NotRequired[Mapping[str, object]]
    retrieved_before_budget: NotRequired[list[dict[str, object]]]
    raw_self_rating: NotRequired[str]
    claims: NotRequired[list[dict[str, object]]]
    uncertainty_note: NotRequired[str]
    submitted_citation_count: NotRequired[int]
    valid_citation_count: NotRequired[int]
    citation_validity_rate: NotRequired[float | None]


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
        return {
            "retrieval_results": results,
            "retrieved_before_budget": results,
            "evidence_source": "hybrid",
        }

    def guard(state: InvestigationState) -> dict[str, object]:
        evidence_check = evaluate_evidence_sufficiency(
            state["retrieval_results"],
        )
        attempts = list(state["tool_calls"])
        attempts.append(
            {
                "tool": "hybrid_search",
                "stage": "widened_retry" if state["retry_count"] else "initial",
                "parameters": {
                    "repository_name": state["repository_name"],
                    "query": state["query"],
                    "limit": state["search_limit"],
                },
                "outcome": {
                    "result_count": len(state["retrieval_results"]),
                    "sufficient": evidence_check["is_sufficient"],
                    "reason": evidence_check["reason"],
                    "best_rrf_score": evidence_check["best_rrf_score"],
                    "best_vector_score": evidence_check["best_vector_score"],
                },
            }
        )
        return {"evidence_check": evidence_check, "tool_calls": attempts}

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
            "tool_calls": state["tool_calls"],
        }

    def build_prompt(state: InvestigationState) -> dict[str, object]:
        kept_results, dropped_count = select_evidence_within_budget(
            state["retrieval_results"], max_chars=MAX_EVIDENCE_CHARS
        )
        tool_calls = list(state["tool_calls"])
        first_content = (
            str(state["retrieval_results"][0].get("content") or "")
            if state["retrieval_results"]
            else ""
        )
        was_truncated = len(first_content) > MAX_EVIDENCE_CHARS
        dropped_results = state["retrieval_results"][len(kept_results) :]
        if dropped_count or was_truncated:
            tool_calls.append(
                {
                    "tool": "prompt_budget",
                    "stage": "evidence_trim",
                    "parameters": {"max_chars": MAX_EVIDENCE_CHARS},
                    "outcome": {
                        "kept": len(kept_results),
                        "dropped": dropped_count,
                        "truncated": was_truncated,
                        "dropped_chunk_ids": [
                            result.get("id") for result in dropped_results
                        ],
                    },
                }
            )
        return {
            "retrieval_results": kept_results,
            "retrieved_before_budget": list(state["retrieval_results"]),
            "tool_calls": tool_calls,
            "prompt": build_grounded_prompt(
                state["query"], kept_results, max_evidence_chars=MAX_EVIDENCE_CHARS
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
            "raw_self_rating": str(parsed["raw_self_rating"]),
            "raw_response": str(parsed["raw_text"]),
            "cited_chunk_ids": list(parsed["cited_chunk_ids"]),
            "claims": list(parsed["claims"]),
            "uncertainty_note": str(parsed["uncertainty_note"]),
            "submitted_citation_count": int(parsed["submitted_citation_count"]),
            "valid_citation_count": int(parsed["valid_citation_count"]),
            "citation_validity_rate": parsed["citation_validity_rate"],
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
        {
            "continue": "build_prompt",
            "retry": "widen_search",
            "stop": "insufficient",
        },
    )
    graph.add_edge("widen_search", "retrieve")
    graph.add_edge("insufficient", END)
    graph.add_edge("build_prompt", "generate")
    graph.add_edge("generate", "parse")
    graph.add_edge("parse", "calibrate")
    graph.add_edge("calibrate", END)
    return graph.compile()
