"""
Эндпоинты управления версиями документа API v1.

Предоставляют просмотр истории версий, создание именованных версий,
получение деталей версии и восстановление документа из версии.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.revision import (
    RevisionCreateRequest,
    RevisionResponse,
    RevisionDetailResponse,
)
from app.services.revision_service import RevisionService

router = APIRouter(prefix="/documents/{document_id}/revisions", tags=["Версии"])


@router.get("", response_model=list[RevisionResponse])
async def list_revisions(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список всех версий документа (от новых к старым)."""
    service = RevisionService(db)
    return await service.list_revisions(document_id, current_user.id)


@router.post("", response_model=RevisionResponse, status_code=201)
async def create_revision(
    document_id: uuid.UUID,
    request: RevisionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать именованную версию текущего состояния документа.

    Полезно перед важными изменениями: отправка на ревью,
    эксперименты с перестановкой сцен и т.д.
    """
    service = RevisionService(db)
    return await service.create_revision(document_id, current_user.id, request)


@router.get("/{revision_id}", response_model=RevisionDetailResponse)
async def get_revision(
    document_id: uuid.UUID,
    revision_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить полные данные версии со снапшотом блоков."""
    service = RevisionService(db)
    return await service.get_revision(revision_id, current_user.id)


@router.post("/{revision_id}/restore", response_model=RevisionResponse)
async def restore_revision(
    document_id: uuid.UUID,
    revision_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Восстановить документ из предыдущей версии.

    Текущее состояние сохраняется в отдельную версию перед восстановлением.
    """
    service = RevisionService(db)
    return await service.restore_revision(revision_id, current_user.id)
