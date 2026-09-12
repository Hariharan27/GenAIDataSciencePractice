from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Supported application environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LLMProvider(StrEnum):
    """Supported LLM providers."""

    OLLAMA = "ollama"
    TOGETHER = "together"
    OPENAI = "openai"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(
        default="AI Project Health Monitor",
        min_length=1,
    )
    app_version: str = Field(
        default="0.1.0",
        min_length=1,
    )
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    health_monitoring_enabled: bool = True
    health_monitoring_interval_minutes: int = Field(
        default=60,
        gt=0,
    )
    health_monitoring_project_ids: list[str] = Field(
        default_factory=lambda: ["PROJ-001"],
    )
    llm_provider: LLMProvider = LLMProvider.OLLAMA
    llm_model: str = Field(
        default="qwen3:8b",
        min_length=1,
    )

    ollama_host: str = Field(
        default="http://localhost:11434",
        min_length=1,
    )

    together_api_key: str | None = None
    openai_api_key: str | None = None
    langfuse_enabled: bool = False
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = Field(
        default="http://localhost:3000",
        min_length=1,
    )

    qdrant_url: str = Field(
        default="http://localhost:6333",
        min_length=1,
    )

    jira_source_path: str = Field(
        default="data/synthetic/jira/events.json",
        min_length=1,
    )

    email_source_path: str = Field(
        default="data/synthetic/emails/events.json",
        min_length=1,
    )

    document_source_directory: str = Field(
        default="data/synthetic/documents",
        min_length=1,
    )
    postgres_dsn: str = Field(
        default="postgresql://postgres:postgres@localhost:5434/ai_project_health_monitor",
        min_length=1,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()