"""
Схемы для управления документами сценария.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.document import EditorMode


class TitlePageData(BaseModel):
    """Данные титульной страницы сценария."""

    title: str = ""
    author: str = ""
    contact: str = ""
    based_on: str = ""


class DocumentUpdateRequest(BaseModel):
    """Запрос на обновление метаданных документа."""

    title_page_data: dict | None = None
    editor_mode: EditorMode | None = None


class DocumentResponse(BaseModel):
    """Ответ с данными документа (без блоков)."""

    id: uuid.UUID
    project_id: uuid.UUID
    title_page_data: dict
    current_revision_id: uuid.UUID | None
    editor_mode: EditorMode
    created_at: datetime
    updated_at: datetime


class DocumentFullResponse(BaseModel):
    """Полный ответ с документом и всеми блоками."""

    id: uuid.UUID
    project_id: uuid.UUID
    title_page_data: dict
    current_revision_id: uuid.UUID | None
    editor_mode: EditorMode
    blocks: list["BlockResponse"]
    created_at: datetime
    updated_at: datetime
