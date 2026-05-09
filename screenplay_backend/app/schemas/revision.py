"""
Схемы для управления версиями документа.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RevisionCreateRequest(BaseModel):
    """Запрос на создание именованной версии."""

    label: str | None = Field(default=None, max_length=255)
    change_summary: str | None = Field(default=None, max_length=1000)


class RevisionResponse(BaseModel):
    """Ответ с данными версии документа."""

    id: uuid.UUID
    document_id: uuid.UUID
    label: str | None
    change_summary: str | None
    created_by: uuid.UUID
    created_at: datetime


class RevisionDetailResponse(BaseModel):
    """Полный ответ с данными версии и снапшотом."""

    id: uuid.UUID
    document_id: uuid.UUID
    label: str | None
    snapshot_json: dict
    change_summary: str | None
    created_by: uuid.UUID
    created_at: datetime
