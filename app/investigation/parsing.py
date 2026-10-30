"""Parse grounded investigation responses from Gemini."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence


class ModelOutputError(RuntimeError):
    """Raised when provider output does not match the required JSON contract."""


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


def _normalized_whitespace(text: str) -> str:
    return " ".join(text.split())


def _structured_response(response_text: str) -> Mapping[str, object]:
    try:
        response = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ModelOutputError("The model response was not valid JSON.") from exc
    if not isinstance(response, Mapping):
        raise ModelOutputError("The model response must be a JSON object.")
    outcome = response.get("outcome")
    if not isinstance(outcome, str) or outcome not in {
        "answered",
        "insufficient_evidence",
    }:
        raise ModelOutputError("The model response has an invalid outcome.")
    if not isinstance(response.get("diagnosis"), str):
        raise ModelOutputError("The model response diagnosis must be a string.")
    self_rating = response.get("self_rating")
    if not isinstance(self_rating, str) or self_rating not in {
        "low",
        "medium",
        "high",
    }:
        raise ModelOutputError("The model response self_rating is invalid.")
    if not isinstance(response.get("uncertainty_note"), str):
        raise ModelOutputError("The model response uncertainty_note must be a string.")
    claims = response.get("claims")
    if not isinstance(claims, list):
        raise ModelOutputError("The model response claims must be an array.")
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise ModelOutputError("Each model claim must be an object.")
        if not isinstance(claim.get("text"), str):
            raise ModelOutputError("Each model claim text must be a string.")
        evidence = claim.get("evidence")
        if not isinstance(evidence, list):
            raise ModelOutputError("Each model claim evidence must be an array.")
        for item in evidence:
            if not isinstance(item, Mapping):
                raise ModelOutputError("Each evidence item must be an object.")
            if not isinstance(item.get("chunk_id"), str) or not isinstance(
                item.get("quote"), str
            ):
                raise ModelOutputError("Evidence chunk_id and quote must be strings.")
    return response


def validate_generation_response_text(response_text: str) -> Mapping[str, object]:
    """Validate provider JSON against the investigation response contract."""

    return _structured_response(response_text)


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
    """Parse structured output and retain only claims with verifiable evidence."""

    raw_text = _response_text(response_payload)
    response = _structured_response(raw_text)

    retrieved_by_id = {
        str(result.get("id")): result
        for result in retrieved_results
        if result.get("id") is not None
    }
    submitted_citations = 0
    valid_citations = 0
    cited_ids: list[str] = []
    validated_claims: list[dict[str, object]] = []
    claims = response.get("claims")
    if isinstance(claims, list):
        for claim in claims:
            if not isinstance(claim, Mapping):
                continue
            claim_text = claim.get("text")
            evidence = claim.get("evidence")
            if not isinstance(claim_text, str) or not claim_text.strip():
                continue
            valid_evidence: list[dict[str, str]] = []
            if isinstance(evidence, list):
                submitted_citations += len(evidence)
                for item in evidence:
                    chunk_id = item.get("chunk_id")
                    quote = item.get("quote")
                    result = retrieved_by_id.get(chunk_id)
                    content = (
                        str(result.get("content") or "")
                        if result is not None
                        else ""
                    )
                    normalized_quote = _normalized_whitespace(quote)
                    if (
                        len(normalized_quote) < 10
                        or normalized_quote not in _normalized_whitespace(content)
                    ):
                        continue
                    valid_evidence.append(
                        {"chunk_id": chunk_id, "quote": quote}
                    )
                    valid_citations += 1
                    if chunk_id not in cited_ids:
                        cited_ids.append(chunk_id)
            if valid_evidence:
                validated_claims.append(
                    {"text": claim_text.strip(), "evidence": valid_evidence}
                )

    requested_outcome = response.get("outcome")
    diagnosis_value = response.get("diagnosis")
    diagnosis = (
        diagnosis_value.strip()
        if isinstance(diagnosis_value, str) and diagnosis_value.strip()
        else "INSUFFICIENT_EVIDENCE"
    )
    raw_self_rating = str(response["self_rating"])
    is_model_abstention = (
        requested_outcome == "insufficient_evidence"
        or diagnosis.rstrip(".").strip().upper() == "INSUFFICIENT_EVIDENCE"
    )
    no_valid_claims = not validated_claims
    if is_model_abstention or no_valid_claims:
        diagnosis = "INSUFFICIENT_EVIDENCE"
        confidence = "low"
        outcome = "insufficient_evidence"
    else:
        confidence = raw_self_rating
        outcome = "answered"

    uncertainty_note = response.get("uncertainty_note")
    return {
        "outcome": outcome,
        "diagnosis": diagnosis,
        "confidence": confidence,
        "raw_self_rating": raw_self_rating,
        "cited_chunk_ids": cited_ids,
        "claims": validated_claims,
        "uncertainty_note": uncertainty_note.strip(),
        "submitted_citation_count": submitted_citations,
        "valid_citation_count": valid_citations,
        "citation_validity_rate": (
            valid_citations / submitted_citations if submitted_citations else None
        ),
        "raw_text": raw_text,
    }
