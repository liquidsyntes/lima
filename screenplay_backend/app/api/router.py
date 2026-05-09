"""
Агрегация всех роутеров API v1 в единый APIRouter.

Подключает роутеры аутентификации, проектов, документов,
блоков, версий и экспорта.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.documents import router as documents_router
from app.api.v1.blocks import router as blocks_router
from app.api.v1.exports import router as exports_router
from app.api.v1.revisions import router as revisions_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(documents_router)
api_router.include_router(blocks_router)
api_router.include_router(exports_router)
api_router.include_router(revisions_router)
