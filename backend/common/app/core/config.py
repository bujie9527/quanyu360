from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    service_name: str = Field(default="service")
    environment: str = Field(default="development")
    api_v1_prefix: str = Field(default="/api/v1")
    port: int = Field(default=8000)
    database_url: str | None = Field(default=None)
    redis_url: str | None = Field(default=None)
    jwt_secret_key: str = Field(default="unsafe-development-secret")
    jwt_algorithm: str = Field(default="HS256")
    jwt_issuer: str = Field(default="ai-workforce-platform")
    jwt_audience: str = Field(default="ai-workforce-platform-users")
    access_token_expire_minutes: int = Field(default=30)
    cors_origins: list[str] = Field(default=["http://localhost:3000"])
    auth_required: bool = Field(default=False, description="Require JWT for project/agent/task/workflow APIs")
    qdrant_url: str | None = Field(default=None, description="Qdrant vector DB URL for knowledge base embeddings.")
    admin_service_url: str | None = Field(default=None, description="Admin service URL for quota check and usage ingest.")
    workflow_service_url: str | None = Field(default=None, description="Workflow service URL for triggering workflows (e.g. from site building).")
    openai_api_key: str | None = Field(default=None)
    openai_base_url: str | None = Field(default=None)
    internal_api_key: str | None = Field(default=None, description="Secret key for internal service-to-service calls (e.g. WP-CLI callback). Set via INTERNAL_API_KEY env var.")


@lru_cache
def get_service_settings() -> ServiceSettings:
    return ServiceSettings()
