"""
Схемы для управления проектами.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project import ProjectFormatType, ProjectStatus


class ProjectCreateRequest(BaseModel):
    """Запрос на создание нового проекта."""

    title: str = Field(min_length=1, max_length=500)
    format_type: ProjectFormatType = ProjectFormatType.FEATURE_FILM
    language: str = Field(default="en", max_length=10)


class ProjectUpdateRequest(BaseModel):
    """Запрос на обновление проекта."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    format_type: ProjectFormatType | None = None
    language: str | None = Field(default=None, max_length=10)
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    """Ответ с данными проекта."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    format_type: ProjectFormatType
    language: str
    status: ProjectStatus
    last_opened_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Список проектов с пагинацией."""

    items: list[ProjectResponse]
    total: int
    offset: int
    limit: int
