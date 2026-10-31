import pytest

from app.config import settings
from app.providers import gemini, groq

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
_PROVIDER_ENV_VARS = (
    "GEMINI_API_KEY",
    "PROVIDER_RATE_LIMIT_RPM",
    "PROVIDER_RATE_LIMIT_TPM",
    "PROVIDER_RATE_LIMIT_RPD",
    "PROVIDER_COOLDOWN_FAILURES",
    "PROVIDER_COOLDOWN_SECONDS",
    "PROVIDER_USAGE_LOG_ENABLED",
    "PROVIDER_USAGE_LOG_TIMEOUT_SECONDS",
    "GROQ_API_KEY",
    "GROQ_MODEL",
    "GROQ_FALLBACK_ENABLED",
    "GROQ_TIMEOUT_SECONDS",
    "GROQ_RATE_LIMIT_RPM",
    "GROQ_RATE_LIMIT_TPM",
    "GROQ_RATE_LIMIT_RPD",
    "GROQ_COOLDOWN_FAILURES",
    "GROQ_COOLDOWN_SECONDS",
)


@pytest.fixture(autouse=True)
def isolate_provider_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep local .env provider settings from slowing or changing unit tests."""
    for name, value in _PROVIDER_DEFAULTS.items():
        monkeypatch.setattr(settings, name, value)
    for name in _PROVIDER_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setattr(gemini, "DEFAULT_ADAPTER", gemini.GeminiProviderAdapter())
    monkeypatch.setattr(groq, "DEFAULT_ADAPTER", groq.GroqProviderAdapter())
