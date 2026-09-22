## Combines all API route modules under /api/v1.
from fastapi import APIRouter

from app.api.routes import auth, health, workspace

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(workspace.router)
