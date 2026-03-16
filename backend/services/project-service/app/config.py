from common.app.core.config import ServiceSettings
from common.app.db.session import create_session_factory


class ProjectSettings(ServiceSettings):
    service_name: str = "project-service"


settings = ProjectSettings()
session_factory = create_session_factory(settings)
