import pytest

from app.api_security import rate_limiter as api_rate_limiter
from app.config import settings
from app.providers import gemini, groq
from app.providers.usage import NullUsageLogger

_PROVIDER_DEFAULTS = {
    "gemini_api_key": None,
    "provider_rate_limit_rpm": None,
    "provider_rate_limit_tpm": None,
    "provider_rate_limit_rpd": None,
    "provider_cooldown_failures": None,
    "provider_cooldown_seconds": None,
    "provider_usage_log_enabled": False,
    "provider_usage_log_timeout_seconds": 2.0,
    "groq_api_key": None,
    "groq_model": None,
    "groq_fallback_enabled": False,
    "groq_timeout_seconds": 60.0,
    "groq_rate_limit_rpm": None,
    "groq_rate_limit_tpm": None,
    "groq_rate_limit_rpd": None,
    "groq_cooldown_failures": None,
    "groq_cooldown_seconds": None,
}


@pytest.fixture(scope="session", autouse=True)
def isolate_provider_configuration() -> None:
    """Apply provider defaults once, before tests construct adapters."""
    for name, value in _PROVIDER_DEFAULTS.items():
        setattr(settings, name, value)
    gemini.DEFAULT_ADAPTER = gemini.GeminiProviderAdapter(
        usage_logger=NullUsageLogger()
    )
    groq.DEFAULT_ADAPTER = groq.GroqProviderAdapter(
        usage_logger=NullUsageLogger()
    )


@pytest.fixture(autouse=True)
def reset_provider_adapter_state(isolate_provider_configuration: None) -> None:
    """Clear mutable limiter and cooldown state without rebuilding adapters."""
    del isolate_provider_configuration
    api_rate_limiter.reset()
    for adapter in (gemini.DEFAULT_ADAPTER, groq.DEFAULT_ADAPTER):
        limiter = adapter.rate_limiter
        limiter._minute_requests.clear()
        limiter._minute_tokens.clear()
        limiter._day_requests.clear()
        limiter._day_tokens.clear()
        cooldown = adapter.cooldown
        cooldown.state = "closed"
        cooldown.consecutive_failures = 0
        cooldown.cooldown_until = 0.0
        cooldown._probe_in_flight = False
