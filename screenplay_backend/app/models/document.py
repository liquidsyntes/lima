"""
Модель документа сценария.

В MVP — один документ на проект. Содержит метаданные титульной страницы
и настройки режима редактора. В будущем проект может иметь несколько
документов (варианты черновика, версии для разных целей).
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class EditorMode(str, Enum):
    """Режим редактора — влияет на строгость валидации."""

    DRAFT = "draft"  # Свободный режим, минимум предупреждений
    PROFESSIONAL = "professional"  # Строгие форматные подсказки
    READ = "read"  # Режим предпросмотра без UI-шума


class ScriptDocument(SQLModel, table=True):
    __tablename__ = "script_documents"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    project_id: uuid.UUID = Field(
        foreign_key="projects.id",
        unique=True,
        index=True,
    )
    # JSON с данными титульной страницы:
    # {"title": "...", "author": "...", "contact": "...", "based_on": "..."}
    title_page_data: dict = Field(default={}, sa_type=JSON)
    current_revision_id: uuid.UUID | None = Field(
        foreign_key="revisions.id",
        default=None,
        nullable=True,
    )
    editor_mode: EditorMode = Field(default=EditorMode.DRAFT)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
