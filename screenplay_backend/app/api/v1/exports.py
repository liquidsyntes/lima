"""
Эндпоинты экспорта сценария API v1.

Предоставляют запуск экспорта в PDF, Fountain и TXT,
получение статуса задачи и скачивание готового файла.
"""

import uuid
import os

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.export_service import ExportService

router = APIRouter(prefix="/documents", tags=["Экспорт"])


@router.post("/{document_id}/export/pdf", status_code=202)
async def export_pdf(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Запустить экспорт сценария в профессиональный PDF.

    Генерирует PDF с Courier 12pt, правильными полями,
    титульной страницей и нумерацией.
    """
    service = ExportService(db)
    return await service.export_pdf(document_id, current_user.id)


@router.post("/{document_id}/export/fountain", status_code=202)
async def export_fountain(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Запустить экспорт сценария в Fountain."""
    service = ExportService(db)
    return await service.export_fountain(document_id, current_user.id)


@router.post("/{document_id}/export/txt", status_code=202)
async def export_txt(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Запустить экспорт сценария в TXT."""
    service = ExportService(db)
    return await service.export_txt(document_id, current_user.id)


@router.get("/exports/{export_id}")
async def get_export_status(
    export_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить статус задачи экспорта."""
    service = ExportService(db)
    return await service.get_export_status(export_id, current_user.id)


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Скачать готовый файл экспорта."""
    service = ExportService(db)
    job = await service.get_export_status(export_id, current_user.id)

    if job["status"] != "completed":
        from app.exceptions import BadRequestException
        raise BadRequestException("Экспорт ещё не завершён или завершился с ошибкой")

    file_path = job["file_path"]
    if not file_path or not os.path.exists(file_path):
        from app.exceptions import NotFoundException
        raise NotFoundException("Файл экспорта не найден")

    # Определяем MIME-тип
    media_type_map = {
        "pdf": "application/pdf",
        "fountain": "text/plain",
        "txt": "text/plain",
    }
    ext = job["export_type"]
    media_type = media_type_map.get(ext, "application/octet-stream")

    filename = f"screenplay_{export_id}.{ext}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )
