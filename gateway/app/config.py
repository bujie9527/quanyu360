"""Gateway configuration."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    service_name: str = Field(default="api-gateway")
    port: int = Field(default=8300)
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    jwt_secret_key: str = Field(default="unsafe-development-secret")
    jwt_algorithm: str = Field(default="HS256")
    jwt_issuer: str = Field(default="ai-workforce-platform")
    jwt_audience: str = Field(default="ai-workforce-platform-users")

    auth_service_url: str = Field(default="http://auth-service:8001")
    project_service_url: str = Field(default="http://project-service:8002")
    agent_service_url: str = Field(default="http://agent-service:8003")
    task_service_url: str = Field(default="http://task-service:8004")
    workflow_service_url: str = Field(default="http://workflow-service:8005")
    tool_service_url: str = Field(default="http://tool-service:8006")
    admin_service_url: str = Field(default="http://admin-service:8007")
    workflow_engine_url: str = Field(default="http://workflow-engine:8100")
    agent_runtime_url: str = Field(default="http://agent-runtime:8200")

    rate_limit_default: str = Field(default="100/minute")
    rate_limit_auth: str = Field(default="20/minute")

    public_paths: tuple[str, ...] = (
        "/api/auth/login",
        "/api/auth/register",
        "/api/metrics",
        "/api/v1/metrics",
        "/api/v1/webhooks",
        "/health/live",
        "/health/ready",
    )

    # Optional: bypass JWT for health checks and docs
    jwt_enabled: bool = Field(default=True)


@lru_cache
def get_settings() -> GatewaySettings:
    return GatewaySettings()
