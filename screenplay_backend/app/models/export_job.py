"""
Модель задачи экспорта (ExportJob).

Отслеживает состояние процесса экспорта сценария в различные форматы.
В MVP экспорт выполняется синхронно, но модель готова к асинхронной
обработке через Celery/RQ в будущем.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class ExportType(str, Enum):
    """Формат экспорта."""

    PDF = "pdf"
    FOUNTAIN = "fountain"
    TXT = "txt"


class ExportStatus(str, Enum):
    """Статус задачи экспорта."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportJob(SQLModel, table=True):
    __tablename__ = "export_jobs"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    document_id: uuid.UUID = Field(foreign_key="script_documents.id")
    export_type: ExportType = Field()
    status: ExportStatus = Field(default=ExportStatus.PENDING)
    file_path: str | None = Field(default=None, max_length=1000)
    error_message: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    completed_at: datetime | None = Field(default=None)
