"""Shared application settings, used by every subproject router."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration, overridable via environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")

    app_name: str = "UK Energy Grid Data & VPP Optimisation API"
    # Origins allowed to call this API in development (the Vite dev server).
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
