"""Admin service configuration."""
from pydantic import Field

from common.app.core.config import ServiceSettings
from common.app.db.session import create_session_factory


class AdminSettings(ServiceSettings):
    service_name: str = "admin-service"
    project_service_url: str = Field(default="http://project-service:8002")
    agent_service_url: str = Field(default="http://agent-service:8003")
    task_service_url: str = Field(default="http://task-service:8004")
    workflow_service_url: str = Field(default="http://workflow-service:8005")
    config_encryption_key: str | None = Field(default=None)


settings = AdminSettings()
session_factory = create_session_factory(settings)
