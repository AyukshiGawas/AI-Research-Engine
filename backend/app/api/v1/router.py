from fastapi import APIRouter

from app.api.v1.endpoints.health import root_router, versioned_router
from app.api.v1.endpoints.version import router as version_router
from app.api.v1.endpoints.ws import router as ws_router

api_router = APIRouter()
api_router.include_router(root_router)
api_router.include_router(versioned_router, prefix="/api/v1")
api_router.include_router(version_router, prefix="/api/v1")
api_router.include_router(ws_router, prefix="/api/v1")
