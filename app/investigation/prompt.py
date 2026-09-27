"""Grounded investigation prompt construction."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

SYSTEM_INSTRUCTION = """You are an evidence-grounded incident investigation assistant.
Use only the repository evidence supplied below. Do not invent causes, files,
lines, or system behavior that the evidence does not support. If the evidence
is insufficient, say exactly: INSUFFICIENT_EVIDENCE.
Return exactly these sections:
Diagnosis:
Confidence: high|medium|low
Evidence used:
"""


def build_grounded_prompt(
    query_text: str,
    retrieval_results: Sequence[Mapping[str, object]],
) -> str:
    """Build the prompt sent to Gemini from a query and retrieved chunks."""

    evidence_sections: list[str] = []
    for index, result in enumerate(retrieval_results, start=1):
        evidence_sections.append(
            "\n".join(
                [
                    f"Evidence {index} (chunk_id={result.get('id')}):",
                    f"File: {result.get('file_path')}",
                    f"Lines: {result.get('line_start')}-{result.get('line_end')}",
                    f"Vector distance: {result.get('vector_score')}",
                    f"FTS score: {result.get('fts_score')}",
                    f"RRF score: {result.get('rrf_score')}",
                    "Content:",
                    str(result.get("content") or ""),
                ]
            )
        )

    evidence_text = "\n\n".join(evidence_sections) or "No repository evidence was retrieved."
    return (
        f"{SYSTEM_INSTRUCTION}\n"
        f"Investigation query:\n{query_text}\n\n"
        f"Retrieved repository evidence:\n{evidence_text}\n\n"
        "Grounding requirement: base every statement on the evidence above. "
        "If it does not establish a diagnosis, return INSUFFICIENT_EVIDENCE "
        "and do not present a speculative explanation as fact."
    )
