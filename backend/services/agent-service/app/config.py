from pydantic import Field

from common.app.core.config import ServiceSettings
from common.app.db.session import create_session_factory


class AgentSettings(ServiceSettings):
    service_name: str = "agent-service"
    agent_runtime_url: str = Field(
        default="http://agent-runtime:8200",
        description="Agent runtime URL for proxying run requests.",
    )


settings = AgentSettings()
session_factory = create_session_factory(settings)
