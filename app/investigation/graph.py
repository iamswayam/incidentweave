"""LangGraph orchestration for evidence-grounded investigations."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.db.session import AsyncSessionLocal
from app.investigation.generation import GEMINI_GENERATION_MODEL, generate_investigation
from app.investigation.guard import evaluate_evidence_sufficiency
from app.investigation.parsing import parse_investigation_response
from app.investigation.prompt import build_grounded_prompt
from app.retrieval.hybrid_search import hybrid_search


class InvestigationState(TypedDict):
    repository_id: int
    repository_name: str
    repository_path: str
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
    response_payload: NotRequired[Mapping[str, object]]
    grep_error: NotRequired[str | None]


ConfidenceCalibrator = Callable[
    [str, float | None, float | None], tuple[str, str]
]


async def call_grep_search_mcp(
    repository_name: str,
    repository_path: str,
    keyword: str,
    limit: int,
) -> tuple[list[dict[str, object]], str | None]:
    """Call grep_search over a real local MCP stdio subprocess."""

    repository_root = Path(__file__).resolve().parents[2]
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.investigation.mcp_server"],
        cwd=repository_root,
    )
    try:
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client:
                await client.initialize()
                response = await client.call_tool(
                    "grep_search",
                    {
                        "repository_name": repository_name,
                        "repository_path": repository_path,
                        "keyword": keyword,
                        "limit": limit,
                    },
                )
        if response.isError:
            details = "; ".join(
                item.text for item in response.content if hasattr(item, "text")
            )
            return [], details or "MCP grep_search returned an error."
        text_parts = [item.text for item in response.content if hasattr(item, "text")]
        if not text_parts:
            return [], "MCP grep_search returned no text content."
        decoded = json.loads(text_parts[0])
        if not isinstance(decoded, list):
            return [], "MCP grep_search returned an unexpected result shape."
        return [item for item in decoded if isinstance(item, dict)], None
    except Exception as exc:
        return [], f"MCP grep_search failed: {type(exc).__name__}: {exc}"


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
            "evidence_source": "hybrid",
            "grep_error": None,
        }

    def guard(state: InvestigationState) -> dict[str, object]:
        evidence_source = state["evidence_source"]
        evidence_check = evaluate_evidence_sufficiency(
            state["retrieval_results"],
            evidence_source=evidence_source,
        )
        attempts = list(state["tool_calls"])
        if evidence_source == "literal":
            outcome: dict[str, object] = {
                "match_count": len(state["retrieval_results"]),
                "sufficient": evidence_check["is_sufficient"],
                "reason": evidence_check["reason"],
            }
            if state.get("grep_error"):
                outcome["error"] = state["grep_error"]
            attempts.append(
                {
                    "tool": "grep_search",
                    "stage": "literal_fallback",
                    "parameters": {
                        "repository_name": state["repository_name"],
                        "repository_path": state["repository_path"],
                        "keyword": state["query"],
                        "limit": 20,
                    },
                    "outcome": outcome,
                }
            )
        else:
            attempts.append(
                {
                    "tool": "hybrid_search",
                    "stage": "widened_retry" if state["retry_count"] else "initial",
                    "parameters": {
                        "repository_id": state["repository_id"],
                        "repository_name": state["repository_name"],
                        "query": state["query"],
                        "query_embedding": state["query_embedding"],
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
        if state["evidence_source"] == "literal":
            return "stop"
        if state["retry_count"] == 0:
            return "retry"
        return "grep"

    def widen_search(state: InvestigationState) -> dict[str, object]:
        return {
            "search_limit": state["retry_limit"],
            "retry_count": state["retry_count"] + 1,
            "retry_used": True,
        }

    async def literal_search(state: InvestigationState) -> dict[str, object]:
        matches, error = await call_grep_search_mcp(
            state["repository_name"],
            state["repository_path"],
            state["query"],
            20,
        )
        return {
            "retrieval_results": matches,
            "evidence_source": "literal",
            "grep_error": error,
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
    graph.add_node("grep_search", literal_search)
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
            "grep": "grep_search",
            "stop": "insufficient",
        },
    )
    graph.add_edge("widen_search", "retrieve")
    graph.add_edge("grep_search", "guard")
    graph.add_edge("insufficient", END)
    graph.add_edge("build_prompt", "generate")
    graph.add_edge("generate", "parse")
    graph.add_edge("parse", "calibrate")
    graph.add_edge("calibrate", END)
    return graph.compile()
