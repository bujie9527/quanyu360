from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    service_name: str = Field(default="agent-runtime")
    port: int = Field(default=8200)
    environment: str = Field(default="development")
    api_v1_prefix: str = Field(default="/api/v1")
    cors_origins: list[str] = Field(default=["http://localhost:3000"])
    redis_url: str = Field(default="redis://:change_me@redis:6379/6")
    default_model: str = Field(default="gpt-4.1-mini")
    tool_timeout_seconds: int = Field(default=30)
    enabled_tool_plugins: list[str] = Field(
        default_factory=list,
        description="Tool plugin names to load. Empty = auto-discover all from tools.plugins.",
    )
    memory_key_prefix: str = Field(default="agent-runtime:memory")
    analytics_key_prefix: str = Field(default="agent-runtime:analytics")
    openai_api_key: str | None = Field(default=None)
    openai_base_url: str = Field(default="https://api.openai.com/v1")
    claude_api_key: str | None = Field(default=None)
    claude_base_url: str = Field(default="https://api.anthropic.com/v1")
    local_model_base_url: str = Field(default="http://localhost:11434/v1")
    local_model_api_key: str | None = Field(default=None)
    llm_request_timeout_seconds: int = Field(default=30)
    qdrant_url: str = Field(default="http://qdrant:6333")
    qdrant_collection: str = Field(default="agent_memory")
    short_term_ttl_seconds: int = Field(default=86400)
    short_term_max_turns: int = Field(default=50)
    long_term_retrieve_limit: int = Field(default=5)
    admin_service_url: str | None = Field(
        default=None,
        description="Admin service URL for audit ingest. Empty = skip audit logging.",
    )
    project_service_url: str = Field(
        default="http://project-service:8002",
        description="Project service URL for RAG knowledge base search.",
    )
    agent_service_url: str = Field(
        default="http://agent-service:8003",
        description="Agent service URL for loading Agent/AgentInstance config.",
    )
    workflow_service_url: str = Field(
        default="http://workflow-service:8005",
        description="Workflow service URL for executing workflows.",
    )
    agent_loop_max_steps: int = Field(default=10, description="Max steps per agent execution loop.")
    agent_loop_timeout_seconds: int = Field(default=300, description="Timeout for full agent loop.")


@lru_cache
def get_settings() -> RuntimeSettings:
    return RuntimeSettings()
