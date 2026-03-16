"""HTTP request handlers."""
from app.controllers.audit_controller import router as audit_router
from app.controllers.dashboard_controller import router as dashboard_router
from app.controllers.observability_controller import router as observability_router
from app.controllers.platform_domains_controller import router as platform_domains_router
from app.controllers.roles_controller import router as roles_router
from app.controllers.tenants_controller import router as tenants_router
from app.controllers.settings_controller import router as settings_router
from app.controllers.server_controller import router as server_router
from app.controllers.usage_controller import router as usage_router

__all__ = [
    "audit_router",
    "dashboard_router",
    "observability_router",
    "platform_domains_router",
    "roles_router",
    "server_router",
    "settings_router",
    "tenants_router",
    "usage_router",
]
