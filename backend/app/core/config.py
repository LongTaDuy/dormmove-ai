"""Application settings loaded from environment variables / .env.

All settings have defaults so the app runs locally without any external
services or API keys.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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

    # Model router
    model_provider: str = "mock"
    model_name: str = "mock-default"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
