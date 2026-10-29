"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the IncidentWeave application."""

    app_env: str = "development"
    database_url: str = "postgresql://incidentweave:incidentweave@localhost:5432/incidentweave"
    gemini_api_key: str | None = None
    api_protection_secret: str | None = None

    provider_retry_max_attempts: int = 3
    provider_retry_deadline_seconds: float = 90.0
    provider_retry_base_delay_seconds: float = 0.5
    provider_rate_limit_rpm: float | None = None
    provider_rate_limit_tpm: float | None = None
    provider_rate_limit_rpd: float | None = None
    provider_cooldown_failures: int | None = None
    provider_cooldown_seconds: float | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
