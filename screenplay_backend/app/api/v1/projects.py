"""
Эндпоинты управления проектами API v1.

Предоставляют CRUD-операции для проектов: создание, получение списка,
получение по ID, обновление, мягкое удаление и дублирование.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Проекты"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str = Query(default=""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список проектов текущего пользователя с поиском и пагинацией."""
    service = ProjectService(db)
    return await service.list_projects(current_user.id, offset, limit, search)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать новый проект сценария.

    Автоматически создаёт документ и настройки по умолчанию.
    """
    service = ProjectService(db)
    return await service.create_project(current_user.id, request)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить проект по ID."""
    service = ProjectService(db)
    return await service.get_project(project_id, current_user.id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    request: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить проект (название, формат, язык, статус)."""
    service = ProjectService(db)
    return await service.update_project(project_id, current_user.id, request)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Мягкое удаление проекта (перевод в архив)."""
    service = ProjectService(db)
    await service.delete_project(project_id, current_user.id)


@router.get("/{project_id}/document")
async def get_project_document(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить ID документа, связанного с проектом."""
    from app.services.document_service import DocumentService
    service = DocumentService(db)
    doc_id = await service.get_document_id_by_project(project_id, current_user.id)
    return {"document_id": str(doc_id), "project_id": str(project_id)}


@router.post("/{project_id}/duplicate", response_model=ProjectResponse, status_code=201)
async def duplicate_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Дублировать проект со всем содержимым."""
    service = ProjectService(db)
    return await service.duplicate_project(project_id, current_user.id)
