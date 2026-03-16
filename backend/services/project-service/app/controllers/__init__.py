"""HTTP request handlers."""
from app.controllers.agent_teams_controller import router as agent_teams_router
from app.controllers.assets_controller import router as assets_router
from app.controllers.knowledge_bases_controller import router as knowledge_bases_router
from app.controllers.projects_controller import router as projects_router
from app.controllers.observability_controller import router as observability_router
from app.controllers.platform_domains_controller import router as platform_domains_router
from app.controllers.quotas_controller import router as quotas_router
from app.controllers.site_building_controller import router as site_building_router
from app.controllers.site_plan_controller import router as site_plan_router
from app.controllers.wordpress_sites_controller import router as wordpress_sites_router

__all__ = [
    "agent_teams_router",
    "assets_router",
    "knowledge_bases_router",
    "projects_router",
    "observability_router",
    "platform_domains_router",
    "quotas_router",
    "site_building_router",
    "site_plan_router",
    "wordpress_sites_router",
]
