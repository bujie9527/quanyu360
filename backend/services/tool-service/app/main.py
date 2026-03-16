"""Tool service - stub for tool management and connector registry."""
from fastapi import FastAPI

from app.controllers import observability_router
from app.controllers import tools_router

app = FastAPI(title="AI Workforce Platform - Tool Service", version="0.1.0")

app.include_router(observability_router)
app.include_router(tools_router)
