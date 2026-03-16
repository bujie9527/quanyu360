from common.app.core.config import ServiceSettings
from common.app.db.session import create_session_factory


class WorkflowSettings(ServiceSettings):
    service_name: str = "workflow-service"
    workflow_engine_url: str = "http://workflow-engine:8100"


settings = WorkflowSettings()
session_factory = create_session_factory(settings)
