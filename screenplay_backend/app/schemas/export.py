"""
Схемы для управления экспортом.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.export_job import ExportType, ExportStatus


class ExportResponse(BaseModel):
    """Ответ с данными задачи экспорта."""

    id: uuid.UUID
    document_id: uuid.UUID
    export_type: ExportType
    status: ExportStatus
    file_path: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
