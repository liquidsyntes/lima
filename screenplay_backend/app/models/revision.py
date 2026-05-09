"""
Модель версии документа (Revision).

Хранит полный снапшот состояния всех блоков на момент сохранения
в виде JSONB. Позволяет пользователю вернуться к любой предыдущей
версии сценария. При восстановлении создаётся новая ревизия
(не перезаписывается существующая, чтобы не терять историю).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class Revision(SQLModel, table=True):
    __tablename__ = "revisions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    document_id: uuid.UUID = Field(
        foreign_key="script_documents.id",
        index=True,
    )
    # Пользовательская метка версии, например "v03_submission" или "v04_notes"
    label: str | None = Field(default=None, max_length=255)
    # Полный слепок всех блоков документа в формате JSON
    # Структура: {"blocks": [{"id": "...", "type": "...", "text": "...", ...}, ...]}
    snapshot_json: dict = Field(sa_type=JSON)
    # Автоматическое описание изменений
    change_summary: str | None = Field(default=None, max_length=1000)
    created_by: uuid.UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
