"""Application settings loaded from environment variables / .env.

All settings have defaults so the app runs locally without any external
services or API keys.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # App
    app_name: str = "DormMove AI"
    app_env: str = "development"
    log_level: str = "info"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "sqlite:///./dormmove.db"

    # SQLite session memory. Relative paths are resolved against the backend
    # working directory. Override with the DORMMOVE_SQLITE_PATH env var.
    sqlite_path: str = Field(
        default="local_data/dormmove.sqlite3",
        validation_alias="DORMMOVE_SQLITE_PATH",
    )

    # Optional Redis checkpointing (LangGraph)
    redis_url: str = ""

    # Model router — mock is default; OpenAI is optional.
    model_provider: str = Field(
        default="mock",
        validation_alias=AliasChoices("DORMMOVE_MODEL_PROVIDER", "MODEL_PROVIDER"),
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="DORMMOVE_LLM_MODEL",
    )
    llm_fallback_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="DORMMOVE_LLM_FALLBACK_MODEL",
    )
    openai_api_key: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
    )
    llm_timeout_seconds: float = Field(
        default=20.0,
        validation_alias="DORMMOVE_LLM_TIMEOUT_SECONDS",
    )
    llm_max_retries: int = Field(
        default=2,
        validation_alias="DORMMOVE_LLM_MAX_RETRIES",
    )
    max_model_calls_per_session: int = Field(
        default=20,
        validation_alias="DORMMOVE_MAX_MODEL_CALLS_PER_SESSION",
    )
    max_estimated_cost_per_session_usd: float = Field(
        default=0.25,
        validation_alias="DORMMOVE_MAX_ESTIMATED_COST_PER_SESSION_USD",
    )
    estimated_cost_per_call_usd: float = Field(
        default=0.002,
        validation_alias="DORMMOVE_ESTIMATED_COST_PER_CALL_USD",
    )
    allow_llm_fallback: bool = Field(
        default=True,
        validation_alias="DORMMOVE_ALLOW_LLM_FALLBACK",
    )

    gemini_api_key: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def _empty_api_key_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
