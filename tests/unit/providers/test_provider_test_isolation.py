from app.config import settings
from app.providers import gemini, groq
from app.providers.usage import NullUsageLogger


def test_provider_settings_and_adapters_start_at_documented_defaults() -> None:
    assert settings.provider_rate_limit_rpm is None
    assert settings.provider_rate_limit_tpm is None
    assert settings.provider_rate_limit_rpd is None
    assert settings.provider_cooldown_failures is None
    assert settings.provider_cooldown_seconds is None
    assert settings.provider_usage_log_enabled is False
    assert settings.provider_usage_log_timeout_seconds == 2.0
    assert settings.gemini_api_key is None
    assert settings.groq_api_key is None
    assert settings.groq_model is None
    assert settings.groq_fallback_enabled is False
    assert settings.groq_timeout_seconds == 60.0
    assert settings.groq_rate_limit_rpm is None
    assert settings.groq_rate_limit_tpm is None
    assert settings.groq_rate_limit_rpd is None
    assert settings.groq_cooldown_failures is None
    assert settings.groq_cooldown_seconds is None
    assert gemini.DEFAULT_ADAPTER.rate_limiter.rpm is None
    assert gemini.DEFAULT_ADAPTER.rate_limiter.tpm is None
    assert gemini.DEFAULT_ADAPTER.rate_limiter.rpd is None
    assert gemini.DEFAULT_ADAPTER.cooldown.enabled is False
    assert isinstance(gemini.DEFAULT_ADAPTER.usage_logger, NullUsageLogger)
    assert groq.DEFAULT_ADAPTER.rate_limiter.rpm is None
    assert groq.DEFAULT_ADAPTER.rate_limiter.tpm is None
    assert groq.DEFAULT_ADAPTER.rate_limiter.rpd is None
    assert groq.DEFAULT_ADAPTER.cooldown.enabled is False
    assert isinstance(groq.DEFAULT_ADAPTER.usage_logger, NullUsageLogger)
