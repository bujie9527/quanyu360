"""HTTP request handlers."""
from app.controllers.observability_controller import router as observability_router
from app.controllers.schedules_controller import router as schedules_router
from app.controllers.task_runs_controller import router as task_runs_router
from app.controllers.task_templates_controller import router as task_templates_router
from app.controllers.workflows_controller import router as workflows_router

__all__ = ["observability_router", "schedules_router", "task_runs_router", "task_templates_router", "workflows_router"]
