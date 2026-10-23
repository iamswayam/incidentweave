"""Parse grounded investigation responses from Gemini."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence

_CONFIDENCE_PATTERN = re.compile(
    r"^\s*confidence\s*:\s*(high|medium|low)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_DIAGNOSIS_PATTERN = re.compile(
    r"^\s*diagnosis\s*:\s*(.+?)(?=\n\s*(?:confidence|evidence used)\s*:|\Z)",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
_CHUNK_PATTERN = re.compile(r"chunk_id\s*[=:]\s*([A-Za-z0-9_-]+)", re.IGNORECASE)


def _response_text(response_payload: Mapping[str, object]) -> str:
    """Extract candidate text from the standard Gemini response shape."""

    candidates = response_payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""

    candidate = candidates[0]
    if not isinstance(candidate, Mapping):
        return ""
    content = candidate.get("content")
    if not isinstance(content, Mapping):
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""

    return "\n".join(
        str(part.get("text"))
        for part in parts
        if isinstance(part, Mapping) and isinstance(part.get("text"), str)
    ).strip()


def _matches_retrieved_citation(response_text: str, result: Mapping[str, object]) -> bool:
    """Return whether the model cited the result by ID or exact file path."""

    if not isinstance(result, Mapping):
        return False

    chunk_id = str(result.get("id"))
    if _CHUNK_PATTERN.search(response_text) and any(
        matched == chunk_id for matched in _CHUNK_PATTERN.findall(response_text)
    ):
        return True

    file_path = str(result.get("file_path") or "").strip()
    if not file_path:
        return False
    if file_path in response_text:
        return True

    line_start = result.get("line_start")
    line_end = result.get("line_end")
    if line_start is None or line_end is None:
        return False

    pattern = (
        rf"{re.escape(file_path)}.*?(?:lines?|line range)\s*[:=]?\s*"
        rf"{re.escape(str(line_start))}\s*[-–]\s*{re.escape(str(line_end))}"
    )
    return bool(re.search(pattern, response_text, re.IGNORECASE | re.DOTALL))


def extract_generation_trace(
    prompt: str | None,
    response_payload: Mapping[str, object] | None,
) -> dict[str, object] | None:
    """Return a compact fingerprint and metadata for one generation call."""

    if response_payload is None:
        return None
    if not isinstance(response_payload, Mapping):
        return None

    candidates = response_payload.get("candidates")
    candidate: Mapping[str, object] | None = None
    if isinstance(candidates, list) and candidates:
        first_candidate = candidates[0]
        if isinstance(first_candidate, Mapping):
            candidate = first_candidate

    usage = response_payload.get("usageMetadata")
    usage_dict: dict[str, object] = (
        dict(usage) if isinstance(usage, Mapping) else {}
    )
    total_tokens = (
        usage_dict.get("totalTokenCount")
        if isinstance(usage_dict.get("totalTokenCount"), int)
        else None
    )
    raw_text = _response_text(response_payload)
    prompt_text = prompt if isinstance(prompt, str) else ""

    return {
        "prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
        "prompt_chars": len(prompt_text),
        "raw_text": raw_text,
        "finish_reason": (
            candidate.get("finishReason")
            if candidate and isinstance(candidate.get("finishReason"), str)
            else None
        ),
        "usage": usage_dict,
        "total_tokens": total_tokens,
    }


def parse_investigation_response(
    response_payload: Mapping[str, object],
    retrieved_results: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Extract diagnosis, categorical confidence, and cited retrieved chunk IDs."""

    response_text = _response_text(response_payload)
    cited_ids = [
        str(result.get("id"))
        for result in retrieved_results
        if _matches_retrieved_citation(response_text, result)
    ]

    confidence_match = _CONFIDENCE_PATTERN.search(response_text)
    confidence = confidence_match.group(1).lower() if confidence_match else "low"

    diagnosis_match = _DIAGNOSIS_PATTERN.search(response_text)
    diagnosis = diagnosis_match.group(1).strip() if diagnosis_match else "INSUFFICIENT_EVIDENCE"
    diagnosis = diagnosis or "INSUFFICIENT_EVIDENCE"
    if diagnosis.rstrip(".").strip().upper() == "INSUFFICIENT_EVIDENCE":
        # An abstention can never carry a confident rating (checklist item 4).
        confidence = "low"

    return {
        "diagnosis": diagnosis,
        "confidence": confidence,
        "cited_chunk_ids": cited_ids,
        "raw_text": response_text,
    }
