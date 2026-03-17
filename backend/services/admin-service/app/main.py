"""Admin service - platform administration and multi-tenant management."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.controllers import audit_router
from app.controllers import dashboard_router
from app.controllers import observability_router
from app.controllers import platform_domains_router
from app.controllers import roles_router
from app.controllers import server_router
from app.controllers import settings_router
from app.controllers import site_pool_router
from app.controllers import tenants_router
from app.controllers import usage_router
from common.app.auth import OptionalJWTMiddleware
from common.app.auth.rbac_middleware import RBACEnrichmentMiddleware

app = FastAPI(
    title="AI Workforce Platform - Admin Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(OptionalJWTMiddleware)
app.add_middleware(RBACEnrichmentMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(observability_router)
app.include_router(audit_router)
app.include_router(platform_domains_router)
app.include_router(usage_router)
app.include_router(settings_router)
app.include_router(dashboard_router)
app.include_router(tenants_router)
app.include_router(roles_router)
app.include_router(server_router)
app.include_router(site_pool_router)
