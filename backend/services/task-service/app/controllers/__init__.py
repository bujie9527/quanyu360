"""HTTP request handlers."""
from app.controllers.observability_controller import router as observability_router
from app.controllers.tasks_controller import router as tasks_router

__all__ = ["observability_router", "tasks_router"]
