from common.app.core.config import ServiceSettings
from common.app.db.session import create_session_factory


class AuthSettings(ServiceSettings):
    service_name: str = "auth-service"


settings = AuthSettings()
session_factory = create_session_factory(settings)
