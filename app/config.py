"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the IncidentWeave application."""

    app_env: str = "development"
    database_url: str = "postgresql://incidentweave:incidentweave@localhost:5432/incidentweave"
    gemini_api_key: str | None = None
    api_protection_secret: str | None = None

    provider_rate_limit_rpm: float | None = None
    provider_rate_limit_tpm: float | None = None
    provider_rate_limit_rpd: float | None = None
    provider_cooldown_failures: int | None = None
    provider_cooldown_seconds: float | None = None
    provider_usage_log_enabled: bool = False
    provider_usage_log_timeout_seconds: float = 2.0
    groq_api_key: str | None = None
    groq_model: str | None = None
    groq_fallback_enabled: bool = False
    groq_timeout_seconds: float = 60.0
    groq_rate_limit_rpm: float | None = None
    groq_rate_limit_tpm: float | None = None
    groq_rate_limit_rpd: float | None = None
    groq_cooldown_failures: int | None = None
    groq_cooldown_seconds: float | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
