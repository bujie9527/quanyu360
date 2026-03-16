from common.app.core.config import ServiceSettings
from common.app.db.session import create_session_factory


class TaskSettings(ServiceSettings):
    service_name: str = "task-service"
    task_queue_name: str = "task-service:queue"
    task_worker_block_seconds: int = 5
    task_default_max_attempts: int = 3
    agent_runtime_url: str = "http://agent-runtime:8200"


settings = TaskSettings()
session_factory = create_session_factory(settings)
