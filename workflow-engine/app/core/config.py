from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EngineSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    service_name: str = Field(default="workflow-engine")
    port: int = Field(default=8100)
    environment: str = Field(default="development")
    api_v1_prefix: str = Field(default="/api/v1")
    cors_origins: list[str] = Field(default=["http://localhost:3000"])
    redis_url: str = Field(default="redis://:change_me@redis:6379/5")
    broker_stream: str = Field(default="workflow-events")
    execution_queue_name: str = Field(default="workflow-engine:queue")
    execution_state_prefix: str = Field(default="workflow-engine:execution")
    execution_index_key: str = Field(default="workflow-engine:executions")
    rate_limit_key_prefix: str = Field(default="workflow-engine")
    execution_worker_block_seconds: int = Field(default=5)
    max_delay_seconds: int = Field(default=5)
    tool_timeout_seconds: int = Field(default=60, description="Timeout for tool execution in workflow nodes.")
    agent_runtime_url: str = Field(default="http://agent-runtime:8200")
    admin_service_url: str | None = Field(
        default=None,
        description="Admin service URL for audit ingest. Empty = skip audit logging.",
    )
    workflow_service_url: str = Field(
        default="http://workflow-service:8005",
        description="Workflow service URL for trigger scheduler to fetch and trigger workflows.",
    )


@lru_cache
def get_settings() -> EngineSettings:
    return EngineSettings()
