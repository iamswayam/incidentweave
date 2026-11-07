"""Official list-price references for configured provider models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

GOOGLE_GEMINI_PRICING_URL = "https://aistudio.google.com/docs/pricing"
PRICING_RETRIEVED_ON = "2026-11-07"


@dataclass(frozen=True)
class ModelPricing:
    input_per_million: Decimal | None
    output_per_million: Decimal | None
    output_tokens_billable: bool
    currency: str
    source_url: str
    retrieved_on: str
    free_tier_note: str


_GOOGLE_FREE_TIER_NOTE = (
    "This model is not listed on the retrieved official pricing page. The page says the "
    'Free tier has "Limited access to certain models" and "Free input & output tokens"; '
    "model-specific eligibility is not stated."
)

PRICING_TABLE: dict[tuple[str, str], ModelPricing] = {
    ("gemini", "gemini-3.5-flash-lite"): ModelPricing(
        input_per_million=None,
        output_per_million=None,
        output_tokens_billable=True,
        currency="USD",
        source_url=GOOGLE_GEMINI_PRICING_URL,
        retrieved_on=PRICING_RETRIEVED_ON,
        free_tier_note=_GOOGLE_FREE_TIER_NOTE,
    ),
    ("gemini", "gemini-embedding-001"): ModelPricing(
        input_per_million=None,
        output_per_million=None,
        output_tokens_billable=False,
        currency="USD",
        source_url=GOOGLE_GEMINI_PRICING_URL,
        retrieved_on=PRICING_RETRIEVED_ON,
        free_tier_note=_GOOGLE_FREE_TIER_NOTE,
    ),
}


def pricing_for(provider: str, model: str) -> ModelPricing | None:
    """Return a model's official price entry, accepting Gemini's API model prefix."""

    canonical_model = model.removeprefix("models/")
    return PRICING_TABLE.get((provider, canonical_model))
