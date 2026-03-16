"""HTTP request handlers."""
from app.controllers.agents_controller import router as agents_router
from app.controllers.agent_instances_controller import router as agent_instances_router
from app.controllers.agent_runs_controller import router as agent_runs_router
from app.controllers.agent_templates_controller import router as agent_templates_router
from app.controllers.observability_controller import router as observability_router

__all__ = ["agents_router", "agent_instances_router", "agent_runs_router", "agent_templates_router", "observability_router"]
