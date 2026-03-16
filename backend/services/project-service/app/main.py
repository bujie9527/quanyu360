from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import agent_teams_router
from app.controllers import assets_router
from app.controllers import knowledge_bases_router
from app.controllers import observability_router
from app.controllers import platform_domains_router
from app.controllers import projects_router
from app.controllers import quotas_router
from app.controllers import site_building_router
from app.controllers import site_plan_router
from app.controllers import wordpress_sites_router
from app.config import settings
from common.app.auth import OptionalJWTMiddleware
from common.app.core.logging import configure_logging

configure_logging(settings.service_name)

app = FastAPI(
    title="AI Workforce Platform - Project Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(OptionalJWTMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(observability_router)
app.include_router(platform_domains_router)
app.include_router(quotas_router)
app.include_router(site_building_router)
app.include_router(site_plan_router)
app.include_router(projects_router)
app.include_router(agent_teams_router)
app.include_router(assets_router)
app.include_router(knowledge_bases_router)
app.include_router(wordpress_sites_router)
