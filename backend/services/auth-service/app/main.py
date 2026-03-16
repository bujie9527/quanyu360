from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import settings
from app.middleware import JWTAuthenticationMiddleware
from common.app.core.logging import configure_logging

configure_logging(settings.service_name)

app = FastAPI(
    title="AI Workforce Platform - Auth Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JWTAuthenticationMiddleware)

app.include_router(router)
