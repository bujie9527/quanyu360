from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import observability_router
from app.controllers import tasks_router
from app.config import settings
from common.app.auth import OptionalJWTMiddleware
from common.app.core.logging import configure_logging

configure_logging(settings.service_name)

app = FastAPI(
    title="AI Workforce Platform - Task Service",
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
app.include_router(tasks_router)
