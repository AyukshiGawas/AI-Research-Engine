"""Main V1 API Router aggregation module."""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.health import root_router, versioned_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.version import router as version_router

api_router = APIRouter()

# Unauthenticated health endpoints
api_router.include_router(root_router)
api_router.include_router(versioned_router, prefix="/api/v1")
api_router.include_router(version_router, prefix="/api/v1")

# Phase 2: Authentication, User, and Project endpoints
api_router.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/api/v1/users", tags=["users"])
api_router.include_router(projects_router, prefix="/api/v1/projects", tags=["projects"])

# Phase 3: Document management endpoints (nested under /projects)
api_router.include_router(documents_router, prefix="/api/v1/projects", tags=["documents"])
